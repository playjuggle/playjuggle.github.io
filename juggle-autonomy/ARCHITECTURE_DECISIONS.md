# Juggle Accepted Architecture Decisions

This file records only durable, material implementation decisions that future workers must respect. It is not a task log and should stay short. Routine implementation details belong in the active handoff or supervisor reports.

## Rules

- Add an entry only after the user has authorized a material architecture choice or an active handoff already contains that authorization.
- Codex and Claude must treat accepted entries as binding until an explicitly authorized later entry supersedes them.
- Do not add an entry for ordinary local coding choices.
- Each entry should state the decision, why it matters, constraints it creates, and what would justify revisiting it.

## Accepted decisions

### Puzzle-save compatibility via content fingerprint (accepted 2026-09-15)

**Decision:** Per-date saved game state (`juggle_puzzle_<date>` in `localStorage`) is validated against the active puzzle's content before being trusted. `saveState()` writes a deterministic `puzzleFingerprint` (derived from theme, per-word answer/scramble/marker indices, final word, and final-slot order) alongside existing fields. `loadState()` clears and restarts only the active date's save if a stored fingerprint mismatches, or if a fingerprint-less legacy save falls on one of the 12 dates the 2026-09-15 historical archive remediation is known to have changed (`LEGACY_INCOMPATIBLE_DATES` in `main.js`); every other legacy save loads normally and is upgraded in place.

**Why it matters:** Prevents future puzzle-content edits from silently overlaying stale guesses/answers/marker positions onto new content, which previously had no cross-check at all (see `HISTORICAL_PUZZLE_REMEDIATION_PLAN.md` §2/§8).

**Constraints:** Only the active date's puzzle-state key may be cleared on incompatibility; global keys (`juggle_settings`, `juggle_visits`, `juggle_achievements`, `juggle_ach_counts`, `juggle_completions`) and per-date analytics session IDs must never be touched by this mechanism. The reset notice shown on incompatible-load is one-time, non-persistent, and emits no analytics.

**What would justify revisiting it:** A future explicit product decision to persist partial/answer-compatible progress across a content edit instead of a full per-date reset, or to change what "effective puzzle content" means for fingerprinting purposes.
