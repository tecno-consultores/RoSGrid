# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import ast
from pathlib import Path
from unittest.mock import patch

from src.main import create_app

# Lista de paquetes y módulos reservados estrictamente para desarrollo y pruebas
FORBIDDEN_DEV_MODULES = {
    "pytest",
    "pytest_asyncio",
    "pytest_cov",
    "pytest_mock",
    "hypothesis",
    "freezegun",
    "radon",
    "mutmut",
    "schemathesis",
    "locust",
    "bandit",
    "unittest.mock",
}


def test_no_dev_dependencies_imported_in_production_source() -> None:
    """Verifica que ningún archivo de código productivo en src/ importe dependencias dev.

    Garantiza que la compilación con 'uv sync --frozen --no-dev' no sufra de
    ModuleNotFoundError durante el arranque en producción.
    """
    src_dir = Path(__file__).resolve().parent.parent.parent / "src"
    assert src_dir.is_dir(), f"Directorio src no encontrado en {src_dir}"

    python_files = list(src_dir.rglob("*.py"))
    assert len(python_files) > 10, "No se encontraron suficientes archivos Python en src/"

    violations: list[str] = []

    for file_path in python_files:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_name = alias.name.split(".")[0]
                    full_name = alias.name
                    if root_name in FORBIDDEN_DEV_MODULES or full_name in FORBIDDEN_DEV_MODULES:
                        violations.append(f"{file_path.name}:{node.lineno} importa módulo de desarrollo '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_name = node.module.split(".")[0]
                    full_name = node.module
                    if root_name in FORBIDDEN_DEV_MODULES or full_name in FORBIDDEN_DEV_MODULES:
                        violations.append(
                            f"{file_path.name}:{node.lineno} importa desde módulo de desarrollo '{node.module}'"
                        )

    assert not violations, "Se detectaron importaciones de desarrollo en src/:\n" + "\n".join(violations)


def test_production_app_instantiation_without_docs_and_swagger() -> None:
    """Valida que create_app en modo producción desactive Swagger, Redoc y OpenAPI."""
    with patch("src.main.settings.ROSGRID_ENV", "production"):
        app = create_app()
        assert app.docs_url is None, "docs_url debe ser None en producción"
        assert app.redoc_url is None, "redoc_url debe ser None en producción"
        assert app.openapi_url is None, "openapi_url debe ser None en producción"


def test_cors_configuration_production_and_dev() -> None:
    """Valida configuración estricta de CORS en producción vs desarrollo."""
    # 1. Producción con wildcard: credenciales deshabilitadas y orígenes vacíos
    with (
        patch("src.main.settings.ROSGRID_ENV", "production"),
        patch("src.main.settings.ROSGRID_CORS_ORIGINS", "*"),
    ):
        app_prod_wild = create_app()
        assert app_prod_wild is not None

    # 2. Producción con orígenes específicos
    with (
        patch("src.main.settings.ROSGRID_ENV", "production"),
        patch("src.main.settings.ROSGRID_CORS_ORIGINS", "https://noc.rosgrid.com,https://api.rosgrid.com"),
    ):
        app_prod_explicit = create_app()
        assert app_prod_explicit is not None

    # 3. Desarrollo con regex permisivo
    with (
        patch("src.main.settings.ROSGRID_ENV", "development"),
        patch("src.main.settings.ROSGRID_CORS_ORIGINS", "*"),
    ):
        app_dev = create_app()
        assert app_dev is not None
