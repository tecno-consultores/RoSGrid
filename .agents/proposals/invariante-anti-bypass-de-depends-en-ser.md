# Propuesta de Evolución Continua: Invariante Anti-Bypass de Depends() en Servicios FastAPI/MCP y Formato Conciso de CHANGELOG.md

**Fecha de Registro:** 2026-11-09T03:05:18.951Z
**Rama Sugerida:** `evolution/invariante-anti-bypass-de-depends-en-ser`
**Repositorio Destino:** `tecno-consultores/qa-testing-blueprints`
**Archivo Objetivo:** `.agents/skills/qa-11x-architect/SKILL.md`

## Justificación Empírica (Dogfooding / Producción)
En FastAPI, los decoradores Depends(require_roles(...)) solo se ejecutan cuando la función es invocada a través del enrutador HTTP. Si un despachador JSON-RPC / MCP interno invoca directamente la función Python de un controlador o servicio, Depends() es omitido. Además, los CHANGELOG.md generados por sub-tarea acumulan miles de líneas y cabeceras duplicadas si no se exige formato conciso por versión.

## Bloque / Cambio Propuesto
```markdown
### Invariante de Defensa RBAC en Capa de Servicio (Anti-Depends Bypass) y Concisión de CHANGELOG
- **Defensa RBAC en Capa de Servicio:** Nunca confíes exclusivamente en `Depends(require_roles(...))` del router HTTP cuando las funciones de mutación puedan ser invocadas internamente (ej. desde un despachador MCP o worker). Valida explícitamente `claims["rol"]` al inicio de la función de servicio y enruta toda herramienta MCP de mutación por `ApprovalRequest` (`AWAITING_APPROVAL`).
- **Higiene de `CHANGELOG.md`:** Mantén un único encabezado por versión publicada con viñetas ejecutivas concisas (1-2 líneas por cambio), prohibiendo volcar bitácoras internas de sub-hitos.
```
