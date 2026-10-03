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

## Stop and failure rules

| State/outcome | Meaning | Action |
| --- | --- | --- |
| `accepted` / `implementation_success` | Codex completed the active handoff and reviewed the evidence | Record acceptance, then choose the next high-leverage authorized handoff if the broader objective remains active |
| `implementation_in_progress` | Codex is actively working on the recorded handoff | Continue that work; do not start a concurrent implementation process |
| `decision_required` | Correctness depends on an unresolved product or material architecture decision | Preserve current work, record the precise decision and evidence for Emaad, and stop dependent implementation |
| `validation_failed` | A required check failed or exposed a defect | Inspect targeted evidence, repair within scope when unambiguous, and rerun affected checks; replan or record a decision if the cause is not safely resolvable |
| `worker_failure` | A command or tool failed for a reason other than an identified validation defect | Read compact state and relevant error output, diagnose the cause, then retry only when the cause is understood; do not blindly repeat a failing action |
| `external_blocker` | A required capability or environmental condition is unavailable | Complete independent work, record what could not run and why, and stop only the dependent work |
| `complete` | The authorized objective and required acceptance evidence are satisfied | Report exact changes, checks, remaining uncertainty, and any required user decision |

A run stops when its active handoff is accepted, an unresolved decision or genuine external blocker prevents safe progress, or the broader objective is complete. Do not treat an arbitrary attempt count, an unrelated backlog item, or a merely inconvenient check as a stop condition. If `HANDOFF.md` changes while unfinished task state exists, reconcile the state and explicitly establish the next authorized slice before proceeding.

## New handoffs

Use `juggle-autonomy/HANDOFF_TEMPLATE.md`. Each new work order must state:

- the problem/evidence, desired outcome or hypothesis, and why this is the highest-leverage next slice;
- one coherent implementation slice and the targeted context to inspect;
- Codex as the sole implementation worker and the continuity basis for the work;
- whether a new material architecture or product decision is required; if unresolved, record it for Emaad before dependent implementation;
- binding approach and constraints, allowed changes and exclusions, acceptance criteria, and complete final validation sufficient for Codex to resume safely from repository state.

Existing handoffs remain valid when their scope and acceptance criteria are clear. Do not rewrite an active handoff merely to adopt a template while unfinished work exists; update it only when the authorized scope or acceptance conditions actually change, and reconcile the recorded task state at the same time.

## Compact persistent state

Machine-local supervisor state belongs in ignored `.juggle-supervisor/`. Keep it compact and structured so a fresh supervision session can resume without relying on conversation memory. The supervisor reads and updates these fields:

- `state.json`: active task identifier/hash, task status, `implementation_owner` (`codex` or `none`), handoff hash, outcome, required/actual validation, changed-file summary, relevant worktree/index fingerprints, unresolved decision or blocker, and last compact diagnostic telemetry when available.
- `codex-report.md`: latest concise implementation report with approach, changed files, exact validation results, impact, and unresolved uncertainty.
- `codex-review.md`: compact acceptance evidence and any bounded correction/review findings.
- `takeover-git-status.txt`, `takeover-worktree.patch`, `takeover-index.patch`, and `takeover-fingerprint.txt`: continuity checkpoint evidence when the local workflow records a material task-state transition.
- `task-result-*`: optional full command/tool diagnostics; inspect only when compact state and targeted output do not explain a failure.

At a gate begin with:

```sh
tools/get-juggle-supervisor-state.sh
```

Then inspect the active handoff, compact report/checkpoint, relevant diff/status, and validation evidence. Broaden only when the task or unexpected evidence requires it. Do not store secrets or rely on ignored machine-local state as the only record of a product or architecture decision; record such decisions in the appropriate tracked document after authorization.

## Legacy supervisor files

`tools/run-juggle-builder.sh` and older Claude state formats are retained for historical recovery evidence only. They are not part of the active workflow and must not be used to launch Claude.
