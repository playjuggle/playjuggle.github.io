# Decisions from Emaad

Newest first. Every scheduled run reads this file before choosing work.
Each entry is an executive decision and is binding until a later entry supersedes it.

## 2026-10-03 (later) — Generate batches only when needed

Do not spend tokens extending the schedule early. The OpenClaw check costs nothing and runs
every few hours, but a worker is launched only when about 7 days of published puzzles remain
(the margin lets one bad night, such as a usage limit or a refused batch, pass without the live
game running out). When due, prepare one batch of 20 and let the gate publish it. This
supersedes the earlier "stay 60 days ahead" target below; everything else in the earlier entry
still stands.

## 2026-10-03 — Juggle runs and publishes itself, indefinitely

Emaad does not approve, commit, or push puzzle batches. Juggle must keep its
schedule from ever running out on its own, in perpetuity, with no human step (the "60 days
ahead" target originally written here is replaced by the later entry above).
This supersedes every earlier "await Emaad's approval to commit or push" rule for
puzzle content.

- Workers prepare and locally validate batches as before. They do not commit or push.
- The OpenClaw publication gate (`C:\Users\hmsla\Documents\Codex\OpenClaw\scripts\juggle_gate.py`,
  outside this repository so a worker cannot weaken it) commits and pushes to `origin/main`
  only when every check passes: contiguous append-only dates, existing entries byte-identical,
  structural rules, uniqueness against history and archive, a written weakest-link critique per
  puzzle, the committed validator, and the full test suite with nothing skipped.
- A worker that is blocked by a failing tool or test must repair the tool or test so that
  it is correct, never by weakening a quality or preservation check, then finish the batch.
  A prepared-but-unpublished batch is not "awaiting approval": validate it, repair what is
  wrong, and let the gate publish it.
- Do not stop to ask Emaad for puzzle publication. Quality is still the product: every rule in
  `juggle-autonomy/PUZZLE_QUALITY_STANDARD.md` applies to every puzzle.
- Application code, gameplay, the retired archive, and published puzzle rows stay out of scope
  for automatic publication.

## 2026-10-02 — Juggle has no players

Nobody currently plays Juggle. Retroactive puzzle changes and deletion of existing
puzzle content are authorized. The save-compatibility migration and owner-approval
gate protect players and saved games that do not exist, so they are not reasons to
avoid a route. Rebuild player-data protection before the game has real players.
