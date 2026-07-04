#!/usr/bin/env bash
# =============================================================================
# Shared helpers for the Odoo Docker tooling.
# Sourced by install.sh and manage.sh — not meant to be executed directly.
# =============================================================================
set -euo pipefail

# --- Project root (parent of this scripts/ directory) ------------------------
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${LIB_DIR}/.." && pwd)"
export PROJECT_ROOT

# --- Colored output (auto-disabled when stdout is not a TTY) -----------------
if [[ -t 1 ]]; then
  C_RESET=$'\033[0m'; C_RED=$'\033[31m'; C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'; C_BLUE=$'\033[34m'; C_BOLD=$'\033[1m'
else
  C_RESET=''; C_RED=''; C_GREEN=''; C_YELLOW=''; C_BLUE=''; C_BOLD=''
fi

log()  { printf '%s[*]%s %s\n'  "$C_BLUE"   "$C_RESET" "$*"; }
ok()   { printf '%s[OK]%s %s\n' "$C_GREEN"  "$C_RESET" "$*"; }
warn() { printf '%s[!]%s %s\n'  "$C_YELLOW" "$C_RESET" "$*" >&2; }
err()  { printf '%s[X]%s %s\n'  "$C_RED"    "$C_RESET" "$*" >&2; }
die()  { err "$*"; exit 1; }
hr()   { printf '%s%s%s\n' "$C_BOLD" "------------------------------------------------------------" "$C_RESET"; }

# --- Dependency checks -------------------------------------------------------
require_cmd() { command -v "$1" >/dev/null 2>&1 || die "Missing dependency: '$1'. Please install it."; }

require_docker() {
  require_cmd docker
  docker compose version >/dev/null 2>&1 \
    || die "Docker Compose v2 plugin not found. Install 'docker-compose-plugin'."
  docker info >/dev/null 2>&1 \
    || die "Docker daemon not reachable. Is Docker running (and do you have permission)?"
}

# --- .env handling -----------------------------------------------------------
ENV_FILE="${PROJECT_ROOT}/.env"

load_env() {
  [[ -f "$ENV_FILE" ]] || die ".env not found. Run: ./install.sh <dev|prod>"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
}

# Read a single key from .env without sourcing it.
env_get() { grep -E "^$1=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- || true; }

# Insert or replace KEY=VALUE in .env (portable across GNU/BSD sed).
env_set() {
  local key="$1" val="$2"
  if grep -qE "^${key}=" "$ENV_FILE"; then
    sed -i.bak "s|^${key}=.*|${key}=${val}|" "$ENV_FILE" && rm -f "${ENV_FILE}.bak"
  else
    printf '%s=%s\n' "$key" "$val" >> "$ENV_FILE"
  fi
}

# Generate a strong alphanumeric password (safe for sed / conf files).
gen_password() { openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c 32; }

# Determine the active deployment mode (persisted in .env by install.sh).
current_mode() { env_get DEPLOY_MODE; }

# --- Compose wrapper ---------------------------------------------------------
# Requires MODE to be set (dev|prod). Always uses project name 'odoo' and the
# base + per-mode compose files so every script targets the same stack.
dc() {
  local mode="${MODE:-$(current_mode)}"
  [[ "$mode" == "dev" || "$mode" == "prod" ]] || die "Unknown mode '$mode' (expected dev|prod)."
  docker compose \
    --project-name odoo \
    --env-file "$ENV_FILE" \
    -f "${PROJECT_ROOT}/docker-compose.yml" \
    -f "${PROJECT_ROOT}/docker-compose.${mode}.yml" \
    "$@"
}

# Wait until a service's container reports a healthy healthcheck.
wait_healthy() {
  local svc="$1" timeout="${2:-180}" elapsed=0 cid status
  log "Waiting for '$svc' to become healthy (timeout ${timeout}s)..."
  cid="$(dc ps -q "$svc")"
  [[ -n "$cid" ]] || die "No container found for service '$svc'."
  while true; do
    status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cid" 2>/dev/null || echo starting)"
    case "$status" in
      healthy) printf '\n'; ok "'$svc' is healthy."; return 0 ;;
      unhealthy) printf '\n'; die "'$svc' is unhealthy. Inspect with: ./manage.sh logs $svc" ;;
    esac
    (( elapsed >= timeout )) && { printf '\n'; die "'$svc' not healthy after ${timeout}s."; }
    printf '.'; sleep 3; elapsed=$(( elapsed + 3 ))
  done
}
