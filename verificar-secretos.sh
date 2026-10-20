#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
# Propósito: Detección preventiva de credenciales y secretos hardcodeados en archivos staged.

LC_ALL=C
set -euo pipefail

if [ "$#" -eq 0 ]; then
  exit 0
fi

# Busca patrones comunes de contraseñas, llaves y tokens hardcodeados
if grep -qiE "(password|secret|api_key|token)[=:] *[\"'][a-zA-Z0-9]{8,}[\"']" "$@"; then
  echo "🚨 ERROR: Posible secreto hardcodeado detectado en los archivos modificados." >&2
  exit 1
fi

exit 0
