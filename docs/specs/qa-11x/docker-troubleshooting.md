# Solución de Problemas de Docker (Troubleshooting)

Este documento centraliza los fallos más comunes al operar con los *blueprints* de QA. Dado que nuestra arquitectura se basa en contenedores efímeros y volúmenes *bind*, la mayoría de los errores no provienen del código, sino de la interacción entre el demonio de Docker, la red interna y el sistema operativo anfitrión.

---

## 1. El Síndrome del Disco Lleno y las Redes Agotadas

**Síntoma:** 
Al intentar ejecutar una prueba, recibes errores como `no space left on device` o `could not find an available, non-overlapping IPv4 address pool`.

**¿Por qué sucede?**
Docker sigue almacenando en caché de forma agresiva: imágenes colgantes (Dangling images), bases de datos temporales de Prometheus o Redes Bridge no destruidas. Además, los **nuevos volúmenes de caché persistentes** (`pnpm-store` y `uv-cache`) pueden crecer descontroladamente con el tiempo.

**La Solución:**
Ejecutar la purga profunda que apagará todos los perfiles ocultos y destruirá los volúmenes (`down -v`):

```bash
sudo ./limpieza.sh
# O utiliza la meta del Makefile en tu proyecto:
make clean-cache
```

---

## 2. Permisos Denegados en Archivos Generados

**Síntoma:** 
Linux te dice: `Permission denied` al intentar manipular reportes generados.

**¿Por qué sucede?**
Efecto secundario de los volúmenes *bind*. El contenedor efímero se ejecuta con `root` y crea los archivos (y carpetas como `prometheus_data/` o `graphify-out/`) con ese propietario.

**La Solución:**

```bash
sudo chown -R $USER:$USER .
```

---

## 3. Conflicto de Puertos con Prometheus (9090) o Graphify (8080)

**Síntoma:**
Error `Bind for 0.0.0.0:9090 failed: port is already allocated` al intentar lanzar el perfil de caos u observabilidad.

**¿Por qué sucede?**
Ya tienes una instancia de Prometheus o un servicio Nginx corriendo en tu máquina *host* o en otro proyecto Docker que olvidaste apagar.

**La Solución:**
Mata el contenedor secuestrador y baja toda la red del compose.

```bash
docker ps | grep 9090
docker kill <id_del_contenedor_conflictivo>
docker compose -f docker-compose.qa.yml --profile chaos down
```

---

## 4. Salida Abrupta: "Exit Code 137" (OOM Killer)

**Síntoma:** 
El contenedor muere arrojando `Exit Code 137`. Suele ocurrir con Playwright o Karate Labs, y especialmente al inyectar concurrencia masiva con Artillery o Locust.

**¿Por qué sucede?**
El *OOM Killer* de Linux asesinó al proceso por consumir toda la memoria RAM.

**La Solución:**
Limitar la concurrencia (`--workers=1`) o asignar más RAM al entorno de Docker.

---

## 5. Errores de Permisos al Ejecutar Profilers (SYS_PTRACE)

**Síntoma:**
Al utilizar herramientas avanzadas de análisis de recursos y profiling como `py-spy` en Python o `clinic.js` en Node.js, el contenedor falla con mensajes de permisos denegados o errores de `ptrace(PTRACE_ATTACH)`.

**¿Por qué sucede?**
Por defecto, Docker aplica un perfil estricto de `seccomp` que prohíbe que un proceso inspeccione la memoria de otro proceso mediante llamadas al sistema de bajo nivel.

**La Solución:**
Debes otorgar capacidades extendidas temporalmente al contenedor en tu archivo `docker-compose.qa.yml`:

```yaml
    cap_add:
      - SYS_PTRACE
```

---

## 6. ZAP (DAST) falla al escribir el reporte HTML

**Síntoma:** 
OWASP ZAP termina de auditar la API exitosamente, pero escupe un error de permisos `Permission Denied` al guardar el archivo `zap-report.html`.

**¿Por qué sucede?**
El contenedor de ZAP corre por defecto con el usuario no privilegiado `zap` interno, el cual no tiene permisos de escritura en el volumen *bind* mapeado desde tu máquina host.

**La Solución:**
Asegúrate de que la directiva `user: root` esté declarada en el servicio `zap` dentro de tu `docker-compose.qa.yml`. Luego, ejecuta `sudo ./limpieza.sh` para restaurar los permisos locales.

---

## 7. Pumba falla indicando "Cannot connect to the Docker daemon"

**Síntoma:** 
Al ejecutar la prueba de resiliencia (`docker compose --profile chaos up`), el contenedor de Pumba muere inmediatamente con un error de conexión al demonio.

**¿Por qué sucede?**
El demonio de Docker en distribuciones como Ubuntu Snap o Docker Desktop (Windows/Mac) a veces utiliza rutas virtuales distintas al socket estándar `/var/run/docker.sock`.

**La Solución:**
Asegúrate de que la ruta montada en tu orquestador coincida con tu configuración de host. Si usas WSL2 en Windows, debes activar la integración explícita de recursos y red en los ajustes de Docker Desktop.

---

## 8. Errores de Dependencias o Compilación en Node.js/Vue/React (Zero-Trust)

**Síntoma:**
Al ejecutar `make qa-unit` o instalar dependencias, paquetes como `esbuild`, `prisma`, `cypress` o `bcrypt` fallan quejándose de que no pudieron ejecutar su script de post-instalación.

**¿Por qué sucede?**
Como medida de seguridad estricta, inyectamos un archivo `.npmrc` configurado con `ignore-scripts=true`. Esto bloquea los ataques de cadena de suministro, pero también detiene a las librerías legítimas que necesitan compilar binarios locales.

**La Solución:**
Identifica la librería que falló y permítela explícitamente en el `package.json` utilizando herramientas de lista blanca (como `pnpm` config o `npm rebuild <paquete>`), o reconstruye el paquete específico al vuelo dentro del `Makefile` de tu proyecto, manteniendo el bloqueo global intacto.
