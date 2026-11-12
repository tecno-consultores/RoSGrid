# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Worker de Comprobación Pasiva de Nuevas Versiones contra GitHub Releases.

Consulta de forma estrictamente pasiva y fail-silent el API de GitHub Releases
para notificar al SuperAdmin/TenantAdmin sobre nuevas versiones disponibles (Zero Auto-Update).
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from src.core.config import settings
from src.redis_layer.client import get_redis_client

logger = logging.getLogger(__name__)

VERSION_CHECK_REDIS_KEY = "rg:system:version_check"
VERSION_CHECK_COOLDOWN_KEY = "rg:system:version_check:manual_cooldown"
ALLOWED_GITHUB_RELEASE_PREFIX = "https://github.com/tecno-consultores/RoSGrid/releases"
DEFAULT_RELEASES_PAGE = "https://github.com/tecno-consultores/RoSGrid/releases"


def parse_semver_tuple(raw: str | None) -> tuple[int, int, int] | None:
    """Extrae la tupla (major, minor, patch) ignorando prefijos v/V y descartando pre-releases (CC <= 4)."""
    if not raw:
        return None
    cleaned = raw.strip().lstrip("vV")
    if "-" in cleaned or "+" in cleaned:
        return None
    parts = cleaned.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return None
    return int(parts[0]), int(parts[1]), int(parts[2])


def is_newer_semver(latest_raw: str | None, current_raw: str | None) -> bool:
    """Retorna True únicamente si latest es semver válido estrictamente mayor que current (CC <= 2)."""
    t_lat = parse_semver_tuple(latest_raw)
    t_cur = parse_semver_tuple(current_raw)
    if not t_lat or not t_cur:
        return False
    return t_lat > t_cur


def _sanitize_release_url(raw_url: Any) -> str:
    """Sanitiza URLs de release para prevenir open redirects o esquemas maliciosos (CC <= 2)."""
    url_str = str(raw_url or "").strip()
    if url_str.startswith(ALLOWED_GITHUB_RELEASE_PREFIX):
        return url_str
    return DEFAULT_RELEASES_PAGE


def _decode_redis_val(val: Any) -> str | None:
    """Decodifica un campo de KeyDB (bytes o str) tolerando nulos (CC <= 2)."""
    if val is None:
        return None
    return val.decode("utf-8") if isinstance(val, bytes) else str(val)


async def get_version_check_status() -> dict[str, Any]:
    """Obtiene el estado actual de comprobación de versión recalculando en caliente (CC <= 3)."""
    current = settings.VERSION
    raw_hash: dict[Any, Any] = {}
    try:
        redis = get_redis_client()
        raw_hash = await redis.hgetall(VERSION_CHECK_REDIS_KEY) or {}
    except Exception as exc:
        logger.debug("Lectura de KeyDB para version-check omitida: %s", exc)

    latest = _decode_redis_val(raw_hash.get("latest_version") or raw_hash.get(b"latest_version"))
    rel_url = _sanitize_release_url(_decode_redis_val(raw_hash.get("release_url") or raw_hash.get(b"release_url")))
    rel_name = _decode_redis_val(raw_hash.get("release_name") or raw_hash.get(b"release_name"))
    pub_at = _decode_redis_val(raw_hash.get("published_at") or raw_hash.get(b"published_at"))
    chk_at = _decode_redis_val(raw_hash.get("last_checked_at") or raw_hash.get(b"last_checked_at"))
    status_str = _decode_redis_val(raw_hash.get("last_status") or raw_hash.get(b"last_status")) or "pending"

    return {
        "enabled": settings.ROSGRID_VERSION_CHECK_ENABLED,
        "current_version": current,
        "latest_version": latest,
        "update_available": is_newer_semver(latest, current) if latest else False,
        "release_url": rel_url,
        "release_name": rel_name,
        "published_at": pub_at,
        "last_checked_at": chk_at,
        "last_status": status_str,
    }


async def _save_version_check_result(
    status_str: str,
    release_data: dict[str, Any] | None = None,
) -> None:
    """Persiste en KeyDB el resultado del chequeo de versión (CC <= 3)."""
    try:
        redis = get_redis_client()
        now_iso = datetime.now(UTC).isoformat()
        mapping: dict[str, str] = {
            "last_status": status_str,
            "last_checked_at": now_iso,
        }
        if release_data:
            mapping["latest_version"] = str(release_data.get("tag_name") or "").lstrip("vV")
            mapping["release_name"] = str(release_data.get("name") or "")[:120]
            mapping["published_at"] = str(release_data.get("published_at") or now_iso)
            mapping["release_url"] = _sanitize_release_url(release_data.get("html_url"))
        await redis.hset(VERSION_CHECK_REDIS_KEY, mapping=mapping)  # type: ignore[arg-type]
    except Exception as exc:
        logger.debug("Persistencia de version check en KeyDB omitida: %s", exc)


async def _check_cooldown_active(force: bool) -> bool:
    """Comprueba y aplica el cooldown manual de 60 segundos en KeyDB si force=True (CC <= 3)."""
    if not force:
        return False
    try:
        redis = get_redis_client()
        is_cooldown = await redis.exists(VERSION_CHECK_COOLDOWN_KEY)
        if is_cooldown:
            return True
        await redis.set(VERSION_CHECK_COOLDOWN_KEY, "1", ex=60)
    except Exception as exc:
        logger.debug("Fallo en verificación de cooldown de version check: %s", exc)
    return False


async def check_github_release_once(force: bool = False) -> dict[str, Any]:
    """Consulta GitHub Releases de forma segura y fail-silent actualizando el caché (CC <= 5)."""
    if not settings.ROSGRID_VERSION_CHECK_ENABLED:
        return await get_version_check_status()

    if await _check_cooldown_active(force):
        return await get_version_check_status()

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"RoSGrid/{settings.VERSION}",
    }
    try:
        async with httpx.AsyncClient(timeout=5.0, headers=headers) as client:
            resp = await client.get(settings.ROSGRID_GITHUB_RELEASES_API_URL)
        if resp.status_code == 200:
            data = resp.json()
            if not data.get("draft") and not data.get("prerelease"):
                await _save_version_check_result("ok", data)
            else:
                await _save_version_check_result("skipped_prerelease")
        elif resp.status_code in (403, 429):
            await _save_version_check_result("rate_limited")
        else:
            await _save_version_check_result(f"http_{resp.status_code}")
    except (httpx.HTTPError, OSError) as exc:
        logger.debug("Chequeo de versiones GitHub omitido fail-silent: %s", exc)
        await _save_version_check_result("offline_skipped")

    return await get_version_check_status()


async def _version_sleep_interval(stop_event: asyncio.Event | None, interval: int) -> bool:
    """Espera el intervalo indicado o retorna True si se activa stop_event (CC <= 3)."""
    if not stop_event:
        await asyncio.sleep(interval)
        return False
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=float(interval))
        return True
    except (asyncio.TimeoutError, TimeoutError):
        return False


async def version_check_worker_loop(stop_event: asyncio.Event | None = None) -> None:
    """Ciclo en segundo plano para comprobación periódica pasiva de nuevas versiones (CC <= 4)."""
    if not settings.ROSGRID_VERSION_CHECK_ENABLED:
        logger.info("VersionCheckWorker desactivado por configuración.")
        return

    logger.info(
        "Iniciando VersionCheckWorker (intervalo: %ds)...",
        settings.ROSGRID_VERSION_CHECK_INTERVAL_SECONDS,
    )
    if await _version_sleep_interval(stop_event, 5):
        return

    interval = max(60, settings.ROSGRID_VERSION_CHECK_INTERVAL_SECONDS)
    while not (stop_event and stop_event.is_set()):
        try:
            await check_github_release_once(force=False)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Fallo no fatal en ciclo de version check: %s", exc)
        if await _version_sleep_interval(stop_event, interval):
            break
