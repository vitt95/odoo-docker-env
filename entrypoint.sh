#!/bin/bash
set -e

# Variabili di connessione al database
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-odoo_db}
DB_USER=${DB_USER:-odoo_user}
DB_PASSWORD=${DB_PASSWORD:-odoo_password}

# Variabile per il comando di avvio base (di default, solo l'esecuzione)
ODOO_START_CMD="python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf"

# Tempo massimo di attesa per il database (in secondi)
MAX_WAIT=30
CURRENT_WAIT=0

echo "PostgreSQL check: Host=$DB_HOST, Port=$DB_PORT, Database=$DB_NAME"

# Funzione per verificare lo stato di PostgreSQL
wait_for_postgres() {
    # Utilizza il client PostgreSQL per verificare la connessione
    pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1
    return $?
}

# Funzione per controllare se il database Odoo esiste
db_exists() {
    # Prova a connettersi al database specifico e verifica l'esistenza
    # del database Odoo. Se fallisce, il DB non esiste o non è pronto.
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -w "$DB_NAME" > /dev/null 2>&1
    return $?
}

# Loop per attendere che PostgreSQL sia pronto
while ! wait_for_postgres && [ $CURRENT_WAIT -lt $MAX_WAIT ]; do
    echo "Waiting for PostgreSQL ($DB_HOST:$DB_PORT)... $CURRENT_WAIT/$MAX_WAIT seconds"
    sleep 1
    CURRENT_WAIT=$((CURRENT_WAIT+1))
done

if [ $CURRENT_WAIT -ge $MAX_WAIT ]; then
    echo "Error: Database connection timed out after $MAX_WAIT seconds."
    exit 1
fi

echo "PostgreSQL is up and running!"

# -------------------------------------------------------------
# LOGICA DI INIZIALIZZAZIONE DEL DATABASE
# -------------------------------------------------------------

# Se il database NON esiste, prepariamo il comando per CREARLO e installare i moduli.
if ! db_exists; then
    echo "Database '$DB_NAME' not found. Preparing to create and initialize the database."
    # Aggiungiamo i parametri di inizializzazione (-i base, --without-demo all)
    # L'opzione --stop-after-init garantisce che Odoo termini subito dopo aver creato il DB.
    INIT_ARGS="-d $DB_NAME -i base --without-demo all --stop-after-init"
    
    # Eseguiamo il comando di inizializzazione
    echo "Executing initialization command: $ODOO_START_CMD $INIT_ARGS"
    # Nota: Utilizziamo il master password solo per questa operazione
    $ODOO_START_CMD --db_user "$DB_USER" --db_password "$DB_PASSWORD" --db_host "$DB_HOST" $INIT_ARGS
    
    # Se l'inizializzazione è andata bene, Odoo è terminato (grazie a --stop-after-init)
    echo "Database initialized successfully. Starting Odoo in normal mode..."
fi

# -------------------------------------------------------------
# ESECUZIONE FINALE DI ODOO
# -------------------------------------------------------------

# Passa il controllo al comando finale di Odoo (il CMD del Dockerfile)
# Assumiamo che il CMD sia il comando di avvio principale (es. [])
echo "Starting Odoo server with configuration."

# Se il primo argomento è un flag (-*), assumiamo che l'utente voglia
# eseguire odoo-bin con i parametri passati dal CMD del Dockerfile
if [ "${1:0:1}" = '-' ]; then
    # Esegue odoo-bin in modalità normale, passando il file di configurazione e tutti gli argomenti (CMD)
    exec $ODOO_START_CMD "$@"
fi

# Altrimenti, esegue il comando passato (utile per debug/shell)
exec "$@"
