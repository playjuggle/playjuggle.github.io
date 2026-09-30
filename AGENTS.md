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
- Prefer a cohesive milestone decomposed into coherent implementation slices. A Claude work order should normally share one subsystem or mental model and have observable acceptance criteria.
- Do not bundle unrelated subsystems into one Claude call merely because they belong to the same milestone. Conversely, do not fragment one mental model into tiny calls that force repeated rereading and reorientation.
- Audits, documentation, tooling, and refactors are valuable when they resolve a concrete risk, unblock the product, or materially improve future reliability. They must not become a substitute for advancing the user-visible objective.
- Codex may reorder, replace, or retire planned work when current evidence shows a higher-leverage path. An old spec, backlog label, metric, or previously chosen milestone is not authority merely because it exists.

## Shared implementation contract

- `juggle-autonomy/SHARED_IMPLEMENTATION_CONTRACT.md` and accepted entries in `juggle-autonomy/ARCHITECTURE_DECISIONS.md` keep Codex and Claude aligned across ownership changes.
- Accepted code is current repository truth regardless of which agent wrote it. A different stylistic preference is not a reason to rewrite accepted work.
- A material architecture choice must already be authorized by the active handoff or an accepted architecture decision. A worker may not silently introduce one.
- Codex fallback may continue only work whose intended direction is explicit or mechanically unambiguous. If continuing Claude's partial work would require guessing at an unwritten architecture plan, Codex must park that slice or choose another implementation-ready slice.
- Routine Claude calls should receive all task-relevant binding constraints in `HANDOFF.md`; they do not need to reread `AGENTS.md`, the entire shared contract, product direction, or architecture log on every task. Those broader files are consulted only for a named conflict, architecture-sensitive work, fallback, or re-entry after another writer changed the task.

## Roles and write ownership

- Codex is the product-minded project manager, technical lead, reviewer, and fallback implementer. It defines scope and acceptance criteria, protects product/architecture/compatibility constraints, reviews implementation evidence, and chooses the next high-leverage work.
- Claude Code is the **preferred primary implementation agent**.
- When Claude subscription usage is exhausted, Codex may become the **temporary fallback implementation agent** only through the guarded fallback transition in `juggle-autonomy/CODEX_SUPERVISOR_PROTOCOL.md`. This is a continuity mechanism, not permission for Codex to make new material architecture or unresolved product choices.
- The current implementation owner is recorded in ignored supervisor state. Exactly one implementation owner may exist at a time. When ownership is `claude`, Codex stays read-only except for handoff/review artifacts. When ownership is `codex`, Claude must remain read-only and the Claude runner must not start.
- A stale Claude session must never resume after Codex has changed implementation work. If Codex takes ownership but safely aborts before any worktree change, the prior Claude session may remain resumable. Otherwise later Claude work starts from current repository state in a fresh session.
- The user authorizes Codex, as project manager, to invoke the locally authenticated Claude Code CLI and provide Anthropic the active handoff, repository instructions, and repository content reasonably necessary for Claude to perform that handoff. Do not repeatedly ask the user to relay or approve routine Codex-to-Claude coordination. This standing authorization does not cover unrelated secrets, API-key billing, materially expanded scope, commits, pushes, or deployments.
- The user retains final authority over scope, product behavior, commits, pushes, and deployment.

## Claude delegation and token efficiency

- `HANDOFF.md` is the single active work order. Do not accumulate contradictory assignments or make Claude reconstruct the assignment from chat history. Codex must copy the specific binding product/architecture constraints needed for that slice into the handoff so Claude does not have to load broad PM documents.
- Reuse the same Claude session for a correction, interruption, or usage-limit recovery while that session remains authoritative and no other implementation writer has changed the task. An attempt number is not a reason to create a new session.
- Do not make a resumed Claude session reread unchanged policy/context files. Give it the bounded correction or re-entry delta and let it use retained context; broaden only when evidence shows context drift or a real conflict.
- Do not model-poll Claude. Invoke the blocking local runner once and let its model-free process wait complete. Re-running status every few seconds/minutes wastes Codex turns without accelerating Claude. Check status only after an interruption/abnormal condition, when the runner has returned, or when the user explicitly asks.
- Use compact supervisor state, the Claude report, targeted diffs, and exact relevant sections before opening full result/stderr logs. Full logs are diagnostic evidence, not routine context.
- Claude should prefer native Read/Grep/Glob plus Edit/Write for code work. Shell commands should be the exact validation/evidence commands the handoff actually requires; if a command is denied, report the denial rather than spending turns trying equivalent wrappers.
- Test proportionately while iterating. Use focused checks for the changed behavior and run the complete handoff validation at the meaningful acceptance boundary. Reuse still-valid evidence rather than rerunning expensive unchanged checks without a reason.
- Token/call telemetry is diagnostic, not an optimization target. Reduce duplicated reading, permission churn, overbroad assignments, and repeated validation; do not reduce necessary reasoning or validation merely to lower a token count.

## Safe repository practice

- Codex begins gates with `tools/get-juggle-supervisor-state.sh` and the relevant current diff/status. Claude should inspect repository status before editing when needed to distinguish pre-existing work from its own changes.
- On a fresh Codex supervision session, read durable direction plus the compact current state/backlog once, then use targeted sections thereafter. On a fresh Claude task session, the runner-loaded `CLAUDE.md` plus `HANDOFF.md` should normally be sufficient before source inspection; `AGENTS.md` and broad PM history are not routine builder context.
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
- If Codex fallback finishes a task but has substantive uncertainty that would benefit from Claude's stronger implementation judgment, it must mark the task for **targeted Claude review** rather than treating the work as final. That review is limited to the named risk, objective defects, and contract violations; it is not an invitation to refactor for preference.

## Lightweight workflow

1. Codex reconstructs current evidence against `juggle-autonomy/PRODUCT_DIRECTION.md`, performs the planning/self-critique loop, updates the dynamic backlog if needed, and records exactly one active coherent slice in `HANDOFF.md`. New handoffs should use `juggle-autonomy/HANDOFF_TEMPLATE.md`.
2. Codex follows `juggle-autonomy/CODEX_SUPERVISOR_PROTOCOL.md`. Claude remains the first-choice worker whenever subscription usage is available.
3. Claude performs only the active handoff, preserves unrelated work, runs proportionate/final validation, and reports exact changes. Claude does not choose the next milestone, commit, or push.
4. Codex independently reviews Claude's diff and required evidence. It accepts the task or records one bounded correction for the same Claude session.
5. If Claude stops specifically because subscription/session usage is exhausted, Codex evaluates the guarded takeover gate. It may take ownership only if the active handoff is implementation-ready without a new material architecture/product decision.
6. During Codex fallback, Codex follows the same handoff and shared contract, preserves a takeover checkpoint, records why its approach is continuous with the existing plan, runs required validation, and either accepts with evidence or requests targeted fresh-session Claude review.
7. Acceptance of one handoff is a gate, not automatically a reason to return control to the user. While the user's broader objective remains active, Codex continues into the next safe, already-authorized high-leverage handoff. Codex stops only for a concrete user decision/approval, materially new authority, genuine external blocker, or completion.
8. The user decides whether and when to commit, push, merge, or deploy. The supervisor never commits, pushes, deploys, or switches to paid API/ChatGPT Work execution.

Machine-local supervisor state belongs in ignored `.juggle-supervisor/`. The normal user instruction to the persistent Codex supervisor remains `continue`; Codex, not the user, operates the worker, fallback, and review gates.
