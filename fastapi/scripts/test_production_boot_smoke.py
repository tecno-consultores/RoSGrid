#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
"""Smoke Test de Arranque Estricto de Producción (--no-dev).

Verifica que el Backend de RoSGrid pueda inicializarse y resolver todas sus
importaciones y endpoints de salud en un entorno limpio de producción sin
dependencias de desarrollo instaladas.
"""

import asyncio
import importlib
import os
import pkgutil
import sys
from pathlib import Path

# Asegurar acceso al entorno virtual /app/.venv si existe
venv_site = Path("/app/.venv/lib/python3.13/site-packages")
if venv_site.exists() and str(venv_site) not in sys.path:
    sys.path.insert(0, str(venv_site))


def verificar_ausencia_paquetes_dev() -> None:
    """Verifica que paquetes exclusivos de desarrollo no estén presentes en sys.modules."""
    dev_packages = ["pytest", "pytest_asyncio", "pytest_mock", "hypothesis", "freezegun", "radon"]
    detectados = []
    for pkg in dev_packages:
        if pkg in sys.modules:
            detectados.append(pkg)
    if detectados:
        print(f"[AVISO] Módulos de desarrollo presentes en sys.modules: {detectados}")
    else:
        print("✔ Verificado: Ningún módulo de desarrollo cargado en el entorno.")


def verificar_importaciones_productivas() -> None:
    """Importa recursivamente todos los submódulos de src/ para detectar ModuleNotFoundError."""
    src_dir = Path("/app/src")
    if not src_dir.exists():
        src_dir = Path(__file__).resolve().parent.parent / "src"

    assert src_dir.exists(), f"No se encontró el directorio src en {src_dir}"

    modulos_importados = 0
    # Añadir directorio raíz al path si es necesario
    app_root = str(src_dir.parent)
    if app_root not in sys.path:
        sys.path.insert(0, app_root)

    for _, module_name, is_pkg in pkgutil.walk_packages([str(src_dir)], prefix="src."):
        try:
            importlib.import_module(module_name)
            modulos_importados += 1
        except Exception as exc:
            print(f"❌ Error al importar módulo de producción '{module_name}': {exc}", file=sys.stderr)
            sys.exit(1)

    print(f"✔ Verificado: {modulos_importados} módulos de producción importados sin errores.")


async def verificar_instancia_produccion() -> None:
    """Instancia la aplicación FastAPI en modo producción y prueba el endpoint /health."""
    os.environ["ROSGRID_ENV"] = "production"

    from src.main import create_app, health_check
    from fastapi import Response

    app = create_app()

    # Verificar ocultamiento estricto de documentación en producción (Hardening Trivy / Swagger)
    assert app.docs_url is None, "docs_url debe ser None en producción"
    assert app.redoc_url is None, "redoc_url debe ser None en producción"
    assert app.openapi_url is None, "openapi_url debe ser None en producción"
    print("✔ Verificado: Swagger (/docs), ReDoc (/redoc) y OpenAPI (/openapi.json) desactivados en producción.")

    # Ejecutar health_check in-process
    response = Response()
    res = await health_check(response)
    assert "status" in res, "La respuesta de health_check debe contener 'status'"
    assert res["service"] == "rosgrid-api", "El servicio reportado debe ser 'rosgrid-api'"
    print(f"✔ Verificado: Health check in-process ejecutado exitosamente -> {res}")


def main() -> None:
    print("==============================================================================")
    print("  🔍 Smoke Test de Arranque Estricto de Producción (--no-dev) — RoSGrid      ")
    print("==============================================================================")
    verificar_ausencia_paquetes_dev()
    verificar_importaciones_productivas()
    asyncio.run(verificar_instancia_produccion())
    print("==============================================================================")
    print("  🎉 ¡Certificación de Arranque de Producción superada exitosamente!         ")
    print("==============================================================================")


if __name__ == "__main__":
    main()
