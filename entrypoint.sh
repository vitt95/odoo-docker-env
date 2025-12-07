#!/bin/bash
set -e

# ----------------------------
# Variabili di connessione DB
# ----------------------------
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-supersecret}

export PGPASSWORD=$DB_PASSWORD

# Comando di avvio Odoo
ODOO_CMD="python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf"

echo "Checking PostgreSQL availability..."

# Loop di attesa finché PostgreSQL non è pronto
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
    echo "Waiting for PostgreSQL..."
    sleep 1
done

echo "PostgreSQL is ready."

echo "Starting Odoo..."
# Avvia Odoo definitivamente
exec $ODOO_CMD
