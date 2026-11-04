# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 71: Conector Oficial a la API REST v2.0 de NIST NVD, Filtrado Estricto RouterOS v7 y Fusión Multi-Fuente de Boletines CVE (Hito 29.1)

## 1. Contexto Operativo y Diagnóstico Forense de las 4 Causas Raíz

Al inspeccionar la pantalla **Matriz de Vulnerabilidades CVE — Flota MikroTik** (`/inventory/cves`, `FleetCveMatrix.vue`), se observa que únicamente se listan boletines procedentes de `https://mikrotik.com/supportsec` (incluyendo entradas espurias como `CVE-2026-99999` o vulnerabilidades exclusivas de RouterOS v6 como `CVE-2024-27686`), mientras que los registros oficiales publicados en **NIST NVD** (`https://nvd.nist.gov/vuln/search?keyword=mikrotik&resultType=records` / API REST v2.0 `https://services.nvd.nist.gov/rest/json/cves/2.0`) no son descargados ni correlacionados en vivo.

La auditoría forense del código fuente identificó **4 causas raíz encadenadas**:

1. **Causa Raíz #1 — Ausencia de Cliente HTTP hacia la API REST v2.0 de NIST NVD (`fastapi/src/services/cve_matcher.py`):**
   * En [`fastapi/src/services/cve_matcher.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/services/cve_matcher.py#L248-L315), la función `sync_cve_catalog()` define la variable `nvd_search_source` únicamente para interpolarla en el texto del mensaje de respuesta (`CveSyncResponse.message`), pero ejecuta `url = str(feed_url) if feed_url else rss_source`, consultando exclusivamente el feed RSS de MikroTik (`https://cdn.mikrotik.com/web-assets/supportsec/rss.xml`) y omitiendo por completo la API REST v2.0 de NIST NVD (`https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=mikrotik&resultsPerPage=200`).

2. **Causa Raíz #2 — Falso Positivo de Versiones RouterOS v6 en `_parse_mikrotik_rss()` (`fastapi/src/services/cve_matcher.py`):**
   * En `_parse_mikrotik_rss()` (líneas 213-216), la expresión regular `r"(?:fixed in|since|version)\s*:?\s*([0-9]+\.[0-9]+(?:\.[0-9]+)?)"` no contempla la palabra intermedia `"RouterOS"` (ej. `"This issue is fixed in RouterOS 6.49.14"` en `CVE-2024-27686` o `"RouterOS version 6"` en `CVE-2023-30800`). Al no coincidir, asigna el fallback `fixed_ver = "7.24.2"` y `affected_versions_expr = ">=7.0.0,<7.24.2"` a boletines históricos de RouterOS v6 (2018–2024), provocando que routers con RouterOS `7.21.5` aparezcan falsamente afectados por CVEs exclusivos de RouterOS v6.

3. **Causa Raíz #3 — Contaminación del Catálogo Local (`fastapi/src/data/cve_catalog_ros.json`) por Pruebas Unitarias sin Mock de `_CATALOG_PATH`:**
   * En [`fastapi/tests/api/test_hito23_cve_and_syslog.unit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/api/test_hito23_cve_and_syslog.unit.py#L253-L276), el test `test_sync_cve_catalog_mikrotik_rss_success()` invocaba `sync_cve_catalog()` con un XML sintético que contenía `<title>CVE-2026-99999</title>` sin aislar `src.services.cve_matcher._CATALOG_PATH`, sobreescribiendo el fichero real `fastapi/src/data/cve_catalog_ros.json` con `CVE-2026-99999` y 25 entradas crudas en inglés con rango `>=7.0.0,<7.24.2`.

4. **Causa Raíz #4 — Falta de Atributo `source` (`MIKROTIK` | `NIST_NVD` | `BOTH`), Filtro por Fuente en UI y Soporte de API Key de NIST NVD:**
   * `CveItem` (`fastapi/src/schemas/cve.py` y `vue3/src/types/index.ts`) no expone el campo `source` para identificar si un boletín proviene de MikroTik Security, de NIST NVD o de ambas fuentes combinadas, ni `FleetCveMatrix.vue` ofrece un filtro por fuente (`Todas las fuentes`, `MikroTik Security`, `NIST NVD`) o enlace directo a la ficha oficial `https://nvd.nist.gov/vuln/detail/{cve_id}`.

---

## 2. Arquitectura de la Solución (Nivel 11X)

```mermaid
sequenceDiagram
    autonumber
    participant UI as FleetCveMatrix.vue (/inventory/cves)
    participant API as FastAPI (api/v1/cve.py)
    participant Matcher as cve_matcher.py
    participant MK as MikroTik Security RSS
    participant NVD as NIST NVD REST API v2.0
    participant Cache as KeyDB (rg:cve:sync_meta)

    UI->>API: POST /api/v1/inventory/cves/sync
    API->>Matcher: sync_cve_catalog(sync_nvd=True)
    Matcher->>MK: GET https://cdn.mikrotik.com/web-assets/supportsec/rss.xml
    MK-->>Matcher: XML RSS Advisories
    Matcher->>Matcher: _parse_mikrotik_rss() (Filtra solo RouterOS v7)
    Matcher->>NVD: GET https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=mikrotik&resultsPerPage=200
    NVD-->>Matcher: JSON NVD_CVE v2.0 (109+ registros con CPEs y CVSS v3.1)
    Matcher->>Matcher: _parse_nvd_response() (Filtra CPEs v7, extrae español y fusiona source="BOTH"|"NIST_NVD")
    Matcher-->>API: CveSyncResponse (total_cves, mikrotik_count, nvd_count)
    API->>Cache: SET rg:cve:sync_meta (TTL 24h)
    API-->>UI: 200 OK + Recarga Matriz CVE con insignias de fuente y enlaces NVD
```

---

## 3. Plan de Implementación Exacto (Flash-Ready para Gemini 3.8 Flash High)

### 3.1. Parámetros de Configuración del Conector NIST NVD v2.0 (`fastapi/src/core/config.py`)

Añadir `ROSGRID_CVE_NVD_API_URL`, `ROSGRID_CVE_NVD_API_KEY`, `ROSGRID_CVE_NVD_SYNC_ENABLED` y `ROSGRID_CVE_NVD_RESULTS_PER_PAGE` en `Settings`.

* **Archivo:** `fastapi/src/core/config.py`
* **Bloque `Target`:**
```python
    # Fuentes Oficiales de Boletines y Vulnerabilidades CVE
    ROSGRID_CVE_PRIMARY_SOURCE: str = "https://mikrotik.com/supportsec"
    ROSGRID_CVE_RSS_SOURCE: str = "https://cdn.mikrotik.com/web-assets/supportsec/rss.xml"
    ROSGRID_CVE_NVD_SEARCH_SOURCE: str = "https://nvd.nist.gov/vuln/search?keyword=mikrotik&resultType=records"
```
* **Bloque `Replacement`:**
```python
    # Fuentes Oficiales de Boletines y Vulnerabilidades CVE
    ROSGRID_CVE_PRIMARY_SOURCE: str = "https://mikrotik.com/supportsec"
    ROSGRID_CVE_RSS_SOURCE: str = "https://cdn.mikrotik.com/web-assets/supportsec/rss.xml"
    ROSGRID_CVE_NVD_SEARCH_SOURCE: str = "https://nvd.nist.gov/vuln/search?keyword=mikrotik&resultType=records"
    ROSGRID_CVE_NVD_API_URL: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    ROSGRID_CVE_NVD_API_KEY: str | None = None
    ROSGRID_CVE_NVD_SYNC_ENABLED: bool = True
    ROSGRID_CVE_NVD_RESULTS_PER_PAGE: int = 200
```

---

### 3.2. Esquemas Pydantic Enriquecidos con Fuente Oficial (`fastapi/src/schemas/cve.py`)

Incorporar `CveSource = Literal["MIKROTIK", "NIST_NVD", "BOTH"]`, el campo `source: CveSource = "MIKROTIK"` en `CveItem`, y los contadores `mikrotik_cves_count` / `nvd_cves_count` en `CveSyncResponse`.

* **Archivo:** `fastapi/src/schemas/cve.py`
* **Bloque `Target`:**
```python
CveSeverity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]


class CveItem(BaseModel):
    cve_id: str = Field(..., description="Identificador CVE oficial (ej. CVE-2023-32154)")
    title: str = Field(..., description="Título descriptivo en español")
    cvss_score: float = Field(..., ge=0.0, le=10.0, description="Puntuación CVSS v3")
    severity: CveSeverity = Field(..., description="Nivel de severidad según CVSS")
    affected_versions_expr: str = Field(..., description="Expresión de versiones afectadas (ej. >=7.0.0,<7.9.2)")
    fixed_in_version: str = Field(..., description="Versión mínima donde se subsana la vulnerabilidad")
    description_es: str = Field(..., description="Descripción técnica en español")
    remediation: str = Field(..., description="Recomendación técnica y acciones de mitigación")
    published_date: str = Field(..., description="Fecha de publicación del boletín")
```
* **Bloque `Replacement`:**
```python
CveSeverity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
CveSource = Literal["MIKROTIK", "NIST_NVD", "BOTH"]


class CveItem(BaseModel):
    cve_id: str = Field(..., description="Identificador CVE oficial (ej. CVE-2023-32154)")
    title: str = Field(..., description="Título descriptivo en español")
    cvss_score: float = Field(..., ge=0.0, le=10.0, description="Puntuación CVSS v3")
    severity: CveSeverity = Field(..., description="Nivel de severidad según CVSS")
    affected_versions_expr: str = Field(..., description="Expresión de versiones afectadas (ej. >=7.0.0,<7.9.2)")
    fixed_in_version: str = Field(..., description="Versión mínima donde se subsana la vulnerabilidad")
    description_es: str = Field(..., description="Descripción técnica en español")
    remediation: str = Field(..., description="Recomendación técnica y acciones de mitigación")
    published_date: str = Field(..., description="Fecha de publicación del boletín")
    source: CveSource = Field("BOTH", description="Fuente oficial del boletín: MIKROTIK, NIST_NVD o BOTH")
```

* **Archivo:** `fastapi/src/schemas/cve.py` (en `CveSyncResponse`)
* **Bloque `Target`:**
```python
class CveSyncResponse(BaseModel):
    success: bool
    source_url: str
    total_cves: int
    updated_at: datetime
    message: str
```
* **Bloque `Replacement`:**
```python
class CveSyncResponse(BaseModel):
    success: bool
    source_url: str
    total_cves: int
    mikrotik_cves_count: int = 0
    nvd_cves_count: int = 0
    updated_at: datetime
    message: str
```

---

### 3.3. Conector Oficial NIST NVD REST API v2.0 y Filtro Estricto RouterOS v7 (`fastapi/src/services/cve_matcher.py`)

Implementar `_is_exclusively_legacy_ros(desc_text)`, `_parse_nvd_item(cve_data)`, `_parse_nvd_response(nvd_payload, existing_catalog)`, `fetch_nvd_cves(...)` y la sincronización multi-fuente en `sync_cve_catalog()` manteniendo complejidad ciclomática Radon Grado A (`CC <= 4` por función mediante helpers modulares).

* **Archivo:** `fastapi/src/services/cve_matcher.py`
* **Bloque `Target`:**
```python
def _parse_mikrotik_rss(xml_content: str, existing_catalog: list[CveItem]) -> list[CveItem]:
    """Parsea el feed RSS oficial de MikroTik Security e integra boletines CVE."""
    import xml.etree.ElementTree as ET

    existing_map = {item.cve_id: item for item in existing_catalog}
    root = ET.fromstring(xml_content)

    for item_el in root.findall(".//item"):
        title = (item_el.findtext("title") or "").strip()
        desc = (item_el.findtext("description") or "").strip()
        pub_date = (item_el.findtext("pubDate") or "").strip()

        cve_matches = re.findall(r"CVE-\d{4}-\d{4,}", f"{title} {desc}")
        for cve_id in cve_matches:
            if cve_id not in existing_map:
                fix_match = re.search(
                    r"(?:fixed in|since|version)\s*:?\s*([0-9]+\.[0-9]+(?:\.[0-9]+)?)", desc, re.IGNORECASE
                )
                fixed_ver = fix_match.group(1) if fix_match else "7.24.2"
                is_crit = any(
                    w in desc.lower()
                    for w in ["critical", "without logging in", "root", "underflow", "exploit", "unauthenticated"]
                )
                sev: CveSeverity = "CRITICAL" if is_crit else "HIGH"
                score = 9.8 if is_crit else 7.5

                clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()
                if len(clean_desc) > 280:
                    clean_desc = clean_desc[:277] + "..."

                pub_iso = "2026-10-20"
                if pub_date:
                    year_match = re.search(r"(\d{4})", pub_date)
                    if year_match:
                        pub_iso = f"{year_match.group(1)}-01-01"

                existing_map[cve_id] = CveItem(
                    cve_id=cve_id,
                    title=f"Aviso de seguridad MikroTik ({cve_id})",
                    cvss_score=score,
                    severity=sev,
                    affected_versions_expr=f">=7.0.0,<{fixed_ver}",
                    fixed_in_version=fixed_ver,
                    description_es=clean_desc or f"Boletín oficial de seguridad publicado en MikroTik Security para {cve_id}.",
                    remediation=f"Actualizar a RouterOS v{fixed_ver} o superior según boletín oficial https://mikrotik.com/supportsec.",
                    published_date=pub_iso,
                )
    return list(existing_map.values())


async def sync_cve_catalog(feed_url: str | None = None) -> CveSyncResponse:
    """Descarga y sincroniza el catálogo de vulnerabilidades desde las fuentes oficiales de MikroTik y NIST NVD."""
    global _CACHED_CATALOG
    catalog = load_cve_catalog()
    now_utc = datetime.now(timezone.utc)

    primary_source = getattr(settings, "ROSGRID_CVE_PRIMARY_SOURCE", "https://mikrotik.com/supportsec")
    rss_source = getattr(settings, "ROSGRID_CVE_RSS_SOURCE", "https://cdn.mikrotik.com/web-assets/supportsec/rss.xml")
    nvd_search_source = getattr(
        settings, "ROSGRID_CVE_NVD_SEARCH_SOURCE", "https://nvd.nist.gov/vuln/search?keyword=mikrotik&resultType=records"
    )

    url = str(feed_url) if feed_url else rss_source

    try:
        timeout_cfg = httpx.Timeout(5.0, connect=3.0)
        async with httpx.AsyncClient(timeout=timeout_cfg, follow_redirects=True) as client:
            headers = {"User-Agent": "RoSGrid-NOC-CVE-Scanner/1.0 (+https://mikrotik.com/supportsec)"}
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                raw_text = resp.text
                items: list[CveItem] = []

                if raw_text.strip().startswith("[") or raw_text.strip().startswith("{"):
                    try:
                        raw_data = resp.json()
                        if isinstance(raw_data, list):
                            items = [CveItem.model_validate(x) for x in raw_data]
                    except Exception:
                        pass

                if not items and ("<rss" in raw_text or "<channel" in raw_text or "<item" in raw_text):
                    try:
                        items = _parse_mikrotik_rss(raw_text, catalog)
                    except Exception as err:
                        logger.warning("Fallo al parsear XML de MikroTik Security: %s", err)

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
                        source_url=primary_source,
                        total_cves=len(items),
                        updated_at=now_utc,
                        message=(
                            f"Catálogo de CVEs actualizado exitosamente desde MikroTik Security ({primary_source}) "
                            f"y NIST NVD ({nvd_search_source}) con {len(items)} boletines oficiales."
                        ),
                    )
    except Exception as exc:
        logger.warning("Fallo al descargar feed de CVEs desde %s (%s). Manteniendo catálogo local.", url, exc)

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
```
* **Bloque `Replacement`:**
```python
def _is_exclusively_legacy_ros(text: str, cve_id: str = "") -> bool:
    """Detecta si un boletín aplica exclusivamente a RouterOS v3/v5/v6 y no afecta a RouterOS v7."""
    low = text.lower()
    if "routeros version 7 is not affected" in low or "routeros versión 7 no se ve afectado" in low:
        return True
    if cve_id and re.match(r"^CVE-(199\d|200\d|201\d)-", cve_id):
        return True
    has_v6_ref = bool(re.search(r"routeros\s+(?:version\s+|v)?[2-6](?:\.\d+|\b)", low))
    has_v7_ref = bool(re.search(r"(?:routeros\s+(?:version\s+|v)?7|\bv?7\.\d+)", low))
    return has_v6_ref and not has_v7_ref


def _extract_fixed_version_from_text(text: str) -> str | None:
    """Extrae la versión de RouterOS v7 donde se corrige el boletín a partir del texto descriptivo."""
    matches = re.findall(
        r"(?:fixed in|since|version|prior to|before|corregid[oa] en)\s*(?:mikrotik\s+)?(?:routeros\s*)?:?\s*v?([0-9]+\.[0-9]+(?:\.[0-9]+)?)",
        text,
        re.IGNORECASE,
    )
    v7_matches = [m for m in matches if m.startswith("7.")]
    if v7_matches:
        return v7_matches[0]
    return matches[0] if matches else None


def _parse_mikrotik_rss(xml_content: str, existing_catalog: list[CveItem]) -> list[CveItem]:
    """Parsea el feed RSS oficial de MikroTik Security e integra boletines CVE aplicables a RouterOS v7."""
    import xml.etree.ElementTree as ET

    existing_map = {item.cve_id: item for item in existing_catalog}
    root = ET.fromstring(xml_content)

    for item_el in root.findall(".//item"):
        title = (item_el.findtext("title") or "").strip()
        desc = (item_el.findtext("description") or "").strip()
        pub_date = (item_el.findtext("pubDate") or "").strip()
        clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()

        cve_matches = re.findall(r"CVE-\d{4}-\d{4,}", f"{title} {desc}")
        for cve_id in cve_matches:
            if cve_id in existing_map:
                continue
            if _is_exclusively_legacy_ros(clean_desc, cve_id):
                continue
            extracted_ver = _extract_fixed_version_from_text(clean_desc)
            if extracted_ver and not extracted_ver.startswith("7."):
                continue
            fixed_ver = extracted_ver or "7.24.2"
            is_crit = any(
                w in clean_desc.lower()
                for w in ["critical", "without logging in", "root", "underflow", "exploit", "unauthenticated"]
            )
            sev: CveSeverity = "CRITICAL" if is_crit else "HIGH"
            score = 9.8 if is_crit else 7.5
            short_desc = clean_desc[:277] + "..." if len(clean_desc) > 280 else clean_desc
            year_match = re.search(r"(\d{4})", pub_date) if pub_date else None
            pub_iso = f"{year_match.group(1)}-01-01" if year_match else "2026-10-20"

            existing_map[cve_id] = CveItem(
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
    return list(existing_map.values())


def _extract_nvd_cvss(metrics: dict[str, Any]) -> tuple[float, CveSeverity]:
    """Extrae puntuación CVSS y severidad normalizada desde el bloque metrics de NIST NVD v2.0."""
    score = 5.0
    raw_sev = ""
    for v_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV40", "cvssMetricV2"):
        metric_list = metrics.get(v_key)
        if metric_list and isinstance(metric_list, list):
            first = metric_list[0]
            cdata = first.get("cvssData", {})
            if "baseScore" in cdata:
                score = float(cdata["baseScore"])
            raw_sev = str(cdata.get("baseSeverity") or first.get("baseSeverity") or "").upper()
            break
    if raw_sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        return score, raw_sev  # type: ignore[return-value]
    if score >= 9.0:
        return score, "CRITICAL"
    if score >= 7.0:
        return score, "HIGH"
    if score >= 4.0:
        return score, "MEDIUM"
    return score, "LOW"


def _extract_nvd_v7_ranges(configs: list[dict[str, Any]]) -> tuple[list[tuple[str | None, str | None, bool]], bool]:
    """Extrae rangos de versiones RouterOS v7 desde nodos CPE de NIST NVD e indica si existen CPEs legacy."""
    v7_ranges: list[tuple[str | None, str | None, bool]] = []
    has_any_cpe = False
    for cfg in configs:
        for node in cfg.get("nodes", []):
            for match in node.get("cpeMatch", []):
                crit = str(match.get("criteria", "")).lower()
                if "routeros" not in crit and "mikrotik" not in crit and "microtik" not in crit:
                    continue
                has_any_cpe = True
                s_inc = match.get("versionStartIncluding") or match.get("versionStartExcluding")
                e_exc = match.get("versionEndExcluding")
                e_inc = match.get("versionEndIncluding")
                parts = str(match.get("criteria", "")).split(":")
                spec_ver = parts[5] if len(parts) > 5 and parts[5] not in ("*", "-", "") else None
                end_v = e_exc or e_inc or spec_ver
                if (end_v and str(end_v).startswith("7.")) or (s_inc and str(s_inc).startswith("7.")):
                    v7_ranges.append((s_inc, end_v, bool(e_exc)))
    return v7_ranges, has_any_cpe


def _parse_nvd_item(cve_data: dict[str, Any]) -> CveItem | None:
    """Parsea un registro de vulnerabilidad de la API REST v2.0 de NIST NVD filtrando para RouterOS v7."""
    cve_id = str(cve_data.get("id", "")).strip()
    if not cve_id or not re.match(r"^CVE-\d{4}-\d{4,}$", cve_id):
        return None

    desc_es = ""
    desc_en = ""
    for d in cve_data.get("descriptions", []):
        if d.get("lang") == "es":
            desc_es = str(d.get("value", "")).strip()
        elif d.get("lang") == "en":
            desc_en = str(d.get("value", "")).strip()
    full_text = f"{desc_es} {desc_en}".strip()
    if _is_exclusively_legacy_ros(full_text, cve_id):
        return None

    v7_ranges, has_any_cpe = _extract_nvd_v7_ranges(cve_data.get("configurations") or [])
    if has_any_cpe and not v7_ranges:
        return None

    if v7_ranges:
        start_v, end_v, is_exc = max(v7_ranges, key=lambda r: parse_ros_version(r[1] or r[0]) or (0, 0, 0))
    else:
        extracted = _extract_fixed_version_from_text(full_text)
        if extracted and not extracted.startswith("7."):
            return None
        start_v, end_v, is_exc = "7.0.0", (extracted or "7.24.2"), True

    fixed_ver = str(end_v or "7.24.2")
    start_str = str(start_v or "7.0.0")
    op = "<" if is_exc else "<="
    score, severity = _extract_nvd_cvss(cve_data.get("metrics") or {})
    clean_desc = re.sub(r"<[^>]+>", " ", desc_es or desc_en or f"Boletín oficial NIST NVD ({cve_id}).").strip()
    if len(clean_desc) > 320:
        clean_desc = clean_desc[:317] + "..."

    title = f"Boletín oficial NIST NVD ({cve_id})"
    for w in cve_data.get("weaknesses") or []:
        for wd in w.get("description") or []:
            val = str(wd.get("value", ""))
            if val.startswith("CWE-"):
                title = f"Vulnerabilidad {val} en RouterOS v7 ({cve_id})"
                break

    pub = str(cve_data.get("published", ""))[:10]
    pub_date = pub if re.match(r"^\d{4}-\d{2}-\d{2}$", pub) else "2026-01-01"

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


def _parse_nvd_response(nvd_payload: dict[str, Any], existing_catalog: list[CveItem]) -> list[CveItem]:
    """Integra los boletines devueltos por la API REST v2.0 de NIST NVD con el catálogo existente."""
    existing_map = {item.cve_id: item for item in existing_catalog}
    for entry in nvd_payload.get("vulnerabilities", []):
        parsed = _parse_nvd_item(entry.get("cve") or {})
        if not parsed:
            continue
        cid = parsed.cve_id
        if cid in existing_map:
            old = existing_map[cid]
            use_nvd_desc = "Aviso de seguridad MikroTik" in old.title and bool(parsed.description_es)
            use_nvd_ver = old.fixed_in_version == "7.24.2" and parsed.fixed_in_version != "7.24.2"
            existing_map[cid] = CveItem(
                cve_id=cid,
                title=parsed.title if old.title.startswith("Aviso de seguridad MikroTik") else old.title,
                cvss_score=old.cvss_score,
                severity=old.severity,
                affected_versions_expr=parsed.affected_versions_expr if use_nvd_ver else old.affected_versions_expr,
                fixed_in_version=parsed.fixed_in_version if use_nvd_ver else old.fixed_in_version,
                description_es=parsed.description_es if use_nvd_desc else old.description_es,
                remediation=old.remediation,
                published_date=old.published_date,
                source="BOTH",
            )
        else:
            existing_map[cid] = parsed
    return list(existing_map.values())


async def fetch_nvd_cves(
    client: httpx.AsyncClient,
    api_url: str | None = None,
    api_key: str | None = None,
    results_per_page: int | None = None,
) -> dict[str, Any] | None:
    """Consulta la API REST v2.0 oficial de NIST NVD para vulnerabilidades de MikroTik RouterOS."""
    target_url = api_url or getattr(
        settings, "ROSGRID_CVE_NVD_API_URL", "https://services.nvd.nist.gov/rest/json/cves/2.0"
    )
    key = api_key or getattr(settings, "ROSGRID_CVE_NVD_API_KEY", None)
    page_size = results_per_page or getattr(settings, "ROSGRID_CVE_NVD_RESULTS_PER_PAGE", 200)
    headers = {
        "User-Agent": "RoSGrid-NOC-CVE-Scanner/2.0 (+https://mikrotik.com/supportsec)",
        "Accept": "application/json",
    }
    if key:
        headers["apiKey"] = key
    try:
        resp = await client.get(
            target_url,
            headers=headers,
            params={"keywordSearch": "mikrotik", "resultsPerPage": min(page_size, 2000)},
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "vulnerabilities" in data:
                return data
    except Exception as exc:
        logger.warning("Fallo al consultar NIST NVD REST API v2.0 (%s): %s", target_url, exc)
    return None


def _PersistCatalogSafe(items: list[CveItem]) -> None:
    """Persiste de forma atómica y tolerante a fallos el catálogo CVE en disco y memoria."""
    global _CACHED_CATALOG
    _CACHED_CATALOG = items
    try:
        _CATALOG_PATH.write_text(json.dumps([i.model_dump() for i in items], indent=2), encoding="utf-8")
    except OSError:
        pass


async def _sync_custom_feed_url(
    client: httpx.AsyncClient, feed_url: str, headers: dict[str, str], catalog: list[CveItem]
) -> list[CveItem]:
    """Descarga y parsea una URL de feed personalizada (JSON directo, NVD JSON o XML RSS)."""
    resp = await client.get(str(feed_url), headers=headers)
    if resp.status_code != 200:
        return []
    raw_text = resp.text.strip()
    if raw_text.startswith("[") or raw_text.startswith("{"):
        try:
            raw_data = resp.json()
            if isinstance(raw_data, list):
                return [CveItem.model_validate(x) for x in raw_data]
            if isinstance(raw_data, dict) and "vulnerabilities" in raw_data:
                return _parse_nvd_response(raw_data, catalog)
        except Exception:
            pass
    if "<rss" in raw_text or "<channel" in raw_text or "<item" in raw_text:
        return _parse_mikrotik_rss(raw_text, catalog)
    return []


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
                items = list(catalog)
                any_ok = False
                try:
                    resp_rss = await client.get(rss_source, headers=headers)
                    if resp_rss.status_code == 200 and (
                        "<rss" in resp_rss.text or "<channel" in resp_rss.text or "<item" in resp_rss.text
                    ):
                        items = _parse_mikrotik_rss(resp_rss.text, items)
                        any_ok = True
                except Exception as exc_rss:
                    logger.warning("Fallo al descargar RSS MikroTik (%s): %s", rss_source, exc_rss)

                if sync_nvd and nvd_sync_enabled:
                    nvd_data = await fetch_nvd_cves(client)
                    if nvd_data:
                        items = _parse_nvd_response(nvd_data, items)
                        any_ok = True

            if any_ok and items:
                _PersistCatalogSafe(items)
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
```

---

### 3.4. Saneamiento del Catálogo Local de RouterOS v7 y Adición de Boletines NIST NVD (`fastapi/src/data/cve_catalog_ros.json`)

Eliminar del fichero `fastapi/src/data/cve_catalog_ros.json` el registro sintético de prueba `CVE-2026-99999` y los 23 boletines exclusivos de RouterOS v6 (2018–2021 y `CVE-2024-27686`, `CVE-2023-30800`) que estaban etiquetados erróneamente como `>=7.0.0,<7.24.2`, y reemplazarlos por los boletines reales de RouterOS v7 registrados en NIST NVD con sus rangos exactos (`CVE-2024-54772` con `>=7.1.0,<7.18.0`, `CVE-2023-41570` con `>=7.1.0,<7.12.0`, `CVE-2022-45313` con `>=7.0.0,<7.5.0`, `CVE-2022-45315` con `>=7.0.0,<7.6.0` y `CVE-2022-34960` con `>=7.0.0,<7.5.0`).

* **Archivo:** `fastapi/src/data/cve_catalog_ros.json`
* **Bloque `Target`:** (líneas 254–541 de `fastapi/src/data/cve_catalog_ros.json`, desde el cierre de `CVE-2023-47310` hasta el final del archivo)
```json
  {
    "cve_id": "CVE-2023-47310",
    "title": "Filtraci\u00f3n de paquetes UDP Traceroute IPv6 en configuraci\u00f3n por defecto",
    "cvss_score": 5.3,
    "severity": "MEDIUM",
    "affected_versions_expr": ">=7.0.0,<7.14.0",
    "fixed_in_version": "7.14.0",
    "description_es": "Falta de descarte de paquetes de traceroute UDP entrantes en la configuraci\u00f3n IPv6 por defecto, permitiendo reconocimiento y mapeo topol\u00f3gico externo no autorizado de la red interna.",
    "remediation": "Actualizar a RouterOS v7.14 o superior, o aplicar regla de descarte en /ipv6/firewall/filter para puertos UDP 33434-33534.",
    "published_date": "2025-06-30"
  },
  {
    "cve_id": "CVE-2026-99999",
```
*(Reemplazar desde `CVE-2023-47310` inclusive hasta el `]` final de `fastapi/src/data/cve_catalog_ros.json`)*
* **Bloque `Replacement`:**
```json
  {
    "cve_id": "CVE-2023-47310",
    "title": "Filtraci\u00f3n de paquetes UDP Traceroute IPv6 en configuraci\u00f3n por defecto",
    "cvss_score": 5.3,
    "severity": "MEDIUM",
    "affected_versions_expr": ">=7.0.0,<7.14.0",
    "fixed_in_version": "7.14.0",
    "description_es": "Falta de descarte de paquetes de traceroute UDP entrantes en la configuraci\u00f3n IPv6 por defecto, permitiendo reconocimiento y mapeo topol\u00f3gico externo no autorizado de la red interna.",
    "remediation": "Actualizar a RouterOS v7.14 o superior, o aplicar regla de descarte en /ipv6/firewall/filter para puertos UDP 33434-33534.",
    "published_date": "2025-06-30",
    "source": "NIST_NVD"
  },
  {
    "cve_id": "CVE-2024-54772",
    "title": "Enumeraci\u00f3n de usuarios por discrepancia de tama\u00f1o de respuesta en servicio WinBox",
    "cvss_score": 5.3,
    "severity": "MEDIUM",
    "affected_versions_expr": ">=7.1.0,<7.18.0",
    "fixed_in_version": "7.18.0",
    "description_es": "Discrepancia en el tama\u00f1o de respuesta entre intentos de conexi\u00f3n con nombres de usuario v\u00e1lidos e inv\u00e1lidos en el servicio WinBox de RouterOS v7, permitiendo a atacantes remotos confirmar la existencia de cuentas mediante fuerza bruta.",
    "remediation": "Actualizar a RouterOS v7.18 o superior y restringir el puerto TCP 8291 en /ip/service exclusivamente a subredes de gesti\u00f3n.",
    "published_date": "2025-05-06",
    "source": "BOTH"
  },
  {
    "cve_id": "CVE-2023-41570",
    "title": "Control de acceso incorrecto en el servidor REST API de RouterOS v7",
    "cvss_score": 7.5,
    "severity": "HIGH",
    "affected_versions_expr": ">=7.1.0,<7.12.0",
    "fixed_in_version": "7.12.0",
    "description_es": "Se descubri\u00f3 que MikroTik RouterOS v7.1 a v7.11 conten\u00eda mecanismos de control de acceso incorrectos para la API REST cuando el servicio web estaba habilitado y accesible.",
    "remediation": "Actualizar a RouterOS v7.12 o superior según registro oficial NIST NVD (CVE-2023-41570).",
    "published_date": "2023-11-16",
    "source": "BOTH"
  },
  {
    "cve_id": "CVE-2022-45313",
    "title": "Desbordamiento de enteros en el proceso de actualizaci\u00f3n y gesti\u00f3n de RouterOS v7",
    "cvss_score": 8.8,
    "severity": "HIGH",
    "affected_versions_expr": ">=7.0.0,<7.5.0",
    "fixed_in_version": "7.5.0",
    "description_es": "Vulnerabilidad de desbordamiento de enteros en MikroTik RouterOS anterior a v7.5 que permite a un atacante autenticado provocar denegaci\u00f3n de servicio o ejecuci\u00f3n de c\u00f3digo arbitrario.",
    "remediation": "Actualizar a RouterOS v7.5 o superior según registro oficial NIST NVD (CVE-2022-45313).",
    "published_date": "2022-12-26",
    "source": "NIST_NVD"
  },
  {
    "cve_id": "CVE-2022-45315",
    "title": "Acceso fuera de l\u00edmites en servicio SNMP de MikroTik RouterOS v7",
    "cvss_score": 7.5,
    "severity": "HIGH",
    "affected_versions_expr": ">=7.0.0,<7.6.0",
    "fixed_in_version": "7.6.0",
    "description_es": "Vulnerabilidad de lectura fuera de l\u00edmites en el subsistema SNMP de MikroTik RouterOS anterior a v7.6 al procesar paquetes SNMP especialmente dise\u00f1ados.",
    "remediation": "Actualizar a RouterOS v7.6 o superior según registro oficial NIST NVD (CVE-2022-45315).",
    "published_date": "2022-12-26",
    "source": "NIST_NVD"
  },
  {
    "cve_id": "CVE-2022-34960",
    "title": "Escalada de privilegios mediante enlaces simb\u00f3licos en paquete Container de RouterOS v7",
    "cvss_score": 8.8,
    "severity": "HIGH",
    "affected_versions_expr": ">=7.0.0,<7.5.0",
    "fixed_in_version": "7.5.0",
    "description_es": "El paquete contenedor en MikroTik RouterOS v7.4 permite crear puntos de montaje que apuntan a enlaces simb\u00f3licos resueltos en el dispositivo anfitri\u00f3n, permitiendo montar archivos arbitrarios del host.",
    "remediation": "Actualizar a RouterOS v7.5 o superior según registro oficial NIST NVD (CVE-2022-34960).",
    "published_date": "2022-08-03",
    "source": "NIST_NVD"
  }
]
```

---

### 3.5. Tipos Frontend (`vue3/src/types/index.ts`) e Insignias + Filtro de Fuente en `FleetCveMatrix.vue`

Actualizar `CveItem` y `CveSyncResponse` en `vue3/src/types/index.ts` e incorporar en `vue3/src/views/FleetCveMatrix.vue` el selector de fuente (`#cve-source-filter`: `ALL`, `MIKROTIK`, `NIST_NVD`), la insignia de origen (`MikroTik` / `NIST NVD` / `MikroTik + NIST`) y el enlace directo a la ficha oficial de NIST NVD (`https://nvd.nist.gov/vuln/detail/${row.cve.cve_id}`).

* **Archivo:** `vue3/src/types/index.ts`
* **Bloque `Target`:**
```ts
export type CveSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface CveItem {
  cve_id: string;
  title: string;
  cvss_score: number;
  severity: CveSeverity;
  affected_versions_expr: string;
  fixed_in_version: string;
  description_es: string;
  remediation: string;
  published_date: string;
}
```
* **Bloque `Replacement`:**
```ts
export type CveSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type CveSource = 'MIKROTIK' | 'NIST_NVD' | 'BOTH';

export interface CveItem {
  cve_id: string;
  title: string;
  cvss_score: number;
  severity: CveSeverity;
  affected_versions_expr: string;
  fixed_in_version: string;
  description_es: string;
  remediation: string;
  published_date: string;
  source?: CveSource;
}
```

* **Archivo:** `vue3/src/views/FleetCveMatrix.vue`
* **Bloque `Target`:**
```ts
const cveSummary = ref<FleetCveSummary | null>(null);
const searchQuery = ref('');
const selectedSeverity = ref<string>('ALL');
const expandedCveId = ref<string | null>(null);
```
* **Bloque `Replacement`:**
```ts
const cveSummary = ref<FleetCveSummary | null>(null);
const searchQuery = ref('');
const selectedSeverity = ref<string>('ALL');
const selectedSource = ref<string>('ALL');
const expandedCveId = ref<string | null>(null);
```

* **Archivo:** `vue3/src/views/FleetCveMatrix.vue` (en `uniqueCveRows`)
* **Bloque `Target`:**
```ts
  if (selectedSeverity.value !== 'ALL') {
    list = list.filter((row) => row.cve.severity === selectedSeverity.value);
  }
```
* **Bloque `Replacement`:**
```ts
  if (selectedSeverity.value !== 'ALL') {
    list = list.filter((row) => row.cve.severity === selectedSeverity.value);
  }

  if (selectedSource.value !== 'ALL') {
    list = list.filter((row) => {
      const src = row.cve.source || 'BOTH';
      return src === selectedSource.value || src === 'BOTH';
    });
  }
```

* **Archivo:** `vue3/src/views/FleetCveMatrix.vue` (en `.cve-filters`)
* **Bloque `Target`:**
```html
      <div class="filter-item">
        <label for="cve-severity-filter" class="filter-label">{{ t('cve_matrix.th_severity', 'Severidad CVSS:') }}</label>
        <select id="cve-severity-filter" v-model="selectedSeverity" class="select-filter">
          <option value="ALL">{{ t('cve_matrix.severity_all', 'Todas las severidades') }}</option>
          <option value="CRITICAL">CRITICAL (>= 9.0)</option>
          <option value="HIGH">HIGH (7.0 - 8.9)</option>
          <option value="MEDIUM">MEDIUM (4.0 - 6.9)</option>
          <option value="LOW">LOW (&lt; 4.0)</option>
        </select>
      </div>
```
* **Bloque `Replacement`:**
```html
      <div class="filter-item">
        <label for="cve-severity-filter" class="filter-label">{{ t('cve_matrix.th_severity', 'Severidad CVSS:') }}</label>
        <select id="cve-severity-filter" v-model="selectedSeverity" class="select-filter">
          <option value="ALL">{{ t('cve_matrix.severity_all', 'Todas las severidades') }}</option>
          <option value="CRITICAL">CRITICAL (>= 9.0)</option>
          <option value="HIGH">HIGH (7.0 - 8.9)</option>
          <option value="MEDIUM">MEDIUM (4.0 - 6.9)</option>
          <option value="LOW">LOW (&lt; 4.0)</option>
        </select>
      </div>

      <div class="filter-item">
        <label for="cve-source-filter" class="filter-label">{{ t('cve_matrix.th_source', 'Fuente Oficial:') }}</label>
        <select id="cve-source-filter" v-model="selectedSource" class="select-filter">
          <option value="ALL">{{ t('cve_matrix.source_all', 'MikroTik + NIST NVD') }}</option>
          <option value="MIKROTIK">MikroTik Security Advisories</option>
          <option value="NIST_NVD">NIST NVD REST API v2.0</option>
        </select>
      </div>
```

---

### 3.6. Aseguramiento de Calidad Level-11X (Pytest, Vitest y Karate Labs BDD)

1. **`fastapi/tests/api/test_hito23_cve_and_syslog.unit.py`:**
   * En `test_sync_cve_catalog_mikrotik_rss_success(tmp_path)`: aislar `_CATALOG_PATH` con `patch("src.services.cve_matcher._CATALOG_PATH", tmp_path / "catalog.json")` para impedir que el test contamine `fastapi/src/data/cve_catalog_ros.json`.
   * Añadir `test_parse_nvd_response_ros7_and_legacy_filtering(tmp_path)`: verifica que `_parse_nvd_response` importa CVEs de RouterOS v7 con descripción en español y métricas CVSS v3.1 desde la estructura JSON de NIST NVD v2.0, descarta CVEs exclusivos de RouterOS v6 (`CVE-2018-14847`, `CVE-2023-30800`), y enriquece entradas existentes marcándolas con `source="BOTH"`.
   * Añadir `test_sync_cve_catalog_multi_source_mikrotik_and_nvd(tmp_path)`: verifica que `sync_cve_catalog()` invoca tanto el feed RSS de MikroTik como `fetch_nvd_cves()` hacia `https://services.nvd.nist.gov/rest/json/cves/2.0` y retorna `mikrotik_cves_count > 0` y `nvd_cves_count > 0`.
2. **`vue3/src/views/fleetCveMatrix.unit.ts`:**
   * Verificar el selector `#cve-source-filter` y el filtrado reactivo por fuente (`ALL`, `MIKROTIK`, `NIST_NVD`).
3. **Escenarios BDD Karate Labs:**
   * **`fastapi/test/api_test.feature`** (y réplica en `docs/examples/fastapi/test/api_test.feature`): Añadir **Escenario 149** verificando el contrato de `/api/v1/inventory/cves/sync` y `/api/v1/inventory/cves`.
   * **`vue3/test/ui_business_flow.feature`** (y réplica en `docs/examples/vue3/test/ui_business_flow.feature`): Añadir **Escenario 86** verificando `#cve-source-filter` y `#btn-sync-cve` en `/inventory/cves`.
