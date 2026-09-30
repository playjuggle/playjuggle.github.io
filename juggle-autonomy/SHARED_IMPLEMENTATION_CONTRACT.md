# Juggle Shared Implementation Contract

Read this file before Codex fallback, architecture-sensitive assignment design, or Claude re-entry after another implementation writer changed the task. Routine builders should receive the binding constraints in `HANDOFF.md` rather than rereading this whole file on every turn.

## Authority and source of truth

Use this order when instructions appear to compete:

1. The user's latest explicit instruction and approvals.
2. `AGENTS.md` repository/product policy.
3. Accepted entries in `juggle-autonomy/ARCHITECTURE_DECISIONS.md` for durable cross-task technical decisions.
4. The active `HANDOFF.md` for the current bounded work order, explicit approach constraints, exclusions, acceptance criteria, and validation.
5. `CURRENT_STATE.md` and observed repository behavior for factual context.
6. Historical plans/audits/specifications only when a current unresolved question requires them.

Do not average conflicting sources. Follow the higher/current authority and identify stale documentation when it matters. A handoff may supersede an accepted architecture decision only when it says so explicitly and records the user's authorization.

## One implementation writer

Exactly one implementation owner exists: `claude`, `codex`, or none. Supervisor state/locks, not conversation memory, determine ownership.

Claude is preferred because the user currently trusts its implementation judgment more. Codex fallback exists to turn otherwise-idle Codex capacity into progress when Claude is usage-limited without creating two competing implementations.

## Default implementation style

- Preserve current behavior and compatibility unless the handoff explicitly changes them.
- Prefer the smallest **complete** change that satisfies the handoff and fits existing repository patterns; do not confuse “smallest” with “highest-value next task.”
- Reuse existing abstractions before inventing new ones. Do not add a framework, dependency, service, generalized subsystem, or speculative abstraction merely because it is cleaner in isolation.
- Keep public behavior, persisted data contracts, analytics contracts, puzzle semantics, and deployment assumptions stable unless explicitly authorized.
- Avoid opportunistic cleanup, broad formatting, renaming, or refactoring outside the active task.
- When multiple local implementations are equally valid and do not alter architecture/contracts, follow nearby code conventions and choose the simpler one.
- Tests should target the changed behavior and failure mode. Use focused checks while iterating and complete required validation at acceptance.

## Work-order quality and continuity

A good handoff/re-entry note is compact and answers:

- **Problem/evidence:** what is wrong or what opportunity matters?
- **Desired outcome/hypothesis:** what player/product/engineering behavior should change?
- **Why now:** why is this the highest-leverage next slice?
- **Implementation slice:** what coherent unit/mental model is being changed now?
- **Binding decisions:** interfaces, product rules, architecture, compatibility, and persistence constraints that may not drift.
- **Files/boundary:** likely relevant files and what must remain untouched.
- **Acceptance:** observable behavior plus proportionate automated/manual evidence.
- **Open question:** only a question that genuinely remains unresolved.

Do not pass full transcripts or force the next model to reverse-engineer reasoning from a large diff. Do not bundle unrelated subsystems into one work order or create tiny calls that repeat the same context loading.

## Preference is not a defect

Accepted code is current repository truth regardless of whether Codex or Claude wrote it. A later agent must not rewrite it merely because it prefers a different idiom, decomposition, naming style, algorithm, or abstraction.

Reopening accepted work requires a material reason such as:

- an acceptance criterion or intended player/product outcome is not actually met;
- required validation fails;
- a reproducible bug or regression exists;
- a documented compatibility, security, data-integrity, maintainability, testability, or performance constraint is materially violated;
- the implementation contradicts an accepted architecture decision; or
- a newly discovered requirement makes the accepted approach materially unsuitable.

If none applies, continue from the accepted implementation.

## Material architecture choices

A worker may make ordinary local coding choices inside established boundaries. It may not silently make a new material architecture choice. Examples include introducing/replacing a framework, persistence model, service boundary, package/dependency strategy, build system, state-management pattern, major data shape, hosting model, or cross-cutting abstraction.

For a material choice, one of the following must already be true before implementation:

- the active handoff specifies the choice; or
- an accepted architecture decision specifies it.

Otherwise the worker reports the decision needed. Codex fallback is never allowed to create a new material architecture or unresolved product decision merely because Claude is unavailable.

## Codex fallback gate

After verified Claude usage/session unavailability and only when no Claude child is active, Codex may take over when at least one of these is true:

- the current implementation approach is already decided and Codex can continue it;
- the defect is bounded and acceptance is objective;
- the handoff/architecture record already resolves the design and interface choices.

Codex must not take over a slice whose next step requires broad refactor strategy, unresolved product judgment, a material architecture choice, or reconstruction of Claude's private intent. Preserve ambiguous partial work and wait for Claude for that implementation. Codex may continue read-only planning/review that does not modify repository implementation state.

## Efficient re-entry after another agent

Before Codex fallback edits, the supervisor records the exact worktree/index/fingerprint and prior Claude session identity. If Codex changes implementation work, the old Claude session becomes stale; later Claude involvement starts fresh from current repository truth. If Codex aborts before any worktree change, the old session may remain resumable.

A fresh Claude review of Codex work should be requested only for a named risk: a complex algorithm/state issue, architecture boundary, meaningful maintainability/testability concern, compatibility/data integrity, or behavior Codex cannot independently verify. Review that risk and relevant changed files first rather than rereading project history.

Reports should explain decisions a returning agent would otherwise have to reconstruct, but should not narrate routine line-by-line coding.

## Reporting standard

Every implementation report should state compactly:

- implementation mode and worker;
- files changed and why;
- approach followed and whether it continued an existing approach;
- exact validation and results;
- player/behavior/compatibility impact;
- objective defect or unresolved uncertainty;
- whether any material architecture/product decision was introduced (normally `none` unless already authorized).
