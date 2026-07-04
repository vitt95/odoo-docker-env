# =============================================================================
# Thin layer on top of the official Odoo image.
# Rationale: the upstream image already ships Odoo core, all Python deps and
# wkhtmltopdf. We only add curl (healthcheck) and any extra Python packages
# required by custom addons. Keeps the image small and trivially upgradable.
# =============================================================================
ARG ODOO_IMAGE_TAG=18.0
FROM odoo:${ODOO_IMAGE_TAG}

# Root needed to install system/python packages.
USER root

# curl: used by the container healthcheck (GET /web/health).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Extra Python deps for custom addons. File is version-controlled and may be
# empty; the layer is skipped entirely in that case (Debian 12 -> PEP 668).
COPY config/requirements.txt /tmp/requirements.txt
RUN if [ -s /tmp/requirements.txt ]; then \
        pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt ; \
    fi \
    && rm -f /tmp/requirements.txt

# Drop back to the unprivileged user shipped by the base image.
USER odoo
