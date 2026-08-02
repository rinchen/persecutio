#!/usr/bin/env bash
# Deploy site with nsyte, retrying transient bunker/network failures.
# Required env: NBUNK_SECRET, NSYTE_BIN, SITE_DIR
# Optional: NSYTE_NAME, NSYTE_RELAYS, NSYTE_SERVERS, MAX_ATTEMPTS,
#           RETRY_BUDGET_SECONDS, NBUNK_BUNKER_RELAYS, NBUNK_PUBKEY_PREFIX
set -euo pipefail

NSYTE_BIN="${NSYTE_BIN:?NSYTE_BIN is required}"
SITE_DIR="${SITE_DIR:?SITE_DIR is required}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-12}"
RETRY_BUDGET_SECONDS="${RETRY_BUDGET_SECONDS:-900}"
NSYTE_NAME="${NSYTE_NAME:-persecutio}"
NSYTE_RELAYS="${NSYTE_RELAYS:-wss://relay.nsite.lol,wss://nos.lol,wss://relay.nostr.band,wss://relay.primal.net}"
NSYTE_SERVERS="${NSYTE_SERVERS:-https://cdn.hzrd149.com}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIAGNOSE_PY="${SCRIPT_DIR}/ci_nbunk_diagnose.py"
STARTED_AT="$(date +%s)"

if [[ ! -x "$NSYTE_BIN" ]]; then
  echo "::error::nsyte binary not executable: $NSYTE_BIN"
  exit 2
fi
if [[ ! -d "$SITE_DIR" ]]; then
  echo "::error::SITE_DIR is not a directory: $SITE_DIR"
  exit 2
fi

RAW_SECRET="${NBUNK_SECRET:-}"
NBUNK_SECRET="$(printf '%s' "$RAW_SECRET" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
if [[ -z "$NBUNK_SECRET" ]]; then
  echo "::error::NBUNK_SECRET is missing or empty"
  exit 2
fi
if [[ "$NBUNK_SECRET" == sec1* ]]; then
  echo "::error::NBUNK_SECRET must not be a sec1 private key; use nbunksec1 from 'nsyte ci'"
  exit 2
fi
if [[ "$NBUNK_SECRET" != nbunksec1* ]]; then
  echo "::error::NBUNK_SECRET must start with nbunksec1"
  exit 2
fi

is_retryable() {
  local log="$1"
  grep -Eiq \
    'Bunker connection timeout|Failed to establish session with bunker|Failed to import from nbunksec|ECONNRESET|ETIMEDOUT|ENOTFOUND|socket hang up|temporarily unavailable|connection reset|network is unreachable' \
    "$log"
}

is_permanent() {
  local log="$1"
  # Credential / format errors — never retry.
  if grep -Eiq \
    'must start with .nbunksec1|must not be a sec1|nbunksec1 value instead|Invalid prefix|bech32 checksum|Failed to decode|The .nbunksec. input must' \
    "$log"; then
    return 0
  fi
  # Signer-init boilerplate wraps both permanent and bunker-timeout failures.
  # Only call it permanent when no retryable markers are present.
  if grep -Eiq 'Signer initialization failed|No valid signing method could be initialized' "$log"; then
    if is_retryable "$log"; then
      return 1
    fi
    return 0
  fi
  return 1
}

append_summary() {
  if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    printf '%s\n' "$@" >>"$GITHUB_STEP_SUMMARY"
  fi
}

budget_remaining() {
  local now elapsed
  now="$(date +%s)"
  elapsed=$((now - STARTED_AT))
  if ((elapsed >= RETRY_BUDGET_SECONDS)); then
    echo 0
  else
    echo $((RETRY_BUDGET_SECONDS - elapsed))
  fi
}

backoff_seconds() {
  # After attempt n: min(60 * 2^(n-1), 120)
  local attempt="$1"
  local delay=$((60 * (1 << (attempt - 1))))
  if ((delay > 120)); then
    delay=120
  fi
  echo "$delay"
}

sleep_up_to() {
  local want="$1"
  local left
  left="$(budget_remaining)"
  if ((left <= 0)); then
    return 1
  fi
  if ((want > left)); then
    want=$left
  fi
  if ((want > 0)); then
    sleep "$want"
  fi
  return 0
}

# Probe bunker relays from NBUNK_BUNKER_RELAYS (comma-separated).
# Prints: ok | down | unknown
probe_bunker_relays() {
  local relays="${NBUNK_BUNKER_RELAYS:-}"
  if [[ -z "$relays" ]]; then
    echo "unknown"
    return 0
  fi
  if [[ ! -f "$DIAGNOSE_PY" ]]; then
    echo "unknown"
    return 0
  fi
  local result
  set +e
  result="$(
    NBUNK_BUNKER_RELAYS="$relays" python3 - "$DIAGNOSE_PY" <<'PY'
import importlib.util
import json
import os
import sys

path = sys.argv[1]
spec = importlib.util.spec_from_file_location("ci_nbunk_diagnose", path)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

relays = [r.strip() for r in os.environ.get("NBUNK_BUNKER_RELAYS", "").split(",") if r.strip()]
if not relays:
    print("unknown")
    raise SystemExit(0)
results = [mod.probe_wss(url) for url in relays]
print(json.dumps(results), file=sys.stderr)
print("ok" if any(r.get("ok") for r in results) else "down")
PY
  )"
  local rc=$?
  set -e
  if [[ "$rc" -ne 0 || -z "$result" ]]; then
    echo "unknown"
    return 0
  fi
  echo "$result"
}

wait_for_bunker_relay() {
  # After backoff: if WS is down, keep probing until up or budget ends.
  local status
  status="$(probe_bunker_relays)"
  if [[ "$status" != "down" ]]; then
    echo "Bunker relay probe: ${status}"
    return 0
  fi
  echo "::warning::Bunker relay WebSocket is down; waiting for recovery before next nsyte attempt"
  while [[ "$(budget_remaining)" -gt 0 ]]; do
    if ! sleep_up_to 30; then
      break
    fi
    status="$(probe_bunker_relays)"
    echo "Bunker relay probe: ${status}"
    if [[ "$status" != "down" ]]; then
      return 0
    fi
    echo "::warning::Bunker relay still down; continuing to wait within retry budget"
  done
  return 1
}

emit_retryable_failure() {
  local attempts_used="$1"
  echo "::error::Retryable bunker/relay failure persisted after ${attempts_used} nsyte attempt(s) within ${RETRY_BUDGET_SECONDS}s budget."
  echo "::error::nsyte uses a hard 30s NIP-46 connect timeout; flaky bunker relays (e.g. powr.build) often deliver the request to the bunker but drop/delay the response. The bunker app may show the request even when CI times out."
  if [[ -n "${NBUNK_BUNKER_RELAYS:-}" ]]; then
    echo "::error::Bunker relays: ${NBUNK_BUNKER_RELAYS}"
  fi
  if [[ -n "${NBUNK_PUBKEY_PREFIX:-}" ]]; then
    echo "::error::Bunker pubkey prefix: ${NBUNK_PUBKEY_PREFIX}…"
  fi
}

LAST_LOG=""
LAST_CLASS="unknown"
LAST_EXIT=1
ATTEMPTS_USED=0

echo "Retry budget: ${RETRY_BUDGET_SECONDS}s; max nsyte attempts: ${MAX_ATTEMPTS}"

for ((attempt = 1; attempt <= MAX_ATTEMPTS; attempt++)); do
  if [[ "$(budget_remaining)" -le 0 ]]; then
    LAST_CLASS="retryable"
    LAST_EXIT=1
    echo "::error::Retry budget exhausted before attempt ${attempt}"
    emit_retryable_failure "$ATTEMPTS_USED"
    break
  fi

  echo "::group::nsyte deploy attempt ${attempt}/${MAX_ATTEMPTS} (budget left $(budget_remaining)s)"
  LOG="$(mktemp)"
  LAST_LOG="$LOG"
  ATTEMPTS_USED=$attempt
  set +e
  "$NSYTE_BIN" deploy "$SITE_DIR" -i \
    --sec "$NBUNK_SECRET" \
    --relays "$NSYTE_RELAYS" \
    --servers "$NSYTE_SERVERS" \
    --name "$NSYTE_NAME" \
    --concurrency 4 \
    --skip-secrets-scan \
    --verbose \
    2>&1 | tee "$LOG"
  EXIT_CODE=${PIPESTATUS[0]}
  set -e
  echo "nsyte exit code: ${EXIT_CODE}"
  echo "::endgroup::"

  if [[ "$EXIT_CODE" -eq 0 ]]; then
    LAST_CLASS="success"
    LAST_EXIT=0
    echo "Deploy succeeded on attempt ${attempt}/${MAX_ATTEMPTS}"
    append_summary "## Nostr deploy"
    append_summary "- Result: **success** (attempt ${attempt}/${MAX_ATTEMPTS})"
    append_summary "- nsyte: \`${NSYTE_BIN}\`"
    append_summary "- Retry budget: ${RETRY_BUDGET_SECONDS}s"
    if [[ -n "${NBUNK_PUBKEY_PREFIX:-}" ]]; then
      append_summary "- Bunker pubkey prefix: \`${NBUNK_PUBKEY_PREFIX}…\`"
    fi
    if [[ -n "${NBUNK_BUNKER_RELAYS:-}" ]]; then
      append_summary "- Bunker relays: \`${NBUNK_BUNKER_RELAYS}\`"
    fi
    exit 0
  fi

  if is_permanent "$LOG"; then
    LAST_CLASS="permanent"
    LAST_EXIT=2
    echo "::error::Permanent deploy error (not retrying). See attempt ${attempt} log."
    break
  fi

  if is_retryable "$LOG"; then
    LAST_CLASS="retryable"
    LAST_EXIT=1
    if ((attempt >= MAX_ATTEMPTS)); then
      emit_retryable_failure "$ATTEMPTS_USED"
      break
    fi
    if [[ "$(budget_remaining)" -le 0 ]]; then
      emit_retryable_failure "$ATTEMPTS_USED"
      break
    fi

    DELAY="$(backoff_seconds "$attempt")"
    echo "::warning::Retryable failure on attempt ${attempt}; sleeping ${DELAY}s (capped by budget)"
    if ! sleep_up_to "$DELAY"; then
      emit_retryable_failure "$ATTEMPTS_USED"
      break
    fi

    if ! wait_for_bunker_relay; then
      emit_retryable_failure "$ATTEMPTS_USED"
      break
    fi
    continue
  fi

  LAST_CLASS="unknown"
  LAST_EXIT=1
  echo "::error::Unrecognized deploy failure (not retrying). See attempt ${attempt} log."
  break
done

append_summary "## Nostr deploy"
append_summary "- Result: **failure** (\`${LAST_CLASS}\`)"
append_summary "- nsyte attempts used: ${ATTEMPTS_USED}/${MAX_ATTEMPTS}"
append_summary "- Retry budget: ${RETRY_BUDGET_SECONDS}s"
if [[ -n "${NBUNK_PUBKEY_PREFIX:-}" ]]; then
  append_summary "- Bunker pubkey prefix: \`${NBUNK_PUBKEY_PREFIX}…\`"
fi
if [[ -n "${NBUNK_BUNKER_RELAYS:-}" ]]; then
  append_summary "- Bunker relays: \`${NBUNK_BUNKER_RELAYS}\`"
fi
if [[ "$LAST_CLASS" == "retryable" ]]; then
  append_summary ""
  append_summary "Likely flaky bunker-relay round-trip (nsyte hard 30s NIP-46 connect). The bunker may show the request even when CI times out if the response is delayed or dropped."
fi
if [[ -n "$LAST_LOG" && -f "$LAST_LOG" && -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  {
    echo ""
    echo "### Last error lines"
    echo '```'
    grep -Eih 'error|timeout|bunker|nip46|signer|fail|✗' "$LAST_LOG" | tail -n 30 || true
    echo '```'
  } >>"$GITHUB_STEP_SUMMARY"
fi

exit "$LAST_EXIT"
