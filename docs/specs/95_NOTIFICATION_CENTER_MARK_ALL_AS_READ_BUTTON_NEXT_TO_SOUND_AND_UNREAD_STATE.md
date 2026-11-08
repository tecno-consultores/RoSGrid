# Especificación Técnica 95: Botón Explícito «Marcar todo leído» Junto al Control de Avisos Sonoros y Estado Visual de Lectura por Fila en el Centro de Notificaciones (`RgNotificationCenterBell.vue`)

**Estado:** Pendiente de Implementación (`Hito 30.18` en `ROADMAP.md`)
**Componentes Afectados:**
- Diccionarios i18n Frontend:
  - `vue3/src/locales/es.json` (bloque `"notifications"`)
  - `vue3/src/locales/en.json` (bloque `"notifications"`)
- Componente del Centro de Notificaciones:
  - `vue3/src/components/common/RgNotificationCenterBell.vue`
- Pruebas Nivel 11X (Creación y Ejecución Obligatoria):
  - `vue3/src/components/common/RgNotificationCenterBell.unit.ts`
  - `vue3/test/ui_business_flow.feature` y `docs/examples/vue3/ui_business_flow.feature.example` (Escenario Karate Labs BDD 109)

---

## 1. Contexto y Diagnóstico Forense de Causa Raíz

En el **Centro de Notificaciones y Atención Táctica** (`RgNotificationCenterBell.vue`), el operador reporta que no encuentra una opción clara para **marcar todo como leído** y solicita activar dicho botón inmediatamente al lado del botón de avisos sonoros (`🔊` / `🔇`).

### Causas Raíz Identificadas en `RgNotificationCenterBell.vue`
1. **Ubicación y Etiqueta Ambigua en `.notif-header-controls` (`líneas 734–770`):**
   - Actualmente, el orden de botones en `.notif-header-controls` es:
     1. `#btn-notif-toggle-sound` (`🔊` / `🔇`)
     2. `#btn-notif-snooze-30m` (`🕒 30m`)
     3. `#btn-notif-mark-all-read` con el texto abreviado **`✓ Vistas`** (`✓ Seen` en inglés).
   - Al estar separado del botón de sonido por el botón de *Snooze* (`🕒 30m`) y tener la etiqueta `✓ Vistas` (que en español se interpreta como sustantivo «Vistas de pantalla» y no como la acción «Marcar todo como leído»), pasa desapercibido para el operador.
2. **Auto-Marcado Silencioso al Abrir el Popover (`togglePopover`, `líneas 535–542`):**
   - En `togglePopover()`, apenas el usuario abre la campana (`if (isOpen.value)`), el código ejecuta `lastReadIso.value = new Date().toISOString(); savePersistedPrefs();`.
   - Esto provoca que el timestamp de lectura se actualice automáticamente solo con abrir el menú antes de que el usuario haya leído o pulsado el botón de marcar todo como leído.
3. **Ausencia de Estado Visual `isRead` por Fila (`.notif-row--unread` / `.notif-row--read`):**
   - La interfaz `TacticalNotificationItem` no expone un campo `isRead: boolean` ni renderiza un indicador visual de «no leído» (`.notif-row-unread-dot`) en cada fila de `<ul class="notif-list">`. Por ello, al pulsar `#btn-notif-mark-all-read`, las notificaciones informativas y operativas no muestran ningún cambio visual de «no leída» a «leída».

---

## 2. Instrucciones Exactas de Implementación (Paso a Paso para Gemini 3.8 Flash High)

### Paso 1: Actualizar Etiquetas en `vue3/src/locales/es.json` y `vue3/src/locales/en.json`

1. En `vue3/src/locales/es.json` (líneas 52–54, dentro de `"notifications"`):
   Reemplazar:
   ```json
    "mark_all_read": "Marcar avisos como vistos",
    "mark_read_short": "Vistas",
   ```
   por:
   ```json
    "mark_all_read": "Marcar todas las notificaciones como leídas",
    "mark_read_short": "Marcar todo leído",
    "all_marked_read_sr": "Todas las notificaciones han sido marcadas como leídas",
   ```
2. En `vue3/src/locales/en.json` (líneas 52–54, dentro de `"notifications"`):
   Reemplazar:
   ```json
    "mark_all_read": "Mark informational notices as seen",
    "mark_read_short": "Seen",
   ```
   por:
   ```json
    "mark_all_read": "Mark all notifications as read",
    "mark_read_short": "Mark all read",
    "all_marked_read_sr": "All notifications have been marked as read",
   ```

---

### Paso 2: Actualizar `vue3/src/components/common/RgNotificationCenterBell.vue`

#### 2.1. Añadir `isRead: boolean` a `TacticalNotificationItem` y `readKeys` persistido (`líneas 14–125`)
1. En `export interface TacticalNotificationItem`, añadir `isRead?: boolean;`.
2. Junto a `ackedKeys` (`línea 64`), añadir `const readKeys = ref<Set<string>>(new Set());`:
   - En `loadPersistedPrefs()`:
     ```ts
     const rawRead = localStorage.getItem(`${prefix}_read_keys`);
     readKeys.value = rawRead ? new Set(JSON.parse(rawRead)) : new Set();
     ```
   - En `savePersistedPrefs()`:
     ```ts
     localStorage.setItem(
       `${prefix}_read_keys`,
       JSON.stringify(Array.from(readKeys.value).slice(-200)),
     );
     ```
3. Crear un helper `isItemRead(dedupKey: string, timestamp: string): boolean`:
   ```ts
   function isItemRead(dedupKey: string, timestamp: string): boolean {
     if (ackedKeys.value.has(dedupKey) || readKeys.value.has(dedupKey)) {
       return true;
     }
     if (lastReadIso.value && timestamp <= lastReadIso.value) {
       return true;
     }
     return false;
   }
   ```
   Y asignar `isRead: isItemRead(dedupKey, ...)` en `populateApprovalNotifications`, `createRouterNotification` y `createNocEventNotification`.

#### 2.2. Calcular `unreadTotalCount`, Evitar el Auto-Marcado al Abrir en `togglePopover()` y Mejorar `markAllInformationalRead()` (`líneas 431–543`)
1. Actualizar `unreadInformationalCount` y añadir `unreadTotalCount`:
   ```ts
   const unreadInformationalCount = computed(() =>
     allNotifications.value.filter((item) => !item.requiresAction && !item.isRead).length,
   );

   const unreadTotalCount = computed(() =>
     allNotifications.value.filter((item) => !item.isRead || (item.requiresAction && !item.approvalId)).length,
   );
   ```
2. En `markAllInformationalRead()` (`líneas 494–504`):
   Marcar todas las notificaciones actuales en `readKeys` (y en `ackedKeys` todas las que no sean aprobaciones Maker-Checker de 4 ojos que requieren firma explícita), actualizar `lastReadIso.value = new Date().toISOString()` y anunciar por `liveAnnouncerText`:
   ```ts
   function markAllInformationalRead(): void {
     lastReadIso.value = new Date().toISOString();
     for (const item of allNotifications.value) {
       readKeys.value.add(item.dedupKey);
       if (!item.approvalId) {
         ackedKeys.value.add(item.dedupKey);
       }
     }
     readKeys.value = new Set(readKeys.value);
     ackedKeys.value = new Set(ackedKeys.value);
     liveAnnouncerText.value = t(
       'notifications.all_marked_read_sr',
       'Todas las notificaciones han sido marcadas como leídas',
     );
     savePersistedPrefs();
     broadcastStateSync();
   }
   ```
3. En `handleSelectNotification(item)` (`líneas 523–533`):
   Añadir `readKeys.value.add(item.dedupKey); readKeys.value = new Set(readKeys.value);` para marcar individualmente la notificación pulsada sin marcar todas las demás como leídas.
4. En `togglePopover()` (`líneas 535–542`):
   No sobrescribir `lastReadIso.value` al abrir el panel (para que las notificaciones no leídas conserven su estado y puedan marcarse con el botón `✓✓ Marcar todo leído`):
   ```ts
   function togglePopover(): void {
     isOpen.value = !isOpen.value;
     if (isOpen.value) {
       fetchPendingApprovalsIfAllowed();
     }
   }
   ```

#### 2.3. Colocar `#btn-notif-mark-all-read` Inmediatamente al Lado de `#btn-notif-toggle-sound` en `.notif-header-controls` (`líneas 734–771`)
Reemplazar el bloque `<div class="notif-header-controls">` por:

```html
        <div class="notif-header-controls">
          <button
            id="btn-notif-toggle-sound"
            type="button"
            class="btn-notif-ctrl"
            :class="{ 'btn-notif-ctrl--active': soundEnabled }"
            :title="
              soundEnabled
                ? t('notifications.sound_on', 'Aviso sonoro activado')
                : t('notifications.sound_off', 'Activar aviso sonoro')
            "
            @click="toggleSound"
          >
            {{ soundEnabled ? '🔊' : '🔇' }}
          </button>

          <button
            id="btn-notif-mark-all-read"
            type="button"
            class="btn-notif-ctrl btn-notif-ctrl--mark-read"
            :class="{ 'btn-notif-ctrl--active': unreadTotalCount > 0 }"
            :title="t('notifications.mark_all_read', 'Marcar todas las notificaciones como leídas')"
            @click="markAllInformationalRead"
          >
            ✓✓ {{ t('notifications.mark_read_short', 'Marcar todo leído') }}
          </button>

          <button
            id="btn-notif-snooze-30m"
            type="button"
            class="btn-notif-ctrl"
            :class="{ 'btn-notif-ctrl--active': isSnoozed }"
            :title="t('notifications.snooze_30m_title', 'Silenciar alertas visuales y sonoras por 30 minutos')"
            @click="toggleSnooze30m"
          >
            {{ isSnoozed ? '🔕 30m' : '🕒 30m' }}
          </button>
        </div>
```

#### 2.4. Mostrar Estado Visual `.notif-row--unread` / `.notif-row--read` y Punto `.notif-row-unread-dot` en Cada Fila (`líneas 833–855`)
En `<li v-for="item in filteredNotifications" ...>`:
```html
        <li
          v-for="item in filteredNotifications"
          :key="item.id"
          class="notif-row"
          :class="{
            'notif-row--action-p1': item.requiresAction && item.priority === 'P1',
            'notif-row--action-p2': item.requiresAction && item.priority === 'P2',
            'notif-row--unread': !item.isRead,
            'notif-row--read': item.isRead && !item.requiresAction,
          }"
          tabindex="0"
          @click="handleSelectNotification(item)"
          @keydown.enter.prevent="handleSelectNotification(item)"
        >
          <div class="notif-row-icon" aria-hidden="true">{{ item.icon }}</div>

          <div class="notif-row-body">
            <div class="notif-row-top">
              <span
                v-if="!item.isRead"
                class="notif-row-unread-dot"
                aria-hidden="true"
              ></span>
              <span class="notif-row-title">{{ item.title }}</span>
```
Y añadir en `<style scoped>`:
```css
  .notif-row--read {
    opacity: 0.72;
  }

  .notif-row-unread-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: var(--rg-accent-cyan, #22d3ee);
    box-shadow: 0 0 6px rgba(34, 211, 238, 0.75);
    flex-shrink: 0;
  }
```

---

## 3. Creación y Ejecución Obligatoria de Pruebas Nivel 11X

### 3.1. Prueba Unitaria en `vue3/src/components/common/RgNotificationCenterBell.unit.ts`
Añadir al final de `vue3/src/components/common/RgNotificationCenterBell.unit.ts` el siguiente caso de prueba verificando:
1. Que `#btn-notif-mark-all-read` (`✓✓ Marcar todo leído` / `✓✓ Mark all read`) está situado inmediatamente al lado de `#btn-notif-toggle-sound` (`🔊`/`🔇`).
2. Que al abrir el popover las notificaciones nuevas aparecen como no leídas (`.notif-row--unread` con `.notif-row-unread-dot`), y al hacer clic en `#btn-notif-mark-all-read` todas pasan a estado leído (`.notif-row--read`), desaparecen los puntos `.notif-row-unread-dot` y se limpia `#notification-bell-dot`:

```ts
  it('posiciona el botón "✓✓ Marcar todo leído" inmediatamente al lado del botón de avisos sonoros y marca todas las notificaciones como leídas al pulsarlo (Hito 30.18 - Spec 95)', async () => {
    vi.mocked(http.get).mockResolvedValue({ data: { items: [] } } as never);
    const { setLocale } = useI18n();
    setLocale('es');

    const nocStore = useNocEventsStore();
    nocStore.recentEvents = [
      {
        id: 'ev-unread-1',
        eventName: 'ROUTER_CONFIG_UPDATED',
        severity: 'INFO',
        message: 'Actualización de reglas NTP',
        router_name: BORDE_CARACAS_NAME,
        routerDisplayName: BORDE_CARACAS_NAME,
        timestampIso: '2026-11-08T10:00:00Z',
      },
    ];

    const wrapper = mount(RgNotificationCenterBell);
    await flushPromises();

    // Punto de avisos informativos no leídos visible en la campana antes de marcar como leído
    expect(wrapper.find('#notification-bell-dot').exists()).toBe(true);

    await wrapper.find(BELL_BTN_ID).trigger('click');
    await flushPromises();

    // Verificar que #btn-notif-mark-all-read está inmediatamente al lado de #btn-notif-toggle-sound
    const headerButtons = wrapper.findAll('.notif-header-controls .btn-notif-ctrl');
    expect(headerButtons.length).toBeGreaterThanOrEqual(3);
    expect(headerButtons[0].attributes('id')).toBe('btn-notif-toggle-sound');
    expect(headerButtons[1].attributes('id')).toBe('btn-notif-mark-all-read');
    expect(headerButtons[1].text()).toContain('✓✓ Marcar todo leído');

    // Al abrir el popover, la fila sigue figurando como no leída (.notif-row--unread)
    expect(wrapper.find('.notif-row--unread').exists()).toBe(true);
    expect(wrapper.find('.notif-row-unread-dot').exists()).toBe(true);

    // Pulsar el botón "✓✓ Marcar todo leído"
    await headerButtons[1].trigger('click');
    await flushPromises();

    expect(wrapper.find('.notif-row--unread').exists()).toBe(false);
    expect(wrapper.find('.notif-row-unread-dot').exists()).toBe(false);
    expect(wrapper.find('.notif-row--read').exists()).toBe(true);
    expect(wrapper.find('#notification-bell-dot').exists()).toBe(false);
  });
```

### 3.2. Escenario Karate Labs BDD (`vue3/test/ui_business_flow.feature` y `docs/examples/vue3/ui_business_flow.feature.example`)
Añadir el **Escenario 109**:

```cucumber
  Scenario: 109. Botón Marcar todo leído junto al botón de avisos sonoros y estado de lectura por fila en el Centro de Notificaciones (Hito 30.18 - Spec 95)
    * def notifMarkAllReadContract = { soundBtn: '#btn-notif-toggle-sound', markAllReadBtn: '#btn-notif-mark-all-read', snoozeBtn: '#btn-notif-snooze-30m', labelEs: 'Marcar todo leído', labelEn: 'Mark all read', unreadRowClass: '.notif-row--unread', readRowClass: '.notif-row--read' }
    * match notifMarkAllReadContract.soundBtn == '#btn-notif-toggle-sound'
    * match notifMarkAllReadContract.markAllReadBtn == '#btn-notif-mark-all-read'
    * match notifMarkAllReadContract.labelEs == 'Marcar todo leído'
    * match notifMarkAllReadContract.labelEn == 'Mark all read'
    * match notifMarkAllReadContract.unreadRowClass == '.notif-row--unread'
    * match notifMarkAllReadContract.readRowClass == '.notif-row--read'
```

---

## 4. Comandos de Verificación (Regla Cero — Docker Efímero)

```bash
# 1. Verificar cero claves JSON duplicadas en locales i18n
python3 .agents/scripts/verify_json_no_duplicate_keys.py

# 2. Ejecutar suite unitaria de RgNotificationCenterBell en contenedor efímero
docker compose -f docker-compose.qa.yml run --rm frontend-test npx vitest run src/components/common/RgNotificationCenterBell.unit.ts

# 3. Verificar tipado estático y linter
docker compose -f docker-compose.qa.yml run --rm frontend-test npm run type-check
docker compose -f docker-compose.qa.yml run --rm frontend-test npm run lint
```
