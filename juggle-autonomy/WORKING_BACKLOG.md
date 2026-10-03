# Juggle working backlog

This is a **dynamic candidate queue**, not a FIFO roadmap or active implementation work order. Codex may reorder, merge, split, add, or retire items whenever current evidence changes the highest-leverage route toward `PRODUCT_DIRECTION.md`. `HANDOFF.md` alone is the active implementation work order.

## Current evidence-derived candidates

- Finish and independently review the current active handoff before replacing it.
- Reassess the known puzzle-data/date issues in `CURRENT_STATE.md`; historical content corrections that require guessing remain blocked on owner-confirmed truth, while tooling/behavior that can prevent recurrence may proceed independently.
- Make routine puzzle authoring/validation/preview/scheduling/publishing safer and less manual where the operational value justifies the change.
- Resolve player-visible date/fallback/persistence behavior when current behavior can present one source puzzle as another date or create misleading daily state.
- Ensure preview/test flows cannot pollute real analytics, completion, streak, or achievement state.
- Evaluate mobile/touch/keyboard/accessibility and responsive polish with real browser/device evidence at appropriate review boundaries.
- Add release/deployment safeguards only when they materially reduce the chance of shipping invalid content or breaking the daily game without creating disproportionate maintenance burden.

## Backlog hygiene

After an accepted milestone or meaningful new user/play evidence, remove obsolete items and add newly evidenced gaps. If several consecutive tasks come from the same subsystem, perform a horizon check against the destination before continuing local optimization. Do not preserve an item because effort was already invested in it.
