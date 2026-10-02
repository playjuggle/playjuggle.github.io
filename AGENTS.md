# Juggle Engineering Rules

This file is the canonical engineering/collaboration policy for this repository. The latest explicit user instruction governs. `juggle-autonomy/PRODUCT_DIRECTION.md` defines durable product intent; `juggle-autonomy/WORKING_BACKLOG.md` is only a revisable candidate queue. If an active handoff appears to conflict with higher-authority direction, stop on the conflicting decision rather than silently averaging them.

## Product and architecture

- Juggle is currently a small static daily word game built with vanilla HTML, CSS, and JavaScript and deployed with GitHub Pages. That describes the present implementation, not a preferred target architecture or hosting decision.
- Architecture, testing, content operations, and hosting choices are provisional. Evaluate realistic alternatives on player/product value, reliability, regression risk, cost, and maintenance burden without favoring either the current stack or modernization for its own sake.
- Do not implement a framework, build system, backend, database, account system, hosting migration, or paid service unless an active implementation handoff explicitly authorizes it after the user reviews the relevant recommendation.
- Preserve existing gameplay and UI behavior unless the active task explicitly authorizes a change.
- Preserve existing `localStorage` keys, stored shapes, and semantics. Any necessary migration must be deliberate, backward-compatible where practical, and called out in the handoff and review.
- Never silently change a published puzzle's answers, theme, date, marker positions, deterministic ordering, scramble, final-letter behavior, or availability. Published-puzzle corrections require explicit user approval and a documented reason.
- Prefer simple, zero-external-dependency, locally runnable automation where practical.
- Routine daily puzzle creation, validation, scheduling, previewing, and publication must not require ChatGPT Work credits or any AI agent. Agents may assist, but normal operation must remain available to a person using local tools.

## Product-first planning and task sizing

- Codex owns sequencing. Start from the durable destination in `juggle-autonomy/PRODUCT_DIRECTION.md` and the current player/product problem, not the easiest measurable defect or smallest unresolved documentation item.
- Use a closed planning loop: reconstruct current evidence; compare it with the destination; identify the highest-leverage gap; consider plausible next moves; actively challenge the preferred move for stale assumptions, opportunity cost, dependency order, evidence quality, and risk of local optimization; then choose one milestone/slice. Keep that critique concise unless the decision is genuinely ambiguous.
- Before a substantial handoff, Codex should be able to state compactly: **problem/evidence**, **desired outcome or hypothesis**, and **why this is the highest-leverage next step**. A green test is evidence of correctness, not itself the product outcome.
- After meaningful new evidence, an accepted milestone, or several consecutive tasks in one subsystem, perform a horizon check against all relevant end-state dimensions rather than automatically continuing the same local optimization. Update `WORKING_BACKLOG.md` when priorities change; sunk effort is not a reason to preserve an item.
- Prefer a cohesive milestone decomposed into coherent implementation slices with observable acceptance criteria.
- Audits, documentation, tooling, and refactors are valuable when they resolve a concrete risk, unblock the product, or materially improve future reliability. They must not become a substitute for advancing the user-visible objective.
- Codex may reorder, replace, or retire planned work when current evidence shows a higher-leverage path. An old spec, backlog label, metric, or previously chosen milestone is not authority merely because it exists.

## Shared implementation contract

- `juggle-autonomy/SHARED_IMPLEMENTATION_CONTRACT.md` and accepted entries in `juggle-autonomy/ARCHITECTURE_DECISIONS.md` keep implementation aligned across tasks.
- Accepted code is current repository truth regardless of which agent wrote it. A different stylistic preference is not a reason to rewrite accepted work.
- A material architecture choice must already be authorized by the active handoff or an accepted architecture decision. A worker may not silently introduce one.
- Codex implements directly under the active handoff and accepted architecture contract. If work requires an unapproved material architecture or product decision, Codex must park that decision for Emaad.

## Roles and write ownership

- Codex is the product-minded project manager, technical lead, reviewer, and implementation worker. It defines scope and acceptance criteria, protects product/architecture/compatibility constraints, reviews implementation evidence, and chooses the next high-leverage work.
- Codex is the sole implementation worker. Juggle does not invoke Claude Code.
- The current implementation owner is recorded in ignored supervisor state. Exactly one implementation owner may exist at a time; Claude ownership is retired for this project.
- Do not start the legacy Claude runner or transmit repository content to Claude. The user retains final authority over scope, product behavior, commits, pushes, and deployment.

## Implementation and token efficiency

- `HANDOFF.md` is the single active work order. Keep its scope, acceptance criteria, and validation evidence concrete.
- Use compact supervisor state, relevant diffs, and exact validation evidence before opening diagnostic logs.
- Use targeted checks while iterating and the complete handoff validation at the acceptance boundary. If a command is unavailable, report that rather than claiming it passed.
- Token/call telemetry is diagnostic, not an optimization target. Reduce duplicated reading, permission churn, overbroad assignments, and repeated validation; do not reduce necessary reasoning or validation merely to lower a token count.

## Safe repository practice

- Codex begins gates with `tools/get-juggle-supervisor-state.sh` and the relevant current diff/status.
- Read durable direction plus compact current state/backlog on a fresh supervision session, then use targeted sections thereafter.
- Treat existing modifications and untracked files as user work. Preserve unrelated changes and never reset, discard, overwrite, or reformat them incidentally.
- Keep changes narrowly scoped. Do not perform opportunistic cleanup or mix puzzle-content corrections with tooling or application changes unless the handoff explicitly requests both.
- Do not commit or push without explicit user approval. Never assume that implementation approval includes publication approval.
- Avoid destructive Git commands. If safe progress would require discarding or overwriting work, stop and ask the user.

## Validation and acceptance

- Run every final validation command listed in `HANDOFF.md` before presenting a task for acceptance, unless the handoff explicitly marks a check as conditional or an expected baseline failure.
- Add focused validation for behavior affected by the change. Do not claim checks passed when they were unavailable, skipped, or expected to fail.
- Report commands and outcomes accurately, including expected baseline failures and environmental limitations.
- Review the final diff and status. Confirm that out-of-scope application files, puzzle data, and user work were not changed.
- A task is not accepted merely because code was written. Its implementation acceptance criteria must be satisfied, required validation must have run, and Codex must review the diff/evidence. Separately, do not treat implementation acceptance as proof of a player/product hypothesis when that hypothesis still requires human/device/operational evidence; record the uncertainty and plan the appropriate validation.

## Lightweight workflow

1. Codex reconstructs current evidence against `juggle-autonomy/PRODUCT_DIRECTION.md`, performs the planning/self-critique loop, updates the dynamic backlog if needed, and records exactly one active coherent slice in `HANDOFF.md`. New handoffs should use `juggle-autonomy/HANDOFF_TEMPLATE.md`.
2. Codex implements the active handoff directly, preserving unrelated work and the shared contract.
3. Codex runs required validation, reviews its diff and evidence, and records exact outcomes.
4. If an unapproved architecture/product decision, unresolved ambiguity, or low confidence blocks correctness, Codex records it for Emaad instead of guessing.
5. Acceptance of one handoff is a gate, not automatically a reason to return control to the user. While the broader objective remains active, Codex continues into the next safe, already-authorized high-leverage handoff. Codex stops only for a concrete user decision/approval, materially new authority, genuine external blocker, or completion.
6. The user decides whether and when to commit, push, merge, or deploy. The supervisor never commits, pushes, deploys, or switches to paid API/ChatGPT Work execution.

Machine-local supervisor state belongs in ignored `.juggle-supervisor/`. The normal user instruction to the persistent Codex supervisor remains `continue`; Codex operates implementation and review directly. The legacy Claude runner is retired and must not be started.
