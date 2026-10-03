#!/usr/bin/env python3
"""Regression tests for storage-failure resilience and Hard Mode restoration.

Exercises the *actual production* functions in main.js (saveSettings,
getAnalyticsSessionId, trackEvent, init, the bootstrap ?reset handler) rather
than reimplementing their logic in Python. puzzles.js, game.js, wordlist.js,
and main.js are loaded verbatim (byte-for-byte, unmodified) into a
JavaScript sandbox via Node.js when available, with macOS's
`osascript -l JavaScript` (JXA) as a runtime fallback. They exercise the
shim, not an actual browser's
localStorage/Safari private-mode behavior.

The harness extends test_puzzle_compatibility's minimal shim with a
permissive mock DOM (so the real init() can run end-to-end without a real
browser) and a controllable localStorage whose getItem/setItem/removeItem
can be swapped per-test to throw, to exercise the failure-boundary paths.

Run with:
    python3 -m unittest scripts.test_storage_resilience
    python3 -m unittest scripts/test_storage_resilience.py
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_puzzle_compatibility import REPO_ROOT, _js_runtime  # noqa: E402

# Minimal, browser-standard-shaped shims, extended with a permissive mock DOM
# so the real init() (theme/board/streak/pregame rendering) can execute
# end-to-end without a real browser. No production logic lives here.
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

function makeMockElement() {
  const classes = Object.create(null);
  return {
    style: { setProperty: function () {}, cssText: '' },
    dataset: {},
    classList: {
      add:      function (c) { classes[c] = true; },
      remove:   function (c) { delete classes[c]; },
      contains: function (c) { return !!classes[c]; },
      toggle:   function (c, force) {
        const next = force === undefined ? !classes[c] : !!force;
        if (next) classes[c] = true; else delete classes[c];
        return next;
      },
    },
    appendChild:           function (child) { return child; },
    prepend:               function () {},
    insertAdjacentElement: function () {},
    addEventListener:      function () {},
    removeEventListener:   function () {},
    querySelector:         function () { return makeMockElement(); },
    querySelectorAll:      function () { return []; },
    closest:               function () { return null; },
    remove:                function () {},
    focus:                 function () {},
    setAttribute:          function () {},
    getAttribute:          function () { return null; },
  };
}

globalThis.localStorage = makeLocalStorage();
globalThis.window = { location: { search: '' } };
globalThis.document = {
  addEventListener:    function () {},
  removeEventListener: function () {},
  getElementById:      function () { return makeMockElement(); },
  createElement:       function () { return makeMockElement(); },
  querySelector:       function () { return makeMockElement(); },
  querySelectorAll:    function () { return []; },
  documentElement:     makeMockElement(),
  body:                makeMockElement(),
};
globalThis.navigator = { userAgent: 'test' };
globalThis.console = { log: function () {}, warn: function () {}, info: function () {}, error: function () {} };
globalThis.getComputedStyle = function () { return { getPropertyValue: function () { return ''; } }; };
globalThis.setTimeout   = function () { return 0; };
globalThis.clearTimeout = function () {};
globalThis.setInterval  = function () { return 0; };
globalThis.clearInterval = function () {};
globalThis.__fetchCalls = [];
globalThis.fetch = function (url, opts) {
  globalThis.__fetchCalls.push({ url: url, opts: opts });
  return Promise.resolve({});
};
"""


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


# JS snippet (not test logic -- pure data-building) used by the two tests that
# need a compatible, already-in-progress per-date save to check load-time
# precedence against the global setting.
_BUILD_COMPATIBLE_SAVE_JS = """
function buildCompatibleSave(puzzle, hardMode) {
  return {
    words: puzzle.words.map(function () {
      return { confirmed: Array(6).fill(false), guess: Array(6).fill(null), bankSlots: Array(6).fill(null), solved: false };
    }),
    final: { bonusLetters: Array(6).fill(null), confirmed: Array(6).fill(false), guess: Array(6).fill(null), bankSlots: Array(6).fill(null), solved: false },
    activeWord: 0, cursor: 0, hardMode: hardMode,
    wrongGuesses: 0, invalidAttempts: 0, hintsUsed: 0, gameStarted: true, timerMs: 0,
    puzzleFingerprint: computePuzzleFingerprint(puzzle),
  };
}
"""


@unittest.skipUnless(_js_runtime(), "Node.js or osascript (JavaScriptCore) is not available on this platform")
class SaveSettingsResilienceTests(unittest.TestCase):

    def test_working_storage_persists_settings_as_before(self):
        result = run_js(
            """
            S.hardMode = true;
            Timer.hidden = true;
            saveSettings();
            JSON.stringify(JSON.parse(localStorage.getItem('juggle_settings')));
            """
        )
        self.assertEqual(result, {"hardMode": True, "timerHidden": True})

    def test_throwing_write_does_not_escape_and_caller_continues(self):
        result = run_js(
            """
            S.hardMode = true;
            Timer.hidden = false;
            localStorage.setItem = function () { throw new Error('quota exceeded'); };
            let threw = false;
            let afterRan = false;
            try { saveSettings(); afterRan = true; } catch (e) { threw = true; }
            JSON.stringify({ threw: threw, afterRan: afterRan });
            """
        )
        self.assertFalse(result["threw"])
        self.assertTrue(result["afterRan"])


@unittest.skipUnless(_js_runtime(), "Node.js or osascript (JavaScriptCore) is not available on this platform")
class BootstrapResetResilienceTests(unittest.TestCase):

    def test_working_removal_clears_only_the_active_puzzle_key(self):
        result = run_js(
            """
            window.location.search = '?reset=1&date=2026-06-10';
            localStorage.setItem('juggle_puzzle_2026-06-10', 'stale-save');
            localStorage.setItem('juggle_settings', 'keep-me');
            init();
            JSON.stringify({
              puzzleKeyRemoved: localStorage.getItem('juggle_puzzle_2026-06-10') === null,
              settingsUnchanged: localStorage.getItem('juggle_settings') === 'keep-me',
            });
            """
        )
        self.assertTrue(result["puzzleKeyRemoved"])
        self.assertTrue(result["settingsUnchanged"])

    def test_throwing_removal_does_not_abort_init_or_touch_other_keys(self):
        result = run_js(
            """
            window.location.search = '?reset=1&date=2026-06-10';
            localStorage.setItem('juggle_settings', 'keep-me');
            localStorage.removeItem = function () { throw new Error('denied'); };
            let threw = false;
            try { init(); } catch (e) { threw = true; }
            JSON.stringify({
              threw: threw,
              settingsUnchanged: localStorage.getItem('juggle_settings') === 'keep-me',
              puzzleInitialized: !!S.puzzle,
            });
            """
        )
        self.assertFalse(result["threw"])
        self.assertTrue(result["settingsUnchanged"])
        self.assertTrue(result["puzzleInitialized"])


@unittest.skipUnless(_js_runtime(), "Node.js or osascript (JavaScriptCore) is not available on this platform")
class AnalyticsSessionIdResilienceTests(unittest.TestCase):

    def test_working_storage_generates_and_persists_then_reuses_id(self):
        result = run_js(
            """
            window.location.search = '?date=2026-06-10';
            const id1 = getAnalyticsSessionId();
            const id2 = getAnalyticsSessionId();
            JSON.stringify({
              id1: id1,
              sameOnSecondCall: id1 === id2,
              nonEmpty: typeof id1 === 'string' && id1.length > 0,
              persisted: localStorage.getItem('juggle_session_2026-06-10') === id1,
            });
            """
        )
        self.assertTrue(result["nonEmpty"])
        self.assertTrue(result["sameOnSecondCall"])
        self.assertTrue(result["persisted"])

    def test_existing_stored_id_is_preserved(self):
        result = run_js(
            """
            window.location.search = '?date=2026-06-10';
            localStorage.setItem('juggle_session_2026-06-10', 'existing-id-123');
            const id = getAnalyticsSessionId();
            JSON.stringify({ id: id });
            """
        )
        self.assertEqual(result["id"], "existing-id-123")

    def test_throwing_read_falls_back_to_stable_unpersisted_id(self):
        result = run_js(
            """
            window.location.search = '?date=2026-06-10';
            let setItemCalls = 0;
            localStorage.getItem = function () { throw new Error('denied'); };
            const realSetItem = localStorage.setItem;
            localStorage.setItem = function (k, v) { setItemCalls++; return realSetItem(k, v); };
            let threw = false;
            let id1, id2;
            try { id1 = getAnalyticsSessionId(); id2 = getAnalyticsSessionId(); }
            catch (e) { threw = true; }
            JSON.stringify({
              threw: threw,
              nonEmpty: typeof id1 === 'string' && id1.length > 0,
              stableAcrossCalls: id1 === id2,
              noWriteAttempted: setItemCalls === 0,
            });
            """
        )
        self.assertFalse(result["threw"])
        self.assertTrue(result["nonEmpty"])
        self.assertTrue(result["stableAcrossCalls"])
        self.assertTrue(result["noWriteAttempted"])

    def test_throwing_write_falls_back_to_stable_id_without_persisting(self):
        result = run_js(
            """
            window.location.search = '?date=2026-06-10';
            localStorage.setItem = function () { throw new Error('denied'); };
            let threw = false;
            let id1, id2;
            try { id1 = getAnalyticsSessionId(); id2 = getAnalyticsSessionId(); }
            catch (e) { threw = true; }
            JSON.stringify({
              threw: threw,
              nonEmpty: typeof id1 === 'string' && id1.length > 0,
              stableAcrossCalls: id1 === id2,
              storedSessionKey: localStorage.getItem('juggle_session_2026-06-10'),
            });
            """
        )
        self.assertFalse(result["threw"])
        self.assertTrue(result["nonEmpty"])
        self.assertTrue(result["stableAcrossCalls"])
        self.assertIsNone(result["storedSessionKey"])

    def test_track_event_still_sends_payload_when_storage_unavailable(self):
        result = run_js(
            """
            window.location.search = '?date=2026-06-10';
            localStorage.getItem = function () { throw new Error('denied'); };
            localStorage.setItem = function () { throw new Error('denied'); };
            S.puzzle = { theme: 'Test Theme' };
            S.hardMode = true;
            trackEvent('start');
            const call = globalThis.__fetchCalls[0];
            const payload = call ? JSON.parse(call.opts.body) : null;
            JSON.stringify({
              callCount: globalThis.__fetchCalls.length,
              event: payload && payload.event,
              hasSessionId: !!(payload && payload.session_id),
              hardMode: payload && payload.hard_mode,
              theme: payload && payload.theme,
            });
            """
        )
        self.assertEqual(result["callCount"], 1)
        self.assertEqual(result["event"], "start")
        self.assertTrue(result["hasSessionId"])
        self.assertTrue(result["hardMode"])
        self.assertEqual(result["theme"], "Test Theme")


@unittest.skipUnless(_js_runtime(), "Node.js or osascript (JavaScriptCore) is not available on this platform")
class HardModeRestorationTests(unittest.TestCase):

    def test_fresh_date_restores_true_from_saved_global_setting(self):
        result = run_js(
            """
            window.location.search = '?date=2026-06-10';
            localStorage.setItem('juggle_settings', JSON.stringify({ hardMode: true, timerHidden: false }));
            init();
            JSON.stringify({ hardMode: S.hardMode });
            """
        )
        self.assertTrue(result["hardMode"])

    def test_fresh_date_defaults_false_when_settings_missing(self):
        result = run_js(
            """
            window.location.search = '?date=2026-06-10';
            init();
            JSON.stringify({ hardMode: S.hardMode });
            """
        )
        self.assertFalse(result["hardMode"])

    def test_fresh_date_defaults_false_when_settings_malformed(self):
        result = run_js(
            """
            window.location.search = '?date=2026-06-10';
            localStorage.setItem('juggle_settings', 'not-valid-json{{{');
            init();
            JSON.stringify({ hardMode: S.hardMode });
            """
        )
        self.assertFalse(result["hardMode"])

    def test_compatible_existing_date_save_still_overrides_global_preference(self):
        result = run_js(
            _BUILD_COMPATIBLE_SAVE_JS
            + """
            window.location.search = '?date=2026-06-10';
            localStorage.setItem('juggle_settings', JSON.stringify({ hardMode: true }));
            const puzzle = PUZZLES['2026-06-10'];
            localStorage.setItem('juggle_puzzle_2026-06-10', JSON.stringify(buildCompatibleSave(puzzle, false)));
            init();
            JSON.stringify({ hardMode: S.hardMode, gameStarted: S.gameStarted });
            """
        )
        self.assertFalse(result["hardMode"])
        self.assertTrue(result["gameStarted"])


if __name__ == "__main__":
    unittest.main()
