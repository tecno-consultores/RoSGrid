# Arquitectura del Ecosistema de Pruebas (Modelo C4)

Este documento describe gráficamente cómo interactúan las herramientas, contenedores y redes dentro de **QA Testing Blueprints**. Utilizamos una adaptación del Modelo C4 orientada a infraestructura efímera para ilustrar el aislamiento estricto de nuestras pruebas, incluyendo las nuevas capas de Seguridad Dinámica (DAST), Ingeniería del Caos y Observabilidad (Nivel 11X).

---

## Nivel 1: Diagrama de Contexto (System Context)
Muestra el panorama general: cómo los usuarios (o IAs) interactúan con el sistema de pruebas y cómo este se relaciona con la máquina anfitriona.

```mermaid
graph TD
    %% Entidades
    Dev["👨‍💻 Desarrollador / Agente IA"]
    Hook["🚧 Lefthook (Pre-Commit & Pre-Push)"]
    QA["🛡️ QA Testing Blueprints (Makefiles / Docker Compose)"]
    Host["🖥️ Máquina Host (LXC / Local)"]
    Reports["📁 Reportes (Coverage, ZAP, Chaos, Métricas)"]

    %% Relaciones
    Dev -- "1. Intenta hacer commit/push" --> Hook
    Hook -- "2. Lanza escaneo efímero (Trivy/Linters). Rechaza si falla" --> QA
    Dev -- "3. Ejecuta pruebas completas (make qa-all)" --> QA
    QA -- "4. Usa motor Docker y solicita permisos PTRACE" --> Host
    Host -- "5. Monta volúmenes bind (.:/app)" --> QA
    QA -- "6. Escribe artefactos al morir" --> Reports
    Reports -- "7. Analiza fallos para corregir" --> Dev

    classDef default fill:#111,stroke:#333,stroke-width:2px,color:#fff;
    classDef highlight fill:#0052cc,stroke:#003d99,stroke-width:2px,color:#fff;
    classDef barrier fill:#ff8c00,stroke:#b8860b,stroke-width:2px,color:#fff;
    class QA highlight;
    class Hook barrier;
```

---

## Nivel 2: Diagrama de Contenedores (Container Diagram)
Muestra el interior del orquestador `docker-compose.qa.yml`. Destaca cómo separamos las responsabilidades en diferentes contenedores que conviven en una red virtual aislada, incluyendo perfiles ocultos para inteligencia artificial, cachés persistentes y pruebas destructivas.

```mermaid
graph LR
    subgraph "Red Virtual Aislada IPv4 (QA Bridge)"
        API["📦 App Viva \n (Nginx / Uvicorn / Node) \n Puerto Expuesto"]
        Test["🧪 Contenedor QA Efímero \n (Vitest/Pytest, SAST) \n Frontera: .unit.ts"]
        Karate["🥋 Contenedor BDD / E2E \n (Karate Labs / Playwright) \n Frontera: .e2e.ts"]
        ZAP["🕷 Contenedor DAST \n (OWASP ZAP) \n Baseline Scan"]
        Pumba["🌪️ Inyector de Caos \n (Pumba) \n Perfil: --profile chaos"]
        Prometheus["📊 Observabilidad \n (Prometheus) \n Perfil: --profile chaos"]
        PushGW["📤 Pushgateway \n (Caché de Métricas) \n Perfil: --profile observability"]
        Graphify["🧠 Servidor MCP IA \n (Graphify) \n Perfil: --profile graphify"]
        Cache["🗄️ Caché Persistente \n (pnpm-store / uv-cache) \n Volumen Nombrado"]
    end

    %% Flujos Internos
    Test -- "Lee/Escribe Dependencias" --> Cache
    Test -- "Intercepción / Mocking de BD" --> Test
    Test -- "Pruebas de Estrés y CPU Profiling" --> API
    Karate -- "Peticiones HTTP Caja Negra" --> API
    ZAP -- "Inyección XSS/SQL y Cabeceras" --> API
    Pumba -- "Inyecta Latencia y Mata Contenedores" --> API
    Test -- "Empuja métricas (cURL)" --> PushGW
    Prometheus -- "Scrapea Métricas (/metrics)" --> API
    Prometheus -- "Scrapea" --> PushGW
    Graphify -- "Lee configuraciones y expone SSE" --> API

    classDef ephemeral fill:#b33a3a,stroke:#800000,stroke-width:2px,color:#fff,stroke-dasharray: 5 5;
    classDef live fill:#228b22,stroke:#006400,stroke-width:2px,color:#fff;
    classDef chaos fill:#4b0082,stroke:#800080,stroke-width:2px,color:#fff,stroke-dasharray: 5 5;
    classDef ai fill:#d4af37,stroke:#8b6508,stroke-width:2px,color:#000;
    classDef obs fill:#e6522c,stroke:#8f3018,stroke-width:2px,color:#fff;
    classDef storage fill:#555,stroke:#999,stroke-width:2px,color:#fff;
    
    class Test,Karate,ZAP ephemeral;
    class Pumba chaos;
    class API live;
    class Graphify ai;
    class Prometheus,PushGW obs;
    class Cache storage;
```

---

## Nivel 3: Diagrama de Componentes (Component Diagram - Flujo Interno)
Cadena de ejecución innegociable. Si un eslabón falla, el pipeline se aborta (Principio de Fallo Rápido).

```mermaid
graph TD
    subgraph "Ejecución del Pipeline (Estándar 11X)"
        direction TB
        
        Graph["0️⃣ Ingestión de Contexto IA \n (Graphify MCP / Leer configs locales)"]
        Obs["1️⃣ Instrumentación RED \n (Middleware o Pushgateway)"]
        IaC["2️⃣ Auditoría IaC y Secretos \n (Trivy / Lefthook pre-push)"]
        SAST["3️⃣ Auditoría de Seguridad Estática \n (Bandit / ESLint Security)"]
        Static["4️⃣ Deuda Técnica y Complejidad \n (Radon / SonarJS)"]
        Unit["5️⃣ Lógica Unitaria y Mocking \n (Pytest / Vitest)"]
        Coverage{"6️⃣ Cobertura Total \n ¿Es >= 95%?"}
        Mutation["7️⃣ Pruebas de Mutación \n (Stryker / Mutmut)"]
        Performance["8️⃣ Profiling de Rendimiento \n (py-spy / clinic.js)"]
        DAST["9️⃣ Seguridad Dinámica \n (OWASP ZAP Baseline)"]
        Chaos["🔟 Ingeniería del Caos \n (Pumba + Locust/Artillery)"]
    end

    %% Enlaces lógicos
    Graph -- "Contexto Comprimido" --> Obs
    Obs -- "App Observable" --> IaC
    IaC -- "Infraestructura Segura" --> SAST
    SAST -- "Pasa" --> Static
    Static -- "Código Limpio" --> Unit
    Unit --> Coverage
    Coverage -- "Sí" --> Mutation
    Coverage -- "No (Exit Code 1)" --> FallaPipeline(("💥 Falla el PR"))
    Mutation -- "Mutantes Sobreviven" --> FallaPipeline
    Mutation -- "Pruebas Sólidas" --> Performance
    Performance -- "Sin Cuellos de Botella" --> DAST
    DAST -- "API Segura" --> Chaos
    Chaos -- "Métricas RED Estables" --> Exito(("✅ Aprobado"))

    classDef pass fill:#2e8b57,stroke:#fff,color:#fff;
    classDef fail fill:#b22222,stroke:#fff,color:#fff;
    class Exito pass;
    class FallaPipeline fail;
```

---

## Patrones Arquitectónicos Clave

1. **Shift-Left Security:** Obligamos a ejecutar validaciones IaC (Trivy) y SAST (Lefthook) localmente antes de gastar poder de cómputo en CI/CD.
2. **Sidecar / Atacante-Defensor:** Herramientas como ZAP o Locust actúan como atacantes temporales que bombardean a la App Viva. Nunca se instalan dentro de la imagen de producción.
3. **Resiliencia por Caos (Chaos Engineering):** Probar si la API funciona no es suficiente. Usamos Pumba para degradar intencionalmente la red interna (Jitter, Packet Loss) y Prometheus para certificar que la latencia (P99) no se dispare indefinidamente.
4. **Blackbox Network Isolation (Fronteras):** Los contenedores BDD (Karate) o E2E (Playwright) están estrictamente separados de las pruebas unitarias mediante convenciones de archivo (`.e2e.ts` vs `.unit.ts`). No tienen acceso al código fuente; se comunican por peticiones HTTP puras simulando a un usuario real.
