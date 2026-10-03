# Juggle Current State

## Live schedule (2026-10-02 to 2026-10-22)

The live schedule contains 21 puzzles for 2026-10-02 through 2026-10-22. Its themes are Computer Desk, Hand Sewing, Farmers' Market, Photo Studio, Diner Brunch, Sports Tournament, Art Studio, Backyard Dinner, Dance Rehearsal, Dental Visit, Lawn Care, Moving Day, Birthday Party, Ocean Life, Hotel Room, Snow Day, Hair Styling, Urban Rail, Roadside Repair, Museum Exhibit, and Toy Box. The 2026-10-02 entry was preserved unchanged. The 2026-10-03 through 2026-10-22 rows were rewritten under `juggle-autonomy/PUZZLE_QUALITY_STANDARD.md`; the per-date rationale and weakest-link critiques are in `juggle-autonomy/QC-2026-10-03-to-2026-10-22.md`. The retired archive remains unchanged at `puzzle-batches/approved-live-puzzles-2026-06-17.js` (SHA-256 `7CB3E3B0F5001393CAC985A365003B43C69DAEEFD44518D27B33397E5D38B318`) and was used only for uniqueness checks. The staged 120-puzzle candidate remains unapproved and is not live. The next date needing content is 2026-10-23. The editorial audit found globally unique answers and six marked letters per replacement by direct source review; full validator and unit-test evidence is recorded below after final checks.

## Puzzle quality standard application (2026-10-03)

The user authorized editing the scheduled 2026-10-03 through 2026-10-22 entries and specified that 2026-10-02 remain unchanged. All 20 in-scope puzzles were replaced after editorial review. LENSES, CLUTCH, and BUBBLE were replaced. The full suite passed (102 tests); the validator reports 21 entries, 0 errors, and 0 warnings; `git diff --check` passed. Live-answer uniqueness, no live/archive overlap, and preservation of 2026-10-02 were confirmed. The retired archive itself contains 9 pre-existing duplicate answer occurrences across 8 words; it was left unchanged. Its SHA-256 remains `7CB3E3B0F5001393CAC985A365003B43C69DAEEFD44518D27B33397E5D38B318`. No validator warnings remain.

## Staged candidate schedule (snapshot from 2026-10-01)

`puzzle-batches/candidate-2026-06-18-to-2026-10-15.json` and its per-date review at `puzzle-batches/QC-2026-06-18-to-2026-10-15.md` are staged only; neither is live. Structural and batch checks passed with 0 candidate errors/warnings and 6 inherited live warnings. Codex's editorial review did not accept the content for promotion: 29 theme/payoff concerns remained and the broad-audience lexical review was incomplete. No apply occurred. The owner's later authorization covers re-dating the approved 25-puzzle archive; it does not approve this candidate.

Baseline captured on 2026-09-13 from local commit `e273c7f` on `main`. At capture time the worktree was clean and `main` matched the locally recorded `origin/main`. No network fetch was performed, so this does not prove that the remote has not changed since its local tracking reference was last updated.

## Confirmed architecture

- Juggle is a static vanilla HTML/CSS/JavaScript game with no package manifest, framework, application backend, build step, or CI workflow. A standard-library-only Python validator (`scripts/validate_puzzles.py`) now exists for puzzle data, runnable locally; it is not wired into any CI or publish-blocking automation.
- `index.html` loads `style.css`, then browser scripts `puzzles.js`, `game.js`, `wordlist.js`, and `main.js`. It also loads Google Fonts and canvas-confetti from external CDNs.
- `puzzles.js` holds the ordered, authored puzzle source (`PUZZLE_ENTRIES`, an array of `{date, theme, row}` in newest-to-oldest declared order, and `PUZZLE_PUBLISHING_RANGE`, the declared inclusive `{start, end}` schedule). Both are written as embedded strict-JSON values specifically so `scripts/validate_puzzles.py` can parse them without executing JavaScript. `game.js` builds `PUZZLE_ROWS` from `PUZZLE_ENTRIES` at load time (later entries for the same date overwrite earlier ones, matching the prior plain-object-literal behavior byte-for-byte; the approved live `PUZZLE_ENTRIES` currently declares exactly one entry per date, so this overwrite rule is presently a dormant compatibility characteristic rather than something any live date exercises).
- `game.js` contains puzzle parsing, deterministic scrambling, deterministic word ordering, final-letter slot assignment, and browser-console validation. Puzzle source content itself moved to `puzzles.js`.
- `wordlist.js` contains the accepted six-letter dictionary for ordinary wrong guesses. All primary and final puzzle answers are separately auto-accepted.
- `main.js` owns rendering, input, timer behavior, hints, game flow, persistence, streaks, achievements, sharing, analytics, feedback, and date selection.
- Game progress and user preferences are stored only in browser `localStorage`; there are no accounts or server-side game records.
- The repository also contains the historical `JUMBLE_spec.md`, social-preview assets and source, and several color-swatch design files. The specification differs from the implementation in several places and must not override observed runtime code without an explicit product decision.

## Confirmed puzzle and date behavior

- Puzzle source is authored as an ordered list, not an object: `puzzles.js`'s `PUZZLE_ENTRIES` array holds one `{date, theme, row}` entry per declaration, newest-to-oldest, with duplicate dates kept as separate array elements so they remain individually inspectable (by eye and by the validator) before any overwrite happens. `game.js` then folds that list into the *effective runtime* object, `PUZZLE_ROWS` (keyed by `YYYY-MM-DD`, later entry wins per date) — that object-with-overwrite-semantics is a build product of `game.js`, not the authored source. Each entry's `row` is a comma-separated row of five six-letter primary answers plus one six-letter final answer.
- An asterisk immediately after a primary-word letter marks that letter for the final puzzle. The intended total is six marked letters across the five primary words, and those letters should be an anagram of the final answer.
- Parsing rejects rows only when the comma-separated item count is not six or an answer is not six alphabetic letters. Marker-count and final-anagram failures produce warnings but are still loaded.
- `validatePuzzles()` runs during browser initialization and reports to the console only. There is no release-blocking validation.
- The active date is the browser's local date, overridden by a public `?date=YYYY-MM-DD` parameter. `?reset` removes saved puzzle state for that active date.
- If an exact date is absent, the game silently selects the most recent puzzle on or before that date. The displayed date, daily colors, storage key, completion date, and analytics date still use the requested date rather than the selected puzzle's source date.
- At the 2026-10-02 to 2026-10-22 authored schedule, every date in that inclusive range has a distinct entry. An absent date still falls back to the most recent puzzle on or before it; content after 2026-10-22 therefore needs to be added before that date is reached.
- Preview state is date-scoped, but previewing is not side-effect-free: a preview can emit analytics and affect completion and achievement records. Visit/streak recording uses the real local date.

## Historical archive remediation (applied 2026-09-15)

At the time of the 2026-09-15 remediation, `puzzles.js` contained the owner-approved 25-entry `PUZZLE_ENTRIES` dataset from `HISTORICAL_PUZZLE_REMEDIATION_PLAN.md` §6, covering `2026-05-24`–`2026-06-17` with one declaration per date. That exact source is preserved before the schedule restoration in `puzzle-batches/approved-live-puzzles-2026-06-17.js`. At the time, the validator reported 25 entries, 0 errors, and 6 warnings. Relative to the pre-remediation state:

- The duplicate `2026-06-17` declaration is gone; only "Garden Path" remains, matching what was already effective at runtime.
- `2026-06-11` ("Hard Hat Zone"), `2026-06-03` ("Once Upon a Time"), and `2026-06-02` ("Animal Kingdom") had their marker positions repaired so the six marked letters anagram to their final word; themes, answers, and dates are unchanged.
- `2026-06-16` and `2026-05-31` (previously duplicate-content repeats of `2026-06-11` and `2026-05-30`) now carry new original content ("Movie Night", "Grocery Store").
- The 7 previously-undeclared dates in range (`2026-05-27`–`2026-05-29`, `2026-06-12`–`2026-06-15`) are now filled, including a repaired, honestly-relabeled "Bake Shop" placed on `2026-06-12` (it was never effective on `2026-06-17`).
- `2026-06-11` ("Hard Hat Zone") is no longer duplicated at `2026-06-16`; `2026-05-30` ("Airplane Mode") is no longer duplicated at `2026-05-31`.

Full per-date rationale, exact row diffs, and validator evidence live in `HISTORICAL_PUZZLE_REMEDIATION_PLAN.md`.

## Save-compatibility fingerprint (added 2026-09-15)

Because this remediation changes puzzle content on 12 dates that could already hold a locally saved (in-progress or fallback) game, `main.js` now guards per-date `localStorage` saves against stale content:

- `saveState()` writes one additional field, `puzzleFingerprint`, alongside existing saved fields — a deterministic string built from the active puzzle's theme, each word's answer/scramble/marker indices, the final word, and the final-slot order (`computePuzzleFingerprint()`).
- `loadState()` compares a saved fingerprint against the puzzle currently in effect for that date (`isSaveCompatible()`). A present, matching fingerprint loads normally. A present, mismatching fingerprint — or a missing (legacy, pre-fingerprint) fingerprint on one of the 12 dates in `LEGACY_INCOMPATIBLE_DATES` — is treated as incompatible: only that date's `juggle_puzzle_<date>` key is cleared, and the pre-game screen shows a one-time, dismissal-free `role="status"` notice for that visit. A legacy save on any other date loads normally and is immediately rewritten with the current fingerprint.
- No other storage key (`juggle_settings`, `juggle_visits`, `juggle_achievements`, `juggle_ach_counts`, `juggle_completions`, `juggle_session_<date>`) is touched by this migration.
- Regression coverage lives in `scripts/test_puzzle_compatibility.py`, which loads the real `puzzles.js`/`game.js`/`wordlist.js`/`main.js` into a JavaScriptCore (`osascript -l JavaScript`) sandbox — no cross-platform JS runtime (node/deno/jsc) is installed in this environment — and exercises the actual `saveState`/`loadState`/`computePuzzleFingerprint`/`isSaveCompatible` functions rather than a Python reimplementation.

## Mobile viewport/touch/safe-area hardening (added 2026-09-16)

Per `HANDOFF.md` ("Harden Mobile Viewport, Touch, and Text-Scaling Reliability") and the audit's Finding #3–4/Phase 1, `index.html`/`style.css` now carry a CSS-only mobile-resilience pass with no gameplay/JS change:

- Viewport meta adds `viewport-fit=cover` (no `user-scalable`/`maximum-scale` — pinch-zoom stays enabled).
- `touch-action: manipulation` covers every real tap target (`button`, `.slot`, `.tile`, `.shuffle-btn`, `.backspace-btn`, `.toggle-row`, `.word-row`, `#timer-display`, `.modal-backdrop`, `#completion`), fixing the reported rapid-Backspace-tap zoom.
- `#app` and the three full-viewport overlays (`#pregame`, `.modal`, `#completion`) add `env(safe-area-inset-*)` padding layered after their existing zero-inset spacing, so unsupported browsers or zero-inset devices are unchanged.
- `html, body { height: 100% }` and the `vh`-based `clamp()` values (`--slot-h`, `#board` padding, `.word-row` margin, `#bank-area` padding, `.modal-card` max-height, `.slot` font-size) each keep their legacy value and get an `@supports (height: 100dvh)`-gated `dvh` override, so the layout follows a collapsing/expanding mobile toolbar instead of the legacy large viewport.
- `#board` changed from `overflow: hidden` to `overflow-y: auto`, and a `@media (max-height: 500px)` rule lets the whole shell (`html, body`, `#app`, `#board`) fall back to natural-height/page-scroll — so a short landscape viewport (or content grown taller by enlarged text) scrolls to every row and the bank instead of silently clipping them.
- No global text-size-adjust suppression or `text-overflow: ellipsis`/truncation was present before or after this change; enlarged browser/user text can still wrap and grow.
- Regression coverage lives in `scripts/test_mobile_ui_contract.py` — a static, no-browser test that inspects the actual `index.html`/`style.css` text for this contract.
- **Not yet verified:** real-iPhone/Safari behavior (notch/home-indicator rendering, actual toolbar-collapse behavior, physical double-tap-zoom suppression). No `node`/`npm`/browser-automation tooling is installed in this environment, so only static-file inspection was performed; the audit's six-step Safari smoke protocol (`PLATFORM_AUDIT.md` §7) is still required before this is trusted on a physical device.

## Storage-failure resilience and Hard Mode restoration (added 2026-09-16)

Per `HANDOFF.md` ("Harden Browser Storage Failures and Restore the Saved Hard-Mode Preference") and the audit's section 9, the three previously-unguarded `localStorage` call sites in `main.js` are now exception-safe, with no key/shape/behavior change on the working-storage path:

- `saveSettings()` wraps its `localStorage.setItem` in `try/catch`; a throwing write (e.g. Safari private-mode quota/security errors) is silently swallowed and never escapes to the toggle handlers or `onReady()` that call it.
- The bootstrap `?reset` handler in `init()` wraps its `localStorage.removeItem` in `try/catch`; a throwing removal no longer aborts initialization, and no other key is touched (there is no fallback removal).
- `getAnalyticsSessionId()` wraps its read/write in `try/catch`. On working storage it behaves exactly as before (reuses an existing `juggle_session_<date>` value, or generates and persists one). If the read or write throws, it returns a `crypto.randomUUID()`/timestamp-random anonymous ID that is cached in a page-lifetime module variable and reused for all later calls in that page instance, without ever writing to any storage, cookie, or other durable mechanism. `trackEvent()` is unchanged and still sends its full existing payload (including this fallback ID) whenever `ANALYTICS_ENDPOINT` is configured, independent of storage availability.
- `init()` now restores `S.hardMode` from `loadSettings()` for a fresh date (`settings.hardMode === true`, so anything missing/non-boolean/malformed defaults to `false`), evaluated before `loadState()` — a compatible existing per-date save's own `hardMode` field still overrides it afterward, preserving in-progress-game precedence.
- Regression coverage lives in `scripts/test_storage_resilience.py`, which loads the real `main.js`/`game.js`/`puzzles.js`/`wordlist.js` into the same JavaScriptCore (`osascript -l JavaScript`) sandbox used by `scripts/test_puzzle_compatibility.py`, extended with a permissive mock DOM so the real `init()` can run end-to-end, and a controllable `localStorage` whose `getItem`/`setItem`/`removeItem` can be swapped per-test to throw. It exercises the real `saveSettings`, `getAnalyticsSessionId`, `trackEvent`, and `init` functions on both the working-storage and throwing-storage paths — not a Python reimplementation.
- **Not yet verified:** actual Safari private-mode/quota-denial behavior on a real device or browser; only the JavaScriptCore shim's simulated throwing storage was exercised.

## Batch puzzle check-and-promote workflow (added 2026-09-16)

Per `HANDOFF.md` ("Build a Safe Batch Puzzle Check-and-Promote Workflow"), `scripts/manage_puzzle_batch.py` is a new standard-library-only tool that turns `scripts/validate_puzzles.py` into a safe content-operations gate for adding future puzzles, without hand-editing `puzzles.js` or risking the accepted historical archive:

- Candidates are authored as a strict-JSON batch file (`{"start", "end", "entries"}`, entries newest-to-oldest, same per-entry shape as `puzzles.js`); `puzzle-batches/README.md` documents the format and `puzzle-batches/template.json` is a deliberately-invalid placeholder (non-contiguous dates, malformed rows) so it can never be accidentally promoted.
- `python3 scripts/manage_puzzle_batch.py check path/to/batch.json` validates the batch twice — its own declared range in isolation, then the full proposed merge with the live schedule — reusing `vp.validate()`/`vp.parse_text()` directly rather than duplicating any content rule. It never writes, regardless of outcome.
- `python3 scripts/manage_puzzle_batch.py apply path/to/batch.json` runs the same two-pass validation and, only when it is fully clean of `ERROR` diagnostics (`WARNING`s never block either command), atomically rewrites the target (default: repository-root `puzzles.js`) — replacing only the `PUZZLE_PUBLISHING_RANGE`/`PUZZLE_ENTRIES` declarations via the validator's balanced-bracket span locator (`vp._locate_balanced_span`, factored out of `vp._extract_json_value` for this reuse) and preserving every existing entry and all surrounding file content byte-for-byte. The rendered target is revalidated before the atomic (temp file + `os.replace`) write, and the write is refused if the target changed on disk since it was read.
- This first workflow is strictly append-only: the batch's `start` must be exactly one day after the live `PUZZLE_PUBLISHING_RANGE.end`, entries must cover every day through the batch's `end` with no gaps, and no candidate date may fall on or before the live end. Overlap, replacement, historical edits, gaps, and any change to the live start are always refused; there is no override flag. Applying an already-promoted batch a second time deterministically refuses (the dates now overlap the new live end).
- Regression coverage lives in `scripts/test_manage_puzzle_batch.py` (21 tests: schema errors, append-only boundary violations, a representative underlying validator error, warnings-only success, check-never-writes, successful apply with historical-entry/surrounding-file preservation, blocked-apply byte preservation, and deterministic second-apply refusal), all against temporary files; the live `puzzles.js` is untouched by the test suite.
- This task did not generate or promote any real puzzle content — no live puzzle data changed, and the live schedule still ends at `2026-06-17` (see below).

## Confirmed integrations and state

- Analytics posts `start`, `finish`, and successful `share` events to a configured Google Apps Script endpoint. Requests are fire-and-forget with `no-cors`; failures are swallowed.
- Completion-screen feedback posts message and game metadata to a configured Formspree endpoint and displays response success or failure.
- Per-date puzzle state stores guesses, confirmed positions, tile-bank mappings, solved flags, final letters, active position, mode, mistake counts, hint count, start state, elapsed time, and (as of 2026-09-15) a `puzzleFingerprint` used for save-compatibility checks (see above).
- Separate global keys store settings, visits/streaks, achievements, completion dates, achievement counts, and per-date analytics session IDs.
- `hardMode` is written to global settings and, as of 2026-09-16 (see below), is restored from that saved setting for a new puzzle (defaulting to `false` when missing/malformed), just like the timer-visibility preference; a compatible existing per-date game save still overrides it.

## Deployment: confirmed versus inferred

Confirmed from the checkout:

- The Git remote is `https://github.com/playjuggle/playjuggle.github.io.git`.
- The public game URL and social metadata use `https://playjuggle.github.io`.
- There is no checked-in GitHub Actions workflow, deployment script, generated-site directory, custom-domain file, or build configuration.

Inferred, not proven by repository files:

- The site is most likely published by GitHub Pages directly from the repository root on `main`, consistent with the repository name and absence of another deployment mechanism.
- The exact GitHub Pages source setting, branch protection, external endpoint health, and currently served commit cannot be confirmed from this checkout alone.

## Current process weaknesses

- The live schedule currently ends at `2026-10-22`; content is next needed for `2026-10-23`. The retired approved archive and staged candidate are not live. `scripts/manage_puzzle_batch.py` still enforces its append-only promotion contract and was not changed for this schedule reorganization.
- If a future edit reintroduces a duplicate date, `PUZZLE_ENTRIES`'s ordered-array authoring keeps both declarations as separate elements so `scripts/validate_puzzles.py` can report it explicitly (rule `duplicate-date`) rather than it silently disappearing before validation runs. The approved live source currently has zero duplicate dates. The runtime `game.js` build step still folds `PUZZLE_ENTRIES` into `PUZZLE_ROWS` with later-entry-wins overwrite semantics, matching prior behavior — this is a retained compatibility characteristic of the build step, not something any live date currently relies on.
- Validation warnings (repeated theme/answer/final-word, scramble preserving an obvious 4-letter run) do not fail the validator and do not prevent publication; nothing currently blocks a commit or a GitHub Pages deploy on validator errors either, since the validator is not wired into CI, a pre-commit hook, or any publish step.
- A publishing range is now declared (`PUZZLE_PUBLISHING_RANGE` in `puzzles.js`) and the validator reports any date missing from that inclusive range, but nothing enforces the range automatically outside of running the validator by hand.
- Recent history contains repeated puzzle additions and same-day content fixes, showing that puzzle maintenance is currently manual and error-prone.
- The ignored local `.claude/settings.local.json` is a machine-specific permission allowlist, not shared workflow documentation.
# Historical live schedule restoration (2026-10-02; superseded 2026-10-02)

- The live schedule now uses 25 owner-approved, remediated puzzles re-dated to cover 2026-10-02 through 2026-10-26. The next date needing content is 2026-10-27.
- Before re-dating, the original complete `puzzles.js` was preserved as `puzzle-batches/approved-live-puzzles-2026-06-17.js` with its original dates and exact file content.
- The 120-puzzle candidate ending 2026-10-15 remains staged and unapproved; it was not promoted or edited.
- No gameplay code, validator, or batch gate was changed. Save compatibility must be rebuilt and verified before launch; no real players exist at this point.
