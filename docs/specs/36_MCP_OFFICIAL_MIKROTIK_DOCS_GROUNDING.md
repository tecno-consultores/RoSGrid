# 36 — INTEGRACIÓN DE DOCUMENTACIÓN OFICIAL DE MIKROTIK ROUTEROS V7 EN EL SERVIDOR MCP (GROUNDING IA)

**[DIRECTIVA PARA ANTIGRAVITY]:** Este documento especifica la arquitectura, contratos Pydantic v2, directivas de seguridad anti-SSRF, motor de caché inteligente en KeyDB y catálogo de herramientas para dotar al **Servidor Model Context Protocol (MCP)** de RoSGrid (`POST /api/v1/mcp`) de acceso directo y contextual a la **Documentación Oficial de MikroTik RouterOS v7** (`https://manual.mikrotik.com/`).

El objetivo es erradicar las alucinaciones de sintaxis y discrepancias entre RouterOS v6 y v7 por parte de agentes de IA autónomos (**Hermes Agent**, **Claude Desktop / Claude Code**, **Cursor**, etc.) durante el diagnóstico, soporte y propuestas de cambio de red (*Maker-Checker*).

Todo el código generado DEBE mantener complejidad ciclomática **Grado A (`CC <= 5` por función en Radon)**, tipado estricto (`mypy --strict`), `0` alertas en `Bandit` y cobertura unitaria `>= 95%`.

---

## 1. Justificación Técnica y Estado del Arte

### 1.1 El Problema de las Alucinaciones en RouterOS v7
Los Modelos de Lenguaje de Gran Escala (LLMs) presentan una tasa de error significativa al interactuar con MikroTik debido a que gran parte de su corpus de entrenamiento histórico contiene documentación, foros y scripts de **RouterOS v6**. Con la llegada de **RouterOS v7**, MikroTik reescribió subsistemas completos:
1. **Routing Filters:** Se abandonó la sintaxis procedural de reglas por un lenguaje estructurado con bloques condicionales `if (...) { ... }`.
2. **BGP y OSPF:** Se rediseñó la arquitectura de instancias, templates, connection tracking y afinidad multi-core.
3. **API REST Nativa:** Se introdujo la interfaz `/rest/*` sobre HTTPS (reemplazando al binario API en puerto 8728).
4. **WireGuard, VXLAN y Containers:** Características modernas inexistentes en v6.

Sin una fuente de verdad en tiempo de ejecución (*Grounding*), un agente de IA puede proponer cambios con sintaxis obsoleta o parámetros inválidos, causando rechazos en la API o bloqueos de configuración.

### 1.2 La Infraestructura Abierta de MikroTik (`llms.txt`)
MikroTik implementó nativamente en su portal oficial de documentación (`https://manual.mikrotik.com/`) el estándar abierto [llmstxt.org](https://llmstxt.org):
- **`https://manual.mikrotik.com/llms.txt`:** Índice estructurado por menús (`/ip/`, `/routing/`, `/interface/`, etc.) con resúmenes concisos y enlaces directos a las páginas en formato Markdown limpio.
- **`https://manual.mikrotik.com/docs/<ruta>.md`:** Representación Markdown pura de cada documento, eliminando etiquetas HTML, estilos CSS y scripts de navegación.
- **`https://manual.mikrotik.com/llms-full.txt`:** Archivo concatenado de toda la enciclopedia (destinado a cargas masivas fuera de línea).

---

## 2. Diagrama de Arquitectura de Grounding MCP

```mermaid
flowchart TD
    subgraph "Agente IA (Hermes / Claude)"
        AgentQuery["1. Búsqueda de Tema o Sintaxis"]
        AgentPropose["4. Propuesta Validada Maker-Checker"]
    end

    subgraph "RoSGrid MCP Server (/api/v1/mcp)"
        Dispatcher{"JSON-RPC Dispatcher"}
        ToolSearch["Tool #21: rosgrid_search_mikrotik_docs"]
        ToolFetch["Tool #22: rosgrid_get_mikrotik_doc_topic"]
        AuditWORM[("audit_logs WORM")]
    end

    subgraph "Capa de Caché y Seguridad RoSGrid"
        CacheCheck{"¿En Caché KeyDB?"}
        KeyDBCache[("🚀 KeyDB Multi-Hilo<br>Índice TTL: 24h<br>Páginas TTL: 7d")]
        SSRFValidator{"🛡️ Validador Anti-SSRF<br>Domain Whitelist"}
    end

    subgraph "Repositorio Oficial MikroTik"
        MTIndex["🌐 https://manual.mikrotik.com/llms.txt"]
        MTDoc["🌐 https://manual.mikrotik.com/docs/*.md"]
    end

    AgentQuery -->|tools/call: rosgrid_search_mikrotik_docs| Dispatcher
    Dispatcher --> ToolSearch
    ToolSearch --> AuditWORM
    ToolSearch --> CacheCheck

    CacheCheck -->|Hit (< 5ms)| KeyDBCache
    CacheCheck -->|Miss| SSRFValidator

    SSRFValidator -->|HTTP GET Seguro| MTIndex
    MTIndex -->|Texto Plano| KeyDBCache
    KeyDBCache --> Filter["Filtrado Semántico & Top N"]
    Filter -->|JSON-RPC Result| AgentQuery

    AgentQuery -->|tools/call: rosgrid_get_mikrotik_doc_topic| Dispatcher
    Dispatcher --> ToolFetch
    ToolFetch --> AuditWORM
    ToolFetch --> SSRFValidator
    SSRFValidator -->|HTTP GET Seguro| MTDoc
    MTDoc -->|Markdown Limpio| KeyDBCache
    KeyDBCache --> AgentQuery

    AgentQuery --> AgentPropose
    AgentPropose -->|tools/call: rosgrid_propose_network_change| Dispatcher
```

---

## 3. Principios de Seguridad y Blindaje Anti-SSRF

Para preservar la postura de seguridad Grado 11X de RoSGrid:

1. **Lista Blanca Estricta de Dominios (Anti-SSRF Innegociable):**
   - El subsistema de descarga solo permitirá conexiones HTTPS salientes hacia el host exacto `manual.mikrotik.com`.
   - Se prohíbe terminantemente cualquier esquema diferente a `https://`.
   - Se prohíbe el uso de redirecciones HTTP externas (máximo 0 saltos a otros dominios).
   - Se valida mediante `ipaddress` que el destino no resuelva a direcciones locales, link-local, loopback o privadas (RFC 1918).

2. **Límites de Carga y Memoria (Anti-DoS):**
   - El índice `llms.txt` tiene un tamaño máximo permitido de descarga de `2 MB`.
   - Cada documento `.md` individual tiene un límite estricto de `1 MB`.
   - Todo cliente HTTP asíncrono (`httpx.AsyncClient`) debe operar con un tiempo límite (*timeout*) de conexión de `5.0s` y lectura de `10.0s`.

3. **Caché en Memoria y Aislamiento Offline:**
   - Para evitar saturación de peticiones hacia MikroTik y permitir operación en NOCs con conectividad satelital o restringida:
     - El índice `llms.txt` se almacena en KeyDB con la clave `mcp:docs:mikrotik:index` y un TTL de **24 horas (86.400 segundos)**.
     - Cada página Markdown se almacena en KeyDB con la clave `mcp:docs:mikrotik:page:{sha256(ruta)}` y un TTL de **7 días (604.800 segundos)**.

4. **Trazabilidad WORM:**
   - Cada consulta a la documentación genera un registro forense inmutable en `audit_logs` con `action_category = "MCP_AI_TOOL_CALL"`, registrando el término buscado o la ruta consultada.

---

## 4. Definición de Herramientas MCP (Tools #21 y #22)

### 4.1 Herramienta #21: `rosgrid_search_mikrotik_docs`

Permite al agente de IA buscar comandos, conceptos o rutas de menú de RouterOS v7 en el índice oficial de MikroTik.

#### Esquema de Entrada JSON Schema
```json
{
  "name": "rosgrid_search_mikrotik_docs",
  "description": "Busca en el índice oficial de documentación de MikroTik RouterOS v7 (llms.txt). Devuelve títulos, fragmentos de descripción y enlaces a la documentación Markdown oficial para validar sintaxis de comandos, routing filters, firewall y parámetros de RouterOS v7.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Término de búsqueda, comando o menú de RouterOS v7 (ej. 'routing bgp template', 'interface wireguard', 'firewall raw', 'routing filter')."
      },
      "category": {
        "type": "string",
        "description": "Categoría opcional para acotar la búsqueda (ej. 'Routing and Networking Protocols', 'Firewall and Quality of Service', 'CLI Reference', 'Getting Started')."
      },
      "max_results": {
        "type": "integer",
        "description": "Número máximo de resultados a devolver (entre 1 y 10, por defecto 5).",
        "default": 5
      }
    },
    "required": ["query"]
  }
}
```

#### Ejemplo de Salida JSON-RPC 2.0
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"query\": \"routing bgp template\",\n  \"total_matches\": 2,\n  \"results\": [\n    {\n      \"title\": \"BGP\",\n      \"category\": \"Routing and Networking Protocols\",\n      \"url\": \"https://manual.mikrotik.com/docs/user-guides/routing-and-networking-protocols/bgp.md\",\n      \"snippet\": \"BGP is an exterior gateway protocol... RouterOS v7 implements a completely redesigned BGP engine with connection templates...\"\n    },\n    {\n      \"title\": \"CLI Reference: /routing/bgp/template\",\n      \"category\": \"CLI Reference\",\n      \"url\": \"https://manual.mikrotik.com/docs/cli-reference/routing/bgp/template.md\",\n      \"snippet\": \"Documents RouterOS /routing/bgp/template menu properties: as, router-id, hold-time, keepalive-time, multihop, nexthop-choice...\"\n    }\n  ]\n}"
      }
    ]
  }
}
```

---

### 4.2 Herramienta #22: `rosgrid_get_mikrotik_doc_topic`

Recupera el contenido Markdown oficial de una página específica a partir de su URL o ruta relativa.

#### Esquema de Entrada JSON Schema
```json
{
  "name": "rosgrid_get_mikrotik_doc_topic",
  "description": "Obtiene el contenido Markdown oficial de una página específica de la documentación de MikroTik RouterOS v7. Permite leer la sintaxis exacta, ejemplos de configuración, parámetros CLI y restricciones técnicas del fabricante.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "doc_path_or_url": {
        "type": "string",
        "description": "URL oficial o ruta relativa de la página de documentación que termina en .md (ej. 'https://manual.mikrotik.com/docs/cli-reference/routing/bgp/template.md' o '/docs/cli-reference/routing/bgp/template.md')."
      },
      "max_characters": {
        "type": "integer",
        "description": "Límite opcional de caracteres para evitar saturación de la ventana de contexto (por defecto 8000 caracteres).",
        "default": 8000
      }
    },
    "required": ["doc_path_or_url"]
  }
}
```

#### Ejemplo de Salida JSON-RPC 2.0
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "# CLI Reference: /routing/bgp/template\n\nMenu path: `/routing/bgp/template`\n\n## Properties\n\n* `as` (integer) - Autonomous System Number.\n* `router-id` (IP) - 32-bit BGP identifier.\n* `hold-time` (time) - Hold timer interval (default: 3m).\n..."
      }
    ]
  }
}
```

---

## 5. Implementación del Servicio Backend (`fastapi/src/services/mikrotik_docs.py`)

Se diseñará el servicio asíncrono `MikrotikDocsService` con las siguientes responsabilidades:
1. **`fetch_or_get_cached_index()`:** Recupera `llms.txt` desde KeyDB o lo descarga de `https://manual.mikrotik.com/llms.txt` si la caché expiró.
2. **`parse_index_entries(raw_text)`:** Convierte el texto de `llms.txt` en una lista estructurada de objetos en memoria (`title`, `category`, `url`, `snippet`).
3. **`search_docs(query, category=None, max_results=5)`:** Ejecuta una búsqueda ponderada (coincidencias exactas en título > coincidencias en URL > coincidencias en snippet) y devuelve los mejores resultados.
4. **`fetch_or_get_cached_topic(url_or_path, max_characters=8000)`:** Valida la URL con el verificador anti-SSRF, consulta KeyDB y, si no existe, descarga el Markdown oficial, lo almacena en caché y lo entrega truncado al límite de seguridad.

---

## 6. Integración en el Endpoint MCP (`fastapi/src/api/v1/mcp.py`)

1. **Ampliación de `_MCP_TOOLS`:**
   - Se registran las definiciones de `rosgrid_search_mikrotik_docs` y `rosgrid_get_mikrotik_doc_topic` en la lista devuelta por `tools/list` (llegando a 22 tools en total).
2. **Ampliación del Dispatcher `_execute_mcp_tool`:**
   - Incorporación de los manejadores `_mcp_search_mikrotik_docs` y `_mcp_get_mikrotik_doc_topic`.
   - Estas dos herramientas de consulta **no requieren `router_id`**, pero sí exigen autenticación válida `SERVICE_ACCOUNT` o administrativa, y aplican el contador de *Rate-Limiting* en KeyDB (`ROSGRID_MCP_RATE_LIMIT_PER_MIN`).

---

## 7. Plan de Validación y Certificación QA 11X

1. **Pruebas Unitarias Pytest (`fastapi/tests/test_mikrotik_docs_mcp.unit.py`):**
   - Verificación de parseo de `llms.txt`.
   - Verificación de búsqueda con acierto exacto, búsqueda insensible a mayúsculas y filtrado por categoría.
   - Verificación de bloqueo anti-SSRF ante URLs maliciosas (ej. `http://evil.com`, `https://169.254.169.254`, `https://localhost/`).
   - Verificación de caché KeyDB (hit vs miss).
   - Verificación de truncamiento seguro de caracteres.
2. **Pruebas BDD Karate Labs (`fastapi/test/api_test.feature`):**
   - Escenario BDD de invocación JSON-RPC a `rosgrid_search_mikrotik_docs`.
   - Escenario BDD de invocación JSON-RPC a `rosgrid_get_mikrotik_doc_topic`.
3. **Métricas de Calidad:**
   - Cobertura de código `>= 95%`.
   - Complejidad ciclomática `CC <= 5` (Radon Grado A).
   - Tipado estricto `mypy` sin errores.
