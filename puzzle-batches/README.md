# Puzzle batches

This directory holds strict-JSON candidate batches for
`scripts/manage_puzzle_batch.py`, the safe check-and-promote workflow for
adding future puzzles to `puzzles.js` without hand-editing it or risking the
accepted historical archive.

`template.json` in this directory is a documentation placeholder only — its
dates (2027-01-01/02) and rows (`"REPLACE, THESE, WORDS, WITH, REAL*,
ANSWER"`) are deliberately invalid (wrong word lengths, wrong marker count,
non-contiguous with any real live schedule) so it can never be accidentally
promoted. Copy it, replace every date/theme/row with real content, then run
`check`.

## Format

```json
{
  "start": "YYYY-MM-DD",
  "end": "YYYY-MM-DD",
  "entries": [
    {"date": "YYYY-MM-DD", "theme": "Example", "row": "W1, W2, W3, W4, W5, FINAL"}
  ]
}
```

- `start`/`end` — the inclusive date range this batch is declaring, matching
  `PUZZLE_PUBLISHING_RANGE`'s shape in `puzzles.js`.
- `entries` — one object per date, **newest-to-oldest** (so the first entry's
  `date` is `end` and the last entry's `date` is `start`), matching
  `PUZZLE_ENTRIES`'s ordering in `puzzles.js`.
- Each entry needs exactly `date`, `theme`, `row` — same shape and asterisk
  marker rules as `puzzles.js` (see the `HOW TO ADD A PUZZLE` comment at the
  top of that file): five six-letter primary words plus one six-letter final
  word, six `*` markers total across the five primary words, marked letters
  an anagram of the final word.

## Commands

```sh
python3 scripts/manage_puzzle_batch.py check path/to/batch.json
python3 scripts/manage_puzzle_batch.py apply path/to/batch.json
```

`check` only ever reads — it never writes, regardless of outcome. `apply`
writes only when every check passes cleanly; on any failure it leaves the
target byte-for-byte unchanged. Both default to the repository-root
`puzzles.js` as the live schedule to check against / write into; pass
`--target path/to/file.js` to point at a different file (mainly useful for a
dry run against a scratch copy).

## Blocking vs warning

Every diagnostic `scripts/validate_puzzles.py` would report as `ERROR`
blocks `apply` and makes `check` exit nonzero (malformed dates, wrong row
shape, bad markers, anagram mismatches, duplicate/out-of-order dates,
schedule gaps, duplicate puzzles, self-identical scrambles, and so on — see
that script's module docstring for the full rule set). `WARNING` diagnostics
(theme reused, answer/final word reused, scramble preserves an obvious
4-letter run) are printed and counted but never block either command.

## Append-only boundary

This is the first, and so far only, batch workflow: **append-only**.

- The batch's `start` must be exactly one calendar day after the live
  `PUZZLE_PUBLISHING_RANGE.end`.
- `entries` must cover every day from `start` through `end` with no gaps.
- No candidate date may fall on or before the live end.
- The live `start` never changes; the merged schedule keeps the live start
  and adopts the batch's `end`.

Overlap, replacement, historical edits, gaps, and any attempt to change the
live start are always refused — there is no override flag.

## What a clean `apply` does

Validates twice — the batch's own declared range in isolation, then the full
proposed merged schedule (live entries + batch entries) — and, only if both
passes are free of `ERROR` diagnostics, atomically rewrites the target:

- Every existing live entry is preserved exactly (date/theme/row unchanged).
- Only `PUZZLE_PUBLISHING_RANGE` and `PUZZLE_ENTRIES` change; all other file
  content (comments, other code) is preserved verbatim.
- The write is atomic (temp file + rename) and refuses if the target changed
  on disk since it was read.

## Safe next steps after a clean `apply`

1. Re-run `python3 scripts/validate_puzzles.py` against the updated file to
   confirm it's still clean (aside from any accepted warnings).
2. Review the diff by hand.
3. Commit/deploy as a separate, explicit step — `manage_puzzle_batch.py`
   never commits, pushes, installs anything, or deploys.
