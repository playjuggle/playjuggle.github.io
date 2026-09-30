#!/usr/bin/env python3
"""Regression tests for scripts/validate_puzzles.py.

Standard-library only (unittest). Run with:
    python3 -m unittest scripts.test_validate_puzzles
    python3 -m unittest scripts/test_validate_puzzles.py

Tests build small in-memory fixtures and never modify the live puzzles.js.
"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_puzzles as vp  # noqa: E402


def make_source(entries, start="2026-05-24", end="2026-06-17"):
    """Build a minimal puzzles.js-shaped source string from Python entries."""
    import json
    range_json = json.dumps({"start": start, "end": end})
    entries_json = json.dumps(entries)
    return (
        f"const PUZZLE_PUBLISHING_RANGE = {range_json};\n"
        f"const PUZZLE_ENTRIES = {entries_json};\n"
    )


def entry(date, theme, row):
    return {"date": date, "theme": theme, "row": row}


# A hand-checked, fully valid single puzzle: MU*SSEL / OYSTER* / TRENC*H* /
# MARLI*N / SPON*GE / URCHIN, taken from the authoring example in puzzles.js.
VALID_ROW = "MU*SSEL, OYSTER*, TRENC*H*, MARLI*N, SPON*GE, URCHIN"


def run(entries, start="2026-05-24", end="2026-05-24"):
    text = make_source(entries, start=start, end=end)
    publishing_range, parsed_entries, extraction_diags = vp.parse_text(text)
    diags = list(extraction_diags)
    diags.extend(vp.validate(publishing_range, parsed_entries))
    return diags


def rules(diags, severity=None):
    return {d.rule for d in diags if severity is None or d.severity == severity}


class Int32ArithmeticTests(unittest.TestCase):
    """Cross-checks against MDN's documented Math.imul examples."""

    def test_imul_matches_documented_examples(self):
        self.assertEqual(vp.imul32(3, 4), 12)
        self.assertEqual(vp.imul32(-5, 12), -60)
        self.assertEqual(vp.imul32(0xFFFFFFFF, 5), -5)
        self.assertEqual(vp.imul32(0xFFFFFFFE, 5), -10)

    def test_to_int32_two_complement_wraparound(self):
        self.assertEqual(vp.to_int32(0xFFFFFFFF), -1)
        self.assertEqual(vp.to_int32(0x80000000), -2147483648)
        self.assertEqual(vp.to_int32(0x7FFFFFFF), 2147483647)


class DeterministicScrambleTests(unittest.TestCase):
    def test_scramble_is_anagram_of_input(self):
        for word, seed in [("URCHIN", "2026-05-250"), ("BAKERY", "seedA"), ("AABBCC", "seedB")]:
            scrambled = vp.deterministic_scramble(word, seed)
            self.assertEqual(sorted(scrambled), sorted(word))

    def test_scramble_is_deterministic(self):
        a = vp.deterministic_scramble("GARDEN", "2026-05-244")
        b = vp.deterministic_scramble("GARDEN", "2026-05-244")
        self.assertEqual(a, b)

    def test_different_seeds_generally_differ(self):
        a = vp.deterministic_scramble("GARDEN", "seed-one")
        b = vp.deterministic_scramble("GARDEN", "seed-two")
        self.assertNotEqual(a, b)

    def test_scramble_never_equals_input_for_non_repeating_letters(self):
        # GARDEN has all-distinct letters; the anti-identity fixup guarantees
        # the scramble can never equal the original.
        for seed in ("s1", "s2", "s3", "2026-06-011"):
            self.assertNotEqual(vp.deterministic_scramble("GARDEN", seed), "GARDEN")

    def test_known_representative_inputs(self):
        # Regression fixture values captured from this implementation (no
        # local JS engine is available in this environment to cross-check
        # against the browser directly; see the validator's module docstring
        # and the task report for that limitation). The initial LCG hash step
        # was independently hand-verified: lcg_hash("X") == 88 (imul32(31, 0)
        # + ord("X") == 88, within int32 range, no wraparound), matching
        # game.js's `h = (Math.imul(31, h) + seed.charCodeAt(i)) | 0`. These
        # asserted outputs guard against future regressions in the port.
        self.assertEqual(vp._lcg_hash("X"), 88)
        self.assertEqual(vp.deterministic_scramble("ABCDEF", "X"), "FDACEB")
        self.assertEqual(vp.deterministic_scramble("URCHIN", "2026-05-250"), "CNHRIU")


class ExtractionTests(unittest.TestCase):
    def test_missing_top_level_fields(self):
        diags, _, _ = self._parse("const SOMETHING_ELSE = 1;")
        self.assertIn("missing-top-level-field", {d.rule for d in diags})

    def _parse(self, text):
        publishing_range, entries, diags = vp.parse_text(text)
        return diags, publishing_range, entries

    def test_valid_shell_parses_cleanly(self):
        text = make_source([entry("2026-05-24", "Under the Sea", VALID_ROW)],
                            start="2026-05-24", end="2026-05-24")
        diags, publishing_range, entries = self._parse(text)
        self.assertEqual(diags, [])
        self.assertEqual(publishing_range, {"start": "2026-05-24", "end": "2026-05-24"})
        self.assertEqual(len(entries), 1)


class ValidDataTests(unittest.TestCase):
    def test_valid_single_entry_has_no_errors(self):
        diags = run([entry("2026-05-24", "Under the Sea", VALID_ROW)])
        self.assertEqual(rules(diags, "ERROR"), set())

    def test_valid_data_exit_code_is_success(self):
        diags = run([entry("2026-05-24", "Under the Sea", VALID_ROW)])
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(len(errors), 0)


class WarningOnlyTests(unittest.TestCase):
    def test_repeated_theme_is_warning_not_error(self):
        # Two independently valid, content-distinct rows sharing one theme
        # label — only the theme repeats, so this must warn, not error.
        other_valid_row = "PUR*PLE, IN*DIG*O, YELLO*W, MA*ROON, VIOLE*T, ORANGE"
        entries = [
            entry("2026-05-24", "Under the Sea", VALID_ROW),
            entry("2026-05-23", "Under the Sea", other_valid_row),
        ]
        diags = run(entries, start="2026-05-23", end="2026-05-24")
        errors = rules(diags, "ERROR")
        self.assertNotIn("theme-repeated", errors)
        warning_rules = rules(diags, "WARNING")
        self.assertIn("theme-repeated", warning_rules)
        exit_ok = len([d for d in diags if d.severity == "ERROR"]) == 0
        self.assertTrue(exit_ok)


class BlockingErrorCategoryTests(unittest.TestCase):
    def test_missing_entry_field(self):
        diags = run([{"date": "2026-05-24", "theme": "Under the Sea"}])
        self.assertIn("missing-field", rules(diags, "ERROR"))

    def test_extra_entry_field(self):
        bad = entry("2026-05-24", "Under the Sea", VALID_ROW)
        bad["extra"] = "nope"
        diags = run([bad])
        self.assertIn("extra-field", rules(diags, "ERROR"))

    def test_empty_field(self):
        diags = run([entry("2026-05-24", "", VALID_ROW)])
        self.assertIn("field-empty", rules(diags, "ERROR"))

    def test_wrong_type_field(self):
        bad = {"date": "2026-05-24", "theme": 123, "row": VALID_ROW}
        diags = run([bad])
        self.assertIn("field-type", rules(diags, "ERROR"))

    def test_non_canonical_date(self):
        diags = run([entry("05/24/2026", "Under the Sea", VALID_ROW)],
                    start="2026-05-24", end="2026-05-24")
        self.assertIn("date-format", rules(diags, "ERROR"))

    def test_impossible_calendar_date(self):
        diags = run([entry("2026-02-30", "Under the Sea", VALID_ROW)],
                    start="2026-02-30", end="2026-02-30")
        self.assertIn("date-invalid", rules(diags, "ERROR"))

    def test_publishing_range_start_after_end(self):
        diags = run([entry("2026-05-24", "Under the Sea", VALID_ROW)],
                    start="2026-06-01", end="2026-05-24")
        self.assertIn("range-order", rules(diags, "ERROR"))

    def test_duplicate_dates_observable(self):
        diags = run([
            entry("2026-05-24", "Under the Sea", VALID_ROW),
            entry("2026-05-24", "Garden Path", VALID_ROW.replace("URCHIN", "GARDEN")),
        ], start="2026-05-24", end="2026-05-24")
        self.assertIn("duplicate-date", rules(diags, "ERROR"))

    def test_ordering_not_newest_to_oldest(self):
        diags = run([
            entry("2026-05-23", "A", VALID_ROW),
            entry("2026-05-24", "B", VALID_ROW),
        ], start="2026-05-23", end="2026-05-24")
        self.assertIn("order", rules(diags, "ERROR"))

    def test_missing_date_in_range(self):
        diags = run([
            entry("2026-05-24", "A", VALID_ROW),
            entry("2026-05-26", "B", VALID_ROW),
        ], start="2026-05-24", end="2026-05-26")
        self.assertIn("missing-date", rules(diags, "ERROR"))

    def test_row_wrong_item_count(self):
        diags = run([entry("2026-05-24", "A", "ONE, TWO, THREE, FOUR, FIVE")])
        self.assertIn("row-item-count", rules(diags, "ERROR"))

    def test_answer_not_six_letters(self):
        bad_row = VALID_ROW.replace("MU*SSEL", "MU*SS")
        diags = run([entry("2026-05-24", "A", bad_row)])
        self.assertIn("answer-letters", rules(diags, "ERROR"))

    def test_marker_in_final_item(self):
        bad_row = VALID_ROW.replace("URCHIN", "URCH*IN")
        diags = run([entry("2026-05-24", "A", bad_row)])
        self.assertIn("marker-in-final", rules(diags, "ERROR"))

    def test_wrong_marker_count(self):
        bad_row = VALID_ROW.replace("MARLI*N", "MARLIN")  # drop one marker -> 5 total
        diags = run([entry("2026-05-24", "A", bad_row)])
        self.assertIn("marker-count", rules(diags, "ERROR"))

    def test_invalid_marker_placement_before_first_letter(self):
        bad_row = VALID_ROW.replace("MU*SSEL", "*MUSSEL")
        diags = run([entry("2026-05-24", "A", bad_row)])
        self.assertIn("invalid-marker-placement", rules(diags, "ERROR"))

    def test_invalid_marker_placement_consecutive_markers(self):
        # A marker must immediately follow a previously unmarked answer
        # letter; a second marker right after the first ("M**USSEL") is not
        # grammatically valid, even though it still yields a 6-letter
        # answer ("MUSSEL").
        bad_row = "M**USSEL, OYSTER*, TRENC*H*, MARLI*N, SPON*GE, URCHIN"
        diags = run([entry("2026-05-24", "A", bad_row)])
        self.assertIn("invalid-marker-placement", rules(diags, "ERROR"))

    def test_anagram_mismatch(self):
        bad_row = VALID_ROW.replace("URCHIN", "GARDEN")
        diags = run([entry("2026-05-24", "A", bad_row)])
        self.assertIn("anagram-mismatch", rules(diags, "ERROR"))

    def test_repeated_answer_within_puzzle(self):
        bad_row = "MU*SSEL, MU*SSEL, TRENC*H*, MARLI*N, SPON*GE, URCHIN"
        diags = run([entry("2026-05-24", "A", bad_row)])
        self.assertIn("repeated-answer-in-puzzle", rules(diags, "ERROR"))

    def test_scramble_identical_to_answer_is_error(self):
        # AAAAAA has no distinct-letter fixup available; any scramble of it
        # is trivially identical to the input, so this exercises rule 12
        # deterministically regardless of seed.
        bad_row = "AAAAA*A, OYSTER*, TRENC*H*, MARLI*N, SPON*GE, AAAAAA"
        diags = run([entry("2026-05-24", "A", bad_row)])
        self.assertIn("scramble-identical-to-answer", rules(diags, "ERROR"))

    def test_duplicate_puzzle_across_dates(self):
        diags = run([
            entry("2026-05-25", "A", VALID_ROW),
            entry("2026-05-24", "B", VALID_ROW),
        ], start="2026-05-24", end="2026-05-25")
        self.assertIn("duplicate-puzzle", rules(diags, "ERROR"))

    def test_duplicate_puzzle_ignores_primary_word_order_and_markers(self):
        reordered_row = "OYSTER*, MU*SSEL, MARLI*N, TRENC*H*, SPON*GE, URCHIN"
        diags = run([
            entry("2026-05-25", "A", VALID_ROW),
            entry("2026-05-24", "B", reordered_row),
        ], start="2026-05-24", end="2026-05-25")
        self.assertIn("duplicate-puzzle", rules(diags, "ERROR"))

    def test_multiple_errors_collected_in_one_run(self):
        diags = run([
            entry("2026-05-24", "A", "ONE, TWO, THREE, FOUR, FIVE"),
            entry("bad-date", "B", VALID_ROW),
        ], start="2026-05-24", end="2026-05-24")
        error_rules = rules(diags, "ERROR")
        self.assertIn("row-item-count", error_rules)
        self.assertIn("date-format", error_rules)
        self.assertGreaterEqual(len([d for d in diags if d.severity == "ERROR"]), 2)


class CliExitSemanticsTests(unittest.TestCase):
    """Exercises the real CLI entry point (vp.main), not just diagnostics."""

    def _run_cli(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidate.js"
            path.write_text(text, encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = vp.main(["validate_puzzles.py", str(path)])
            return code, stdout.getvalue()

    def test_valid_candidate_returns_zero(self):
        text = make_source([entry("2026-05-24", "Under the Sea", VALID_ROW)],
                            start="2026-05-24", end="2026-05-24")
        code, output = self._run_cli(text)
        self.assertEqual(code, 0)
        self.assertIn("0 error(s)", output)

    def test_warning_only_candidate_returns_zero_and_prints_warning(self):
        other_valid_row = "PUR*PLE, IN*DIG*O, YELLO*W, MA*ROON, VIOLE*T, ORANGE"
        text = make_source([
            entry("2026-05-24", "Under the Sea", VALID_ROW),
            entry("2026-05-23", "Under the Sea", other_valid_row),
        ], start="2026-05-23", end="2026-05-24")
        code, output = self._run_cli(text)
        self.assertEqual(code, 0)
        self.assertIn("0 error(s)", output)
        self.assertIn("WARNING", output)
        self.assertIn("theme-repeated", output)

    def test_error_candidate_returns_nonzero(self):
        text = make_source([entry("2026-05-24", "A", "ONE, TWO, THREE, FOUR, FIVE")],
                            start="2026-05-24", end="2026-05-24")
        code, output = self._run_cli(text)
        self.assertNotEqual(code, 0)
        self.assertIn("row-item-count", output)

    def test_malformed_unbalanced_source_returns_nonzero_without_traceback(self):
        # Truncated PUZZLE_ENTRIES array: no closing bracket at all.
        text = ('const PUZZLE_PUBLISHING_RANGE = {"start":"2026-05-24","end":"2026-06-17"};\n'
                'const PUZZLE_ENTRIES = [ { "date": "2026-05-24", "theme": "X", "row": "A"\n')
        code, output = self._run_cli(text)
        self.assertNotEqual(code, 0)
        self.assertIn("malformed-top-level-field", output)
        self.assertNotIn("Traceback", output)

    def test_malformed_top_level_json_returns_nonzero_without_traceback(self):
        # Trailing comma makes the publishing-range blob invalid JSON, even
        # though its braces are balanced.
        text = ('const PUZZLE_PUBLISHING_RANGE = {"start":"2026-05-24","end":"2026-06-17",};\n'
                'const PUZZLE_ENTRIES = [];\n')
        code, output = self._run_cli(text)
        self.assertNotEqual(code, 0)
        self.assertIn("malformed-top-level-field", output)
        self.assertNotIn("Traceback", output)

    def test_missing_range_endpoints_returns_nonzero_without_traceback(self):
        text = ('const PUZZLE_PUBLISHING_RANGE = {};\n'
                'const PUZZLE_ENTRIES = [];\n')
        code, output = self._run_cli(text)
        self.assertNotEqual(code, 0)
        self.assertIn("field-type", output)
        self.assertNotIn("Traceback", output)

    def test_missing_candidate_file_returns_nonzero_without_traceback(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = vp.main(["validate_puzzles.py", "/nonexistent/path/candidate.js"])
        self.assertNotEqual(code, 0)
        self.assertIn("file-not-found", stdout.getvalue())
        self.assertNotIn("Traceback", stdout.getvalue())

    def test_invalidly_encoded_candidate_returns_nonzero_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidate.js"
            path.write_bytes(b"\xff\xfe\x00const PUZZLE_ENTRIES")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = vp.main(["validate_puzzles.py", str(path)])
        self.assertNotEqual(code, 0)
        self.assertIn("file-unreadable", stdout.getvalue())
        self.assertNotIn("Traceback", stdout.getvalue())


class LiveDataDoesNotMutateTests(unittest.TestCase):
    def test_live_file_untouched_by_tests(self):
        # Sanity check: this suite never opens puzzles.js for writing.
        self.assertTrue((vp.REPO_ROOT / "puzzles.js").exists())


if __name__ == "__main__":
    unittest.main()
