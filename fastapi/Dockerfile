# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
FROM sinfallas/base-python-uv:3.15

ARG BUILD_DATE="unknown"
LABEL org.opencontainers.image.title="RoSGrid Backend API & Workers" \
      org.opencontainers.image.description="Backend Multi-Tenant para Flotas MikroTik RouterOS v7+" \
      org.opencontainers.image.authors="Sinfallas <sinfallas@yahoo.com>" \
      org.opencontainers.image.licenses="GPL-3.0-only" \
      org.opencontainers.image.created="${BUILD_DATE}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ROSGRID_IMAGE_PREBUILT=1 \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

# Crear usuario y grupo sin privilegios (Cumplimiento Trivy DS002)
RUN groupadd -g 10001 rosgrid && \
    useradd -u 10001 -g rosgrid -m -s /usr/sbin/nologin rosgrid && \
    mkdir -p /var/lib/rosgrid/backups && \
    chown -R rosgrid:rosgrid /app /var/lib/rosgrid

# Copiar archivos de configuración y código fuente
COPY --chown=rosgrid:rosgrid pyproject.toml uv.lock alembic.ini ./
COPY --chown=rosgrid:rosgrid migrations ./migrations
COPY --chown=rosgrid:rosgrid scripts ./scripts
COPY --chown=rosgrid:rosgrid src ./src

# Sincronizar e instalar todas las dependencias de producción con uv respetando uv.lock
RUN chmod +x /app/scripts/*.sh /app/scripts/*.py && \
    uv sync --frozen --no-dev --compile-bytecode

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD ["curl", "-fsS", "http://127.0.0.1:8000/health"]

ENTRYPOINT ["/usr/bin/env", "bash", "/app/scripts/entrypoint.sh"]
