# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Gobernador y Sistema Anti-Saturación para Diagnósticos de Red y Clientes.

Protege la CPU de los routers MikroTik RouterOS v7 y los recursos del backend RoSGrid:
1. Anti-Thundering Herd: Caché de resultados diagnósticos por 15 segundos en KeyDB.
2. Semáforo Concurrente por Router: Máximo 3 peticiones de diagnóstico en paralelo por equipo.
3. Cuota por Router: Máximo 30 diagnósticos por minuto por router MikroTik.
4. Cuota por Usuario: Máximo 60 diagnósticos por minuto por técnico/operador.
5. Circuit Breaker Táctico: Si un router acumula 3 fallas/timeouts consecutivos, abre el circuito
   por 30 segundos, respondiendo de inmediato sin saturar los sockets de red.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import json
import logging
import uuid
from typing import Any, Optional

from fastapi import HTTPException, status

from src.redis_layer.client import get_redis_client

logger = logging.getLogger(__name__)


class DiagnosticGovernor:
    """Controlador central de tasa y concurrencia para diagnósticos sobre routers y abonados."""

    CACHE_TTL_SECONDS: int = 15
    MAX_CONCURRENT_PER_ROUTER: int = 3
    MAX_PER_MINUTE_PER_ROUTER: int = 30
    MAX_PER_MINUTE_PER_USER: int = 60
    CIRCUIT_BREAKER_FAILURES_THRESHOLD: int = 3
    CIRCUIT_BREAKER_COOLDOWN_SECONDS: int = 30

    @classmethod
    async def get_cached_ping(
        cls, tenant_id: uuid.UUID, device_id: uuid.UUID
    ) -> Optional[dict[str, Any]]:
        """Recupera el resultado de un diagnóstico reciente desde la caché de KeyDB si existe."""
        try:
            redis = get_redis_client()
            cache_key = f"rg:{tenant_id}:diag:cache:{device_id}"
            raw = await redis.get(cache_key)
            if not raw:
                return None

            ttl = await redis.ttl(cache_key)
            ttl_remaining = max(1, ttl) if ttl and ttl > 0 else cls.CACHE_TTL_SECONDS
            data = json.loads(raw)
            data["is_cached"] = True
            data["cache_ttl_remaining"] = ttl_remaining
            return data
        except Exception as e:
            logger.debug(f"Aviso al consultar caché diagnóstica para {device_id}: {e}")
            return None

    @classmethod
    async def set_cached_ping(
        cls,
        tenant_id: uuid.UUID,
        device_id: uuid.UUID,
        data: dict[str, Any],
        ttl_seconds: int = 15,
    ) -> None:
        """Almacena el resultado de un diagnóstico en KeyDB con TTL corto."""
        try:
            redis = get_redis_client()
            cache_key = f"rg:{tenant_id}:diag:cache:{device_id}"
            payload = {
                "device_id": str(data.get("device_id")),
                "assigned_ipv4": data.get("assigned_ipv4"),
                "last_reachability_status": data.get("last_reachability_status"),
                "ping_latency_ms": str(data.get("ping_latency_ms")) if data.get("ping_latency_ms") is not None else None,
                "packet_loss_pct": str(data.get("packet_loss_pct")) if data.get("packet_loss_pct") is not None else None,
                "message": data.get("message"),
            }
            await redis.set(cache_key, json.dumps(payload), ex=ttl_seconds)
        except Exception as e:
            logger.debug(f"Aviso al almacenar en caché diagnóstica para {device_id}: {e}")

    @classmethod
    async def check_user_rate_limit(
        cls, tenant_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Verifica que el usuario no exceda la tasa de diagnósticos permitida por minuto."""
        try:
            redis = get_redis_client()
            key = f"rg:{tenant_id}:diag:rate:user:{user_id}"
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 60)
            if count > cls.MAX_PER_MINUTE_PER_USER:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Límite de solicitudes de diagnóstico excedido (máximo 60 por minuto). Reintente en un momento.",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.debug(f"Aviso en verificación de rate limit de usuario: {e}")

    @classmethod
    @asynccontextmanager
    async def acquire_router_slot(
        cls, tenant_id: uuid.UUID, router_id: uuid.UUID
    ) -> AsyncGenerator[None, None]:
        """Adquiere un slot de concurrencia para el router MikroTik asegurando que no se sature.
        Verifica el Circuit Breaker, el límite por minuto y el semáforo concurrente in-flight.
        """
        redis = get_redis_client()
        cb_key = f"rg:{tenant_id}:diag:cb:{router_id}"
        rate_key = f"rg:{tenant_id}:diag:rate:router:{router_id}"
        inflight_key = f"rg:{tenant_id}:diag:inflight:{router_id}"

        # 1. Comprobar Circuit Breaker
        try:
            cb_val = await redis.get(cb_key)
            if cb_val == "OPEN":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Circuito de diagnóstico abierto: el router MikroTik presentó fallas recientes. Enfriamiento activo por 30s.",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.debug(f"Error consultando circuit breaker: {e}")

        # 2. Comprobar tasa por minuto en el router
        try:
            r_count = await redis.incr(rate_key)
            if r_count == 1:
                await redis.expire(rate_key, 60)
            if r_count > cls.MAX_PER_MINUTE_PER_ROUTER:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="El router MikroTik ha alcanzado el límite de 30 diagnósticos por minuto para proteger su CPU.",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.debug(f"Error verificando tasa por router: {e}")

        # 3. Adquirir semáforo de concurrencia in-flight
        acquired = False
        try:
            inflight = await redis.incr(inflight_key)
            if inflight == 1:
                await redis.expire(inflight_key, 10)
            if inflight > cls.MAX_CONCURRENT_PER_ROUTER:
                await redis.decr(inflight_key)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="El router MikroTik se encuentra atendiendo diagnósticos concurrentes (máximo 3 en paralelo). Reintente en breve.",
                )
            acquired = True
        except HTTPException:
            raise
        except Exception as e:
            logger.debug(f"Error en semáforo in-flight: {e}")

        try:
            yield
        finally:
            if acquired:
                try:
                    await redis.decr(inflight_key)
                except Exception as e:
                    logger.debug(f"Error liberando slot in-flight: {e}")

    @classmethod
    async def record_router_failure(
        cls, tenant_id: uuid.UUID, router_id: uuid.UUID
    ) -> None:
        """Registra un fallo o timeout contra el router y activa el Circuit Breaker si se supera el umbral."""
        try:
            redis = get_redis_client()
            fail_key = f"rg:{tenant_id}:diag:fail:{router_id}"
            fails = await redis.incr(fail_key)
            if fails == 1:
                await redis.expire(fail_key, 60)
            if fails >= cls.CIRCUIT_BREAKER_FAILURES_THRESHOLD:
                cb_key = f"rg:{tenant_id}:diag:cb:{router_id}"
                await redis.set(cb_key, "OPEN", ex=cls.CIRCUIT_BREAKER_COOLDOWN_SECONDS)
                logger.warning(
                    f"Circuit Breaker ACTIVADO para router {router_id} tras {fails} fallas consecutivas."
                )
        except Exception as e:
            logger.debug(f"Error registrando falla de router: {e}")

    @classmethod
    async def record_router_success(
        cls, tenant_id: uuid.UUID, router_id: uuid.UUID
    ) -> None:
        """Limpia el contador de fallas ante una ejecución exitosa."""
        try:
            redis = get_redis_client()
            fail_key = f"rg:{tenant_id}:diag:fail:{router_id}"
            cb_key = f"rg:{tenant_id}:diag:cb:{router_id}"
            await redis.delete(fail_key, cb_key)
        except Exception as e:
            logger.debug(f"Error limpiando fallas de router: {e}")
