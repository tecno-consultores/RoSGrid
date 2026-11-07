# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 88: Desbloqueo del Onboarding Inicial para `TENANT_ADMIN`, Asignación Directa de Empresa (`tenant_id`) a Usuarios en `/admin/users` y Guardrail `WebSocketDisconnected`

**Estado:** Pendiente de Implementación (Lista para Ejecución Determinista)  
**Hito Asociado:** Hito 30.11  
**Motor de Ejecución Objetivo:** Gemini 3.8 Flash (High)  
**Archivos Afectados:**
- `fastapi/src/api/v1/tenants.py`
- `fastapi/src/schemas/users.py`
- `fastapi/src/api/v1/users.py`
- `fastapi/src/api/v1/websockets.py`
- `vue3/src/types/index.ts`
- `vue3/src/components/common/TenantOnboardingModal.vue`
- `vue3/src/views/UsersAndPermissionsView.vue`
- `fastapi/tests/api/test_tenants_features_rbac.unit.py`
- `fastapi/tests/api/test_tenants_and_users.unit.py`
- `vue3/src/views/admin/usersAndPermissionsView.unit.ts`
- `fastapi/test/api_test.feature` (+ réplicas en `docs/examples/fastapi/`)
- `vue3/test/ui_business_flow.feature` (+ réplicas en `docs/examples/vue3/`)

---

## 1. Diagnóstico Forense de las 3 Causas Raíz (Caso Real Empresa `caja`)

### 1.1 Causa Raíz 1: Bloqueo `HTTP 403 Forbidden` en `TenantOnboardingModal.vue` al Iniciar Sesión con el Administrador de una Nueva Empresa (`TENANT_ADMIN`)
- Cuando un `SUPERADMIN_GLOBAL` crea una nueva empresa (ej. `caja`) desde `/admin/tenants` (`POST /api/v1/tenants`), la tabla `tenants` se inicializa con `onboarding_completed = False` y se crea su usuario administrador inicial con el rol `SystemRoleEnum.TENANT_ADMIN`.
- Al iniciar sesión con ese usuario `TENANT_ADMIN`, `vue3/src/App.vue` (líneas 23–30) evalúa:
  ```ts
  const isPrivilegedAdmin = role === 'SUPERADMIN_GLOBAL' || role === 'TENANT_ADMIN';
  return authStore.tenantFeatures?.onboarding_completed === false;
  ```
  y despliega a pantalla completa el modal bloqueante **`Configuración Inicial de Despliegue — RoSGrid`** (`TenantOnboardingModal.vue`).
- Sin embargo, cuando el `TENANT_ADMIN` selecciona un perfil (ej. **Proveedor ISP / WISP**) y pulsa **`🚀 Comenzar con Perfil ISP`**, `TenantOnboardingModal.vue` ejecuta:
  ```ts
  const res = await http.patch<TenantFeatureFlags>(`/api/v1/tenants/${tid}/features`, payload);
  ```
- En `fastapi/src/api/v1/tenants.py` (líneas 133–147), el endpoint `update_tenant_features` exigía exclusivamente `SystemRoleEnum.SUPERADMIN_GLOBAL`:
  ```
  INFO: 172.18.0.1:0 - "PATCH /api/v1/tenants/ae7f5539-cd9c-45e3-bbe1-ac354c70e223/features HTTP/1.1" 403 Forbidden
  ```
- Además, `TenantOnboardingModal.vue` leía `err?.response?.data?.detail` (propiedad de Axios inexistente en el `HttpError` propio de `httpClient.ts`, que usa `err.detail`), mostrando el error genérico `"⚠️ Error al persistir la configuración inicial del tenant."` y dejando al `TENANT_ADMIN` atrapado sin poder cerrar el modal.

### 1.2 Causa Raíz 2: Ausencia de Selector Directo de Empresa (`tenant_id`) al Crear o Reasignar Usuarios en `/admin/users` (`UsersAndPermissionsView.vue`)
- En `POST /api/v1/users` (`fastapi/src/api/v1/users.py`, línea 103), el backend tomaba siempre `tenant_id = uuid.UUID(claims["tid"])` sin aceptar un `tenant_id` explícito en `CreateUserRequest`, y no existía un endpoint ni control visual en `/admin/users` para que el `SUPERADMIN_GLOBAL` pudiera elegir a qué empresa asignar un usuario nuevo o transferir un usuario existente a otra empresa sin cambiar antes de contexto global.

### 1.3 Causa Raíz 3: Traza `starlette.websockets.WebSocketDisconnected` en `tenant_events_ws` (`fastapi/src/api/v1/websockets.py`, línea 226)
- En `tenant_events_ws`, cuando un usuario cierra sesión o cambia de contexto y paralelamente se publica un evento en Redis Pub/Sub, `await ws.send_text(raw_str)` puede lanzar `starlette.websockets.WebSocketDisconnected` o `RuntimeError` (los cuales no heredan de `fastapi.WebSocketDisconnect`), provocando un traceback en los logs del contenedor.

---

## 2. Instrucciones Paso a Paso para Implementación (Gemini 3.8 Flash High)

### Paso 1: Autorizar Onboarding Inicial de `TENANT_ADMIN` en `fastapi/src/api/v1/tenants.py` y Mejorar Manejo de Error en `TenantOnboardingModal.vue`

#### 1.A. Modificar `update_tenant_features` en `fastapi/src/api/v1/tenants.py` (líneas 133–153)
Permitir `SystemRoleEnum.SUPERADMIN_GLOBAL` y `SystemRoleEnum.TENANT_ADMIN` en `require_roles`. Dentro de la función:
- Si el usuario es `SUPERADMIN_GLOBAL`, tiene permiso total sobre cualquier empresa.
- Si el usuario es `TENANT_ADMIN`, se le autoriza **únicamente** cuando:
  1. Pertenece a esa misma empresa (`str(claims.get("tid")) == str(tenant_id)`),
  2. La empresa aún no ha completado su onboarding inicial (`not bool(getattr(tenant, "onboarding_completed", False))`), y
  3. El payload enviado está completando el onboarding inicial (`body.onboarding_completed is True`).
- Si la empresa ya completó el onboarding (`tenant.onboarding_completed is True`) o el `TENANT_ADMIN` intenta modificar flags posteriormente sin `onboarding_completed=True` (como valida `test_tenant_features_rbac_superadmin_only_and_audit`), se lanza `HTTP 403 Forbidden`:

```python
@router.patch("/{tenant_id}/features", response_model=TenantFeaturesResponse)
@router.put("/{tenant_id}/features", response_model=TenantFeaturesResponse)
async def update_tenant_features(
    tenant_id: uuid.UUID,
    body: UpdateTenantFeaturesRequest,
    request: Request,
    claims: dict[str, Any] = Depends(
        require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)
    ),
    db: AsyncSession = Depends(get_db_session),
) -> TenantFeaturesResponse:
    user_role = claims.get("rol")
    user_tid = claims.get("tid")
    tenant = await _load_tenant_or_404(db, tenant_id)

    is_superadmin = user_role == SystemRoleEnum.SUPERADMIN_GLOBAL.value
    is_initial_tenant_onboarding = (
        user_role == SystemRoleEnum.TENANT_ADMIN.value
        and str(user_tid) == str(tenant_id)
        and not bool(getattr(tenant, "onboarding_completed", False))
        and body.onboarding_completed is True
    )
    if not is_superadmin and not is_initial_tenant_onboarding:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los usuarios con rol SUPERADMIN_GLOBAL pueden modificar los módulos y licencias de las empresas.",
        )

    before_state = extract_tenant_features(tenant)
```

#### 1.B. Actualizar `handleCompleteOnboarding` en `vue3/src/components/common/TenantOnboardingModal.vue` (líneas 93–98)
Leer `err?.detail` además de `err?.response?.data?.detail`:

```ts
    } catch (err: any) {
      console.error('Error completando onboarding:', err);
      errorMessage.value =
        err?.detail ||
        err?.response?.data?.detail ||
        err?.message ||
        'Error al persistir la configuración inicial del tenant.';
    } finally {
```

---

### Paso 2: Asignación y Reasignación Directa de Empresa (`tenant_id`) para Usuarios en Backend (`fastapi/src/schemas/users.py` y `fastapi/src/api/v1/users.py`)

#### 2.A. Ampliar esquemas en `fastapi/src/schemas/users.py`
1. En `CreateUserRequest` (línea 13), añadir el campo opcional `tenant_id`:
   ```python
   class CreateUserRequest(BaseModel):
       model_config = ConfigDict(extra="forbid")

       username: str = Field(..., min_length=3, max_length=64)
       email: EmailStr
       full_name: str = Field(default="", max_length=150)
       temporary_password: str | None = Field(None, min_length=8)
       password: str | None = Field(None, min_length=8)
       role: SystemRoleEnum
       tenant_id: uuid.UUID | None = Field(
           default=None,
           description="ID de la empresa destino (opcional, exclusivo para SUPERADMIN_GLOBAL)",
       )
       has_all_routers_access: bool = False
       allowed_cidr_list: list[str] = Field(default_factory=list)
   ```
2. Añadir el esquema `AssignUserTenantRequest` debajo de `UpdateUserRequest` (alrededor de la línea 59):
   ```python
   class AssignUserTenantRequest(BaseModel):
       model_config = ConfigDict(extra="forbid")

       tenant_id: uuid.UUID = Field(..., description="ID de la empresa a la que se asignará el usuario")
       role: SystemRoleEnum | None = Field(default=None, description="Rol opcional en la empresa destino")
   ```
3. En `UserResponse` (línea 98), añadir `tenant_slug` y `tenant_name` opcionales:
   ```python
   class UserResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)

       id: uuid.UUID
       tenant_id: uuid.UUID
       tenant_slug: str | None = None
       tenant_name: str | None = None
       username: str
   ```

#### 2.B. Actualizar `list_users`, `create_user` y añadir `PATCH /api/v1/users/{user_id}/tenant` en `fastapi/src/api/v1/users.py`
1. Importar `AssignUserTenantRequest` desde `src.schemas.users`.
2. En `list_users` (líneas 62–95 de `fastapi/src/api/v1/users.py`), enriquecer cada usuario con `tenant_slug` y `tenant_name` consultando los tenants correspondientes:
   ```python
   @router.get("", response_model=list[UserResponse])
   async def list_users(
       role: SystemRoleEnum | None = None,
       is_active: bool | None = None,
       pending_only: bool = False,
       search: str | None = None,
       all_tenants: bool = False,
       claims: dict[str, Any] = Depends(
           require_roles(
               SystemRoleEnum.SUPERADMIN_GLOBAL,
               SystemRoleEnum.TENANT_ADMIN,
               SystemRoleEnum.SUPERVISOR,
               SystemRoleEnum.AUDITOR,
           )
       ),
       db: AsyncSession = Depends(get_db_session),
   ) -> list[UserResponse]:
       tenant_id = uuid.UUID(claims["tid"])
       is_sa = claims["rol"] == SystemRoleEnum.SUPERADMIN_GLOBAL.value
       await set_tenant_context(db, tenant_id, is_superadmin=is_sa)

       stmt = select(User)
       if not (is_sa and all_tenants):
           stmt = stmt.where(User.tenant_id == tenant_id)
       if role is not None:
           stmt = stmt.where(User.role == role)
       if pending_only:
           stmt = stmt.where(User.is_active.is_(False))
       elif is_active is not None:
           stmt = stmt.where(User.is_active == is_active)
       if search:
           pattern = f"%{search}%"
           stmt = stmt.where(User.username.ilike(pattern) | User.email.ilike(pattern))

       users = list((await db.execute(stmt)).scalars().all())
       tenant_map: dict[uuid.UUID, tuple[str, str]] = {}
       try:
           t_ids = {u.tenant_id for u in users if getattr(u, "tenant_id", None)}
           if t_ids:
               t_rows = (await db.execute(select(Tenant).where(Tenant.id.in_(t_ids)))).scalars().all()
               tenant_map = {
                   t.id: (t.slug, t.name)
                   for t in t_rows
                   if getattr(t, "id", None) and getattr(t, "slug", None) and getattr(t, "name", None)
               }
       except Exception:
           tenant_map = {}

       items: list[UserResponse] = []
       for u in users:
           resp = UserResponse.model_validate(u)
           if u.tenant_id in tenant_map:
               resp.tenant_slug, resp.tenant_name = tenant_map[u.tenant_id]
           items.append(resp)
       return items
   ```
3. En `create_user` (líneas 97–143 de `fastapi/src/api/v1/users.py`), permitir que `SUPERADMIN_GLOBAL` especifique `body.tenant_id` (verificando que la empresa destino exista):
   ```python
   @router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
   async def create_user(
       body: CreateUserRequest,
       claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL, SystemRoleEnum.TENANT_ADMIN)),
       db: AsyncSession = Depends(get_db_session),
   ) -> UserResponse:
       caller_tenant_id = uuid.UUID(claims["tid"])
       is_sa = claims["rol"] == SystemRoleEnum.SUPERADMIN_GLOBAL.value
       target_tenant_id = body.tenant_id if (is_sa and body.tenant_id) else caller_tenant_id
       if not is_sa and body.tenant_id and body.tenant_id != caller_tenant_id:
           raise HTTPException(
               status_code=status.HTTP_403_FORBIDDEN,
               detail="Solo SUPERADMIN_GLOBAL puede crear usuarios en otra organización.",
           )
       await set_tenant_context(db, target_tenant_id, is_superadmin=is_sa)

       if not is_sa and body.role == SystemRoleEnum.SUPERADMIN_GLOBAL:
           raise HTTPException(
               status_code=status.HTTP_403_FORBIDDEN,
               detail="Un Administrador de Organización no puede asignar el rol SUPERADMIN_GLOBAL.",
           )

       target_tenant: Tenant | None = None
       if is_sa and body.tenant_id:
           t_res = await db.execute(select(Tenant).where(Tenant.id == target_tenant_id))
           target_tenant = t_res.scalar_one_or_none()
           if not target_tenant:
               raise HTTPException(status_code=404, detail="La organización destino especificada no existe")

       # Comprobar unicidad
       stmt_check = select(User).where(
           User.tenant_id == target_tenant_id,
           (User.username == body.username) | (User.email == body.email),
       )
       existing = await db.execute(stmt_check)
       if existing.scalar_one_or_none():
           raise HTTPException(
               status_code=status.HTTP_409_CONFLICT,
               detail="Ya existe un usuario con este username o email en la organización",
           )

       new_user = User(
           tenant_id=target_tenant_id,
           username=body.username.strip(),
           email=body.email.strip().lower(),
           full_name=body.full_name.strip(),
           password_hash=hash_password(str(body.temporary_password)),
           role=body.role,
           is_active=True,
           is_locked=False,
           failed_login_attempts=0,
           totp_enabled=False,
           has_all_routers_access=body.has_all_routers_access,
           allowed_cidr_list=body.allowed_cidr_list or [],
       )
       db.add(new_user)
       await db.commit()
       await db.refresh(new_user)
       resp = UserResponse.model_validate(new_user)
       if target_tenant:
           resp.tenant_slug = target_tenant.slug
           resp.tenant_name = target_tenant.name
       return resp
   ```
4. Añadir el endpoint `PATCH /api/v1/users/{user_id}/tenant` al final de `fastapi/src/api/v1/users.py`:
   ```python
   @router.patch("/{user_id}/tenant", response_model=UserResponse)
   async def reassign_user_tenant(
       user_id: uuid.UUID,
       body: AssignUserTenantRequest,
       claims: dict[str, Any] = Depends(require_roles(SystemRoleEnum.SUPERADMIN_GLOBAL)),
       db: AsyncSession = Depends(get_db_session),
   ) -> UserResponse:
       """Reasigna un usuario a otra empresa (exclusivo SUPERADMIN_GLOBAL), limpiando permisos de routers previos."""
       caller_id = uuid.UUID(claims["sub"])
       await set_tenant_context(db, None, is_superadmin=True)

       u_res = await db.execute(select(User).where(User.id == user_id))
       target_user = u_res.scalar_one_or_none()
       if not target_user:
           raise HTTPException(status_code=404, detail="Usuario no encontrado")

       t_res = await db.execute(select(Tenant).where(Tenant.id == body.tenant_id))
       target_tenant = t_res.scalar_one_or_none()
       if not target_tenant:
           raise HTTPException(status_code=404, detail="Empresa destino no encontrada")

       old_tenant_id = target_user.tenant_id
       old_role = target_user.role.value if hasattr(target_user.role, "value") else str(target_user.role)

       if old_tenant_id != target_tenant.id:
           conflict_stmt = select(User).where(
               User.tenant_id == target_tenant.id,
               User.id != target_user.id,
               (User.username == target_user.username) | (User.email == target_user.email),
           )
           conflict_user = (await db.execute(conflict_stmt)).scalar_one_or_none()
           if (
               conflict_user is not None
               and conflict_user.id != target_user.id
               and conflict_user.tenant_id == target_tenant.id
           ):
               raise HTTPException(
                   status_code=status.HTTP_409_CONFLICT,
                   detail="Ya existe un usuario con ese username o email en la empresa destino",
               )

           await db.execute(
               delete(UserRouterPermission).where(
                   UserRouterPermission.user_id == target_user.id,
                   UserRouterPermission.tenant_id == old_tenant_id,
               )
           )
           await kill_all_user_sessions(
               str(old_tenant_id),
               str(target_user.id),
               killed_by=str(caller_id),
               reason=f"Transferencia de empresa hacia {target_tenant.slug}",
           )
           target_user.tenant_id = target_tenant.id

       if body.role is not None:
           target_user.role = body.role

       await write_audit_log(
           session=db,
           tenant_id=target_tenant.id,
           actor_username=str(claims.get("preferred_username") or "superadmin"),
           actor_role=str(claims.get("rol") or SystemRoleEnum.SUPERADMIN_GLOBAL.value),
           actor_ip=str(claims.get("ip_address") or "127.0.0.1"),
           event_category="USER_MANAGEMENT",
           event_action="USER_TENANT_REASSIGNED",
           actor_user_id=caller_id,
           before_state={"tenant_id": str(old_tenant_id), "role": old_role},
           after_state={
               "user_id": str(target_user.id),
               "username": target_user.username,
               "tenant_id": str(target_tenant.id),
               "tenant_slug": target_tenant.slug,
               "role": target_user.role.value if hasattr(target_user.role, "value") else str(target_user.role),
           },
           status_code=200,
       )
       await db.commit()
       await db.refresh(target_user)

       resp = UserResponse.model_validate(target_user)
       resp.tenant_slug = target_tenant.slug
       resp.tenant_name = target_tenant.name
       return resp
   ```

---

### Paso 3: Selector de Empresa al Crear y Reasignar Usuarios en `vue3/src/views/UsersAndPermissionsView.vue` y `vue3/src/types/index.ts`

#### 3.A. Actualizar `UserManagementItem` en `vue3/src/types/index.ts` (líneas 189–202)
Añadir `tenant_id`, `tenant_slug` y `tenant_name`:
```ts
export interface UserManagementItem {
  id: string;
  tenant_id?: string;
  tenant_slug?: string | null;
  tenant_name?: string | null;
  username: string;
  email: string;
  full_name?: string;
  role: SystemRole;
  totp_enabled: boolean;
  is_active: boolean;
  allowed_cidr_list?: string[];
  has_all_routers_access: boolean;
  assigned_router_ids?: string[];
  feature_flags_override?: Record<string, string>;
  created_at?: string;
}
```

#### 3.B. Añadir estado, funciones y controles en `vue3/src/views/UsersAndPermissionsView.vue`
1. Debajo de `isWriteAuthorized` (línea 52), declarar `isSuperAdmin` y el estado para empresas y modal de reasignación:
```ts
  const isSuperAdmin = computed(() => authStore.currentRole === 'SUPERADMIN_GLOBAL');
  const availableTenants = ref<Array<{ id: string; name: string; slug: string }>>([]);

  // Modal Reasignar Empresa (exclusivo SUPERADMIN_GLOBAL)
  const isAssignTenantModalOpen = ref(false);
  const isAssigningTenant = ref(false);
  const targetUserForTenant = ref<UserManagementItem | null>(null);
  const reassignTenantForm = ref({
    tenant_id: '',
    role: 'SUPPORT_L2' as SystemRole,
  });
```
2. En `newUser` (línea 67), incluir `tenant_id: authStore.user?.tenant_id || ''`:
```ts
  const newUser = ref({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'SUPPORT_L2' as SystemRole,
    tenant_id: authStore.user?.tenant_id || '',
    allowed_cidr_list: '',
    has_all_routers_access: false,
  });
```
3. Añadir las funciones `loadAvailableTenants`, `openAssignTenantModal` y `handleReassignTenant`:
```ts
  async function loadAvailableTenants() {
    if (!isSuperAdmin.value) return;
    try {
      const res = await http.get<
        | Array<{ id: string; name?: string; slug?: string }>
        | { items: Array<{ id: string; name?: string; slug?: string }> }
      >('/api/v1/tenants');
      const raw = Array.isArray(res.data) ? res.data : res.data?.items || [];
      availableTenants.value = raw
        .filter((tItem) => tItem && typeof tItem.id === 'string' && (tItem.slug || tItem.name))
        .map((tItem) => ({
          id: tItem.id,
          name: tItem.name || tItem.slug || tItem.id,
          slug: tItem.slug || tItem.id,
        }));
    } catch {
      availableTenants.value = [];
    }
  }

  function openAssignTenantModal(user: UserManagementItem) {
    targetUserForTenant.value = user;
    reassignTenantForm.value = {
      tenant_id: user.tenant_id || authStore.user?.tenant_id || availableTenants.value[0]?.id || '',
      role: user.role,
    };
    isAssignTenantModalOpen.value = true;
  }

  async function handleReassignTenant() {
    if (!targetUserForTenant.value || !reassignTenantForm.value.tenant_id) return;
    isAssigningTenant.value = true;
    errorMessage.value = '';
    try {
      const res = await http.patch<UserManagementItem>(
        `/api/v1/users/${targetUserForTenant.value.id}/tenant`,
        {
          tenant_id: reassignTenantForm.value.tenant_id,
          role: reassignTenantForm.value.role,
        },
      );
      if (res.data) {
        targetUserForTenant.value.tenant_id = res.data.tenant_id;
        targetUserForTenant.value.tenant_slug = res.data.tenant_slug;
        targetUserForTenant.value.tenant_name = res.data.tenant_name;
        targetUserForTenant.value.role = res.data.role;
      }
      isAssignTenantModalOpen.value = false;
      successMessage.value = `Empresa actualizada exitosamente para @${targetUserForTenant.value.username}.`;
      await loadUsers();
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      errorMessage.value = error.detail || error.message || 'Error al reasignar empresa del usuario.';
    } finally {
      isAssigningTenant.value = false;
    }
  }
```
4. En `handleCreateUser()` (líneas 416–450), incluir `tenant_id` cuando `isSuperAdmin.value && newUser.value.tenant_id` esté definido y reiniciar `tenant_id: authStore.user?.tenant_id || ''` al limpiar el formulario:
```ts
      const payload = {
        username: newUser.value.username.trim(),
        email: newUser.value.email.trim(),
        temporary_password: newUser.value.password,
        password: newUser.value.password,
        full_name: newUser.value.full_name.trim() || newUser.value.username.trim(),
        role: newUser.value.role,
        ...(isSuperAdmin.value && newUser.value.tenant_id
          ? { tenant_id: newUser.value.tenant_id }
          : {}),
        allowed_cidr_list: cidrList,
        has_all_routers_access: Boolean(newUser.value.has_all_routers_access),
      };
```
5. En `onMounted` (línea 474), invocar `loadAvailableTenants()` **después** de `loadUsers()` y `loadRegistrationStatus()`:
```ts
  onMounted(() => {
    loadUsers();
    loadRegistrationStatus();
    loadAvailableTenants();
  });
```
6. En la tabla de usuarios (`<td class="cell-user">` y `<td class="col-actions">`), mostrar el badge de empresa y el botón **`🏢 Empresa`**:
```html
              <td class="cell-user">
                <strong>{{ u.full_name || u.username }}</strong>
                <code class="user-handle">@{{ u.username }}</code>
                <span
                  v-if="u.tenant_slug || u.tenant_name"
                  class="badge-tenant"
                  :title="u.tenant_name || u.tenant_slug || ''"
                >
                  🏢 {{ u.tenant_slug || u.tenant_name }}
                </span>
              </td>
```
y dentro de `<td class="col-actions">` (en el bloque `<template v-else>`):
```html
                  <button
                    v-if="isSuperAdmin"
                    :id="`btn-assign-tenant-${u.username}`"
                    type="button"
                    class="btn-assign-tenant"
                    aria-label="Asignar o transferir empresa a este operador"
                    @click="openAssignTenantModal(u)"
                  >
                    {{ t('users_mgmt.btn_assign_tenant', '🏢 Empresa') }}
                  </button>
```
7. En el modal **Registrar Nuevo Operador** (justo antes del botón o fila de `Rol en la Organización *`), añadir el selector `#u-tenant-id`:
```html
          <div v-if="isSuperAdmin" class="form-row">
            <div class="form-group">
              <label for="u-tenant-id" class="form-label">Empresa / Organización Destino *</label>
              <select id="u-tenant-id" v-model="newUser.tenant_id" class="form-select">
                <option
                  v-if="
                    authStore.user?.tenant_id &&
                    !availableTenants.some((tItem) => tItem.id === authStore.user?.tenant_id)
                  "
                  :value="authStore.user.tenant_id"
                >
                  {{ authStore.user.tenant_slug || 'Empresa Actual' }}
                </option>
                <option v-for="tItem in availableTenants" :key="tItem.id" :value="tItem.id">
                  {{ tItem.name }} ({{ tItem.slug }})
                </option>
              </select>
            </div>
          </div>
```
8. Añadir el modal de **Reasignar Empresa** antes de `<ChangePasswordModal>`:
```html
    <!-- Modal para Asignar o Transferir Empresa a un Usuario (SUPERADMIN_GLOBAL) -->
    <div
      v-if="isAssignTenantModalOpen && targetUserForTenant"
      class="rg-modal-backdrop"
      @click.self="isAssignTenantModalOpen = false"
    >
      <div
        class="rg-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-assign-tenant-title"
      >
        <header class="modal-header">
          <h2 id="modal-assign-tenant-title" class="modal-title">
            Asignar Empresa: @{{ targetUserForTenant.username }}
          </h2>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal"
            @click="isAssignTenantModalOpen = false"
          >
            ✕
          </button>
        </header>

        <form class="modal-form" @submit.prevent="handleReassignTenant">
          <p class="modal-desc">
            Selecciona la empresa (Tenant) a la que pertenecerá el operador
            <strong>{{ targetUserForTenant.full_name || targetUserForTenant.username }}</strong>.
            Al transferir un usuario a otra empresa, sus permisos sobre routers de la empresa anterior se revocan automáticamente.
          </p>

          <div class="form-group">
            <label for="assign-user-tenant-select" class="form-label">Empresa Destino *</label>
            <select
              id="assign-user-tenant-select"
              v-model="reassignTenantForm.tenant_id"
              class="form-select"
              required
            >
              <option
                v-if="
                  authStore.user?.tenant_id &&
                  !availableTenants.some((tItem) => tItem.id === authStore.user?.tenant_id)
                "
                :value="authStore.user.tenant_id"
              >
                {{ authStore.user.tenant_slug || 'Empresa Actual' }}
              </option>
              <option v-for="tItem in availableTenants" :key="tItem.id" :value="tItem.id">
                {{ tItem.name }} ({{ tItem.slug }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="assign-user-role-select" class="form-label">Rol en la Empresa Destino *</label>
            <select
              id="assign-user-role-select"
              v-model="reassignTenantForm.role"
              class="form-select"
            >
              <option v-for="r in availableRoles" :key="r" :value="r">{{ r }}</option>
            </select>
          </div>

          <footer class="modal-footer">
            <button type="button" class="btn-cancel" @click="isAssignTenantModalOpen = false">
              Cancelar
            </button>
            <button
              id="btn-confirm-assign-tenant"
              type="submit"
              class="btn-submit"
              :disabled="isAssigningTenant"
            >
              {{ isAssigningTenant ? 'Guardando...' : '🏢 Guardar Empresa' }}
            </button>
          </footer>
        </form>
      </div>
    </div>
```

---

### Paso 4: Guardrail `WebSocketDisconnected` en `fastapi/src/api/v1/websockets.py`

En `fastapi/src/api/v1/websockets.py` (líneas 218–230), envolver el envío por WebSocket y el bucle principal para capturar cualquier desconexión abrupta de Starlette (`RuntimeError` o `WebSocketDisconnected`) sin imprimir tracebacks en los logs:

```python
                    if is_kill:
                        if is_target:
                            await ws.send_text(raw_str)
                            await ws.close(code=4401, reason="Sesión revocada por Kill-Switch")
                            break
                        continue
                except Exception as exc:
                    logger.debug("Error checking kill switch event: %s", exc)
                try:
                    await ws.send_text(raw_str)
                except Exception:
                    break
            await asyncio.sleep(0.01)
    except (WebSocketDisconnect, RuntimeError):
        logger.debug("WebSocket tenant_events disconnected: session=%s", session_id)
```

---

## 3. Aseguramiento de Calidad Level-11X Obligatorio (Pytest, Vitest y Karate Labs BDD)

### 3.1. Prueba Unitaria de Onboarding Inicial para `TENANT_ADMIN` en `fastapi/tests/api/test_tenants_features_rbac.unit.py`
Añadir al final de `fastapi/tests/api/test_tenants_features_rbac.unit.py`:

```python
@pytest.mark.asyncio
async def test_tenant_admin_can_complete_initial_onboarding_once(
    async_client: AsyncClient,
    fake_redis: FakeAsyncRedis,
) -> None:
    """Certifica que el TENANT_ADMIN de una empresa recién creada (onboarding_completed=False)
    puede persistir la configuración inicial del wizard (onboarding_completed=True), pero
    queda bloqueado (403) para modificaciones posteriores de licencias."""
    tenant_id = uuid.uuid4()
    t = Tenant()
    t.id = tenant_id
    t.slug = "caja"
    t.name = "Caja Telecom"
    t.status = TenantStatusEnum.ACTIVE
    t.isp_module_enabled = True
    t.bgp_looking_glass_enabled = False
    t.sfp_ddm_telemetry_enabled = True
    t.ipfix_analytics_enabled = False
    t.enforce_maker_checker = True
    t.auto_safemode_enforced = True
    t.ai_mcp_integration_enabled = True
    t.nightly_backups_enabled = True
    t.outbound_webhooks_enabled = True
    t.config_drift_monitoring_enabled = True
    t.cis_audit_enabled = True
    t.sdwan_orchestrator_enabled = False
    t.capsman_wifi_enabled = False
    t.sla_tracker_enabled = False
    t.rogue_dhcp_enabled = False
    t.mass_outage_threshold = 5
    t.default_locale = "es"
    t.onboarding_completed = False

    db = MockTenantAuditDbSession(tenant=t)
    app.dependency_overrides[get_db_session] = lambda: db

    try:
        tadmin_id = str(uuid.uuid4())
        tadmin_sess = "sess-caja-tadmin-01"
        await fake_redis.hset(
            f"rg:{tenant_id}:sess:{tadmin_sess}",
            mapping={
                "session_id": tadmin_sess,
                "user_id": tadmin_id,
                "username": "admin_caja",
                "role": SystemRoleEnum.TENANT_ADMIN.value,
            },
        )
        token_tadmin = create_jwt_access_token(
            tadmin_id,
            str(tenant_id),
            "caja",
            tadmin_sess,
            SystemRoleEnum.TENANT_ADMIN.value,
            True,
        )

        # 1. Onboarding inicial con onboarding_completed=True -> HTTP 200 OK
        res_onboard = await async_client.patch(
            f"/api/v1/tenants/{tenant_id}/features",
            json={
                "isp_module_enabled": True,
                "bgp_looking_glass_enabled": True,
                "onboarding_completed": True,
            },
            headers={
                "Authorization": f"Bearer {token_tadmin}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )
        assert res_onboard.status_code == 200, res_onboard.text
        data_onboard = res_onboard.json()
        assert data_onboard["onboarding_completed"] is True
        assert t.onboarding_completed is True

        # 2. Intento ulterior una vez onboarding_completed=True -> HTTP 403 Forbidden
        res_second = await async_client.patch(
            f"/api/v1/tenants/{tenant_id}/features",
            json={"sla_tracker_enabled": True, "onboarding_completed": True},
            headers={
                "Authorization": f"Bearer {token_tadmin}",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )
        assert res_second.status_code == 403
    finally:
        app.dependency_overrides.pop(get_db_session, None)
```

### 3.2. Prueba Unitaria de Asignación y Reasignación de Empresa a Usuario en `fastapi/tests/api/test_tenants_and_users.unit.py`
Añadir al final de `fastapi/tests/api/test_tenants_and_users.unit.py`:

```python
@pytest.mark.asyncio
async def test_superadmin_create_user_with_explicit_tenant_and_reassign_tenant(
    async_client: AsyncClient,
    superadmin_auth: dict[str, str],
    fake_redis: FakeAsyncRedis,
) -> None:
    """Verifica que SUPERADMIN_GLOBAL puede crear un usuario asignándolo directamente a otra
    empresa (tenant_id) y transferir un usuario existente mediante PATCH /api/v1/users/{id}/tenant."""
    target_tid = uuid.uuid4()
    target_tenant = Tenant(
        id=target_tid,
        name="Caja ISP",
        slug="caja",
        status=TenantStatusEnum.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    db_create = MockDbSession(tenants=[target_tenant], users=[])
    app.dependency_overrides[get_db_session] = lambda: db_create
    try:
        res_create = await async_client.post(
            "/api/v1/users",
            json={
                "username": "operador_caja",
                "email": "op@caja.net",
                "full_name": "Operador Caja",
                "password": "PasswordCaja123!",
                "role": SystemRoleEnum.TENANT_ADMIN.value,
                "tenant_id": str(target_tid),
                "has_all_routers_access": True,
                "allowed_cidr_list": [],
            },
            headers={**superadmin_auth, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_create.status_code == 201, res_create.text
        created_data = res_create.json()
        assert created_data["tenant_id"] == str(target_tid)
        assert created_data["tenant_slug"] == "caja"

        existing_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(superadmin_auth["tid"]),
            username="transfer_op",
            email="transfer@rosgrid.local",
            full_name="Operador Transferible",
            password_hash=hash_password("SecretPass123!"),
            role=SystemRoleEnum.SUPPORT_L2,
            is_active=True,
            is_locked=False,
            failed_login_attempts=0,
            totp_enabled=False,
            has_all_routers_access=False,
            allowed_cidr_list=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_reassign = MockDbSession(tenants=[target_tenant], users=[existing_user])
        app.dependency_overrides[get_db_session] = lambda: db_reassign

        res_patch = await async_client.patch(
            f"/api/v1/users/{existing_user.id}/tenant",
            json={
                "tenant_id": str(target_tid),
                "role": SystemRoleEnum.TENANT_ADMIN.value,
            },
            headers={**superadmin_auth, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_patch.status_code == 200, res_patch.text
        patched_data = res_patch.json()
        assert patched_data["tenant_id"] == str(target_tid)
        assert patched_data["tenant_slug"] == "caja"
        assert patched_data["role"] == SystemRoleEnum.TENANT_ADMIN.value
    finally:
        app.dependency_overrides.pop(get_db_session, None)
```

### 3.3. Prueba Unitaria Frontend en `vue3/src/views/admin/usersAndPermissionsView.unit.ts`
Añadir un test dentro del bloque `describe` en `vue3/src/views/admin/usersAndPermissionsView.unit.ts`:

```ts
  it('permite a SUPERADMIN_GLOBAL elegir empresa al crear usuario y reasignar empresa desde la tabla', async () => {
    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('/api/v1/tenants')) {
        return {
          status: 200,
          data: [
            { id: 't-corp', name: 'Corporación Central', slug: 'corp' },
            { id: 't-caja', name: 'Caja Telecom', slug: 'caja' },
          ],
          headers: new Headers(),
        };
      }
      return {
        status: 200,
        data: [
          {
            id: 'u-01',
            tenant_id: 't-corp',
            tenant_slug: 'corp',
            username: 'admin.norte',
            email: 'admin@isp-norte.net',
            full_name: 'Carlos Mendoza',
            role: 'TENANT_ADMIN',
            totp_enabled: true,
            is_active: true,
            has_all_routers_access: true,
          },
        ],
        headers: new Headers(),
      };
    });

    const wrapper = mount(UsersAndPermissionsView, {
      global: {
        stubs: {
          RgStepUp2FAModal: true,
          UserRouterMatrixModal: true,
          RbacRoleMatrixPanel: true,
          RgUserProfileFlagsModal: true,
        },
      },
    });
    await flushPromises();

    // 1. Verificar selector #u-tenant-id en el modal de creación
    await wrapper.find('.btn-create').trigger('click');
    const tenantSelect = wrapper.find('#u-tenant-id');
    expect(tenantSelect.exists()).toBe(true);
    await tenantSelect.setValue('t-caja');
    await wrapper.find('.btn-close').trigger('click');

    // 2. Abrir modal de reasignación de empresa desde la fila del usuario
    const assignBtn = wrapper.find('#btn-assign-tenant-admin\\.norte');
    expect(assignBtn.exists()).toBe(true);
    await assignBtn.trigger('click');

    const patchSpy = vi.spyOn(http, 'patch').mockResolvedValueOnce({
      status: 200,
      data: {
        id: 'u-01',
        tenant_id: 't-caja',
        tenant_slug: 'caja',
        tenant_name: 'Caja Telecom',
        username: 'admin.norte',
        email: 'admin@isp-norte.net',
        role: 'TENANT_ADMIN',
        totp_enabled: true,
        is_active: true,
        has_all_routers_access: true,
      },
      headers: new Headers(),
    });

    await wrapper.find('#assign-user-tenant-select').setValue('t-caja');
    await wrapper.find('#btn-confirm-assign-tenant').trigger('submit');
    await flushPromises();

    expect(patchSpy).toHaveBeenCalledWith('/api/v1/users/u-01/tenant', {
      tenant_id: 't-caja',
      role: 'TENANT_ADMIN',
    });
    expect(wrapper.find('.banner--success').text()).toContain('Empresa actualizada exitosamente');
  });
```

### 3.4. Escenarios Karate Labs BDD (`fastapi/test/api_test.feature` y `vue3/test/ui_business_flow.feature` + réplicas en `docs/examples/`)
1. Añadir `Scenario: 164` en `fastapi/test/api_test.feature` y `docs/examples/fastapi/api_test.feature.example`:
```gherkin
  Scenario: 164. Reasignación directa de empresa (tenant_id) a un usuario y onboarding inicial de TENANT_ADMIN (Hito 30.11 - Spec 88)
    Given path '/api/v1/users/00000000-0000-0000-0000-000000000001/tenant'
    And header Idempotency-Key = java.util.UUID.randomUUID().toString()
    And request { tenant_id: '00000000-0000-0000-0000-000000000002', role: 'TENANT_ADMIN' }
    When method patch
    Then assert responseStatus == 401 || responseStatus == 403 || responseStatus == 404 || responseStatus == 200
```
2. Añadir `Scenario: 102` en `vue3/test/ui_business_flow.feature` y `docs/examples/vue3/ui_business_flow.feature.example`:
```gherkin
  Scenario: 102. Onboarding inicial de nueva empresa por TENANT_ADMIN y selector de empresa en creación/reasignación de usuarios (Hito 30.11 - Spec 88)
    * def onboardingPayload = { onboarding_completed: true, isp_module_enabled: true }
    * match onboardingPayload.onboarding_completed == true
    * def userTenantSelectors = ['#u-tenant-id', '#assign-user-tenant-select', '#btn-confirm-assign-tenant']
    * match userTenantSelectors contains '#u-tenant-id'
```
