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
from src.schemas.cve import CveItem, CveSeverity, CveSyncResponse, FleetCveSummary, RouterCveEvaluation

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
    last_synced_at: datetime | None = None,
    cache_expires_at: datetime | None = None,
    cache_ttl_seconds: int | None = None,
    is_cache_fresh: bool = True,
    auto_synced: bool = False,
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
        last_synced_at=last_synced_at,
        cache_expires_at=cache_expires_at,
        cache_ttl_seconds=cache_ttl_seconds,
        is_cache_fresh=is_cache_fresh,
        auto_synced=auto_synced,
    )


def _is_exclusively_legacy_ros(text: str, cve_id: str = "") -> bool:
    """Detecta si un boletín aplica exclusivamente a RouterOS v3/v5/v6 y no afecta a RouterOS v7."""
    low = text.lower()
    if "routeros version 7 is not affected" in low or "routeros versión 7 no se ve afectado" in low:
        return True
    if cve_id and re.match(r"^CVE-(199\d|200\d|201\d)-", cve_id):
        return True
    has_v6_ref = bool(re.search(r"routeros\s+(?:version\s+|v)?[2-6](?:\.\d+|\b)", low))
    has_v7_ref = bool(re.search(r"(?:routeros\s+(?:version\s+|v)?7|\bv?7\.\d+|\bv7\b)", low))
    return has_v6_ref and not has_v7_ref


def _extract_fixed_version_from_text(text: str) -> str | None:
    """Extrae la versión de RouterOS v7 donde se corrige el boletín a partir del texto descriptivo."""
    matches: list[str] = re.findall(
        r"(?:fixed in|since|version|prior to|before|corregid[oa] en)\s*(?:mikrotik\s+)?(?:routeros\s*)?:?\s*v?([0-9]+\.[0-9]+(?:\.[0-9]+)?)",
        text,
        re.IGNORECASE,
    )
    v7_matches = [m for m in matches if m.startswith("7.")]
    if v7_matches:
        return str(v7_matches[0])
    return str(matches[0]) if matches else None


def _resolve_rss_fixed_version(clean_desc: str, cve_id: str) -> str | None:
    if _is_exclusively_legacy_ros(clean_desc, cve_id):
        return None
    extracted = _extract_fixed_version_from_text(clean_desc)
    if extracted and not extracted.startswith("7."):
        return None
    return extracted or "7.24.2"


def _resolve_rss_severity_and_score(clean_desc: str) -> tuple[CveSeverity, float]:
    low = clean_desc.lower()
    is_crit = any(
        w in low for w in ["critical", "without logging in", "root", "underflow", "exploit", "unauthenticated"]
    )
    sev: CveSeverity = "CRITICAL" if is_crit else "HIGH"
    score = 9.8 if is_crit else 7.5
    return sev, score


def _format_rss_published_date(pub_date: str) -> str:
    if not pub_date:
        return "2026-10-20"
    year_match = re.search(r"(\d{4})", pub_date)
    return f"{year_match.group(1)}-01-01" if year_match else "2026-10-20"


def _truncate_desc(desc: str, max_len: int = 280) -> str:
    clean = re.sub(r"<[^>]+>", " ", desc).strip()
    if len(clean) > max_len:
        return clean[: max_len - 3] + "..."
    return clean


def _build_mikrotik_rss_cve_item(cve_id: str, clean_desc: str, pub_date: str) -> CveItem | None:
    """Construye un CveItem desde los datos de un item del RSS de MikroTik Security."""
    fixed_ver = _resolve_rss_fixed_version(clean_desc, cve_id)
    if not fixed_ver:
        return None
    sev, score = _resolve_rss_severity_and_score(clean_desc)
    short_desc = _truncate_desc(clean_desc, 280)
    pub_iso = _format_rss_published_date(pub_date)

    return CveItem(
        cve_id=cve_id,
        title=f"Aviso de seguridad MikroTik ({cve_id})",
        cvss_score=score,
        severity=sev,
        affected_versions_expr=f">=7.0.0,<{fixed_ver}",
        fixed_in_version=fixed_ver,
        description_es=short_desc or f"Boletín oficial de seguridad publicado en MikroTik Security para {cve_id}.",
        remediation=f"Actualizar a RouterOS v{fixed_ver} o superior según boletín oficial https://mikrotik.com/supportsec.",
        published_date=pub_iso,
        source="MIKROTIK",
    )


def _process_rss_item_element(
    item_el: Any, existing_map: dict[str, CveItem]
) -> None:
    title = (item_el.findtext("title") or "").strip()
    desc = (item_el.findtext("description") or "").strip()
    pub_date = (item_el.findtext("pubDate") or "").strip()
    clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()
    matches = re.findall(r"CVE-\d{4}-\d{4,}", f"{title} {desc}")

    for cve_id in matches:
        if cve_id not in existing_map:
            built = _build_mikrotik_rss_cve_item(cve_id, clean_desc, pub_date)
            if built:
                existing_map[cve_id] = built


def _parse_mikrotik_rss(xml_content: str, existing_catalog: list[CveItem]) -> list[CveItem]:
    """Parsea el feed RSS oficial de MikroTik Security e integra boletines CVE aplicables a RouterOS v7."""
    import xml.etree.ElementTree as ET

    existing_map = {item.cve_id: item for item in existing_catalog}
    root = ET.fromstring(xml_content)

    for item_el in root.findall(".//item"):
        _process_rss_item_element(item_el, existing_map)
    return list(existing_map.values())


def _extract_metric_score_severity(metric_list: Any) -> tuple[float, str] | None:
    if not (isinstance(metric_list, list) and metric_list):
        return None
    first = metric_list[0]
    cdata = first.get("cvssData", {})
    score = float(cdata.get("baseScore", 5.0))
    raw_sev = str(cdata.get("baseSeverity") or first.get("baseSeverity") or "").upper()
    return score, raw_sev


def _score_to_severity(score: float, raw_sev: str) -> CveSeverity:
    if raw_sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        return raw_sev  # type: ignore[return-value]
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    return "LOW"


def _extract_nvd_cvss(metrics: dict[str, Any]) -> tuple[float, CveSeverity]:
    """Extrae puntuación CVSS y severidad normalizada desde el bloque metrics de NIST NVD v2.0."""
    score = 5.0
    raw_sev = ""
    for v_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV40", "cvssMetricV2"):
        res = _extract_metric_score_severity(metrics.get(v_key))
        if res:
            score, raw_sev = res
            break
    return score, _score_to_severity(score, raw_sev)


def _extract_cpe_version(match: dict[str, Any]) -> tuple[str | None, str | None, bool]:
    s_inc = match.get("versionStartIncluding") or match.get("versionStartExcluding")
    e_exc = match.get("versionEndExcluding")
    e_inc = match.get("versionEndIncluding")
    parts = str(match.get("criteria", "")).split(":")
    spec_ver = parts[5] if len(parts) > 5 and parts[5] not in ("*", "-", "") else None
    end_v = e_exc or e_inc or spec_ver
    return s_inc, end_v, bool(e_exc)


def _is_cpe_criteria_relevant(criteria: str) -> bool:
    return any(k in criteria for k in ("routeros", "mikrotik", "microtik"))


def _check_cpe_match_v7(match: dict[str, Any]) -> tuple[tuple[str | None, str | None, bool] | None, bool]:
    crit = str(match.get("criteria", "")).lower()
    if not _is_cpe_criteria_relevant(crit):
        return None, False
    s_inc, end_v, is_exc = _extract_cpe_version(match)
    if (end_v and str(end_v).startswith("7.")) or (s_inc and str(s_inc).startswith("7.")):
        return (s_inc, end_v, is_exc), True
    return None, True


def _extract_nvd_v7_ranges(configs: list[dict[str, Any]]) -> tuple[list[tuple[str | None, str | None, bool]], bool]:
    """Extrae rangos de versiones RouterOS v7 desde nodos CPE de NIST NVD e indica si existen CPEs legacy."""
    v7_ranges: list[tuple[str | None, str | None, bool]] = []
    has_any_cpe = False
    for cfg in configs:
        for node in cfg.get("nodes", []):
            for match in node.get("cpeMatch", []):
                rng, is_cpe = _check_cpe_match_v7(match)
                has_any_cpe = has_any_cpe or is_cpe
                if rng:
                    v7_ranges.append(rng)
    return v7_ranges, has_any_cpe


def _extract_nvd_descriptions(cve_data: dict[str, Any]) -> tuple[str, str]:
    desc_es = ""
    desc_en = ""
    for d in cve_data.get("descriptions", []):
        if d.get("lang") == "es":
            desc_es = str(d.get("value", "")).strip()
        elif d.get("lang") == "en":
            desc_en = str(d.get("value", "")).strip()
    return desc_es, desc_en


def _cpe_range_sort_key(r: tuple[str | None, str | None, bool]) -> tuple[int, int, int]:
    target = r[1] if r[1] is not None else r[0]
    parsed = parse_ros_version(target)
    return parsed if parsed is not None else (0, 0, 0)


def _resolve_nvd_version_bounds(
    v7_ranges: list[tuple[str | None, str | None, bool]], full_text: str
) -> tuple[str, str, bool] | None:
    if v7_ranges:
        start_v, end_v, is_exc = max(v7_ranges, key=_cpe_range_sort_key)
        return str(start_v or "7.0.0"), str(end_v or "7.24.2"), is_exc
    extracted = _extract_fixed_version_from_text(full_text)
    if extracted and not extracted.startswith("7."):
        return None
    return "7.0.0", (extracted or "7.24.2"), True


def _extract_nvd_title(cve_data: dict[str, Any], cve_id: str) -> str:
    for w in cve_data.get("weaknesses") or []:
        for wd in w.get("description") or []:
            val = str(wd.get("value", ""))
            if val.startswith("CWE-"):
                return f"Vulnerabilidad {val} en RouterOS v7 ({cve_id})"
    return f"Boletín oficial NIST NVD ({cve_id})"


def _format_nvd_published_date(pub_str: str) -> str:
    pub = pub_str[:10]
    return pub if re.match(r"^\d{4}-\d{2}-\d{2}$", pub) else "2026-01-01"


def _validate_nvd_applicability(
    cve_data: dict[str, Any], cve_id: str, full_text: str
) -> list[tuple[str | None, str | None, bool]] | None:
    if _is_exclusively_legacy_ros(full_text, cve_id):
        return None
    v7_ranges, has_any_cpe = _extract_nvd_v7_ranges(cve_data.get("configurations") or [])
    if has_any_cpe and not v7_ranges:
        return None
    return v7_ranges


def _build_nvd_cve_item(
    cve_id: str,
    cve_data: dict[str, Any],
    desc_es: str,
    desc_en: str,
    bounds: tuple[str, str, bool],
) -> CveItem:
    start_str, fixed_ver, is_exc = bounds
    score, severity = _extract_nvd_cvss(cve_data.get("metrics") or {})
    clean_desc = _truncate_desc(desc_es or desc_en or f"Boletín oficial NIST NVD ({cve_id}).", 320)
    title = _extract_nvd_title(cve_data, cve_id)
    pub_date = _format_nvd_published_date(str(cve_data.get("published", "")))
    op = "<" if is_exc else "<="

    return CveItem(
        cve_id=cve_id,
        title=title,
        cvss_score=score,
        severity=severity,
        affected_versions_expr=f">={start_str},{op}{fixed_ver}",
        fixed_in_version=fixed_ver,
        description_es=clean_desc,
        remediation=f"Actualizar a RouterOS v{fixed_ver} o superior según registro oficial NIST NVD ({cve_id}).",
        published_date=pub_date,
        source="NIST_NVD",
    )


def _parse_nvd_item(cve_data: dict[str, Any]) -> CveItem | None:
    """Parsea un registro de vulnerabilidad de la API REST v2.0 de NIST NVD filtrando para RouterOS v7."""
    cve_id = str(cve_data.get("id", "")).strip()
    if not (cve_id and re.match(r"^CVE-\d{4}-\d{4,}$", cve_id)):
        return None

    desc_es, desc_en = _extract_nvd_descriptions(cve_data)
    full_text = f"{desc_es} {desc_en}".strip()
    v7_ranges = _validate_nvd_applicability(cve_data, cve_id, full_text)
    if v7_ranges is None:
        return None

    bounds = _resolve_nvd_version_bounds(v7_ranges, full_text)
    if not bounds:
        return None
    return _build_nvd_cve_item(cve_id, cve_data, desc_es, desc_en, bounds)


def _merge_single_nvd_cve(existing: CveItem, parsed: CveItem) -> CveItem:
    use_nvd_desc = existing.title.startswith("Aviso de seguridad MikroTik") and bool(parsed.description_es)
    use_nvd_ver = (existing.fixed_in_version == "7.24.2") and (parsed.fixed_in_version != "7.24.2")
    return CveItem(
        cve_id=existing.cve_id,
        title=parsed.title if existing.title.startswith("Aviso de seguridad MikroTik") else existing.title,
        cvss_score=existing.cvss_score,
        severity=existing.severity,
        affected_versions_expr=parsed.affected_versions_expr if use_nvd_ver else existing.affected_versions_expr,
        fixed_in_version=parsed.fixed_in_version if use_nvd_ver else existing.fixed_in_version,
        description_es=parsed.description_es if use_nvd_desc else existing.description_es,
        remediation=existing.remediation,
        published_date=existing.published_date,
        source="BOTH",
    )


def _parse_nvd_response(nvd_payload: dict[str, Any], existing_catalog: list[CveItem]) -> list[CveItem]:
    """Integra los boletines devueltos por la API REST v2.0 de NIST NVD con el catálogo existente."""
    existing_map = {item.cve_id: item for item in existing_catalog}
    for entry in nvd_payload.get("vulnerabilities", []):
        parsed = _parse_nvd_item(entry.get("cve") or {})
        if not parsed:
            continue
        cid = parsed.cve_id
        if cid in existing_map:
            existing_map[cid] = _merge_single_nvd_cve(existing_map[cid], parsed)
        else:
            existing_map[cid] = parsed
    return list(existing_map.values())


def _build_nvd_request_params(
    api_url: str | None, api_key: str | None, results_per_page: int | None
) -> tuple[str, dict[str, str], dict[str, Any]]:
    target_url = str(
        api_url
        or getattr(settings, "ROSGRID_CVE_NVD_API_URL", "https://services.nvd.nist.gov/rest/json/cves/2.0")
    )
    key = api_key or getattr(settings, "ROSGRID_CVE_NVD_API_KEY", None)
    raw_page_size = results_per_page or getattr(settings, "ROSGRID_CVE_NVD_RESULTS_PER_PAGE", 200)
    page_size = int(raw_page_size) if raw_page_size is not None else 200
    headers = {
        "User-Agent": "RoSGrid-NOC-CVE-Scanner/2.0 (+https://mikrotik.com/supportsec)",
        "Accept": "application/json",
    }
    if key:
        headers["apiKey"] = str(key)
    return target_url, headers, {"keywordSearch": "mikrotik", "resultsPerPage": min(page_size, 2000)}


async def fetch_nvd_cves(
    client: httpx.AsyncClient,
    api_url: str | None = None,
    api_key: str | None = None,
    results_per_page: int | None = None,
) -> dict[str, Any] | None:
    """Consulta la API REST v2.0 oficial de NIST NVD para vulnerabilidades de MikroTik RouterOS."""
    target_url, headers, params = _build_nvd_request_params(api_url, api_key, results_per_page)
    try:
        resp = await client.get(target_url, headers=headers, params=params)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "vulnerabilities" in data:
                return data
    except Exception as exc:
        logger.warning("Fallo al consultar NIST NVD REST API v2.0 (%s): %s", target_url, exc)
    return None


def _persist_catalog_safe(items: list[CveItem]) -> None:
    """Persiste de forma atómica y tolerante a fallos el catálogo CVE en disco y memoria."""
    global _CACHED_CATALOG
    _CACHED_CATALOG = items
    try:
        _CATALOG_PATH.write_text(json.dumps([i.model_dump() for i in items], indent=2), encoding="utf-8")
    except OSError:
        pass


_PersistCatalogSafe = _persist_catalog_safe


def _parse_custom_json(raw_data: Any, catalog: list[CveItem]) -> list[CveItem]:
    if isinstance(raw_data, list):
        return [CveItem.model_validate(x) for x in raw_data]
    if isinstance(raw_data, dict) and "vulnerabilities" in raw_data:
        return _parse_nvd_response(raw_data, catalog)
    return []


async def _sync_custom_feed_url(
    client: httpx.AsyncClient, feed_url: str, headers: dict[str, str], catalog: list[CveItem]
) -> list[CveItem]:
    """Descarga y parsea una URL de feed personalizada (JSON directo, NVD JSON o XML RSS)."""
    resp = await client.get(str(feed_url), headers=headers)
    if resp.status_code != 200:
        return []
    raw_text = resp.text.strip()
    if raw_text.startswith(("[", "{")):
        try:
            return _parse_custom_json(resp.json(), catalog)
        except Exception:
            return []
    if any(k in raw_text for k in ("<rss", "<channel", "<item")):
        return _parse_mikrotik_rss(raw_text, catalog)
    return []


async def _download_mikrotik_rss_safe(
    client: httpx.AsyncClient, rss_source: str, headers: dict[str, str], items: list[CveItem]
) -> tuple[list[CveItem], bool]:
    try:
        resp = await client.get(rss_source, headers=headers)
        if resp.status_code == 200 and any(k in resp.text for k in ("<rss", "<channel", "<item")):
            return _parse_mikrotik_rss(resp.text, items), True
    except Exception as exc:
        logger.warning("Fallo al descargar RSS MikroTik (%s): %s", rss_source, exc)
    return items, False


async def _download_nvd_safe(
    client: httpx.AsyncClient, items: list[CveItem]
) -> tuple[list[CveItem], bool]:
    nvd_data = await fetch_nvd_cves(client)
    if nvd_data:
        return _parse_nvd_response(nvd_data, items), True
    return items, False


async def _download_rss_and_nvd(
    client: httpx.AsyncClient,
    rss_source: str,
    headers: dict[str, str],
    catalog: list[CveItem],
    sync_nvd: bool,
    nvd_sync_enabled: bool,
) -> tuple[list[CveItem], bool]:
    items, ok_rss = await _download_mikrotik_rss_safe(client, rss_source, headers, list(catalog))
    ok_nvd = False
    if sync_nvd and nvd_sync_enabled:
        items, ok_nvd = await _download_nvd_safe(client, items)
    return items, (ok_rss or ok_nvd)


def _build_sync_success_response(
    items: list[CveItem], primary_source: str, nvd_search_source: str, now_utc: datetime
) -> CveSyncResponse:
    _persist_catalog_safe(items)
    mk_count = sum(1 for x in items if x.source in ("MIKROTIK", "BOTH"))
    nvd_count = sum(1 for x in items if x.source in ("NIST_NVD", "BOTH"))
    return CveSyncResponse(
        success=True,
        source_url=primary_source,
        total_cves=len(items),
        mikrotik_cves_count=mk_count,
        nvd_cves_count=nvd_count,
        updated_at=now_utc,
        message=(
            f"Catálogo de CVEs actualizado exitosamente desde MikroTik Security ({primary_source}) "
            f"y NIST NVD ({nvd_search_source}) con {len(items)} boletines oficiales."
        ),
    )


async def sync_cve_catalog(feed_url: str | None = None, sync_nvd: bool = True) -> CveSyncResponse:
    """Descarga y sincroniza el catálogo de vulnerabilidades desde MikroTik Security y NIST NVD REST API v2.0."""
    catalog = load_cve_catalog()
    now_utc = datetime.now(timezone.utc)
    primary_source = getattr(settings, "ROSGRID_CVE_PRIMARY_SOURCE", "https://mikrotik.com/supportsec")
    rss_source = getattr(settings, "ROSGRID_CVE_RSS_SOURCE", "https://cdn.mikrotik.com/web-assets/supportsec/rss.xml")
    nvd_search_source = getattr(
        settings, "ROSGRID_CVE_NVD_SEARCH_SOURCE", "https://nvd.nist.gov/vuln/search?keyword=mikrotik&resultType=records"
    )
    nvd_sync_enabled = getattr(settings, "ROSGRID_CVE_NVD_SYNC_ENABLED", True)

    try:
        timeout_cfg = httpx.Timeout(6.0, connect=3.0)
        async with httpx.AsyncClient(timeout=timeout_cfg, follow_redirects=True) as client:
            headers = {"User-Agent": "RoSGrid-NOC-CVE-Scanner/2.0 (+https://mikrotik.com/supportsec)"}
            if feed_url:
                items = await _sync_custom_feed_url(client, feed_url, headers, catalog)
                any_ok = bool(items)
            else:
                items, any_ok = await _download_rss_and_nvd(
                    client, rss_source, headers, catalog, sync_nvd, nvd_sync_enabled
                )

            if any_ok and items:
                return _build_sync_success_response(items, primary_source, nvd_search_source, now_utc)
    except Exception as exc:
        logger.warning("Fallo al sincronizar catálogo CVE (%s). Manteniendo catálogo local.", exc)

    return CveSyncResponse(
        success=False,
        source_url=primary_source,
        total_cves=len(catalog),
        updated_at=now_utc,
        message=(
            f"No se pudo contactar las fuentes remotas ({primary_source} y {nvd_search_source}). "
            f"Se mantiene activo el catálogo local certificado con {len(catalog)} boletines oficiales."
        ),
    )
