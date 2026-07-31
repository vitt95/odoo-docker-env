# Odoo 18 — Dockerized stack

Professional, reproducible Docker infrastructure for **Odoo 18 (Community)** +
**PostgreSQL 16**, with separate **development** and **production** modes driven
by a single bootstrap script.

```bash
./install.sh dev     # development: hot-reload, debug logs, pgAdmin
./install.sh prod    # production:  workers, resource limits, hardened
```

Clone on any host with Docker installed — Linux or macOS, amd64 or arm64 — and
run one of the commands above. No file needs to be edited by hand: `install.sh`
clones the Odoo source, generates every secret and renders the config.

> **First run downloads the Odoo source** (`./core`, ~1.2 GB shallow clone of
> `odoo/odoo` at `ODOO_SOURCE_BRANCH`). Subsequent runs reuse it; refresh it
> with `./install.sh dev --update-core`.

---

## Requirements

- Docker Engine + **Docker Compose v2** plugin (`docker compose`)
- `git` (clones the Odoo source), `openssl` (secret generation), `bash`, `sed`, `grep`
- Linux recommended for `prod`
- Architecture: amd64 and arm64 both work — every base image is multi-arch and
  no `platform:` is pinned, so containers run natively on either.

---

## Architecture

| Component   | Choice                          | Why |
|-------------|---------------------------------|-----|
| Odoo runtime| Official `odoo:18.0` image + thin `Dockerfile` | Supplies the interpreter, every Python dep and wkhtmltopdf |
| Odoo code   | `./core` — shallow clone of `odoo/odoo`, bind-mounted read-only at `/opt/odoo/core` | Core sources readable and hot-reloadable during UI work |
| Database    | `postgres:16-alpine`            | Max version officially supported by Odoo 18 |
| Config      | `odoo.conf.template` → rendered `odoo.conf` | Single source; secrets injected from `.env`, never committed |
| Modes       | `docker-compose.{dev,prod}.yml` overrides | One base file, per-mode flags via `command:` (DRY) |
| Secrets     | `.env` + `secrets/` (both mode 600, gitignored) | Never in the repo, never in the container environment |
| Networking  | dedicated bridge `odoo_net`     | Isolated; DB not exposed in prod |
| Persistence | named volumes `db_data`, `odoo_filestore` | Survive recreation |
| Health      | `pg_isready` + `GET /web/health`; `depends_on: service_healthy` | Ordered, verified startup |
| Logging     | stdout + `json-file` rotation (10m × 3) | 12-factor, bounded disk |

`ODOO_SOURCE_BRANCH` and `ODOO_IMAGE_TAG` must stay on the same series — the
image provides the dependencies that the source is executed against.
`install.sh` warns when they drift.

### DEV vs PROD

| Aspect        | DEV                                  | PROD |
|---------------|--------------------------------------|------|
| Source        | addons bind-mounted (`./custom_addons`) | mounted read-only |
| Reload        | `--dev=reload,qweb,xml`, `--log-level=debug` | workers, `--log-level=info` |
| Odoo workers  | threaded (0)                         | `--workers=$ODOO_WORKERS` + limits |
| Exposure      | `127.0.0.1` only (Odoo, Postgres, pgAdmin) | `127.0.0.1` only (reverse proxy), DB internal |
| pgAdmin       | included (`:5050`)                   | absent |
| DB listing    | enabled                              | `--no-database-list` |
| Restart       | `unless-stopped`                     | `always` |

> **Prod note:** Odoo binds to `127.0.0.1` and runs with `--proxy-mode`. Put a
> reverse proxy (Nginx/Traefik/Caddy) in front to terminate TLS.

---

## Directory layout

```
.
├── install.sh                 # one-command bootstrap (dev|prod)
├── manage.sh                  # day-2 operations CLI
├── docker-compose.yml         # base stack
├── docker-compose.dev.yml     # dev override
├── docker-compose.prod.yml    # prod override
├── Dockerfile                 # thin layer over odoo:18
├── .env.example               # template (copied to .env, gitignored)
├── .dockerignore              # keeps .env/secrets/core out of the build context
├── secrets/                   # file-backed Docker secrets (mode 600, gitignored)
├── core/                      # Odoo source, cloned by install.sh (gitignored)
├── config/
│   ├── odoo.conf.template     # committed, no secrets
│   ├── requirements.txt       # extra pip deps for custom addons
│   └── pgadmin/servers.json   # pgAdmin pre-registered server (dev)
├── scripts/lib.sh             # shared bash helpers
├── custom_addons/             # your modules
├── enterprise/                # optional enterprise addons (mounted if present)
├── logs/  backups/  docs/
```

---

## Management CLI

```bash
./manage.sh status               # containers, health, URLs
./manage.sh logs [svc]           # tail logs (follow)
./manage.sh shell [svc]          # bash into a container (default: odoo)
./manage.sh psql [db]            # psql session
./manage.sh odoo-shell <db>      # Odoo python shell
./manage.sh update               # pull/rebuild images, recreate
./manage.sh upgrade <db> [mods]  # upgrade modules (default: all)
./manage.sh backup               # dump all DBs + filestore -> ./backups
./manage.sh restore <timestamp>  # restore a backup (destructive)
./manage.sh rotate-secrets       # regenerate all passwords and apply them live
./manage.sh cleanup [--all]      # remove containers (--all also volumes)
./manage.sh start|stop|restart
```

### Backup / restore

```bash
./manage.sh backup
# -> backups/db_20260630_140000.sql.gz
# -> backups/filestore_20260630_140000.tar.gz

./manage.sh restore 20260630_140000   # asks for explicit confirmation
```

---

## Switching modes

Re-run the installer with the other mode; it reuses `.env` and re-renders config:

```bash
./manage.sh stop
./install.sh prod
```

## Enterprise addons (optional)

Place an enterprise checkout under `enterprise/` — it is mounted at
`/mnt/enterprise` and already on the `addons_path`. Empty by default; nothing is
downloaded (a valid Odoo Enterprise subscription is required).

## Custom Python deps

Add packages to `config/requirements.txt`, then `./manage.sh update`.

---

## Security notes

- **No secret is ever an environment variable.** Postgres and pgAdmin read their
  passwords from file-backed Docker secrets (`/run/secrets/*`), and Odoo reads
  its credentials from `config/odoo.conf`. Nothing sensitive shows up in
  `docker inspect`, `docker compose config` or `/proc/<pid>/environ`.
- `.env`, `config/odoo.conf` and everything in `secrets/` are mode 600 and
  gitignored. `install.sh` never echoes a generated password to the terminal —
  read them from `.env`, rotate them with `./manage.sh rotate-secrets`.
- **Adding a path to `.gitignore` does not untrack an already-committed file.**
  `config/odoo.conf` was tracked with live credentials until it was purged from
  history; check with `git ls-files | grep -E 'odoo\.conf|\.env'` before
  trusting the ignore list.
- All host ports bind to `127.0.0.1` in both modes — nothing is offered to the
  local network. In prod the database has no host port at all.
- The Werkzeug debugger is deliberately not enabled in dev (`--dev=reload,qweb,xml`,
  no `werkzeug`): it turns any traceback page into remote code execution.
- Containers run with `no-new-privileges`.
- Passwords are generated with `openssl rand` on first install.
- If a credential ever reaches a commit: rotate it *and* purge it from history.
  Rotation alone is not enough (clones and forks keep the old object), and a
  purge alone is not enough (GitHub may retain unreferenced objects).
