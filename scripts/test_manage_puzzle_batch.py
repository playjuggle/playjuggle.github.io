#!/usr/bin/env python3
"""Regression tests for scripts/manage_puzzle_batch.py.

Standard-library only (unittest). Run with:
    python3 -m unittest scripts.test_manage_puzzle_batch
    python3 -m unittest scripts/test_manage_puzzle_batch.py

Every test operates on temporary files only; the live repository-root
puzzles.js is never opened for writing.
"""

import contextlib
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import manage_puzzle_batch as mpb  # noqa: E402
import validate_puzzles as vp  # noqa: E402

# Rows taken/adapted from validated, individually hand-checked puzzles (see
# scripts/test_validate_puzzles.py) so their marker/anagram shape is known
# good; each uses a primary-answer set distinct from any other row here and
# from the live puzzles.js content used as LIVE_ENTRIES below.
ROW_SEA = "MU*SSEL, OYSTER*, TRENC*H*, MARLI*N, SPON*GE, URCHIN"
ROW_COLOR = "PUR*PLE, IN*DIG*O, YELLO*W, MA*ROON, VIOLE*T, ORANGE"
ROW_DESERT = "CANYON*, DESERT*, NOMADS*, SAFARI*, VOYAG*E*, SIGNET"

LIVE_HEADER = "// live-header-marker unique-12345\n// second header line\n\n"
LIVE_TRAILER = "\n// live-trailer-marker unique-67890\n"

LIVE_ENTRIES = [
    {"date": "2026-06-17", "theme": "Garden Path",
     "row": "BA*MBOO, CACT*U*S, OR*CHID, GARDEN*, FLOWE*R, NATURE"},
    {"date": "2026-06-16", "theme": "Movie Night",
     "row": "CINEMA*, AC*TIO*N, SCR*EEN, POS*T*ER, CREDIT, ACTORS"},
]
LIVE_START = "2026-06-16"
LIVE_END = "2026-06-17"


def build_live_text(entries=None, start=LIVE_START, end=LIVE_END):
    entries = LIVE_ENTRIES if entries is None else entries
    entry_lines = ",\n".join(
        f'  {{ "date": "{e["date"]}", "theme": "{e["theme"]}", "row": "{e["row"]}" }}'
        for e in entries
    )
    return (
        LIVE_HEADER
        + "const PUZZLE_PUBLISHING_RANGE = {\n"
        f'  "start": "{start}",\n'
        f'  "end": "{end}"\n'
        "};\n\n"
        "const PUZZLE_ENTRIES = [\n"
        f"{entry_lines}\n"
        "];\n"
        + LIVE_TRAILER
    )


def build_batch_json(start, end, entries):
    return json.dumps({"start": start, "end": end, "entries": entries}, indent=2)


class BatchWorkflowTestCase(unittest.TestCase):
    """Base class that wires up a fresh temp dir with a live target per test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)
        self.target = self.tmp_path / "puzzles.js"
        self.target.write_text(build_live_text(), encoding="utf-8")
        self.original_bytes = self.target.read_bytes()

    def write_batch(self, text, name="batch.json"):
        path = self.tmp_path / name
        path.write_text(text, encoding="utf-8")
        return path

    def run_cli(self, *args):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = mpb.main(["manage_puzzle_batch.py", *args])
        return code, stdout.getvalue()

    def assertTargetUnchanged(self):
        self.assertEqual(self.target.read_bytes(), self.original_bytes)


class SchemaErrorTests(BatchWorkflowTestCase):
    def test_malformed_json(self):
        batch = self.write_batch("{not valid json")
        code, output = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("batch-invalid-json", output)
        self.assertTargetUnchanged()

    def test_missing_top_level_fields(self):
        batch = self.write_batch(json.dumps({"start": "2026-06-18"}))
        code, output = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("batch-missing-field", output)

    def test_extra_top_level_fields(self):
        batch = self.write_batch(json.dumps({
            "start": "2026-06-18", "end": "2026-06-18", "entries": [], "extra": True,
        }))
        code, output = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("batch-extra-field", output)

    def test_empty_batch(self):
        batch = self.write_batch(build_batch_json("2026-06-18", "2026-06-18", []))
        code, output = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("batch-entries-empty", output)

    def test_wrong_start_end_format(self):
        batch = self.write_batch(build_batch_json(
            "06-18-2026", "2026-06-18",
            [{"date": "2026-06-18", "theme": "X", "row": ROW_DESERT}]))
        code, output = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("date-format", output)

    def test_start_after_end(self):
        batch = self.write_batch(build_batch_json(
            "2026-06-20", "2026-06-18",
            [{"date": "2026-06-18", "theme": "X", "row": ROW_DESERT},
             {"date": "2026-06-19", "theme": "Y", "row": ROW_COLOR},
             {"date": "2026-06-20", "theme": "Z", "row": ROW_SEA}]))
        code, output = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("range-order", output)


class AppendOnlyBoundaryTests(BatchWorkflowTestCase):
    def test_duplicate_dates_within_batch(self):
        batch = self.write_batch(build_batch_json(
            "2026-06-18", "2026-06-18",
            [{"date": "2026-06-18", "theme": "A", "row": ROW_DESERT},
             {"date": "2026-06-18", "theme": "B", "row": ROW_COLOR}]))
        code, output = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("duplicate-date", output)

    def test_batch_overlaps_live(self):
        # Live end is 2026-06-17; starting the batch on the live end itself
        # is an overlap, not a contiguous append.
        batch = self.write_batch(build_batch_json(
            "2026-06-17", "2026-06-17",
            [{"date": "2026-06-17", "theme": "A", "row": ROW_DESERT}]))
        code, output = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("batch-overlaps-live", output)
        self.assertIn("batch-start-not-contiguous", output)

    def test_batch_start_not_contiguous_gap_before_live_end(self):
        # Skips 2026-06-18 entirely by starting on 2026-06-19.
        batch = self.write_batch(build_batch_json(
            "2026-06-19", "2026-06-19",
            [{"date": "2026-06-19", "theme": "A", "row": ROW_DESERT}]))
        code, output = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("batch-start-not-contiguous", output)

    def test_date_gap_inside_batch(self):
        batch = self.write_batch(build_batch_json(
            "2026-06-18", "2026-06-20",
            [{"date": "2026-06-20", "theme": "A", "row": ROW_SEA},
             {"date": "2026-06-18", "theme": "B", "row": ROW_DESERT}]))
        code, output = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("missing-date", output)

    def test_chronological_order_error(self):
        batch = self.write_batch(build_batch_json(
            "2026-06-18", "2026-06-19",
            [{"date": "2026-06-18", "theme": "A", "row": ROW_DESERT},
             {"date": "2026-06-19", "theme": "B", "row": ROW_COLOR}]))
        code, output = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("order", output)


class UnderlyingValidatorErrorTests(BatchWorkflowTestCase):
    def test_representative_validator_error_wrong_marker_count(self):
        bad_row = ROW_DESERT.replace("CANYON*", "CANYON")  # drop one marker
        batch = self.write_batch(build_batch_json(
            "2026-06-18", "2026-06-18",
            [{"date": "2026-06-18", "theme": "A", "row": bad_row}]))
        code, output = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("marker-count", output)


class SuccessPathTests(BatchWorkflowTestCase):
    def test_warnings_only_check_returns_zero(self):
        # Reuses ROW_SEA's OYSTER/URCHIN, which do not appear in LIVE_ENTRIES,
        # against a distinct second-date row so only the theme repeats,
        # producing a warning-only result.
        batch = self.write_batch(build_batch_json(
            "2026-06-18", "2026-06-19",
            [{"date": "2026-06-19", "theme": "Under the Sea", "row": ROW_SEA},
             {"date": "2026-06-18", "theme": "Under the Sea", "row": ROW_COLOR}]))
        code, output = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertEqual(code, 0)
        self.assertIn("0 error(s)", output)
        self.assertIn("WARNING", output)
        self.assertIn("theme-repeated", output)
        self.assertTargetUnchanged()

    def test_check_never_writes(self):
        batch = self.write_batch(build_batch_json(
            "2026-06-18", "2026-06-19",
            [{"date": "2026-06-19", "theme": "A", "row": ROW_DESERT},
             {"date": "2026-06-18", "theme": "B", "row": ROW_SEA}]))
        code, _ = self.run_cli("check", str(batch), "--target", str(self.target))
        self.assertEqual(code, 0)
        self.assertTargetUnchanged()

    def test_successful_apply_updates_target(self):
        batch = self.write_batch(build_batch_json(
            "2026-06-18", "2026-06-19",
            [{"date": "2026-06-19", "theme": "Desert Trek", "row": ROW_DESERT},
             {"date": "2026-06-18", "theme": "Under the Sea", "row": ROW_SEA}]))
        code, output = self.run_cli("apply", str(batch), "--target", str(self.target))
        self.assertEqual(code, 0)
        self.assertIn("Applied batch", output)

        new_text = self.target.read_text(encoding="utf-8")
        publishing_range, entries, diags = vp.parse_text(new_text)
        self.assertEqual(diags, [])
        self.assertEqual(publishing_range, {"start": LIVE_START, "end": "2026-06-19"})
        self.assertEqual(len(entries), 4)
        self.assertEqual([e["date"] for e in entries],
                          ["2026-06-19", "2026-06-18", "2026-06-17", "2026-06-16"])
        # Historical entries preserved byte-for-data.
        self.assertEqual(entries[2], LIVE_ENTRIES[0])
        self.assertEqual(entries[3], LIVE_ENTRIES[1])
        old_start, old_end, old_err = vp._locate_balanced_span(
            self.original_bytes.decode("utf-8"), "PUZZLE_ENTRIES", "[", "]")
        self.assertIsNone(old_err)
        old_body = self.original_bytes.decode("utf-8")[old_start + 1:old_end - 1]
        self.assertIn(old_body, self.target.read_bytes().decode("utf-8"))

        validation_diags = vp.validate(publishing_range, entries)
        self.assertEqual([d for d in validation_diags if d.severity == "ERROR"], [])

    def test_surrounding_file_content_preserved_verbatim(self):
        batch = self.write_batch(build_batch_json(
            "2026-06-18", "2026-06-18",
            [{"date": "2026-06-18", "theme": "Desert Trek", "row": ROW_DESERT}]))
        code, _ = self.run_cli("apply", str(batch), "--target", str(self.target))
        self.assertEqual(code, 0)

        new_text = self.target.read_text(encoding="utf-8")
        self.assertTrue(new_text.startswith(LIVE_HEADER))
        self.assertTrue(new_text.endswith(LIVE_TRAILER))

    def test_deterministic_second_apply_refusal(self):
        batch_text = build_batch_json(
            "2026-06-18", "2026-06-19",
            [{"date": "2026-06-19", "theme": "Desert Trek", "row": ROW_DESERT},
             {"date": "2026-06-18", "theme": "Under the Sea", "row": ROW_SEA}])
        batch = self.write_batch(batch_text)

        code1, _ = self.run_cli("apply", str(batch), "--target", str(self.target))
        self.assertEqual(code1, 0)
        after_first_apply = self.target.read_bytes()

        code2, output2 = self.run_cli("apply", str(batch), "--target", str(self.target))
        self.assertNotEqual(code2, 0)
        self.assertIn("batch-overlaps-live", output2)
        self.assertEqual(self.target.read_bytes(), after_first_apply)

    def test_successful_apply_preserves_target_permission_mode(self):
        os.chmod(self.target, 0o640)
        self.original_bytes = self.target.read_bytes()  # unchanged by chmod; kept for clarity
        original_mode = stat.S_IMODE(self.target.stat().st_mode)
        if os.name != "nt":
            self.assertEqual(original_mode, 0o640)

        batch = self.write_batch(build_batch_json(
            "2026-06-18", "2026-06-18",
            [{"date": "2026-06-18", "theme": "Desert Trek", "row": ROW_DESERT}]))
        code, _ = self.run_cli("apply", str(batch), "--target", str(self.target))
        self.assertEqual(code, 0)

        new_mode = stat.S_IMODE(self.target.stat().st_mode)
        # Windows exposes only a subset of POSIX mode bits through chmod and
        # stat; the safety contract is that apply preserves what the platform
        # reports for the source file.
        self.assertEqual(new_mode, original_mode)


class BlockedApplyTests(BatchWorkflowTestCase):
    def test_blocked_apply_preserves_target_bytes(self):
        bad_row = ROW_DESERT.replace("CANYON*", "CANYON")  # drop one marker
        batch = self.write_batch(build_batch_json(
            "2026-06-18", "2026-06-18",
            [{"date": "2026-06-18", "theme": "A", "row": bad_row}]))
        code, output = self.run_cli("apply", str(batch), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("marker-count", output)
        self.assertIn("Apply refused", output)
        self.assertTargetUnchanged()

    def test_apply_missing_batch_file_is_refused_without_writing(self):
        code, output = self.run_cli(
            "apply", str(self.tmp_path / "nonexistent.json"), "--target", str(self.target))
        self.assertNotEqual(code, 0)
        self.assertIn("batch-file-not-found", output)
        self.assertTargetUnchanged()

    def test_os_replace_failure_returns_nonzero_and_preserves_target(self):
        original_mode = stat.S_IMODE(self.target.stat().st_mode)
        batch = self.write_batch(build_batch_json(
            "2026-06-18", "2026-06-18",
            [{"date": "2026-06-18", "theme": "Desert Trek", "row": ROW_DESERT}]))

        with mock.patch("manage_puzzle_batch.os.replace", side_effect=OSError("boom")):
            code, output = self.run_cli("apply", str(batch), "--target", str(self.target))

        self.assertNotEqual(code, 0)
        self.assertIn("apply-write-failed", output)
        self.assertNotIn("Traceback", output)
        self.assertTargetUnchanged()
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), original_mode)
        # No stray temp file left behind in the target's directory.
        leftover = [p for p in self.tmp_path.iterdir() if p.name.endswith(".tmp")]
        self.assertEqual(leftover, [])


class LiveDataDoesNotMutateTests(unittest.TestCase):
    def test_default_target_is_repo_root_puzzles_js(self):
        self.assertEqual(mpb.vp.DEFAULT_DATA_PATH, mpb.vp.REPO_ROOT / "puzzles.js")

    def test_live_file_untouched_by_tests(self):
        self.assertTrue((mpb.vp.REPO_ROOT / "puzzles.js").exists())


if __name__ == "__main__":
    unittest.main()
