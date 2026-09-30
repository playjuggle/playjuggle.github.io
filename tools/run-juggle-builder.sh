#!/bin/bash

# Run or resume exactly one bounded Claude Code implementation turn for Juggle.
# Codex remains responsible for reviewing the resulting diff and evidence.

set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_DIR="$REPO_DIR/.juggle-supervisor"
STATE_FILE="$STATE_DIR/state.json"
LOCK_DIR="$STATE_DIR/run.lock"
HANDOFF_FILE="$REPO_DIR/HANDOFF.md"
CONTRACT_FILE="$REPO_DIR/juggle-autonomy/SHARED_IMPLEMENTATION_CONTRACT.md"
DECISIONS_FILE="$REPO_DIR/juggle-autonomy/ARCHITECTURE_DECISIONS.md"
MAX_ATTEMPTS=0  # 0 = no hard attempt cap; every supervisor command still invokes at most one Claude turn.
DEFAULT_TIMEOUT_SECONDS=5400  # Emergency wall-clock failsafe, not a progress/stall detector.

usage() {
  cat <<'EOF'
Usage:
  tools/run-juggle-builder.sh continue
  tools/run-juggle-builder.sh claude-resume
  tools/run-juggle-builder.sh review accept <pass|expected-failure> [review-note-file]
  tools/run-juggle-builder.sh review correction <correction-file>
  tools/run-juggle-builder.sh fallback start <takeover-note-file>
  tools/run-juggle-builder.sh fallback finish <pass|expected-failure> <fallback-report-file> <accept|claude-review>
  tools/run-juggle-builder.sh fallback abort <reason-file>
  tools/run-juggle-builder.sh auth-check
  tools/run-juggle-builder.sh self-test-auth
  tools/run-juggle-builder.sh dry-run

`continue` invokes Claude only when the state machine assigns Claude the next turn.
`claude-resume` explicitly retries a usage-limited Claude session after Codex has determined subscription usage is available again.
Fallback commands never invoke Claude; they transfer or close Codex write ownership.
Every command performs one bounded state-machine action and never loops.
EOF
}

die() {
  echo "juggle supervisor: $*" >&2
  exit 2
}

need_command() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

copy_if_needed() {
  local source="$1"
  local destination="$2"
  local source_path destination_path
  source_path="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve())' "$source")"
  destination_path="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve())' "$destination")"
  if [ "$source_path" != "$destination_path" ]; then
    cp "$source" "$destination" || die "could not copy $source to supervisor state"
  fi
}

handoff_hash() {
  python3 -c 'import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$HANDOFF_FILE"
}

handoff_title() {
  sed -n 's/^# //p' "$HANDOFF_FILE" | head -n 1
}

state_field() {
  python3 - "$STATE_FILE" "$1" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
key = sys.argv[2]
if not path.exists():
    print("")
else:
    value = json.loads(path.read_text(encoding="utf-8")).get(key, "")
    print(value if value is not None else "")
PY
}

write_state() {
  local status="$1"
  local outcome="$2"
  local validation="$3"
  local session_id="$4"
  local attempt="$5"
  local exit_code="$6"
  local note="$7"
  local task_hash="$8"
  local task_title_value="$9"

  mkdir -p "$STATE_DIR"
  python3 - "$STATE_FILE" "$status" "$outcome" "$validation" "$session_id" \
    "$attempt" "$MAX_ATTEMPTS" "$exit_code" "$note" "$task_hash" \
    "$task_title_value" <<'PY'
import datetime
import json
import os
import pathlib
import sys
import tempfile

(
    path_text, status, outcome, validation, session_id, attempt,
    max_attempts, exit_code, note, task_hash, task_title
) = sys.argv[1:]
path = pathlib.Path(path_text)
previous = {}
if path.exists():
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        previous = {}

owner = "none"
if status == "worker_running":
    owner = "claude"
elif status == "codex_fallback_active":
    owner = "codex"

data = {
    "version": 2,
    "status": status,
    "outcome": outcome or None,
    "validation_outcome": validation or None,
    "task_title": task_title,
    "handoff_sha256": task_hash,
    "claude_session_id": session_id or None,
    "attempt": int(attempt or 0),
    "max_attempts": int(max_attempts),
    "last_exit_code": int(exit_code) if exit_code else None,
    "note": note or None,
    "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "claude_report": "claude-report.md",
    "implementation_owner": owner,
}
for key in (
    "last_implementation_owner",
    "claude_session_reusable",
    "claude_task_mode",
    "takeover_base_fingerprint",
    "fallback_result_fingerprint",
    "fallback_disposition",
    "usage_reset_hint",
    "superseded_claude_session_id",
    "last_claude_usage_attempt",
    "last_claude_num_turns",
    "last_claude_model_input_tokens",
    "last_claude_cache_creation_tokens",
    "last_claude_cache_read_tokens",
    "last_claude_model_output_tokens",
    "last_claude_thinking_tokens",
    "last_claude_permission_denials",
    "last_claude_duration_ms",
):
    if key in previous:
        data[key] = previous[key]
fd, temp_name = tempfile.mkstemp(prefix="state.", suffix=".json", dir=path.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temp_name, path)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)
PY
}

classify_auth_status() {
  local auth_json="$1"
  local auth_exit="$2"
  local sandboxed="$3"
  python3 - "$auth_json" "$auth_exit" "$sandboxed" <<'PY'
import json
import sys

payload_text, exit_code, sandboxed = sys.argv[1:]
try:
    payload = json.loads(payload_text)
except (json.JSONDecodeError, TypeError):
    print("unknown")
    raise SystemExit

logged_in = payload.get("loggedIn")
if logged_in is True:
    print("ready")
elif logged_in is False and sandboxed == "yes":
    # Claude Code stores subscription OAuth in the macOS Keychain. A Codex
    # seatbelt process cannot see that credential and Claude 2.1.270 reports
    # the resulting Keychain denial as a normal loggedIn:false response.
    print("unavailable")
elif logged_in is False and exit_code == "1":
    print("not_logged_in")
else:
    print("unknown")
PY
}

auth_status() {
  local auth_json auth_exit sandboxed
  auth_json="$(
    env \
      -u ANTHROPIC_API_KEY \
      -u ANTHROPIC_AUTH_TOKEN \
      -u CLAUDE_CODE_USE_BEDROCK \
      -u CLAUDE_CODE_USE_VERTEX \
      -u CLAUDE_CODE_USE_FOUNDRY \
      claude auth status --json 2>/dev/null
  )"
  auth_exit=$?
  sandboxed="no"
  if [ "${CODEX_SANDBOX:-}" = "seatbelt" ]; then
    sandboxed="yes"
  fi
  classify_auth_status "$auth_json" "$auth_exit" "$sandboxed"
}

self_test_auth_gate() {
  local actual
  actual="$(classify_auth_status '{"loggedIn":true,"authMethod":"claude.ai"}' 0 no)"
  [ "$actual" = "ready" ] || die "auth self-test: logged-in OAuth was not ready"
  actual="$(classify_auth_status '{"loggedIn":false,"authMethod":"none"}' 1 no)"
  [ "$actual" = "not_logged_in" ] || die "auth self-test: host logout was not detected"
  actual="$(classify_auth_status '{"loggedIn":false,"authMethod":"none"}' 1 yes)"
  [ "$actual" = "unavailable" ] || die "auth self-test: sandbox isolation was misclassified"
  actual="$(classify_auth_status 'not-json' 1 no)"
  [ "$actual" = "unknown" ] || die "auth self-test: malformed output was not rejected"
  echo "auth_gate_self_test=pass"
}

acquire_lock() {
  mkdir -p "$STATE_DIR"
  if [ -f "$STATE_DIR/worker.pid" ]; then
    local worker_pid
    worker_pid="$(sed -n '1p' "$STATE_DIR/worker.pid")"
    if [ -n "$worker_pid" ] && kill -0 "$worker_pid" 2>/dev/null; then
      die "a Claude worker is still active (pid $worker_pid)"
    fi
    rm -f "$STATE_DIR/worker.pid"
  fi
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "$$" > "$LOCK_DIR/pid"
    return
  fi

  local lock_pid=""
  if [ -f "$LOCK_DIR/pid" ]; then
    lock_pid="$(sed -n '1p' "$LOCK_DIR/pid")"
  fi
  if [ -n "$lock_pid" ] && kill -0 "$lock_pid" 2>/dev/null; then
    die "another runner is active (pid $lock_pid)"
  fi
  rmdir "$LOCK_DIR" 2>/dev/null || die "stale lock could not be removed: $LOCK_DIR"
  mkdir "$LOCK_DIR" || die "could not acquire runner lock"
  echo "$$" > "$LOCK_DIR/pid"
}

release_lock() {
  if [ -d "$LOCK_DIR" ]; then
    rm -f "$LOCK_DIR/pid"
    rmdir "$LOCK_DIR" 2>/dev/null || true
  fi
}

extract_report() {
  local result_file="$1"
  local report_file="$2"
  python3 - "$result_file" "$report_file" <<'PY'
import json
import pathlib
import sys

source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])
try:
    payload = json.loads(source.read_text(encoding="utf-8"))
except Exception as exc:
    target.write_text(f"Claude result could not be parsed: {exc}\n", encoding="utf-8")
    raise SystemExit(1)

result = payload.get("result")
if isinstance(result, str):
    report = result
elif result is not None:
    report = json.dumps(result, indent=2, sort_keys=True)
elif payload.get("structured_output") is not None:
    report = json.dumps(payload["structured_output"], indent=2, sort_keys=True)
else:
    report = json.dumps(payload, indent=2, sort_keys=True)
target.write_text(report.rstrip() + "\n", encoding="utf-8")
if payload.get("is_error"):
    raise SystemExit(10)
PY
}

classify_usage_limit() {
  local result_file="$1"
  local stderr_file="$2"
  python3 - "$result_file" "$stderr_file" <<'PY'
import pathlib
import re
import sys

text = "\n".join(
    pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    if pathlib.Path(path).exists() else ""
    for path in sys.argv[1:]
).lower()
patterns = (
    r"usage limit", r"session limit", r"rate limit",
    r"limit (?:has been )?reached", r"you(?:'|’)ve hit your .*limit",
    r"out of usage", r"quota exceeded", r"credit balance",
    r"resets at", r"resets in", r"\bresets \d{1,2}:\d{2}(?:am|pm)\b",
)
raise SystemExit(0 if any(re.search(pattern, text) for pattern in patterns) else 1)
PY
}


patch_state_fields() {
  [ -f "$STATE_FILE" ] || die "no supervisor state exists to patch"
  python3 - "$STATE_FILE" "$@" <<'PY'
import json
import os
import pathlib
import sys
import tempfile

path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
for item in sys.argv[2:]:
    if "=" not in item:
        raise SystemExit(f"invalid state patch: {item}")
    key, value = item.split("=", 1)
    if value == "__NULL__":
        data[key] = None
    else:
        data[key] = value
fd, temp_name = tempfile.mkstemp(prefix="state.", suffix=".json", dir=path.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temp_name, path)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)
PY
}

record_usage_summary() {
  local result_file="$1"
  local attempt_value="$2"
  [ -f "$STATE_FILE" ] || return 0
  [ -f "$result_file" ] || return 0
  python3 - "$STATE_FILE" "$result_file" "$attempt_value" <<'PY'
import json
import os
import pathlib
import sys
import tempfile

state_path = pathlib.Path(sys.argv[1])
result_path = pathlib.Path(sys.argv[2])
attempt = int(sys.argv[3] or 0)
try:
    payload = json.loads(result_path.read_text(encoding="utf-8", errors="replace"))
except Exception:
    raise SystemExit(0)
if not isinstance(payload, dict):
    raise SystemExit(0)

model_usage = payload.get("modelUsage") or {}
totals = {"input": 0, "cache_create": 0, "cache_read": 0, "output": 0, "thinking": 0}
if isinstance(model_usage, dict):
    for usage in model_usage.values():
        if not isinstance(usage, dict):
            continue
        totals["input"] += int(usage.get("inputTokens") or 0)
        totals["cache_create"] += int(usage.get("cacheCreationInputTokens") or 0)
        totals["cache_read"] += int(usage.get("cacheReadInputTokens") or 0)
        totals["output"] += int(usage.get("outputTokens") or 0)
        totals["thinking"] += int(usage.get("thinkingTokens") or 0)

# Some CLI/error responses do not populate modelUsage. Fall back to top-level
# usage so compact telemetry remains useful without opening the full JSON.
if not any(totals.values()):
    usage = payload.get("usage") or {}
    if isinstance(usage, dict):
        totals["input"] = int(usage.get("input_tokens") or 0)
        totals["cache_create"] = int(usage.get("cache_creation_input_tokens") or 0)
        totals["cache_read"] = int(usage.get("cache_read_input_tokens") or 0)
        totals["output"] = int(usage.get("output_tokens") or 0)
        details = usage.get("output_tokens_details") or {}
        if isinstance(details, dict):
            totals["thinking"] = int(details.get("thinking_tokens") or 0)

try:
    state = json.loads(state_path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(0)
state["last_claude_usage_attempt"] = attempt
state["last_claude_num_turns"] = int(payload.get("num_turns") or 0)
state["last_claude_model_input_tokens"] = totals["input"]
state["last_claude_cache_creation_tokens"] = totals["cache_create"]
state["last_claude_cache_read_tokens"] = totals["cache_read"]
state["last_claude_model_output_tokens"] = totals["output"]
state["last_claude_thinking_tokens"] = totals["thinking"]
denials = payload.get("permission_denials") or []
state["last_claude_permission_denials"] = len(denials) if isinstance(denials, list) else 0
state["last_claude_duration_ms"] = int(payload.get("duration_ms") or 0)

fd, temp_name = tempfile.mkstemp(prefix="state.", suffix=".json", dir=state_path.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temp_name, state_path)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)
PY
}

worktree_fingerprint() {
  python3 - "$REPO_DIR" <<'PY'
import hashlib
import os
import pathlib
import subprocess
import sys

repo = pathlib.Path(sys.argv[1])
h = hashlib.sha256()

def run(*args):
    return subprocess.check_output(["git", "-C", str(repo), *args])

status = run("status", "--porcelain=v1", "-z", "--untracked-files=all")
h.update(b"STATUS\0")
h.update(status)
paths = set()
for command in (
    ("ls-files", "-m", "-d", "-o", "--exclude-standard", "-z"),
    ("diff", "--cached", "--name-only", "-z"),
):
    raw = run(*command)
    paths.update(p.decode("utf-8", "surrogateescape") for p in raw.split(b"\0") if p)
for rel in sorted(paths):
    if rel.startswith(".juggle-supervisor/"):
        continue
    h.update(b"PATH\0" + rel.encode("utf-8", "surrogateescape") + b"\0")
    path = repo / rel
    if path.is_symlink():
        h.update(b"SYMLINK\0" + os.readlink(path).encode("utf-8", "surrogateescape"))
    elif path.is_file():
        h.update(b"FILE\0" + path.read_bytes())
    elif not path.exists():
        h.update(b"MISSING\0")
    else:
        h.update(b"OTHER\0")
h.update(b"INDEX\0")
h.update(run("diff", "--cached", "--binary"))
print(h.hexdigest())
PY
}

save_worktree_snapshot() {
  local prefix="$1"
  mkdir -p "$STATE_DIR"
  git -C "$REPO_DIR" status --short --branch > "$STATE_DIR/${prefix}-git-status.txt"
  git -C "$REPO_DIR" diff --binary > "$STATE_DIR/${prefix}-worktree.patch"
  git -C "$REPO_DIR" diff --cached --binary > "$STATE_DIR/${prefix}-index.patch"
  worktree_fingerprint > "$STATE_DIR/${prefix}-fingerprint.txt"
}

validate_takeover_note() {
  local note_file="$1"
  [ -f "$note_file" ] || die "takeover note file not found: $note_file"
  grep -Eq '^Fallback safety:[[:space:]]*SAFE[[:space:]]*$' "$note_file" || \
    die "takeover note must contain: Fallback safety: SAFE"
  grep -Eq '^New material architecture decision required:[[:space:]]*no[[:space:]]*$' "$note_file" || \
    die "Codex fallback is forbidden when a new material architecture decision is required"
  grep -Eq '^Continuity basis:[[:space:]]*(existing accepted approach|handoff-specified approach|mechanically unambiguous local continuation)[[:space:]]*$' "$note_file" || \
    die "takeover note must state an allowed Continuity basis"
}

validate_fallback_report() {
  local report_file="$1"
  [ -f "$report_file" ] || die "fallback report file not found: $report_file"
  grep -Eq '^Implementation worker:[[:space:]]*Codex fallback[[:space:]]*$' "$report_file" || \
    die "fallback report must contain: Implementation worker: Codex fallback"
  grep -Eq '^Material architecture decisions introduced:[[:space:]]*none[[:space:]]*$' "$report_file" || \
    die "fallback report must confirm no new material architecture decision was introduced"
  grep -Eq '^Approach continuity:' "$report_file" || \
    die "fallback report must include an Approach continuity line"
  grep -Eq '^Validation:' "$report_file" || \
    die "fallback report must include a Validation line"
}

extract_usage_reset_hint() {
  local result_file="$1"
  python3 - "$result_file" <<'PY'
import json
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
if not path.exists():
    print("")
    raise SystemExit
try:
    payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    text = str(payload.get("result", ""))
except Exception:
    text = path.read_text(encoding="utf-8", errors="replace")
match = re.search(r"resets?\s+([^\n]+)", text, re.I)
print(match.group(1).strip() if match else "")
PY
}

run_with_timeout() {
  local timeout_seconds="$1"
  local stdout_file="$2"
  local stderr_file="$3"
  local pid_file="$4"
  shift 4

  python3 - "$timeout_seconds" "$stdout_file" "$stderr_file" "$pid_file" "$@" <<'PY'
import os
import pathlib
import signal
import subprocess
import sys

timeout = int(sys.argv[1])
stdout_path = pathlib.Path(sys.argv[2])
stderr_path = pathlib.Path(sys.argv[3])
pid_path = pathlib.Path(sys.argv[4])
command = sys.argv[5:]
process = None

def handle_signal(_signum, _frame):
    raise KeyboardInterrupt

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def stop_process():
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=10)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
    try:
        process = subprocess.Popen(
            command,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        pid_path.write_text(f"{process.pid}\n", encoding="utf-8")
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            stop_process()
            code = 124
    except KeyboardInterrupt:
        stop_process()
        code = 130
try:
    pid_path.unlink()
except FileNotFoundError:
    pass
raise SystemExit(code)
PY
}

dry_run() {
  need_command git
  need_command python3
  need_command claude
  need_command codex
  need_command uuidgen
  [ -f "$HANDOFF_FILE" ] || die "HANDOFF.md is missing"
  [ -f "$REPO_DIR/AGENTS.md" ] || die "AGENTS.md is missing"
  [ -f "$REPO_DIR/CURRENT_STATE.md" ] || die "CURRENT_STATE.md is missing"
  [ -f "$REPO_DIR/CLAUDE.md" ] || die "CLAUDE.md is missing"
  [ -f "$CONTRACT_FILE" ] || die "shared implementation contract is missing"
  [ -f "$DECISIONS_FILE" ] || die "architecture decision log is missing"
  [ -f "$REPO_DIR/juggle-autonomy/PRODUCT_DIRECTION.md" ] || die "durable product direction is missing"
  [ -f "$REPO_DIR/juggle-autonomy/WORKING_BACKLOG.md" ] || die "working backlog is missing"

  bash -n "$SCRIPT_DIR/run-juggle-builder.sh" || die "runner syntax check failed"
  bash -n "$SCRIPT_DIR/get-juggle-supervisor-state.sh" || die "state-reader syntax check failed"

  local ignored="no"
  if git -C "$REPO_DIR" check-ignore -q .juggle-supervisor/probe; then
    ignored="yes"
  fi
  [ "$ignored" = "yes" ] || die ".juggle-supervisor/ is not ignored"

  local claude_help required_flag
  claude_help="$(claude --help 2>&1)"
  for required_flag in \
    --resume --session-id --print --output-format --permission-mode \
    --permission-prompts --setting-sources --disallowedTools --no-chrome; do
    case "$claude_help" in
      *"$required_flag"*) ;;
      *) die "installed Claude CLI does not support required flag: $required_flag" ;;
    esac
  done

  local timeout_seconds="${JUGGLE_CLAUDE_TIMEOUT_SECONDS:-$DEFAULT_TIMEOUT_SECONDS}"
  case "$timeout_seconds" in
    ''|*[!0-9]*) die "JUGGLE_CLAUDE_TIMEOUT_SECONDS must be an integer" ;;
  esac
  [ "$timeout_seconds" -ge 300 ] && [ "$timeout_seconds" -le 21600 ] || \
    die "timeout must be between 300 and 21600 seconds"

  echo "dry_run=pass"
  echo "codex_version=$(codex --version 2>/dev/null | tail -n 1)"
  echo "claude_version=$(claude --version 2>/dev/null)"
  echo "claude_auth=$(auth_status)"
  echo "runtime_state_ignored=$ignored"
  echo "task=$(handoff_title)"
  echo "handoff_sha256=$(handoff_hash)"
  echo "timeout_seconds=$timeout_seconds"
  echo "attempt_cap=none (one invocation per supervisor command)"
  echo "claude_worker_invoked=no"
}

record_review() {
  [ -f "$STATE_FILE" ] || die "no supervisor result exists to review"
  acquire_lock
  trap release_lock EXIT
  local current_status
  current_status="$(state_field status)"
  [ "$current_status" = "awaiting_codex_review" ] || \
    die "review is only valid from awaiting_codex_review (current: $current_status)"

  local action="${1:-}"
  local session_id attempt task_hash task_title_value task_mode
  session_id="$(state_field claude_session_id)"
  attempt="$(state_field attempt)"
  task_hash="$(state_field handoff_sha256)"
  task_title_value="$(state_field task_title)"
  task_mode="$(state_field claude_task_mode)"
  [ -n "$task_mode" ] || task_mode="implementation"
  [ "$task_hash" = "$(handoff_hash)" ] || \
    die "HANDOFF.md changed after the worker ran; Codex must reconcile it before review"

  case "$action" in
    accept)
      local validation="${2:-}"
      local note_file="${3:-}"
      case "$validation" in
        pass) validation="pass" ;;
        expected-failure) validation="expected_failure" ;;
        *) die "accept requires validation classification: pass or expected-failure" ;;
      esac
      local note="Codex independently accepted the implementation."
      if [ -n "$note_file" ]; then
        [ -f "$note_file" ] || die "review note file not found: $note_file"
        copy_if_needed "$note_file" "$STATE_DIR/codex-review.md"
        note="Codex review saved in codex-review.md."
      fi
      write_state "accepted" "implementation_success" "$validation" "$session_id" \
        "$attempt" "0" "$note" "$task_hash" "$task_title_value"
      if [ "$task_mode" = "codex_review" ]; then
        patch_state_fields "last_implementation_owner=claude" "claude_session_reusable=no" "fallback_disposition=accepted_after_claude_review"
      else
        patch_state_fields "last_implementation_owner=claude" "claude_session_reusable=no"
      fi
      echo "review=accepted"
      echo "validation=$validation"
      ;;
    correction)
      local correction_file="${2:-}"
      [ -n "$correction_file" ] || die "correction requires a bounded correction file"
      [ -f "$correction_file" ] || die "correction file not found: $correction_file"
      copy_if_needed "$correction_file" "$STATE_DIR/CODEX_CORRECTION.md"
      write_state "correction_pending" "genuine_implementation_failure" "actual_failure" \
        "$session_id" "$attempt" "1" "Bounded correction saved in CODEX_CORRECTION.md." \
        "$task_hash" "$task_title_value"
      patch_state_fields "claude_session_reusable=yes" "claude_task_mode=$task_mode"
      echo "review=correction_pending"
      echo "next=tools/run-juggle-builder.sh continue"
      ;;
    *)
      die "review action must be accept or correction"
      ;;
  esac
}

refresh_auth_state() {
  need_command python3
  need_command claude
  [ -f "$HANDOFF_FILE" ] || die "HANDOFF.md is missing"

  acquire_lock
  trap release_lock EXIT

  local current_hash current_title status session_id attempt result
  current_hash="$(handoff_hash)"
  current_title="$(handoff_title)"
  status=""
  session_id=""
  attempt=0
  if [ -f "$STATE_FILE" ]; then
    status="$(state_field status)"
    session_id="$(state_field claude_session_id)"
    attempt="$(state_field attempt)"
  fi

  result="$(auth_status)"
  case "$result" in
    ready)
      if [ "$status" = "auth_required" ] || [ "$status" = "auth_check_unavailable" ]; then
        write_state "ready" "not_started" "not_run" "$session_id" "$attempt" "0" \
          "Claude Pro subscription OAuth verified; no worker was invoked." \
          "$current_hash" "$current_title"
      fi
      echo "status=ready"
      echo "claude_auth=ready"
      echo "claude_worker_invoked=no"
      ;;
    not_logged_in)
      write_state "auth_required" "authentication_required" "not_run" \
        "$session_id" "$attempt" "1" \
        "Claude CLI explicitly reported loggedIn:false outside a known sandbox." \
        "$current_hash" "$current_title"
      echo "status=auth_required"
      echo "claude_auth=not_logged_in"
      ;;
    unavailable)
      write_state "auth_check_unavailable" "authentication_check_unavailable" "not_run" \
        "$session_id" "$attempt" "1" \
        "Claude OAuth status is unavailable inside the Codex seatbelt because it cannot read the macOS Keychain; rerun the supervisor outside that sandbox." \
        "$current_hash" "$current_title"
      echo "status=auth_check_unavailable"
      echo "claude_auth=unavailable"
      ;;
    *)
      die "Claude authentication status returned an unrecognized result"
      ;;
  esac
}

fallback_control() {
  [ -f "$STATE_FILE" ] || die "no supervisor state exists"
  [ -f "$HANDOFF_FILE" ] || die "HANDOFF.md is missing"
  need_command git
  need_command python3

  local action="${1:-}"
  shift || true

  acquire_lock
  trap release_lock EXIT

  local status saved_hash current_hash session_id attempt task_title_value task_mode
  status="$(state_field status)"
  saved_hash="$(state_field handoff_sha256)"
  current_hash="$(handoff_hash)"
  session_id="$(state_field claude_session_id)"
  attempt="$(state_field attempt)"
  task_title_value="$(state_field task_title)"
  task_mode="$(state_field claude_task_mode)"

  [ "$saved_hash" = "$current_hash" ] || \
    die "HANDOFF.md changed; reconcile the active task before changing ownership"

  case "$action" in
    start)
      local takeover_file="${1:-}"
      [ -n "$takeover_file" ] || die "fallback start requires a takeover note file"
      [ "$#" -eq 1 ] || die "fallback start takes exactly one takeover note file"
      [ "$status" = "usage_limit_exhausted" ] || \
        die "Codex fallback may start only from usage_limit_exhausted (current: $status)"
      [ "$task_mode" != "codex_review" ] || \
        die "Codex may not take over a Claude review of Codex fallback work"
      validate_takeover_note "$takeover_file"

      local policy
      policy="$(sed -n 's/^\*\*Codex fallback:\*\*[[:space:]]*//p' "$HANDOFF_FILE" | head -n 1 | tr '[:upper:]' '[:lower:]')"
      case "$policy" in
        disallowed*) die "HANDOFF.md explicitly disallows Codex fallback" ;;
        allowed*) ;;
        "") echo "warning=legacy handoff has no explicit Codex fallback field; guarded takeover note controls this transition" ;;
        *) die "unrecognized Codex fallback policy in HANDOFF.md: $policy" ;;
      esac

      save_worktree_snapshot "takeover"
      copy_if_needed "$takeover_file" "$STATE_DIR/CODEX_TAKEOVER.md"
      local base_fingerprint
      base_fingerprint="$(cat "$STATE_DIR/takeover-fingerprint.txt")"
      write_state "codex_fallback_active" "codex_fallback_in_progress" "not_run" \
        "$session_id" "$attempt" "0" \
        "Codex owns implementation under the guarded fallback contract; Claude is frozen." \
        "$current_hash" "$task_title_value"
      patch_state_fields \
        "takeover_base_fingerprint=$base_fingerprint" \
        "claude_session_reusable=no" \
        "claude_task_mode=implementation" \
        "fallback_disposition=in_progress"
      echo "status=codex_fallback_active"
      echo "implementation_owner=codex"
      echo "takeover=.juggle-supervisor/CODEX_TAKEOVER.md"
      echo "next=Codex implements only the active handoff, then runs fallback finish"
      ;;

    finish)
      local validation_arg="${1:-}"
      local report_file="${2:-}"
      local disposition="${3:-}"
      [ "$#" -eq 3 ] || \
        die "fallback finish requires <pass|expected-failure> <fallback-report-file> <accept|claude-review>"
      [ "$status" = "codex_fallback_active" ] || \
        die "fallback finish is only valid from codex_fallback_active (current: $status)"
      validate_fallback_report "$report_file"

      local validation
      case "$validation_arg" in
        pass) validation="pass" ;;
        expected-failure) validation="expected_failure" ;;
        *) die "fallback finish requires validation classification: pass or expected-failure" ;;
      esac
      case "$disposition" in
        accept|claude-review) ;;
        *) die "fallback disposition must be accept or claude-review" ;;
      esac

      save_worktree_snapshot "fallback-result"
      copy_if_needed "$report_file" "$STATE_DIR/codex-fallback-report.md"
      local result_fingerprint old_session
      result_fingerprint="$(cat "$STATE_DIR/fallback-result-fingerprint.txt")"
      old_session="$session_id"

      if [ "$disposition" = "accept" ]; then
        write_state "accepted" "codex_fallback_success" "$validation" "$session_id" \
          "$attempt" "0" \
          "Codex fallback satisfied the handoff and validation under existing architecture constraints." \
          "$current_hash" "$task_title_value"
        patch_state_fields \
          "last_implementation_owner=codex" \
          "claude_session_reusable=no" \
          "fallback_result_fingerprint=$result_fingerprint" \
          "fallback_disposition=accepted"
        echo "status=accepted"
        echo "outcome=codex_fallback_success"
        echo "implementation_owner=none"
        echo "next=Codex may advance to the next authorized handoff; any future Claude implementation starts fresh"
      else
        write_state "codex_fallback_waiting_for_claude_review" \
          "codex_fallback_completed_pending_claude_review" "$validation" "" "0" "0" \
          "Codex fallback completed, but targeted fresh-session Claude review is required before acceptance." \
          "$current_hash" "$task_title_value"
        patch_state_fields \
          "last_implementation_owner=codex" \
          "claude_session_reusable=no" \
          "claude_task_mode=codex_review" \
          "fallback_result_fingerprint=$result_fingerprint" \
          "fallback_disposition=claude_review" \
          "superseded_claude_session_id=$old_session"
        echo "status=codex_fallback_waiting_for_claude_review"
        echo "implementation_owner=none"
        echo "next=when Claude usage is available, tools/run-juggle-builder.sh continue starts a fresh targeted review session"
      fi
      ;;

    abort)
      local reason_file="${1:-}"
      [ -n "$reason_file" ] || die "fallback abort requires a reason file"
      [ "$#" -eq 1 ] || die "fallback abort takes exactly one reason file"
      [ -f "$reason_file" ] || die "fallback abort reason file not found: $reason_file"
      [ "$status" = "codex_fallback_active" ] || \
        die "fallback abort is only valid from codex_fallback_active (current: $status)"
      local base current
      base="$(state_field takeover_base_fingerprint)"
      current="$(worktree_fingerprint)"
      [ -n "$base" ] || die "takeover baseline fingerprint is missing"
      [ "$base" = "$current" ] || \
        die "Codex changed the worktree after takeover; abort is unsafe. Finish/review the fallback or reconcile explicitly."
      copy_if_needed "$reason_file" "$STATE_DIR/codex-fallback-abort.md"
      write_state "usage_limit_exhausted" "usage_limit_exhaustion" "not_run" \
        "$session_id" "$attempt" "0" \
        "Codex fallback was aborted before any worktree change; the Claude session remains resumable after usage resets." \
        "$current_hash" "$task_title_value"
      patch_state_fields \
        "claude_session_reusable=yes" \
        "claude_task_mode=implementation" \
        "fallback_disposition=aborted"
      echo "status=usage_limit_exhausted"
      echo "implementation_owner=none"
      echo "next=wait for Claude usage or prepare a new safe takeover"
      ;;

    *)
      die "fallback action must be start, finish, or abort"
      ;;
  esac
}

claude_resume_after_usage() {
  JUGGLE_RESUME_USAGE=1 continue_task
}

continue_task() {
  need_command git
  need_command python3
  need_command claude
  need_command uuidgen
  [ -f "$HANDOFF_FILE" ] || die "HANDOFF.md is missing"

  acquire_lock
  trap release_lock EXIT

  local current_hash current_title status saved_hash session_id attempt resume_reason auth_result task_mode claude_mode fresh_session reset_hint
  current_hash="$(handoff_hash)"
  current_title="$(handoff_title)"
  status=""
  saved_hash=""
  session_id=""
  attempt=0
  resume_reason=""
  task_mode="implementation"
  claude_mode="implementation"
  fresh_session="no"

  if [ -f "$STATE_FILE" ]; then
    status="$(state_field status)"
    saved_hash="$(state_field handoff_sha256)"
    session_id="$(state_field claude_session_id)"
    attempt="$(state_field attempt)"
    task_mode="$(state_field claude_task_mode)"
    [ -n "$task_mode" ] || task_mode="implementation"
  fi

  if [ -n "$saved_hash" ] && [ "$saved_hash" != "$current_hash" ]; then
    case "$status" in
      accepted)
        status=""
        session_id=""
        attempt=0
        task_mode="implementation"
        fresh_session="yes"
        ;;
      *)
        die "HANDOFF.md changed while task state is $status; Codex must reconcile it"
        ;;
    esac
  fi

  case "$status" in
    awaiting_codex_review)
      echo "status=awaiting_codex_review"
      echo "next=Codex must inspect the diff, report, and validation evidence"
      return 0
      ;;
    accepted)
      echo "status=accepted"
      echo "next=Codex must create a new HANDOFF.md before another worker run"
      return 0
      ;;
    codex_fallback_active)
      echo "status=codex_fallback_active"
      echo "implementation_owner=codex"
      echo "next=Claude is frozen; Codex must finish or safely abort the fallback"
      return 0
      ;;
    codex_fallback_waiting_for_claude_review)
      resume_reason="review_codex_fresh"
      claude_mode="codex_review"
      session_id=""
      attempt=0
      fresh_session="yes"
      ;;
    auth_required|auth_check_unavailable)
      if [ -n "$session_id" ] && [ "$attempt" -gt 0 ]; then
        if [ "$task_mode" = "codex_review" ]; then
          resume_reason="review_codex_resume"
          claude_mode="codex_review"
        else
          resume_reason="interruption"
          claude_mode="implementation"
        fi
      fi
      ;;
    ready)
      status=""
      if [ -n "$session_id" ] && [ "$attempt" -gt 0 ]; then
        if [ "$task_mode" = "codex_review" ]; then
          resume_reason="review_codex_resume"
          claude_mode="codex_review"
        else
          resume_reason="interruption"
          claude_mode="implementation"
        fi
      fi
      ;;
    usage_limit_exhausted)
      if [ "$task_mode" = "codex_review" ]; then
        if [ "${JUGGLE_RESUME_USAGE:-0}" != "1" ]; then
          echo "status=usage_limit_exhausted"
          echo "mode=codex_review"
          echo "next=wait for Claude usage; Codex may not take over its own pending review"
          return 0
        fi
        resume_reason="review_codex_resume"
        claude_mode="codex_review"
      elif [ "${JUGGLE_RESUME_USAGE:-0}" = "1" ]; then
        resume_reason="usage_limit"
        claude_mode="implementation"
      else
        echo "status=usage_limit_exhausted"
        echo "implementation_owner=none"
        reset_hint="$(state_field usage_reset_hint)"
        [ -z "$reset_hint" ] || echo "usage_reset_hint=$reset_hint"
        echo "next=Codex evaluates guarded fallback; use claude-resume only after usage is known to be available"
        return 0
      fi
      ;;
    worker_failure)
      local failed_result="$STATE_DIR/claude-result-attempt-$attempt.json"
      local failed_stderr="$STATE_DIR/claude-stderr-attempt-$attempt.log"
      if classify_usage_limit "$failed_result" "$failed_stderr"; then
        local reset_hint
        reset_hint="$(extract_usage_reset_hint "$failed_result")"
        write_state "usage_limit_exhausted" "usage_limit_exhaustion" "not_run" \
          "$session_id" "$attempt" "$(state_field last_exit_code)" \
          "Previously misclassified Claude session/usage limit was reconciled; no worker was invoked." \
          "$current_hash" "$current_title"
        patch_state_fields "claude_session_reusable=yes" "claude_task_mode=$task_mode" "usage_reset_hint=$reset_hint"
        echo "status=usage_limit_exhausted"
        echo "reconciled_from=worker_failure"
        [ -z "$reset_hint" ] || echo "usage_reset_hint=$reset_hint"
        echo "next=Codex evaluates guarded fallback; use claude-resume only after usage is known to be available"
      else
        echo "status=$status"
        echo "next=stop; Codex must inspect the saved logs and resolve the execution failure"
      fi
      return 0
      ;;
    correction_pending)
      resume_reason="correction"
      claude_mode="$task_mode"
      ;;
    worker_timeout|worker_interrupted)
      resume_reason="interruption"
      claude_mode="$task_mode"
      ;;
    worker_running)
      resume_reason="interruption"
      claude_mode="$task_mode"
      ;;
    "")
      claude_mode="implementation"
      ;;
    *)
      die "unknown state: $status"
      ;;
  esac

  auth_result="$(auth_status)"
  case "$auth_result" in
    ready)
      ;;
    not_logged_in)
      write_state "auth_required" "authentication_required" "not_run" \
        "$session_id" "$attempt" "1" \
        "Claude CLI explicitly reported loggedIn:false outside a known sandbox. No worker was invoked." \
        "$current_hash" "$current_title"
      echo "status=auth_required"
      echo "next=authenticate the local Claude CLI, then continue"
      return 0
      ;;
    unavailable)
      write_state "auth_check_unavailable" "authentication_check_unavailable" "not_run" \
        "$session_id" "$attempt" "1" \
        "Claude OAuth status is unavailable inside the Codex seatbelt because it cannot read the macOS Keychain. No worker was invoked." \
        "$current_hash" "$current_title"
      echo "status=auth_check_unavailable"
      echo "next=rerun this supervisor command outside the Codex seatbelt"
      return 0
      ;;
    *)
      die "Claude authentication status returned an unrecognized result; no worker was invoked"
      ;;
  esac

  attempt=$((attempt + 1))
  if [ -z "$session_id" ]; then
    session_id="$(uuidgen | tr '[:upper:]' '[:lower:]')"
  fi

  local prompt
  if [ "$resume_reason" = "correction" ]; then
    prompt="Resume this same Juggle session for Codex's bounded correction. Your prior task context remains authoritative. Read .juggle-supervisor/CODEX_CORRECTION.md, inspect the current diff, and read only files needed to correct the named defect. Do not reread unchanged AGENTS.md, CURRENT_STATE.md, the shared contract, or architecture log unless the correction exposes a genuine conflict. Address only the bounded correction, preserve unrelated work, rerun affected checks plus the required final validation before completion, and finish with the concise CLAUDE.md report. Do not redesign for preference, delegate, commit, push, or deploy."
  elif [ "$resume_reason" = "interruption" ]; then
    prompt="Resume this same Juggle session after interruption. Your prior task context remains authoritative and no other implementation writer has intervened. Inspect the current diff and continue only unfinished HANDOFF work. Do not reread unchanged policy/context documents or repeat completed work. Read additional files only when needed for unfinished implementation or validation. Finish the required validation/report. Do not delegate, commit, push, or deploy."
  elif [ "$resume_reason" = "usage_limit" ]; then
    prompt="Resume this same Juggle session after subscription usage reset. No Codex fallback implementation occurred while paused. Use retained task context, inspect the current diff, and continue only unfinished HANDOFF work. Do not reread unchanged policy/context documents or repeat completed work. Run remaining required validation and finish the concise report. Do not delegate, commit, push, deploy, or use API billing."
  elif [ "$resume_reason" = "review_codex_fresh" ]; then
    prompt="Project instructions are loaded from CLAUDE.md. Perform the targeted fresh-session review of Codex fallback work for the current HANDOFF. Read HANDOFF.md once, .juggle-supervisor/CODEX_TAKEOVER.md, and .juggle-supervisor/codex-fallback-report.md; then inspect the named risk, recorded changed files, and current diff first. Follow CLAUDE.md context discipline for any additional policy/context. Do not redesign or refactor for preference. Correct only a concrete material defect within the HANDOFF; otherwise leave accepted implementation unchanged. Run required validation and report exactly what you reviewed/corrected. Do not delegate, commit, push, or deploy."
  elif [ "$resume_reason" = "review_codex_resume" ]; then
    prompt="Resume the same targeted Codex-fallback review after Claude usage reset. Use retained review context; inspect only unfinished review/correction work and any current diff. Do not reread unchanged policy/history or refactor for preference. Finish required validation/report. Do not delegate, commit, push, deploy, or use API billing."
  else
    prompt="Project builder instructions are loaded from CLAUDE.md. Implement the single active task in HANDOFF.md. Read HANDOFF.md once, then inspect only the source/evidence needed for that task. Do not routinely load AGENTS.md, broad product/history documents, or model memory; the handoff carries binding task constraints. Preserve unrelated work, use focused checks while iterating, and run every required final validation before completion. Finish with the concise required report. Do not choose a different milestone, delegate, commit, push, deploy, or ask the user to relay anything."
  fi

  local timeout_seconds="${JUGGLE_CLAUDE_TIMEOUT_SECONDS:-$DEFAULT_TIMEOUT_SECONDS}"
  case "$timeout_seconds" in
    ''|*[!0-9]*) die "JUGGLE_CLAUDE_TIMEOUT_SECONDS must be an integer" ;;
  esac
  [ "$timeout_seconds" -ge 300 ] && [ "$timeout_seconds" -le 21600 ] || \
    die "timeout must be between 300 and 21600 seconds"

  local result_file="$STATE_DIR/claude-result-attempt-$attempt.json"
  local stderr_file="$STATE_DIR/claude-stderr-attempt-$attempt.log"
  local report_file="$STATE_DIR/claude-report.md"
  local pid_file="$STATE_DIR/worker.pid"
  local -a claude_command

  if [ -n "$resume_reason" ] && [ "$resume_reason" != "review_codex_fresh" ]; then
    claude_command=(
      env
      -u ANTHROPIC_API_KEY
      -u ANTHROPIC_AUTH_TOKEN
      -u CLAUDE_CODE_USE_BEDROCK
      -u CLAUDE_CODE_USE_VERTEX
      -u CLAUDE_CODE_USE_FOUNDRY
      CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
      claude --resume "$session_id" -p
      --output-format json
      --permission-mode auto
      --permission-prompts none
      --setting-sources project,local
      --disallowedTools "Bash(git commit *),Bash(git push *),Bash(git reset *),Bash(git checkout *)"
      --no-chrome
      "$prompt"
    )
  else
    claude_command=(
      env
      -u ANTHROPIC_API_KEY
      -u ANTHROPIC_AUTH_TOKEN
      -u CLAUDE_CODE_USE_BEDROCK
      -u CLAUDE_CODE_USE_VERTEX
      -u CLAUDE_CODE_USE_FOUNDRY
      CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
      claude --session-id "$session_id" -p
      --output-format json
      --permission-mode auto
      --permission-prompts none
      --setting-sources project,local
      --disallowedTools "Bash(git commit *),Bash(git push *),Bash(git reset *),Bash(git checkout *)"
      --no-chrome
      "$prompt"
    )
  fi

  write_state "worker_running" "" "not_run" "$session_id" "$attempt" "" \
    "Claude invocation is in progress." "$current_hash" "$current_title"
  patch_state_fields "claude_task_mode=$claude_mode" "claude_session_reusable=yes"
  echo "status=worker_running"
  echo "attempt=$attempt"
  echo "session_id=$session_id"

  local exit_code=0
  (
    cd "$REPO_DIR" || exit 2
    run_with_timeout "$timeout_seconds" "$result_file" "$stderr_file" "$pid_file" \
      "${claude_command[@]}"
  ) || exit_code=$?

  case "$exit_code" in
    0)
      local report_exit=0
      extract_report "$result_file" "$report_file" || report_exit=$?
      if [ "$report_exit" -eq 0 ]; then
        write_state "awaiting_codex_review" "worker_completed_unreviewed" "unreviewed" \
          "$session_id" "$attempt" "$exit_code" \
          "Claude completed; Codex review is required." "$current_hash" "$current_title"
        echo "status=awaiting_codex_review"
        echo "report=.juggle-supervisor/claude-report.md"
      elif classify_usage_limit "$result_file" "$stderr_file"; then
        write_state "usage_limit_exhausted" "usage_limit_exhaustion" "not_run" \
          "$session_id" "$attempt" "$report_exit" \
          "Claude subscription/session usage is exhausted. Codex may evaluate guarded fallback; no API fallback or blind retry will occur." \
          "$current_hash" "$current_title"
        reset_hint="$(extract_usage_reset_hint "$result_file")"
        patch_state_fields "claude_session_reusable=yes" "claude_task_mode=$claude_mode" "usage_reset_hint=$reset_hint"
        echo "status=usage_limit_exhausted"
        [ -z "$reset_hint" ] || echo "usage_reset_hint=$reset_hint"
        if [ "$claude_mode" = "codex_review" ]; then
          echo "next=wait for Claude usage; Codex may not take over its own targeted review"
        else
          echo "next=Codex evaluates guarded fallback; use claude-resume only after usage is known to be available"
        fi
      else
        write_state "worker_failure" "worker_execution_failure" "unknown" \
          "$session_id" "$attempt" "$report_exit" \
          "Claude returned an error or invalid JSON; inspect the saved result and stderr." \
          "$current_hash" "$current_title"
        echo "status=worker_failure"
      fi
      ;;
    124)
      write_state "worker_timeout" "timeout_or_interruption" "unknown" \
        "$session_id" "$attempt" "$exit_code" \
        "Claude exceeded the bounded timeout; the same session may be resumed once." \
        "$current_hash" "$current_title"
      echo "status=worker_timeout"
      echo "next=ask Codex to continue to resume the same session"
      ;;
    130|143)
      write_state "worker_interrupted" "timeout_or_interruption" "unknown" \
        "$session_id" "$attempt" "$exit_code" \
        "Claude was interrupted; the same session may be resumed." \
        "$current_hash" "$current_title"
      echo "status=worker_interrupted"
      ;;
    *)
      if classify_usage_limit "$result_file" "$stderr_file"; then
        write_state "usage_limit_exhausted" "usage_limit_exhaustion" "not_run" \
          "$session_id" "$attempt" "$exit_code" \
          "Claude subscription/session usage is exhausted. Codex may evaluate guarded fallback; no API fallback or blind retry will occur." \
          "$current_hash" "$current_title"
        reset_hint="$(extract_usage_reset_hint "$result_file")"
        patch_state_fields "claude_session_reusable=yes" "claude_task_mode=$claude_mode" "usage_reset_hint=$reset_hint"
        echo "status=usage_limit_exhausted"
        [ -z "$reset_hint" ] || echo "usage_reset_hint=$reset_hint"
        if [ "$claude_mode" = "codex_review" ]; then
          echo "next=wait for Claude usage; Codex may not take over its own targeted review"
        else
          echo "next=Codex evaluates guarded fallback; use claude-resume only after usage is known to be available"
        fi
      else
        write_state "worker_failure" "worker_execution_failure" "unknown" \
          "$session_id" "$attempt" "$exit_code" \
          "Claude exited unsuccessfully; Codex must inspect the saved stderr/result." \
          "$current_hash" "$current_title"
        echo "status=worker_failure"
      fi
      echo "stderr=.juggle-supervisor/$(basename "$stderr_file")"
      ;;
  esac

  # Keep compact usage/permission telemetry in state so Codex can diagnose
  # expensive rereads or tool churn without opening the full Claude result JSON.
  record_usage_summary "$result_file" "$attempt"
}

cd "$REPO_DIR" || exit 2

case "${1:-}" in
  continue)
    shift
    [ "$#" -eq 0 ] || die "continue takes no arguments"
    continue_task
    ;;
  claude-resume)
    shift
    [ "$#" -eq 0 ] || die "claude-resume takes no arguments"
    claude_resume_after_usage
    ;;
  review)
    shift
    record_review "$@"
    ;;
  fallback)
    shift
    fallback_control "$@"
    ;;
  auth-check)
    shift
    [ "$#" -eq 0 ] || die "auth-check takes no arguments"
    refresh_auth_state
    ;;
  self-test-auth)
    shift
    [ "$#" -eq 0 ] || die "self-test-auth takes no arguments"
    self_test_auth_gate
    ;;
  dry-run|--dry-run)
    shift
    [ "$#" -eq 0 ] || die "dry-run takes no arguments"
    dry_run
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
