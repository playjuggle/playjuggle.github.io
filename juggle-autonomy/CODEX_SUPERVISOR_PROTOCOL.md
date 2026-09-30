# Juggle Codex Supervisor Protocol

## Purpose and authority

The persistent Codex conversation is the user's single project-management control point. The normal user instruction remains `continue`. Codex owns product-minded sequencing, task definition, worker selection, validation/review, and guarded fallback. Codex is the implementation worker for Juggle. Claude Code is not invoked for this project. If a slice genuinely exceeds Codex's judgment, stop and raise it with Emaad rather than delegating it, because Claude's usage is a scarce resource shared with his studying.

The user has standing-authorized Codex to send Anthropic, through the locally authenticated Claude Code CLI and Claude Pro subscription, the current handoff and repository content reasonably necessary for that task. Routine launches/resumptions do not require another confirmation. This does not authorize API-key billing, unrelated secret disclosure, expanded product scope, commits, pushes, deployment, or a new material architecture/product decision.

## Plan by product leverage, not task convenience

At a new Codex supervision session, reconstruct the planning state from `juggle-autonomy/PRODUCT_DIRECTION.md`, current `CURRENT_STATE.md`, `juggle-autonomy/WORKING_BACKLOG.md`, the active `HANDOFF.md`, compact supervisor state, and the current diff/status. Read historical plans/audits only for a named unresolved question.

Before creating a substantial handoff, Codex identifies:

- the player/product/engineering problem and evidence;
- the desired outcome or hypothesis;
- why this is the highest-leverage next slice toward the durable destination;
- one coherent implementation slice with observable acceptance criteria.

Use a closed-loop PM cycle rather than backlog autopilot:

1. compare current evidence with the destination/end-state dimensions;
2. identify the most consequential gaps and dependencies;
3. consider at least two plausible next moves when there is a real choice;
4. challenge the preferred move for stale assumptions, local-metric gaming, opportunity cost, evidence weakness, unnecessary complexity, and whether a different dependency would unlock more value;
5. choose one milestone/slice, then define what evidence would falsify or complete it;
6. after implementation review, separately ask whether the product/engineering hypothesis was actually supported; code can be accepted while an experiential hypothesis remains unproven;
7. update state/backlog/decisions and repeat from current evidence rather than assuming the prior roadmap remains correct.

Keep this reasoning compact; it is a quality gate, not a requirement to spend model tokens writing essays. Trigger a broader horizon review after meaningful user/player evidence, after an accepted milestone, when several consecutive tasks have stayed in one subsystem, when the same correction repeats, or when local metrics improve without a corresponding product outcome.

Do not mechanically choose the smallest unresolved item, the easiest metric to move, or another audit/document because it is locally convenient. Do not bundle unrelated mental models into one Claude call, and do not micro-fragment one mental model into repeated calls that force context reloads. The backlog is a revisable candidate set, not authority or a completion checklist.

`HANDOFF.md` is the single active work order. Durable product intent belongs in `juggle-autonomy/PRODUCT_DIRECTION.md`; durable cross-task technical decisions belong in `juggle-autonomy/ARCHITECTURE_DECISIONS.md`; factual current-state evidence belongs in `CURRENT_STATE.md`; short-lived candidate work belongs in `juggle-autonomy/WORKING_BACKLOG.md`.

## Core invariants

These rules are never relaxed merely because one model is unavailable:

1. **Exactly one implementation writer.** Supervisor state records `implementation_owner=claude|codex|none`. Claude cannot run while Codex fallback owns implementation.
2. **Codex implements.** Claude Code is not a worker on this project. Low confidence or a repeated failure is a stop condition to raise with Emaad, not a reason to delegate.
3. **No stale-session continuation after cross-agent edits.** If Codex changes the worktree during fallback, the prior Claude implementation session is no longer authoritative. If Codex safely aborts before any worktree change, that session may remain resumable.
4. **No architecture/product invention during fallback.** Codex may continue an existing accepted approach, handoff-specified approach, or mechanically unambiguous local continuation. If a new material architecture/product decision or reconstruction of Claude's private intent is required, wait for Claude/user decision instead of guessing.
5. **Preference is not a defect.** Neither model rewrites accepted work merely because it prefers another style/decomposition. Rework requires material evidence under the shared implementation contract.
6. **Checkpoint every ownership transfer.** The runner captures status, worktree/index patches, and a content fingerprint before Codex writes, including untracked files.
7. **Targeted review, not automatic re-litigation.** Valid Codex fallback need not consume Claude tokens for a complete second implementation review. Request Claude only for a named material risk or uncertainty.
8. **No arbitrary attempt ceiling.** The runner performs one bounded invocation per command but does not stop a sound task merely because an attempt counter reached a ritual number. Repeated failure should trigger Codex replanning, not a mechanical cap.

## Claude token/call discipline

Efficiency means removing duplicated work, not weakening reasoning or verification.

- Invoke `tools/run-juggle-builder.sh continue` once and let it block while the local Claude process works. Its local waiting consumes no Codex/Claude model turns. Do **not** model-poll `get-juggle-supervisor-state.sh` on a cadence while the runner is still active.
- Resume the same Claude session after a bounded correction, interruption, or usage reset when no other implementation writer changed the task and its context remains useful. Start a new session for a distinct accepted task/slice. If telemetry shows a repeatedly bloated session with poor useful progress, and repository/handoff state fully captures the unfinished work, a deliberate fresh-session reset is preferable to carrying irrelevant history; record the reason rather than resetting by ritual.
- A resumed session should receive only the re-entry delta: correction note, changed handoff section if any, current diff, and unfinished work. Do not instruct it to reread unchanged `AGENTS.md`, `CURRENT_STATE.md`, the shared contract, and architecture log by ritual.
- On a fresh task session, Claude Code automatically loads the concise project `CLAUDE.md`; Claude then reads the current handoff once and only task-relevant source/evidence. `AGENTS.md`, product direction, current-state history, shared contract, and architecture log are **not** routine builder reads. Codex carries binding constraints into the handoff and points Claude to a targeted broader entry only when needed.
- Use the compact state/Claude report/usage telemetry first. Open full result JSON or stderr only to diagnose a specific failure. Do not pass full transcripts between models. Cached-read telemetry reflects reused request context, not literal repository file rereads; treat sustained high cache/context use with low progress as a signal to narrow/restart context, not as a reason to weaken reasoning.
- Prefer focused validation during iteration and the complete required handoff validation at acceptance. Reuse still-valid evidence rather than repeating expensive unchanged checks.
- Token counts are diagnostic. High cache-read/output counts should prompt investigation of repeated reading, oversized handoffs, permission churn, or duplicated validation; they are not a reason to reduce necessary reasoning quality.

## Compact persistent state

Machine-local state is kept in ignored `.juggle-supervisor/`:

- `state.json`: task hash/state/owner, outcome/validation, Claude session/mode, fallback disposition, last compact usage telemetry, and fingerprints.
- `claude-report.md`: Claude's latest concise final report.
- `claude-result-attempt-N.json` / `claude-stderr-attempt-N.log`: full diagnostic evidence; do not read routinely.
- `CODEX_CORRECTION.md`: one bounded correction after Claude implementation/review.
- `codex-review.md`: optional compact Codex acceptance evidence.
- `CODEX_TAKEOVER.md`: Codex's required safety/continuity declaration before fallback ownership begins.
- `takeover-git-status.txt`, `takeover-worktree.patch`, `takeover-index.patch`, `takeover-fingerprint.txt`: exact takeover checkpoint evidence.
- `codex-fallback-report.md`: compact explanation of Codex implementation approach, changed files, and validation.
- `fallback-result-*`: post-fallback checkpoint evidence.

At a gate begin with:

```sh
tools/get-juggle-supervisor-state.sh
```

Then inspect only the active handoff, compact report/checkpoint, relevant diff/status, and validation evidence. Broaden only when the task or unexpected evidence requires it.

## Normal Claude path

When state is ready for Claude, Codex runs:

```sh
tools/run-juggle-builder.sh continue
```

The runner launches exactly one bounded Claude invocation and waits locally. Do not issue periodic Codex status checks while that command is still running.

After it returns, Codex independently reviews the changed behavior/diff and required validation evidence. Claude's report or process exit alone is not acceptance.

If accepted:

```sh
tools/run-juggle-builder.sh review accept pass .juggle-supervisor/codex-review.md
```

or, only when the handoff explicitly defines the nonzero result as expected:

```sh
tools/run-juggle-builder.sh review accept expected-failure .juggle-supervisor/codex-review.md
```

If implementation is materially deficient, Codex writes one bounded `.juggle-supervisor/CODEX_CORRECTION.md` focused on the observed defect and records:

```sh
tools/run-juggle-builder.sh review correction .juggle-supervisor/CODEX_CORRECTION.md
```

The next `continue` resumes the same Claude session. The resumed prompt does not replay the full policy/context stack.

If repeated corrections expose a wrong premise or oversized slice, Codex replans the handoff rather than repeatedly asking Claude to patch symptoms. An attempt count itself is never the blocker.

## Claude usage-limit path

The runner recognizes usage/session exhaustion separately from generic failure, including responses such as `You've hit your session limit ... resets ...`. It stores any available reset hint and returns `usage_limit_exhausted` without API fallback or blind retry.

For compatibility with older Juggle state, a `continue` from `worker_failure` first checks saved result/stderr evidence. If that evidence is actually a usage/session limit, the runner repairs state to `usage_limit_exhausted` **without invoking Claude**.

Once `usage_limit_exhausted` is reached, Codex chooses one of two paths.

### A. Resume Claude after usage resets

Only after subscription usage is known to be available again:

```sh
tools/run-juggle-builder.sh claude-resume
```

This resumes the same Claude session only if Codex has not changed implementation ownership/work in the meantime.

### B. Guarded Codex takeover

Takeover is allowed only when all are true:

- the handoff does not explicitly disallow fallback;
- remaining work is within already-authorized scope;
- current partial implementation has an explicit or mechanically unambiguous direction;
- Codex can continue without a new material architecture/product decision;
- Codex can preserve Claude's already-correct partial work rather than replacing it wholesale; and
- acceptance criteria/validation are concrete enough to determine correctness.

If any item is false, Codex does not code around Claude. It may continue read-only planning/review that does not alter repository implementation state, but implementation waits for Claude.

If safe, Codex writes a short takeover note containing these exact safety markers:

```text
Fallback safety: SAFE
New material architecture decision required: no
Continuity basis: existing accepted approach

Why continuation is unambiguous:
<brief evidence from HANDOFF/current diff>

Binding constraints:
<the approach/contracts Codex must preserve>
```

Allowed `Continuity basis` values are exactly:

- `existing accepted approach`
- `handoff-specified approach`
- `mechanically unambiguous local continuation`

Then:

```sh
tools/run-juggle-builder.sh fallback start /path/to/takeover-note.md
```

The runner verifies state/note, snapshots the dirty worktree/index, sets `implementation_owner=codex`, and freezes Claude. If Codex later aborts with an unchanged fingerprint, the prior Claude session is restored as resumable; otherwise it remains stale.

## Codex fallback implementation

Codex implements **the same active handoff** under the same product/architecture contract. Fallback is not permission to broaden scope, redesign working code, or substitute a different architecture.

Before closing fallback, Codex runs required final handoff validation and writes a compact report containing at least:

```text
Implementation worker: Codex fallback
Approach continuity: <how this continued the existing/handoff approach>
Validation: <commands and results>
Material architecture decisions introduced: none
```

Also list changed files, player/behavior/compatibility impact, and unresolved material uncertainty.

If the handoff is fully satisfied:

```sh
tools/run-juggle-builder.sh fallback finish pass /path/to/fallback-report.md accept
```

Use `expected-failure` only when explicitly permitted by the handoff. This accepts valid work without automatically spending Claude tokens re-reviewing it.

## Targeted Claude review of Codex fallback

If Codex completed fallback but has a **named material risk** that merits Claude's stronger implementation judgment:

```sh
tools/run-juggle-builder.sh fallback finish pass /path/to/fallback-report.md claude-review
```

State becomes `codex_fallback_waiting_for_claude_review`. When Claude usage is available:

```sh
tools/run-juggle-builder.sh continue
```

starts a **fresh Claude session**. Review the takeover/report and named risk/changed files first. Claude is explicitly prohibited from reimplementation for stylistic preference and may change code only for a concrete bounded defect within the active handoff.

Codex performs the ordinary review gate afterward. If Claude hits a usage limit during this review, Codex may **not** take over its own review; wait and later `claude-resume`.

## Safe fallback abort

If Codex transfers ownership but realizes before changing the worktree that takeover should not proceed, write a reason file and run:

```sh
tools/run-juggle-builder.sh fallback abort /path/to/reason.md
```

Abort is permitted only when the current worktree fingerprint exactly matches the takeover checkpoint. Any tracked/staged/deleted/untracked relevant change refuses abort, preventing work from silently disappearing and preserving stale-session safety.

## New handoffs

Use `juggle-autonomy/HANDOFF_TEMPLATE.md`. New work orders explicitly state:

- the problem/evidence, desired outcome/hypothesis, and why-now leverage;
- one coherent implementation slice and targeted context to inspect;
- `Codex fallback: Allowed | Disallowed`;
- whether a new material architecture/product decision is required;
- fallback continuity basis; and
- binding approach/constraints, acceptance criteria, and final validation sufficient for another worker to continue without reconstructing private reasoning.

Existing pre-template handoffs remain valid legacy handoffs. Do not rewrite an active handoff merely to adopt the template while unfinished state exists.

## Stop and failure rules

| State/outcome | Meaning | Action |
| --- | --- | --- |
| `accepted` / `implementation_success` | Codex accepted Claude implementation | Choose the next high-leverage authorized handoff |
| `accepted` / `codex_fallback_success` | Codex fallback met current contract/validation | Advance; future Claude implementation starts fresh |
| `awaiting_codex_review` | Claude completed implementation/review | Codex independently validates and accepts/corrects |
| `correction_pending` | Bounded Claude correction required | Resume same Claude session; no other writer |
| `usage_limit_exhausted` + implementation mode | Claude subscription/session limit | Safely take over or wait and later `claude-resume` |
| `usage_limit_exhausted` + `codex_review` mode | Claude limit during Codex-work review | Wait; Codex fallback is forbidden |
| `codex_fallback_active` | Codex owns implementation | Claude frozen; Codex finishes or unchanged-worktree aborts |
| `codex_fallback_waiting_for_claude_review` | Codex finished but requested stronger review | Fresh Claude targeted review when available |
| `worker_timeout` / `worker_interrupted` | Claude invocation ended early with no cross-agent edits | Resume same Claude session |
| `worker_failure` | Non-usage Claude/CLI failure unless reconciled as limit | Read compact state, then only necessary logs; no blind retry |
| `auth_required` | Genuine local Claude logout | Authenticate local CLI; no worker ran |
| `auth_check_unavailable` | Codex sandbox cannot inspect macOS Keychain OAuth | Re-run supervisor command outside seatbelt; do not infer logout |
| `worker_running` | Claude child active | Let blocking runner finish; no second writer/model polling |

If `HANDOFF.md` changes while unfinished state exists, the runner refuses to proceed. A completed accepted task advances only after Codex deliberately writes the next handoff.

## Setup validation

After installing/changing this workflow, run:

```sh
bash -n tools/run-juggle-builder.sh
bash -n tools/get-juggle-supervisor-state.sh
tools/run-juggle-builder.sh self-test-auth
tools/run-juggle-builder.sh dry-run
tools/get-juggle-supervisor-state.sh
git diff --check
git status --short --branch
```

The dry run checks required files, CLI flags, ignored state, handoff hash, emergency timeout configuration, and Claude authentication without invoking a worker. Claude Pro OAuth is intentionally used without `ANTHROPIC_API_KEY`. On macOS, Codex must invoke Claude outside its seatbelt sandbox when Keychain access is required.
