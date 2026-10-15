# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from locust import HttpUser, between, task


class FastApiStressUser(HttpUser):
    # Simula latencia natural entre acciones de usuario (1 a 3 segundos)
    wait_time = between(1, 3)

    def on_start(self):
        """Simula un proceso de autenticación o preparación antes de bombardear la API."""
        self.headers = {"Content-Type": "application/json"}
        # Auto-mock de token si la API lo requiere para las pruebas:
        self.token = "Bearer test-load-token-123"

    @task(3)
    def check_health(self):
        """Simula múltiples lecturas concurrentes de estado."""
        self.client.get("/health", headers=self.headers)

    @task(2)
    def simulate_heavy_computation(self):
        """Ataca endpoints de lectura intensiva para evaluar si bloquean el Event Loop asíncrono."""
        with self.client.get("/data?limit=100", headers={"Authorization": self.token}, catch_response=True) as response:
            if response.status_code in (200, 404):
                response.success()  # Marca como éxito temporal si la API no tiene esta ruta configurada aún.

    @task(1)
    def invalid_login_attempt(self):
        """Genera carga enviando peticiones POST para validar el rendimiento y parsing de Pydantic."""
        payload = {"username": "load_test", "password": "123", "client_id": "locust_bot"}
        self.client.post("/login", json=payload, headers=self.headers)
