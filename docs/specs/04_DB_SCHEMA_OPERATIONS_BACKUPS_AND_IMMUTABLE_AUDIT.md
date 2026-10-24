# 04 — ESQUEMA DE BASE DE DATOS: MAKER-CHECKER, BACKUPS DEDUPLICADOS, OPERACIONES MASIVAS Y AUDITORÍA INMUTABLE (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica las tablas en **PostgreSQL 17** para el flujo de aprobaciones críticas (*Maker-Checker*), el sistema de respaldos automáticos (.rsc y .backup) con deduplicación criptográfica SHA-256 y retención de 30 días, plantillas parametrizables (*Golden Configs*), ejecución de acciones masivas multi-router, canales de alerta por Tenant y la bitácora de **Auditoría Inmutable** (audit\_logs) protegida contra alteraciones mediante triggers en PostgreSQL.




## **1. Tipos Enumerados (ENUM) de Operaciones y Auditoría**

-- Estados del flujo Maker-Checker (Aprobación de Cambios Críticos)


CREATE TYPE approval\_status\_enum AS ENUM (


    'PENDING',


    'APPROVED\_AND\_EXECUTED',


    'APPROVED\_EXECUTION\_FAILED',


    'REJECTED',


    'EXPIRED',


    'CANCELLED\_BY\_REQUESTER'


);


-- Tipos de acciones críticas interceptadas por Maker-Checker


CREATE TYPE critical\_action\_type\_enum AS ENUM (


    'ROUTER\_REBOOT\_OR\_SHUTDOWN',


    'BULK\_MULTI\_ROUTER\_EXECUTION',


    'ROUTING\_BGP\_OSPF\_DEFAULT\_CHANGE',


    'FIREWALL\_INPUT\_OR\_SERVICE\_PORT\_CHANGE',


    'WAN\_TRUNK\_INTERFACE\_OR\_IP\_CHANGE',


    'BACKUP\_RESTORE\_OR\_CUSTOM\_SCRIPT',


    'ROUTER\_INTERNAL\_USER\_CHANGE'


);


-- Estado de trabajos masivos (Multi-Router)


CREATE TYPE bulk\_job\_status\_enum AS ENUM (


    'QUEUED',


    'AWAITING\_APPROVAL',


    'RUNNING',


    'COMPLETED',


    'PARTIAL\_FAILURE',


    'FAILED',


    'CANCELLED'


);


-- Tipos de canales de alerta por Tenant


CREATE TYPE alert\_channel\_type\_enum AS ENUM (


    'TELEGRAM\_BOT',


    'SMTP\_EMAIL',


    'GENERIC\_WEBHOOK'


);




## **2. Tabla approval\_requests (Flujo Maker-Checker)**

Cuando un técnico con un rol que no posee permiso directo de ejecución crítica solicita una acción sensible, el backend serializa la petición exacta hacia la REST API de RouterOS y la almacena aquí en espera de la firma de un SUPERVISOR, SUPPORT\_L3 o TENANT\_ADMIN:


CREATE TABLE approval\_requests (


    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),


    tenant\_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,


    router\_id UUID REFERENCES routers(id) ON DELETE CASCADE, -- NULL si es una acción masiva multi-router


    


    action\_type critical\_action\_type\_enum NOT NULL,


    status approval\_status\_enum NOT NULL DEFAULT 'PENDING',


    


    -- Detalles técnicos exactos de la operación solicitada


    summary VARCHAR(255) NOT NULL,


    requester\_justification TEXT NOT NULL,


    ros\_rest\_method VARCHAR(10) NOT NULL,   -- GET, POST, PATCH, PUT, DELETE


    ros\_rest\_path VARCHAR(255) NOT NULL,    -- Ej. /rest/system/reboot o /rest/ip/firewall/filter/\*1A


    request\_payload JSONB NOT NULL DEFAULT '\{\}'::jsonb,


    previous\_state\_snapshot JSONB,          -- Estado leído del MikroTik antes del cambio (para preview y rollback)


    


    -- Trazabilidad de Solicitud (Maker) y Revisión (Checker)


    requested\_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,


    reviewed\_by UUID REFERENCES users(id) ON DELETE RESTRICT,


    review\_comment TEXT,


    


    expires\_at TIMESTAMPTZ NOT NULL,


    reviewed\_at TIMESTAMPTZ,


    executed\_at TIMESTAMPTZ,


    execution\_result JSONB,


    created\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    CONSTRAINT chk\_maker\_not\_checker CHECK (reviewed\_by IS NULL OR requested\_by \<\> reviewed\_by)


);


CREATE INDEX idx\_approvals\_tenant\_status ON approval\_requests (tenant\_id, status, created\_at DESC);




## **3. Tabla router\_backups (Respaldos .rsc y .backup con Deduplicación SHA-256 y Retención 30 Días)**

Para evitar el crecimiento descontrolado del almacenamiento:


1. El worker nocturno (o bajo demanda) descarga el texto de exportación (/rest/export) de cada MikroTik.

2. Calcula el hash SHA-256 del contenido .rsc normalizado (ignorando el comentario de primera línea con la fecha de generación \# oct/14/2026 ... que pone RouterOS).

3. **Deduplicación:** Si el rsc\_sha256\_hash es idéntico al último backup exitoso de ese router, **NO se inserta una copia duplicada**, sino que solo se actualiza el campo last\_verified\_identical\_at del registro existente.

4. **Comparador Visual Estilo Git (Diff):** El contenido .rsc se guarda comprimido y cifrado con AES-256-GCM (rsc\_ciphertext), permitiendo al backend desencriptar en memoria dos versiones y generar el unified diff línea por línea para el Auditor, Supervisor o Soporte N3.

5. **Purga Automática (30 días):** Un job diario elimina los respaldos con created\_at \< NOW() - INTERVAL '30 days', conservando siempre al menos el último backup válido de cada router.


CREATE TABLE router\_backups (


    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),


    tenant\_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,


    router\_id UUID NOT NULL REFERENCES routers(id) ON DELETE CASCADE,


    


    backup\_type VARCHAR(20) NOT NULL DEFAULT 'AUTOMATIC\_NIGHTLY', -- AUTOMATIC\_NIGHTLY, MANUAL, PRE\_UPGRADE


    ros\_version\_at\_backup VARCHAR(64) NOT NULL,


    


    -- Deduplicación y almacenamiento cifrado del script .rsc (para Diff Git)


    rsc\_sha256\_hash CHAR(64) NOT NULL,


    rsc\_size\_bytes INTEGER NOT NULL,


    rsc\_ciphertext BYTEA NOT NULL,


    rsc\_iv BYTEA NOT NULL CONSTRAINT chk\_rsc\_iv CHECK (octet\_length(rsc\_iv) = 12),


    rsc\_tag BYTEA NOT NULL CONSTRAINT chk\_rsc\_tag CHECK (octet\_length(rsc\_tag) = 16),


    


    -- Resumen precalculado de cambios respecto al backup inmediatamente anterior


    diff\_lines\_added INTEGER NOT NULL DEFAULT 0,


    diff\_lines\_removed INTEGER NOT NULL DEFAULT 0,


    parent\_backup\_id UUID REFERENCES router\_backups(id) ON DELETE SET NULL,


    


    -- Referencia al archivo binario .backup en volumen cifrado


    binary\_backup\_file\_path VARCHAR(512),


    binary\_backup\_sha256 CHAR(64),


    binary\_backup\_size\_bytes INTEGER,


    


    triggered\_by UUID REFERENCES users(id) ON DELETE SET NULL,


    created\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    last\_verified\_identical\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    expires\_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '30 days')


);


CREATE INDEX idx\_backups\_router\_created ON router\_backups (tenant\_id, router\_id, created\_at DESC);


CREATE INDEX idx\_backups\_expiration ON router\_backups (expires\_at);




## **4. Tablas config\_templates y bulk\_jobs (Plantillas Parametrizables y Acciones Masivas)**

### **4.1 Tabla config\_templates (Golden Configs / Macros)**

CREATE TABLE config\_templates (


    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),


    tenant\_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,


    name VARCHAR(120) NOT NULL,


    category VARCHAR(64) NOT NULL, -- FIREWALL, VLAN, BGP, SYSTEM, DNS, HARDENING, CUSTOM


    description TEXT NOT NULL,


    


    -- Esquema de variables esperadas: ej. \[\{"name": "VLAN\_ID", "type": "integer", "min": 2, "max": 4094\}\]


    variables\_schema JSONB NOT NULL DEFAULT '\[\]'::jsonb,


    


    -- Secuencia ordenada de operaciones REST a inyectar en RouterOS v7


    -- Ej. \[\{"method": "POST", "path": "/rest/interface/vlan", "body": \{"name": "vlan-\{\{VLAN\_ID\}\}", "vlan-id": "\{\{VLAN\_ID\}\}"\}\}\]


    rest\_steps\_template JSONB NOT NULL,


    


    requires\_safemode BOOLEAN NOT NULL DEFAULT TRUE,


    created\_by UUID REFERENCES users(id) ON DELETE SET NULL,


    created\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    updated\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    CONSTRAINT uq\_template\_tenant\_name UNIQUE (tenant\_id, name)


);

### **4.2 Tabla bulk\_jobs y bulk\_job\_items (Operaciones Masivas y Actualizaciones de RouterOS)**

CREATE TABLE bulk\_jobs (


    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),


    tenant\_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,


    job\_type VARCHAR(64) NOT NULL, -- TEMPLATE\_APPLY, ROS\_UPGRADE, PASSWORD\_ROTATION, CUSTOM\_REST\_CALL


    title VARCHAR(180) NOT NULL,


    status bulk\_job\_status\_enum NOT NULL DEFAULT 'QUEUED',


    


    template\_id UUID REFERENCES config\_templates(id) ON DELETE SET NULL,


    execution\_parameters JSONB NOT NULL DEFAULT '\{\}'::jsonb,


    target\_router\_ids JSONB NOT NULL, -- Array de UUIDs de routers seleccionados


    


    total\_routers INTEGER NOT NULL,


    succeeded\_count INTEGER NOT NULL DEFAULT 0,


    failed\_count INTEGER NOT NULL DEFAULT 0,


    


    approval\_request\_id UUID REFERENCES approval\_requests(id) ON DELETE SET NULL,


    created\_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,


    started\_at TIMESTAMPTZ,


    completed\_at TIMESTAMPTZ,


    created\_at TIMESTAMPTZ NOT NULL DEFAULT NOW()


);


CREATE TABLE bulk\_job\_items (


    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),


    tenant\_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,


    bulk\_job\_id UUID NOT NULL REFERENCES bulk\_jobs(id) ON DELETE CASCADE,


    router\_id UUID NOT NULL REFERENCES routers(id) ON DELETE CASCADE,


    status VARCHAR(32) NOT NULL DEFAULT 'PENDING', -- PENDING, RUNNING, SUCCESS, ROLLED\_BACK, FAILED


    response\_summary JSONB,


    error\_detail TEXT,


    started\_at TIMESTAMPTZ,


    finished\_at TIMESTAMPTZ


);


CREATE INDEX idx\_bulk\_items\_job ON bulk\_job\_items (tenant\_id, bulk\_job\_id);




## **5. Tabla notification\_channels (Canales de Alerta por Tenant: Telegram, SMTP, Webhook)**

CREATE TABLE notification\_channels (


    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),


    tenant\_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,


    name VARCHAR(100) NOT NULL,


    channel\_type alert\_channel\_type\_enum NOT NULL,


    is\_enabled BOOLEAN NOT NULL DEFAULT TRUE,


    


    -- Configuración cifrada (token de bot Telegram, credenciales SMTP o secreto HMAC de Webhook)


    config\_ciphertext BYTEA NOT NULL,


    config\_iv BYTEA NOT NULL CONSTRAINT chk\_notif\_iv CHECK (octet\_length(config\_iv) = 12),


    config\_tag BYTEA NOT NULL CONSTRAINT chk\_notif\_tag CHECK (octet\_length(config\_tag) = 16),


    


    -- Eventos suscritos: \["ROUTER\_DOWN", "ROUTER\_UP", "HIGH\_CPU", "SSL\_MISMATCH", "APPROVAL\_NEEDED", "BACKUP\_FAILED"\]


    subscribed\_events JSONB NOT NULL DEFAULT '\["ROUTER\_DOWN", "ROUTER\_UP", "SSL\_MISMATCH", "APPROVAL\_NEEDED"\]'::jsonb,


    


    created\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    updated\_at TIMESTAMPTZ NOT NULL DEFAULT NOW()


);




## **6. Tabla audit\_logs (Bitácora de Auditoría 100% Inmutable — WORM)**

Absolutamente toda acción realizada en **RoSGrid** (inicios de sesión, fallos de 2FA, revelación de claves de la bóveda con *Step-Up Auth*, expulsión de sesiones por *Kill-Switch*, llamadas a la REST API de un MikroTik en Capa 1 o Capa 2, aprobaciones Maker-Checker y rollbacks de Safe Mode) se registra en audit\_logs.

### **6.1 Definición DDL de audit\_logs con Encadenamiento Hash (prev\_record\_hash)**

CREATE TABLE audit\_logs (


    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),


    tenant\_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,


    


    -- Quién, desde dónde y con qué rol (Desacoplado de FK cascade para preservar inmutabilidad WORM e integridad hash)
    actor_user_id UUID,

    actor_username VARCHAR(64) NOT NULL,

    actor_role system_role_enum NOT NULL,

    actor_ip INET NOT NULL,

    actor_user_agent VARCHAR(512),

    -- Qué hizo y sobre qué equipo/recurso
    event_category VARCHAR(64) NOT NULL, -- AUTH, VAULT, INVENTORY, WEBFIG_L1, WEBFIG_L2, MAKER_CHECKER, SAFEMODE, SESSION_KILL

    event_action VARCHAR(128) NOT NULL,  -- Ej. CREDENTIAL_REVEALED, FIREWALL_RULE_UPDATED, SESSION_TERMINATED

    -- Identificador del router histórico (Desacoplado de FK para permitir eliminación en routers sin violar WORM)
    router_id UUID,

    router_display_name VARCHAR(120),


    


    -- Trazabilidad exacta hacia RouterOS y Diff de datos (Sanitizado de contraseñas en texto plano)


    ros\_rest\_method VARCHAR(10),


    ros\_rest\_endpoint VARCHAR(255),


    idempotency\_key VARCHAR(64),


    before\_state JSONB,


    after\_state JSONB,


    status\_code SMALLINT NOT NULL,


    error\_message TEXT,


    


    -- Integridad Criptográfica (Cadena de custodia tipo Blockchain/Hash-Chain por Tenant)


    prev\_record\_hash CHAR(64) NOT NULL,


    record\_sha256\_hash CHAR(64) NOT NULL,


    


    created\_at TIMESTAMPTZ NOT NULL DEFAULT NOW()


);


CREATE INDEX idx\_audit\_tenant\_created ON audit\_logs (tenant\_id, created\_at DESC);


CREATE INDEX idx\_audit\_tenant\_actor ON audit\_logs (tenant\_id, actor\_user\_id, created\_at DESC);


CREATE INDEX idx\_audit\_tenant\_router ON audit\_logs (tenant\_id, router\_id, created\_at DESC);


CREATE INDEX idx\_audit\_tenant\_category ON audit\_logs (tenant\_id, event\_category, created\_at DESC);

### **6.2 Trigger PostgreSQL que Prohíbe UPDATE, DELETE y TRUNCATE en audit\_logs**

Para garantizar que ni siquiera un usuario con acceso de escritura a la aplicación pueda alterar o borrar la evidencia de auditoría:


CREATE OR REPLACE FUNCTION prevent\_audit\_log\_modification()


RETURNS TRIGGER AS $$


BEGIN


    RAISE EXCEPTION 'VIOLACIÓN DE SEGURIDAD (RoSGrid WORM): La tabla audit\_logs es estrictamente inmutable. Operaciones % están prohibidas.', TG\_OP


        USING ERRCODE = '42501';


END;


$$ LANGUAGE plpgsql;


CREATE TRIGGER trg\_immutable\_audit\_logs


    BEFORE UPDATE OR DELETE OR TRUNCATE ON audit\_logs


    FOR EACH STATEMENT


    EXECUTE FUNCTION prevent\_audit\_log\_modification();




## **7. Activación de RLS para Tablas Operativas y Auditoría**

ALTER TABLE approval\_requests ENABLE ROW LEVEL SECURITY;


ALTER TABLE approval\_requests FORCE ROW LEVEL SECURITY;


CREATE POLICY tenant\_isolation\_approvals ON approval\_requests


    USING (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid)


    WITH CHECK (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid);


ALTER TABLE router\_backups ENABLE ROW LEVEL SECURITY;


ALTER TABLE router\_backups FORCE ROW LEVEL SECURITY;


CREATE POLICY tenant\_isolation\_backups ON router\_backups


    USING (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid)


    WITH CHECK (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid);


ALTER TABLE config\_templates ENABLE ROW LEVEL SECURITY;


ALTER TABLE config\_templates FORCE ROW LEVEL SECURITY;


CREATE POLICY tenant\_isolation\_templates ON config\_templates


    USING (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid)


    WITH CHECK (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid);


ALTER TABLE bulk\_jobs ENABLE ROW LEVEL SECURITY;


ALTER TABLE bulk\_jobs FORCE ROW LEVEL SECURITY;


CREATE POLICY tenant\_isolation\_bulk\_jobs ON bulk\_jobs


    USING (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid)


    WITH CHECK (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid);


ALTER TABLE bulk\_job\_items ENABLE ROW LEVEL SECURITY;


ALTER TABLE bulk\_job\_items FORCE ROW LEVEL SECURITY;


CREATE POLICY tenant\_isolation\_bulk\_items ON bulk\_job\_items


    USING (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid)


    WITH CHECK (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid);


ALTER TABLE notification\_channels ENABLE ROW LEVEL SECURITY;


ALTER TABLE notification\_channels FORCE ROW LEVEL SECURITY;


CREATE POLICY tenant\_isolation\_notif ON notification\_channels


    USING (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid)


    WITH CHECK (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid);


ALTER TABLE audit\_logs ENABLE ROW LEVEL SECURITY;


ALTER TABLE audit\_logs FORCE ROW LEVEL SECURITY;


CREATE POLICY tenant\_isolation\_audit ON audit\_logs


    USING (


        current\_setting('app.is\_superadmin\_global', true) = 'true'


        OR tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid


    )


    WITH CHECK (


        current\_setting('app.is\_superadmin\_global', true) = 'true'


        OR tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid


    );
