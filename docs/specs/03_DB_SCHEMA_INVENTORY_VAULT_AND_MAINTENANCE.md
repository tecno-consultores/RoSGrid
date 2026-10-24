# 03 — ESQUEMA DE BASE DE DATOS: INVENTARIO MIKROTIK, BÓVEDA AES-256-GCM, TOFU SSL Y MANTENIMIENTO (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento define las tablas en **PostgreSQL 17** para el inventario de equipos MikroTik RouterOS v7+, su clasificación por rol en la red, ubicación física y coordenadas GPS (para OpenStreetMap), la bóveda criptográfica AES-256-GCM para credenciales de la REST API, el historial de rotación automática de claves, el almacenamiento de huellas SSL autofirmadas (TOFU SHA-256) y las ventanas de mantenimiento programadas.




## **1. Tipos Enumerados (ENUM) del Inventario**

-- Clasificación de los MikroTik según su rol en la topología de red


CREATE TYPE router\_network\_role\_enum AS ENUM (


    'CORE',                 -- Router principal / Core de red


    'EDGE\_BGP',             -- Router de borde / Peering BGP


    'WAN\_BALANCER',         -- Balanceador multi-WAN (ECMP / PCC / Failover)


    'BRAS\_PPPOE',           -- Concentrador PPPoE / Autenticación de abonados


    'DISTRIBUTION\_SWITCH',  -- Switch de distribución / CRS (L2/L3 HW Offload)


    'TOWER\_AP',             -- Nodo inalámbrico / Punto de acceso en torre


    'CORPORATE\_CPE'         -- Equipo de borde en cliente corporativo / Sucursal


);


-- Estado administrativo del equipo en la plataforma


CREATE TYPE router\_admin\_state\_enum AS ENUM (


    'PRODUCTION',           -- En producción (monitoreo activo y alertas habilitadas)


    'MAINTENANCE',          -- En mantenimiento manual (suprime alertas externas)


    'STAGING\_LAB',          -- En laboratorio / pre-producción


    'RETIRED'               -- Fuera de línea permanentemente / Desincorporado


);


-- Estado de verificación del certificado SSL autofirmado del MikroTik (TOFU)


CREATE TYPE ssl\_trust\_status\_enum AS ENUM (


    'PENDING\_TOFU',         -- Registrado, esperando primera conexión para capturar huella SHA-256


    'TRUSTED\_PINNED',       -- Huella SHA-256 capturada y verificada en cada llamada REST


    'FINGERPRINT\_MISMATCH'  -- ALERTA CRÍTICA: El certificado del MikroTik cambió sin autorización


);




## **2. Tabla routers (Inventario Central de Equipos MikroTik)**

Separa claramente los **campos administrativos (manuales)** de los **campos autodescubiertos** automáticamente cuando FastAPI se conecta a /rest/system/resource, /rest/system/routerboard y /rest/system/identity:


CREATE TABLE routers (


    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),


    tenant\_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,


    


    -- Datos de Identificación y Conexión REST API (RouterOS v7+)


    display\_name VARCHAR(120) NOT NULL,


    api\_base\_url VARCHAR(255) NOT NULL


        CONSTRAINT chk\_api\_https\_url CHECK (api\_base\_url ~ '^https://\[a-zA-Z0-9.\_-\]+(:\[0-9\]\{1,5\})?$'),


    api\_port INTEGER NOT NULL DEFAULT 443


        CONSTRAINT chk\_api\_port\_range CHECK (api\_port BETWEEN 1 AND 65535),


    


    -- Clasificación Administrativa (Manual o Dinámica)
    -- En PostgreSQL 17 evolucionado a VARCHAR(64) (Alembic 0008) para admitir roles estándar y personalizados
    network_role VARCHAR(64) NOT NULL DEFAULT 'CORE',

    admin_state router_admin_state_enum NOT NULL DEFAULT 'PRODUCTION',


    physical\_location VARCHAR(255) NOT NULL,


    latitude NUMERIC(9, 6)


        CONSTRAINT chk\_lat\_range CHECK (latitude IS NULL OR (latitude BETWEEN -90.0 AND 90.0)),


    longitude NUMERIC(9, 6)


        CONSTRAINT chk\_lng\_range CHECK (longitude IS NULL OR (longitude BETWEEN -180.0 AND 180.0)),


    online\_since\_date DATE NOT NULL,


    operational\_notes TEXT,


    site\_contact\_info VARCHAR(255),


    


    -- Datos Autodescubiertos (Actualizados por FastAPI desde RouterOS v7 REST API)


    serial\_number VARCHAR(64) NOT NULL,


    ros\_identity VARCHAR(128),


    board\_name VARCHAR(64),


    model\_name VARCHAR(128),


    architecture\_name VARCHAR(64),


    ros\_version VARCHAR(64),


    firmware\_version VARCHAR(64),


    upgrade\_firmware\_version VARCHAR(64),


    update\_available\_version VARCHAR(64),


    


    -- Seguridad SSL Autofirmado (TOFU - Trust On First Use)


    ssl\_trust\_status ssl\_trust\_status\_enum NOT NULL DEFAULT 'PENDING\_TOFU',


    ssl\_sha256\_fingerprint CHAR(64),


    ssl\_cert\_subject VARCHAR(255),


    ssl\_cert\_expires\_at TIMESTAMPTZ,


    ssl\_pinned\_at TIMESTAMPTZ,


    


    -- Metadatos de Último Contacto (Sin almacenar métricas de consumo)


    is\_reachable BOOLEAN NOT NULL DEFAULT FALSE,


    last\_seen\_at TIMESTAMPTZ,


    last\_discovery\_sync\_at TIMESTAMPTZ,


    last\_connection\_error TEXT,


    


    created\_by UUID REFERENCES users(id) ON DELETE SET NULL,


    created\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    updated\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    CONSTRAINT uq\_routers\_tenant\_name UNIQUE (tenant\_id, display\_name),


    CONSTRAINT uq\_routers\_tenant\_url UNIQUE (tenant\_id, api\_base\_url),


    CONSTRAINT uq\_routers\_tenant\_serial UNIQUE (tenant\_id, serial\_number)


);


-- Vinculación diferida de FK en user\_router\_permissions


ALTER TABLE user\_router\_permissions


    ADD CONSTRAINT fk\_urp\_router


    FOREIGN KEY (router\_id) REFERENCES routers(id) ON DELETE CASCADE;


CREATE INDEX idx\_routers\_tenant\_role ON routers (tenant\_id, network\_role);


CREATE INDEX idx\_routers\_tenant\_state ON routers (tenant\_id, admin\_state);


CREATE INDEX idx\_routers\_tenant\_coords ON routers (tenant\_id, latitude, longitude)


    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;




## **2b. Tabla tenant_custom_roles (Catálogo de Roles de Red Personalizados por Tenant)**

Permite a los operadores registrar roles de red dinámicos (ej. `L1`, `AP-Sectorial`) que extienden el catálogo estándar sin alterar el código base, gobernados con Row Level Security (RLS) estricto.

```sql
CREATE TABLE tenant_custom_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    role_name VARCHAR(64) NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_tenant_custom_role UNIQUE (tenant_id, role_name)
);

CREATE INDEX idx_tenant_custom_roles_lookup ON tenant_custom_roles (tenant_id, role_name);

ALTER TABLE tenant_custom_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_custom_roles FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_custom_roles ON tenant_custom_roles
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
```

## **3. Tabla router_tags (Etiquetado Libre para Filtros y Acciones Masivas)**

CREATE TABLE router\_tags (


    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),


    tenant\_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,


    router\_id UUID NOT NULL REFERENCES routers(id) ON DELETE CASCADE,


    tag\_name VARCHAR(48) NOT NULL


        CONSTRAINT chk\_tag\_slug CHECK (tag\_name ~ '^\[a-z0-9-\]+$'),


    created\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    CONSTRAINT uq\_router\_tag UNIQUE (tenant\_id, router\_id, tag\_name)


);


CREATE INDEX idx\_router\_tags\_lookup ON router\_tags (tenant\_id, tag\_name);




## **4. Tabla router\_credentials\_vault (Bóveda Criptográfica AES-256-GCM y Rotación)**

Almacena las credenciales de conexión a la REST API de cada MikroTik.


- **Cifrado Autenticado Obligatorio (AES-256-GCM):**

  - La contraseña actual (current\_password\_\*) y la contraseña inmediatamente anterior previa a la última rotación automática (previous\_password\_\*) se almacenan cifradas con un IV único de 12 bytes (96 bits) generado con os.urandom(12) y su correspondiente authentication tag de 16 bytes (128 bits).

  - Como **Additional Authenticated Data (AAD)** de AESGCM en Python (cryptography.hazmat.primitives.ciphers.aead.AESGCM), se DEBE pasar la cadena f"\{tenant\_id\}:\{router\_id\}".encode("utf-8"). Esto impide que alguien copie el ciphertext de un router a otra fila en la base de datos.

- **Acceso para Consulta Humana (*Step-Up Auth*):**

  - Solo los 2 perfiles más altos (SUPERADMIN\_GLOBAL y TENANT\_ADMIN) pueden desencriptar y visualizar estas claves tras validar su código 2FA TOTP en tiempo real.


CREATE TABLE router\_credentials\_vault (


    router\_id UUID PRIMARY KEY REFERENCES routers(id) ON DELETE CASCADE,


    tenant\_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,


    


    api\_username VARCHAR(64) NOT NULL,


    


    -- Clave API Actual (AES-256-GCM con AAD = tenant\_id:router\_id)


    current\_password\_ciphertext BYTEA NOT NULL,


    current\_password\_iv BYTEA NOT NULL CONSTRAINT chk\_curr\_iv\_len CHECK (octet\_length(current\_password\_iv) = 12),


    current\_password\_tag BYTEA NOT NULL CONSTRAINT chk\_curr\_tag\_len CHECK (octet\_length(current\_password\_tag) = 16),


    


    -- Clave API Inmediatamente Anterior (Respaldo ante fallo de red durante rotación automática)


    previous\_password\_ciphertext BYTEA,


    previous\_password\_iv BYTEA CONSTRAINT chk\_prev\_iv\_len CHECK (previous\_password\_iv IS NULL OR octet\_length(previous\_password\_iv) = 12),


    previous\_password\_tag BYTEA CONSTRAINT chk\_prev\_tag\_len CHECK (previous\_password\_tag IS NULL OR octet\_length(previous\_password\_tag) = 16),


    


    -- Política de Rotación Automática de Contraseña en el MikroTik


    auto\_rotate\_enabled BOOLEAN NOT NULL DEFAULT TRUE,


    rotation\_interval\_days SMALLINT NOT NULL DEFAULT 30


        CONSTRAINT chk\_rotation\_days CHECK (rotation\_interval\_days BETWEEN 1 AND 365),


    last\_rotated\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    next\_rotation\_due\_at TIMESTAMPTZ,


    last\_rotation\_status VARCHAR(32) NOT NULL DEFAULT 'SUCCESS',


    


    updated\_by UUID REFERENCES users(id) ON DELETE SET NULL,


    updated\_at TIMESTAMPTZ NOT NULL DEFAULT NOW()


);


CREATE INDEX idx\_vault\_next\_rotation ON router\_credentials\_vault (tenant\_id, next\_rotation\_due\_at)


    WHERE auto\_rotate\_enabled = TRUE;




## **5. Tabla maintenance\_windows (Ventanas de Mantenimiento Programadas)**

Permite agendar mantenimientos individuales o por etiqueta/grupo para que el monitor en segundo plano suprima alertas externas y pinte los equipos en azul en el mapa y el Wallboard NOC:


CREATE TABLE maintenance\_windows (


    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),


    tenant\_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,


    title VARCHAR(150) NOT NULL,


    reason TEXT NOT NULL,


    


    -- Alcance: puede aplicar a un router puntual o a una etiqueta (tag\_name)


    router\_id UUID REFERENCES routers(id) ON DELETE CASCADE,


    target\_tag VARCHAR(48),


    


    starts\_at TIMESTAMPTZ NOT NULL,


    ends\_at TIMESTAMPTZ NOT NULL,


    suppress\_alerts BOOLEAN NOT NULL DEFAULT TRUE,


    is\_cancelled BOOLEAN NOT NULL DEFAULT FALSE,


    


    created\_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,


    created\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    CONSTRAINT chk\_window\_dates CHECK (ends\_at \> starts\_at),


    CONSTRAINT chk\_window\_target CHECK (router\_id IS NOT NULL OR target\_tag IS NOT NULL)


);


CREATE INDEX idx\_maint\_active\_window ON maintenance\_windows (tenant\_id, starts\_at, ends\_at)


    WHERE is\_cancelled = FALSE;




## **6. Políticas RLS para Inventario, Bóveda y Mantenimiento**

ALTER TABLE routers ENABLE ROW LEVEL SECURITY;


ALTER TABLE routers FORCE ROW LEVEL SECURITY;


CREATE POLICY tenant\_isolation\_routers ON routers


    USING (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid)


    WITH CHECK (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid);


ALTER TABLE router\_tags ENABLE ROW LEVEL SECURITY;


ALTER TABLE router\_tags FORCE ROW LEVEL SECURITY;


CREATE POLICY tenant\_isolation\_router\_tags ON router\_tags


    USING (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid)


    WITH CHECK (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid);


ALTER TABLE router\_credentials\_vault ENABLE ROW LEVEL SECURITY;


ALTER TABLE router\_credentials\_vault FORCE ROW LEVEL SECURITY;


CREATE POLICY tenant\_isolation\_vault ON router\_credentials\_vault


    USING (


        current\_setting('app.is\_superadmin\_global', true) = 'true'


        OR tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid


    )


    WITH CHECK (


        current\_setting('app.is\_superadmin\_global', true) = 'true'


        OR tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid


    );


ALTER TABLE maintenance\_windows ENABLE ROW LEVEL SECURITY;


ALTER TABLE maintenance\_windows FORCE ROW LEVEL SECURITY;


CREATE POLICY tenant\_isolation\_maint ON maintenance\_windows


    USING (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid)


    WITH CHECK (tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid);
