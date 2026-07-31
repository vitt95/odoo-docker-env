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

# --- Well-known paths --------------------------------------------------------
ENV_FILE="${PROJECT_ROOT}/.env"
SECRETS_DIR="${PROJECT_ROOT}/secrets"
CORE_DIR="${PROJECT_ROOT}/core"
ODOO_CONF="${PROJECT_ROOT}/config/odoo.conf"
ODOO_CONF_TEMPLATE="${PROJECT_ROOT}/config/odoo.conf.template"
PG_PASSWORD_FILE="${SECRETS_DIR}/postgres_password"

# Compose project name. Fixed (not derived from the directory name) so that
# renaming or moving the checkout keeps addressing the same containers and
# named volumes. Overridable via .env.
DEFAULT_PROJECT_NAME="odoo"

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
  chmod 600 "$ENV_FILE"
}

# Generate a strong alphanumeric password (safe for sed / conf files).
gen_password() { openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c 32; }

# Determine the active deployment mode (persisted in .env by install.sh).
current_mode() { env_get DEPLOY_MODE; }

project_name() {
  local name; name="$(env_get COMPOSE_PROJECT_NAME)"
  printf '%s' "${name:-$DEFAULT_PROJECT_NAME}"
}

# --- Secrets -----------------------------------------------------------------
# Docker secrets are file-backed: compose mounts them at /run/secrets/<name>
# instead of exporting them as environment variables, so they stay out of
# `docker inspect`, `docker compose config` and /proc/<pid>/environ.
write_secret_file() {
  local path="$1" value="$2"
  mkdir -p "$(dirname "$path")"
  ( umask 077; printf '%s' "$value" > "$path" )
  chmod 600 "$path"
}

# Render config/odoo.conf from the committed template, injecting secrets.
render_odoo_conf() {
  local admin_passwd="$1" pg_user="$2" pg_password="$3"
  [[ -f "$ODOO_CONF_TEMPLATE" ]] || die "Missing ${ODOO_CONF_TEMPLATE}"
  # A stale directory here (created by Docker for a missing bind-mount source)
  # would make the write fail with a confusing error.
  [[ -d "$ODOO_CONF" ]] && die "${ODOO_CONF} is a directory (left over from a failed run). Remove it and retry."
  ( umask 077
    sed -e "s|\$ODOO_ADMIN_PASSWD|${admin_passwd}|g" \
        -e "s|\$POSTGRES_USER|${pg_user}|g" \
        -e "s|\$POSTGRES_PASSWORD|${pg_password}|g" \
      "$ODOO_CONF_TEMPLATE" > "$ODOO_CONF" )
  chmod 600 "$ODOO_CONF"
}

# Postgres applies POSTGRES_PASSWORD only when it initialises an empty PGDATA.
# On a pre-existing db_data volume the role keeps the password it was created
# with, so a regenerated or rotated .env silently breaks Odoo's login with
# "password authentication failed". Reconcile from inside the cluster (local
# socket, trust auth) — idempotent, safe to run on every install.
# Requires the db service to be up and healthy.
sync_db_password() {
  local user="${POSTGRES_USER:-odoo}" db="${POSTGRES_DB:-postgres}" pass="$1"
  # Passed on stdin, not argv: psql arguments show up in `ps` output.
  printf "ALTER ROLE %s WITH PASSWORD '%s';\n" "$user" "$pass" \
    | dc exec -T db psql -q -v ON_ERROR_STOP=1 -U "$user" -d "$db" >/dev/null \
    || die "Could not set the '${user}' role password inside PostgreSQL."
}

# --- Preflight ---------------------------------------------------------------
# Every check below currently surfaces as an opaque container exit (127, or a
# config parse error) if it is left to fail at runtime. Fail early instead,
# with the command that fixes it.
preflight() {
  [[ -f "$ENV_FILE" ]] \
    || die ".env not found. Run: ./install.sh <dev|prod>"

  [[ -f "${CORE_DIR}/odoo-bin" ]] \
    || die "Odoo source missing at ./core (no odoo-bin). Run: ./install.sh $(current_mode) — it clones it."

  [[ -f "$ODOO_CONF" ]] \
    || die "config/odoo.conf missing. Run: ./install.sh $(current_mode) — it renders it from the template."

  [[ -s "$PG_PASSWORD_FILE" ]] \
    || die "secrets/postgres_password missing or empty. Run: ./install.sh $(current_mode)."
}

# A compose project whose config files have been moved or deleted leaves
# containers behind that still reference the old paths — they fail in ways that
# look like a broken stack. Detect and report.
check_stale_project() {
  local name; name="$(project_name)"
  local ids stale=0 f
  ids="$(docker ps -aq --filter "label=com.docker.compose.project=${name}" 2>/dev/null || true)"
  [[ -z "$ids" ]] && return 0
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    [[ -f "$f" ]] || stale=1
  done < <(docker inspect \
             --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}' \
             $ids 2>/dev/null | tr ',' '\n' | sort -u)
  if (( stale )); then
    warn "Containers from a previous location of this project were found."
    warn "Removing them (named volumes with your data are preserved)..."
    docker rm -f $ids >/dev/null 2>&1 || true
    ok "Stale containers removed."
  fi
}

# --- Compose wrapper ---------------------------------------------------------
# Requires MODE to be set (dev|prod). Always uses the same project name and the
# base + per-mode compose files so every script targets the same stack.
dc() {
  local mode="${MODE:-$(current_mode)}"
  [[ "$mode" == "dev" || "$mode" == "prod" ]] || die "Unknown mode '$mode' (expected dev|prod)."
  docker compose \
    --project-name "$(project_name)" \
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
