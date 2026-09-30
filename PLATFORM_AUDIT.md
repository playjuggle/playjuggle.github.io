# Juggle Platform & UX Reliability Audit

Prepared by Claude Code per `HANDOFF.md` (2026-09-13; revised 2026-09-13 per bounded Codex correction). Read-only audit; no application file was modified. Local environment note (fact, checked 2026-09-13): this checkout has `git` 2.39.3, `python3` 3.12.0, and `gh` 2.92.0, but **no `node`, `npm`, or `npx`** are installed. Any Node-based recommendation below (Vite, Playwright) requires installing Node first; it is not available today.

Labels used throughout: **[FACT]** observed directly in this repository or environment; **[HYPOTHESIS]** reasoned inference, not yet verified by running code; **[DOC]** backed by an external primary source, linked inline where the claim appears; **[NEEDS DEVICE]** cannot be confirmed without a real iPhone/Safari test. All `[DOC]` claims below carry a Markdown link to the specific page fetched during this audit (2026-09-13); dates/plan terms/prices may change after that date and should be re-verified before any decision that depends on them.

---

## 1. Executive recommendation and highest-risk issues

**Recommendation:** Keep the current no-build vanilla HTML/CSS/JS architecture and GitHub Pages hosting exactly as they are today — no architecture or hosting change is recommended now. The current biggest risks are not architectural — they are (a) silently broken puzzle content already live in the runtime data, and (b) a set of concrete, fixable mobile-Safari CSS/viewport gaps. Fix those first. The one architecture change worth planning for later — modularizing `main.js`/`game.js` into ES modules, with no new build tooling — is a **deferred, trigger-conditioned** recommendation (see §3, §8, §9), not something to do now; adopting it today would be modernizing without a concrete need, which `AGENTS.md` and the handoff both instruct against.

**Highest-risk issues found, ranked:**

1. **[FACT]** `game.js:38-46` declares `"2026-06-17"` twice ("Bake Shop" then "Garden Path"). JavaScript object-literal semantics silently drop "Bake Shop"; its row is also malformed (missing comma, `game.js:41`), so it would have failed parsing anyway. This is a real player-facing content bug: any player will get "Garden Path" for a date that was also supposed to have a separate puzzle, with no console trace pointing at the discarded entry.
2. **[FACT]** `validatePuzzles()` (`game.js:325-371`) only ever calls `console.warn`/`console.info`; nothing blocks load or publishing. Four dated puzzles have marker/anagram errors (`2026-06-11`, `2026-06-16`, `2026-06-03`, `2026-06-02` — confirmed by re-deriving each row's asterisk positions against its final word) and will not be completable via the final-word bank on a touch device, since the bank only ever contains the (wrong) collected bonus letters (`main.js:837-839`).
3. **[FACT]** No `dvh`/`svh` viewport units, no `env(safe-area-inset-*)`, and no `viewport-fit=cover` appear anywhere in `style.css` or `index.html` (confirmed by grep). Combined with `html, body { height: 100%; overflow: hidden; }` (`style.css:23-25`) and `vh`-based `clamp()` sizing throughout (e.g. `--slot-h`, `#board` padding, `.word-row` margins), the layout is built entirely on the legacy `vh` unit. **[DOC]** Per MDN, [`vh` is defined as equivalent to `lvh` (the *large* viewport unit)](https://developer.mozilla.org/en-US/docs/Web/CSS/length#relative_length_units_based_on_viewport), and MDN explicitly warns that content sized with the large-viewport unit "can hide the content that is sized or positioned using the *large* viewport-percentage units" once a mobile browser's retractable toolbar (address bar) expands. **[HYPOTHESIS]** this is the most likely root cause of "unwanted scrolling," content clipped by the address bar, or bottom UI (bank/backspace) being cut off under the home indicator on notched iPhones. **[DOC]** WebKit's own guidance for notch/home-indicator devices recommends `viewport-fit=cover` plus `env(safe-area-inset-*)` padding on critical UI, [WebKit blog: "Designing Websites for iPhone X"](https://webkit.org/blog/7929/designing-websites-for-iphone-x/) — neither is present here.
4. **[FACT]** No element anywhere sets `touch-action: manipulation` (confirmed by grep), and the viewport meta tag (`index.html:5`) does not disable double-tap zoom. **[DOC]** Per MDN, [`touch-action: manipulation`](https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action) "disable[s] additional non-standard gestures such as double-tap to zoom." **[HYPOTHESIS]** its absence is the direct, fixable cause of the reported "repeated Backspace tapping causing iPhone zoom" symptom: without it, iOS Safari can interpret rapid same-spot taps on a button as a double-tap-to-zoom gesture. This is a one-line CSS fix candidate, not an architecture problem.
5. **[FACT]** There is no test suite, CI workflow, or package manifest of any kind (confirmed: no `.github/`, `package.json`, or lockfile in the repo). All release confidence today is manual.

---

## 2. Evidence and hypotheses from the current codebase

### Architecture / maintainability

- **[FACT]** No build step. `index.html:148-151` loads, in order: `canvas-confetti` from a CDN, then `game.js`, then `wordlist.js`, then `main.js`, all as classic (non-module) scripts sharing the global scope (`PUZZLES`, `PUZZLE_ANSWERS`, `WORD_LIST`, `S`, `Timer`, etc.).
- **[FACT]** `game.js` mixes authored content (`PUZZLE_ROWS`, `game.js:38-116`) with the parsing/scrambling engine (`parsePuzzleRow`, `deterministicScramble`, `computeBonusSlotOrder`) in the same file. Editing a puzzle means hand-editing a JS object literal with asterisk-marker syntax that is easy to get wrong (see the missing comma above).
- **[FACT]** `main.js` (1701 lines) owns rendering, input, timer, hints, persistence, streaks, achievements, sharing, analytics, feedback, and date selection in one file with a single global `S` state object (`main.js:229-240`). There are no module boundaries; everything communicates through shared globals and direct DOM queries by ID.
- **[FACT]** External dependencies: Google Fonts (`index.html:25-27`) and `canvas-confetti@1.9.2` from `cdn.jsdelivr.net` (`index.html:148`), both unpinned to a local copy — an outage or CDN block loses the font and/or confetti but not core gameplay (confetti call is guarded by `typeof confetti === 'function'`, `main.js:1544`).
- **[FACT]** Testability: pure functions (`deterministicScramble`, `lcgPermutation`, `computeBonusSlotOrder`, `parsePuzzleRow`) are already side-effect-free and could be unit tested today with zero framework — this is a low-cost improvement independent of any bigger migration.

### CSS / layout / viewport (see risk #3–4 above for the concrete gaps and citations)

- **[FACT]** `#app` is capped at `max-width: 480px` (`style.css:384`) and centered — desktop framing is intentionally a mobile-width column, consistent with a phone-first daily word game; this is a design choice, not a bug.
- **[FACT]** `--tile-sz: clamp(36px, calc((100vw - 74px) / 8), 44px)` (`style.css:18`) sizes bank tiles off raw viewport width; on very narrow phones (e.g. iPhone SE, 320–375px logical width) this is untested and could compress the shuffle/backspace buttons.
- **[HYPOTHESIS]** Landscape phone orientation is a likely failure mode: `#board { overflow: hidden }` (`style.css:562-566`) with six fixed-margin rows could exceed a short landscape viewport height, silently clipping the bottom row(s) rather than scrolling.

### Input / touch / accessibility

- **[FACT]** All interaction is via `click` listeners (slots, tiles, buttons — `main.js:672,865,868,881,891` etc.), not raw `touchstart`, which is the safer default (avoids double-firing between touch and synthesized click) but does not by itself prevent the double-tap-zoom issue noted above. **[DOC]** MDN notes that `touch-action: manipulation` also removes the browser's click-event delay used to detect double-tap, a secondary responsiveness benefit beyond the zoom fix ([MDN: touch-action](https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action)).
- **[FACT]** Keyboard support exists in parallel (`onKey`, `main.js:1240-1262`: arrows, Tab, Backspace, Enter, A–Z) — desktop/hardware-keyboard users have a full input path; there is no `aria-live` region announcing wrong/correct guesses or solved rows, and slots/tiles are plain `div`s with no ARIA roles — screen-reader accessibility is effectively unaddressed today (see §6 for explicit ownership of this gap).
- **[FACT]** `document.addEventListener('visibilitychange', ...)` (`main.js:1215-1218`) pauses/resumes the timer on tab/app backgrounding — this is the one piece of "suspension" handling that exists; it does not persist anything beyond what `saveState()` already writes on every input action. **[NEEDS DEVICE]** whether iOS actually reloads the page (vs. suspending JS in place) under memory pressure the way this code assumes is unconfirmed without a real device.

### Persistence / storage

- **[FACT]** localStorage keys, confirmed by grep of `main.js`: `juggle_settings`, `juggle_puzzle_<date>`, `juggle_visits`, `juggle_achievements`, `juggle_ach_counts`, `juggle_completions`, `juggle_session_<date>`.
- **[FACT — corrected]** Storage-access safety is **not uniform**, contrary to a blanket "all reads are wrapped" claim. Wrapped in `try/catch`: `loadSettings` (`main.js:258-262`), `saveState`/`loadState` (`main.js:264-323`), `recordVisit`/`getStreak` (`main.js:328-357`), achievements/completions read-write (`main.js:391-419`). **Unguarded** (no `try/catch`): `saveSettings()` (`main.js:251-256`, a plain `localStorage.setItem` call) and `getAnalyticsSessionId()` (`main.js:1657-1672`, both the `localStorage.getItem` read at line 1659 and the `localStorage.setItem` write at line 1668). In Safari private browsing or under a full storage quota, either of these can throw synchronously and uncaught — `saveSettings()` is called directly from click/change handlers (e.g. the hard-mode and timer-hide toggles, `main.js:567-575`, and `onReady`, `main.js:582-593`), so an uncaught exception there would abort the rest of that handler's work (e.g., `onReady` would not reach `Timer.start()`/`saveState()`/`trackEvent('start')` if `saveSettings()` throws first). This is the actual, narrower failure surface — not "every localStorage access is safe."
- **[FACT — corrected]** `hardMode` restoration: `init()` calls `loadSettings()` and restores **only** `Timer.hidden` from it (`main.js:518-519`: `Timer.hidden = settings.timerHidden ?? false;` — `hardMode` is never read from `settings` here). `S.hardMode` starts at its `S` object default of `false` (`main.js:235`) and is overwritten **only if** `loadState()` finds an existing per-date save (`main.js:312`: `S.hardMode = d.hardMode ?? false;`). In other words: starting a *new* puzzle never restores the player's previously-chosen Hard Mode preference from global settings, even though `saveSettings()` persists `hardMode` globally on every toggle change (`main.js:252-255`) — that saved value is only ever read back by an *existing* per-date save, not by a fresh one. This matches `CURRENT_STATE.md`'s note exactly and corrects the previous version of this audit, which incorrectly implied `hardMode` was restored from global settings for new puzzles too.

### Puzzle/content loading and operations

- **[FACT]** `parsePuzzleRow` (`game.js:120-192`) rejects a row only for wrong item count or non-6-letter/non-alphabetic answers; marker-count ≠ 6 and non-anagram bonus letters are warnings only (`game.js:164-174`), so bad rows still ship to players.
- **[FACT]** `getActivePuzzle()` (`main.js:462-469`) falls back to "most recent date ≤ requested" with no future-date leakage (good), but silently reuses the same puzzle content for every date past the last scheduled one (`2026-06-17`) while displaying the real requested date — confirmed logic matches `CURRENT_STATE.md`. As of today, 2026-09-13, every visit is silently served "Garden Path" under today's real date and gets its own separate save under `juggle_puzzle_2026-09-13`.
- **[FACT]** Future puzzle content ships in the same `game.js` bundle as everything else — **there is no secrecy boundary today**; any answer for any future scheduled date is visible in page source the moment it's committed and deployed (see §5 for the operating-model recommendation this drives).

### Deployment

- **[FACT]** Remote is `https://github.com/playjuggle/playjuggle.github.io.git`; no Actions workflow, build script, or generated-site directory exists. Consistent with GitHub Pages serving directly from `main` at the repo root (standard for a `<owner>.github.io` repo). **[DOC]** [GitHub Pages: configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) confirms two supported publishing methods (deploy from a branch, or a custom GitHub Actions workflow) and states plainly that "GitHub Pages sites are publicly available on the internet, even if the repository for the site is private" — i.e., no built-in access control regardless of which method is used.

---

## 3. Architecture options comparison

| Option | Migration cost | Regression risk | Browser reliability | Testability | Dev ergonomics | Dependency/security burden | Fit for likely scope |
|---|---|---|---|---|---|---|---|
| **1. Current no-build vanilla** | None | None (status quo) | Same as today — good, since no build toolchain can introduce transpilation/polyfill bugs | Low today, but pure functions are already testable without a framework | Low friction to edit content; high friction to reason about global state as file grows | Zero (2 CDN scripts only) | Good fit for a small daily game with 1 active writer |
| **2. Modular vanilla JS (ES modules, still no build)** | Low–medium: split `main.js`/`game.js` into modules, add `<script type="module">` | Low: mostly mechanical extraction; risk is import-order/circular-dependency mistakes | Same as #1 — native browser ES modules are broadly supported | Improves: modules can be imported into a headless test runner | Improves readability/navigation of the 1700-line file without adding tooling | Zero new dependencies | Good middle step **if and when** `main.js` keeps growing or a second regular contributor joins |
| **3. Vite + TypeScript, no UI framework** | Medium: introduces `package.json`, `node_modules`, a build/dev-server workflow, TS types for existing globals | Medium: build-time bugs (path resolution, asset URLs, env handling) are a new failure class that doesn't exist today | Same runtime output (still compiles to plain JS/CSS) — reliability is about the *build*, not the browser | High: enables fast unit tests (Vitest) and typed refactors | High once set up, but **requires installing Node locally first** (not present in this environment today) and ongoing dependency maintenance | New: `node_modules` supply chain, need for periodic `npm audit`/updates | Reasonable only if puzzle/content tooling or contributor count grows enough to want types and fast unit tests |
| **4. UI framework (React/Vue/etc.)** | High: rewrite of DOM-manipulation code in `main.js` to a component model | High: this is a full behavioral rewrite of interaction/rendering logic; the current bug surface (viewport, touch, iOS Safari quirks) is not framework-related and would not be fixed by adopting one | No inherent improvement — framework doesn't change WebKit/Safari behavior | Improves component-level testing, but at a cost disproportionate to a single-page word game | Higher long-term ergonomics for a growing app; overkill for current scope | Meaningfully larger dependency surface | **Not justified** — no material product advantage identified for a five-word daily puzzle with one screen and no routing/auth needs |

**Recommended target, stated once and used consistently throughout this document (§1, §8, §9): keep Option 1 (current no-build vanilla) now.** No architecture change is authorized or recommended today. **Option 2 (modular ES modules, zero new tooling) is the recommended *next* step, but only once a concrete trigger occurs** — `main.js`/`game.js` continuing to grow, or more than one person regularly editing them concurrently — and is not scheduled or implied to happen soon. **Option 3 (Vite + TS) is deferred further still**, behind Option 2, and requires installing Node first regardless. **Option 4 (a UI framework) is not recommended at any point under current scope** — no requirement in this repo (routing, component reuse, complex client state) benefits from one, and it would not address any of the actual reported bugs (all of which are CSS/viewport/data-validation issues, not rendering-architecture issues).

---

## 4. Hosting and deployment comparison

Source control (GitHub) is not in question — it stays. This section is about *hosting* only. All feature claims below are sourced from official docs fetched 2026-09-13; verify again before any actual decision, since plan terms and limits change.

| Platform | Preview deployments | Rollback | CI/test integration | Future-puzzle secrecy | Cost | Lock-in | Notes |
|---|---|---|---|---|---|---|---|
| **GitHub Pages** (current) | Not built in — [GitHub Pages docs](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) describe direct publish from a branch, or a custom Actions workflow; neither is a per-PR preview URL feature. | Not built in — rollback means reverting the commit/branch that Pages serves from. | External only (e.g., a separately-added GitHub Actions workflow); none exists today. | None — [same page](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) states "GitHub Pages sites are publicly available on the internet" regardless of repo visibility settings. | Free for public repos (standard GitHub Pages offering; not separately re-verified for pricing changes here). | Minimal — plain static files, trivially portable to any static host. | Simplest possible operational model; matches "no daily human maintenance, no paid service" constraint well. |
| **Cloudflare Pages** | Yes, per branch — [Cloudflare Pages: preview deployments](https://developers.cloudflare.com/pages/configuration/preview-deployments/): each branch gets a unique alias URL (e.g. `<branch>.<project>.pages.dev`) plus a per-deployment hash URL; PRs from forks do not get preview URLs; all preview URLs send `X-Robots-Tag: noindex`. Docs state "an unlimited number of preview deployments" may be active at once. | Yes, for **production** deployments only — [Cloudflare Pages: rollbacks](https://developers.cloudflare.com/pages/configuration/rollbacks/): one-click "Rollback to this deployment" from the dashboard; explicitly "preview deployments are not valid rollback targets." | Native Git-based build-and-deploy on push. | No better than any static host by default — still a public bundle unless a Worker/Function gate is added. | Free tier is **500 builds/month** (not "deploys" — a build is what a push triggers; preview-deployment *count* is separately unlimited) per [Cloudflare Pages: limits](https://developers.cloudflare.com/pages/platform/limits/), which also lists 20,000 files/site (free) and a 25 MiB per-file cap. Paid tiers raise build and file caps. | Low-medium — Cloudflare's own [Pages overview](https://developers.cloudflare.com/pages/) states "Workers supports most Pages use cases and offers a broader feature set" and calls Workers "Cloudflare's primary platform for building applications," i.e. Cloudflare is steering new projects toward Workers over Pages. | Best low-effort upgrade path if PR-preview URLs and one-click production rollback become valuable; verify current limits again before committing, since free-tier numbers can change. |
| **Cloudflare Workers (static assets)** | Yes, per branch, contrary to the previous version of this audit — [Cloudflare's own Pages-to-Workers migration guide](https://developers.cloudflare.com/workers/static-assets/migration-guides/migrate-from-pages/) confirms preview URLs are "on by default" and that enabling "non-production branch builds" in Workers Builds reproduces Pages-style per-branch previews, with the caveat that this "does not yet have the same level of configurability as Pages does." | Standard Workers/Wrangler deployment rollback; the fetched migration guide does not fully detail one-click parity with Pages — **needs verification** against Wrangler's own rollback docs before relying on it. | Requires `wrangler` CLI/config (needs Node) — more tooling overhead than Pages' zero-config Git integration. | Same as any static host. | Usage-based billing; the migration guide does not itself state numeric limits — **needs verification** against Cloudflare's current Workers pricing page. | The same migration guide frames Workers as having "a distinctly broader set of features" (Durable Objects, Cron Triggers, more Observability) without explicitly telling new static-site projects to prefer Workers over Pages — it is a migration guide, not a greenfield recommendation. | More power (can add server logic later) than this project currently needs; roughly at parity with Pages for preview URLs today, contrary to what the previous audit draft assumed. |
| **Vercel** | Yes — [Vercel: deployments overview](https://vercel.com/docs/deployments/overview) confirms "each commit or pull request... automatically triggers a new deployment," with distinct Preview and Production environments. | Yes, but **plan-gated**: per [Vercel: Instant Rollback](https://vercel.com/docs/instant-rollback), Hobby (free) accounts "can roll back to the previous deployment" only; Pro/Enterprise can roll back to *any* deployment that was previously aliased to production. Only deployments that were once live in production are eligible — ordinary preview deployments are not rollback targets. | Native Git deploy-on-push; framework-agnostic static hosting supported. | **Partially available for free, partially paid**: per [Vercel: methods to protect deployments](https://vercel.com/docs/deployment-protection/methods-to-protect-deployments) and [Vercel's own "Deployment Protection... available on all plans" post](https://vercel.com/blog/protecting-deployments), **Vercel Authentication** (require a Vercel account or a shared link to view non-public preview URLs) is free on every plan; **Password Protection** is part of "Advanced Deployment Protection," a paid add-on (quoted at $150/mo on Pro, bundled into Enterprise) — it is not free-tier. Trusted IPs plan-availability was not stated in the fetched pages and needs verification. | Free Hobby tier exists; exact current build-minute/bandwidth limits should be checked at deploy time, not assumed from memory — not independently re-verified in this pass. | Higher — richer platform (functions, edge middleware, AI/agent tooling) than a static game needs; lock-in here is mostly about workflow/tooling habits, not data, since the core artifact is still static files. | Strongest preview/rollback ergonomics of the three alternatives, but the *free-tier* rollback story (previous-deployment-only) and the *paid* password-gating for previews are real, plan-specific caveats — do not assume full parity with the paid-tier feature set when comparing against GitHub Pages/Cloudflare Pages free tiers. |

**Recommendation, unchanged from the executive summary: keep GitHub Pages** for now — it fully satisfies "no daily human maintenance, no required paid service, no required AI agent," and none of the reported bugs are hosting-related. **If** preview-before-publish and one-click rollback become a real operational need (e.g., once a non-technical puzzle author is involved), **Cloudflare Pages** is the better-fitting upgrade over Vercel for a project this size: no build-tooling requirement beyond what's already true today, a generous free tier per the limits above, and — per Cloudflare's own migration guide — near feature parity with Workers on preview URLs today, so there is no urgency to choose Workers over Pages specifically for that reason. This remains a **Defer**, not a **Replace** — do not migrate without a concrete trigger.

---

## 5. Future puzzle/content operating model

Recommended model, addressing every required element. Where secrecy and zero-maintenance publication could conflict, the choice below is made explicit rather than asserting both at once.

- **Bulk creation/import:** Author puzzles in a plain data file separate from game logic — this was already scoped as the (currently queued, not active) "Puzzle Data Safety Foundation" task in `juggle-autonomy/queued/PUZZLE_DATA_SAFETY_FOUNDATION.md`. That task's design (a dedicated data file + a stdlib-only Python validator script) is sound and requires no new runtime dependency.
- **Schema/full-batch validation:** A local `python3 scripts/validate_puzzles.py` (per the queued task) that checks every entry in one pass — duplicate dates, malformed rows, marker/anagram mismatches, schedule gaps — and exits nonzero on any failure. This directly fixes Findings #1–2 in §1 without needing Node, a build step, or CI.
- **Scheduled availability / timezone semantics — recommended present choice:** keep `todayKey()`/`realTodayKey()`'s current *browser-local-date* semantics (`main.js:55-65`) exactly as they are; do not change puzzle-release timing behavior as part of this audit. State the tradeoff explicitly for the owner: two players in different timezones can see different puzzle dates at the same real-world moment, since there is no server-side "release at a fixed UTC time" concept in a static-only site. Introducing a fixed release timezone would be a genuine behavior change requiring explicit product authorization per `AGENTS.md` ("Preserve existing gameplay and UI behavior unless the active task explicitly authorizes a change") — it is not something this audit unilaterally recommends adopting.
- **Future-answer privacy — recommended present choice, stated once and not contradicted elsewhere in this document:** **accept that all committed-and-deployed puzzle data, including near-future dates, is public and downloadable**, per the handoff's own instruction to state this boundary honestly. The present-day operating model is therefore: *bulk-validate a full schedule locally with the recommended validator, and commit/deploy it on the normal cadence, without attempting to hide future answers by obscuring them client-side (base64, split arrays, etc. — none of which actually withholds the data).* **Separately, and only if spoiler-secrecy becomes an explicit future product requirement:** a genuinely private-until-release model would need infrastructure this project does not have today — e.g., a small serving layer (a Worker/Function/endpoint) that withholds not-yet-released entries from the shipped bundle, or a build step that excludes future-dated entries at publish time. That option is **explicitly deferred**, not partially adopted; do not simultaneously claim "don't ship until close to release" as a present mitigation and "zero daily maintenance" as a present property — the recommendation above (accept public future data, validate and ship on schedule) is the one that is actually zero-maintenance today, and the private-source alternative is the one that would cost maintenance/infrastructure if ever adopted.
- **Preview/review workflow:** The existing `?date=YYYY-MM-DD` query param (`main.js:61-65`) already lets an author preview any date's puzzle without needing a backend. `CURRENT_STATE.md` correctly flags that preview is not fully side-effect-free (it can emit analytics and affect completion/achievement records) — worth a small, separately-scoped fix (e.g., suppress `trackEvent` and achievement writes when `?date=` is present) but that is out of this audit's allowed scope.
- **Rollback/correction policy:** Per `AGENTS.md`, published-puzzle corrections require explicit owner approval and a documented reason. Operationally: keep corrections as normal commits (Git history *is* the rollback mechanism at this scale); do not add a special rollback system.
- **Zero-daily-human-maintenance publication:** Already true in the sense that no human has to "release" anything — puzzles simply become active once their date arrives, consistent with the accept-public-data choice above. What's missing is *validation before merge*: running the recommended `validate_puzzles.py` before committing new content closes the correctness gap without adding automation the owner didn't ask for, and without requiring the deferred private-source infrastructure.
- **Local operation without ChatGPT Work credits:** The recommended validator is a local Python script with no external calls — fully satisfies this constraint.

---

## 6. Cross-browser testing matrix

Proportionate to a small static game — no framework, no paid device cloud required for the baseline tier. Concern-by-concern ownership is assigned explicitly below so nothing is implicitly uncovered.

### Ownership by concern

| Concern | Local (manual / pre-commit) | Chromium CI *(deferred — no CI exists today)* | WebKit CI *(deferred; caveat below)* | Preview-deployment gate *(N/A today — see note)* | Real-device smoke |
|---|---|---|---|---|---|
| Layout overflow | ✅ primary today (DevTools emulation) | Would own automated viewport-overflow assertions once adopted | Secondary, same caveat as all WebKit CI rows | Would re-check against the live preview URL once a preview-capable host exists | Confirms on real hardware |
| Visual framing (desktop/tablet/mobile sizing) | ✅ primary today | Visual-diff screenshots once adopted | Secondary | Same as above | Spot-check only |
| Dynamic viewport (toolbar collapse) | Cannot reliably reproduce with DevTools alone | Cannot reproduce (static viewport only) | Cannot reproduce (no real toolbar behavior) | Cannot reproduce | ✅ **only reliable owner** — see §7 |
| Safe areas / notch | Limited — Safari Web Inspector can simulate device frames but not full physical certainty | Not applicable | Not applicable | Not applicable | ✅ **primary owner** — see §7 |
| Gesture / double-tap zoom | ✅ static check only (confirm `touch-action: manipulation` is present in CSS) | Cannot reliably reproduce real gesture recognition | Cannot reliably reproduce | Not applicable | ✅ **primary owner** — see §7 |
| Keyboard input | ✅ today | ✅ **primary owner once adopted** — fully scriptable | Secondary | N/A | Not needed (desktop-oriented concern) |
| Accessibility (ARIA, screen reader, focus) | ✅ **primary owner today** — manual keyboard/VoiceOver spot check by the implementer before any UI change ships; **this is currently the only assigned check, and it is manual, not automated** — flagged as a real gap, not silently covered | Would own automated `axe-core`-style checks once both CI and an accessibility-testing decision are adopted (not currently planned; would need explicit scoping) | Same caveat as above | N/A | Manual spot check only |
| Persistence — **same-browser** reload/suspend restoration | ✅ today (manual reload test) | ✅ primary owner once adopted — scriptable via localStorage inspection | Secondary | Would re-check on the preview URL once adopted | Confirms real suspend/resume (§7) |
| Persistence — **cross-browser/device** restoration | **Not supported and not tested** — `localStorage` is scoped to one origin within one browser profile; Chrome-to-Safari or device-to-device sync does not exist and is not a bug to fix. Documented here so it is not silently assumed to work. | N/A | N/A | N/A | N/A |
| Date selection / fallback (`?date=`, `?reset`, schedule fallback) | ✅ primary today (already testable via `python3 -m http.server`) | ✅ primary owner once adopted | Secondary | Would re-check on preview URL | Not needed |
| Core gameplay (solve flow, hard mode, hints, achievements) | ✅ primary today | ✅ **primary automation target once adopted** | Secondary | Would gate promotion to production once adopted | Confirms real-device feel |

**Preview-deployment gate note:** no preview-capable host is in use today (GitHub Pages has none — §4); this column is a placeholder for *if* Cloudflare Pages or an equivalent host is ever adopted per §4's deferred recommendation. At that point its role would be: re-run the local/Chromium checks above against the live preview URL before promoting to production — not a new category of check, just a later gate for the same checks.

**WebKit CI caveat, restated per the handoff's requirement:** **[DOC]** Playwright's own docs state its WebKit build "doesn't work with the branded version of Safari" — it is a patched, open-source WebKit build, useful as an approximate desktop-Safari proxy but not a substitute for Safari, and it has **no iOS-specific build at all** ([Playwright: browsers](https://playwright.dev/docs/browsers)). Every WebKit-CI row above is marked "secondary" for exactly this reason — it can catch some rendering differences from Chromium but cannot validate any iOS-Safari-specific behavior in the rows above where only "Real-device smoke" is marked as the primary/only reliable owner.

### Suggested viewport/device set (portrait + landscape each, where applicable)

| Class | Example | Why |
|---|---|---|
| Small phone | 375×667 (iPhone SE-class logical size) | Tightest fit for 6-row board + bank |
| Standard notched phone | 390×844 (iPhone 12/13/14-class) | Most common notch + home-indicator safe-area case |
| Large phone | 428×926 (iPhone Pro Max-class) | Upper bound for `--tile-sz` clamp behavior |
| Small tablet / large-phone landscape | ~768 width | Landscape clipping risk (`#board { overflow: hidden }`) |
| Desktop | ≥1024 width | Confirms `max-width: 480px` centered-column framing looks intentional, not broken |

---

## 7. Minimal real-iPhone Safari smoke-test protocol

Automation (Playwright WebKit, DevTools emulation) cannot prove any of the following — they require a physical iPhone running real Safari. These are the same rows marked "real-device smoke" as sole/primary owner in §6.

1. **Browser chrome behavior:** load the page fresh, scroll, and confirm the address bar collapsing/expanding does not clip the board or bank (directly tests the `vh`/`lvh` risk in Finding #3, §1).
2. **Notch/home-indicator safe areas:** on a notched iPhone in both orientations, confirm no interactive element (backspace, shuffle, hint button) sits under the status bar or home-indicator gesture zone (tests the missing `viewport-fit=cover`/`env(safe-area-inset-*)` gap).
3. **Zoom/gesture interference:** rapidly tap the backspace button ~10 times in place; confirm the page does not zoom (directly tests Finding #4 and any fix applied for it).
4. **Orientation change mid-game:** rotate portrait→landscape→portrait mid-puzzle with tiles placed; confirm no state loss and no layout clipping.
5. **Suspend/restore (same-browser only — see §6's persistence split):** start a puzzle, switch to another app for 30+ seconds (trigger real iOS backgrounding, not just a tab switch), return, and confirm the timer/board state restore correctly from `localStorage` (validates the `visibilitychange` assumption, `main.js:1215-1218`). This tests same-browser restoration only; cross-browser/device sync is out of scope because it is not a supported feature (§6).
6. **Different phone sizes:** repeat steps 1–3 on at least one small (SE-class) and one large (Pro Max-class) device if available; otherwise flag as an evidence gap.

This protocol is intentionally short — five to six checks, a few minutes total — proportionate to a small static game, not a full regression pass.

---

## 8. Phased migration sequence

Ordered by product value ÷ regression risk (highest first). Architecture timing here matches §3 exactly: Option 2 is a deferred, trigger-conditioned step, not a scheduled phase.

| Phase | Work | Value | Risk | Depends on |
|---|---|---|---|---|
| **0 (this audit)** | Document findings only | — | None | — |
| **1** | Fix the two concrete, low-risk CSS/viewport bugs: add `touch-action: manipulation` to interactive elements; add `viewport-fit=cover` + `env(safe-area-inset-*)` padding; evaluate replacing key `vh` usages with `svh`/`dvh` with a fallback | High (directly fixes reported symptoms) | Low — CSS-only, no behavior/logic change | Real-iPhone smoke test to confirm (§7) |
| **2** | Extract puzzle data into a dedicated data-only file + stdlib Python validator (the already-queued, not-yet-active task) — fixes Findings #1–2 by making bad data *visible*, without touching historical content | High (prevents silent content bugs) | Low — additive, no runtime behavior change per that task's own constraints | User authorization to promote the queued task |
| **Deferred, trigger-conditioned (not a scheduled phase)** | Modularize `main.js`/`game.js` into ES modules (Option 2, §3) | Medium (maintainability), only once the trigger below occurs | Low-medium (mechanical, but touches every file) | Trigger: `main.js`/`game.js` continuing to grow, or a second regular contributor — neither has occurred yet |
| **Deferred further still (not a scheduled phase)** | Add a minimal local Playwright Chromium smoke suite (gameplay, persistence, date fallback) | Medium (catches regressions before they ship) | Low, but requires installing Node first (not present today) | Node/npm installation, and would logically follow the ES-module step above |
| **Deferred furthest (not a scheduled phase)** | Vite + TypeScript (Option 3, §3) | Speculative until content/contributor volume grows | Medium (new build-time failure class) | The ES-module step above, first |
| **Not recommended at any point** | UI framework adoption (Option 4); hosting migration off GitHub Pages | No identified material advantage today | N/A | Would need a concrete future trigger (§4/§9) that does not exist today |

---

## 9. Keep / Replace / Defer

- **Keep:** No-build vanilla HTML/CSS/JS architecture (Option 1, §3) — this is the recommended target *now*, not a placeholder; GitHub Pages hosting; client-only `localStorage` persistence model (including its documented same-browser-only restoration scope, §6); manual Git-history-as-rollback for puzzle corrections; `?date=`/`?reset` preview mechanism; current browser-local-date puzzle-release timezone semantics (§5).
- **Replace:** The current silent-warning-only puzzle validation (`validatePuzzles()`) with a blocking, pre-commit validator — this is a correctness fix, not an architecture change. Add `touch-action: manipulation` and safe-area CSS — same category. Wrap `saveSettings()` and `getAnalyticsSessionId()` in the same `try/catch` pattern already used elsewhere in `main.js` — same category (a defensive-coding correctness fix, not an architecture change).
- **Defer:** ES-module refactor of `main.js`/`game.js` (Option 2, §3) — recommended *next* architecture step once its stated trigger occurs, not adopted now; Vite/TypeScript adoption (Option 3); any UI framework (Option 4, not recommended at any point); migration off GitHub Pages to Cloudflare Pages/Vercel; Playwright CI; the private-source/scheduled-release puzzle-secrecy model (§5) unless spoiler-secrecy becomes an explicit requirement.

---

## 10. Open decisions and evidence gaps requiring user input or real-device verification

1. **Real-iPhone Safari testing has not been performed** (explicitly out of scope for this read-only audit) — every claim in §1 (Finding #3–4) about `vh`/safe-area/double-tap-zoom is a strong, code-grounded and now doc-backed **[HYPOTHESIS]**, not a confirmed reproduction. Run §7 before trusting any CSS fix.
2. **Whether to promote the queued "Puzzle Data Safety Foundation" task** (`juggle-autonomy/queued/PUZZLE_DATA_SAFETY_FOUNDATION.md`) is a decision for the user/Codex, not this audit — it directly addresses Findings #1–2 and is already fully scoped.
3. **Whether the four known-bad puzzle rows** (`2026-06-11`/`2026-06-16` "Hard Hat Zone", `2026-06-03` "Once Upon a Time", `2026-06-02` "Animal Kingdom") and the dropped "Bake Shop" entry should be corrected — per `AGENTS.md`, this requires explicit owner-confirmed dates/markers and is out of this audit's scope.
4. **Whether cross-timezone puzzle-date skew is acceptable, and whether spoiler-secrecy for future puzzles is ever required** (§5) — both are product decisions this audit deliberately does not make; it documents the present behavior and the cost of changing it.
5. **Cloudflare/Vercel current pricing and exact free-tier limits should be re-verified at the time of any actual hosting decision** — this revision sources specific figures (Cloudflare Pages: 500 builds/month free, 20,000 files, 25 MiB/file; Vercel: Password Protection at $150/mo on Pro) from pages fetched 2026-09-13, but Workers static-assets pricing and Trusted IPs plan-availability were not confirmed in the fetched pages and are flagged `needs verification` inline in §4.
6. **Node.js is not installed in this environment** — confirm whether the owner's actual working machine has it before assuming the deferred Chromium-CI or Vite phases in §8 are readily reachable.
7. **The accessibility gap in §6 has no automated owner today** — it is explicitly a manual-only check; deciding whether to invest in automated accessibility tooling (and when) is an open product decision, not something this audit resolves.

---

## Required validation

Commands run from the repository root, exact output below (rerun after this correction).

```
$ git status --short --branch
## main...origin/main
 M .gitignore
?? AGENTS.md
?? CLAUDE.md
?? CURRENT_STATE.md
?? HANDOFF.md
?? PLATFORM_AUDIT.md
?? juggle-autonomy/
?? tools/
```

```
$ test -f PLATFORM_AUDIT.md
(exit 0)
```

```
$ git diff --check
(exit 0, no output)
```

```
$ git diff --exit-code -- game.js main.js style.css index.html wordlist.js
(exit 0, no output — no changes to any application file)
```

```
$ git status --short --branch
## main...origin/main
 M .gitignore
?? AGENTS.md
?? CLAUDE.md
?? CURRENT_STATE.md
?? HANDOFF.md
?? PLATFORM_AUDIT.md
?? juggle-autonomy/
?? tools/
```

**Changed/untracked paths, before vs. after this task:** `AGENTS.md`, `CLAUDE.md`, `CURRENT_STATE.md`, `HANDOFF.md`, `juggle-autonomy/`, `tools/`, and the modified `.gitignore` were all already present/untracked before this task and were not touched. The only path this task (including this correction pass) created or modified is `PLATFORM_AUDIT.md`. No application/source file, puzzle content, dependency manifest, or deployment configuration was changed.

No local server was started and no browser/localStorage state was mutated during this audit or this correction pass, per the handoff's explicit instruction; all behavioral claims above are either static-code analysis **[FACT]**/**[HYPOTHESIS]** or externally documented **[DOC]** with an inline link to the specific page fetched, and real-device gaps are called out explicitly in §10.
