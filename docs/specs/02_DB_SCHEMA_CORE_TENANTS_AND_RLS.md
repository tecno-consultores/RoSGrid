# 02 — ESQUEMA DE BASE DE DATOS: NÚCLEO MULTI-TENANT, USUARIOS, ROLES Y POLÍTICAS RLS (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento define el esquema relacional en **PostgreSQL 17** para el aislamiento Multi-Tenant, gestión de usuarios, autenticación de doble factor (2FA TOTP), los 11 roles del sistema y la matriz de asignación de routers por usuario. Toda tabla que pertenezca a un Tenant DEBE implementar **Row-Level Security (RLS)** forzoso a nivel de motor de base de datos.




## **1. Reglas Generales de Modelado en PostgreSQL 17 y SQLAlchemy 2.0 Async**

1. **Identificadores Primarios (UUIDv7 / UUIDv4):**

   - Todas las claves primarias (id) usarán el tipo nativo UUID de PostgreSQL.

   - En Python (SQLAlchemy 2.0 MappedAsDataclass / DeclarativeBase), se generarán mediante UUIDv7 ordenable por tiempo (o gen\_random\_uuid() como respaldo a nivel DDL).

2. **Marcas de Tiempo (TIMESTAMPTZ):**

   - Todas las columnas de fecha/hora DEBEN ser TIMESTAMPTZ (TIMESTAMP WITH TIME ZONE) almacenadas en UTC. Queda prohibido usar TIMESTAMP WITHOUT TIME ZONE.

3. **Aislamiento Estricto por Empresa (tenant\_id):**

   - Cada empresa es una entidad 100% independiente (tenants).

   - Si un mismo humano presta servicios a dos empresas distintas, tendrá un registro de usuario independiente en cada tenant\_id.

   - La restricción de unicidad de correo y nombre de usuario es compuesta: UNIQUE (tenant\_id, email) y UNIQUE (tenant\_id, username).

4. **Cero Métricas en PostgreSQL:**

   - Queda prohibido agregar columnas o tablas de historial de CPU, RAM, temperatura o tráfico en PostgreSQL.




## **2. Tipos Enumerados (ENUM) del Dominio Core**

AntiGravity DEBE declarar los siguientes tipos en la primera migración de Alembic (migrations/versions/0001\_initial\_core.py):


-- Estado operativo de una organización (Tenant)


CREATE TYPE tenant\_status\_enum AS ENUM (


    'ACTIVE',


    'SUSPENDED',


    'MAINTENANCE'


);


-- Catálogo oficial de los 11 roles de RoSGrid


CREATE TYPE system\_role\_enum AS ENUM (


    'SUPERADMIN\_GLOBAL',      -- 1. Administración de plataforma y creación de Tenants


    'TENANT\_ADMIN',           -- 2. Administrador total dentro de su empresa (incluye Bóveda Step-Up)


    'SUPERVISOR',             -- 3. Aprobador Maker-Checker, control de sesiones (Kill-Switch) y ventanas


    'SUPPORT\_L3',             -- 4. Ingeniería Core, BGP/OSPF, acciones masivas, backups/restore y capa 2


    'SUPPORT\_L2',             -- 5. Administración de red intermedia (sujeto a Maker-Checker en acciones críticas)


    'SUPPORT\_L1',             -- 6. Helpdesk, diagnóstico en vivo, reconexión PPPoE/DHCP y solicitud de cambios


    'FIELD\_TECH',             -- 7. Técnico de campo/instalador acotado a nodos asignados y validación física/SFP


    'INVENTORY\_MANAGER',      -- 8. Gestor de inventario, onboarding CSV, rotación de claves y datos físicos


    'AUDITOR',                -- 9. Solo lectura de bitácora inmutable (audit\_logs) y comparador Diff (.rsc)


    'NOC\_MONITOR',            -- 10. Wallboard NOC de solo lectura (mapa OSM, estado Up/Down y alertas en vivo)


    'SERVICE\_ACCOUNT'         -- 11. Cuenta Machine-to-Machine acotada por IP y alcances puntuales


);




## **3. Definición DDL de Tablas Core**

### **3.1 Tabla tenants (Empresas / Organizaciones)**

CREATE TABLE tenants (


    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),


    slug VARCHAR(64) NOT NULL UNIQUE


        CONSTRAINT chk\_tenant\_slug\_format CHECK (slug ~ '^\[a-z0-9\]+(?:-\[a-z0-9\]+)\*$'),


    name VARCHAR(150) NOT NULL,


    tax\_id VARCHAR(64),


    status tenant\_status\_enum NOT NULL DEFAULT 'ACTIVE',


    max\_routers\_quota INTEGER NOT NULL DEFAULT 100


        CONSTRAINT chk\_max\_routers\_positive CHECK (max\_routers\_quota \> 0),


    max\_users\_quota INTEGER NOT NULL DEFAULT 50


        CONSTRAINT chk\_max\_users\_positive CHECK (max\_users\_quota \> 0),


    require\_2fa\_all\_users BOOLEAN NOT NULL DEFAULT TRUE,


    default\_safemode\_seconds INTEGER NOT NULL DEFAULT 60


        CONSTRAINT chk\_safemode\_range CHECK (default\_safemode\_seconds BETWEEN 15 AND 300),


    created\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    updated\_at TIMESTAMPTZ NOT NULL DEFAULT NOW()


);


CREATE INDEX idx\_tenants\_slug ON tenants (slug);


CREATE INDEX idx\_tenants\_status ON tenants (status);

### **3.2 Tabla users (Usuarios por Tenant y Configuración 2FA TOTP)**

- **Nota de Seguridad:** El secreto TOTP (totp\_secret\_encrypted) NO se almacena en texto plano; se cifra con AES-256-GCM usando la llave maestra ROSGRID\_MASTER\_VAULT\_KEY igual que las credenciales de los routers.

- Las contraseñas de usuarios humanos se almacenan exclusivamente con hash **Argon2id** (argon2-cffi con parámetros OWASP: time\_cost=3, memory\_cost=65536, parallelism=4).


CREATE TABLE users (


    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),


    tenant\_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,


    username VARCHAR(64) NOT NULL,


    email VARCHAR(255) NOT NULL,


    full\_name VARCHAR(150) NOT NULL,


    password\_hash TEXT NOT NULL,


    role system\_role\_enum NOT NULL,


    is\_active BOOLEAN NOT NULL DEFAULT TRUE,


    is\_locked BOOLEAN NOT NULL DEFAULT FALSE,


    failed\_login\_attempts SMALLINT NOT NULL DEFAULT 0,


    locked\_until TIMESTAMPTZ,


    


    -- Doble Factor de Autenticación (TOTP RFC 6238)


    totp\_enabled BOOLEAN NOT NULL DEFAULT FALSE,


    totp\_secret\_ciphertext BYTEA,


    totp\_secret\_iv BYTEA,


    totp\_secret\_tag BYTEA,


    totp\_recovery\_codes\_hashes JSONB NOT NULL DEFAULT '\[\]'::jsonb,


    


    -- Restricción opcional de IPs origen (obligatoria para SERVICE\_ACCOUNT)


    allowed\_cidr\_list JSONB NOT NULL DEFAULT '\[\]'::jsonb,


    


    -- Control de acceso a todos los routers del Tenant o solo asignados explícitamente


    has\_all\_routers\_access BOOLEAN NOT NULL DEFAULT FALSE,


    


    last\_login\_at TIMESTAMPTZ,


    last\_login\_ip INET,


    password\_changed\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    created\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    updated\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    CONSTRAINT uq\_users\_tenant\_email UNIQUE (tenant\_id, email),


    CONSTRAINT uq\_users\_tenant\_username UNIQUE (tenant\_id, username)


);


CREATE INDEX idx\_users\_tenant\_id ON users (tenant\_id);


CREATE INDEX idx\_users\_tenant\_role ON users (tenant\_id, role);


CREATE INDEX idx\_users\_tenant\_email ON users (tenant\_id, LOWER(email));

### **3.3 Tabla user\_router\_permissions (Segmentación Granular de Equipos y Permisos por Usuario)**

Permite que el **Administrador de Tenant** asigne a cada técnico exactamente qué MikroTiks puede ver u operar, y si tiene permisos adicionales o restringidos sobre ese equipo puntual:


CREATE TABLE user\_router\_permissions (


    id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),


    tenant\_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,


    user\_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,


    router\_id UUID NOT NULL, -- FK hacia routers(id) definida en 03\_DB\_SCHEMA\_INVENTORY


    


    -- Permisos específicos sobre este router


    can\_read BOOLEAN NOT NULL DEFAULT TRUE,


    can\_write\_layer1 BOOLEAN NOT NULL DEFAULT FALSE,


    can\_write\_layer2 BOOLEAN NOT NULL DEFAULT FALSE,


    can\_execute\_diagnostics BOOLEAN NOT NULL DEFAULT TRUE,


    can\_trigger\_backup BOOLEAN NOT NULL DEFAULT FALSE,


    can\_reboot BOOLEAN NOT NULL DEFAULT FALSE,


    bypass\_maker\_checker BOOLEAN NOT NULL DEFAULT FALSE,


    


    assigned\_by UUID REFERENCES users(id) ON DELETE SET NULL,


    created\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    updated\_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    CONSTRAINT uq\_user\_router\_perm UNIQUE (tenant\_id, user\_id, router\_id)


);


CREATE INDEX idx\_urp\_tenant\_user ON user\_router\_permissions (tenant\_id, user\_id);


CREATE INDEX idx\_urp\_tenant\_router ON user\_router\_permissions (tenant\_id, router\_id);




## **4. Políticas de Aislamiento Multi-Tenant (*Row-Level Security — RLS*)**

Para garantizar que ningún bug de código pueda filtrar registros de una empresa a otra, PostgreSQL aplicará RLS en todas las tablas con tenant\_id.

### **4.1 Variables de Contexto de Sesión PostgreSQL**

En cada transacción HTTP o tarea de worker, el middleware de base de datos de FastAPI ejecutará al abrir la transacción:


SET LOCAL app.current\_tenant\_id = '\<uuid\_del\_tenant\>';


SET LOCAL app.is\_superadmin\_global = 'false'; -- 'true' solo para rol SUPERADMIN\_GLOBAL en endpoints globales

### **4.2 Activación de RLS y Políticas DDL**

ALTER TABLE users ENABLE ROW LEVEL SECURITY;


ALTER TABLE users FORCE ROW LEVEL SECURITY;


CREATE POLICY tenant\_isolation\_users ON users


    USING (


        current\_setting('app.is\_superadmin\_global', true) = 'true'


        OR tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid


    )


    WITH CHECK (


        current\_setting('app.is\_superadmin\_global', true) = 'true'


        OR tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid


    );


ALTER TABLE user\_router\_permissions ENABLE ROW LEVEL SECURITY;


ALTER TABLE user\_router\_permissions FORCE ROW LEVEL SECURITY;


CREATE POLICY tenant\_isolation\_urp ON user\_router\_permissions


    USING (


        tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid


    )


    WITH CHECK (


        tenant\_id = NULLIF(current\_setting('app.current\_tenant\_id', true), '')::uuid


    );




## **5. Implementación del Contexto RLS en SQLAlchemy 2.0 (fastapi/src/db/session.py)**

AntiGravity DEBE implementar un generador de dependencias get\_tenant\_db\_session con complejidad ciclomática Grado A (CC \<= 4) que inyecte de manera determinista las variables de sesión en PostgreSQL:


- Extrae tenant\_id y role del token de sesión validado.

- Abre una transacción async with async\_session\_maker.begin() as session:.

- Ejecuta await session.execute(text("SELECT set\_config('app.current\_tenant\_id', :tid, true), set\_config('app.is\_superadmin\_global', :sa, true)"), \{"tid": str(tenant\_id), "sa": "true" if is\_superadmin else "false"\}).

- Entrega la sesión al endpoint o servicio.

- En pruebas unitarias (\*.unit.py), este generador se reemplaza limpiamente mediante app.dependency\_overrides y pytest-mock sin requerir conexión a PostgreSQL.
