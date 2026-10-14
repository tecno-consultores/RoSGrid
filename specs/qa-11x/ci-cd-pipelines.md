# Pipelines de CI/CD (Integración Continua)

Este documento explica cómo trasladar la ejecución de nuestras pruebas locales a entornos automatizados (como GitHub Actions o GitLab CI). El objetivo principal es garantizar que **ningún código llegue a producción si no cumple con la regla estricta del 95% de cobertura y pasa todas las auditorías**.

## 1. El Anti-Patrón vs. La Vía "Blueprints"

**El enfoque tradicional (Anti-Patrón):**
Normalmente, los pipelines de CI instalan el lenguaje directamente en el *runner* de GitHub/GitLab (ej. usando `actions/setup-node` o `actions/setup-python`), luego ejecutan `npm install` y finalmente corren los tests.
*   **¿Por qué está mal para nosotros?** Porque rompe el aislamiento. El *runner* de CI podría tener dependencias globales preinstaladas de Ubuntu que enmascaran errores, haciendo que el pipeline pase en GitHub pero falle en tu servidor Proxmox de producción.

**Nuestro enfoque (Blueprints):**
El *runner* de CI se trata como una máquina "tonta" cuyo único trabajo es tener Docker instalado. **Ejecutamos exactamente los mismos comandos encapsulados de los Makefiles que usamos en local**. 
*   **¿Por qué es así?** Paridad absoluta. Si `make qa-unit` pasa en tu laptop, pasará en CI y funcionará en producción. Toda la inteligencia, herramientas (SAST, Mutación, BATS), configuraciones `.npmrc` y dependencias viven dentro de las imágenes `sinfallas/*` y se respaldan en los volúmenes de caché.

---

## 2. Anatomía de la Ejecución en CI (Nivel 11X)

Para que el pipeline funcione correctamente, debe seguir una estructura estricta:

### Paso 0: Auditoría de Infraestructura (Trivy)
Antes de descargar dependencias de lenguaje, escaneamos estáticamente los manifiestos de Docker para prevenir inyecciones a la infraestructura o escalamiento de privilegios.
### Paso 1: Checkout y Preparación
Clonar el código fuente. No necesitamos instalar Python, Node ni dependencias de sistema.
### Paso 2: Ejecución Efímera Base (El Núcleo)
Lanzar las suites utilizando los comandos definidos en el `Makefile` (ej. `make qa-lint`, `make qa-unit`). Si la prueba de cobertura detecta menos del 95%, o si fallan las métricas de complejidad, arrojará un código de salida `1` (Exit Code 1) bloqueando el *merge*.
### Paso 3: Seguridad Dinámica (DAST)
OWASP ZAP levanta un ataque ligero (*Baseline Scan*) sobre el contenedor vivo para auditar vulnerabilidades en la red.
### Paso 4: Resiliencia, Caos y Observabilidad
Se activa el perfil oculto `--profile chaos` inyectando latencia con Pumba y oleadas de estrés concurrente, mientras Prometheus recopila métricas.
### Paso 5: Extracción de Artefactos (Reportes)
Como utilizamos volúmenes *bind*, cuando el contenedor efímero muere, deja los reportes HTML y JSON físicamente en el disco del *runner*. El pipeline toma esa carpeta y la sube como un "Artifact" para que el equipo pueda descargarlo.
### Paso 6: Limpieza
Ejecutar `make clean-cache` o `./limpieza.sh` para destruir las cachés de volumen y no saturar el almacenamiento del *runner*.

---

## 3. Ejemplo Práctico: GitHub Actions

Aquí tienes la plantilla base para `.github/workflows/qa-pipeline.yml`. Al usar los `Makefiles` corporativos, el pipeline es extremadamente limpio y fácil de leer.

```yaml
name: QA Testing Blueprint Pipeline (Nivel 11X)

on:
  pull_request:
    branches: [ "main", "develop" ]

jobs:
  auditoria-y-pruebas:
    name: 🛡️ Auditoría Estricta (95% Coverage) y Resiliencia
    runs-on: ubuntu-latest

    steps:
      - name: 1️⃣ Checkout del código
        uses: actions/checkout@v4

      - name: 2️⃣ Inyectar Secretos de Entorno
        run: |
          echo "API_KEY=${{ secrets.PROD_API_KEY }}" >> .env
          echo "DB_PASS=${{ secrets.DB_PASS }}" >> .env

      - name: 3️⃣ Auditoría de Infraestructura y Contenedores (Trivy)
        run: |
          ./auditar-infra.sh

      - name: 4️⃣ Análisis Estático, Complejidad y Formateo
        # Ejecuta linting, tipeo (Mypy/TS) y reglas de complejidad.
        run: make qa-lint

      - name: 5️⃣ Ejecutar Suite Efímera con Intercepción de Red
        # Si la cobertura es menor a 95%, este comando falla y aborta el pipeline.
        run: make qa-unit

      - name: 6️⃣ Pruebas de Mutación (Anti-Falsos Positivos)
        # Asegura que las pruebas realmente validen la lógica.
        run: make qa-mutation

      - name: 7️⃣ Seguridad Dinámica DAST (OWASP ZAP)
        # Levanta la API en segundo plano y lanza un Baseline Scan.
        # (Nota: Ignorar este paso si es un script Bash o Python Standalone)
        run: |
          docker compose -f docker-compose.qa.yml up -d api
          docker compose -f docker-compose.qa.yml run --rm zap zap-baseline.py -t http://api:3000 -r zap-report.html

      - name: 8️⃣ Ingeniería del Caos y Observabilidad (Prometheus + Pumba)
        # Activa el perfil oculto para inyectar latencia y levantar Prometheus automáticamente.
        # (Nota: Si tu proyecto es un script Bash o Python puro, cambia '--profile chaos' por '--profile observability')
        run: docker compose -f docker-compose.qa.yml --profile chaos up --abort-on-container-exit stress_test

      - name: 9️⃣ Archivar Reportes de Calidad (Artefactos)
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: qa-reports
          path: |
            coverage/
            coverage_report/
            reports/
            stryker.html
            zap-report.html
            chaos-report.html
            chaos-report.json
          retention-days: 7

      - name: 🔟 Limpieza del Entorno
        if: always()
        run: make clean-cache
```
