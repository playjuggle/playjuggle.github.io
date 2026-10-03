# Juggle Shared Implementation Contract

Read this file before architecture-sensitive work or resuming implementation after an interruption or material worktree change. Codex is Juggle's sole implementation worker; do not invoke Claude Code for this project. Keep routine handoffs focused by including the binding constraints they need rather than requiring repeated broad rereads.

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

Exactly one implementation owner exists at a time: `codex` or none. Supervisor state, not conversation memory, records ownership and task status. Codex must not start a second concurrent implementation process for the same task.

Codex is the sole implementation worker. If Codex cannot resolve a product or architecture decision, or confidence is too low to proceed safely, stop and record the decision for Emaad rather than guessing or transferring implementation ownership.

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

Accepted code is current repository truth regardless of who authored it. Codex must not rewrite accepted work merely because it prefers a different idiom, decomposition, naming style, algorithm, or abstraction.

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

Otherwise Codex records the decision needed for Emaad and does not implement a guess. Unresolved material architecture and product decisions remain outside the worker's authority.

## Continuity after interruption or worktree changes

Before resuming implementation after an interruption or a material worktree change, Codex inspects the current handoff, status, diff, and relevant state so it continues from repository truth. Continue only when at least one of these is true:

- the current implementation approach is already decided and Codex can continue it;
- the defect is bounded and acceptance is objective;
- the handoff/architecture record already resolves the design and interface choices.

If none applies, do not guess at broad refactor strategy, unresolved product judgment, or a material architecture choice. Preserve ambiguous partial work and record the concrete decision needed for Emaad. Read-only investigation may continue where it does not imply an implementation decision.

## Efficient resumption

Before resuming after a material interruption or ownership-state transition, record the relevant status, staged/unstaged diff, untracked paths, and content fingerprint where the local supervisor supports them. This preserves a clear continuity point and prevents accidental loss or duplication of work.

Re-read only the changed handoff/context, current diff, and unfinished work; revisit broader project documents only when a named unresolved question requires them.

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
