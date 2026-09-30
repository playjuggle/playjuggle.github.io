# <Task title>

**Status:** Active
**Primary worker:** Claude Code
**Supervisor/reviewer:** Codex
**Codex fallback:** Allowed | Disallowed
**New material architecture/product decision required:** No | Yes — describe and obtain user approval before implementation
**Fallback continuity basis:** Existing accepted approach | Handoff-specified approach | Mechanically unambiguous local continuation | Not safe for fallback

## Why this work now

- **Problem/evidence:** <player/product/engineering issue and the evidence establishing it>
- **Desired outcome / hypothesis:** <what should materially improve>
- **Why this is the highest-leverage next slice:** <brief rationale; do not cite “smallest/easiest task” as the reason>

## Implementation slice

<One coherent unit sharing a subsystem/mental model. Keep unrelated work for another handoff.>

## Context to inspect

- <exact files/sections/evidence needed for this slice>
- <avoid broad historical reading unless needed for a named question>

## Binding approach and constraints

Copy the **specific** product/architecture decisions needed for this slice here; do not make Claude load broad PM documents merely to discover them.

- <implementation direction another worker must preserve>
- <compatibility/persistence/data/UI/product constraints that materially narrow the solution>
- <if implementation is intentionally open, define boundaries that make local choices interchangeable>

## Allowed changes

- <paths or classes of changes>

## Explicit exclusions

- <things that must not change>

## Acceptance criteria

- <observable player/product/engineering behavior>
- <objective criteria sufficient to distinguish correct from merely “code was written”>

## Required final validation

```sh
<commands>
```

Use focused checks while iterating. Run the complete list above once the slice is ready for acceptance unless a command must be repeated because relevant code changed after it ran.

## Reporting requirements

Report changed files, approach continuity, exact validation/results, player/behavior/compatibility impact, unresolved material uncertainty, and whether any material architecture/product decision was introduced. Do not restate large source documents or full transcripts.
