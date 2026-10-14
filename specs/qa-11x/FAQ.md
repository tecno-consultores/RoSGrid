# Preguntas Frecuentes (FAQ) - QA Testing Blueprints

Este documento resuelve las dudas arquitectónicas y los errores más comunes al implementar y ejecutar los ecosistemas de prueba estandarizados (Nivel 11X) en este repositorio.

## 🏗️ Filosofía y Ejecución

### ¿Por qué no puedo ejecutar `npm install`, `pip install` o las pruebas directamente en mi máquina local?
Para garantizar **inmutabilidad y paridad absoluta con producción**. El problema de "en mi máquina sí funciona" suele deberse a versiones globales ocultas de Node, Python o variables de entorno residuales. Al forzar el uso de contenedores efímeros (a través de los comandos simplificados como `make qa-unit`), el entorno nace completamente virgen, utilizando cachés aislados, ejecuta la suite y se autodestruye.

### Lefthook bloqueó mi `git commit`, ¿qué hago?
Nuestra política es **"Fail & Forbid" (Rechazo Educativo)**. Si Lefthook detectó errores de formato o un secreto *hardcodeado*, abortará tu commit. NO intentes evadirlo con `--no-verify`. Debes ejecutar el comando sugerido en la terminal (ej. `ruff format` o `Prettier`), revisar que el código haya quedado bien, y volver a intentar hacer commit.

### Todo mi código funciona y mi cobertura está en 100%, ¿por qué el pipeline sigue arrojando fallo?
Si superaste el 95% de cobertura, el pipeline ahora evalúa la **Deuda Técnica y Seguridad**. Es altamente probable que:
1. Herramientas como `SonarJS` (Node) o `Radon` (Python) detectaron **Complejidad Ciclomática** alta (Código Espagueti). Tendrás que refactorizar las funciones muy largas.
2. Fallaste los estándares de calidad de código visual (`Prettier`, `Ruff`).
3. Introdujiste vulnerabilidades detectadas por `ESLint Security` o `bandit` (SAST), o fallaste el escaneo dinámico de `OWASP ZAP` (DAST).
4. El rendimiento de Lighthouse (Vue3) bajó de 90.

### ¿Qué significa "contenedor efímero" y cómo guardo los reportes si el contenedor se borra?
Un contenedor efímero se crea dinámicamente con el flag `--rm`. Nace, ejecuta un comando único y muere. Los reportes (como la cobertura HTML o Flamegraphs de Profiling) no se pierden porque el `docker-compose.qa.yml` utiliza **volúmenes bind** (`- .:/app`), guardando los resultados directamente en tu disco duro físico.

## 🛡️ Herramientas y Casos Específicos

### ¿Por qué estoy obligado a usar librerías de Mocking (`nock`, `pytest-mock`) si la API a la que llamo es rápida?
Para garantizar el **determinismo y el aislamiento total**. Si tu prueba depende del internet o de una API de terceros que se cae temporalmente, tu prueba fallará (falso negativo) rompiendo el pipeline de CI/CD. Las pruebas unitarias jamás deben salir del contenedor.

### Estoy probando un script en Bash que formatea discos o reinicia servicios. ¿No es peligroso?
Es **extremadamente peligroso y está estrictamente prohibido**. Debes utilizar la técnica de *Mocking*. La imagen `sinfallas/base-bash-qa:latest` trae la librería `bats-mock` para interceptar binarios peligrosos e inyectar respuestas falsas.

### ¿Qué diferencia hay entre SAST (Bandit/ESLint) y DAST (OWASP ZAP)?
*   **SAST (Estático):** Escanea tu código fuente escrito como si fuera un libro, buscando vulnerabilidades de sintaxis o lógica antes de que el programa corra.
*   **DAST (Dinámico):** Es un hacker automatizado. Necesita que tu API esté viva y corriendo. ZAP le envía peticiones maliciosas reales (XSS, SQLi) evaluando si el servidor se rompe o expone cabeceras inseguras en las respuestas HTTP.

### ¿Qué son las Pruebas de Mutación (Stryker / mutmut)?
No prueban tu código, **prueban tus pruebas**. Alteran intencionalmente el código fuente original (cambian un `>` por `<`, o un `true` por `false`) y corren tu suite de pruebas de nuevo. Si tus pruebas unitarias dicen "Todo pasó" a pesar del daño, significa que tus pruebas tienen falsos positivos (no están auditando nada realmente).

### ¿Para qué utilizar Karate Labs (BDD) si ya tengo Vitest, Pytest o Supertest evaluando el código?
Porque cumplen propósitos distintos. Vitest/Pytest prueban cajas blancas (conocen el código interno). Karate Labs evalúa cajas negras: ataca el puerto vivo de la aplicación emulando a un usuario real mediante lenguaje natural (Gherkin).

### ¿Por qué me obligan a inyectar un middleware de Prometheus en mi código fuente?
Porque la Ingeniería del Caos a ciegas no sirve de nada. Si inyectamos latencia o pérdida de paquetes con Pumba, necesitamos ver el impacto real en los tiempos de respuesta (Métricas RED) de forma instantánea. Los middlewares seleccionados (`express-prom-bundle`, `prometheus-fastapi-instrumentator`) son de impacto cero y no alteran tu lógica de negocio.
*   **Nota para scripts (Bash/Python):** Para tareas efímeras que no levantan un servidor HTTP, no usamos middlewares. En su lugar, utilizamos inyecciones de comandos (ej. `curl`) para empujar las métricas hacia un **Pushgateway**, permitiendo que Prometheus las recolecte después de que el script haya terminado de ejecutarse.

### ¿Por qué Pumba (Caos) necesita acceder al socket de Docker (`/var/run/docker.sock`) si nuestra política prohíbe esto?
Porque la **Ingeniería del Caos** consiste en simular fallos catastróficos a nivel de infraestructura. Pumba necesita comunicarse con el demonio de Docker para interceptar el tráfico de red de otros contenedores o apagarlos abruptamente. Esta es una **excepción de seguridad documentada**, y es por ello que está oculta bajo el flag `--profile chaos` en el orquestador. Jamás se debe activar en un servidor de producción.

## 🚨 Resolución de Problemas (Troubleshooting)

### Docker me da "Permission Denied" o "ptrace(PTRACE_ATTACH)" al ejecutar Profilers (`clinic.js` o `py-spy`).
Por seguridad, el demonio de Docker bloquea la inspección de memoria entre procesos.
**Solución:** Asegúrate de que el servicio en el `docker-compose.qa.yml` tenga habilitados los privilegios del kernel:
```yaml
    cap_add:
      - SYS_PTRACE
    security_opt:
      - seccomp:unconfined
```

### ZAP (DAST) falla al escribir el `zap-report.html` (Permission Denied)
El contenedor de ZAP corre por defecto con un usuario no privilegiado que no tiene permisos de escritura en el volumen *bind* del host.
**Solución:** Asegúrate de incluir explícitamente la directiva `user: root` en la definición del servicio `zap` en tu `docker-compose.qa.yml`. Luego, ejecuta `sudo ./limpieza.sh` en tu host para restaurar los permisos.

### Docker se quedó sin espacio, está muy lento o las pruebas fallan porque detectan código viejo.
Los contenedores y gestores acumulan cachés masivos. 
**Solución:** Ejecuta el script maestro de purga como administrador:
```bash
sudo ./limpieza.sh
```
Esto fuerza un `docker system prune -af` y borra reportes y dependencias huérfanas, limpiando también los volúmenes nombrados de caché (`pnpm-store` o `uv-cache`).

### El contenedor E2E de Vue 3 (Playwright / Lighthouse) se queja de un conflicto de red al intentar alcanzar la interfaz.
Asegúrate de haber levantado primero el servidor mock de producción en segundo plano ejecutando `docker compose -f docker-compose.qa.yml up -d ui-prod` antes de lanzar el comando efímero a través del Makefile:
```bash
make qa-e2e
```
