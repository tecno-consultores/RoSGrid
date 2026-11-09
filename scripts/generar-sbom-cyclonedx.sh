#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
# Generador automatizado de Software Bill of Materials (SBOM) CycloneDX 1.5 (OWASP DevGuide 5.3.4 / DISA STIG V-222658)

LC_ALL=C
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${ROOT_DIR}/docs/sbom"
mkdir -p "${OUT_DIR}"

echo "[SBOM] Generando CycloneDX SBOM para Backend (FastAPI) y Frontend (Vue 3) en contenedor efímero Trivy..."
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "${ROOT_DIR}:/workspace:ro" \
  -v "${OUT_DIR}:/out" \
  aquasec/trivy:latest fs --format cyclonedx --output /out/rosgrid-sbom.cdx.json /workspace

echo "[OK] SBOM CycloneDX generado en docs/sbom/rosgrid-sbom.cdx.json"
