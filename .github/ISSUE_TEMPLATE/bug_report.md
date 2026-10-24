---
name: 🐛 Reporte de Error (Bug)
about: Reporta un fallo en el Backend FastAPI, Consola WebFig Vue 3, Conector RouterOS v7 (`/rest/*`), KeyDB o Contenedores
title: 'fix(fastapi|vue3): [Descripción corta del error]'
labels: bug, triage
assignees: ''
---

## 🛑 Descripción del Problema
Un resumen claro y conciso de lo que está fallando (ej. "Al reordenar una regla de Firewall Mangle con Safe Mode activo o consultar el diagnóstico óptico SFP DDM se produce un error...").

## 👣 Pasos para Reproducir
1. Módulo o ruta afectada (ej. `/routers/{id}/webfig/firewall` o endpoint `/api/v1/...`):
2. Comando o acción ejecutada:
   ~~~bash
   docker compose -f docker-compose.qa.yml run --rm [servicio] [comando]
   ~~~
3. El error observado fue...

## 🎯 Comportamiento Esperado
Descripción clara de lo que debería haber ocurrido según las especificaciones de `docs/specs/`.

## 💻 Entorno de Ejecución
- **Subsistema Afectado:** [ej. Backend FastAPI, Frontend Vue 3, Conector MikroTik REST v7, Endpoint MCP, Docker/KeyDB]
- **Modelo y Versión de RouterOS (si aplica):** [ej. MikroTik RB4011 / CCR2004 — RouterOS v7.15+]
- **Sistema Operativo (Host):** [ej. Ubuntu 24.04 / 26.04, Proxmox LXC]
- **Navegador (si es UI):** [ej. Chrome, Firefox, Vista Móvil PWA]

## 📋 Logs o Capturas de Pantalla (Sin Credenciales ni Secretos)
~~~text
Pega aquí el volcado de error sanitizado (Stack trace).
~~~
