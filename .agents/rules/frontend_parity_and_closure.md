# Regla de Paridad Terminal ↔ Frontend y Protocolo de Cierre (RoSGrid)

## 1. Invariante de Paridad Terminal ↔ Frontend

1. **Cero Funcionalidades Exclusivas de Consola:** Cualquier acción administrativa, de soporte u operacional concebida para ser ejecutada desde el terminal (con la única excepción de la instalación inicial desatendida del sistema) DEBE contar con su pantalla correspondiente en el frontend Vue 3.
2. **Cero Endpoints Huérfanos en la API:** Ninguna ruta o función de `fastapi/src/api/v1/` puede existir sin una interfaz de usuario asociada en el frontend que permita su visualización, configuración y ejecución de pruebas interactivas.
3. **Sincronización Bidireccional de Autoría:** Todo script de terminal de mantenimiento que emita tokens o modifique sesiones debe sincronizar sus metadatos en KeyDB/Redis (`issued_by_username: "CLI (Terminal)"`) para garantizar su visibilidad y revocación inmediata desde la pantalla de Sesiones Activas & Kill-Switch (`ActiveSessionsKillSwitchView.vue`).

## 2. Auditoría Preventiva de Vulnerabilidades en Código Nuevo

Ante cualquier nueva funcionalidad o endpoint expuesto:

1. **Validación de Estados de Usuario:** Comprobar rigurosamente que los usuarios inactivos (`is_active = False`) o bloqueados (`is_locked = True`) no puedan emitir tokens ni ejecutar acciones privilegiadas.
2. **Aislamiento Multi-Tenant:** Toda consulta de base de datos debe enlazarse al contexto de tenant (`set_tenant_context`) y verificar pertenencia estricta.
3. **SAST Automatizado:** Ejecutar Bandit (`bandit -r src/ -ll`) y escaneo de dependencias en Docker efímero con 0 alertas High/Medium.
4. **Protección Anti-XSS y Anti-CSRF:** En frontend, evitar `v-html` con datos dinámicos no sanitizados; en backend, requerir tokens Anti-CSRF o cabeceras Bearer según directrices OWASP.

## 3. Protocolo Obligatorio de Cierre y Publicación

Antes de dar por concluida una tarea y hacer push a GitHub:

1. **Ejecución Completa de Pruebas en Docker:**
   - Backend: `uv run pytest tests/ --cov=src` (cobertura >= 95%).
   - Frontend: `npx vitest run` y `npx vue-tsc --noEmit` (100% pruebas aprobadas, 0 errores).
2. **Sincronización Documental Integral:**
   - Actualizar especificaciones en `specs/`.
   - Actualizar manuales técnicos en `docs/`.
   - Actualizar `CHANGELOG.md` y `ROADMAP.md`.
   - Certificar sintaxis con `markdownlint-cli` (0 errores).
3. **Limpieza e Higiene:** Ejecutar `./limpieza.sh` previo a cualquier commit.
4. **Git Commit & Push:** Usar Conventional Commits (`feat:`, `fix:`, `docs:`) y subir a `origin/main`.
