#!/bin/bash

# Print only the compact durable state needed for the next Codex supervisor gate.

set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_FILE="$REPO_DIR/.juggle-supervisor/state.json"
HANDOFF_FILE="$REPO_DIR/HANDOFF.md"

cd "$REPO_DIR" || exit 2

if [ ! -f "$STATE_FILE" ]; then
  task="$(sed -n 's/^# //p' "$HANDOFF_FILE" | head -n 1)"
  task_hash="$(python3 -c 'import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$HANDOFF_FILE")"
  echo "status=ready"
  echo "outcome=not_started"
  echo "implementation_owner=none"
  echo "task=$task"
  echo "handoff_sha256=$task_hash"
  echo "attempt=0"
  echo "next=tools/run-juggle-builder.sh continue"
  exit 0
fi

python3 - "$STATE_FILE" <<'PY'
import json
import pathlib
import sys

state = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
for key in (
    "status", "outcome", "validation_outcome", "implementation_owner",
    "last_implementation_owner", "task_title", "handoff_sha256",
    "claude_session_id", "claude_session_reusable", "claude_task_mode",
    "fallback_disposition", "usage_reset_hint",
):
    value = state.get(key)
    if value is not None and value != "":
        print(f"{key}={value}")
print(f"attempt={state.get('attempt', 0)}")
if state.get("last_exit_code") is not None:
    print(f"last_exit_code={state['last_exit_code']}")
usage_fields = (
    "last_claude_usage_attempt", "last_claude_num_turns",
    "last_claude_model_input_tokens", "last_claude_cache_creation_tokens",
    "last_claude_cache_read_tokens", "last_claude_model_output_tokens",
    "last_claude_thinking_tokens", "last_claude_permission_denials",
    "last_claude_duration_ms",
)
if any(state.get(k) is not None for k in usage_fields):
    print(
        "last_claude_usage="
        f"attempt:{state.get('last_claude_usage_attempt', '')},"
        f"turns:{state.get('last_claude_num_turns', 0)},"
        f"input:{state.get('last_claude_model_input_tokens', 0)},"
        f"cache_create:{state.get('last_claude_cache_creation_tokens', 0)},"
        f"cache_read:{state.get('last_claude_cache_read_tokens', 0)},"
        f"output:{state.get('last_claude_model_output_tokens', 0)},"
        f"thinking:{state.get('last_claude_thinking_tokens', 0)},"
        f"permission_denials:{state.get('last_claude_permission_denials', 0)},"
        f"duration_ms:{state.get('last_claude_duration_ms', 0)}"
    )
if state.get("note"):
    print(f"note={state['note']}")
print(f"updated_at={state.get('updated_at', '')}")
PY

status="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["status"])' "$STATE_FILE")"
task_mode="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("claude_task_mode", "implementation"))' "$STATE_FILE")"
case "$status" in
  awaiting_codex_review)
    echo "next=Codex reviews HANDOFF, concise Claude report, relevant diff/status, and required validation; consult broader contract/logs only if needed"
    ;;
  correction_pending|worker_timeout|worker_interrupted)
    echo "next=tools/run-juggle-builder.sh continue"
    ;;
  usage_limit_exhausted)
    if [ "$task_mode" = "codex_review" ]; then
      echo "next=wait for Claude subscription usage; then tools/run-juggle-builder.sh claude-resume resumes the targeted review; Codex fallback is forbidden"
    else
      echo "next=Codex evaluates guarded takeover; if safe use fallback start, otherwise wait; after reset use claude-resume"
    fi
    ;;
  codex_fallback_active)
    echo "next=Codex is the sole implementation writer; finish with fallback finish or abort only if the worktree is unchanged"
    ;;
  codex_fallback_waiting_for_claude_review)
    echo "next=when Claude usage is available, tools/run-juggle-builder.sh continue starts a fresh targeted review session"
    ;;
  auth_required)
    echo "next=authenticate the local Claude CLI, then ask Codex to continue"
    ;;
  auth_check_unavailable)
    echo "next=Codex reruns tools/run-juggle-builder.sh outside the seatbelt sandbox"
    ;;
  ready)
    echo "next=tools/run-juggle-builder.sh continue"
    ;;
  worker_failure)
    echo "next=Codex runs continue once; the runner first reconciles any previously misclassified usage/session limit, otherwise Codex inspects logs"
    ;;
  accepted)
    echo "next=Codex writes the next HANDOFF.md, or stops"
    ;;
  worker_running)
    echo "next=let the blocking runner finish; do not model-poll status and do not start another writer"
    ;;
esac
