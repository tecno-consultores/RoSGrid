# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

# Especificación 62: Aislamiento de Destinatario en Kill-Switch de Sesiones (`SESSION_KILLED`) — Prevención de Cierre Colateral de Sesión del SuperAdmin en WebSocket y Pinia (Hito 28.7)

**Estado:** ✅ Completado y Certificado al 100% en Hito 28  
**Hito Asociado:** Hito 28.7 (`ROADMAP.md`)  
**Fecha de Certificación:** Noviembre 2026  
**Módulos Afectados:**
- `fastapi/src/redis_layer/sessions.py`
- `fastapi/src/api/v1/websockets.py`
- `vue3/src/stores/useNocEventsStore.ts`
- `fastapi/tests/api/test_websockets_and_workers.unit.py`
- `vue3/src/stores/useNocEventsStore.unit.ts`

---

## 1. Diagnóstico Causa Raíz (Hallazgo UAT al Expulsar a un Usuario)

Durante las pruebas manuales con dos navegadores abiertos simultáneamente (uno con el **SuperAdmin** y otro con un operador del mismo tenant), al expulsar al operador desde **Sesiones Activas y Kill-Switch**, se cerraba tanto la sesión del usuario expulsado como la sesión del propio SuperAdmin.

### Cadena de 3 Defectos Causantes

1. **Inconsistencia de Esquema en el Evento Pub/Sub (`fastapi/src/redis_layer/sessions.py` vs. `fastapi/src/api/v1/websockets.py`):**
   - `kill_session` (`sessions.py`, líneas 118–127) publica en `rg:pubsub:events:{tenant_id}` un JSON plano con `"event": "SESSION_KILLED"`, `"target_session_id"` y `"target_user_id"` en la raíz.
   - Sin embargo, `_handle_telemetry_msg` y `tenant_events_ws` (`websockets.py`, líneas 113–117 y 200–204) buscaban `ev.get("event_name") == "SESSION_KILLED"` y `ev.get("payload", {}).get("target_session_id")`. Al no coincidir el nombre de la clave (`"event"` vs `"event_name"`), el filtro del backend jamás se activaba.
2. **Difusión Indiscriminada (`await ws.send_text(raw_str)`) a Todos los WebSockets del Tenant (`fastapi/src/api/v1/websockets.py`, línea 207):**
   - En `tenant_events_ws`, incluso cuando un evento `SESSION_KILLED` no correspondía al `session_id` / `user_id` del WebSocket actual, el bucle continuaba hacia `await ws.send_text(raw_str)` y enviaba la trama `SESSION_KILLED` a **todos los demás navegadores conectados al tenant** (incluido el navegador del SuperAdmin).
3. **Ejecución Incondicional de `forceKillSwitchLogout` en el Frontend (`vue3/src/stores/useNocEventsStore.ts`, líneas 43–50):**
   - En `handleIncomingEvent` (`useNocEventsStore.ts`), al recibir cualquier trama con `eventName === 'SESSION_KILLED'`, el cliente invocaba `authStore.forceKillSwitchLogout(...)` **sin verificar si `target_session_id` o `target_user_id` coincidían con `authStore.sessionId` o `authStore.user?.id`**.

---

## 2. Solución Arquitectónica de Doble Candado (`Target` / `Replacement`)

### 2.1. Normalización del Payload Pub/Sub en `kill_session` (`fastapi/src/redis_layer/sessions.py`)

Emitir tanto `"event"` como `"event_name"` y el sub-objeto `"payload"` para compatibilidad total entre consumidores legacy y modernos.

#### Bloque `Target` en `fastapi/src/redis_layer/sessions.py` (líneas 117–130):
```python
    if notify_ws:
        event_payload = json.dumps(
            {
                "event": "SESSION_KILLED",
                "target_session_id": session_id,
                "target_user_id": user_id,
                "reason": reason,
                "killed_by": killed_by,
            }
        )
        pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)

    await pipe.execute()
    return True
```

#### Bloque `Replacement` en `fastapi/src/redis_layer/sessions.py`:
```python
    if notify_ws:
        target_info = {
            "target_session_id": session_id,
            "target_user_id": user_id,
            "reason": reason,
            "killed_by": killed_by,
        }
        event_payload = json.dumps(
            {
                "event": "SESSION_KILLED",
                "event_name": "SESSION_KILLED",
                **target_info,
                "payload": target_info,
            }
        )
        pipe.publish(f"rg:pubsub:events:{tenant_id}", event_payload)

    await pipe.execute()
    return True
```

---

### 2.2. Aislamiento Estricto por Sesión en el Multiplexor WebSocket (`fastapi/src/api/v1/websockets.py`)

Crear el helper determinista `_classify_session_kill_event(ev: dict[str, Any], sid: str, uid: str) -> tuple[bool, bool]` (Complejidad Ciclomática Radon Grado A) y asegurar que `tenant_events_ws` **nunca** reenvíe eventos `SESSION_KILLED` a sesiones de otros operadores (`if is_kill and not is_target: continue`).

#### Primer Bloque `Target` en `fastapi/src/api/v1/websockets.py` (líneas 109–124):
```python
async def _handle_telemetry_msg(ws: WebSocket, channel: str, raw_data: str, sid: str, uid: str) -> bool:
    if "events" in channel:
        try:
            event = json.loads(raw_data)
            if event.get("event_name") == "SESSION_KILLED":
                p = event.get("payload", {})
                if p.get("target_session_id") == sid or p.get("target_user_id") == uid:
                    await ws.close(code=4401, reason="Sesión revocada por Kill-Switch")
                    return False
        except Exception as exc:
            logger.debug("Error processing telemetry websocket event: %s", exc)
        return True

    await ws.send_text(raw_data)
    return True
```

#### Primer Bloque `Replacement` en `fastapi/src/api/v1/websockets.py`:
```python
def _classify_session_kill_event(ev: dict[str, Any], sid: str, uid: str) -> tuple[bool, bool]:
    """Determina si el evento es SESSION_KILLED y si aplica exactamente a la sesión/usuario actual."""
    ev_name = ev.get("event_name") or ev.get("event")
    if ev_name != "SESSION_KILLED":
        return False, False
    p = ev.get("payload") if isinstance(ev.get("payload"), dict) else ev
    if p.get("killed_by") == "SUPERADMIN_TENANT_SWITCH":
        return True, False
    target_sid = p.get("target_session_id")
    if target_sid:
        return True, str(target_sid) == str(sid)
    target_uid = p.get("target_user_id")
    if target_uid:
        return True, str(target_uid) == str(uid)
    return True, False


async def _handle_telemetry_msg(ws: WebSocket, channel: str, raw_data: str, sid: str, uid: str) -> bool:
    if "events" in channel:
        try:
            event = json.loads(raw_data)
            is_kill, is_target = _classify_session_kill_event(event, sid, uid)
            if is_kill and is_target:
                await ws.close(code=4401, reason="Sesión revocada por Kill-Switch")
                return False
        except Exception as exc:
            logger.debug("Error processing telemetry websocket event: %s", exc)
        return True

    await ws.send_text(raw_data)
    return True
```

#### Segundo Bloque `Target` en `fastapi/src/api/v1/websockets.py` (líneas 193–209):
```python
    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("data"):
                raw_str = msg["data"] if isinstance(msg["data"], str) else msg["data"].decode("utf-8")
                try:
                    ev = json.loads(raw_str)
                    if ev.get("event_name") == "SESSION_KILLED":
                        p = ev.get("payload", {})
                        if p.get("target_session_id") == session_id or p.get("target_user_id") == user_id:
                            await ws.close(code=4401, reason="Sesión revocada por Kill-Switch")
                            break
                except Exception as exc:
                    logger.debug("Error checking kill switch event: %s", exc)
                await ws.send_text(raw_str)
            await asyncio.sleep(0.01)
```

#### Segundo Bloque `Replacement` en `fastapi/src/api/v1/websockets.py`:
```python
    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("data"):
                raw_str = msg["data"] if isinstance(msg["data"], str) else msg["data"].decode("utf-8")
                try:
                    ev = json.loads(raw_str)
                    is_kill, is_target = _classify_session_kill_event(ev, session_id, user_id)
                    if is_kill:
                        if is_target:
                            await ws.send_text(raw_str)
                            await ws.close(code=4401, reason="Sesión revocada por Kill-Switch")
                            break
                        continue
                except Exception as exc:
                    logger.debug("Error checking kill switch event: %s", exc)
                await ws.send_text(raw_str)
            await asyncio.sleep(0.01)
```

---

### 2.3. Candado de Verificación de Destinatario en Pinia (`vue3/src/stores/useNocEventsStore.ts`)

En `useNocEventsStore.ts`, verificar que `target_session_id` o `target_user_id` coincidan con la sesión (`authStore.sessionId`) o el usuario (`authStore.user?.id`) activo en ese navegador antes de ejecutar `forceKillSwitchLogout`. Si el evento pertenece a otra sesión o usuario, ignorar el cierre forzado.

#### Bloque `Target` en `vue3/src/stores/useNocEventsStore.ts` (líneas 42–51):
```typescript
      // Intercepción del Kill-Switch en vivo
      if (eventName === 'SESSION_KILLED') {
        if (payload?.killed_by === 'SUPERADMIN_TENANT_SWITCH') {
          return;
        }
        const authStore = useAuthStore();
        authStore.forceKillSwitchLogout(payload?.reason || 'Sesión finalizada por el Administrador');
        return;
      }
```

#### Bloque `Replacement` en `vue3/src/stores/useNocEventsStore.ts`:
```typescript
      // Intercepción del Kill-Switch en vivo (solo si aplica a la sesión/usuario actual)
      if (eventName === 'SESSION_KILLED') {
        const p = payload?.payload && typeof payload.payload === 'object' ? payload.payload : payload;
        if (p?.killed_by === 'SUPERADMIN_TENANT_SWITCH' || payload?.killed_by === 'SUPERADMIN_TENANT_SWITCH') {
          return;
        }
        const authStore = useAuthStore();
        const targetSid = p?.target_session_id || payload?.target_session_id;
        const targetUid = p?.target_user_id || payload?.target_user_id;

        if (targetSid && authStore.sessionId && String(targetSid) !== String(authStore.sessionId)) {
          return;
        }
        if (
          !targetSid &&
          targetUid &&
          authStore.user?.id &&
          String(targetUid) !== String(authStore.user.id)
        ) {
          return;
        }
        if (
          targetSid &&
          !authStore.sessionId &&
          targetUid &&
          authStore.user?.id &&
          String(targetUid) !== String(authStore.user.id)
        ) {
          return;
        }

        authStore.forceKillSwitchLogout(
          p?.reason || payload?.reason || 'Sesión finalizada por el Administrador',
        );
        return;
      }
```

---

## 3. Pruebas Unitarias e Invariantes 11X (`Target` / `Replacement`)

### 3.1. Pruebas Unitarias Backend (`fastapi/tests/api/test_websockets_and_workers.unit.py`)

Verificar que `_handle_telemetry_msg` y `_classify_session_kill_event` cierran el WebSocket cuando `target_session_id` coincide con la sesión actual (tanto en formato raíz `"event"` como anidado `"event_name"`/`"payload"`), pero mantienen intacta la conexión cuando `target_session_id` pertenece a otro usuario.

#### Bloque `Target` en `fastapi/tests/api/test_websockets_and_workers.unit.py` (líneas 154–165):
```python
    # Kill switch event matching current session
    kill_ev = json.dumps(
        {
            "event_name": "SESSION_KILLED",
            "payload": {"target_session_id": "sid1", "target_user_id": "uid1"},
        }
    )
    ws_kill = AsyncMock()
    keep_kill = await _handle_telemetry_msg(ws_kill, "rg:pubsub:events:1", kill_ev, "sid1", "uid1")
    assert keep_kill is False
    ws_kill.close.assert_awaited_once()
```

#### Bloque `Replacement` en `fastapi/tests/api/test_websockets_and_workers.unit.py`:
```python
    # Kill switch event matching current session
    kill_ev = json.dumps(
        {
            "event_name": "SESSION_KILLED",
            "payload": {"target_session_id": "sid1", "target_user_id": "uid1"},
        }
    )
    ws_kill = AsyncMock()
    keep_kill = await _handle_telemetry_msg(ws_kill, "rg:pubsub:events:1", kill_ev, "sid1", "uid1")
    assert keep_kill is False
    ws_kill.close.assert_awaited_once()

    # Kill switch event for ANOTHER user/session must NOT close SuperAdmin's WebSocket
    other_kill_ev = json.dumps(
        {
            "event": "SESSION_KILLED",
            "target_session_id": "sid-other-operator",
            "target_user_id": "uid-other-operator",
        }
    )
    ws_superadmin = AsyncMock()
    keep_superadmin = await _handle_telemetry_msg(
        ws_superadmin, "rg:pubsub:events:1", other_kill_ev, "sid-superadmin", "uid-superadmin"
    )
    assert keep_superadmin is True
    ws_superadmin.close.assert_not_called()
```

### 3.2. Pruebas Unitarias Frontend (`vue3/src/stores/useNocEventsStore.unit.ts`)

Añadir prueba en `useNocEventsStore.unit.ts` certificando que cuando `authStore` tiene una sesión activa (`sid-superadmin` / `uid-superadmin`) y llega un evento `SESSION_KILLED` dirigido a `sid-operador-expulsado`, **no** se dispara `rosgrid:kill-switch` ni se cierra la sesión del SuperAdmin.

#### Bloque `Target` en `vue3/src/stores/useNocEventsStore.unit.ts` (líneas 188–204):
```typescript
  it('ignora SESSION_KILLED cuando killed_by es SUPERADMIN_TENANT_SWITCH para evitar auto-deslogueo', () => {
    const store = useNocEventsStore();
    const switchPayload = JSON.stringify({
      event_name: 'SESSION_KILLED',
      killed_by: 'SUPERADMIN_TENANT_SWITCH',
      reason: 'Conmutación al tenant fibra-norte',
    });

    const eventSpy = vi.fn();
    window.addEventListener('rosgrid:kill-switch', eventSpy);

    store.handleIncomingEvent(switchPayload);

    expect(eventSpy).not.toHaveBeenCalled();
    window.removeEventListener('rosgrid:kill-switch', eventSpy);
  });
```

#### Bloque `Replacement` en `vue3/src/stores/useNocEventsStore.unit.ts`:
```typescript
  it('ignora SESSION_KILLED cuando killed_by es SUPERADMIN_TENANT_SWITCH para evitar auto-deslogueo', () => {
    const store = useNocEventsStore();
    const switchPayload = JSON.stringify({
      event_name: 'SESSION_KILLED',
      killed_by: 'SUPERADMIN_TENANT_SWITCH',
      reason: 'Conmutación al tenant fibra-norte',
    });

    const eventSpy = vi.fn();
    window.addEventListener('rosgrid:kill-switch', eventSpy);

    store.handleIncomingEvent(switchPayload);

    expect(eventSpy).not.toHaveBeenCalled();
    window.removeEventListener('rosgrid:kill-switch', eventSpy);
  });

  it('ignora SESSION_KILLED dirigido a otro usuario/sesión sin cerrar la sesión del SuperAdmin', async () => {
    const { useAuthStore } = await import('./useAuthStore');
    const authStore = useAuthStore();
    authStore.setAuth(
      {
        id: 'uid-superadmin',
        username: 'sinfallas',
        email: 'admin@rosgrid.local',
        role: 'SUPERADMIN_GLOBAL',
        tenant_id: 'tid-1',
        tenant_slug: 'sistemas',
      },
      'csrf-admin',
      'sid-superadmin',
    );

    const store = useNocEventsStore();
    const otherUserKillPayload = JSON.stringify({
      event: 'SESSION_KILLED',
      event_name: 'SESSION_KILLED',
      target_session_id: 'sid-operador-2',
      target_user_id: 'uid-operador-2',
      reason: 'Revocación manual por el Administrador',
    });

    const eventSpy = vi.fn();
    window.addEventListener('rosgrid:kill-switch', eventSpy);

    store.handleIncomingEvent(otherUserKillPayload);

    expect(eventSpy).not.toHaveBeenCalled();
    expect(authStore.isAuthenticated).toBe(true);
    expect(authStore.sessionId).toBe('sid-superadmin');
    window.removeEventListener('rosgrid:kill-switch', eventSpy);
  });
```
