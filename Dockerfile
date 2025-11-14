# Usa Debian 12 (Bookworm) come base. Fornisce Python 3.11 nativamente.
FROM debian:bookworm-slim

# 1. Variabili d'ambiente Core
ENV ODOO_VERSION 17.0
ENV ODOO_USER odoo
# Imposta la locale per evitare problemi con la codifica Odoo/PostgreSQL
ENV LANG C.UTF-8
# Variabili per la connessione al DB (Cruciali per entrypoint.sh)
ENV DB_HOST db
ENV DB_PORT 5432
ENV DB_USER odoo_user
ENV DB_PASSWORD odoo_password

# 2. Aggiornamento sistema e installazione dipendenze di sistema (come ROOT)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        # Core Python e Build Tools (Python 3.11 è la versione predefinita)
        python3 python3-pip python3-dev \
        build-essential git \
        # Librerie di compilazione essenziali (lxml, psycopg2, zlib)
        libxml2-dev libxslt1-dev zlib1g-dev \
        libpq-dev postgresql-client \
        # Dipendenze per Pillow (Immagini: risolve molti problemi di allegati)
        libjpeg-dev libpng-dev libfreetype6-dev liblcms2-dev libwebp-dev \
        # Dipendenze per python-ldap (RISOLVE L'ERRORE 'sasl/sasl.h')
        libldap2-dev libsasl2-dev \
        # Altre dipendenze utili (libtiff per Pillow) e librerie X11 per wkhtmltopdf
        libtiff-dev libxext6 libxrender1 xfonts-base xfonts-75dpi \
    && rm -rf /var/lib/apt/lists/*

# 3. Installazione di WKHTMLTOPDF per la generazione di PDF
# Usiamo la versione 0.12.5-1 (più stabile e compatibile) con la tecnica "fix broken"
RUN apt-get update && apt-get install -y wget \
    && wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.5-1/wkhtmltox_0.12.5-1.bullseye_amd64.deb \
    # Tentiamo l'installazione che fallirà, ma ci serve per registrare le dipendenze
    && dpkg -i wkhtmltox_0.12.5-1.bullseye_amd64.deb || true \
    # Usiamo apt-get -f install per forzare l'installazione delle dipendenze mancanti
    && apt-get install -y -f \
    && rm -f wkhtmltox_0.12.5-1.bullseye_amd64.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Installazione Dipendenze Python Odoo Core e Custom
# Deve usare --break-system-packages per bypassare il blocco PEP 668 di Bookworm
COPY ./src/requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade pip setuptools wheel --break-system-packages \
    && pip3 install -r /tmp/requirements.txt --break-system-packages \
    && pip3 install openpyxl requests --break-system-packages \
    && rm -f /tmp/requirements.txt

# 5. Creazione dell'utente e delle directory di Odoo
RUN adduser --system --group --home=/opt/odoo ${ODOO_USER}
# Crea tutte le cartelle necessarie (addons, dati, configurazione) e imposta i permessi
RUN mkdir -p /mnt/extra-addons /var/lib/odoo /etc/odoo \
    && chown -R ${ODOO_USER}:${ODOO_USER} /mnt/extra-addons /var/lib/odoo /etc/odoo

# 6. Copia del codice sorgente di Odoo e dei file di configurazione
COPY ./src /opt/odoo/src 
COPY ./custom_addons /mnt/extra-addons
# Assicurati che il file di configurazione sia presente
COPY ./config/odoo.conf /etc/odoo/odoo.conf

# 7. Setup dei permessi del codice Odoo (assicura che l'utente odoo possa leggere tutto)
RUN chown -R ${ODOO_USER}:${ODOO_USER} /opt/odoo \
    && chown -R ${ODOO_USER}:${ODOO_USER} /mnt/extra-addons \
    && chown ${ODOO_USER}:${ODOO_USER} /etc/odoo/odoo.conf

# 8. Esposizione della porta
EXPOSE 8069 8072

# 9. Aggiungi e rendi eseguibile lo script di entrypoint (DEVE ESSERE FATTO PRIMA DI CAMBIARE UTENTE)
# Nota: assumiamo che entrypoint.sh sia nella stessa directory del Dockerfile
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Switch all'utente non-root per l'esecuzione
USER ${ODOO_USER}
WORKDIR /opt/odoo/src

# 10. ENTRYPOINT e CMD
# Usa ENTRYPOINT per eseguire lo script di attesa che bloccherà l'avvio di Odoo finché il DB non è pronto
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# CMD passerà gli argomenti a entrypoint.sh
CMD ["-i", "base", "--without-demo", "all"]
