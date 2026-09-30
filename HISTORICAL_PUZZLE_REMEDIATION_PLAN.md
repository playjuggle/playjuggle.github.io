# Historical Puzzle Archive Remediation — Decision Package

**Status:** Decision-ready proposal. Read-only investigation only — no `puzzles.js`, application code, or other tracked/untracked file was modified while producing this document. This file is the only artifact created by this task.

---

## 1. Executive summary

**Recommendation:** Adopt the single 25-entry replacement dataset in §6 for the full `2026-05-24`..`2026-06-17` publishing range. It:

- leaves 13 of the archive's 18 existing effective date entries byte-for-byte unchanged (same theme, five answers, final word, and date);
- repairs the three marker/anagram defects (`2026-06-11`, `2026-06-03`, `2026-06-02`) by moving the minimum number of asterisks needed to make the six marked letters anagram to the final word, without touching any answer, theme, or date;
- resolves the `2026-06-17` duplicate declaration by keeping "Garden Path" (the puzzle that has always actually won at runtime) and dropping the never-effective "Bake Shop" declaration from that date;
- repairs Bake Shop's row (missing delimiter, wrong marked letter) and reuses it, honestly labeled as an archive repair, on `2026-06-12` — one of the seven dates that currently have no declared puzzle at all — rather than presenting it as something `2026-06-17` players ever saw;
- replaces the two duplicate-content puzzles (`2026-06-16` and `2026-05-31`, each byte-identical to an earlier date) with two new original puzzles, since deleting those dates outright is not an option — the range must stay contiguous;
- fills the remaining six gap dates with six new original puzzles;
- leaves the publishing-range endpoints (`2026-05-24`..`2026-06-17`) unchanged.

**Precise baseline count, stated once here and used consistently below:** the current runtime has **18 effective date keys** but only **16 distinct puzzle-content signatures**, because two rows are each effective under two dates (Hard Hat Zone: `2026-06-11`/`2026-06-16`; Airplane Mode: `2026-05-30`/`2026-05-31`). Three distinct content signatures are structurally invalid today (Hard Hat Zone, Once Upon a Time, and Animal Kingdom). Among the 18 existing effective date entries, this proposal leaves 13 valid, non-duplicated entries untouched; repairs 3 marker-invalid entries; and replaces the later entry in each of the 2 duplicate-content pairs.

**Player/product rationale:** this is the smallest edit that turns “every blocking validator error, plus a dropped historical puzzle” into “zero blocking errors” while retaining every valid, non-duplicated effective entry. Of the dates that already have declarations, 13 remain untouched, 3 receive marker-only repairs, and only the 2 later duplicate-content dates (`2026-06-16`, `2026-05-31`) receive new answers. The 7 undeclared dates become real archive entries instead of continuing to replay fallback content; because players could have saved that fallback state under those dates, the bundled migration in §8 explicitly protects compatibility.

---

## 2. Source-history and effective-runtime findings

Confidence and method: derived from `git log -p --follow -- game.js` (the puzzle data lived in `game.js` before the pending, currently-uncommitted split into `puzzles.js`; `puzzles.js` itself is untracked and has no independent git history yet) and from reading `puzzles.js`, `game.js`, `scripts/validate_puzzles.py` as they exist in this checkout. No network access was used.

**Limits of what local history proves:** this repository has no CI and no recorded deploy step (`CURRENT_STATE.md`, `PLATFORM_AUDIT.md` §2 "Deployment"). A commit landing on `main` is evidence someone intended to ship that content, not proof GitHub Pages ever served that exact commit to a real visitor, or for how long. Below, "effective" means "would win at runtime under today's overwrite semantics," not "was definitely seen by a player."

**`2026-06-17` — Bake Shop vs. Garden Path (duplicate date):**
Both declarations were introduced in the *same* commit, `e273c7f` ("New puzzles", 2026-06-16 09:01:45 -0700). The diff adds "Bake Shop" first and "Garden Path" immediately after, for the identical key. Under JavaScript object-literal semantics (the same later-entry-wins rule `PUZZLE_ROWS`/`PUZZLE_ROWS`-building code still applies today, confirmed in `CURRENT_STATE.md`), "Garden Path" has overwritten "Bake Shop" from the instant this commit landed — there is no earlier commit or intermediate state in which "Bake Shop" was ever the effective value for `2026-06-17`. It was never live, in this checkout's history, for even one commit.
Separately, the "Bake Shop" row is independently broken: `"PASTR*Y* COO*KIE, BA*TTE*R, MUFFIN, B*UTTER, BAKERY"` is missing the comma between item 1 and item 2, so it parses as five items, not six (`scripts/validate_puzzles.py` rule `row-item-count`) — it could not have functioned as a puzzle even if it had won the overwrite.

**`2026-06-11` vs `2026-06-16` — Hard Hat Zone (duplicate content, same primary-answer set and final word):**
`2026-06-11` was introduced in commit `c9a0a0a` ("Add'l puzzles", 2026-06-08 21:44:21 -0500) and has not been edited since (single commit touches it). `2026-06-16` was introduced five days of game-content later, in commit `e273c7f` (2026-06-16 09:01:45 -0700), with a row string byte-for-byte identical to `2026-06-11`'s. `2026-06-11` is therefore the strictly earlier occurrence, both by commit date and by in-game date, and was the sole "Hard Hat Zone" puzzle in the archive for eight days before the duplicate was added.

**`2026-05-30` vs `2026-05-31` — Airplane Mode (duplicate content):**
`2026-05-30` first appeared in commit `ec8a2f1` (2026-05-30 09:32:41 -0500) with a *different* row (`"WI*NDOW, BUC*K*LE, T*RAVEL, SAFE*TY, FLIGHT*, TICKET"`), then was edited twice more the same day — `c449ea3` (swap `T*RAVEL`→`DEPART*`) and `02c7c19` (a full rewrite to `"SA*FETY, BUCK*LE, WI*NDOW, ENG*INE, H*EIGH*T, FLIGHT"`) — before settling, in `def9beb` ("Today's final puzzle I hope lol", 2026-05-30 10:00:38 -0500), into the row that is still live today: `"WI*N*DOW, RUN*WAY, FLIG*HT, JE*TLAG, TICKE*T, ENGINE"`. That content was stable for a full day before `2026-05-31` was added in `cabccde` ("aesthetic updates", 2026-05-31 15:29:03 -0500) with the identical stabilized row. `2026-05-30` is the earlier occurrence by every measure. (The transient `TRAVEL`/`DEPART`/`SAFETY`/`BUCKLE`/`HEIGHT`/`ENGINE`-as-primary words tried and abandoned within `2026-05-30` on 2026-05-30 never reached a duplicate or a shipped state; they do not appear anywhere in the current archive and are not "used" by any live puzzle, so they are not treated as reserved words below.)

**Marker/anagram defects** (`2026-06-11`/`2026-06-16` "Hard Hat Zone", `2026-06-03` "Once Upon a Time", `2026-06-02` "Animal Kingdom"): each was introduced with the defect already present (no evidence in history of a prior correct version), per the errors already itemized in `CURRENT_STATE.md` and `PLATFORM_AUDIT.md`.

**Compatibility-risk analysis (localStorage):** traced directly in `main.js`.
- Per-date state key: `` `juggle_puzzle_${date}` `` (`main.js:247-249`); a parallel per-date analytics id, `` `juggle_session_${date}` ``, also exists (`main.js:1658`).
- Global keys — `juggle_settings`, `juggle_visits`, `juggle_achievements`, `juggle_ach_counts`, `juggle_completions` — use plain string literals with no date component and are written/read by entirely separate code paths (`main.js:252,260,330,333,340,392,397,402,407,413,416,560`). No per-date operation touches them; the only existing per-date clear, `?reset`'s `localStorage.removeItem(puzzleStorageKey())` (`main.js:480-482`), targets only that one date's key.
- **No content fingerprint exists today.** `saveState()`/`loadState()` (`main.js:264-323`) persist and restore only gameplay progress (`confirmed`, `guess`, `bankSlots`, `solved`, `final`, cursor, hard-mode, mistake/hint counts, timer) — never a hash or version of the puzzle's answers/row/markers.
- **No cross-check exists today.** `getActivePuzzle()` rebuilds `S.words`/`S.final` from whatever `PUZZLE_ROWS` currently declares for that date (`main.js:462-469`, 497-514); `loadState()` then overlays the *old* saved `confirmed`/`guess`/`bankSlots`/`solved` arrays onto that fresh structure purely by array index, with no comparison to the new answers or scramble. If puzzle content at a date changes between visits, the saved state is trusted uncritically: `renderSlots()`/`renderBank()` would display old guessed/confirmed letters and old bank-slot mappings against new answers/scramble, silently producing mismatched or nonsensically "solved" board state rather than erroring or resetting.
- **Twelve dates can have incompatible legacy saves.** They are the 3 marker-repair dates, the 2 duplicate-content replacement dates, and all 7 currently-missing dates. A visit to a missing date such as `2026-06-13` could have saved fallback progress against an earlier puzzle under the `2026-06-13` key; publishing a real entry makes that state stale. `2026-06-17` is not in this set because Garden Path remains its effective content.

A concrete, implementable mitigation for all of this is proposed in §8; nothing described there has been implemented as part of this task.

---

## 3. Date-by-date change table

"Prior save possible?" reflects the localStorage fallback behavior above — even nominally "missing" dates could carry a stale save from the fallback puzzle.

| Date | Theme (before → after) | Change class | Prior save possible? |
|---|---|---|---|
| 2026-06-17 | Garden Path → Garden Path | No effective change (duplicate "Bake Shop" declaration removed; "Bake Shop" was never the winning value — see §2) | Yes, under Garden Path content (unchanged) |
| 2026-06-16 | Hard Hat Zone (dup) → **Movie Night (new)** | Content replacement (duplicate-content puzzle removed) | Yes, under old duplicate Hard Hat Zone content — **will be stale** |
| 2026-06-15 | *(missing)* → **Road Trip (new)** | New puzzle on previously-undeclared date | Yes, via fallback content — **will be stale** |
| 2026-06-14 | *(missing)* → **Rainy Day (new)** | New puzzle on previously-undeclared date | Yes, via fallback content — **will be stale** |
| 2026-06-13 | *(missing)* → **Game Night (new)** | New puzzle on previously-undeclared date | Yes, via fallback content — **will be stale** |
| 2026-06-12 | *(missing)* → **Bake Shop (repaired, reused)** | Historical repair reused on a formerly-missing date, not presented as ever having run on 06-17 | Yes, via fallback content — **will be stale** |
| 2026-06-11 | Hard Hat Zone → Hard Hat Zone (marker fix only) | Marker-position repair; theme/answers/final/date unchanged | Yes — primary-letter progress stays answer-compatible, but saved bonus/final state will not match new marker assignment (see §8) |
| 2026-06-10 | Bird Watching → Bird Watching | No change | Yes, unaffected |
| 2026-06-09 | Crayon Box → Crayon Box | No change | Yes, unaffected |
| 2026-06-08 | What's for Dessert? → What's for Dessert? | No change | Yes, unaffected |
| 2026-06-07 | The Veggie Garden → The Veggie Garden | No change | Yes, unaffected |
| 2026-06-06 | Outer Space → Outer Space | No change | Yes, unaffected |
| 2026-06-05 | Hail Mary → Hail Mary | No change | Yes, unaffected |
| 2026-06-04 | X Marks the Spot → X Marks the Spot | No change | Yes, unaffected |
| 2026-06-03 | Once Upon a Time → Once Upon a Time (marker fix only) | Marker-position repair; theme/answers/final/date unchanged | Yes — see 06-11 caveat above |
| 2026-06-02 | Animal Kingdom → Animal Kingdom (marker fix only) | Marker-position repair; theme/answers/final/date unchanged | Yes — see 06-11 caveat above |
| 2026-06-01 | Class is in Session → Class is in Session | No change | Yes, unaffected |
| 2026-05-31 | Airplane Mode (dup) → **Grocery Store (new)** | Content replacement (duplicate-content puzzle removed) | Yes, under old duplicate Airplane Mode content — **will be stale** |
| 2026-05-30 | Airplane Mode → Airplane Mode | No change | Yes, unaffected |
| 2026-05-29 | *(missing)* → **Music Class (new)** | New puzzle on previously-undeclared date | Yes, via fallback content — **will be stale** |
| 2026-05-28 | *(missing)* → **Beach Day (new)** | New puzzle on previously-undeclared date | Yes, via fallback content — **will be stale** |
| 2026-05-27 | *(missing)* → **Camping Trip (new)** | New puzzle on previously-undeclared date | Yes, via fallback content — **will be stale** |
| 2026-05-26 | Breakfast → Breakfast | No change | Yes, unaffected |
| 2026-05-25 | Under the Sea → Under the Sea | No change | Yes, unaffected |
| 2026-05-24 | Around the House → Around the House | No change | Yes, unaffected |

---

## 4. Exact old-to-new row diffs for modified existing content

### 2026-06-11 / 2026-06-16 "Hard Hat Zone" (repairing the retained 06-11 occurrence)

- Old row: `HELME*T, HAM*MER, LADDE*R, WORKE*R, WREN*C*H, CEMENT`
- Marked letters before (one per word except WRENCH, which has two): HELMET→E (its 2nd E), HAMMER→M, LADDER→E, WORKER→E, WRENCH→N,C. Collected sequence: `E,M,E,E,N,C` (the validator reports this sorted as `EMEENC`) — three E's and no T. Final word CEMENT needs `C,E,E,M,N,T` — two E's and one T, not three E's.
- New row: `HELMET*, HAM*MER, LADDE*R, WORKE*R, WREN*C*H, CEMENT`
- Fix: move HELMET's single mark from its 2nd E (index 4) to its final T (index 5) — `HELME*T` → `HELMET*`. No other word changes.
- Marked letters after: HELMET→T, HAMMER→M, LADDER→E, WORKER→E, WRENCH→N,C. Collected sequence: `T,M,E,E,N,C`.
- Anagram proof: sorted `C,E,E,M,N,T` = sorted `CEMENT` (`C,E,E,M,N,T`). ✓ Exact match, 6 letters.

### 2026-06-03 "Once Upon a Time"

- Old row: `KNI*GHT, WIZAR*D, THR*ONE, CA*STLE, PR*IN*CE, DRAGON`
- Marked letters before: KNIGHT→I, WIZARD→R, THRONE→R, CASTLE→A, PRINCE→R,N. Collected sequence: `I,R,R,A,R,N` (the validator reports this sorted as `IRRARN`) — three R's and one I, with D, G, and O missing entirely. Final word DRAGON needs `A,D,G,N,O,R` — one of each letter, not three R's.
- New row: `KNIG*HT, WIZARD*, THRO*NE, CA*STLE, PR*IN*CE, DRAGON`
- Fix (smallest defensible movement — 3 of 5 words each move their *single* existing mark to a different letter already present in the same unchanged word; CASTLE and PRINCE are untouched):
  - `KNI*GHT` → `KNIG*HT`: mark moves from I (idx 2) to G (idx 3).
  - `WIZAR*D` → `WIZARD*`: mark moves from R (idx 4) to D (idx 5).
  - `THR*ONE` → `THRO*NE`: mark moves from R (idx 2) to O (idx 3).
- Marked letters after: KNIGHT→G, WIZARD→D, THRONE→O, CASTLE→A (unchanged), PRINCE→R,N (unchanged). Collected sequence: `G,D,O,A,R,N`.
- Anagram proof: sorted `A,D,G,N,O,R` = sorted `DRAGON` (`A,D,G,N,O,R`). ✓ Exact match, 6 letters.

### 2026-06-02 "Animal Kingdom"

- Old row: `JAGU*AR, RABBIT*, PAR*ROT, L*IZARD, MONKE*Y, TURTLE`
- Marked letters before: JAGUAR→U, RABBIT→T, PARROT→R, LIZARD→L, MONKEY→E. Collected sequence: `U,T,R,L,E` — only 5 marks (validator rule `marker-count`, found 5), and even as a 5-letter set it is missing one `T` versus TURTLE's required `E,L,R,T,T,U` (two T's).
- New row: `JAGU*AR, RABBIT*, PAR*ROT*, L*IZARD, MONKE*Y, TURTLE`
- Fix: add one more mark to PARROT's existing, previously-unmarked final T (the only unmarked letter it has that TURTLE still needs) — `PAR*ROT` → `PAR*ROT*`. JAGUAR, RABBIT, LIZARD, MONKEY unchanged.
- Marked letters after: JAGUAR→U, RABBIT→T, PARROT→R,T, LIZARD→L, MONKEY→E. Collected sequence: `U,T,R,T,L,E`.
- Anagram proof: sorted `E,L,R,T,T,U` = sorted `TURTLE` (`E,L,R,T,T,U`). ✓ Exact match, 6 letters, 6 markers.

### 2026-06-17 (declaration-level change, not a row edit)

- Before: two declarations for the same date — `Bake Shop` (`PASTR*Y* COO*KIE, BA*TTE*R, MUFFIN, B*UTTER, BAKERY`, malformed, never effective) and `Garden Path` (`BA*MBOO, CACT*U*S, OR*CHID, GARDEN*, FLOWE*R, NATURE`, effective).
- After: one declaration — `Garden Path`, byte-identical to today's effective row. The Bake Shop declaration is removed from this date entirely (repaired and moved — see §5).

---

## 5. New and reused puzzle details

All five new-original-content answers per puzzle are mutually distinct within that puzzle; all are familiar English words; none are proper nouns, trademarks, offensive terms, or unusually obscure vocabulary; and (checked against the full 25-entry set) none collide with an existing primary or final word anywhere else in the archive except where explicitly noted as a preservation tradeoff (Bake Shop, below). Deterministic-scramble identity and 4-letter-sequence preservation were checked by running the real scrambler (`scripts/validate_puzzles.py`, which ports `game.js`'s `deterministicScramble` exactly) against the actual candidate block in §6 — see §7 for the full result.

### 2026-06-12 — Bake Shop *(repaired historical content, reused — not new)*

- Row: `PASTR*Y*, COOK*IE, BA*TTE*R, MUFFIN, B*UTTER, BAKERY`
- Repairs applied to the original, never-effective `2026-06-17` declaration: (1) inserted the missing comma between `PASTRY` and `COOKIE` so the row has six items instead of five; (2) moved COOKIE's mark from its 3rd letter (O) to its 4th letter (K) — the original marked letters (`R,Y,O,A,E,B`) do not anagram to BAKERY (`B,A,K,E,R,Y`; wrong letter, O instead of K), and after the fix (`R,Y,K,A,E,B`) they do. No answer, theme, or intended date-of-authorship content was altered beyond that.
- Anagram proof: PASTRY contributes R (idx 4), Y (idx 5); COOKIE contributes K (idx 3); BATTER contributes A (idx 1), E (idx 4); BUTTER contributes B (idx 0); MUFFIN contributes none. Collected `R,Y,K,A,E,B`; sorted `A,B,E,K,R,Y` = sorted BAKERY. ✓
- Labeling: this puzzle was **never** playable on `2026-06-17` (§2) and is not being presented as such. It is placed on `2026-06-12`, a date that has never had any declared puzzle, and should be understood by the owner as "the Bake Shop puzzle, finally fixed and given a real publish date," not as a historical replay.
- Unavoidable inherited overlap: `PASTRY` and `COOKIE` are also primary answers in `2026-06-08` "What's for Dessert?" — this is intrinsic to the original (defective) content itself, not introduced by this proposal's choices, and cannot be removed without changing an answer in one of the two puzzles (excluded by the preservation policy). It produces two `answer-reused` warnings, attached to this entry — see §7.
- Editorial note: PASTRY, COOKIE, BATTER, MUFFIN, BUTTER are all common, easy baking vocabulary; BAKERY is an easy, highly-guessable final. Expect this to play fast and easy, similar in difficulty to the existing "What's for Dessert?" puzzle it partially overlaps with.

### 2026-06-16 — Movie Night *(new)*

- Row: `CINEMA*, AC*TIO*N, SCR*EEN, POS*T*ER, CREDIT, ACTORS`
- Marks: CINEMA→A(idx5); ACTION→C(idx1),O(idx4); SCREEN→R(idx2); POSTER→S(idx2),T(idx3); CREDIT→none. Collected `A,C,O,R,S,T`; sorted `A,C,O,R,S,T` = sorted ACTORS. ✓
- Editorial note: CINEMA, ACTION, SCREEN, POSTER, CREDIT are all everyday movie-night vocabulary, and ACTORS is a direct, concrete payoff — the people the other five words are all in service of (you buy a poster, watch the screen, read the credits, all *for* the actors). This replaces the earlier draft's final, DIRECT, which was an indirect verb-form with no natural noun relationship to the primaries; ACTORS is a plain noun with an earned, obvious tie to the theme. Expect an easy, satisfying solve.

### 2026-06-15 — Road Trip *(new)*

- Row: `T*R*AVEL, DETO*U*R, MOTE*LS, SCENIC, S*NACKS, ROUTES`
- Marks: TRAVEL→T(0),R(1); DETOUR→O(3),U(4); MOTELS→E(3); SNACKS→S(0); SCENIC→none. Collected `T,R,O,U,E,S`; sorted `E,O,R,S,T,U` = sorted ROUTES. ✓
- Editorial note: all six words are common travel vocabulary with no obscure terms; ROUTES follows directly from the theme. Expect an easy, quick solve.

### 2026-06-14 — Rainy Day *(new)*

- Row: `C*LOUD*S, PUDDLE*, SPLASH*, PON*CHO, STOR*MY, DRENCH`
- Marks: CLOUDS→C(idx0),D(idx4); PUDDLE→E(idx5); SPLASH→H(idx5); PONCHO→N(idx2); STORMY→R(idx3). Collected `C,D,E,H,N,R`; sorted `C,D,E,H,N,R` = sorted DRENCH. ✓
- Editorial note: CLOUDS, PUDDLE, SPLASH, PONCHO, and STORMY are all everyday, familiar rainy-day vocabulary — PONCHO replaces the earlier draft's NIMBUS (a meteorology term for a rain cloud) with a plainer, universally-recognized piece of rain gear, tightening familiarity without weakening the theme fit. DRENCH is an easy, natural final. Expect a fast, easy solve.

### 2026-06-13 — Game Night *(new)*

- Row: `TOKE*NS, BOA*R*D*S, PUZZL*E*, WINNER, SCORES, DEALER`
- Marks: TOKENS→E(idx3); BOARDS→A(idx2),R(idx3),D(idx4); PUZZLE→L(idx4),E(idx5); WINNER→none; SCORES→none. Collected `E,A,R,D,L,E`; sorted `A,D,E,E,L,R` = sorted DEALER. ✓
- Editorial note: the theme is renamed from the earlier draft's "Board Games" to "Game Night" — a broader, still-plain category that naturally covers TOKENS, BOARDS, and PUZZLE (board-game vocabulary) alongside WINNER, SCORES, and DEALER (card- and general-game vocabulary), resolving the earlier mismatch where DEALER (card-specific) sat under a strictly board-game theme. All six answers now plainly fit the theme as stated. Expect an easy, familiar solve.

### 2026-05-31 — Grocery Store *(new, replaces duplicate Airplane Mode; also replaces the earlier draft's "Farmers Market")*

- Row: `BASKET, A*ISLES, CO*UPON*, GROC*ER, MAR*KET*, CARTON`
- Marks: BASKET→none; AISLES→A(idx0); COUPON→O(idx1),N(idx5); GROCER→C(idx3); MARKET→R(idx2),T(idx5). Collected `A,O,N,C,R,T`; sorted `A,C,N,O,R,T` = sorted CARTON. ✓
- Editorial note: BASKET, AISLES, COUPON, GROCER, and MARKET are all common, everyday grocery-shopping vocabulary, and CARTON (egg carton, milk carton) is a direct, concrete, satisfying final. This replaces the earlier draft's "Farmers Market" (ACORNS/APPLES/LEAVES/GOURDS/MAPLES → GOLDEN), which read as an autumn-produce cluster mismatched to a late-May date; "Grocery Store" is deliberately date-neutral — grocery shopping has no season — so it carries no calendar-mismatch judgment call for the owner to weigh. Expect an easy, quick solve.

### 2026-05-29 — Music Class *(new)*

- Row: `GU*IT*AR, VIO*LIN, MELOD*Y, S*INGER, PI*ANOS, STUDIO`
- Marks: GUITAR→U(1),T(3); VIOLIN→O(2); MELODY→D(4); SINGER→S(0); PIANOS→I(1). Collected `U,T,O,D,S,I`; sorted `D,I,O,S,T,U` = sorted STUDIO. ✓
- Editorial note: GUITAR, VIOLIN, MELODY, SINGER, PIANOS are all common, familiar music vocabulary; STUDIO is an easy, natural final. Expect a fast, easy solve.

### 2026-05-28 — Beach Day *(new)*

- Row: `SUN*TAN, S*ANDAL, CO*OLE*R, C*A*BANA, TROPIC, OCEANS`
- Marks: SUNTAN→N(2); SANDAL→S(0); COOLER→O(1),E(4); CABANA→C(0),A(1); TROPIC→none. Collected `N,S,O,E,C,A`; sorted `A,C,E,N,O,S` = sorted OCEANS. ✓
- Editorial note: SUNTAN, SANDAL, COOLER, CABANA, TROPIC are common beach vocabulary; OCEANS is an easy, obvious final. Expect a fast, easy solve.

### 2026-05-27 — Camping Trip *(new)*

- Row: `FORE*ST, GR*OUND, SUM*MIT, C*ANOP*Y, TRA*ILS, CAMPER`
- Marks: FOREST→E(3); GROUND→R(1); SUMMIT→M(2); CANOPY→C(0),P(4); TRAILS→A(2). Collected `E,R,M,C,P,A`; sorted `A,C,E,M,P,R` = sorted CAMPER. ✓
- Editorial note: FOREST, GROUND, SUMMIT, CANOPY, and TRAILS are all familiar outdoor/camping vocabulary, while CAMPER is a direct, concrete final answer. This replaces the earlier draft's generic OUTING final. Expect an easy-to-moderate solve, with SUMMIT providing modest difficulty without obscurity.

### Deterministic scramble evidence for proposed additions and replacements

These are the production-compatible scrambles for the five primary answers on every new or reassigned date. None is identical to its answer, and the validator reports no four-letter preserved-sequence warning for any of them.

| Date | Theme | Answer → deterministic scramble |
|---|---|---|
| 2026-06-16 | Movie Night | CINEMA→MNACEI; ACTION→IAOCNT; SCREEN→ECNRSE; POSTER→OTPESR; CREDIT→EIRDTC |
| 2026-06-15 | Road Trip | TRAVEL→EALTVR; DETOUR→UTREOD; MOTELS→MEOSTL; SCENIC→CNSEIC; SNACKS→KNCSAS |
| 2026-06-14 | Rainy Day | CLOUDS→LUSODC; PUDDLE→LUEDPD; SPLASH→APLHSS; PONCHO→OOCPHN; STORMY→MOSRTY |
| 2026-06-13 | Game Night | TOKENS→TKNOES; BOARDS→ODASRB; PUZZLE→ZEZPLU; WINNER→NWNRIE; SCORES→SSOECR |
| 2026-06-12 | Bake Shop | PASTRY→ATPYSR; COOKIE→KCEOIO; BATTER→TRAEBT; MUFFIN→IUNFMF; BUTTER→EURTBT |
| 2026-05-31 | Grocery Store | BASKET→KBESTA; AISLES→SSAEIL; COUPON→NOOCUP; GROCER→RRCGOE; MARKET→AKMTRE |
| 2026-05-29 | Music Class | GUITAR→AIGRUT; VIOLIN→IILONV; MELODY→LYEDMO; SINGER→RGIESN; PIANOS→IOASPN |
| 2026-05-28 | Beach Day | SUNTAN→NNTSAU; SANDAL→SAALDN; COOLER→OECLRO; CABANA→CBAAAN; TROPIC→PCTOIR |
| 2026-05-27 | Camping Trip | FOREST→EFSRTO; GROUND→ONGUDR; SUMMIT→UISMTM; CANOPY→NYAOCP; TRAILS→TALRSI |

---

## 6. Complete proposed data block

Strict-JSON-compatible (as required by `scripts/validate_puzzles.py`'s parser), newest-to-oldest, 25 entries, publishing range unchanged:

```js
const PUZZLE_PUBLISHING_RANGE = {
  "start": "2026-05-24",
  "end": "2026-06-17"
};

const PUZZLE_ENTRIES = [
  { "date": "2026-06-17", "theme": "Garden Path", "row": "BA*MBOO, CACT*U*S, OR*CHID, GARDEN*, FLOWE*R, NATURE" },
  { "date": "2026-06-16", "theme": "Movie Night", "row": "CINEMA*, AC*TIO*N, SCR*EEN, POS*T*ER, CREDIT, ACTORS" },
  { "date": "2026-06-15", "theme": "Road Trip", "row": "T*R*AVEL, DETO*U*R, MOTE*LS, SCENIC, S*NACKS, ROUTES" },
  { "date": "2026-06-14", "theme": "Rainy Day", "row": "C*LOUD*S, PUDDLE*, SPLASH*, PON*CHO, STOR*MY, DRENCH" },
  { "date": "2026-06-13", "theme": "Game Night", "row": "TOKE*NS, BOA*R*D*S, PUZZL*E*, WINNER, SCORES, DEALER" },
  { "date": "2026-06-12", "theme": "Bake Shop", "row": "PASTR*Y*, COOK*IE, BA*TTE*R, MUFFIN, B*UTTER, BAKERY" },
  { "date": "2026-06-11", "theme": "Hard Hat Zone", "row": "HELMET*, HAM*MER, LADDE*R, WORKE*R, WREN*C*H, CEMENT" },
  { "date": "2026-06-10", "theme": "Bird Watching", "row": "FALC*ON, MA*GPIE, PA*R*ROT, PIGEON*, TURKEY*, CANARY" },
  { "date": "2026-06-09", "theme": "Crayon Box", "row": "PUR*PLE, IN*DIG*O, YELLO*W, MA*ROON, VIOLE*T, ORANGE" },
  { "date": "2026-06-08", "theme": "What's for Dessert?", "row": "C*OOKI*E, GE*L*ATO, SUNDA*E, PASTR*Y, MOUSSE, ECLAIR" },
  { "date": "2026-06-07", "theme": "The Veggie Garden", "row": "C*ELERY, GA*R*LIC, TO*MATO, POT*ATO, PEPPER*, CARROT" },
  { "date": "2026-06-06", "theme": "Outer Space", "row": "R*OC*KET, GA*LAXY, METEOR*, PLANE*T*, COSMOS, CRATER" },
  { "date": "2026-06-05", "theme": "Hail Mary", "row": "KIC*K*ER, HELMET*, PLA*YER, JERSE*Y, HUDDL*E, TACKLE" },
  { "date": "2026-06-04", "theme": "X Marks the Spot", "row": "PAR*ROT, CA*NNON, ANCHO*R, IS*L*AND, PI*STOL, SAILOR" },
  { "date": "2026-06-03", "theme": "Once Upon a Time", "row": "KNIG*HT, WIZARD*, THRO*NE, CA*STLE, PR*IN*CE, DRAGON" },
  { "date": "2026-06-02", "theme": "Animal Kingdom", "row": "JAGU*AR, RABBIT*, PAR*ROT*, L*IZARD, MONKE*Y, TURTLE" },
  { "date": "2026-06-01", "theme": "Class is in Session", "row": "CR*AYON, PE*NCIL, LES*SON, MA*RKER*, RE*CESS, ERASER" },
  { "date": "2026-05-31", "theme": "Grocery Store", "row": "BASKET, A*ISLES, CO*UPON*, GROC*ER, MAR*KET*, CARTON" },
  { "date": "2026-05-30", "theme": "Airplane Mode", "row": "WI*N*DOW, RUN*WAY, FLIG*HT, JE*TLAG, TICKE*T, ENGINE" },
  { "date": "2026-05-29", "theme": "Music Class", "row": "GU*IT*AR, VIO*LIN, MELOD*Y, S*INGER, PI*ANOS, STUDIO" },
  { "date": "2026-05-28", "theme": "Beach Day", "row": "SUN*TAN, S*ANDAL, CO*OLE*R, C*A*BANA, TROPIC, OCEANS" },
  { "date": "2026-05-27", "theme": "Camping Trip", "row": "FORE*ST, GR*OUND, SUM*MIT, C*ANOP*Y, TRA*ILS, CAMPER" },
  { "date": "2026-05-26", "theme": "Breakfast", "row": "C*EREAL, YO*GURT, WAF*F*LE, OME*LET, ORANGE*, COFFEE" },
  { "date": "2026-05-25", "theme": "Under the Sea", "row": "TU*RTLE, OYSTER*, ANC*H*OR, SHRI*MP, SALMON*, URCHIN" },
  { "date": "2026-05-24", "theme": "Around the House", "row": "CLOSE*T, FRID*G*E, CA*RPET, PAN*TRY, SHOWER*, GARDEN" }
];
```

---

## 7. Validator evidence for the exact block above

Command run, from the repository root, against a temporary file containing exactly the block in §6 (not the live `puzzles.js`):

```
$ python3 scripts/validate_puzzles.py /tmp/temporary-proposed-puzzles.js
```

Full output:

```
[WARNING] 2026-06-04 theme='X Marks the Spot' rule=answer-reused: Primary answer "ANCHOR" previously appeared on 2026-05-25 (10 day(s) earlier)
[WARNING] 2026-06-04 theme='X Marks the Spot' rule=answer-reused: Primary answer "PARROT" previously appeared on 2026-06-02 (2 day(s) earlier)
[WARNING] 2026-06-10 theme='Bird Watching' rule=answer-reused: Primary answer "PARROT" previously appeared on 2026-06-04 (6 day(s) earlier)
[WARNING] 2026-06-11 theme='Hard Hat Zone' rule=answer-reused: Primary answer "HELMET" previously appeared on 2026-06-05 (6 day(s) earlier)
[WARNING] 2026-06-12 theme='Bake Shop' rule=answer-reused: Primary answer "COOKIE" previously appeared on 2026-06-08 (4 day(s) earlier)
[WARNING] 2026-06-12 theme='Bake Shop' rule=answer-reused: Primary answer "PASTRY" previously appeared on 2026-06-08 (4 day(s) earlier)

Summary: 25 entrie(s), 0 error(s), 6 warning(s)
```

**Exit code: 0.**

**Warning classification (all 6 are non-blocking `answer-reused` warnings; none are errors):**

| Warning | Classification |
|---|---|
| ANCHOR reused (06-04 vs 05-25) | **Inherited** — pre-existing in the current live archive (X Marks the Spot / Under the Sea), unchanged by this proposal |
| PARROT reused (06-04 vs 06-02) | **Inherited** — pre-existing, unchanged |
| PARROT reused (06-10 vs 06-04) | **Inherited** — pre-existing, unchanged |
| HELMET reused (06-11 vs 06-05) | **Inherited** — pre-existing (Hard Hat Zone's marker fix does not touch its answer list); unchanged |
| COOKIE reused (06-12 vs 06-08) | **Introduced by this proposal**, but unavoidable given the preservation policy: it comes from historically-authored Bake Shop content (§5) reused as-is, not from a new design choice, and colliding with an unrelated pre-existing puzzle's answer that also cannot be changed |
| PASTRY reused (06-12 vs 06-08) | **Introduced by this proposal**, same explanation as COOKIE above |

No other warning categories (`theme-repeated`, `final-reused`, `scramble-identical-to-answer`, `scramble-preserves-sequence`) appear in the final block. The newly designed puzzles introduce no warnings. Earlier drafts that produced a weak theme/final relationship or a scramble-quality warning were replaced before this recommendation was finalized.

Zero errors confirms only deterministic structural/content correctness (row shape, marker grammar, marker count, anagram match, no duplicate dates/puzzles, no missing dates in range, no self-identical scrambles). It does not by itself prove subjective puzzle quality, difficulty balance, or player enjoyment — those are addressed narratively in §5's editorial notes, which are judgment, not a deterministic guarantee.

---

## 8. Stale-save handling recommendation (for a later implementation handoff — not implemented here)

**Current state, confirmed by reading `main.js` directly:** there is no puzzle-content fingerprint stored anywhere today, and no code path compares a saved date's stored gameplay state against what `PUZZLE_ROWS` currently declares for that date before trusting it (`main.js:264-323` `saveState`/`loadState`; `main.js:462-469, 497-514` `getActivePuzzle`/board construction). The only existing reset path is the manual, date-scoped `?reset` flag (`main.js:480-482`), which a player has to trigger themselves and does not fire automatically on content change.

**Recommended policy** (design only; requires an explicit implementation handoff to build):

1. **Fingerprint new saves.** Add one field to the object written by `saveState()` containing a deterministic fingerprint of the active authored row, including markers. This is additive; the existing key and all existing stored fields retain their meanings.
2. **Handle fingerprinted saves automatically.** In `loadState()`, compare a present saved fingerprint with the current puzzle fingerprint before trusting progress. Load on a match; on a mismatch, clear only that date's incompatible state and start it fresh.
3. **Migrate legacy saves selectively.** Existing saves have no fingerprint, so treating every missing fingerprint as incompatible would unnecessarily erase progress on unchanged dates. For this one migration, use the explicit 12-date incompatible set identified in §2/§3: `2026-05-27`, `2026-05-28`, `2026-05-29`, `2026-05-31`, `2026-06-02`, `2026-06-03`, `2026-06-11`, `2026-06-12`, `2026-06-13`, `2026-06-14`, `2026-06-15`, and `2026-06-16`. Reset a fingerprint-less legacy save only on those dates. Load legacy saves on every unchanged date and upgrade them with the current fingerprint when next saved.
4. **Reset only incompatible per-date state**, using the same date-scoped target as `?reset` (`juggle_puzzle_<date>`). Do not change `juggle_settings`, `juggle_visits`, `juggle_achievements`, `juggle_ach_counts`, `juggle_completions`, or the per-date analytics session identifier.
5. **Preserve global history.** `juggle_completions` records historical participation, not puzzle answers, so retain it along with achievements and visits. A future archive UI should use the current per-date saved `solved` state—not the global completion-count list—when showing whether the revised puzzle itself has been completed.
6. **Communicate a reset once, locally.** When an incompatible save is cleared, show a small one-time in-page notice such as “This puzzle was updated since your last visit — your previous progress for this date was reset.” No backend, tracking, or new storage category is required.

This selective legacy migration plus ongoing fingerprint comparison handles all 12 known incompatible dates without erasing compatible progress elsewhere. Focused tests should cover a matching fingerprint, a mismatching fingerprint, a legacy save on an affected date, a legacy save on an unchanged date, and preservation of all global keys.

---

## 9. Alternatives considered

- **Leave the historical gaps unfilled (narrower range, or explicit "no puzzle" days).** Rejected as the primary recommendation because the handoff explicitly asks for one contiguous, sale-ready archive across the full existing declared range, and narrowing the range is excluded by the preservation policy ("do not change the publishing-range endpoints"). Worth surfacing as a fallback if the owner does not want to approve 8 new-content puzzles at once (see §10) — in that case, only the 3 marker fixes and the 06-17 duplicate-declaration cleanup would ship now, and the 7 gap dates plus the 2 duplicate-content replacements would stay open/deferred rather than filled with unreviewed new content.
- **Widen or otherwise change the publishing range** to exclude the problematic dates. Rejected — excluded by the preservation policy and would create a new inconsistency between the declared range and what's actually been communicated as the archive's coverage.
- **Correct Bake Shop's markers but keep it as the winning `2026-06-17` declaration instead of Garden Path.** Rejected: Garden Path is the only puzzle that has ever actually been effective at `2026-06-17` in this checkout's history (§2); swapping it for Bake Shop would change an effective puzzle's content on a date, not just repair a never-effective one, which is a materially different (and higher-risk) kind of change than what this plan proposes.
- **Preserve the later occurrence instead of the earlier one for the two duplicate-content pairs.** Rejected per the handoff's stated default preservation policy and because the earlier occurrence in both cases (`2026-06-11`, `2026-05-30`) is also chronologically earlier in-game, so preserving it maximizes the amount of real playing history left undisturbed.
- **Try to hand-derive whether existing saves are compatible instead of a blanket fingerprint reset (§8).** Considered and rejected as the recommended default: for the three marker-only repairs, primary-letter guesses remain answer-compatible but the bonus/final-letter assignment changes, so a byte-perfect partial-preservation scheme is possible in principle but meaningfully more complex to build and verify correctly than a single fingerprint check, for a game with no accounts and only local, single-browser persistence at stake.

---

## 10. Executive approval requested

**Requested approval, stated as narrowly as practical:**

> Approve the single 25-entry replacement dataset in §6 (publishing range unchanged: `2026-05-24`..`2026-06-17`) and the §8 fingerprint-based stale-save protection as one later, separately scoped implementation package.

This approval, if given, authorizes only:
- a future implementation handoff to replace `PUZZLE_ENTRIES` in `puzzles.js` with the exact block in §6 (and nothing else in that file); and
- that same handoff to implement the minimal stale-save fingerprint/reset mechanism described in §8, with focused tests and preservation of global settings, visits, achievements, and completion history.

**Recommendation on the remaining warnings:** accept the two Bake Shop repeat-answer warnings. They are the explicit, documented cost of salvaging already-authored hidden content while preserving the valid `2026-06-08` puzzle. They do not affect correctness, introduce obscure vocabulary, or justify leaving a hole in an otherwise contiguous archive. The other four warnings are inherited from unchanged historical puzzles and should not trigger additional published-answer rewrites in this repair.

It does **not** authorize:
- commit, push, or deployment of any of this (per `AGENTS.md`, this document's task, and every prior handoff, no agent commits/pushes/deploys without the user doing so or explicitly directing it);
- promoting or altering the separately-queued `juggle-autonomy/queued/PUZZLE_DATA_SAFETY_FOUNDATION.md` task, which this document does not touch;
- any other item flagged as excluded in `AGENTS.md`/`HANDOFF.md` (UI, CI, storage migration, framework, backend, hosting, or any other application/product change beyond puzzle content and the described stale-save mechanism).

---

## Required validation — commands run and results

All commands below were run from the repository root (`/Users/emaad/Documents/juggle`) in the final resumed session, after the subscription usage reset. Claude Code applied the bounded editorial correction across two work sessions separated by that reset; no Codex fallback implementation occurred during the pause (confirmed on resume via `.juggle-supervisor/state.json`: `implementation_owner: "claude"` and `validation_outcome: "not_run"` at resume time, and the absence of any `CODEX_TAKEOVER.md`/`codex-fallback-report.md`). Every result below is from this session's own fresh run, not carried over from an earlier claim.

```
$ git status --short --branch
## main...origin/main
 M .gitignore
 M game.js
 M index.html
?? AGENTS.md
?? CLAUDE.md
?? CURRENT_STATE.md
?? HANDOFF.md
?? HISTORICAL_PUZZLE_REMEDIATION_PLAN.md
?? PLATFORM_AUDIT.md
?? juggle-autonomy/
?? puzzles.js
?? scripts/
?? tools/
```
(Identical before and after this session's validation pass — see final status below. `HISTORICAL_PUZZLE_REMEDIATION_PLAN.md` itself is untracked/new, as expected for this task's sole artifact.)

```
$ python3 scripts/validate_puzzles.py
```
Exit code: **1**. Summary line: `19 entrie(s), 16 error(s), 18 warning(s)` — matches the expected unchanged baseline exactly (verified against the live, untouched `puzzles.js`).

```
$ python3 -m unittest scripts/test_validate_puzzles.py
```
Result: **`Ran 43 tests in 0.006s — OK`** — 43/43 passing, matching the expected baseline.

```
$ shasum -a 256 puzzles.js game.js index.html main.js style.css wordlist.js scripts/validate_puzzles.py scripts/test_validate_puzzles.py
9ca168c78e0dd7df8b3f80b7372500b60a5519a0407ffc04d00d86e6e2644b51  puzzles.js
0a0091b0d17a5ee3e60987fa6b2549bb9ef84f05af4e57ff84ba9a0219c5e295  game.js
b1fca0b64b5e44493c8c915ad83661ded67e85d8dccb5b145ecb3b14f64809ba  index.html
9a59243743b3ef1a85eabb059b74e4ce49d41837e5a09688a0f538b5bee1d0da  main.js
657a75d082fc9d3e7b3547f7975164a154115b36bfe959afde72314be2726ac0  style.css
9e81c47cc2b20f23698ab985250162ecae5d119a1ad28bd58386b4c7d4fa03d5  wordlist.js
14557d7121c36d878f3f19e9019f0fad945a29bc1c10e0c39a6f2416d4ded2ab  scripts/validate_puzzles.py
d52eaef76de4caecec7a004b5abeed9aebad52771471a121e78711fd3880801c  scripts/test_validate_puzzles.py
```
All 8 hashes **match** the protected-file baseline in `HANDOFF.md` exactly — none of these files were modified by this task.

```
$ git diff --check
```
No output, exit 0 — no whitespace-conflict-marker issues in the working tree.

```
$ git status --short --branch
```
(second run, post-task — identical to the pre-task run above, confirming nothing changed)

**Candidate-block validation** (per §7, extracted verbatim from §6 into `/tmp/temporary-proposed-puzzles.js`, outside the repository):

```
$ python3 scripts/validate_puzzles.py /tmp/temporary-proposed-puzzles.js
```
Exit code: **0**. `25 entrie(s), 0 error(s), 6 warning(s)` — full output and classification in §7. The temporary file was removed after validation (`rm /tmp/temporary-proposed-puzzles.js`) and does not remain in or out of the repository.

**Deliverable path:** `HISTORICAL_PUZZLE_REMEDIATION_PLAN.md` (created and finalized) — the sole task artifact. Protected application, puzzle-data, and validator files remained byte-for-byte unchanged. No historical correction was applied to live data; no commit, push, or deploy was performed.
