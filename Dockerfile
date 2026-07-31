# =============================================================================
# Thin layer on top of the official Odoo image.
# Rationale: the upstream image already ships all Python deps and wkhtmltopdf.
# The stack runs Odoo from the ./core source bind-mount, but the interpreter
# and every dependency come from this image — so the image tag and the core
# branch must stay on the same series (both driven from .env).
#
# No apt layer: the healthcheck uses the interpreter already present, which
# keeps the build offline-friendly, smaller, and identical on amd64/arm64.
# =============================================================================
ARG ODOO_IMAGE_TAG=18.0
FROM odoo:${ODOO_IMAGE_TAG}

# Root needed to install python packages.
USER root

# Extra Python deps for custom addons. File is version-controlled and may be
# empty; the layer is skipped entirely in that case (Debian/Ubuntu -> PEP 668).
COPY config/requirements.txt /tmp/requirements.txt
RUN if [ -s /tmp/requirements.txt ]; then \
        pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt ; \
    fi \
    && rm -f /tmp/requirements.txt

# Drop back to the unprivileged user shipped by the base image.
USER odoo
