# Create and Editorially QC a 120-Day Candidate Puzzle Schedule

**Status:** Active  
**Primary worker:** Claude Code  
**Supervisor/reviewer:** Codex  
**Codex fallback:** Disallowed — the owner directed Codex to stop if Claude usage is exhausted  
**New material architecture/product decision required:** No for staged creation/QC; yes before promotion, because 91 dates are already past and previously served fallback content  
**Fallback continuity basis:** Not safe for fallback under the owner's current stop condition

## Why this work now

- **Problem/evidence:** The accepted live schedule stops at 2026-06-17, and every later date falls back to Garden Path. The safe batch gate now exists, but there is no future candidate content to operate on.
- **Desired outcome / hypothesis:** Produce one high-quality, fully validated 120-day candidate schedule covering 2026-06-18 through 2026-10-15, with enough editorial evidence for Codex and the owner to decide whether to promote it.
- **Why this is the highest-leverage next slice:** Puzzle quality and daily freshness are the core product. This fills the current schedule gap and extends roughly one month beyond today's 2026-09-16 date without touching live data before executive approval.

## Implementation slice

Create exactly one staged batch JSON file and one concise but auditable editorial QC report. Iterate locally until the candidate has zero blocking errors and introduces zero new automated warnings when checked against the live archive. Do not run apply and do not modify puzzles.js or application code.

## Required artifacts

- puzzle-batches/candidate-2026-06-18-to-2026-10-15.json
- puzzle-batches/QC-2026-06-18-to-2026-10-15.md

The candidate must use the accepted strict-JSON batch format, contain exactly 120 entries, and remain newest-to-oldest.

## Binding content and quality rubric

- Exactly one entry for every date from 2026-06-18 through 2026-10-15 inclusive; no gaps or overlaps.
- Every puzzle has one clear, natural theme, five distinct six-letter primary answers, one six-letter final answer, and exactly six marked letters that anagram to the final.
- Treat all 720 answer slots (600 primary + 120 final) as globally unique across the candidate and also unique against every primary/final word in the 25-entry live archive. Do not reuse a word across primary/final roles.
- Use familiar contemporary English words recognizable to a broad US general audience. No proper nouns, trademarks, abbreviations, unexplained jargon, offensive terms, questionable spellings, very rare words, or strained inflections chosen merely to reach six letters.
- Every primary and final word must fit the displayed theme directly and defensibly. Avoid vague umbrella themes that could justify almost anything. Avoid five near-synonyms that make the final arbitrary; prefer a coherent category or setting with a satisfying final member/payoff.
- Themes must be unique and meaningfully distinct across the batch and from the live archive, not merely relabeled duplicates. Seasonal/calendar flavor is welcome where it naturally matches the scheduled date, but do not depend on a religious, national, or regional observance as assumed universal knowledge.
- Difficulty should be approachable and varied: target 45 easy, 60 medium, and 15 challenging puzzles. “Challenging” means less immediate association or moderately less common—but still familiar—words, never obscurity. Spread difficulty across the schedule; no run longer than three puzzles of the same band.
- Within each puzzle, aim for at least two strong theme anchors, two moderate associations, and no more than one answer that needs a second thought. The final answer must be a fair six-letter thematic payoff.
- Avoid insensitive groupings, stereotypes, politics, medical/legal danger, adult-only content, and themes likely to age badly.
- Automated quality contract: candidate isolation must produce 0 errors and 0 warnings. Merged check against live must produce 0 errors and exactly the 6 already accepted historical warnings—no new theme-repeated, answer-reused, final-reused, or scramble-preserves-sequence warning.
- Do not weaken, bypass, or modify the validator or batch gate to make content pass. Replace weak content instead.

## Editorial QC process and report

Review in four 30-puzzle blocks. For each entry, the report must include date, theme, difficulty band, final answer, and a terse quality note identifying the strongest anchors or why the payoff is fair. Keep each row compact.

The report must also include:

- exact automated commands/results and a statement that all new warning categories are absent;
- counts for entries, distinct dates, distinct themes, distinct primary words, distinct final words, and distinct words across both roles;
- difficulty counts and maximum same-band run;
- a theme-variety summary by broad category (food, nature, activities, places, objects, arts, science, etc.) so overconcentration is visible;
- a lexical review statement covering familiarity, proper nouns/trademarks, abbreviations, spelling, offensiveness, and forced morphology;
- a list of any remaining subjective concerns. If a word/theme is genuinely questionable, replace it before finalizing rather than hiding it in this list;
- promotion implications: as of 2026-09-16, dates 2026-06-18 through 2026-09-16 (91 dates) are retroactive replacements for fallback content and require explicit owner approval plus expansion of the fingerprint-less legacy-save incompatibility set before live apply; 2026-09-17 through 2026-10-15 are future dates. State that the batch tool alone must not be run against live until that paired migration is approved.

## Allowed changes

- Add the two required artifacts under puzzle-batches/.
- CURRENT_STATE.md — a short factual note that a staged 120-day candidate exists, is not live, and awaits Codex/owner review.

## Explicit exclusions

- Do not edit or apply to puzzles.js.
- Do not edit any application code, validator, batch tool, tests, docs other than the two artifacts and narrow CURRENT_STATE.md note.
- Do not commit, push, deploy, use network services, add dependencies, or spend API-key/paid API billing.
- Do not claim player-tested difficulty or enjoyment; editorial bands are reasoned judgments pending play evidence.

## Acceptance criteria

- Candidate JSON parses and the batch gate check exits 0.
- Candidate contains exactly the specified 120 contiguous newest-to-oldest entries.
- Candidate-only validator result is 120 entries, 0 errors, 0 warnings; merged result is 145 entries, 0 errors, exactly 6 inherited warnings.
- All 720 answer uses are unique across candidate and non-overlapping with live answers/finals.
- Themes are exact-unique and editorially distinct; required difficulty distribution and maximum-run rule are satisfied.
- QC report contains all 120 compact review rows and every aggregate/evidence section above.
- Live puzzles.js remains byte-for-byte unchanged at SHA-256 467eb5c9c2817c1fe4b02cd99ea261f10f0f29d38537f726e05f66e1e1e826f3.
- No promotion occurs; final output is ready for Codex review and then an executive approval decision.

## Required final validation

```sh
git status --short --branch
python3 -m json.tool puzzle-batches/candidate-2026-06-18-to-2026-10-15.json
python3 scripts/manage_puzzle_batch.py check puzzle-batches/candidate-2026-06-18-to-2026-10-15.json
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/validate_puzzles.py
python3 -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('scripts').glob('*.py')]"
git diff --check
shasum -a 256 puzzles.js
git diff --exit-code -- puzzles.js game.js main.js index.html style.css wordlist.js scripts
git status --short --branch
```

Expected results:

- JSON formatting check exits 0;
- batch check exits 0 with 0 errors and exactly 6 inherited warnings;
- all existing tests pass;
- live validator remains 25 entries, 0 errors, 6 warnings;
- AST and whitespace checks pass;
- puzzles.js hash remains exactly as stated;
- excluded-file diff shows only accepted pre-task changes and no task-introduced change.

Also run a standard-library analysis command/script (temporary, not checked in) that independently reports exact counts, continuity/order, cross-role/live word uniqueness, theme uniqueness, difficulty counts from the QC table, and maximum same-band run.

## Reporting requirements

Report artifact paths, automated counts/results, editorial distribution, any remaining subjective uncertainty, exact retroactive/future date split, and whether any live/application file changed. Confirm no apply, commit, push, or deployment occurred. The next step after Codex acceptance is an executive approval decision, not automatic promotion.
