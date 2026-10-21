# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.session import get_tenant_db_session
from src.models.inventory import Router
from src.redis_layer.client import get_redis_client
from src.services.cve_matcher import evaluate_router_cves

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics/fleet", tags=["Fleet Prometheus Metrics"])


def _validate_scrape_auth(authorization: str | None = Header(None)) -> None:
    expected_token = settings.ROSGRID_PROMETHEUS_SCRAPE_TOKEN
    if not expected_token:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "PROMETHEUS_UNAUTHORIZED", "message": "Bearer token requerido para scraping."},
        )
    token = authorization.split("Bearer ", 1)[1].strip()
    if token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "PROMETHEUS_UNAUTHORIZED", "message": "Token de scraping inválido."},
        )


def _format_metric_line(name: str, labels: dict[str, str], value: Any) -> str:
    labels_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
    return f"{name}{{{labels_str}}} {value}\n"


def _build_router_labels(r: Router) -> dict[str, str]:
    return {
        "tenant_id": str(r.tenant_id),
        "router_id": str(r.id),
        "identity": r.ros_identity or r.display_name,
        "model": r.model_name or "unknown",
    }


async def _get_router_ephemeral_telemetry(tenant_id: Any, router_id: Any) -> dict[str, float]:
    try:
        redis = get_redis_client()
        raw = await redis.hgetall(f"rg:{tenant_id}:router:{router_id}:state")
        cpu = float(raw.get("cpu_percent", 0.0)) if raw else 0.0
        mem = float(raw.get("memory_usage_ratio", 0.0)) if raw else 0.0
        return {"cpu_percent": cpu, "memory_usage_ratio": mem}
    except Exception:
        return {"cpu_percent": 0.0, "memory_usage_ratio": 0.0}


@router.get("", response_class=Response)
async def get_prometheus_fleet_metrics(
    db: AsyncSession = Depends(get_tenant_db_session),
    _auth: None = Depends(_validate_scrape_auth),
) -> Response:
    """Exportador dinámico de telemetría de flota en formato estándar Prometheus (cero persistencia en Postgres)."""
    query = select(Router).where(Router.admin_state == "PRODUCTION")
    result = await db.execute(query)
    routers = list(result.scalars().all())

    lines: list[str] = [
        "# HELP rosgrid_router_status Estado de conexion (1=ONLINE, 0=OFFLINE)\n",
        "# TYPE rosgrid_router_status gauge\n",
        "# HELP rosgrid_router_cpu_percent Porcentaje de CPU en vivo\n",
        "# TYPE rosgrid_router_cpu_percent gauge\n",
        "# HELP rosgrid_router_memory_usage_ratio Proporcion de memoria RAM utilizada\n",
        "# TYPE rosgrid_router_memory_usage_ratio gauge\n",
        "# HELP rosgrid_router_active_cves_count Cantidad de CVEs pendientes por criticidad\n",
        "# TYPE rosgrid_router_active_cves_count gauge\n",
    ]

    for r in routers:
        labels = _build_router_labels(r)
        status_val = 1 if r.is_reachable else 0
        lines.append(_format_metric_line("rosgrid_router_status", labels, status_val))

        telem = await _get_router_ephemeral_telemetry(r.tenant_id, r.id)
        lines.append(_format_metric_line("rosgrid_router_cpu_percent", labels, telem["cpu_percent"]))
        lines.append(_format_metric_line("rosgrid_router_memory_usage_ratio", labels, telem["memory_usage_ratio"]))

        cve_eval = evaluate_router_cves(r.id, r.display_name, r.ros_version)
        crit_labels = {**labels, "severity": "critical"}
        lines.append(_format_metric_line("rosgrid_router_active_cves_count", crit_labels, cve_eval.critical_count))
        high_labels = {**labels, "severity": "high"}
        lines.append(_format_metric_line("rosgrid_router_active_cves_count", high_labels, cve_eval.high_count))

    content = "".join(lines)
    return Response(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")
