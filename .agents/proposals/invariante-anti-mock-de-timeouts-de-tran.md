# Propuesta de Evolución Continua: Invariante Anti-Mock de Timeouts de Transferencia Pesada y Validación por Ítem en Respuestas HTTP 200 Batch

**Fecha de Registro:** 2026-11-06T02:09:33.700Z
**Rama Sugerida:** `evolution/invariante-anti-mock-de-timeouts-de-tran`
**Repositorio Destino:** `tecno-consultores/qa-testing-blueprints`
**Archivo Objetivo:** `.agents/skills/qa-11x-architect/SKILL.md`

## Justificación Empírica (Dogfooding / Producción)
Durante la actualización real de RouterOS v7 sobre equipos CHR en producción local, los mocks instantáneos (AsyncMock) ocultaron dos fallos reales de protocolo: (1) descargas síncronas de paquetes .npk (~21 MB) abortadas por timeouts HTTP cortos de 10s dejando archivos truncados de 0 bytes, y (2) respuestas HTTP 200 OK con payload de fallo interno por ítem (results[].status == 'FAILED' o status: 'ERROR: bad HTTP response'). Se recomienda incorporar la Invariante Anti-Mock de Timeouts de Transferencia y Estado por Ítem en Lote.

## Bloque / Cambio Propuesto
```markdown
### Invariante de Transferencia Síncrona y Validación por Ítem en Lote (Batch 200 OK)
1. **Separación de Timeouts de Telemetría vs. Transferencia de Imagen/Firmware:** Todo cliente HTTP que ejecute descargas de paquetes/firmware síncronas debe permitir override de timeout por petición (`>= 180s`) y purgar artefactos truncados (`0 bytes`) previos.
2. **Prohibición de Éxito Ciego por HTTP 200 en Endpoints Batch:** En vistas UI que consuman endpoints de ejecución masiva (`POST .../execute`), queda prohibido asumir éxito global por `HTTP 200 OK`; se debe inspeccionar `res.data.results[].status` por cada recurso objetivo.
```
