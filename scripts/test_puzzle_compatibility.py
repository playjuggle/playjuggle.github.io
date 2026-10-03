#!/usr/bin/env python3
"""Regression tests for the puzzle-save fingerprint/compatibility contract.

Exercises the *actual production* helpers in main.js (computePuzzleFingerprint,
isSaveCompatible, LEGACY_INCOMPATIBLE_DATES, saveState, loadState) rather than
reimplementing their logic in Python. puzzles.js, game.js, wordlist.js, and
main.js are loaded verbatim (byte-for-byte, unmodified) into a JavaScript
sandbox via Node.js when available, with macOS's `osascript -l JavaScript`
(JXA) as a runtime fallback.
The harness supplies minimal, browser-standard-shaped shims for
document/window/localStorage/URLSearchParams so the production files can load
without a real browser; it never changes what the production helpers do.

Also asserts the live puzzles.js dataset validates with zero errors and the
documented warning contract, using the real validator module directly.

Run with:
    python3 -m unittest scripts.test_puzzle_compatibility
    python3 -m unittest scripts/test_puzzle_compatibility.py
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_puzzles as vp  # noqa: E402

# The 12 dates the implementation handoff approved as incompatible for a
# fingerprint-less (legacy) save, per HISTORICAL_PUZZLE_REMEDIATION_PLAN.md §8.
EXPECTED_LEGACY_INCOMPATIBLE_DATES = sorted([
    "2026-05-27", "2026-05-28", "2026-05-29", "2026-05-31",
    "2026-06-02", "2026-06-03", "2026-06-11", "2026-06-12",
    "2026-06-13", "2026-06-14", "2026-06-15", "2026-06-16",
])

GLOBAL_KEYS = [
    "juggle_settings", "juggle_visits", "juggle_achievements",
    "juggle_ach_counts", "juggle_completions",
]

# Minimal, browser-standard-shaped shims. No production logic lives here.
_SHIM = r"""
function makeLocalStorage() {
  const store = {};
  return {
    getItem: function (k) { return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null; },
    setItem: function (k, v) { store[k] = String(v); },
    removeItem: function (k) { delete store[k]; },
  };
}
function URLSearchParams(search) {
  this._params = {};
  String(search || '').replace(/^\?/, '').split('&').filter(Boolean).forEach(function (pair) {
    var eq = pair.indexOf('=');
    var k = eq === -1 ? pair : pair.slice(0, eq);
    var v = eq === -1 ? '' : pair.slice(eq + 1);
    this._params[decodeURIComponent(k)] = decodeURIComponent(v);
  }, this);
}
URLSearchParams.prototype.get = function (key) {
  return Object.prototype.hasOwnProperty.call(this._params, key) ? this._params[key] : null;
};
URLSearchParams.prototype.has = function (key) {
  return Object.prototype.hasOwnProperty.call(this._params, key);
};
globalThis.localStorage = makeLocalStorage();
globalThis.window = { location: { search: '' } };
globalThis.document = { addEventListener: function () {}, getElementById: function () { return null; } };
globalThis.navigator = { userAgent: 'test' };
globalThis.console = { log: function () {}, warn: function () {}, info: function () {}, error: function () {} };

// Mirrors the S.words/S.final scaffold init() builds in main.js (main.js:497-514)
// so the real saveState()/loadState() have the shape they expect to operate on.
function setupState(puzzle) {
  S.puzzle = puzzle;
  S.words = puzzle.words.map(function (w) {
    return {
      answer: w.answer, scrambled: w.scrambled, bonusIndices: w.bonusIndices,
      confirmed: Array(6).fill(false), guess: Array(6).fill(null),
      bankSlots: Array(6).fill(null), solved: false,
    };
  });
  S.final = {
    answer: puzzle.finalWord, bonusLetters: Array(6).fill(null),
    confirmed: Array(6).fill(false), guess: Array(6).fill(null),
    bankSlots: Array(6).fill(null), solved: false,
  };
  S.activeWord = 0;
  S.cursor = 0;
  S.hardMode = false;
  S.wrongGuesses = 1;
  S.invalidAttempts = 0;
  S.hintsUsed = 0;
  S.gameStarted = true;
}
"""


def _js_runtime():
    """Return the preferred JavaScript runtime command, or None if absent."""
    node = shutil.which("node")
    if node:
        return "node", node
    osascript = shutil.which("osascript")
    if osascript:
        return "osascript", osascript
    return None


def run_js(body):
    """Load the real production JS files plus `body` into Node.js or JXA
    and return the JSON-decoded result of evaluating `body` (which
    must be a single JSON.stringify(...) expression)."""
    files = ["puzzles.js", "game.js", "wordlist.js", "main.js"]
    source = _SHIM + "\n"
    for name in files:
        source += (REPO_ROOT / name).read_text(encoding="utf-8") + "\n"
    source += body
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(source)
        path = f.name
    try:
        runtime = _js_runtime()
        if runtime is None:
            raise RuntimeError("Neither Node.js nor osascript (JavaScriptCore) is available")
        if runtime[0] == "node":
            command = [runtime[1], "-e", (
                "const fs = require('fs'); const vm = require('vm'); "
                "const result = vm.runInThisContext(fs.readFileSync(process.argv[1], 'utf8')); "
                "process.stdout.write(String(result));"
            ), path]
        else:
            command = [runtime[1], "-l", "JavaScript", path]
        result = subprocess.run(
            command,
            capture_output=True, text=True, timeout=30,
        )
    finally:
        Path(path).unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(f"JavaScript harness failed (exit {result.returncode}): {result.stderr.strip()}")
    return json.loads(result.stdout)


@unittest.skipUnless(_js_runtime(), "Node.js or osascript (JavaScriptCore) is not available on this platform")
class PuzzleCompatibilityTests(unittest.TestCase):

    def test_legacy_incompatible_dates_are_the_exact_approved_twelve(self):
        result = run_js(
            "JSON.stringify({ dates: Array.from(LEGACY_INCOMPATIBLE_DATES).sort(), "
            "size: LEGACY_INCOMPATIBLE_DATES.size });"
        )
        self.assertEqual(result["size"], 12)
        self.assertEqual(result["dates"], EXPECTED_LEGACY_INCOMPATIBLE_DATES)

    def test_matching_fingerprint_loads_normally(self):
        result = run_js(
            """
            window.location.search = '?date=2026-10-19';
            setupState(PUZZLES['2026-10-19']);
            saveState();
            S.gameStarted = false;
            S.wrongGuesses = 0;
            var ok = loadState();
            JSON.stringify({
              ok: ok,
              wasReset: S.puzzleWasReset,
              gameStarted: S.gameStarted,
              wrongGuesses: S.wrongGuesses,
            });
            """
        )
        self.assertTrue(result["ok"])
        self.assertFalse(result["wasReset"])
        self.assertTrue(result["gameStarted"])
        self.assertEqual(result["wrongGuesses"], 1)

    def test_mismatching_fingerprint_resets_only_active_key_and_requests_notice(self):
        result = run_js(
            """
            window.location.search = '?date=2026-10-19';
            setupState(PUZZLES['2026-10-19']);
            saveState();
            var raw = JSON.parse(localStorage.getItem('juggle_puzzle_2026-10-19'));
            raw.puzzleFingerprint = 'not-a-real-fingerprint';
            localStorage.setItem('juggle_puzzle_2026-10-19', JSON.stringify(raw));
            localStorage.setItem('juggle_settings', JSON.stringify({hardMode:false}));
            localStorage.setItem('juggle_visits', JSON.stringify(['2026-10-19']));
            localStorage.setItem('juggle_achievements', JSON.stringify(['flawless']));
            localStorage.setItem('juggle_ach_counts', JSON.stringify({flawless:['2026-10-19']}));
            localStorage.setItem('juggle_completions', JSON.stringify(['2026-10-19']));
            localStorage.setItem('juggle_session_2026-10-19', 'session-abc');
            var before = {
              settings: localStorage.getItem('juggle_settings'),
              visits: localStorage.getItem('juggle_visits'),
              achievements: localStorage.getItem('juggle_achievements'),
              achCounts: localStorage.getItem('juggle_ach_counts'),
              completions: localStorage.getItem('juggle_completions'),
              session: localStorage.getItem('juggle_session_2026-10-19'),
            };
            S.puzzleWasReset = false;
            var ok = loadState();
            JSON.stringify({
              ok: ok,
              wasReset: S.puzzleWasReset,
              keyRemoved: localStorage.getItem('juggle_puzzle_2026-10-19') === null,
              settingsUnchanged: localStorage.getItem('juggle_settings') === before.settings,
              visitsUnchanged: localStorage.getItem('juggle_visits') === before.visits,
              achievementsUnchanged: localStorage.getItem('juggle_achievements') === before.achievements,
              achCountsUnchanged: localStorage.getItem('juggle_ach_counts') === before.achCounts,
              completionsUnchanged: localStorage.getItem('juggle_completions') === before.completions,
              sessionUnchanged: localStorage.getItem('juggle_session_2026-10-19') === before.session,
            });
            """
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result["wasReset"])
        self.assertTrue(result["keyRemoved"])
        for key in (
            "settingsUnchanged", "visitsUnchanged", "achievementsUnchanged",
            "achCountsUnchanged", "completionsUnchanged", "sessionUnchanged",
        ):
            self.assertTrue(result[key], key)

    def test_legacy_save_on_affected_date_resets(self):
        result = run_js(
            """
            // Keep this historical migration case tied to its legacy date,
            // while borrowing an active sample puzzle for the test harness.
            PUZZLES['2026-06-13'] = PUZZLES['2026-10-22'];
            window.location.search = '?date=2026-06-13';
            setupState(PUZZLES['2026-06-13']);
            saveState();
            var raw = JSON.parse(localStorage.getItem('juggle_puzzle_2026-06-13'));
            delete raw.puzzleFingerprint;
            localStorage.setItem('juggle_puzzle_2026-06-13', JSON.stringify(raw));
            S.puzzleWasReset = false;
            var ok = loadState();
            JSON.stringify({
              ok: ok,
              wasReset: S.puzzleWasReset,
              keyRemoved: localStorage.getItem('juggle_puzzle_2026-06-13') === null,
            });
            """
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result["wasReset"])
        self.assertTrue(result["keyRemoved"])

    def test_legacy_save_on_unchanged_date_loads_and_upgrades(self):
        result = run_js(
            """
            window.location.search = '?date=2026-10-19';
            setupState(PUZZLES['2026-10-19']);
            saveState();
            var raw = JSON.parse(localStorage.getItem('juggle_puzzle_2026-10-19'));
            delete raw.puzzleFingerprint;
            localStorage.setItem('juggle_puzzle_2026-10-19', JSON.stringify(raw));
            S.puzzleWasReset = false;
            S.gameStarted = false;
            S.wrongGuesses = 0;
            var ok = loadState();
            var after = JSON.parse(localStorage.getItem('juggle_puzzle_2026-10-19'));
            JSON.stringify({
              ok: ok,
              wasReset: S.puzzleWasReset,
              gameStartedRestored: S.gameStarted,
              wrongGuessesRestored: S.wrongGuesses,
              upgraded: !!after.puzzleFingerprint,
              fingerprintMatchesCurrent: after.puzzleFingerprint === computePuzzleFingerprint(PUZZLES['2026-10-19']),
            });
            """
        )
        self.assertTrue(result["ok"])
        self.assertFalse(result["wasReset"])
        self.assertTrue(result["gameStartedRestored"])
        self.assertEqual(result["wrongGuessesRestored"], 1)
        self.assertTrue(result["upgraded"])
        self.assertTrue(result["fingerprintMatchesCurrent"])

    def test_present_falsy_fingerprint_is_not_treated_as_missing(self):
        # A present-but-falsy saved fingerprint ('' or null) must be compared
        # strictly, not treated like an absent (legacy, `undefined`) field --
        # even on a date outside LEGACY_INCOMPATIBLE_DATES, where a genuinely
        # missing fingerprint would otherwise be trusted.
        result = run_js(
            """
            JSON.stringify({
              emptyString: isSaveCompatible('2026-10-19', '', 'real-fingerprint'),
              nullValue: isSaveCompatible('2026-10-19', null, 'real-fingerprint'),
              trulyMissing: isSaveCompatible('2026-10-19', undefined, 'real-fingerprint'),
            });
            """
        )
        self.assertFalse(result["emptyString"])
        self.assertFalse(result["nullValue"])
        self.assertTrue(result["trulyMissing"])

    def test_present_empty_fingerprint_resets_via_real_load_path_on_unaffected_date(self):
        # End-to-end regression for the same defect through the actual
        # saveState()/loadState() path (not just the isolated helper), on a
        # date that is NOT in LEGACY_INCOMPATIBLE_DATES, so only the strict
        # present-value check -- not the legacy-date list -- can be causing
        # the reset.
        result = run_js(
            """
            window.location.search = '?date=2026-10-19';
            setupState(PUZZLES['2026-10-19']);
            saveState();
            var raw = JSON.parse(localStorage.getItem('juggle_puzzle_2026-10-19'));
            raw.puzzleFingerprint = '';
            localStorage.setItem('juggle_puzzle_2026-10-19', JSON.stringify(raw));
            S.puzzleWasReset = false;
            var ok = loadState();
            JSON.stringify({
              ok: ok,
              wasReset: S.puzzleWasReset,
              keyRemoved: localStorage.getItem('juggle_puzzle_2026-10-19') === null,
            });
            """
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result["wasReset"])
        self.assertTrue(result["keyRemoved"])

    def test_fingerprint_changes_when_marker_positions_change(self):
        # Fingerprints include marked-letter positions. Use a current live
        # puzzle without coupling this compatibility test to authored answers.
        result = run_js(
            """
            var puzzle = PUZZLES['2026-10-20'];
            var fp = computePuzzleFingerprint(puzzle);
            var mutated = JSON.parse(JSON.stringify(puzzle));
            var markedWord = mutated.words.find(function (w) { return w.bonusIndices.length > 0; });
            markedWord.bonusIndices = [
              (markedWord.bonusIndices[0] + 1) % markedWord.answer.length
            ];
            JSON.stringify({
              markedWordFound: !!markedWord,
              changed: fp !== computePuzzleFingerprint(mutated),
            });
            """
        )
        self.assertTrue(result["markedWordFound"])
        self.assertTrue(result["changed"])


class LivePuzzleDatasetValidationTests(unittest.TestCase):
    """Confirms the new live schedule excludes retired archive content."""

    def test_live_dataset_extends_original_schedule_with_no_archive_reuse(self):
        publishing_range, entries, diags = vp.load_source(REPO_ROOT / "puzzles.js")
        self.assertIsNotNone(entries)
        self.assertGreaterEqual(len(entries), 21)
        self.assertEqual(publishing_range["start"], "2026-10-02")
        self.assertEqual(publishing_range["end"], entries[0]["date"])
        self.assertEqual(entries[-1]["date"], "2026-10-02")

        diags = list(diags) + vp.validate(publishing_range, entries)
        errors = [d for d in diags if d.severity == "ERROR"]
        self.assertEqual(errors, [])

        _, archived, archive_diags = vp.load_source(
            REPO_ROOT / "puzzle-batches" / "approved-live-puzzles-2026-06-17.js"
        )
        self.assertEqual(archive_diags, [])
        archived_themes = {entry["theme"].casefold() for entry in archived}
        archived_words = {
            token.strip().replace("*", "").upper()
            for entry in archived for token in entry["row"].split(",")
        }
        live_themes = {entry["theme"].casefold() for entry in entries}
        live_words = {
            token.strip().replace("*", "").upper()
            for entry in entries for token in entry["row"].split(",")
        }
        self.assertTrue(live_themes.isdisjoint(archived_themes))
        self.assertTrue(live_words.isdisjoint(archived_words))


if __name__ == "__main__":
    unittest.main()
