# Claude Code Instructions

Claude Code is Juggle's preferred primary implementation agent. Codex is the product-minded project manager/reviewer and may temporarily implement only through the guarded fallback workflow when Claude subscription usage is exhausted.

`HANDOFF.md` is the single active work order. The current handoff overrides older conversation plans; do not choose backlog work, infer the next milestone, or revive a superseded task.

## Context discipline

Claude Code automatically loads this file for delegated project sessions. The delegated runner disables Claude auto-memory so stale model-written notes cannot compete with repository truth. Do not reconstruct project history from prior chats.

On a **fresh implementation session**:

1. Read `HANDOFF.md` once.
2. Inspect only the source files, current diff/status, and exact evidence named or materially required by that handoff.
3. Read a targeted entry from `juggle-autonomy/ARCHITECTURE_DECISIONS.md`, `juggle-autonomy/SHARED_IMPLEMENTATION_CONTRACT.md`, `CURRENT_STATE.md`, or `juggle-autonomy/PRODUCT_DIRECTION.md` only when the handoff explicitly points to it or a concrete conflict/architecture-sensitive question requires it. Do not read `AGENTS.md` routinely; Codex must carry task-relevant binding product/architecture constraints into the handoff.
4. If this is a targeted review of Codex fallback work, read `.juggle-supervisor/CODEX_TAKEOVER.md` and `.juggle-supervisor/codex-fallback-report.md`, then inspect the named risk and changed files first.

On a **resumed session** after a correction, interruption, or usage reset, use retained task context. Read only the new correction/re-entry delta, any actually changed handoff section, the current diff, and files needed for unfinished work. Do not reread unchanged policy documents or repository history by ritual.

If automatic context compaction occurs, preserve the active handoff objective, binding decisions, modified files, unresolved defects, and remaining validation. Do not resurrect superseded work after compaction.

If supervisor evidence says `implementation_owner=codex` or state is `codex_fallback_active`, do not modify implementation files.

Preserve unrelated tracked and untracked user changes. Do not reset, discard, broadly reformat, or opportunistically clean up files. Do not delegate product-code edits, choose a new milestone, commit, push, or deploy.

## Implementation continuity

- Treat accepted code as current repository truth regardless of whether Claude or Codex wrote it.
- Do not rewrite Codex-authored code merely because you would have implemented it differently.
- Reopen accepted work only for a material reason: failed acceptance/player outcome, reproducible regression, validation failure, compatibility/data-integrity/security violation, meaningful maintainability/testability problem, performance problem, or conflict with an accepted architecture decision.
- If the active handoff specifies an implementation direction, follow it. If a materially better alternative would require changing architecture, product behavior, or a binding contract, report the decision needed instead of silently switching approaches.
- When reviewing Codex fallback work, review the recorded approach, named risk, and changed files first. Expand inspection only when evidence requires it.
- Preserve published-puzzle data and existing `localStorage` compatibility unless the handoff explicitly authorizes a change. Never guess historical puzzle corrections.

## Tool and token discipline

- Read only task-relevant files. Prefer native Read/Grep/Glob for inspection and Edit/Write for changes.
- Use shell commands only when necessary for exact validation/evidence in the handoff or a tightly related diagnosis. Run the direct command from the existing project directory; do not add `cd`, pipes, redirects, `tail`, `echo`, loops, `sed`, or alternate wrappers merely to work around a denial.
- If a required command is denied by permissions, record the denial once and continue with available evidence rather than spending turns trying variants.
- Use focused checks while iterating; run the complete required handoff validation before final completion. Do not rerun expensive unchanged evidence without a reason.
- Do not summarize or restate large source documents merely to prove you read them. Spend reasoning on the implementation and named acceptance risks.

## Validation and completion

Run every final validation command required by the handoff. Do not hide expected failures or claim unavailable checks passed.

At completion, report compactly:

- implementation mode (`primary implementation`, `resumed Claude work`, or `Codex fallback review`);
- every file changed and why;
- approach followed and whether it continued an existing approach;
- exact validation commands run and results;
- behavioral/player or compatibility impact;
- objective defects found or corrected, if any;
- known failures, limitations, and decisions still needed;
- whether any material architecture/product decision was introduced (normally `none` unless already authorized);
- final repository status relevant to the task.
