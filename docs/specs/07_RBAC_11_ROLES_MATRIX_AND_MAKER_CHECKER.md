# 07 — MATRIZ DE PERMISOS RBAC (11 ROLES), SEGMENTACIÓN POR EQUIPO Y MOTOR MAKER-CHECKER (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento define la matriz de control de acceso basado en roles (**RBAC**) para los **11 perfiles oficiales** de **RoSGrid**, la combinación con los permisos por equipo (user\_router\_permissions) y la lógica determinista del interceptor **Maker-Checker** (fastapi/src/rbac/). Para cumplir con Radon CC \< C (CC \<= 5), la evaluación de permisos DEBE implementarse mediante tablas declarativas de políticas (diccionarios inmutables de permisos) y nunca mediante bloques if/elif/else anidados.




## **1. Catálogo Oficial de los 11 Roles y Nivel Jerárquico**

| **\#** | **Código ENUM (system\_role\_enum)** | **Nombre del Perfil** | **Alcance de Routers por Defecto** | **2FA TOTP** |
| - | - | - | - | - |
| **1** | SUPERADMIN\_GLOBAL | SuperAdministrador de Plataforma | Global (Gestión de Tenants/Plataforma + Acceso total si se asigna) | Obligatorio |
| **2** | TENANT\_ADMIN | Administrador de Empresa (Tenant) | Todos los routers de su Tenant (has\_all\_routers\_access = True) | Obligatorio |
| **3** | SUPERVISOR | Supervisor Operativo | Todos los routers de su Tenant o lista asignada | Obligatorio |
| **4** | SUPPORT\_L3 | Soporte Nivel 3 (Ingeniería / Core) | Routers asignados (o todos si el Admin lo habilita) | Obligatorio |
| **5** | SUPPORT\_L2 | Soporte Nivel 2 (Administración Red) | Exclusivamente routers asignados en user\_router\_permissions | Obligatorio |
| **6** | SUPPORT\_L1 | Soporte Nivel 1 (Helpdesk / Diagnóstico) | Exclusivamente routers asignados en user\_router\_permissions | Obligatorio |
| **7** | FIELD\_TECH | Técnico de Campo / Instalador | Exclusivamente nodos/routers asignados a su cuadrilla | Obligatorio |
| **8** | INVENTORY\_MANAGER | Gestor de Inventario y Provisioning | Todos los routers de su Tenant (solo plano de inventario/bóveda) | Obligatorio |
| **9** | AUDITOR | Auditor de Seguridad y Cumplimiento | Todos los routers de su Tenant (100% Solo Lectura / Bitácora / Diff) | Obligatorio |
| **10** | NOC\_MONITOR | Monitor NOC (Wallboard / Pantallas) | Todos los routers de su Tenant (Solo Lectura de Estado/Mapa/Alertas) | Opcional / Token |
| **11** | SERVICE\_ACCOUNT | Cuenta de Servicio (API / Webhook M2M) | Exclusivamente routers y scopes asignados + filtro IP CIDR obligatorio | API Key + HMAC |




## **2. Matriz Exhaustiva de Permisos por Módulo y Acción**

Leyenda de valores de política en fastapi/src/rbac/policy\_matrix.py:


- ALLOW: Ejecución directa permitida (sujeta a Safe Mode si modifica red).

- MAKER\_CHECKER: El usuario **no puede ejecutarlo en directo**, pero el sistema acepta la petición (HTTP 202 Accepted), captura el estado previo y crea un registro en approval\_requests (PENDING) para que un aprobador (TENANT\_ADMIN, SUPERVISOR o SUPPORT\_L3) lo autorice con un clic.

- DENY: Rechazado inmediatamente con HTTP 403 Forbidden y registrado en audit\_logs.


| **Módulo / Acción en RoSGrid** | **SUPERADMIN** | **TENANT\_ADMIN** | **SUPERVISOR** | **SUPPORT\_L3** | **SUPPORT\_L2** | **SUPPORT\_L1** | **FIELD\_TECH** | **INVENTORY\_MGR** | **AUDITOR** | **NOC\_MONITOR** | **SERVICE\_ACCT** |
| - | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **1. Gestión de Tenants (Crear/Suspender Empresas)** | ALLOW | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| **2. Gestión de Usuarios y Asignación de Routers** | ALLOW | ALLOW | READ\_ONLY | DENY | DENY | DENY | DENY | DENY | READ\_ONLY | DENY | DENY |
| **3. Ver Sesiones Activas y Ejecutar *Kill-Switch*** | ALLOW | ALLOW | ALLOW | DENY | DENY | DENY | DENY | DENY | READ\_ONLY | DENY | DENY |
| **4. Alta/Edición de Routers e Importación CSV** | ALLOW | ALLOW | ALLOW | ALLOW | DENY | DENY | DENY | ALLOW | DENY | DENY | DENY |
| **5. Revelar Claves API de Bóveda (*Step-Up 2FA*)** | ALLOW | ALLOW | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| **6. Disparar Rotación Automática de Clave API** | ALLOW | ALLOW | ALLOW | ALLOW | DENY | DENY | DENY | ALLOW | DENY | DENY | DENY |
| **7. Programar Ventanas de Mantenimiento** | ALLOW | ALLOW | ALLOW | ALLOW | MAKER\_CHECKER | DENY | DENY | ALLOW | DENY | DENY | DENY |
| **8. Ver Mapa OSM, Wallboard NOC y Gráficas en Vivo** | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | DENY |
| **9. Diagnóstico en Vivo (Ping, Traceroute, ARP, SFP DDM, Neighbors, Log)** | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | DENY | DENY | DENY | ALLOW |
| **10. Operaciones L1 Operativas (Reconectar PPPoE activo, renovar DHCP lease, limpiar entrada ARP/Host)** | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | DENY | DENY | DENY | ALLOW |
| **11. Configuración Estándar WebFig Capa 1 (VLANs, Colas, PPP Secrets, DHCP, DNS, Reglas Firewall Forward, NAT)** | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | MAKER\_CHECKER | DENY | DENY | DENY | DENY | ALLOW |
| **12. Acciones Críticas de Red (BGP/OSPF, Ruta 0.0.0.0/0, Firewall input, /ip/service, IPs troncales/WAN)** | ALLOW | ALLOW | ALLOW | ALLOW | MAKER\_CHECKER | MAKER\_CHECKER | DENY | DENY | DENY | DENY | DENY |
| **13. Reiniciar (reboot) o Apagar (shutdown) Router** | ALLOW | ALLOW | ALLOW | ALLOW | MAKER\_CHECKER | MAKER\_CHECKER | MAKER\_CHECKER | DENY | DENY | DENY | DENY |
| **14. Motor Dinámico Universal WebFig (Capa 2 /rest/\*)** | ALLOW | ALLOW | READ\_ONLY | ALLOW | READ\_ONLY | DENY | DENY | DENY | READ\_ONLY | DENY | DENY |
| **15. Ejecutar Backup Manual y Comparar Diff .rsc (Git)** | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | DENY | DENY | ALLOW | READ\_ONLY | DENY | ALLOW |
| **16. Restaurar Backup o Inyectar Script (/system/script)** | ALLOW | ALLOW | ALLOW | ALLOW | MAKER\_CHECKER | DENY | DENY | DENY | DENY | DENY | DENY |
| **17. Acciones Masivas Multi-Router y Upgrade RouterOS** | ALLOW | ALLOW | ALLOW | ALLOW | MAKER\_CHECKER | DENY | DENY | DENY | DENY | DENY | DENY |
| **18. Aprobar / Rechazar Solicitudes *Maker-Checker*** | ALLOW | ALLOW | ALLOW | ALLOW | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| **19. Consultar y Exportar Bitácora Inmutable (audit\_logs)** | ALLOW | ALLOW | ALLOW | DENY | DENY | DENY | DENY | DENY | ALLOW | DENY | DENY |




## **3. Algoritmo de Evaluación en 2 Niveles (Rol Global + Permiso por Equipo)**

Toda petición hacia un endpoint que incluya \{router\_id\} pasa por el verificador verify\_router\_access(user, router\_id, required\_capability):


1. **Nivel 1 (Aislamiento Tenant):** Verifica que el router exista en el tenant\_id del usuario (garantizado por RLS + comprobación explícita; si no existe, devuelve 404 Not Found).

2. **Nivel 2 (Asignación de Equipo):**

   - Si el usuario tiene role in (SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, INVENTORY\_MANAGER, AUDITOR, NOC\_MONITOR) o tiene has\_all\_routers\_access == True, pasa a la evaluación de capacidad.

   - En caso contrario (SUPPORT\_L3, SUPPORT\_L2, SUPPORT\_L1, FIELD\_TECH, SERVICE\_ACCOUNT sin acceso global), consulta user\_router\_permissions para (tenant\_id, user\_id, router\_id). Si no tiene fila asignada o can\_read == False, rechaza con HTTP 403 Forbidden.

3. **Nivel 3 (Evaluación de Capacidad y *Maker-Checker*):**

   - Consulta la tabla declarativa POLICY\_MATRIX\[user.role\]\[action\_code\].

   - Si la fila de user\_router\_permissions tiene bypass\_maker\_checker == True (otorgado explícitamente por el TENANT\_ADMIN para ese router particular), un resultado MAKER\_CHECKER se promueve a ALLOW.




## **4. Catálogo Exacto de Reglas de Intercepción *Maker-Checker***

Además de la clasificación por rol, el clasificador classify\_critical\_mikrotik\_operation(method, ros\_path, payload) marca automáticamente una operación como **Crítica** cuando cumple cualquiera de estas 7 firmas técnicas:


1. **ROUTER\_REBOOT\_OR\_SHUTDOWN:**

   - ros\_path es /rest/system/reboot, /rest/system/shutdown o /rest/system/reset-configuration.

2. **BULK\_MULTI\_ROUTER\_EXECUTION:**

   - Cualquier operación en /api/v1/operations/bulk-jobs donde len(target\_router\_ids) \> 1.

3. **ROUTING\_BGP\_OSPF\_DEFAULT\_CHANGE:**

   - Cualquier POST, PATCH, PUT o DELETE sobre /rest/routing/bgp/\*, /rest/routing/ospf/\*, /rest/routing/filter/\*, o sobre /rest/ip/route cuando dst-address == "0.0.0.0/0" o dst-address == "::/0".

4. **FIREWALL\_INPUT\_OR\_SERVICE\_PORT\_CHANGE:**

   - Modificación o eliminación en /rest/ip/firewall/filter o /rest/ipv6/firewall/filter donde chain == "input", o cualquier cambio en /rest/ip/service (puertos www-ssl, winbox, ssh, api, api-ssl).

5. **WAN\_TRUNK\_INTERFACE\_OR\_IP\_CHANGE:**

   - Deshabilitar (disabled: "true") o eliminar una interfaz física/bridge/vlan/bonding o modificar una IP en /rest/ip/address.

6. **BACKUP\_RESTORE\_OR\_CUSTOM\_SCRIPT:**

   - Ejecución de /rest/system/backup/load, /rest/import o escritura en /rest/system/script / /rest/system/scheduler.

7. **ROUTER\_INTERNAL\_USER\_CHANGE:**

   - Cualquier operación mutable sobre /rest/user o /rest/user/group (excepto la rotación automática ejecutada por el servicio interno de Bóveda).

### **Respuesta Estándar cuando una Petición es Interceptada por *Maker-Checker* (HTTP 202 Accepted)**

\{


  "status": "INTERCEPTED\_FOR\_APPROVAL",


  "approval\_request\_id": "01928f99-1234-7a00-8000-abcdef123456",


  "action\_type": "FIREWALL\_INPUT\_OR\_SERVICE\_PORT\_CHANGE",


  "message": "Esta operación es crítica para tu nivel de permisos y ha sido enviada a la bandeja de aprobación del Supervisor / Soporte N3.",


  "expires\_at": "2026-10-15T18:15:00Z"


\}


Al mismo tiempo, FastAPI publica un evento en Redis Pub/Sub y envía notificación por los canales activos del Tenant (APPROVAL\_NEEDED) para que el Supervisor la autorice en tiempo real.
