#!/usr/bin/env bash
# Deploy site with nsyte, retrying transient bunker/network failures.
# Required env: NBUNK_SECRET, NSYTE_BIN, SITE_DIR
# Optional: NSYTE_NAME, NSYTE_RELAYS, NSYTE_SERVERS, MAX_ATTEMPTS,
#           NBUNK_BUNKER_RELAYS, NBUNK_PUBKEY_PREFIX
set -euo pipefail

NSYTE_BIN="${NSYTE_BIN:?NSYTE_BIN is required}"
SITE_DIR="${SITE_DIR:?SITE_DIR is required}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-3}"
NSYTE_NAME="${NSYTE_NAME:-persecutio}"
NSYTE_RELAYS="${NSYTE_RELAYS:-wss://relay.nsite.lol,wss://nos.lol,wss://relay.nostr.band,wss://relay.primal.net}"
NSYTE_SERVERS="${NSYTE_SERVERS:-https://cdn.hzrd149.com}"

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

LAST_LOG=""
LAST_CLASS="unknown"
LAST_EXIT=1

for ((attempt = 1; attempt <= MAX_ATTEMPTS; attempt++)); do
  echo "::group::nsyte deploy attempt ${attempt}/${MAX_ATTEMPTS}"
  LOG="$(mktemp)"
  LAST_LOG="$LOG"
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
    if ((attempt < MAX_ATTEMPTS)); then
      # Backoff: 20s after attempt 1, 40s after attempt 2
      DELAY=$((attempt * 20))
      echo "::warning::Retryable failure on attempt ${attempt}; sleeping ${DELAY}s"
      sleep "$DELAY"
      continue
    fi
    echo "::error::Retryable failure persisted after ${MAX_ATTEMPTS} attempts"
    break
  fi

  LAST_CLASS="unknown"
  LAST_EXIT=1
  echo "::error::Unrecognized deploy failure (not retrying). See attempt ${attempt} log."
  break
done

append_summary "## Nostr deploy"
append_summary "- Result: **failure** (\`${LAST_CLASS}\`)"
append_summary "- Attempts used: up to ${MAX_ATTEMPTS}"
if [[ -n "${NBUNK_PUBKEY_PREFIX:-}" ]]; then
  append_summary "- Bunker pubkey prefix: \`${NBUNK_PUBKEY_PREFIX}…\`"
fi
if [[ -n "${NBUNK_BUNKER_RELAYS:-}" ]]; then
  append_summary "- Bunker relays: \`${NBUNK_BUNKER_RELAYS}\`"
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
