# Author a New Three-Week Live Schedule

**Status:** Validation passed; publish authorized
**Primary worker:** Codex

## Problem and outcome

The owner retired all 25 previously approved puzzles permanently from the live schedule. Author at least 21 new puzzles and replace `PUZZLE_ENTRIES` directly so the live schedule consists only of newly authored content from 2026-10-02 onward. The historical archive remains unchanged and must never be used as live content or as a source for answers.

## Acceptance

- At least 21 contiguous, newly authored dates starting 2026-10-02; final range: 2026-10-02 through 2026-10-22.
- Each puzzle has one distinct natural theme, five distinct six-letter primary answers, one six-letter final answer, and exactly six marked letters that form the final answer.
- Themes and every primary/final answer are globally unique within the live batch and do not occur in `puzzle-batches/approved-live-puzzles-2026-06-17.js`.
- Broad-audience familiar English; no proper nouns, trademarks, abbreviations, jargon, offensive terms, questionable spellings, rare words, or strained inflections.
- Update schedule-dependent regression expectations without weakening save-compatibility behavior. Do not change application code, the validator, or `scripts/manage_puzzle_batch.py`.
- Update `CURRENT_STATE.md` and this handoff with the final range, themes, and exact validation evidence.
- Full suite: `python.exe -m unittest discover -s scripts -p 'test_*.py'` passed (102 tests). Validator: 21 entries, 0 errors, 3 warnings (all `scramble-preserves-sequence`). `git diff --check` passed. Archive SHA-256 remains `7CB3E3B0F5001393CAC985A365003B43C69DAEEFD44518D27B33397E5D38B318`.
- After all checks pass, commit `puzzles.js`, the unchanged archive record, required schedule-coupled test updates, backlog/state/handoff documentation to `main`, then push to `origin`. Do not include attribution trailers. Do not push application code.

## Validation commands (PowerShell)

```powershell
$python = 'C:\Users\hmsla\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$env:PYTHONDONTWRITEBYTECODE = '1'
& $python -m unittest discover -s scripts -p 'test_*.py'
& $python scripts/validate_puzzles.py
git diff --check
```

## Decision record

The user explicitly authorized direct rewriting of `puzzles.js` for this reorganization, retired the archived puzzles permanently, and authorized committing/pushing the specified content and state files only if all checks pass. The archive itself must remain unchanged.
