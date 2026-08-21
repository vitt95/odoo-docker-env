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
preflight

# Odoo is executed from the ./core bind-mount, not from the image's packaged
# copy — every one-off invocation below has to use the same entry point.
ODOO_BIN=(python3 /opt/odoo/core/odoo-bin -c /etc/odoo/odoo.conf)

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
  ${C_BOLD}loadtest${C_RESET} <db> [n] [s]   Isolation proof of D27 on prefork workers
  ${C_BOLD}campo${C_RESET} <db> [famiglia]  Batteria sul campo: le frasi di ai/16 col modello vero
  ${C_BOLD}ollama${C_RESET} [stato]         Avvia il fornitore locale con la finestra giusta
  ${C_BOLD}atlante${C_RESET} <db>           Raccoglie il vocabolario di tutte le app (fine tuning)
  ${C_BOLD}dizionario${C_RESET} <db> [prova] Scrive i sinonimi delle date nel registro delle voci
  ${C_BOLD}backup${C_RESET}                 Dump all databases + filestore to ./backups
  ${C_BOLD}restore${C_RESET} <timestamp>    Restore a backup (DESTRUCTIVE)
  ${C_BOLD}rotate-secrets${C_RESET}         Regenerate all passwords and apply them live
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
  dc exec odoo python3 /opt/odoo/core/odoo-bin shell -c /etc/odoo/odoo.conf -d "$db"
}

cmd_campo() {
  # La batteria sul campo: le frasi di `tools/campo/frasi.py` attraverso il prodotto
  # vero, sul database indicato e con il modello del profilo in servizio.
  #
  # Non e' una prova ed e' apposta fuori da `check` e da `test`: il modello non e'
  # deterministico, e una suite che dipendesse da lui direbbe cose diverse a ogni
  # giro. E' una **misura**, e costa tempo di modello — un'ora abbondante per intero.
  #
  #   ./manage.sh campo db            tutte le famiglie
  #   ./manage.sh campo db date       una famiglia sola
  #   CAMPO_MAX=5 ./manage.sh campo db    le prime cinque
  local db="${1:?Usage: ./manage.sh campo <db> [intenti|operatori|date|limiti]}"
  local famiglia="${2:-}"
  log "Batteria sul campo su '${db}'${famiglia:+ (famiglia: ${famiglia})}..."
  dc exec -T \
    -e "CAMPO_FAMIGLIA=${famiglia}" \
    -e "CAMPO_MAX=${CAMPO_MAX:-}" \
    -e "CAMPO_SCRIVI=${CAMPO_SCRIVI:-}" \
    odoo python3 /opt/odoo/core/odoo-bin shell -c /etc/odoo/odoo.conf -d "$db" \
    --log-level=warn \
    < <(cat "${PROJECT_ROOT}/tools/campo/verifica_finestra.py" \
           "${PROJECT_ROOT}/tools/campo/frasi.py" \
           "${PROJECT_ROOT}/tools/campo/batteria.py")
  ok "Batteria finita."
}

cmd_ollama() {
  # Avvia il fornitore locale con la finestra che il profilo dichiara, e lo verifica.
  #
  # Serve perche' `Ollama.app` avvia `ollama serve` con un ambiente suo e **non**
  # eredita `launchctl setenv`: verificato il 21 agosto 2026 leggendo l'ambiente del
  # processo vero. L'impostazione `context_length` nel database dell'applicazione vale
  # per la sua chat, non per il server. L'unico modo e' avviarlo con la variabile.
  #
  # Senza, il server ne serve 4096, i prompt arrivano tagliati a meta' catalogo e il
  # prodotto risponde `not_understood`: sembra un limite del modello. La batteria adesso
  # si rifiuta di misurare in quel caso, ma il prodotto no.
  #
  #   ./manage.sh ollama            avvia (o riavvia) e verifica
  #   ./manage.sh ollama stato      dice solo che cosa serve adesso
  local finestra="${OLLAMA_CONTEXT_LENGTH:-8192}"
  local servita
  servita="$(curl -s --max-time 5 http://127.0.0.1:11434/api/ps \
    | python3 -c 'import json,sys
try:
    modelli = json.load(sys.stdin).get("models") or []
except Exception:
    modelli = []
print(next((str(m.get("context_length")) for m in modelli if m.get("context_length")), ""))' 2>/dev/null || true)"

  if [ "${1:-}" = "stato" ]; then
    if [ -z "$servita" ]; then
      warn "Nessun modello caricato: /api/ps non dice niente finche' non arriva una domanda."
    else
      log "Il server serve ${servita} gettoni (il profilo ne vuole ${finestra})."
    fi
    return 0
  fi

  log "Fermo Ollama e lo riavvio con OLLAMA_CONTEXT_LENGTH=${finestra}..."
  osascript -e 'quit app "Ollama"' 2>/dev/null || true
  sleep 3
  pkill -f "ollama serve" 2>/dev/null || true
  sleep 2
  OLLAMA_CONTEXT_LENGTH="${finestra}" nohup ollama serve > /tmp/ollama-serve.log 2>&1 &
  sleep 5
  ok "Avviato. Verifica con: ./manage.sh ollama stato (dopo una domanda qualunque)."
}

cmd_dizionario() {
  # I sinonimi delle date nel registro delle voci approvate (D108).
  #
  # Perche' un comando e non un file di dati del modulo: sono parole di una lingua e
  # di un'installazione, non struttura. Chi installa in inglese non li vuole, e chi
  # aggiunge un'entita' al perimetro li rivuole — quindi si esegue quando serve.
  #
  #   ./manage.sh dizionario db          scrive
  #   ./manage.sh dizionario db prova    dice cosa scriverebbe, senza scrivere
  local db="${1:?Usage: ./manage.sh dizionario <db> [prova]}"
  local prova=""
  [ "${2:-}" = "prova" ] && prova="1"
  # Due file, due esecuzioni separate: ognuno chiude la propria transazione
  # (`commit` o `rollback`), e concatenarli come fa `campo` significherebbe che il
  # rollback della prova del primo si porta via anche il secondo.
  log "Dizionario — sinonimi delle date su '${db}'${prova:+ (prova, non scrive)}..."
  dc exec -T -e "DIZIONARIO_PROVA=${prova}" \
    odoo python3 /opt/odoo/core/odoo-bin shell -c /etc/odoo/odoo.conf -d "$db" \
    --log-level=warn \
    < "${PROJECT_ROOT}/tools/dizionario/sinonimi_date.py"

  # `pacchetti.py` e' zona pura e provata da sola; `sinonimi_entita.py` e' la meta'
  # che legge l'installazione. Si concatenano come `campo` fa con `frasi.py`, perche'
  # la shell di Odoo riceve un sorgente solo e dentro il container `tools/` non c'e'.
  log "Dizionario — parole di entita' su '${db}'${prova:+ (prova, non scrive)}..."
  dc exec -T -e "DIZIONARIO_PROVA=${prova}" \
    odoo python3 /opt/odoo/core/odoo-bin shell -c /etc/odoo/odoo.conf -d "$db" \
    --log-level=warn \
    < <(cat "${PROJECT_ROOT}/tools/dizionario/pacchetti.py" \
           "${PROJECT_ROOT}/tools/dizionario/sinonimi_entita.py")
}

cmd_atlante() {
  # Raccoglie l'atlante: tutto quello che AIDA può nominare in un'installazione con
  # tutte le applicazioni Odoo Community. È l'ingresso del dataset di addestramento.
  #
  #   ./manage.sh atlante atlante            # etichette italiane
  #   ./manage.sh atlante atlante en_US      # le stesse entità, etichette inglesi
  #
  # Il documento esce in tools/finetuning/atlante.json, o atlante_<lingua>.json.
  # La seconda raccolta serve al 15% di esempi con catalogo inglese di ai/18 §5bis, e
  # non richiede una banca dati diversa: l'inglese è la lingua sorgente di Odoo.
  local db="${1:?Usage: ./manage.sh atlante <db> [lingua]}"
  local lingua="${2:-}"
  local nome="atlante"
  [ -n "$lingua" ] && nome="atlante_${lingua%%_*}"
  log "Raccolgo l'atlante da '${db}'${lingua:+ in ${lingua}} (una entità per volta, ci vuole qualche minuto)..."
  dc exec -T -e "ATLANTE_LANG=${lingua}" -e "ATLANTE_OUT=/var/lib/odoo/${nome}.json" \
    odoo python3 /opt/odoo/core/odoo-bin shell -c /etc/odoo/odoo.conf \
    -d "$db" --log-level=warn < "${PROJECT_ROOT}/tools/finetuning/atlante.py"
  docker compose --project-name odoo --env-file "$ENV_FILE" \
    -f "${PROJECT_ROOT}/docker-compose.yml" \
    cp "odoo:/var/lib/odoo/${nome}.json" "${PROJECT_ROOT}/tools/finetuning/${nome}.json"
  ok "Atlante in tools/finetuning/${nome}.json"
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

  log "Tests of the dataset generator (fine tuning)..."
  python3 -m unittest discover -s "${PROJECT_ROOT}/tools/finetuning/tests" -t "${PROJECT_ROOT}"
  log "Tests of the dictionary packs..."
  python3 -m unittest discover -s "${PROJECT_ROOT}/tools/dizionario/tests" -t "${PROJECT_ROOT}"
  log "Tests of the field battery's own guard..."
  python3 -m unittest discover -s "${PROJECT_ROOT}/tools/campo/tests" -t "${PROJECT_ROOT}"
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
  local mods="nli_core,nli_semantics,nli_engine,nli_dispatch,nli_web,nli_observability"
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
  dc run --rm odoo "${ODOO_BIN[@]}" -d "$db" -u "$mods" --stop-after-init
  dc up -d odoo
  ok "Upgrade finished."
}

# Load bench for the isolation proof of D27 (05 §7.1).
#
# Brings the stack up on the prefork override — the only configuration in which
# the proof means anything, because RA3 *is* the saturation of the worker pool
# and the dev stack has no pool. Seeds a representative volume, then runs the
# harness. Returning to dev is `./manage.sh start`.
cmd_loadtest() {
  local db="${1:?Usage: ./manage.sh loadtest <db> [users] [seconds]}"
  local users="${2:-20}"
  local seconds="${3:-30}"

  log "Bringing the stack up with prefork workers (docker-compose.load.yml)..."
  docker compose --project-name odoo --env-file "$ENV_FILE" \
    -f "${PROJECT_ROOT}/docker-compose.yml" \
    -f "${PROJECT_ROOT}/docker-compose.load.yml" up -d
  wait_healthy odoo || true

  log "Seeding a representative volume on '${db}'..."
  python3 "${PROJECT_ROOT}/tools/load/popola.py" --db "$db"

  log "Running the isolation harness (${users} users, ${seconds}s)..."
  python3 "${PROJECT_ROOT}/tools/load/prova_isolamento.py" \
    --db "$db" --utenti "$users" --secondi "$seconds"

  warn "The stack is still on the load override. './manage.sh start' returns to ${MODE}."
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

# Rotating POSTGRES_PASSWORD in .env is not enough: the postgres entrypoint only
# applies it when it initialises an empty PGDATA, so an existing db_data volume
# keeps the old password and Odoo would simply fail to authenticate. Apply the
# change inside the running cluster with ALTER ROLE.
cmd_rotate_secrets() {
  confirm "This regenerates POSTGRES_PASSWORD, ODOO_ADMIN_PASSWD and PGADMIN_PASSWORD, and restarts the stack."

  local new_pg new_admin new_pgadmin
  new_pg="$(gen_password)"
  new_admin="$(gen_password)"
  new_pgadmin="$(gen_password)"

  log "Applying the new password to the running PostgreSQL role..."
  dc up -d db >/dev/null
  wait_healthy db 120
  # Passed via stdin, not argv: psql arguments are visible in `ps` output.
  printf "ALTER ROLE %s WITH PASSWORD '%s';\n" "${POSTGRES_USER:-odoo}" "$new_pg" \
    | dc exec -T db psql -v ON_ERROR_STOP=1 -U "${POSTGRES_USER:-odoo}" -d "${POSTGRES_DB:-postgres}" -q \
    || die "ALTER ROLE failed — nothing was rotated, the stack is untouched."

  log "Updating .env, secrets/ and config/odoo.conf..."
  env_set POSTGRES_PASSWORD  "$new_pg"
  env_set ODOO_ADMIN_PASSWD  "$new_admin"
  env_set PGADMIN_PASSWORD   "$new_pgadmin"
  write_secret_file "$PG_PASSWORD_FILE"               "$new_pg"
  write_secret_file "${SECRETS_DIR}/pgadmin_password" "$new_pgadmin"
  render_odoo_conf "$new_admin" "${POSTGRES_USER:-odoo}" "$new_pg"

  log "Recreating containers with the new credentials..."
  dc up -d --force-recreate odoo $( [[ "$MODE" == "dev" ]] && echo pgadmin )
  wait_healthy odoo 240

  ok "Secrets rotated. Values are in .env (mode 600) — not printed here."
  warn "pgAdmin keeps the old login until its data volume is reset:"
  warn "  docker volume rm $(project_name)_pgadmin_data"
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
  loadtest)          cmd_loadtest "$@" ;;
  campo)             cmd_campo "$@" ;;
  ollama)            cmd_ollama "$@" ;;
  dizionario)        cmd_dizionario "$@" ;;
  atlante)           cmd_atlante "$@" ;;
  backup)            cmd_backup "$@" ;;
  restore)           cmd_restore "$@" ;;
  rotate-secrets)    cmd_rotate_secrets "$@" ;;
  cleanup)           cmd_cleanup "$@" ;;
  help|-h|--help)    usage ;;
  *)                 err "Unknown command: '$cmd'"; usage; exit 1 ;;
esac
