# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid

from locust import HttpUser, between, task


class RoSGridStressUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.headers = {
            "Content-Type": "application/json",
            "X-CSRF-Token": "qa-load-test-csrf",
        }

    @task(4)
    def check_health(self) -> None:
        """Verifica disponibilidad continua bajo inyección de jitter de Pumba."""
        self.client.get("/health", headers=self.headers)

    @task(2)
    def check_prometheus_metrics(self) -> None:
        """Verifica que el colector de métricas RED responda sin bloqueos."""
        self.client.get("/metrics")

    @task(2)
    def simulate_inventory_read_unauthorized_or_cached(self) -> None:
        """Evalúa velocidad de respuesta del guard de sesión/RBAC bajo carga."""
        with self.client.get(
            "/api/v1/inventory/routers",
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code in (200, 401):
                response.success()

    @task(1)
    def invalid_login_attempt_validation(self) -> None:
        """Estresa el parser Pydantic v2 y el control de intentos fallidos."""
        payload = {
            "tenant_slug": "isp-chaos-test",
            "email": f"bot-{uuid.uuid4().hex[:6]}@isp.net",
            "password": "invalid_password_123",
        }
        with self.client.post(
            "/api/v1/auth/login",
            json=payload,
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code in (401, 422, 423, 429):
                response.success()
