#!/usr/bin/env python3
"""Safe, standard-library-only batch check-and-promote workflow for Juggle
puzzle data.

Reuses scripts/validate_puzzles.py as the single source of truth for every
content rule (date/row/marker/anagram/duplicate/ordering/schedule-gap
checks). This tool adds only the batch-specific mechanics around it: strict
JSON candidate loading, an append-only schedule-boundary check against the
live file, and an atomic, verbatim-preserving promotion of a fully clean
batch.

This is the first (and, for now, only) workflow: append-only. Every
candidate date must extend the live schedule by exactly one contiguous run
starting the day after the current live PUZZLE_PUBLISHING_RANGE.end.
Overlap, replacement, historical edits, gaps, and changes to the live start
are always refused.

Commands:
    python3 scripts/manage_puzzle_batch.py check path/to/batch.json
    python3 scripts/manage_puzzle_batch.py apply path/to/batch.json

`check` only ever reads; it never writes. `apply` writes only when every
ERROR-severity diagnostic (from either validation pass) is absent; WARNING
diagnostics are printed and counted but never block. See
puzzle-batches/README.md for the full JSON format and an authoring
template.
"""

import argparse
import json
import os
import stat
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_puzzles as vp  # noqa: E402

BATCH_TOP_LEVEL_FIELDS = ("start", "end", "entries")

EPILOG = """\
Batch JSON format:
  {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD",
    "entries": [
      {"date": "YYYY-MM-DD", "theme": "...", "row": "W1, W2, W3, W4, W5, FINAL"}
    ]
  }
Entries are newest-to-oldest, matching puzzles.js (so the first entry's date
is "end" and the last entry's date is "start"). See puzzle-batches/README.md
for the full authoring guide and a documented, intentionally-non-live
template.

Blocking vs warning: every diagnostic scripts/validate_puzzles.py would
report as ERROR blocks `apply` (and makes `check` exit nonzero). WARNING
diagnostics are printed and counted but never block either command.

Append-only boundary: the batch's "start" must equal the live
PUZZLE_PUBLISHING_RANGE.end plus exactly one calendar day, "entries" must
cover every day through "end" with no gaps, and no candidate date may fall
on or before the live end. Overlap, replacement, historical edits, gaps, and
changes to the live start are always refused.

Commands:
  check <batch.json>   Validate only; never writes.
  apply <batch.json>   Validate, then atomically promote into --target
                        (default: repository-root puzzles.js) if, and only
                        if, every blocking check passes. Preserves every
                        existing live entry and all surrounding file content
                        verbatim; only PUZZLE_PUBLISHING_RANGE and
                        PUZZLE_ENTRIES change.

Safe next steps after a clean apply: re-run
`python3 scripts/validate_puzzles.py` against the updated target, review the
diff by hand, then commit/deploy as a separate, explicit step — this tool
never commits, pushes, installs anything, or deploys.
"""


# ─── Batch loading (structural schema only; content rules are vp's job) ───────

def load_batch(path):
    """Read and schema-check a batch JSON file.

    Returns (batch_dict_or_None, diagnostics). Never raises for a missing,
    unreadable, or malformed file. Only checks the batch's own top-level
    shape (valid JSON, an object with exactly start/end/entries, entries a
    non-empty list); per-entry and date-format content is left to
    scripts/validate_puzzles.py so those rules are never duplicated.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, [vp.err("batch-file-not-found", f"Batch file not found: {path}")]
    except IsADirectoryError:
        return None, [vp.err("batch-unreadable", f"Batch path is a directory, not a file: {path}")]
    except UnicodeDecodeError as e:
        return None, [vp.err("batch-unreadable", f"Batch file is not valid UTF-8 text ({path}): {e}")]
    except OSError as e:
        return None, [vp.err("batch-unreadable", f"Batch file could not be read ({path}): {e}")]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return None, [vp.err("batch-invalid-json", f"Batch file is not valid JSON: {e}")]

    if not isinstance(data, dict):
        return None, [vp.err("batch-top-level-type",
                              "Batch JSON must be an object with 'start', 'end', 'entries'")]

    missing = [f for f in BATCH_TOP_LEVEL_FIELDS if f not in data]
    extra = sorted(set(data.keys()) - set(BATCH_TOP_LEVEL_FIELDS))
    diags = []
    if missing:
        diags.append(vp.err("batch-missing-field",
                             f"Batch is missing required field(s): {', '.join(missing)}"))
    if extra:
        diags.append(vp.err("batch-extra-field",
                             f"Batch has unexpected top-level field(s): {', '.join(extra)}"))
    if diags:
        return None, diags

    entries_raw = data["entries"]
    if not isinstance(entries_raw, list):
        return None, [vp.err("batch-entries-type", "Batch 'entries' must be a list")]
    if len(entries_raw) == 0:
        return None, [vp.err("batch-entries-empty", "Batch 'entries' must not be empty")]

    return data, []


# ─── Live target loading (extraction only; full content validation happens
#     implicitly via the merged pass below, per the "validate twice" rule) ────

def _load_live(path):
    try:
        # Decode bytes directly: read_text() normalizes CRLF on Windows,
        # which would break the exact target-change check and verbatim
        # preservation promised by apply.
        text = Path(path).read_bytes().decode("utf-8")
    except FileNotFoundError:
        return None, None, None, [vp.err("live-file-not-found", f"Target file not found: {path}")]
    except IsADirectoryError:
        return None, None, None, [vp.err("live-unreadable", f"Target path is a directory, not a file: {path}")]
    except UnicodeDecodeError as e:
        return None, None, None, [vp.err("live-unreadable", f"Target file is not valid UTF-8 text ({path}): {e}")]
    except OSError as e:
        return None, None, None, [vp.err("live-unreadable", f"Target file could not be read ({path}): {e}")]

    publishing_range, entries, diags = vp.parse_text(text)
    diags = list(diags)

    if not isinstance(publishing_range, dict) or not isinstance(publishing_range.get("start"), str) \
            or not isinstance(publishing_range.get("end"), str):
        if not diags:
            diags.append(vp.err("live-range-invalid",
                                 "Live PUZZLE_PUBLISHING_RANGE must be an object with string 'start'/'end'"))
        publishing_range = None
    if not isinstance(entries, list):
        if not diags:
            diags.append(vp.err("live-entries-invalid", "Live PUZZLE_ENTRIES must be a list"))
        entries = None

    return text, publishing_range, entries, diags


def _parse_simple_date(value):
    if not isinstance(value, str) or not vp.DATE_RE.match(value):
        return None
    try:
        y, mo, d = (int(p) for p in value.split("-"))
        return date(y, mo, d)
    except ValueError:
        return None


# ─── Evaluation: batch schema -> isolation validate -> append-only boundary
#     -> merged validate. Shared by both `check` and `apply`. ─────────────────

def evaluate_batch(batch_path, target_path):
    """Run the full two-pass validation pipeline.

    Returns (diagnostics, context). context is None whenever apply cannot
    safely proceed (batch or live target could not be loaded/parsed);
    otherwise it carries the merged range/entries and the live file's exact
    original text for apply() to render and splice into, without re-deriving
    any of this evaluation.
    """
    diags = []

    batch, batch_diags = load_batch(batch_path)
    diags.extend(batch_diags)
    if batch is None:
        return diags, None

    candidate_range = {"start": batch["start"], "end": batch["end"]}
    candidate_entries = batch["entries"]
    diags.extend(vp.validate(candidate_range, candidate_entries))

    live_text, live_range, live_entries, live_diags = _load_live(target_path)
    diags.extend(live_diags)
    if live_range is None or live_entries is None:
        return diags, None

    batch_start = _parse_simple_date(batch["start"])
    batch_end = _parse_simple_date(batch["end"])
    live_end = _parse_simple_date(live_range["end"])

    if batch_start is not None and live_end is not None:
        expected_start = live_end + timedelta(days=1)
        if batch_start != expected_start:
            diags.append(vp.err(
                "batch-start-not-contiguous",
                f"Batch start ({batch['start']}) must be exactly one day after the live "
                f"publishing range end ({live_range['end']}); expected {expected_start.isoformat()}"))

        overlapping = sorted({
            e["date"] for e in candidate_entries
            if isinstance(e, dict) and isinstance(e.get("date"), str)
            and (d := _parse_simple_date(e["date"])) is not None and d <= live_end
        })
        for d_str in overlapping:
            diags.append(vp.err(
                "batch-overlaps-live",
                f"Batch entry date {d_str} is not strictly after the live publishing "
                f"range end ({live_range['end']})", d_str))

    merged_range = None
    merged_entries = None
    if batch_end is not None:
        merged_range = {"start": live_range["start"], "end": batch["end"]}
        merged_entries = list(candidate_entries) + list(live_entries)
        diags.extend(vp.validate(merged_range, merged_entries))

    context = {
        "batch": batch,
        "live_text": live_text,
        "merged_range": merged_range,
        "merged_entries": merged_entries,
    }
    return diags, context


# ─── Rendering (splice-only: only the two declaration spans change) ───────────

def _render_entry_line(entry):
    date_ = json.dumps(entry["date"])
    theme = json.dumps(entry["theme"])
    row = json.dumps(entry["row"])
    return f'  {{ "date": {date_}, "theme": {theme}, "row": {row} }}'


def _render_range_blob(range_obj):
    start = json.dumps(range_obj["start"])
    end = json.dumps(range_obj["end"])
    return f'{{\n  "start": {start},\n  "end": {end}\n}}'


def _render_entries_blob(entries):
    body = ",\n".join(_render_entry_line(e) for e in entries)
    return f'[\n{body}\n]'


def _render_target(original_text, merged_range, new_entries):
    """Return original_text with only the two declaration spans replaced.

    Returns (new_text_or_None, error_message_or_None). Uses the same
    balanced-bracket span locator as the validator (not a regex-only
    replacement) so declaration boundaries are deterministic.
    """
    range_start, range_end, range_err = vp._locate_balanced_span(
        original_text, "PUZZLE_PUBLISHING_RANGE", "{", "}")
    entries_start, entries_end, entries_err = vp._locate_balanced_span(
        original_text, "PUZZLE_ENTRIES", "[", "]")

    if range_err or range_start is None:
        return None, range_err or "'PUZZLE_PUBLISHING_RANGE' declaration not found in target"
    if entries_err or entries_start is None:
        return None, entries_err or "'PUZZLE_ENTRIES' declaration not found in target"

    original_entries = original_text[entries_start:entries_end]
    newline = "\r\n" if "\r\n" in original_entries else "\n"
    # Insert only the new declarations. Re-rendering the merged data changes
    # every existing declaration's source bytes even when its value is equal.
    if original_entries[1:].startswith(newline):
        insertion_at = 1 + len(newline)
        insertion = ("," + newline).join(_render_entry_line(e) for e in new_entries) + "," + newline
    else:
        insertion_at = 1
        insertion = ", ".join(_render_entry_line(e).strip() for e in new_entries) + ", "
    entries_blob = (original_entries[:insertion_at] + insertion
                    + original_entries[insertion_at:])

    replacements = sorted(
        [
            (range_start, range_end, _render_range_blob(merged_range)),
            (entries_start, entries_end, entries_blob),
        ],
        key=lambda t: t[0],
        reverse=True,
    )
    new_text = original_text
    for start, end, blob in replacements:
        new_text = new_text[:start] + blob + new_text[end:]
    return new_text, None


# ─── Reporting ─────────────────────────────────────────────────────────────────

def _print_diags(diags):
    for d in sorted(diags, key=vp._sort_key):
        print(d.format())


def _summarize(diags, label):
    errors = [d for d in diags if d.severity == "ERROR"]
    warnings = [d for d in diags if d.severity == "WARNING"]
    print()
    print(f"{label}: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


# ─── Commands ───────────────────────────────────────────────────────────────────

def cmd_check(args):
    diags, _context = evaluate_batch(args.batch, args.target)
    _print_diags(diags)
    return _summarize(diags, "Check")


def cmd_apply(args):
    diags, context = evaluate_batch(args.batch, args.target)
    errors = [d for d in diags if d.severity == "ERROR"]
    if errors or context is None:
        _print_diags(diags)
        return _summarize(diags, "Apply refused")

    target_path = Path(args.target)
    original_text = context["live_text"]
    original_bytes = original_text.encode("utf-8")
    merged_range = context["merged_range"]
    merged_entries = context["merged_entries"]
    new_entries = context["batch"]["entries"]

    new_text, render_err = _render_target(original_text, merged_range, new_entries)
    if render_err is not None:
        diags.append(vp.err("apply-render-failed",
                             f"Could not render the updated target; refusing to write: {render_err}"))
        _print_diags(diags)
        return _summarize(diags, "Apply refused")

    # Revalidate the exact rendered candidate target before replacement.
    rendered_range, rendered_entries, rendered_extract_diags = vp.parse_text(new_text)
    revalidation_diags = list(rendered_extract_diags)
    if rendered_range is not None and rendered_entries is not None:
        revalidation_diags.extend(vp.validate(rendered_range, rendered_entries))
    if any(d.severity == "ERROR" for d in revalidation_diags):
        diags.append(vp.err("apply-revalidation-failed",
                             "Rendered target failed revalidation; refusing to write"))
        diags.extend(revalidation_diags)
        _print_diags(diags)
        return _summarize(diags, "Apply refused")

    # Refuse if the target changed on disk since it was read.
    try:
        current_bytes = target_path.read_bytes()
    except OSError as e:
        diags.append(vp.err("target-changed", f"Target file could not be re-read before writing: {e}"))
        _print_diags(diags)
        return _summarize(diags, "Apply refused")
    if current_bytes != original_bytes:
        diags.append(vp.err("target-changed",
                             "Target file changed on disk since it was read; refusing to write"))
        _print_diags(diags)
        return _summarize(diags, "Apply refused")

    try:
        target_mode = stat.S_IMODE(target_path.stat().st_mode)
    except OSError as e:
        diags.append(vp.err("apply-write-failed", f"Could not stat target file before writing: {e}"))
        _print_diags(diags)
        return _summarize(diags, "Apply refused")

    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(target_path.parent), prefix=f".{target_path.name}.", suffix=".tmp")
        # Binary output avoids Windows text-mode newline translation. This
        # keeps untouched surrounding bytes verbatim and makes the replace
        # atomic with respect to the exact rendered UTF-8 bytes.
        with os.fdopen(fd, "wb") as f:
            f.write(new_text.encode("utf-8"))
        os.chmod(tmp_path, target_mode)
        os.replace(tmp_path, target_path)
    except OSError as e:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        diags.append(vp.err("apply-write-failed", f"Could not write the updated target: {e}"))
        _print_diags(diags)
        return _summarize(diags, "Apply refused")

    _print_diags(diags)
    print()
    print(f"Applied batch: merged range {merged_range['start']}..{merged_range['end']}, "
          f"{len(merged_entries)} total entrie(s) ({len(context['batch']['entries'])} new). "
          f"Wrote {target_path}")
    return _summarize(diags, "Apply")


# ─── CLI ────────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="manage_puzzle_batch.py",
        description=(
            "Safe, standard-library-only batch check-and-promote workflow for "
            "Juggle puzzle data (append-only: see below)."
        ),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check", help="Validate a batch file without writing anything.")
    check_parser.add_argument("batch", help="Path to the candidate batch JSON file.")
    check_parser.add_argument(
        "--target", default=str(vp.DEFAULT_DATA_PATH),
        help="Live puzzles.js-shaped file to validate the merge against "
             "(default: repository-root puzzles.js). Never written by `check`.")
    check_parser.set_defaults(func=cmd_check)

    apply_parser = subparsers.add_parser(
        "apply", help="Validate a batch file and, if fully clean, atomically promote it.")
    apply_parser.add_argument("batch", help="Path to the candidate batch JSON file.")
    apply_parser.add_argument(
        "--target", default=str(vp.DEFAULT_DATA_PATH),
        help="File to update in place (default: repository-root puzzles.js). Only "
             "PUZZLE_PUBLISHING_RANGE and PUZZLE_ENTRIES are replaced; everything "
             "else is preserved verbatim.")
    apply_parser.set_defaults(func=cmd_apply)

    return parser


def main(argv):
    parser = build_parser()
    args = parser.parse_args(argv[1:])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
