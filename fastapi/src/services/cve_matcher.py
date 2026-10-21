# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from src.core.config import settings
from src.schemas.cve import CveItem, CveSyncResponse, FleetCveSummary, RouterCveEvaluation

logger = logging.getLogger(__name__)

_CATALOG_PATH = Path(__file__).parent.parent / "data" / "cve_catalog_ros.json"
_CACHED_CATALOG: list[CveItem] | None = None


def parse_ros_version(version_str: str | None) -> tuple[int, int, int] | None:
    """Parsea una cadena de versión de RouterOS a una tupla (major, minor, patch)."""
    if not version_str:
        return None
    clean = version_str.strip().lower().lstrip("v")
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", clean)
    if not match:
        return None
    major = int(match.group(1))
    minor = int(match.group(2) or 0)
    patch = int(match.group(3) or 0)
    return (major, minor, patch)


def compare_ros_versions(v1: tuple[int, int, int], op: str, v2: tuple[int, int, int]) -> bool:
    """Evalúa un operador de comparación entre dos versiones de RouterOS."""
    if op == ">=":
        return v1 >= v2
    if op == "<=":
        return v1 <= v2
    if op == ">":
        return v1 > v2
    if op == "<":
        return v1 < v2
    if op == "==":
        return v1 == v2
    return False


def _check_single_clause(target: tuple[int, int, int], clause: str) -> bool:
    """Verifica una única cláusula de versión como '>=7.0.0' o '<7.9.2'."""
    clause = clause.strip()
    match = re.match(r"^(>=|<=|>|<|==)?\s*(\d+(?:\.\d+)*)$", clause)
    if not match:
        return False
    op = match.group(1) or "=="
    ver = parse_ros_version(match.group(2))
    if not ver:
        return False
    return compare_ros_versions(target, op, ver)


def is_version_affected(version_str: str | None, expr: str) -> bool:
    """Determina si una versión de RouterOS está afectada por una expresión de rango."""
    target = parse_ros_version(version_str)
    if not target:
        return False
    clauses = [c.strip() for c in expr.split(",") if c.strip()]
    return all(_check_single_clause(target, clause) for clause in clauses)


def load_cve_catalog(force_reload: bool = False) -> list[CveItem]:
    """Carga el catálogo local de CVEs desde el fichero JSON embebido."""
    global _CACHED_CATALOG
    if _CACHED_CATALOG is not None and not force_reload:
        return _CACHED_CATALOG

    if not _CATALOG_PATH.exists():
        logger.warning("Catálogo CVE no encontrado en %s", _CATALOG_PATH)
        return []

    try:
        raw_data = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
        items = [CveItem(**item) for item in raw_data]
        _CACHED_CATALOG = items
        return items
    except Exception as exc:
        logger.error("Error al cargar catálogo CVE: %s", exc)
        return []


def _calculate_highest_fixed_version(vulnerabilities: list[CveItem]) -> str | None:
    """Encuentra la versión mínima requerida para solventar todas las vulnerabilidades."""
    if not vulnerabilities:
        return None
    highest_tuple: tuple[int, int, int] = (0, 0, 0)
    highest_str: str | None = None
    for item in vulnerabilities:
        parsed = parse_ros_version(item.fixed_in_version)
        if parsed and parsed > highest_tuple:
            highest_tuple = parsed
            highest_str = item.fixed_in_version
    return highest_str


def evaluate_router_cves(
    router_id: uuid.UUID,
    display_name: str,
    ros_version: str | None,
    catalog: list[CveItem] | None = None,
) -> RouterCveEvaluation:
    """Evalúa un router específico contra el catálogo local de CVEs."""
    active_catalog = catalog if catalog is not None else load_cve_catalog()
    matching: list[CveItem] = []
    crit = high = med = 0
    max_cvss = 0.0

    for cve in active_catalog:
        if is_version_affected(ros_version, cve.affected_versions_expr):
            matching.append(cve)
            if cve.severity == "CRITICAL":
                crit += 1
            elif cve.severity == "HIGH":
                high += 1
            elif cve.severity == "MEDIUM":
                med += 1
            if cve.cvss_score > max_cvss:
                max_cvss = cve.cvss_score

    recommended = _calculate_highest_fixed_version(matching)

    return RouterCveEvaluation(
        router_id=router_id,
        display_name=display_name,
        ros_version=ros_version,
        total_vulnerabilities=len(matching),
        critical_count=crit,
        high_count=high,
        medium_count=med,
        max_cvss_score=max_cvss,
        vulnerabilities=matching,
        recommended_target_version=recommended,
    )


def evaluate_fleet_cves(
    routers_data: list[dict[str, Any]],
    catalog: list[CveItem] | None = None,
) -> FleetCveSummary:
    """Evalúa el inventario completo de routers del tenant contra el catálogo CVE."""
    active_catalog = catalog if catalog is not None else load_cve_catalog()
    vulnerable_list: list[RouterCveEvaluation] = []
    unique_cves: set[str] = set()
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    crit_routers = high_routers = 0

    for r in routers_data:
        ev = evaluate_router_cves(
            router_id=r["id"],
            display_name=r["display_name"],
            ros_version=r.get("ros_version"),
            catalog=active_catalog,
        )
        if ev.total_vulnerabilities > 0:
            vulnerable_list.append(ev)
            if ev.critical_count > 0:
                crit_routers += 1
            if ev.high_count > 0:
                high_routers += 1
            for v in ev.vulnerabilities:
                unique_cves.add(v.cve_id)
                severity_counts[v.severity] = severity_counts.get(v.severity, 0) + 1

    return FleetCveSummary(
        total_evaluated_routers=len(routers_data),
        vulnerable_routers_count=len(vulnerable_list),
        critical_routers_count=crit_routers,
        high_routers_count=high_routers,
        total_unique_cves=len(unique_cves),
        summary_by_severity=severity_counts,
        vulnerable_routers=vulnerable_list,
        timestamp=datetime.now(timezone.utc),
    )


async def sync_cve_catalog(feed_url: str | None = None) -> CveSyncResponse:
    """Descarga y sincroniza el catálogo de vulnerabilidades desde el feed oficial o remoto."""
    global _CACHED_CATALOG
    url: str = str(
        feed_url or getattr(settings, "ROSGRID_CVE_FEED_URL", "https://services.nvd.nist.gov/rest/json/cves/2.0")
    )
    now_utc = datetime.now(timezone.utc)
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                raw_data = resp.json()
                items = [CveItem.model_validate(x) for x in raw_data] if isinstance(raw_data, list) else []
                if items:
                    _CACHED_CATALOG = items
                    try:
                        _CATALOG_PATH.write_text(
                            json.dumps([i.model_dump() for i in items], indent=2), encoding="utf-8"
                        )
                    except OSError:
                        pass
                    return CveSyncResponse(
                        success=True,
                        source_url=url,
                        total_cves=len(items),
                        updated_at=now_utc,
                        message=f"Catálogo de CVEs actualizado exitosamente con {len(items)} boletines.",
                    )
    except Exception as exc:
        logger.warning("Fallo al descargar feed de CVEs desde %s (%s). Manteniendo catálogo local.", url, exc)

    catalog = load_cve_catalog()
    return CveSyncResponse(
        success=False,
        source_url=url,
        total_cves=len(catalog),
        updated_at=now_utc,
        message=f"No se pudo contactar el feed remoto ({url}). Se mantiene el catálogo local con {len(catalog)} boletines.",
    )
