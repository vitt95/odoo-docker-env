#!/usr/bin/env bash
# =============================================================================
# install.sh — one-command bootstrap for the Odoo 18 stack.
#
#   ./install.sh dev    # development environment (hot-reload, pgAdmin)
#   ./install.sh prod   # production environment (workers, hardened)
#
# Idempotent: safe to run repeatedly. It creates the directory layout, the
# .env file, generates missing secrets, renders the Odoo config, builds the
# images and brings the stack up, then waits for healthchecks.
# =============================================================================
set -euo pipefail

# Resolve own location and load shared helpers.
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "${SELF_DIR}/scripts/lib.sh"

GENERATED_SECRETS=()

usage() {
  cat <<EOF
Usage: ./install.sh <dev|prod>

  dev   Development: source bind-mounts, hot-reload, debug logs, pgAdmin.
  prod  Production:  multiprocess workers, resource limits, hardened config.
EOF
  exit "${1:-1}"
}

# --- 1. Validate the mode argument ------------------------------------------
[[ $# -eq 1 ]] || usage
MODE="$1"
case "$MODE" in
  dev|prod) ;;
  -h|--help) usage 0 ;;
  *) err "Invalid mode: '$MODE'"; usage ;;
esac
export MODE

hr; log "Bootstrapping Odoo 18 stack in '${C_BOLD}${MODE}${C_RESET}' mode"; hr

# --- 2. Host / OS sanity checks ---------------------------------------------
OS="$(uname -s)"
log "Host OS: ${OS}"
if [[ "$MODE" == "prod" && "$OS" != "Linux" ]]; then
  warn "Production mode is designed for Linux servers; '${OS}' detected. Continuing anyway."
fi

# --- 3. Prerequisites --------------------------------------------------------
log "Checking prerequisites..."
require_docker
require_cmd openssl
require_cmd sed
require_cmd grep
ok "All prerequisites satisfied."

# --- 4. Directory layout (idempotent) ---------------------------------------
log "Ensuring directory structure..."
mkdir -p "${PROJECT_ROOT}"/{custom_addons,enterprise,logs,backups,config/pgadmin,scripts,docs}
touch "${PROJECT_ROOT}/logs/.gitkeep" \
      "${PROJECT_ROOT}/backups/.gitkeep" \
      "${PROJECT_ROOT}/enterprise/.gitkeep"
ok "Directories ready."

# --- 5. .env (create from example, never overwrite an existing one) ---------
if [[ ! -f "$ENV_FILE" ]]; then
  [[ -f "${PROJECT_ROOT}/.env.example" ]] || die ".env.example is missing — cannot create .env."
  cp "${PROJECT_ROOT}/.env.example" "$ENV_FILE"
  ok "Created .env from .env.example"
else
  log ".env already exists — keeping it."
fi

# Persist the chosen mode.
env_set DEPLOY_MODE "$MODE"

# --- 6. Generate missing secrets --------------------------------------------
ensure_secret() {
  local key="$1"
  if [[ -z "$(env_get "$key")" ]]; then
    local val; val="$(gen_password)"
    env_set "$key" "$val"
    GENERATED_SECRETS+=("${key}=${val}")
    ok "Generated ${key}"
  fi
}
log "Ensuring secrets..."
ensure_secret POSTGRES_PASSWORD
ensure_secret ODOO_ADMIN_PASSWD
ensure_secret PGADMIN_PASSWORD

# --- 7. Render Odoo config from template ------------------------------------
log "Rendering config/odoo.conf..."
load_env
sed -e "s|\$ODOO_ADMIN_PASSWD|${ODOO_ADMIN_PASSWD}|g" \
    -e "s|\$POSTGRES_USER|${POSTGRES_USER:-odoo}|g" \
    -e "s|\$POSTGRES_PASSWORD|${POSTGRES_PASSWORD}|g" \
  "${PROJECT_ROOT}/config/odoo.conf.template" > "${PROJECT_ROOT}/config/odoo.conf"
chmod 600 "${PROJECT_ROOT}/config/odoo.conf"
ok "config/odoo.conf rendered (chmod 600)."

# --- 8. Build images + pull base layers -------------------------------------
log "Building images (pulling latest base layers)..."
dc build --pull
log "Pulling external images (db, pgAdmin)..."
dc pull db >/dev/null 2>&1 || true
[[ "$MODE" == "dev" ]] && { dc pull pgadmin >/dev/null 2>&1 || true; }
ok "Images ready."

# --- 9. Start the stack ------------------------------------------------------
log "Starting the stack..."
dc up -d
ok "Containers started."

# --- 10. Wait for healthchecks ----------------------------------------------
wait_healthy db 120
wait_healthy odoo 240

# --- 11. Final summary -------------------------------------------------------
ODOO_VER="$(dc exec -T odoo odoo --version 2>/dev/null | head -1 || echo 'Odoo 18.0')"
PG_VER="$(dc exec -T db postgres --version 2>/dev/null | awk '{print $1, $3}' || echo 'PostgreSQL')"
HOST_PORT="$(env_get ODOO_PORT)"; HOST_PORT="${HOST_PORT:-8069}"

hr
ok "Odoo 18 stack is up and running."
hr
printf '%sEnvironment%s   : %s\n'  "$C_BOLD" "$C_RESET" "$MODE"
printf '%sOdoo URL%s      : %s\n'  "$C_BOLD" "$C_RESET" "http://localhost:${HOST_PORT}"
printf '%sOdoo version%s  : %s\n'  "$C_BOLD" "$C_RESET" "$ODOO_VER"
printf '%sPostgres%s      : %s\n'  "$C_BOLD" "$C_RESET" "$PG_VER"
printf '%sCustom addons%s : %s\n'  "$C_BOLD" "$C_RESET" "${PROJECT_ROOT}/custom_addons"
printf '%sEnterprise%s    : %s\n'  "$C_BOLD" "$C_RESET" "${PROJECT_ROOT}/enterprise (optional)"
printf '%sFilestore%s     : %s\n'  "$C_BOLD" "$C_RESET" "docker volume 'odoo_filestore' -> /var/lib/odoo"
printf '%sLogs%s          : %s\n'  "$C_BOLD" "$C_RESET" "./manage.sh logs  (docker json-file, rotated)"
printf '%sBackups%s       : %s\n'  "$C_BOLD" "$C_RESET" "${PROJECT_ROOT}/backups  (./manage.sh backup)"
if [[ "$MODE" == "dev" ]]; then
  printf '%spgAdmin%s       : %s\n' "$C_BOLD" "$C_RESET" "http://localhost:$(env_get PGADMIN_PORT)  (login: $(env_get PGADMIN_EMAIL))"
fi
hr
if [[ ${#GENERATED_SECRETS[@]} -gt 0 ]]; then
  warn "Generated credentials (also stored in .env — keep it safe):"
  for s in "${GENERATED_SECRETS[@]}"; do printf '   %s\n' "$s"; done
  hr
fi
printf 'Manage the stack with: %s./manage.sh <command>%s  (try: ./manage.sh help)\n' "$C_BOLD" "$C_RESET"
