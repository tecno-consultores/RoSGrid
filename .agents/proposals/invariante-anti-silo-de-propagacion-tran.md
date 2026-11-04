# Propuesta de Evolución Continua: Invariante Anti-Silo de Propagación Transversal de Estado, Ciclo Temporal de 3 Fases y Auditoría Semántica Anti-UUID Crudo

**Fecha de Registro:** 2026-11-04T18:25:54.973Z
**Rama Sugerida:** `evolution/invariante-anti-silo-de-propagacion-tran`
**Repositorio Destino:** `tecno-consultores/qa-testing-blueprints`
**Archivo Objetivo:** `.agents/skills/qa-11x-architect/SKILL.md`

## Justificación Empírica (Dogfooding / Producción)
Durante pruebas UAT reales en RoSGrid se descubrió que aun teniendo >= 95% de cobertura unitaria en Backend (pytest) y Frontend (Vitest), existían desconexiones funcionales entre módulos porque los tests unitarios probaban cada módulo en un silo aislado usando mocks en la frontera (ej. crear una ventana de mantenimiento en POST /maintenance/windows devolvía 201 en su test, y el Wallboard NOC probaba el contador de mantenimiento inyectando un mock manual con admin_state='MAINTENANCE', pero GET /inventory/routers jamás cruzaba las ventanas activas reales). Asimismo, las entidades con vigencia temporal solo probaban 2 estados estáticos (Cancelada vs Programada, omitiendo el estado intermedio En Curso cuando starts_at <= now <= ends_at), y el uso de patch('...write_audit_log', AsyncMock) ocultaba que se estaba registrando el UUID crudo claims['sub'] en lugar del username legible humano.

## Bloque / Cambio Propuesto
```markdown
### Invariante Anti-Silo de Propagación Transversal de Estado, Ciclo Temporal de 3 Fases y Auditoría Semántica (Anti-Silo & Cross-Module State Propagation Invariant)

La cobertura de código (`>= 95%`) mide el porcentaje de líneas existentes ejecutadas, pero NO detecta desconexiones entre módulos cuando las pruebas abusan de mocks en las fronteras (*Silo Mock Blindness*) o utilizan aserciones tautológicas. Toda suite bajo el Estándar QA 11X DEBE cumplir obligatoriamente:

1. **Propagación Transversal de Estado sin Mocks Intermedios (*Cross-Module State Propagation*):**
   - Está prohibido dar por válido un test de mutación verificando únicamente el `HTTP 200/201` del endpoint mutador mientras los módulos consumidores usan fixtures estáticos desconectados.
   - Cuando una operación en el Módulo A modifica el estado operativo de una entidad (ej. programar/cancelar ventanas de mantenimiento, activar Safe Mode transaccional, emparejar recursos de red o cambiar identidades), el test DEBE invocar inmediatamente los endpoints de consulta y stores del Módulo B consumidor **sin mocks intermedios**, certificando que el estado efectivo, contadores KPI, insignias y mapas reflejan la mutación de extremo a extremo.
2. **Ciclo de Vida Temporal de 3 Fases (*3-Phase Temporal Lifecycle Assertion*):**
   - Toda entidad gobernada por ventanas de tiempo o TTL (`starts_at` / `ends_at`, timers de reversión Safe Mode, expiración de sesiones/tokens o leases) DEBE probarse obligatoriamente en sus **3 fases**:
     - **Fase 1 (`t < starts_at`):** Estado Programado / Pendiente (`Programada`).
     - **Fase 2 (`starts_at <= t <= ends_at`):** Estado Activo / En Curso (`En Curso`, proyectando el estado operativo a todos los módulos consumidores).
     - **Fase 3 (`t > ends_at` o Cancelado):** Estado Expirado / Purgado / Revertido (restaurando el estado nominal original y generando traza de auditoría).
3. **Prohibición de Mocks Ciegos en Auditoría y Aserción Semántica Anti-UUID Crudo:**
   - Prohibido reemplazar funciones de auditoría (`write_audit_log`) con `AsyncMock` vacíos sin inspeccionar la carga útil persistida. Los tests DEBEN certificar que los campos de actor y recurso visibles en la UI resuelvan a nombres humanos legibles (`username`, `display_name`) y nunca expongan UUIDs v4 crudos (`claims["sub"]`) ni etiquetas `else` genéricas engañosas en cintas de eventos o bitácoras.
```
