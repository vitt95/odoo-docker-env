#!/usr/bin/env bash
# =============================================================================
# install.sh — one-command bootstrap for the Odoo 18 stack.
#
#   ./install.sh dev            # development environment (hot-reload, pgAdmin)
#   ./install.sh prod           # production environment (workers, hardened)
#   ./install.sh dev --update-core   # also fast-forward the ./core checkout
#
# Idempotent: safe to run repeatedly. It creates the directory layout, clones
# the Odoo source, writes the .env file, generates missing secrets, renders the
# Odoo config, builds the images, brings the stack up and waits for health.
#
# Secrets are never echoed to the terminal: they are written to .env and
# secrets/ (both mode 600) and only their locations are printed.
# =============================================================================
set -euo pipefail

# Resolve own location and load shared helpers.
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "${SELF_DIR}/scripts/lib.sh"

GENERATED_SECRETS=()
UPDATE_CORE=0

usage() {
  cat <<EOF
Usage: ./install.sh <dev|prod> [--update-core]

  dev            Development: source bind-mounts, hot-reload, debug logs, pgAdmin.
  prod           Production:  multiprocess workers, resource limits, hardened config.
  --update-core  Fast-forward the ./core Odoo source checkout to the tip of
                 ODOO_SOURCE_BRANCH before starting.
EOF
  exit "${1:-1}"
}

# --- 1. Parse arguments ------------------------------------------------------
[[ $# -ge 1 ]] || usage
MODE="$1"; shift
case "$MODE" in
  dev|prod) ;;
  -h|--help) usage 0 ;;
  *) err "Invalid mode: '$MODE'"; usage ;;
esac
while [[ $# -gt 0 ]]; do
  case "$1" in
    --update-core) UPDATE_CORE=1 ;;
    -h|--help) usage 0 ;;
    *) err "Unknown option: '$1'"; usage ;;
  esac
  shift
done
export MODE

hr; log "Bootstrapping Odoo 18 stack in '${C_BOLD}${MODE}${C_RESET}' mode"; hr

# --- 2. Host / OS sanity checks ---------------------------------------------
OS="$(uname -s)"
log "Host OS: ${OS} ($(uname -m))"
if [[ "$MODE" == "prod" && "$OS" != "Linux" ]]; then
  warn "Production mode is designed for Linux servers; '${OS}' detected. Continuing anyway."
fi

# --- 3. Prerequisites --------------------------------------------------------
log "Checking prerequisites..."
require_docker
require_cmd git
require_cmd openssl
require_cmd sed
require_cmd grep
ok "All prerequisites satisfied."

# --- 4. Directory layout (idempotent) ---------------------------------------
log "Ensuring directory structure..."
mkdir -p "${PROJECT_ROOT}"/{custom_addons,enterprise,logs,backups,config/pgadmin,scripts,docs}
mkdir -p "$SECRETS_DIR" && chmod 700 "$SECRETS_DIR"
touch "${PROJECT_ROOT}/logs/.gitkeep" \
      "${PROJECT_ROOT}/backups/.gitkeep" \
      "${PROJECT_ROOT}/enterprise/.gitkeep"
ok "Directories ready."

# --- 5. .env (create from example, never overwrite an existing one) ---------
if [[ ! -f "$ENV_FILE" ]]; then
  [[ -f "${PROJECT_ROOT}/.env.example" ]] || die ".env.example is missing — cannot create .env."
  ( umask 077; cp "${PROJECT_ROOT}/.env.example" "$ENV_FILE" )
  ok "Created .env from .env.example"
else
  log ".env already exists — keeping it."
fi
chmod 600 "$ENV_FILE"

# Persist the chosen mode.
env_set DEPLOY_MODE "$MODE"

# --- 6. Odoo source checkout (./core) ---------------------------------------
# The stack runs `python3 /opt/odoo/core/odoo-bin`, so this checkout is a hard
# requirement — without it the container exits 127 (command not found).
SOURCE_REPO="$(env_get ODOO_SOURCE_REPO)";     SOURCE_REPO="${SOURCE_REPO:-https://github.com/odoo/odoo.git}"
SOURCE_BRANCH="$(env_get ODOO_SOURCE_BRANCH)"; SOURCE_BRANCH="${SOURCE_BRANCH:-18.0}"

if [[ ! -f "${CORE_DIR}/odoo-bin" ]]; then
  if [[ -d "${CORE_DIR}" ]] && [[ -n "$(ls -A "${CORE_DIR}" 2>/dev/null)" ]]; then
    die "./core exists but has no odoo-bin. Remove it and re-run: rm -rf '${CORE_DIR}'"
  fi
  warn "Odoo source not found. Cloning ${SOURCE_REPO} (branch ${SOURCE_BRANCH})."
  warn "This is a ~1.2 GB shallow clone and takes several minutes on first run."
  git clone --depth 1 --branch "$SOURCE_BRANCH" --single-branch \
    "$SOURCE_REPO" "$CORE_DIR"
  ok "Odoo source cloned into ./core"
else
  if (( UPDATE_CORE )); then
    log "Updating ./core to the tip of ${SOURCE_BRANCH}..."
    git -C "$CORE_DIR" fetch --depth 1 origin "$SOURCE_BRANCH"
    git -C "$CORE_DIR" reset --hard FETCH_HEAD
    ok "./core updated."
  else
    log "./core present ($(git -C "$CORE_DIR" rev-parse --short HEAD 2>/dev/null || echo 'not a git checkout')) — keeping it. Use --update-core to refresh."
  fi
fi

# Warn when the source series and the image tag drift apart: the image supplies
# the interpreter and every Python dependency the source is executed with.
IMAGE_TAG="$(env_get ODOO_IMAGE_TAG)"; IMAGE_TAG="${IMAGE_TAG:-18.0}"
[[ "$SOURCE_BRANCH" == "$IMAGE_TAG" ]] \
  || warn "ODOO_SOURCE_BRANCH (${SOURCE_BRANCH}) != ODOO_IMAGE_TAG (${IMAGE_TAG}). Dependency mismatches are likely."

# --- 7. Generate missing secrets --------------------------------------------
ensure_secret() {
  local key="$1"
  if [[ -z "$(env_get "$key")" ]]; then
    env_set "$key" "$(gen_password)"
    GENERATED_SECRETS+=("$key")
    ok "Generated ${key}"
  fi
}
log "Ensuring secrets..."
ensure_secret POSTGRES_PASSWORD
ensure_secret ODOO_ADMIN_PASSWD
ensure_secret PGADMIN_PASSWORD

load_env

# Mirror the passwords into file-backed Docker secrets so compose never has to
# put them in a container's environment.
write_secret_file "$PG_PASSWORD_FILE"                "$POSTGRES_PASSWORD"
write_secret_file "${SECRETS_DIR}/pgadmin_password"  "$PGADMIN_PASSWORD"
ok "Docker secrets written to secrets/ (mode 600)."

# --- 8. Render Odoo config from template ------------------------------------
log "Rendering config/odoo.conf..."
render_odoo_conf "$ODOO_ADMIN_PASSWD" "${POSTGRES_USER:-odoo}" "$POSTGRES_PASSWORD"
ok "config/odoo.conf rendered (chmod 600)."

# --- 9. Clean up any containers left behind by a previous location ----------
check_stale_project
preflight

# --- 10. Build images + pull base layers ------------------------------------
log "Building images (pulling latest base layers)..."
dc build --pull
log "Pulling external images (db, pgAdmin)..."
dc pull db >/dev/null 2>&1 || true
[[ "$MODE" == "dev" ]] && { dc pull pgadmin >/dev/null 2>&1 || true; }
ok "Images ready."

# --- 11. Start the database first and reconcile its password ----------------
# An existing db_data volume keeps the password its role was created with, so
# the freshly generated one in .env has to be applied explicitly before Odoo
# tries to connect.
log "Starting the database..."
dc up -d db
wait_healthy db 120
log "Reconciling the PostgreSQL role password with .env..."
sync_db_password "$POSTGRES_PASSWORD"
ok "Database credentials in sync."

# --- 12. Start the rest of the stack ----------------------------------------
log "Starting the stack..."
dc up -d
ok "Containers started."
wait_healthy odoo 240

# --- 13. Final summary -------------------------------------------------------
ODOO_VER="$(dc exec -T odoo python3 /opt/odoo/core/odoo-bin --version 2>/dev/null | head -1 || echo 'Odoo 18.0')"
PG_VER="$(dc exec -T db postgres --version 2>/dev/null | awk '{print $1, $3}' || echo 'PostgreSQL')"
HOST_PORT="$(env_get ODOO_PORT)"; HOST_PORT="${HOST_PORT:-8069}"

hr
ok "Odoo 18 stack is up and running."
hr
printf '%sEnvironment%s   : %s\n'  "$C_BOLD" "$C_RESET" "$MODE"
printf '%sOdoo URL%s      : %s\n'  "$C_BOLD" "$C_RESET" "http://127.0.0.1:${HOST_PORT}"
printf '%sOdoo version%s  : %s\n'  "$C_BOLD" "$C_RESET" "$ODOO_VER"
printf '%sOdoo source%s   : %s\n'  "$C_BOLD" "$C_RESET" "${CORE_DIR} (branch ${SOURCE_BRANCH})"
printf '%sPostgres%s      : %s\n'  "$C_BOLD" "$C_RESET" "$PG_VER"
printf '%sCustom addons%s : %s\n'  "$C_BOLD" "$C_RESET" "${PROJECT_ROOT}/custom_addons"
printf '%sEnterprise%s    : %s\n'  "$C_BOLD" "$C_RESET" "${PROJECT_ROOT}/enterprise (optional)"
printf '%sFilestore%s     : %s\n'  "$C_BOLD" "$C_RESET" "docker volume '$(project_name)_odoo_filestore' -> /var/lib/odoo"
printf '%sLogs%s          : %s\n'  "$C_BOLD" "$C_RESET" "./manage.sh logs  (docker json-file, rotated)"
printf '%sBackups%s       : %s\n'  "$C_BOLD" "$C_RESET" "${PROJECT_ROOT}/backups  (./manage.sh backup)"
if [[ "$MODE" == "dev" ]]; then
  printf '%spgAdmin%s       : %s\n' "$C_BOLD" "$C_RESET" "http://127.0.0.1:$(env_get PGADMIN_PORT)  (login: $(env_get PGADMIN_EMAIL))"
fi
hr
if [[ ${#GENERATED_SECRETS[@]} -gt 0 ]]; then
  warn "Generated ${#GENERATED_SECRETS[@]} credential(s): ${GENERATED_SECRETS[*]}"
  warn "Values are NOT printed here on purpose (terminal scrollback / CI logs)."
  warn "Read them with:  grep '^<KEY>=' .env"
  warn "Rotate them any time with:  ./manage.sh rotate-secrets"
  hr
fi
printf 'Manage the stack with: %s./manage.sh <command>%s  (try: ./manage.sh help)\n' "$C_BOLD" "$C_RESET"
