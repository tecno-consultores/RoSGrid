# 🌐 RoSGrid — Consola Centralizada Multi-Tenant para Flotas MikroTik RouterOS v7+

**Licencia:** GNU General Public License v3.0 (GPL-3.0-only)  
**Stack Principal:** FastAPI (Python 3.13) + Vue 3 (TypeScript / Pinia) + PostgreSQL 17 (RLS) + Redis 7  
**Calidad y Seguridad:** Certificado bajo el Estándar Corporativo **QA 11X**




## **🎯 Propósito del Proyecto**

**RoSGrid** es una plataforma web centralizada de alta seguridad diseñada para que proveedores de internet (ISP), operadores de telecomunicaciones, centros de monitoreo (NOC) y departamentos de infraestructura administren, diagnostiquen, respalden y auditen flotas de equipos **MikroTik con RouterOS v7.1+** utilizando exclusivamente su **REST API nativa sobre TLS (/rest/\*)**.


El sistema traslada la experiencia operativa y técnica de **WinBox / WebFig** a un entorno web centralizado **Multi-Tenant**, con control de acceso granular de **11 roles**, protección automática contra pérdida de conectividad (**Safe Mode Anti-Bloqueo**), bóveda criptográfica AES-256-GCM y una bitácora de **Auditoría Inmutable (WORM)**.


**Principios de Diseño Operativo:**


- **No es un sistema de facturación:** RoSGrid se enfoca 100% en la operación técnica de red, aprovisionamiento, seguridad y diagnóstico.

- **Cero almacenamiento de métricas históricas en base de datos:** Para series históricas a largo plazo existen herramientas dedicadas como Zabbix. En RoSGrid, las gráficas de CPU, RAM y tráfico en vivo funcionan exactamente igual que en **WinBox**: se alimentan por WebSocket y se acumulan en memoria RAM del navegador (RingBuffer de hasta 3 horas) mientras el técnico mantiene la vista abierta, reiniciándose al salir sin consumir disco en PostgreSQL.




## **✨ Características Principales**

### **1. Seguridad Criptográfica e Identidad Multi-Tenant**

- **Aislamiento Estricto por Empresa (Tenant):** Cada organización opera en un entorno aislado mediante políticas **Row-Level Security (RLS)** forzadas a nivel de motor en PostgreSQL 17.

- **Autenticación *Split-Credential* + 2FA TOTP Obligatorio:**

  - Inicio de sesión mediante Identificador de Empresa (Slug) + Correo/Usuario + Contraseña (Argon2id) + Código 2FA TOTP.

  - Tokens de sesión encapsulados en cookies \_\_Host- con banderas HttpOnly; Secure; SameSite=Strict (inmunes a exfiltración por XSS) y protección X-CSRF-Token firmada con HMAC-SHA256.

  - Rotación estricta de Refresh Tokens en Redis con detección automática de robo por reúso (*Reuse Detection*).

- **Control de Sesiones en Vivo (*Kill-Switch*):** Panel en tiempo real para que Administradores y Supervisores visualicen qué técnicos están conectados, desde qué IP/dispositivo y qué MikroTik están operando, con botón de expulsión instantánea en Redis y cierre forzoso de WebSockets.

### **2. Bóveda de Credenciales AES-256-GCM, Rotación Automática y Pinning SSL (TOFU)**

- **Cifrado Autenticado con AAD:** Las credenciales de la REST API de cada MikroTik se almacenan cifradas con AES-256-GCM vinculadas criptográficamente al tenant\_id y router\_id.

- **Rotación Automática de Contraseñas API:** RoSGrid puede rotar periódicamente (o bajo demanda) la contraseña del usuario API dentro del MikroTik por llaves aleatorias de 32 caracteres, conservando la clave inmediatamente anterior como respaldo transaccional.

- **Consulta Protegida con *Step-Up Auth* (30 Segundos):** Solo los 2 perfiles más altos (SUPERADMIN\_GLOBAL y TENANT\_ADMIN) pueden revelar una clave de la bóveda tras validar su código 2FA TOTP en vivo, dejando traza inmutable en auditoría y ocultando la clave automáticamente a los 30 segundos.

- **Certificados SSL Autofirmados con TOFU (*Trust On First Use*):** Acepta certificados autofirmados de RouterOS v7 capturando su huella SHA-256 en la primera conexión y bloqueando cualquier cambio no autorizado de certificado (*MitM protection*).

### **3. Consola Centralizada WebFig de Doble Capa (RouterOS v7+)**

- **Capa 1 — Módulos Nativos Especializados:**

  - **Dashboard en Vivo:** Gráficas efímeras estilo WinBox (CPU, RAM, Disco, Temperatura, Voltaje y Tráfico bps/pps por interfaz).

  - **Interfaces & Óptica SFP:** Ethernet, diagnóstico óptico **SFP/SFP+ DDM** (potencia láser TX/RX en dBm, temperatura), test de cables TDR, VLANs 802.1Q, Bridges, WireGuard y tabla de registro WiFi.

  - **IP & Servicios:** Addresses, Routes (incluyendo balanceo ECMP), ARP, Pools, DHCP Server Leases (conversión a estático en un clic), DNS, IP Neighbors (MNDP/LLDP/CDP) y /ip/service (con protección anti-suicidio del puerto www-ssl).

  - **Firewall Completo con *Drag & Drop*:** Reglas Filter, NAT, Mangle, RAW, Address-Lists y Connection Tracking, con reordenamiento visual e interactivo protegido por Safe Mode.

  - **Routing Avanzado v7:** Sesiones y peers BGP en vivo, prefijos anunciados, OSPF v2/v3, Routing Tables, Policy Rules, BFD y Routing Filters.

  - **PPP, VPNs & Queues:** Sesiones PPPoE Active (con botón de reconexión rápida para Soporte N1), Secrets, Profiles, Simple Queues y Queue Tree.

  - **System & Diagnóstico en Vivo:** Identity, usuarios del router, Scripts, Scheduler, Packages, Ping, Traceroute, Torch y visor de Log.

- **Capa 2 — Motor Dinámico Universal:**

  - Renderizador automático de tablas y formularios para el **100% restante de submenús /rest/\* de RouterOS v7** (MPLS, VXLAN, ZeroTier, Containers, CAPsMAN, User-Manager, RADIUS, SNMP, Certificates).

### **4. Protección Anti-Bloqueo (*Safe Mode*), *Maker-Checker* y Operaciones Masivas**

- **Safe Mode vía *Dead Man's Switch* (/system/scheduler):** Antes de aplicar un cambio delicado de red o firewall, RoSGrid inyecta un scheduler temporal de reversión a 60 segundos en el propio MikroTik. Si el cambio deja incomunicado al router, el MikroTik revierte el cambio por sí solo y recupera la conexión automáticamente.

- **Flujo de Aprobación (*Maker-Checker*):** Las 7 categorías de acciones críticas ejecutadas por niveles operativos intermedios se interceptan hacia una bandeja de aprobación para que un Supervisor o Soporte N3 las autorice revisando el Diff previo.

- **Backups Nocturnos Deduplicados y Comparador Diff Estilo Git (.rsc):** Retención de 30 días con deduplicación por hash SHA-256 y visor lado a lado estilo Git para auditar qué líneas exactas cambiaron en un router entre dos fechas o frente al estado en vivo.

- **Mapa Interactivo OpenStreetMap (Leaflet) y Wallboard NOC:** Georreferenciación 100% gratuita sin API Keys, ventanas de mantenimiento programadas y alertas *Zero-Storage* hacia **Telegram, Correo SMTP, Webhooks y Pantalla NOC**.




## **👥 Matriz de los 11 Roles del Sistema (RBAC)**

1. **SUPERADMIN\_GLOBAL**: Gobierno global de la plataforma y creación/suspensión de empresas (Tenants).

2. **TENANT\_ADMIN**: Administración total de su empresa, asignación de routers por técnico y acceso *Step-Up* a la Bóveda de Claves.

3. **SUPERVISOR**: Aprobador de cambios críticos (*Maker-Checker*), gestión de ventanas de mantenimiento y *Kill-Switch* de sesiones.

4. **SUPPORT\_L3**: Ingeniería Core/Borde, BGP/OSPF, WebFig Capa 1 y Capa 2, acciones masivas y aprobaciones técnicas.

5. **SUPPORT\_L2**: Administración de red intermedia en equipos asignados (cambios críticos sujetos a *Maker-Checker*).

6. **SUPPORT\_L1**: Helpdesk, diagnóstico en vivo (Ping, Traceroute, ARP, SFP), reconexión de sesiones PPPoE/DHCP y solicitud de cambios.

7. **FIELD\_TECH**: Técnico de campo / instalador acotado a los nodos asignados para validación física, óptica y vecinos.

8. **INVENTORY\_MANAGER**: Alta de equipos, importación masiva por CSV en 2 pasos (*Dry-Run* + ejecución) y rotación de credenciales.

9. **AUDITOR**: Acceso 100% de solo lectura a la bitácora inmutable WORM (audit\_logs), verificación criptográfica de cadena de custodia y comparador Diff (.rsc).

10. **NOC\_MONITOR**: Perfil exclusivo para televisores y pantallas de monitoreo 24/7 (Mapa OpenStreetMap, KPIs y alertas en tiempo real).

11. **SERVICE\_ACCOUNT**: Cuenta Machine-to-Machine restringida por lista blanca CIDR y alcances específicos.




## **🗂️ Estructura del Repositorio**

rosgrid/


├── LICENSE                         \# Licencia GNU GPLv3


├── README.md                       \# Documentación principal del proyecto


├── TESTING.md                      \# Bitácora Viva de certificación QA 11X


├── docker-compose.yml              \# Orquestador de despliegue (Imágenes inmutables sin Dockerfile)


├── .env.example                    \# Plantilla de configuración de entorno


├── lefthook.yml                    \# Barrera de seguridad Pre-Commit, Commit-Msg y Pre-Push


├── commitlint.config.js            \# Convenciones estrictas de mensajes de commit


├── instalar-hooks.sh               \# Instalador local de hooks Lefthook


├── auditar-infra.sh                \# Auditoría efímera Trivy (IaC + File System CVEs)


├── specs/                          \# Enciclopedia de 30 especificaciones técnicas para AntiGravity + Blueprints 11X


├── docs/                           \# Documentación operativa y manuales de usuario de RoSGrid


├── fastapi/                        \# Ecosistema Backend (FastAPI + SQLAlchemy 2.0 + Alembic + Redis + QA 11X)


└── vue3/                           \# Ecosistema Frontend (Vue 3 + TypeScript + Pinia + Leaflet + QA 11X)




## **🚀 Despliegue con Docker Compose**

RoSGrid opera bajo el principio de **infraestructura inmutable** y ejecuta las migraciones de base de datos automáticamente al iniciar o actualizar contenedores (protegidas mediante pg\_advisory\_lock en PostgreSQL):


\# 1. Copiar la plantilla de variables de entorno y configurar secretos criptográficos


cp .env.example .env


\# 2. Auditar la configuración de infraestructura con Trivy


./auditar-infra.sh


\# 3. Levantar toda la plataforma en segundo plano


docker compose up -d




## **🧪 Certificación de Calidad (Estándar QA 11X)**

Toda prueba unitaria, de mutación, análisis estático, accesibilidad WCAG 2.1 AA, rendimiento y caos se ejecuta exclusivamente dentro de contenedores efímeros a través de los Makefile de cada ecosistema. Consulta [TESTING.md](http://./TESTING.md) para ver los comandos detallados de validación.




## **📄 Licencia**

Este proyecto es Software Libre distribuido bajo los términos de la **GNU General Public License v3.0 (GPL-3.0-only)**. Consulta el archivo [LICENSE](http://./LICENSE) para más detalles.
