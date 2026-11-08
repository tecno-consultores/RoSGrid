# Propuesta de Evolución Continua: Invariante de UUID Dinámico para Idempotency-Key en Karate Labs BDD

**Fecha de Registro:** 2026-11-08T22:14:23.540Z
**Rama Sugerida:** `evolution/invariante-de-uuid-dinamico-para-idempot`
**Repositorio Destino:** `tecno-consultores/qa-testing-blueprints`
**Archivo Objetivo:** `.agents/skills/qa-11x-architect/SKILL.md`

## Justificación Empírica (Dogfooding / Producción)
Durante el cierre v1.0.0 de RoSGrid se detectó que escenarios Karate Labs BDD (api_test.feature) para endpoints mutables (POST/PUT/PATCH/DELETE) fallaban con HTTP 400 (falta Idempotency-Key) o HTTP 409/422 en re-ejecuciones contra KeyDB vivo por usar UUIDs estáticos. Inyectar dinámicamente java.util.UUID.randomUUID() + '' garantiza idempotencia limpia en ejecuciones repetidas.

## Bloque / Cambio Propuesto
```markdown
### Dynamic Idempotency-Key in Karate Labs BDD
All mutable requests (`POST`, `PUT`, `PATCH`, `DELETE`) in `api_test.feature` against APIs enforcing `IdempotencyMiddleware` MUST include `And header Idempotency-Key = java.util.UUID.randomUUID() + ''` (unless specifically testing missing key `400`), preventing `400 Bad Request` or `409/422` collisions across repeated runs against live Redis/KeyDB.
```
