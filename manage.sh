#!/usr/bin/env bash
# =============================================================================
# manage.sh — day-2 operations CLI for the Odoo 18 stack.
#
# A single entry point (instead of many scripts) keeps shared logic in one
# place (scripts/lib.sh), avoids duplication and stays self-documenting.
#
#   ./manage.sh <command> [args]
#
# The active mode (dev|prod) is read from .env, so commands always target the
# same stack created by install.sh.
# =============================================================================
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "${SELF_DIR}/scripts/lib.sh"

MODE="$(current_mode)"
[[ "$MODE" == "dev" || "$MODE" == "prod" ]] || die "No valid DEPLOY_MODE in .env. Run ./install.sh <dev|prod> first."
export MODE
load_env

# Ask for an explicit 'yes' before a destructive action.
confirm() {
  warn "$1"
  read -r -p "Type 'yes' to continue: " answer
  [[ "$answer" == "yes" ]] || die "Aborted."
}

usage() {
  cat <<EOF
${C_BOLD}Odoo stack manager${C_RESET}  (mode: ${MODE})

Usage: ./manage.sh <command> [args]

  ${C_BOLD}status${C_RESET}                 Show container + health status and URLs
  ${C_BOLD}start${C_RESET}                  Start the stack
  ${C_BOLD}stop${C_RESET}                   Stop the stack (containers, keep data)
  ${C_BOLD}restart${C_RESET} [svc]          Restart all services or one (odoo|db|pgadmin)
  ${C_BOLD}logs${C_RESET} [svc] [-f]        Tail logs (default: all, follow on)
  ${C_BOLD}shell${C_RESET} [svc]            Open a bash shell in a container (default: odoo)
  ${C_BOLD}odoo-shell${C_RESET} <db>        Open an Odoo interactive python shell on <db>
  ${C_BOLD}psql${C_RESET} [db]              Open psql (default db: \$POSTGRES_DB)
  ${C_BOLD}check${C_RESET}                  Boundary checks (D24), pure-zone tests, corpus
  ${C_BOLD}test${C_RESET} <db> [tags]       Boundary checks, then Odoo tests on <db>
  ${C_BOLD}update${C_RESET}                 Pull/rebuild images and recreate containers
  ${C_BOLD}upgrade${C_RESET} <db> [mods]    Upgrade modules (default: all) on <db>
  ${C_BOLD}backup${C_RESET}                 Dump all databases + filestore to ./backups
  ${C_BOLD}restore${C_RESET} <timestamp>    Restore a backup (DESTRUCTIVE)
  ${C_BOLD}cleanup${C_RESET} [--all]        Remove containers/networks (--all also volumes)
  ${C_BOLD}help${C_RESET}                   Show this help
EOF
}

cmd_status() {
  hr; dc ps; hr
  local port; port="$(env_get ODOO_PORT)"; port="${port:-8069}"
  printf 'Odoo URL : http://localhost:%s\n' "$port"
  [[ "$MODE" == "dev" ]] && printf 'pgAdmin  : http://localhost:%s\n' "$(env_get PGADMIN_PORT)"
}

cmd_start()   { log "Starting stack..."; dc up -d; ok "Started."; }
cmd_stop()    { log "Stopping stack..."; dc stop; ok "Stopped (data preserved)."; }
cmd_restart() { log "Restarting ${1:-all}..."; dc restart ${1:+"$1"}; ok "Restarted."; }

cmd_logs() {
  # Default: follow everything. Pass a service and/or extra flags through.
  if [[ $# -eq 0 ]]; then
    dc logs -f --tail=200
  else
    dc logs -f --tail=200 "$@"
  fi
}

cmd_shell() {
  local svc="${1:-odoo}"
  log "Opening bash in '$svc' (exit to leave)..."
  dc exec "$svc" bash
}

cmd_odoo_shell() {
  local db="${1:?Usage: ./manage.sh odoo-shell <db>}"
  dc exec odoo odoo shell -c /etc/odoo/odoo.conf -d "$db"
}

cmd_psql() {
  local db="${1:-${POSTGRES_DB:-postgres}}"
  dc exec db psql -U "${POSTGRES_USER}" -d "$db"
}

# The four checks of D24 are static: no stack, no database, stdlib only. They
# run here, in CI (.github/workflows/boundaries.yml) and on pre-push, so a
# boundary violation is caught by whichever of the three comes first.
cmd_check() {
  log "Architecture boundaries (D24)..."
  python3 "${PROJECT_ROOT}/tools/arch/run.py"
  log "Tests of the checks themselves..."
  python3 -m unittest discover -s "${PROJECT_ROOT}/tools/arch/tests" -t "${PROJECT_ROOT}"
  log "Contract, pure zone (no Odoo, no database)..."
  python3 "${PROJECT_ROOT}/tools/pure/run.py"
  log "Foundational corpus against the contract..."
  python3 "${PROJECT_ROOT}/ai/corpus/verifica_contratto.py"
  log "Dictionary and catalogue against the corpus..."
  python3 "${PROJECT_ROOT}/ai/corpus/misura_catalogo.py"
  ok "Boundaries, contract and catalogue verified."
}

cmd_test() {
  local db="${1:?Usage: ./manage.sh test <db> [test-tags]}"
  local mods="nli_core,nli_semantics,nli_engine,nli_web,nli_observability"
  # Default: every test of every product module. Derived from the module list so
  # a module that gains tests is covered without editing two places — a tag list
  # that silently stops matching is a suite that silently stops running.
  local tags="${2:-/${mods//,/,/}}"

  # Static first: it is faster, and a broken boundary makes a green test suite
  # misleading rather than reassuring.
  cmd_check

  log "Installing/updating '${mods}' and running tests (tags: ${tags}) on '${db}'..."
  # Same interpreter and same source tree as the dev override: the image also
  # ships an Odoo, and running the tests against a different copy than the one
  # serving requests is a way to get a green suite for the wrong build.
  dc run --rm odoo python3 /opt/odoo/core/odoo-bin -c /etc/odoo/odoo.conf -d "$db" \
    -i "$mods" -u "$mods" \
    --test-enable --test-tags "$tags" --stop-after-init --log-level=test
  ok "Tests finished."
}

cmd_update() {
  log "Pulling base images and rebuilding Odoo image..."
  dc pull db >/dev/null 2>&1 || true
  [[ "$MODE" == "dev" ]] && { dc pull pgadmin >/dev/null 2>&1 || true; }
  dc build --pull odoo
  log "Recreating containers..."
  dc up -d
  wait_healthy odoo 240
  ok "Update complete. To apply module changes: ./manage.sh upgrade <db>"
}

cmd_upgrade() {
  local db="${1:?Usage: ./manage.sh upgrade <db> [modules|all]}"
  local mods="${2:-all}"
  log "Upgrading modules '${mods}' on database '${db}'..."
  dc run --rm odoo odoo -c /etc/odoo/odoo.conf -d "$db" -u "$mods" --stop-after-init
  dc up -d odoo
  ok "Upgrade finished."
}

cmd_backup() {
  local ts dir
  ts="$(date +%Y%m%d_%H%M%S)"
  dir="${PROJECT_ROOT}/backups"
  log "Dumping all PostgreSQL databases..."
  dc exec -T db pg_dumpall -U "${POSTGRES_USER}" | gzip > "${dir}/db_${ts}.sql.gz"
  log "Archiving filestore..."
  dc exec -T odoo tar czf - -C /var/lib/odoo . > "${dir}/filestore_${ts}.tar.gz"
  ok "Backup complete:"
  printf '   %s\n' "${dir}/db_${ts}.sql.gz" "${dir}/filestore_${ts}.tar.gz"
}

cmd_restore() {
  local ts="${1:?Usage: ./manage.sh restore <timestamp>  (see ./backups)}"
  local db="${PROJECT_ROOT}/backups/db_${ts}.sql.gz"
  local fs="${PROJECT_ROOT}/backups/filestore_${ts}.tar.gz"
  [[ -f "$db" ]] || die "Backup not found: $db"
  confirm "This will OVERWRITE all current databases and the filestore from backup '${ts}'."
  log "Restoring databases..."
  gunzip -c "$db" | dc exec -T db psql -U "${POSTGRES_USER}" -d postgres
  if [[ -f "$fs" ]]; then
    log "Restoring filestore..."
    dc exec -T odoo sh -c 'rm -rf /var/lib/odoo/* && tar xzf - -C /var/lib/odoo' < "$fs"
  else
    warn "No filestore archive for '${ts}' — skipping filestore restore."
  fi
  dc restart odoo
  ok "Restore complete."
}

cmd_cleanup() {
  if [[ "${1:-}" == "--all" ]]; then
    confirm "This will remove containers, networks AND volumes (ALL data: DB + filestore lost)."
    dc down --remove-orphans --volumes
    ok "Stack and volumes removed."
  else
    confirm "This will remove containers and networks. Named volumes (data) are kept."
    dc down --remove-orphans
    docker image prune -f >/dev/null 2>&1 || true
    ok "Containers/networks removed. Volumes preserved (use 'cleanup --all' to drop them)."
  fi
}

# --- Dispatch ----------------------------------------------------------------
cmd="${1:-help}"; shift || true
case "$cmd" in
  status)            cmd_status "$@" ;;
  start)             cmd_start "$@" ;;
  stop)              cmd_stop "$@" ;;
  restart)           cmd_restart "$@" ;;
  logs)              cmd_logs "$@" ;;
  shell)             cmd_shell "$@" ;;
  odoo-shell)        cmd_odoo_shell "$@" ;;
  psql)              cmd_psql "$@" ;;
  check)             cmd_check "$@" ;;
  test)              cmd_test "$@" ;;
  update)            cmd_update "$@" ;;
  upgrade)           cmd_upgrade "$@" ;;
  backup)            cmd_backup "$@" ;;
  restore)           cmd_restore "$@" ;;
  cleanup)           cmd_cleanup "$@" ;;
  help|-h|--help)    usage ;;
  *)                 err "Unknown command: '$cmd'"; usage; exit 1 ;;
esac
