#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)
# Propósito: Detección preventiva de credenciales y secretos hardcodeados en archivos productivos.

LC_ALL=C
set -euo pipefail

FILES_TO_SCAN=()
if [ "$#" -gt 0 ]; then
  RAW_FILES=("$@")
else
  mapfile -t RAW_FILES < <(git ls-files 2>/dev/null || true)
fi

for f in "${RAW_FILES[@]}"; do
  [ -f "$f" ] || continue
  case "$f" in
    docs/*|*/tests/*|*.unit.py|*.unit.ts|*.feature|*.feature.example|*/graphify-out/*|graphify-out/*)
      continue
      ;;
  esac
  FILES_TO_SCAN+=("$f")
done

if [ "${#FILES_TO_SCAN[@]}" -eq 0 ]; then
  exit 0
fi

# Busca patrones comunes de contraseñas, llaves y tokens hardcodeados
if grep -qiE "(password|secret|api_key|token)[=:] *[\"'][a-zA-Z0-9]{8,}[\"']" "${FILES_TO_SCAN[@]}"; then
  echo "🚨 ERROR: Posible secreto hardcodeado detectado en los archivos modificados." >&2
  exit 1
fi

exit 0
