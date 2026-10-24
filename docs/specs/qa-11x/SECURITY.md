# Política de Seguridad (Security Policy)

En **Tecno Consultores**, la seguridad de nuestra infraestructura y del código que producimos es nuestra máxima prioridad. Este repositorio, **QA Testing Blueprints**, define la barrera arquitectónica que evita que código vulnerable llegue a nuestros entornos de producción.

Si descubres una vulnerabilidad en nuestras imágenes base, en los scripts de limpieza o en la configuración de los orquestadores efímeros, te pedimos que nos lo notifiques de inmediato siguiendo el proceso de divulgación responsable.

---

## 🛡️ Versiones Soportadas

Dado que este repositorio actúa como una plantilla arquitectónica y una base de conocimientos ("blueprints"), las actualizaciones de seguridad se aplican exclusivamente a la rama principal (`main`).

| Versión | Soportada |
| ------- | ------------------ |
| `main`  | ✅ Sí              |
| `< 1.0` | ❌ No              |

*Nota: Te recomendamos mantener siempre sincronizados los archivos de tu proyecto con el último commit de la rama `main` de este repositorio para heredar las reglas de SAST y dependencias más actualizadas.*

---

## 🔒 Mejores Prácticas y Hardening (Obligatorio)

Todo proyecto que implemente estos *blueprints* debe acatar las siguientes normativas de seguridad:

### 1. Manejo Estricto de Secretos (`.env`)
* **Prohibición de Commits:** Jamás se debe hacer commit de un archivo `.env` o `.env.*` (ej. `.env.test`, `.env.local`). Los archivos `.gitignore` incluidos en este repositorio están preconfigurados para bloquearlos.
* **Plantillas Seguras:** Utiliza siempre archivos `.env.example` que contengan únicamente la estructura de las variables con valores ficticios (ej. `API_KEY=tu_api_key_aqui`).
* **Inyección en CI/CD:** En entornos automatizados (GitHub Actions, GitLab CI), los secretos jamás deben escribirse en disco. Deben inyectarse en tiempo de ejecución utilizando el gestor de secretos de la plataforma (ej. `${{ secrets.PROD_API_KEY }}`).

### 2. Aislamiento de Volúmenes de Docker (Bind Mounts)
Nuestros orquestadores `docker-compose.qa.yml` utilizan volúmenes enlazados (`- .:/app`) para que la IA y el código interactúen rápidamente. 
* **Peligro de Propietario (Root):** Si un contenedor crea un archivo, por defecto pertenecerá a `root`. Nunca ejecutes scripts de terceros no confiables, ya que podrían sobrescribir archivos críticos del sistema anfitrión.
* **Restricción de Montaje:** Tienes prohibido montar directorios sensibles del host dentro del contenedor efímero. Nunca montes `/var/run/docker.sock`, `/etc`, o el directorio `/` de la máquina host en el entorno de QA.

### 3. Permisos Extendidos del Kernel (Capabilities)
Para ejecutar pruebas avanzadas de *Profiling* (como `py-spy` o `clinic.js`), algunos de nuestros blueprints requieren elevar privilegios con `cap_add: - SYS_PTRACE` y `security_opt: - seccomp:unconfined`.
* **Regla de Entorno:** Estos privilegios **SOLO** están permitidos en el archivo `docker-compose.qa.yml`. Queda estrictamente prohibido utilizar estos flags en los contenedores o manifiestos de producción, ya que permitirían a un atacante inspeccionar la memoria de otros procesos.

### 4. Contención de Agentes de IA
Este repositorio está diseñado para orquestar agentes autónomos (Claude Code, Hermes).
* **Sandboxing:** La IA nunca debe recibir credenciales de producción. El agente operará exclusivamente dentro de la red interna de contenedores efímeros.
* **Aislamiento de Red (Mocking):** Para evitar filtraciones de datos o ataques involuntarios de Denegación de Servicio (DoS) orquestados por un agente de IA, las pruebas unitarias y de integración temprana deben utilizar librerías de intercepción (`nock`, `pytest-mock`, `bats-mock`).

### 5. Auditoría de Infraestructura y Prevención de Fugas
* **Escaneo IaC Obligatorio:** Todo cambio propuesto a los manifiestos de Docker o scripts en bash es auditado estáticamente por **Trivy** para detectar escalamiento de privilegios o contenedores inseguros.
* **Barrera Pre-Commit (Lefthook):** Tienes estrictamente prohibido saltarte los hooks de Git. El hook de seguridad (`leaks-check`) interceptará de forma local cualquier intento de hacer commit de un archivo que contenga contraseñas en texto plano, tokens o API Keys, bloqueando la operación.

---

## 🐛 Alcance de las Vulnerabilidades a Reportar

Consideramos como incidentes críticos de seguridad en este repositorio:

1. **Fugas de Aislamiento (Container Escapes):** Cualquier falla en los `docker-compose.qa.yml` que permita a un script escapar del contenedor y alcanzar el host.
2. **Evasión de Políticas (Bypasses):** Métodos que permitan engañar a nuestros pipelines para aprobar Pull Requests con menos del 95% de cobertura real o ignorando alertas de SAST (Bandit, ESLint Security).
3. **Imágenes Base Comprometidas (Supply Chain):** Identificación de malware inyectado en la cadena de suministro de nuestra flota de imágenes (`sinfallas/*`).
4. **Ejecución de Comandos (RCE):** Fallos en los scripts auxiliares (`limpieza.sh`) que permitan inyección de comandos.

---

## 📩 Cómo reportar una vulnerabilidad

Por favor, **NO** abras un "Issue" público ni un "Pull Request" para reportar una vulnerabilidad de seguridad, ya que esto expone la falla antes de que podamos mitigarla.

Envía un correo electrónico directamente a nuestro equipo de seguridad:
📧 **soporte@tecnoconsultores.net**

**Formato recomendado para el reporte:**
*   **Tipo de vulnerabilidad:** (Ej. Evasión de validación SAST, Escalada de privilegios).
*   **Paso a paso para reproducirla:** Incluye comandos, los archivos afectados y un script de prueba de concepto (PoC).
*   **Impacto potencial:** Qué podría lograr un atacante interno o una IA mal configurada explotando este fallo.

## ⏱️ Nuestro Compromiso (SLA)

1. **Recepción:** Acusaremos recibo en un plazo máximo de 48 horas laborables.
2. **Evaluación:** Nuestro equipo evaluará la vulnerabilidad y confirmará su validez.
3. **Resolución:** Trabajaremos en un parche y emitiremos las instrucciones de mitigación para todos los proyectos internos que dependan de estos *blueprints*.
4. **Reconocimiento:** Una vez mitigado el problema, si lo deseas, te daremos crédito en nuestro archivo `CHANGELOG.md`.
