# Juggle Codex Supervisor Protocol

## Purpose and authority

The persistent Codex conversation is the user's project-management control point. Codex owns product-minded sequencing, task definition, implementation, validation, and review. Codex is the sole implementation worker for Juggle; Claude Code is not invoked for this project. If a slice requires an unapproved material architecture or product decision, or correctness is uncertain, record the decision for Emaad rather than guessing.

The user retains final authority over scope, product behavior, commits, pushes, and deployment. Do not commit, push, deploy, use network services, or switch to paid API/ChatGPT Work execution unless an active user instruction explicitly authorizes it.

## Product-first planning

At a new supervision session, reconstruct current evidence from `juggle-autonomy/PRODUCT_DIRECTION.md`, `CURRENT_STATE.md`, `juggle-autonomy/WORKING_BACKLOG.md`, the active `HANDOFF.md`, supervisor state, and the current diff/status. Consult historical plans only for a named unresolved question.

Before a substantial handoff, identify the player/product/engineering problem and evidence, the desired outcome or hypothesis, why it is the highest-leverage slice, and observable completion criteria. Consider credible alternatives and challenge stale assumptions, opportunity cost, evidence quality, unnecessary complexity, and dependency order. Keep the reasoning compact. After implementation, distinguish code acceptance from any product hypothesis that still needs player or device evidence. Update state/backlog and reassess the horizon after meaningful new evidence or several tasks in one subsystem.

`HANDOFF.md` is the single active work order. Durable product intent belongs in `PRODUCT_DIRECTION.md`; technical decisions in `ARCHITECTURE_DECISIONS.md`; factual evidence in `CURRENT_STATE.md`; candidate work in `WORKING_BACKLOG.md`.

## Core invariants

1. Exactly one implementation writer exists at a time. Supervisor state may record `implementation_owner=codex|none`; Claude ownership is retired for this project.
2. Codex implements the active handoff directly and preserves unrelated work and accepted code.
3. Do not introduce an unapproved material architecture or product decision. Surface unresolved taste, low confidence, or ambiguity to Emaad.
4. A stylistic preference is not a defect. Rework requires material evidence under the shared implementation contract.
5. Do not start the legacy Claude runner, create Claude invocation sessions, or transmit repository content to Claude.
6. Keep changes within the active handoff. Do not commit, push, deploy, or publish without explicit user approval.

## Safe repository practice

- Begin with `tools/get-juggle-supervisor-state.sh`, `git status --short --branch`, the active handoff, and relevant current state.
- Treat existing modifications and untracked files as user work. Preserve unrelated changes; never reset, discard, overwrite, or reformat them incidentally.
- Use focused validation while iterating and every required final validation command in the handoff before acceptance. Report unavailable checks accurately.
- Review the final diff/status and confirm excluded files and live puzzle data remain unchanged.
- Prefer compact supervisor state, targeted diffs, and exact validation evidence over broad log dumps.

## Workflow

1. Reconstruct current evidence against product direction, challenge the next move, and choose one coherent authorized slice.
2. Record the slice and acceptance criteria in `HANDOFF.md`, using `HANDOFF_TEMPLATE.md` for new work orders.
3. Implement directly under the handoff and shared contract, preserving all pre-existing work.
4. Run required checks, review the diff, and record what changed, test outcomes, remaining uncertainty, and any decisions for Emaad.
5. After acceptance, continue into the next safe, already-authorized high-leverage slice while the broader objective remains active. Stop for a concrete user decision, materially new authority, genuine external blocker, or completion.

## Legacy supervisor files

`tools/run-juggle-builder.sh` and older Claude state formats are retained for historical recovery evidence only. They are not part of the active workflow and must not be used to launch Claude.
