#!/usr/bin/env python3
"""Deterministic, standard-library-only validator for Juggle puzzle data.

Parses puzzles.js (PUZZLE_PUBLISHING_RANGE, PUZZLE_ENTRIES) as embedded JSON
without executing any JavaScript, and reports structural/content diagnostics.
Blocking errors cause a nonzero exit; non-blocking quality warnings do not.

Usage:
    python3 scripts/validate_puzzles.py [path/to/candidate.js]

If no path is given, validates the live puzzles.js at the repository root.
"""

import json
import re
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = REPO_ROOT / "puzzles.js"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ANSWER_RE = re.compile(r"^[A-Z]{6}$")
REQUIRED_ENTRY_FIELDS = ("date", "theme", "row")


# ─── JS-integer-compatible arithmetic (for deterministicScramble) ─────────────

def to_int32(x):
    x &= 0xFFFFFFFF
    return x - 0x100000000 if x >= 0x80000000 else x


def imul32(a, b):
    """Port of JavaScript's Math.imul(a, b)."""
    return to_int32(a * b)


def _lcg_step(h):
    return to_int32(imul32(h, 1664525) + 1013904223)


def _lcg_hash(seed):
    h = 0
    for ch in seed:
        h = to_int32(imul32(31, h) + ord(ch))
    return h


def deterministic_scramble(word, seed):
    """Python port of game.js's deterministicScramble(word, seed)."""
    letters = list(word)
    h = _lcg_hash(seed)

    # Fisher-Yates.
    for i in range(len(letters) - 1, 0, -1):
        h = _lcg_step(h)
        j = abs(h) % (i + 1)
        letters[i], letters[j] = letters[j], letters[i]

    # If shuffle produced the original, swap the first non-identical
    # adjacent pair.
    if "".join(letters) == word:
        for i in range(len(letters) - 1):
            if letters[i] != letters[i + 1]:
                letters[i], letters[i + 1] = letters[i + 1], letters[i]
                break

    # Break any bigram (forward or reversed) that appears consecutively
    # in the original word.
    answer_bigrams = set()
    for i in range(len(word) - 1):
        answer_bigrams.add(word[i:i + 2])
        answer_bigrams.add(word[i + 1] + word[i])

    for _ in range(30):
        bad_idx = -1
        for i in range(len(letters) - 1):
            if letters[i] + letters[i + 1] in answer_bigrams:
                bad_idx = i
                break
        if bad_idx == -1:
            break
        h = _lcg_step(h)
        n = len(letters)
        swap_with = (abs(h) % (n - 2) + bad_idx + 2) % n
        letters[bad_idx + 1], letters[swap_with] = letters[swap_with], letters[bad_idx + 1]

    return "".join(letters)


# ─── Diagnostics ───────────────────────────────────────────────────────────────

@dataclass
class Diagnostic:
    severity: str  # "ERROR" or "WARNING"
    rule: str
    message: str
    entry_date: str = ""
    theme: str = ""

    def format(self):
        loc_bits = [self.entry_date or "-"]
        if self.theme:
            loc_bits.append(f"theme={self.theme!r}")
        loc = " ".join(loc_bits)
        return f"[{self.severity}] {loc} rule={self.rule}: {self.message}"


def err(rule, message, entry_date="", theme=""):
    return Diagnostic("ERROR", rule, message, entry_date, theme)


def warn(rule, message, entry_date="", theme=""):
    return Diagnostic("WARNING", rule, message, entry_date, theme)


# ─── Source extraction (no JS execution) ──────────────────────────────────────

def _extract_balanced(text, start_idx, open_ch, close_ch):
    depth = 0
    in_str = False
    escape = False
    for i in range(start_idx, len(text)):
        c = text[i]
        if in_str:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    return text[start_idx:i + 1]
    raise ValueError(f"unbalanced '{open_ch}{close_ch}' starting at index {start_idx}")


def _locate_balanced_span(text, const_name, open_ch, close_ch):
    """Locate `const <const_name> = <balanced open_ch...close_ch>` in text.

    Returns (start, end, error). text[start:end] is the balanced block
    (inclusive of both bracket characters, end exclusive) when found without
    a structural error. When the declaration is absent, returns
    (None, None, None) so the caller can report "missing". When present but
    malformed (no opening bracket, or an unbalanced/unterminated block),
    returns (None, None, error_message) so the caller can report an
    actionable diagnostic instead of letting an exception escape. Exposed
    (beyond _extract_json_value's blob-only return) so callers that need to
    rewrite a declaration in place — not just read it — have a deterministic
    span to splice around instead of re-deriving one with a fragile regex.
    """
    m = re.search(rf"const\s+{re.escape(const_name)}\s*=\s*", text)
    if not m:
        return None, None, None
    try:
        start = text.index(open_ch, m.end())
    except ValueError:
        return None, None, (f"'{const_name}' declaration has no opening "
                             f"'{open_ch}' after 'const {const_name} ='")
    try:
        blob = _extract_balanced(text, start, open_ch, close_ch)
    except ValueError:
        return None, None, (f"'{const_name}' has an unbalanced or malformed "
                             f"'{open_ch} ... {close_ch}' block")
    return start, start + len(blob), None


def _extract_json_value(text, const_name, open_ch, close_ch):
    """Locate `const <const_name> = <balanced open_ch...close_ch>` in text.

    Returns (blob_or_None, error_message_or_None). blob is None with no error
    when the declaration is simply absent (caller reports "missing"); blob is
    None with an error message when the declaration exists but is malformed
    (e.g. unbalanced brackets) so the caller can report an actionable
    diagnostic instead of letting an exception escape.
    """
    start, end, error = _locate_balanced_span(text, const_name, open_ch, close_ch)
    if error is not None:
        return None, error
    if start is None:
        return None, None
    return text[start:end], None


def parse_text(text):
    """Extract PUZZLE_PUBLISHING_RANGE and PUZZLE_ENTRIES from source text.

    Returns (publishing_range, entries, diagnostics). Either value may be
    None if the corresponding top-level field is missing or malformed. Never
    raises for malformed/unbalanced/invalid-JSON input; such input becomes a
    diagnostic instead.
    """
    diags = []

    range_blob, range_err = _extract_json_value(text, "PUZZLE_PUBLISHING_RANGE", "{", "}")
    entries_blob, entries_err = _extract_json_value(text, "PUZZLE_ENTRIES", "[", "]")

    publishing_range = None
    entries = None

    if range_err:
        diags.append(err("malformed-top-level-field", range_err))
    elif range_blob is None:
        diags.append(err("missing-top-level-field",
                          "PUZZLE_PUBLISHING_RANGE declaration not found"))
    else:
        try:
            publishing_range = json.loads(range_blob)
        except json.JSONDecodeError as e:
            diags.append(err("malformed-top-level-field",
                              f"PUZZLE_PUBLISHING_RANGE is not valid JSON: {e}"))

    if entries_err:
        diags.append(err("malformed-top-level-field", entries_err))
    elif entries_blob is None:
        diags.append(err("missing-top-level-field",
                          "PUZZLE_ENTRIES declaration not found"))
    else:
        try:
            entries = json.loads(entries_blob)
        except json.JSONDecodeError as e:
            diags.append(err("malformed-top-level-field",
                              f"PUZZLE_ENTRIES is not valid JSON: {e}"))

    return publishing_range, entries, diags


def load_source(path):
    """Read and parse a candidate data file.

    Never raises for a missing, unreadable, or invalidly-encoded file; such
    conditions become a diagnostic (and thus a nonzero validator exit)
    instead of an uncaught exception.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, None, [err("file-not-found", f"Data file not found: {path}")]
    except IsADirectoryError:
        return None, None, [err("file-unreadable", f"Data file path is a directory, not a file: {path}")]
    except UnicodeDecodeError as e:
        return None, None, [err("file-unreadable", f"Data file is not valid UTF-8 text ({path}): {e}")]
    except OSError as e:
        return None, None, [err("file-unreadable", f"Data file could not be read ({path}): {e}")]

    return parse_text(text)


# ─── Validation ────────────────────────────────────────────────────────────────

def _validate_date_field(value, label, diags, entry_date="", theme=""):
    """Validate a YYYY-MM-DD string field. Returns a date object or None."""
    if not isinstance(value, str) or value == "":
        diags.append(err("field-type", f"'{label}' must be a non-empty string",
                          entry_date, theme))
        return None
    if not DATE_RE.match(value):
        diags.append(err("date-format", f"'{label}' ({value}) is not canonical YYYY-MM-DD",
                          entry_date, theme))
        return None
    try:
        y, mo, d = (int(p) for p in value.split("-"))
        return date(y, mo, d)
    except ValueError:
        diags.append(err("date-invalid", f"'{label}' ({value}) is not a valid calendar date",
                          entry_date, theme))
        return None


def _parse_row_markers(raw_item):
    """Scan a raw (possibly asterisked) item for markers.

    Valid marker grammar: a marker must occur exactly once, immediately
    after a previously unmarked answer letter. A leading marker (no letter
    yet), consecutive markers (e.g. "A**BCDEF"), or any other marker not
    immediately preceded by a fresh letter is grammatically invalid.

    Returns (answer, bonus_indices, grammar_ok). bonus_indices only contains
    indices from grammatically valid markers.
    """
    answer = raw_item.replace("*", "")
    bonus_indices = []
    answer_pos = 0
    prev_was_unmarked_letter = False
    grammar_ok = True
    for ch in raw_item:
        if ch == "*":
            if not prev_was_unmarked_letter:
                grammar_ok = False
            else:
                bonus_indices.append(answer_pos - 1)
            prev_was_unmarked_letter = False
        else:
            answer_pos += 1
            prev_was_unmarked_letter = True
    return answer, bonus_indices, grammar_ok


def validate(publishing_range, entries):
    diags = []

    if not isinstance(entries, list):
        diags.append(err("entry-list-type", "PUZZLE_ENTRIES must be a list"))
        entries = []

    if not isinstance(publishing_range, dict):
        diags.append(err("publishing-range-type", "PUZZLE_PUBLISHING_RANGE must be an object"))
        publishing_range = {}

    # ── Per-entry field validation ────────────────────────────────────────
    parsed = []  # dicts with: index, date_str, theme, row, date_obj
    for i, raw in enumerate(entries):
        if not isinstance(raw, dict):
            diags.append(err("entry-type", f"Entry #{i + 1} is not an object"))
            continue

        missing = [f for f in REQUIRED_ENTRY_FIELDS if f not in raw]
        extra = sorted(set(raw.keys()) - set(REQUIRED_ENTRY_FIELDS))

        entry_date = raw.get("date")
        entry_theme = raw.get("theme")
        entry_row = raw.get("row")
        loc_date = entry_date if isinstance(entry_date, str) and entry_date else f"entry #{i + 1}"
        loc_theme = entry_theme if isinstance(entry_theme, str) else ""

        if missing:
            diags.append(err("missing-field",
                              f"Entry missing required field(s): {', '.join(missing)}",
                              loc_date, loc_theme))
        if extra:
            diags.append(err("extra-field",
                              f"Entry has unexpected field(s): {', '.join(extra)}",
                              loc_date, loc_theme))

        for field_name, value in (("date", entry_date), ("theme", entry_theme), ("row", entry_row)):
            if field_name not in raw:
                continue
            if not isinstance(value, str):
                diags.append(err("field-type", f"Field '{field_name}' must be a string",
                                  loc_date, loc_theme))
            elif value == "":
                diags.append(err("field-empty", f"Field '{field_name}' must not be empty",
                                  loc_date, loc_theme))

        date_obj = None
        if isinstance(entry_date, str) and entry_date:
            if not DATE_RE.match(entry_date):
                diags.append(err("date-format", f"Date '{entry_date}' is not canonical YYYY-MM-DD",
                                  entry_date, loc_theme))
            else:
                try:
                    y, mo, d = (int(p) for p in entry_date.split("-"))
                    date_obj = date(y, mo, d)
                except ValueError:
                    diags.append(err("date-invalid", f"Date '{entry_date}' is not a valid calendar date",
                                      entry_date, loc_theme))

        parsed.append({
            "index": i,
            "date_str": entry_date if isinstance(entry_date, str) and entry_date else None,
            "theme": entry_theme if isinstance(entry_theme, str) and entry_theme else None,
            "row": entry_row if isinstance(entry_row, str) and entry_row else None,
            "date_obj": date_obj,
            "primary_answers": None,   # filled in below, list of 5 (str or None)
            "final_word": None,       # filled in below
        })

    # ── Publishing range ──────────────────────────────────────────────────
    start_raw = publishing_range.get("start") if isinstance(publishing_range, dict) else None
    end_raw = publishing_range.get("end") if isinstance(publishing_range, dict) else None
    range_diags = []
    range_start = _validate_date_field(start_raw, "start", range_diags)
    range_end = _validate_date_field(end_raw, "end", range_diags)
    diags.extend(range_diags)

    range_usable = range_start is not None and range_end is not None
    if range_usable and range_start > range_end:
        diags.append(err("range-order",
                          f"Publishing range start ({start_raw}) is after end ({end_raw})"))
        range_usable = False

    # ── Duplicate dates (rule 5) ──────────────────────────────────────────
    by_date = {}
    for e in parsed:
        if e["date_obj"] is not None:
            by_date.setdefault(e["date_str"], []).append(e)
    for date_str, group in by_date.items():
        if len(group) > 1:
            themes = [g["theme"] or "?" for g in group]
            diags.append(err("duplicate-date",
                              f"Date declared {len(group)} times (themes: {', '.join(themes)})",
                              date_str, "/".join(themes)))

    # ── Entry ordering, newest-to-oldest (rule 6) ─────────────────────────
    dated_sequence = [e for e in parsed if e["date_obj"] is not None]
    for prev, cur in zip(dated_sequence, dated_sequence[1:]):
        if cur["date_obj"] > prev["date_obj"]:
            diags.append(err("order",
                             f"Entry ordering is not newest-to-oldest: "
                             f"{cur['date_str']} appears after {prev['date_str']}",
                             cur["date_str"], cur["theme"] or ""))

    # ── Missing dates inside the declared inclusive range (rule 7) ────────
    if range_usable:
        declared = {e["date_obj"] for e in parsed if e["date_obj"] is not None}
        cur = range_start
        while cur <= range_end:
            if cur not in declared:
                diags.append(err("missing-date",
                                  f"No puzzle declared for {cur.isoformat()} within "
                                  f"publishing range {start_raw}..{end_raw}",
                                  cur.isoformat()))
            cur += timedelta(days=1)

    # ── Row-level validation (rules 8-13) ─────────────────────────────────
    scramble_records = []  # (answer, scrambled, entry_date, theme) for warning 4

    for e in parsed:
        if e["row"] is None:
            continue

        loc_date = e["date_str"] or ""
        loc_theme = e["theme"] or ""

        items_raw = [s.strip() for s in e["row"].split(",")]
        if len(items_raw) != 6:
            diags.append(err("row-item-count",
                              f"Row must have exactly 6 comma-separated items "
                              f"(5 primary + 1 final), got {len(items_raw)}",
                              loc_date, loc_theme))
            continue

        items = [s.upper() for s in items_raw]
        final_item = items[5]

        if "*" in final_item:
            diags.append(err("marker-in-final",
                              f"Final item \"{final_item}\" must not contain a marker",
                              loc_date, loc_theme))

        final_word = final_item.replace("*", "")
        final_ok = bool(ANSWER_RE.match(final_word))
        if not final_ok:
            diags.append(err("answer-letters",
                              f"Final word \"{final_word}\" must be exactly 6 ASCII letters",
                              loc_date, loc_theme))

        primary_answers = []
        primary_bonus_indices = []
        for wi in range(5):
            raw_item = items[wi]
            answer, bonus_idx, grammar_ok = _parse_row_markers(raw_item)
            if not ANSWER_RE.match(answer):
                diags.append(err("answer-letters",
                                  f"Word {wi + 1} \"{answer}\" must be exactly 6 ASCII letters",
                                  loc_date, loc_theme))
                primary_answers.append(None)
                primary_bonus_indices.append([])
                continue

            if not grammar_ok:
                diags.append(err("invalid-marker-placement",
                                  f"Word {wi + 1} (\"{answer}\") has a marker that does not "
                                  f"immediately follow a previously unmarked answer letter "
                                  f"(leading marker or consecutive markers)",
                                  loc_date, loc_theme))

            primary_answers.append(answer)
            primary_bonus_indices.append(bonus_idx)

        total_markers = sum(len(b) for b in primary_bonus_indices)
        if total_markers != 6:
            diags.append(err("marker-count",
                              f"Expected exactly 6 marked/circled letters across the 5 "
                              f"primary answers, found {total_markers}",
                              loc_date, loc_theme))

        if final_ok:
            bonus_letters = []
            for ans, idxs in zip(primary_answers, primary_bonus_indices):
                if ans is None:
                    continue
                for idx in idxs:
                    bonus_letters.append(ans[idx])
            if sorted(bonus_letters) != sorted(final_word):
                diags.append(err("anagram-mismatch",
                                  f"Marked letters \"{''.join(bonus_letters)}\" are not an "
                                  f"anagram of final word \"{final_word}\"",
                                  loc_date, loc_theme))

        valid_answers = [a for a in primary_answers if a is not None]
        seen_answers = set()
        repeated_answers = set()
        for a in valid_answers:
            if a in seen_answers:
                repeated_answers.add(a)
            seen_answers.add(a)
        for a in sorted(repeated_answers):
            diags.append(err("repeated-answer-in-puzzle",
                              f"Primary answer \"{a}\" is repeated within the same puzzle",
                              loc_date, loc_theme))

        if e["date_str"]:
            for wi, ans in enumerate(primary_answers):
                if ans is None:
                    continue
                seed = e["date_str"] + str(wi)
                scrambled = deterministic_scramble(ans, seed)
                if scrambled == ans:
                    diags.append(err("scramble-identical-to-answer",
                                      f"Word {wi + 1} (\"{ans}\") scrambles to itself "
                                      f"(\"{scrambled}\")",
                                      loc_date, loc_theme))
                else:
                    scramble_records.append((ans, scrambled, loc_date, loc_theme))

        all_primary_valid = len(valid_answers) == 5 and all(a is not None for a in primary_answers)
        if all_primary_valid and final_ok:
            e["primary_answers"] = primary_answers
            e["final_word"] = final_word

    # ── Duplicate puzzle across dates (rule 14) ───────────────────────────
    signature_groups = {}
    for e in parsed:
        if e["primary_answers"] is None or e["final_word"] is None:
            continue
        signature = (tuple(sorted(e["primary_answers"])), e["final_word"])
        signature_groups.setdefault(signature, []).append(e)

    for group in signature_groups.values():
        if len(group) < 2:
            continue
        first = group[0]
        for other in group[1:]:
            diags.append(err("duplicate-puzzle",
                              f"Puzzle on {other['date_str']} (\"{other['theme']}\") has the same "
                              f"primary-answer set and final word as the puzzle on "
                              f"{first['date_str']} (\"{first['theme']}\")",
                              other["date_str"], other["theme"] or ""))

    # ── Non-blocking quality warnings ──────────────────────────────────────

    # Warning 1: theme repeated.
    theme_occurrences = {}
    for e in parsed:
        if e["theme"] and e["date_obj"] is not None:
            theme_occurrences.setdefault(e["theme"], []).append((e["date_obj"], e["date_str"], e["index"]))
    for theme, occurrences in theme_occurrences.items():
        occurrences.sort(key=lambda t: (t[0], t[2]))
        for (prev_obj, prev_str, _), (cur_obj, cur_str, _) in zip(occurrences, occurrences[1:]):
            if cur_obj == prev_obj:
                continue
            days = (cur_obj - prev_obj).days
            diags.append(warn("theme-repeated",
                               f"Theme \"{theme}\" repeated {days} day(s) after {prev_str}",
                               cur_str, theme))

    # Warning 2 & 3: primary answer / final word reused from an earlier puzzle.
    ordered = sorted(
        [e for e in parsed if e["date_obj"] is not None],
        key=lambda e: (e["date_obj"], e["index"]),
    )

    last_seen_answer = {}
    last_seen_final = {}
    for e in ordered:
        if e["primary_answers"] is not None:
            for ans in e["primary_answers"]:
                prev = last_seen_answer.get(ans)
                if prev is not None and prev[0] < e["date_obj"]:
                    days = (e["date_obj"] - prev[0]).days
                    diags.append(warn("answer-reused",
                                       f"Primary answer \"{ans}\" previously appeared on "
                                       f"{prev[1]} ({days} day(s) earlier)",
                                       e["date_str"], e["theme"] or ""))
                last_seen_answer[ans] = (e["date_obj"], e["date_str"])

        if e["final_word"] is not None:
            fw = e["final_word"]
            prev = last_seen_final.get(fw)
            if prev is not None and prev[0] < e["date_obj"]:
                days = (e["date_obj"] - prev[0]).days
                diags.append(warn("final-reused",
                                   f"Final word \"{fw}\" previously used on "
                                   f"{prev[1]} ({days} day(s) earlier)",
                                   e["date_str"], e["theme"] or ""))
            last_seen_final[fw] = (e["date_obj"], e["date_str"])

    # Warning 4: scramble preserves an obvious 4-letter contiguous sequence.
    for answer, scrambled, loc_date, loc_theme in scramble_records:
        reversed_answer = answer[::-1]
        seen_sequences = set()
        for i in range(len(scrambled) - 3):
            window = scrambled[i:i + 4]
            if window in seen_sequences:
                continue
            if window in answer or window in reversed_answer:
                seen_sequences.add(window)
                diags.append(warn("scramble-preserves-sequence",
                                   f"Scramble \"{scrambled}\" of answer \"{answer}\" preserves "
                                   f"the 4-letter sequence \"{window}\"",
                                   loc_date, loc_theme))

    return diags


# ─── CLI ────────────────────────────────────────────────────────────────────

def _sort_key(d):
    return (d.severity != "ERROR", d.entry_date or "", d.rule, d.message)


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT_DATA_PATH
    publishing_range, entries, extraction_diags = load_source(path)
    diags = list(extraction_diags)
    diags.extend(validate(publishing_range, entries))

    for d in sorted(diags, key=_sort_key):
        print(d.format())

    errors = [d for d in diags if d.severity == "ERROR"]
    warnings = [d for d in diags if d.severity == "WARNING"]
    entry_count = len(entries) if isinstance(entries, list) else 0

    print()
    print(f"Summary: {entry_count} entrie(s), {len(errors)} error(s), {len(warnings)} warning(s)")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
