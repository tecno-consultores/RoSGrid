# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# --- Etapa 1: Compilación de la SPA Vue 3 + TypeScript ---
FROM sinfallas/base-node-ionic:26 AS builder

WORKDIR /app

COPY package.json .npmrc ./
RUN pnpm install --frozen-lockfile=false

COPY . .
RUN pnpm run build

# --- Etapa 2: Servidor Nginx Endurecido (Non-Root) ---
FROM nginx:1.27-alpine

ARG BUILD_DATE="unknown"
LABEL org.opencontainers.image.title="RoSGrid Frontend UI" \
      org.opencontainers.image.description="Consola WebFig Multi-Tenant y Wallboard NOC para MikroTik RouterOS v7+" \
      org.opencontainers.image.authors="Sinfallas <sinfallas@yahoo.com>" \
      org.opencontainers.image.licenses="GPL-3.0-only" \
      org.opencontainers.image.created="${BUILD_DATE}"

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

# Ajustar permisos para ejecución sin root (Cumplimiento Trivy DS002)
RUN chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

USER 101:101

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/"]

CMD ["nginx", "-g", "daemon off;"]
