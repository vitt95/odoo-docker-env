# Odoo 18 — Dockerized stack

Professional, reproducible Docker infrastructure for **Odoo 18 (Community)** +
**PostgreSQL 16**, with separate **development** and **production** modes driven
by a single bootstrap script.

```bash
./install.sh dev     # development: hot-reload, debug logs, pgAdmin
./install.sh prod    # production:  workers, resource limits, hardened
```

Clone on any Linux host with Docker installed and run one of the commands above —
no file needs to be edited by hand. Secrets are generated automatically into
`.env` on first run.

---

## Requirements

- Docker Engine + **Docker Compose v2** plugin (`docker compose`)
- `openssl` (secret generation), `bash`, `sed`, `grep`
- Linux recommended for `prod`

---

## Architecture

| Component   | Choice                          | Why |
|-------------|---------------------------------|-----|
| Odoo core   | Official `odoo:18.0` image + thin `Dockerfile` | Upstream ships deps + wkhtmltopdf; tiny, upgradable |
| Database    | `postgres:16-alpine`            | Max version officially supported by Odoo 18 |
| Config      | `odoo.conf.template` → rendered `odoo.conf` | Single source; secrets injected from `.env`, never committed |
| Modes       | `docker-compose.{dev,prod}.yml` overrides | One base file, per-mode flags via `command:` (DRY) |
| Secrets     | `.env` (gitignored, auto-generated) | No credentials in the repo |
| Networking  | dedicated bridge `odoo_net`     | Isolated; DB not exposed in prod |
| Persistence | named volumes `db_data`, `odoo_filestore` | Survive recreation |
| Health      | `pg_isready` + `GET /web/health`; `depends_on: service_healthy` | Ordered, verified startup |
| Logging     | stdout + `json-file` rotation (10m × 3) | 12-factor, bounded disk |

### DEV vs PROD

| Aspect        | DEV                                  | PROD |
|---------------|--------------------------------------|------|
| Source        | addons bind-mounted (`./custom_addons`) | mounted read-only |
| Reload        | `--dev=reload,qweb,xml`, `--log-level=debug` | workers, `--log-level=info` |
| Odoo workers  | threaded (0)                         | `--workers=$ODOO_WORKERS` + limits |
| Exposure      | `0.0.0.0` ports, Postgres on host    | `127.0.0.1` only (reverse proxy), DB internal |
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

- `.env`, `config/odoo.conf` and `*.pem` are gitignored — never commit them.
- Passwords are generated with `openssl rand` on first install.
- In prod the database has no host port and Odoo is loopback-only.
