---
name: 🚀 Propuesta de Módulo RouterOS v7, Tool MCP o Mejora QA
about: Sugerir soporte para un nuevo módulo WebFig Capa 1, una nueva Tool para el servidor MCP o una mejora del pipeline QA 11X
title: 'feat(global): integra [nombre del módulo o herramienta]'
labels: enhancement, proposal
assignees: ''
---

## 🛠️ Módulo o Herramienta Propuesta
- **Nombre de la funcionalidad / herramienta:** 
- **Subsistema objetivo:** [ej. WebFig Capa 1 (`vue3` + `fastapi`), Tool MCP (`/api/v1/mcp`), Suite QA 11X]
- **Ruta de la API de RouterOS v7 o Documentación oficial:** [ej. `/rest/routing/bgp/connection` o enlace oficial]

## 🎯 ¿Qué necesidad operativa o de calidad resuelve?
Explica qué problema resuelve para los operadores del NOC, ingenieros de red o agentes IA (Hermes / Claude).

## 🐳 Prueba de Concepto / Contrato Propuesto
Describe cómo se integraría respetando las reglas de RoSGrid (Cero almacenamiento de métricas históricas en PostgreSQL, ejecución en contenedores `sinfallas/*`, Safe Mode de 60s y Maker-Checker):

~~~bash
# Ejemplo de comando QA o payload JSON-RPC / REST propuesto
~~~

## ✅ Checklist de Arquitectura RoSGrid (Estándar 11X)
- [ ] Cumple con la filosofía *Zero-Metrics Storage* (no guarda series temporales en PostgreSQL 17).
- [ ] Si modifica configuraciones críticas en el MikroTik, pasa por el clasificador **Maker-Checker** y **Safe Mode (60s)**.
- [ ] Puede probarse al 100% en nuestros contenedores efímeros (`sinfallas/base-python-uv:3.13` y `sinfallas/base-node-ionic:22`) manteniendo cobertura `>= 95%`.
