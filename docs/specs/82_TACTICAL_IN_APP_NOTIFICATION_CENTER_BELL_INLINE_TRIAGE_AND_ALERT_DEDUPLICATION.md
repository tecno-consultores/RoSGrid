# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 82: Centro Táctico de Notificaciones In-App (`RgNotificationCenterBell.vue`), Triaje en Línea 1-Clic, Deduplicación Anti-Fatiga, Separación Visto vs. Resuelto, Alerta en Pestaña y Audio Opcional (`Subhito 30.4`)

> **Hito de Referencia:** Hito 30 (Subhito `30.4`)  
> **Motor de Ejecución Asignado:** Gemini 3.8 Flash (High)  
> **Estado:** Especificación *Flash-Ready* lista para ejecución determinista  
> **Dependencias:** `docs/specs/80_MAINTENANCE_WINDOW_TIMEZONE_ADMIN_STATE_SYNC_AND_NOC_DASHBOARD_VISIBILITY.md` y `docs/specs/81_MAKER_CHECKER_REALTIME_WS_PUSH_AUTO_REFRESH_AND_INBOX_REACTIVITY.md`

---

## 1. Contexto Operativo y Fundamentos de Investigación (Estándares NOC & SaaS B2B)

En un entorno NOC 24/7 o de administración de flotas MikroTik RouterOS v7, depender exclusivamente de notificaciones externas (Telegram, SMTP o Webhook en `alert_dispatcher.py`) deja un punto ciego crítico cuando el operador o supervisor **sí está trabajando dentro de RoSGrid** (ej. configurando Firewall, revisando IPAM o auditando CVEs) o cuando la red de gestión opera en modo *air-gapped* sin salida a Internet.

A partir de la investigación sobre los estándares de la industria en plataformas de observabilidad (**Datadog, Grafana Alerting/OnCall, PagerDuty**) y consolas SaaS B2B de alta densidad (**Linear, GitHub, Cloudflare**), este diseño implementa los **6 pilares de un Centro de Notificaciones NOC de Clase Empresarial**:

1. **Separación Estricta entre "Visto / Leído" (*Read State*) y "Resuelto" (*Action Completion*):**
   - Abrir la campana o pulsar `[ ✓ Marcar vistas ]` limpia la marca de lectura informativa, pero **nunca oculta ni desvanece** los ítems que requieren intervención activa (**Solicitudes Maker-Checker pendientes de firma** o **Routers Caídos `OFFLINE` sin reconocer**). Estos permanecen fijados (*Pinned*) en la sección superior **`📌 Requieren tu Atención`** hasta que sean aprobados, rechazados, reconocidos (`Ack`) o restablecidos.
2. **Triaje en Línea en 1 Clic (*Inline Actions* sin cambiar de pantalla):**
   - Para solicitudes Maker-Checker (`AWAITING_APPROVAL`), el supervisor autorizado (`SUPERADMIN_GLOBAL`, `TENANT_ADMIN`, `SUPERVISOR`, `SUPPORT_L3`, respetando la regla de no auto-aprobación) puede pulsar **`[ ✓ Aprobar ]`** directamente dentro de la fila de la campana (invocando `POST /api/v1/operations/approvals/{id}/approve`) o **`[ 🔍 Revisar ]`** para ir a `/approvals`.
   - Para routers caídos (`OFFLINE`) o con alerta `TOFU SSL`, el operador puede pulsar **`[ 👁️ Ack ]`** (*Reconocer alerta*) para silenciar el pulso de emergencia e indicar que ya está siendo atendida, o hacer clic para navegar directo al equipo.
3. **Filtro Anti-Ruido y Deduplicación Inteligente (*Alert Flattening / Anti-Fatigue*):**
   - **Exclusión de Ruido Administrativo:** Eventos rutinarios de sesión o lecturas (`SESSION_REFRESHED`, `USER_LOGIN`, `USER_LOGOUT`, `TOKEN_RENEWED`) jamás entran a la campana para prevenir la fatiga de alertas (*Alert Fatigue*).
   - **Colapso y Conteo de Repeticiones (`[×N]`):** Si un mismo equipo o acción emite múltiples eventos del mismo tipo en la ventana reciente, se agrupan en una única tarjeta mostrando el badge **`[×N]`** con la marca de tiempo de la ocurrencia más reciente.
4. **Semáforo Inteligente de Insignia en Barra Superior (`RgResponsiveShell.vue`):**
   - **Calma (`0`):** Campana `🔔` neutra sin globo numérico.
   - **Emergencia Crítica (`P1` — Rojo con anillo pulsante):** Hay al menos 1 router `OFFLINE`, alerta `TOFU SSL` o evento `CRITICAL` no reconocido (`!acked`).
   - **Gobernanza / Atención Requerida (`P2` — Ámbar):** Hay solicitudes **Maker-Checker (4 ojos)** pendientes de aprobación o mantenimientos activos.
   - **Informativo No Leído (`P3` — Punto Cian Discreto `•`):** Eventos operativos recientes no vistos que no constituyen una emergencia ni bloquean a otro operador.
5. **Filtrado Estricto por Rol RBAC y Contexto Multi-Tenant (*Zero 403 Dead-Ends*):**
   - Solo los roles con permiso `MAKER_CHECKER_APPROVE` (`authStore.canUseUserFeature('MAKER_CHECKER_APPROVE')`) consultan y visualizan la cola de aprobaciones pendientes.
   - Al conmutar de organización mediante `RgTenantSwitcher` (`rosgrid:tenant-switched`), el centro de notificaciones purga y recarga automáticamente el contexto del nuevo tenant.
6. **Indicador en Título de Pestaña (`document.title`), Audio Sintetizado (`Web Audio API`), Modo No Molestar (`🔕 30m`), Sincronización Multi-Pestaña (`BroadcastChannel`) y Accesibilidad WCAG 2.1 AA:**
   - Prefijo dinámico `(N) 🔔` en `document.title` cuando existen ítems `P1`/`P2` que requieren acción, visible aunque el operador esté en otra pestaña del navegador.
   - Pulso acústico opcional generado con `Web Audio API` (cero archivos externos), con conmutador `🔊 / 🔇` y modo **`🔕 Silenciar 30m`** (*Snooze / Do Not Disturb*) persistidos en `localStorage`.
   - Atajo de teclado global **`Alt + N`**, cierre con `Escape` devolviendo el foco al botón `#btn-notification-bell`, región `aria-live="polite"` para lectores de pantalla y sincronización instantánea entre pestañas vía `BroadcastChannel('rosgrid_notifications_sync')`.

---

## 2. Instrucciones de Implementación Paso a Paso (Flash-Ready)

### Paso 1: Crear el Componente `vue3/src/components/common/RgNotificationCenterBell.vue`

Crear el archivo `vue3/src/components/common/RgNotificationCenterBell.vue` con soporte completo para triaje en línea Maker-Checker, reconocimiento (`Ack`) de caídas, deduplicación `[×N]`, 4 pestañas de filtrado (`all`, `action`, `network`, `ops`), modo *Snooze* de 30 minutos, audio sintetizado Web Audio API y sincronización multi-pestaña:

```vue
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
  import { useRouter } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import { useNocEventsStore } from '@/stores/useNocEventsStore';
  import { useI18n } from '@/composables/useI18n';

  export interface TacticalNotificationItem {
    id: string;
    dedupKey: string;
    category: 'action' | 'network' | 'ops';
    priority: 'P1' | 'P2' | 'P3';
    icon: string;
    title: string;
    subtitle: string;
    timestamp: string;
    repeatCount: number;
    targetPath: string;
    requiresAction: boolean;
    approvalId?: string;
    requestedByUserId?: string;
    routerId?: string;
  }

  const router = useRouter();
  const authStore = useAuthStore();
  const inventoryStore = useInventoryStore();
  const nocStore = useNocEventsStore();
  const { t } = useI18n();

  const isOpen = ref(false);
  const activeTab = ref<'all' | 'action' | 'network' | 'ops'>('all');
  const bellContainerRef = ref<HTMLElement | null>(null);
  const bellButtonRef = ref<HTMLButtonElement | null>(null);
  const liveAnnouncerText = ref('');

  const pendingApprovals = ref<
    Array<{
      id: string;
      summary: string;
      router_id: string;
      router_name: string;
      requested_by: string;
      requested_by_username: string;
      created_at: string;
    }>
  >([]);
  const approvingId = ref<string | null>(null);

  // Estado persistido por tenant/usuario (Read timestamp, Acked IDs, Sound, Snooze)
  const storageKeyPrefix = computed(() => {
    const tid = authStore.user?.tenant_id || 'default';
    const uid = authStore.user?.id || 'anon';
    return `rg_notif_${tid}_${uid}`;
  });

  const lastReadIso = ref<string>('');
  const ackedKeys = ref<Set<string>>(new Set());
  const soundEnabled = ref<boolean>(false);
  const snoozedUntilMs = ref<number>(0);
  const nowTickMs = ref<number>(Date.now());

  let syncChannel: BroadcastChannel | null = null;
  let clockInterval: ReturnType<typeof setInterval> | null = null;
  const baseDocumentTitle = ref<string>(
    typeof document !== 'undefined' ? document.title.replace(/^\(\d+\)\s*🔔\s*/, '') : 'RoSGrid',
  );

  const NOISE_ACTIONS = new Set([
    'SESSION_REFRESHED',
    'TOKEN_RENEWED',
    'USER_LOGIN',
    'USER_LOGOUT',
    'AUTH_LOGIN_SUCCESS',
    'AUTH_LOGOUT',
  ]);

  const isCheckerAuthorized = computed(() => {
    const role = authStore.currentRole || authStore.user?.role;
    return (
      role === 'SUPERADMIN_GLOBAL' ||
      role === 'TENANT_ADMIN' ||
      role === 'SUPERVISOR' ||
      role === 'SUPPORT_L3'
    );
  });

  const isSnoozed = computed(() => snoozedUntilMs.value > nowTickMs.value);

  function loadPersistedPrefs(): void {
    if (typeof localStorage === 'undefined') return;
    try {
      const prefix = storageKeyPrefix.value;
      lastReadIso.value = localStorage.getItem(`${prefix}_last_read`) || '';
      const rawAck = localStorage.getItem(`${prefix}_acked`);
      ackedKeys.value = rawAck ? new Set(JSON.parse(rawAck)) : new Set();
      soundEnabled.value = localStorage.getItem(`${prefix}_sound`) === 'true';
      snoozedUntilMs.value = Number(localStorage.getItem(`${prefix}_snooze_until`) || '0');
    } catch {
      // Ignorar errores de acceso a localStorage
    }
  }

  function savePersistedPrefs(): void {
    if (typeof localStorage === 'undefined') return;
    try {
      const prefix = storageKeyPrefix.value;
      localStorage.setItem(`${prefix}_last_read`, lastReadIso.value);
      localStorage.setItem(`${prefix}_acked`, JSON.stringify(Array.from(ackedKeys.value).slice(-100)));
      localStorage.setItem(`${prefix}_sound`, String(soundEnabled.value));
      localStorage.setItem(`${prefix}_snooze_until`, String(snoozedUntilMs.value));
    } catch {
      // Ignorar errores de cuota
    }
  }

  function broadcastStateSync(): void {
    try {
      syncChannel?.postMessage({
        type: 'SYNC_PREFS',
        tenantId: authStore.user?.tenant_id,
      });
    } catch {
      // Ignorar si BroadcastChannel no está disponible
    }
  }

  function playTacticalTone(priority: 'P1' | 'P2'): void {
    if (!soundEnabled.value || isSnoozed.value || typeof window === 'undefined') return;
    const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioCtx) return;
    try {
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = priority === 'P1' ? 'triangle' : 'sine';
      osc.frequency.setValueAtTime(priority === 'P1' ? 880 : 587.33, ctx.currentTime);
      gain.gain.setValueAtTime(0.06, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.18);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.18);
    } catch {
      // Ignorar restricciones de autoplay del navegador
    }
  }

  async function fetchPendingApprovalsIfAllowed(): Promise<void> {
    if (!isCheckerAuthorized.value) {
      pendingApprovals.value = [];
      return;
    }
    try {
      const res = await http.get<{ items: Record<string, unknown>[] } | Record<string, unknown>[]>(
        '/api/v1/operations/approvals',
      );
      const raw = Array.isArray(res.data) ? res.data : res.data?.items || [];
      const awaiting = raw.filter(
        (item) => item.status === 'PENDING' || item.status === 'AWAITING_APPROVAL',
      );
      pendingApprovals.value = awaiting.map((item) => ({
        id: String(item.id || ''),
        summary: String(item.justification || item.summary || 'Operación crítica pendiente de 4 ojos'),
        router_id: String(item.router_id || ''),
        router_name: String(item.router_name || item.summary || 'Router MikroTik'),
        requested_by: String(item.requested_by || ''),
        requested_by_username: String(item.requested_by_username || 'operador'),
        created_at: String(item.created_at || new Date().toISOString()),
      }));
      if (typeof nocStore.setPendingApprovalsCount === 'function') {
        nocStore.setPendingApprovalsCount(pendingApprovals.value.length);
      } else {
        nocStore.pendingApprovalsCount = pendingApprovals.value.length;
      }
    } catch {
      // Mantener estado actual ante fallos transitorios de red
    }
  }

  function isUuidLike(val: string): boolean {
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(val.trim());
  }

  const allNotifications = computed<TacticalNotificationItem[]>(() => {
    const itemsMap = new Map<string, TacticalNotificationItem>();

    // 1. Solicitudes Maker-Checker Pendientes (P2 — Requieren Firma 4 Ojos)
    if (isCheckerAuthorized.value) {
      for (const req of pendingApprovals.value) {
        const dedupKey = `approval:${req.id}`;
        itemsMap.set(dedupKey, {
          id: dedupKey,
          dedupKey,
          category: 'action',
          priority: 'P2',
          icon: '🛡️',
          title: `${t('notifications.approval_title', 'Aprobación 4 Ojos')}: ${req.router_name}`,
          subtitle: `${req.summary} (${t('notifications.by', 'por')} ${req.requested_by_username})`,
          timestamp: req.created_at,
          repeatCount: 1,
          targetPath: '/approvals',
          requiresAction: true,
          approvalId: req.id,
          requestedByUserId: req.requested_by,
          routerId: req.router_id,
        });
      }
    }

    // 2. Estado Activo de Flota en Inventario (Routers Caídos / Alerta TOFU / En Mantenimiento)
    for (const r of inventoryStore.routers) {
      if (r.admin_state === 'MAINTENANCE') {
        const dedupKey = `router-maint:${r.id}`;
        itemsMap.set(dedupKey, {
          id: dedupKey,
          dedupKey,
          category: 'ops',
          priority: 'P3',
          icon: '🛠️',
          title: `${r.display_name} (${r.ip_address})`,
          subtitle: t('notifications.router_in_maintenance', 'Equipo en ventana de mantenimiento activa (alertas silenciadas)'),
          timestamp: r.last_seen_at || new Date().toISOString(),
          repeatCount: 1,
          targetPath: '/inventory/maintenance-windows',
          requiresAction: false,
          routerId: r.id,
        });
        continue;
      }

      if (r.last_reachability_status === 'OFFLINE') {
        const dedupKey = `router-offline:${r.id}`;
        const isAcked = ackedKeys.value.has(dedupKey);
        itemsMap.set(dedupKey, {
          id: dedupKey,
          dedupKey,
          category: 'network',
          priority: 'P1',
          icon: '🚨',
          title: `${r.display_name} (${r.ip_address}) — OFFLINE`,
          subtitle: t('notifications.router_unreachable', 'Pérdida de conectividad REST/ICMP detectada'),
          timestamp: r.last_seen_at || new Date().toISOString(),
          repeatCount: 1,
          targetPath: '/noc-wallboard',
          requiresAction: !isAcked,
          routerId: r.id,
        });
      } else if (r.last_reachability_status === 'TOFU_ALERT') {
        const dedupKey = `router-tofu:${r.id}`;
        const isAcked = ackedKeys.value.has(dedupKey);
        itemsMap.set(dedupKey, {
          id: dedupKey,
          dedupKey,
          category: 'network',
          priority: 'P1',
          icon: '🔐',
          title: `${r.display_name} — ${t('notifications.tofu_alert', 'Alerta TOFU SSL')}`,
          subtitle: t('notifications.tofu_mismatch', 'Discrepancia de certificado TLS SHA-256 detectada'),
          timestamp: r.last_seen_at || new Date().toISOString(),
          repeatCount: 1,
          targetPath: '/inventory',
          requiresAction: !isAcked,
          routerId: r.id,
        });
      }
    }

    // 3. Eventos en Tiempo Real del Canal NOC (Deduplicados y sin Ruido de Sesión)
    for (const ev of nocStore.recentEvents) {
      const rawAction = String(ev.type || '').toUpperCase();
      const rawSummary = String(ev.summary || '');
      if (
        NOISE_ACTIONS.has(rawAction) ||
        rawSummary.toLowerCase().includes('session token renewed')
      ) {
        continue;
      }

      const routerLabel = ev.router_name && !isUuidLike(ev.router_name) ? ev.router_name : 'Sistema RoSGrid';
      const dedupKey = `ev:${rawAction}:${ev.router_id || routerLabel}`;
      const existing = itemsMap.get(dedupKey);
      if (existing) {
        existing.repeatCount += 1;
        if (ev.timestamp > existing.timestamp) {
          existing.timestamp = ev.timestamp;
        }
        continue;
      }

      const isCritical = ev.type === 'CRITICAL' || rawAction.includes('DOWN') || rawAction.includes('OUTAGE');
      const isMaintenance = ev.type === 'MAINTENANCE' || rawAction.includes('MAINTENANCE');
      const isAcked = ackedKeys.value.has(dedupKey);

      itemsMap.set(dedupKey, {
        id: ev.id || dedupKey,
        dedupKey,
        category: isCritical ? 'network' : 'ops',
        priority: isCritical ? 'P1' : isMaintenance ? 'P2' : 'P3',
        icon: isCritical ? '🚨' : isMaintenance ? '🛠️' : '📡',
        title: routerLabel,
        subtitle: rawSummary,
        timestamp: ev.timestamp,
        repeatCount: 1,
        targetPath: isMaintenance
          ? '/inventory/maintenance-windows'
          : isCritical
            ? '/noc-wallboard'
            : '/inventory',
        requiresAction: isCritical && !isAcked,
        routerId: ev.router_id,
      });
    }

    return Array.from(itemsMap.values()).sort((a, b) => {
      if (a.requiresAction !== b.requiresAction) return a.requiresAction ? -1 : 1;
      const prioOrder = { P1: 0, P2: 1, P3: 2 };
      if (prioOrder[a.priority] !== prioOrder[b.priority]) {
        return prioOrder[a.priority] - prioOrder[b.priority];
      }
      return b.timestamp.localeCompare(a.timestamp);
    });
  });

  const actionRequiredItems = computed(() =>
    allNotifications.value.filter((item) => item.requiresAction),
  );

  const unreadInformationalCount = computed(() =>
    allNotifications.value.filter(
      (item) => !item.requiresAction && (!lastReadIso.value || item.timestamp > lastReadIso.value),
    ).length,
  );

  const highestActivePriority = computed<'P1' | 'P2' | 'P3' | 'NONE'>(() => {
    if (actionRequiredItems.value.some((i) => i.priority === 'P1')) return 'P1';
    if (actionRequiredItems.value.some((i) => i.priority === 'P2')) return 'P2';
    if (unreadInformationalCount.value > 0) return 'P3';
    return 'NONE';
  });

  const filteredNotifications = computed(() => {
    if (activeTab.value === 'action') {
      return allNotifications.value.filter((i) => i.requiresAction || i.category === 'action');
    }
    if (activeTab.value === 'network') {
      return allNotifications.value.filter((i) => i.category === 'network');
    }
    if (activeTab.value === 'ops') {
      return allNotifications.value.filter((i) => i.category === 'ops');
    }
    return allNotifications.value;
  });

  function canInlineApprove(item: TacticalNotificationItem): boolean {
    if (!item.approvalId || !isCheckerAuthorized.value) return false;
    if (authStore.currentRole === 'SUPERADMIN_GLOBAL') return true;
    return Boolean(authStore.user?.id && item.requestedByUserId !== authStore.user.id);
  }

  async function handleInlineApprove(item: TacticalNotificationItem, e: Event): Promise<void> {
    e.stopPropagation();
    if (!item.approvalId || approvingId.value) return;
    approvingId.value = item.approvalId;
    try {
      await http.post(`/api/v1/operations/approvals/${item.approvalId}/approve`, {
        review_comment: 'Aprobado en 1 clic desde el Centro Táctico de Notificaciones',
      });
      pendingApprovals.value = pendingApprovals.value.filter((a) => a.id !== item.approvalId);
      if (typeof nocStore.setPendingApprovalsCount === 'function') {
        nocStore.setPendingApprovalsCount(pendingApprovals.value.length);
      }
      liveAnnouncerText.value = t('notifications.approved_inline_sr', 'Solicitud aprobada correctamente');
      broadcastStateSync();
    } catch {
      // Si requiere inspección adicional, redirigir a la bandeja Maker-Checker
      isOpen.value = false;
      router.push('/approvals');
    } finally {
      approvingId.value = null;
    }
  }

  function handleAcknowledge(item: TacticalNotificationItem, e: Event): void {
    e.stopPropagation();
    ackedKeys.value.add(item.dedupKey);
    ackedKeys.value = new Set(ackedKeys.value);
    savePersistedPrefs();
    broadcastStateSync();
  }

  function markAllInformationalRead(): void {
    lastReadIso.value = new Date().toISOString();
    for (const item of allNotifications.value) {
      if (!item.approvalId) {
        ackedKeys.value.add(item.dedupKey);
      }
    }
    ackedKeys.value = new Set(ackedKeys.value);
    savePersistedPrefs();
    broadcastStateSync();
  }

  function toggleSound(): void {
    soundEnabled.value = !soundEnabled.value;
    savePersistedPrefs();
    broadcastStateSync();
  }

  function toggleSnooze30m(): void {
    if (isSnoozed.value) {
      snoozedUntilMs.value = 0;
    } else {
      snoozedUntilMs.value = Date.now() + 30 * 60 * 1000;
    }
    nowTickMs.value = Date.now();
    savePersistedPrefs();
    broadcastStateSync();
  }

  function handleSelectNotification(item: TacticalNotificationItem): void {
    if (!item.approvalId) {
      ackedKeys.value.add(item.dedupKey);
      ackedKeys.value = new Set(ackedKeys.value);
    }
    lastReadIso.value = new Date().toISOString();
    savePersistedPrefs();
    broadcastStateSync();
    isOpen.value = false;
    router.push(item.targetPath);
  }

  function togglePopover(): void {
    isOpen.value = !isOpen.value;
    if (isOpen.value) {
      lastReadIso.value = new Date().toISOString();
      savePersistedPrefs();
      fetchPendingApprovalsIfAllowed();
    }
  }

  function closePopover(restoreFocus = false): void {
    if (!isOpen.value) return;
    isOpen.value = false;
    if (restoreFocus && bellButtonRef.value) {
      bellButtonRef.value.focus();
    }
  }

  function formatRelativeTime(iso: string): string {
    if (!iso) return '—';
    const parsed = Date.parse(iso);
    if (Number.isNaN(parsed)) return iso;
    const diffSec = Math.max(0, Math.floor((nowTickMs.value - parsed) / 1000));
    if (diffSec < 60) return `${diffSec}s`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m`;
    const diffHours = Math.floor(diffMin / 60);
    if (diffHours < 24) return `${diffHours}h`;
    return new Date(parsed).toLocaleDateString();
  }

  function onDocumentClick(e: MouseEvent): void {
    if (bellContainerRef.value && !bellContainerRef.value.contains(e.target as Node)) {
      closePopover(false);
    }
  }

  function onGlobalKeydown(e: KeyboardEvent): void {
    if (e.altKey && (e.key === 'n' || e.key === 'N')) {
      e.preventDefault();
      togglePopover();
      return;
    }
    if (e.key === 'Escape' && isOpen.value) {
      e.preventDefault();
      closePopover(true);
    }
  }

  function onMakerCheckerRealtimeEvent(): void {
    fetchPendingApprovalsIfAllowed();
    playTacticalTone('P2');
  }

  function onTenantSwitched(): void {
    loadPersistedPrefs();
    fetchPendingApprovalsIfAllowed();
  }

  // Actualizar título de la pestaña cuando hay elementos P1/P2 pendientes de atención
  watch(
    () => actionRequiredItems.value.length,
    (count, prevCount) => {
      if (typeof document !== 'undefined') {
        const cleanTitle = document.title.replace(/^\(\d+\)\s*🔔\s*/, '') || baseDocumentTitle.value;
        document.title = count > 0 ? `(${count}) 🔔 ${cleanTitle}` : cleanTitle;
      }
      if (count > (prevCount || 0)) {
        const latest = actionRequiredItems.value[0];
        if (latest) {
          liveAnnouncerText.value = `${latest.title}: ${latest.subtitle}`;
          playTacticalTone(latest.priority === 'P1' ? 'P1' : 'P2');
        }
      }
    },
    { immediate: true },
  );

  onMounted(() => {
    loadPersistedPrefs();
    fetchPendingApprovalsIfAllowed();
    clockInterval = setInterval(() => {
      nowTickMs.value = Date.now();
    }, 30000);

    if (typeof document !== 'undefined') {
      document.addEventListener('click', onDocumentClick);
      document.addEventListener('keydown', onGlobalKeydown);
    }
    if (typeof window !== 'undefined') {
      window.addEventListener('rosgrid:maker-checker-updated', onMakerCheckerRealtimeEvent);
      window.addEventListener('rosgrid:tenant-switched', onTenantSwitched);
      if ('BroadcastChannel' in window) {
        try {
          syncChannel = new BroadcastChannel('rosgrid_notifications_sync');
          syncChannel.onmessage = () => {
            loadPersistedPrefs();
            fetchPendingApprovalsIfAllowed();
          };
        } catch {
          syncChannel = null;
        }
      }
    }
  });

  onBeforeUnmount(() => {
    if (clockInterval) {
      clearInterval(clockInterval);
    }
    if (typeof document !== 'undefined') {
      document.removeEventListener('click', onDocumentClick);
      document.removeEventListener('keydown', onGlobalKeydown);
      document.title = document.title.replace(/^\(\d+\)\s*🔔\s*/, '');
    }
    if (typeof window !== 'undefined') {
      window.removeEventListener('rosgrid:maker-checker-updated', onMakerCheckerRealtimeEvent);
      window.removeEventListener('rosgrid:tenant-switched', onTenantSwitched);
    }
    try {
      syncChannel?.close();
    } catch {
      // Ignorar al desmontar
    }
  });
</script>

<template>
  <div ref="bellContainerRef" class="rg-notification-center">
    <!-- Región ARIA Live para Lectores de Pantalla (WCAG 4.1.3) -->
    <div id="rg-notification-live-announcer" class="sr-only" aria-live="polite" aria-atomic="true">
      {{ liveAnnouncerText }}
    </div>

    <!-- Botón de Campana en Barra Superior -->
    <button
      id="btn-notification-bell"
      ref="bellButtonRef"
      type="button"
      class="btn-notification-bell"
      :class="{
        'btn-notification-bell--open': isOpen,
        'btn-notification-bell--p1': highestActivePriority === 'P1' && !isSnoozed,
        'btn-notification-bell--p2': highestActivePriority === 'P2' && !isSnoozed,
      }"
      aria-haspopup="dialog"
      :aria-expanded="isOpen"
      aria-controls="rg-notification-popover"
      :title="t('notifications.bell_title', 'Centro de Notificaciones y Atención Táctica (Alt+N)')"
      :aria-label="
        t('notifications.bell_aria', 'Centro de notificaciones') +
        (actionRequiredItems.length > 0 ? ` (${actionRequiredItems.length})` : '')
      "
      @click="togglePopover"
    >
      <span class="bell-icon" aria-hidden="true">{{ isSnoozed ? '🔕' : '🔔' }}</span>

      <!-- Insignia Numérica para Ítems que Requieren Acción (P1 Crítico / P2 Gobernanza) -->
      <span
        v-if="actionRequiredItems.length > 0"
        id="notification-bell-badge"
        class="bell-badge"
        :class="{
          'bell-badge--p1': highestActivePriority === 'P1',
          'bell-badge--p2': highestActivePriority !== 'P1',
        }"
        aria-hidden="true"
      >
        {{ actionRequiredItems.length > 99 ? '99+' : actionRequiredItems.length }}
      </span>

      <!-- Punto Cian Discreto para Avisos Informativos No Leídos (P3) -->
      <span
        v-else-if="unreadInformationalCount > 0"
        id="notification-bell-dot"
        class="bell-unread-dot"
        aria-hidden="true"
      ></span>
    </button>

    <!-- Panel Flotante de Notificaciones y Triaje Rápido -->
    <div
      v-if="isOpen"
      id="rg-notification-popover"
      class="rg-notification-popover"
      role="dialog"
      aria-modal="false"
      :aria-label="t('notifications.panel_title', 'Centro de Notificaciones')"
    >
      <!-- Cabecera del Panel -->
      <div class="notif-popover-header">
        <div class="notif-header-title-wrap">
          <h2 class="notif-header-title">
            🔔 {{ t('notifications.panel_title', 'Centro de Notificaciones') }}
          </h2>
          <span v-if="actionRequiredItems.length > 0" class="notif-pending-pill">
            {{ actionRequiredItems.length }} {{ t('notifications.require_attention', 'requieren atención') }}
          </span>
        </div>

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
            id="btn-notif-snooze-30m"
            type="button"
            class="btn-notif-ctrl"
            :class="{ 'btn-notif-ctrl--active': isSnoozed }"
            :title="t('notifications.snooze_30m_title', 'Silenciar alertas visuales y sonoras por 30 minutos')"
            @click="toggleSnooze30m"
          >
            {{ isSnoozed ? '🔕 30m' : '🕒 30m' }}
          </button>

          <button
            id="btn-notif-mark-all-read"
            type="button"
            class="btn-notif-ctrl"
            :title="t('notifications.mark_all_read', 'Marcar avisos como vistos')"
            @click="markAllInformationalRead"
          >
            ✓ {{ t('notifications.mark_read_short', 'Vistas') }}
          </button>
        </div>
      </div>

      <!-- Pestañas de Categorización -->
      <div class="notif-tabs-bar" role="tablist">
        <button
          id="notif-tab-all"
          type="button"
          role="tab"
          class="notif-tab-btn"
          :class="{ 'notif-tab-btn--active': activeTab === 'all' }"
          :aria-selected="activeTab === 'all'"
          @click="activeTab = 'all'"
        >
          {{ t('notifications.tab_all', 'Todas') }} ({{ allNotifications.length }})
        </button>
        <button
          id="notif-tab-action"
          type="button"
          role="tab"
          class="notif-tab-btn"
          :class="{ 'notif-tab-btn--active': activeTab === 'action' }"
          :aria-selected="activeTab === 'action'"
          @click="activeTab = 'action'"
        >
          ⚡ {{ t('notifications.tab_action', 'Acción') }} ({{ actionRequiredItems.length }})
        </button>
        <button
          id="notif-tab-network"
          type="button"
          role="tab"
          class="notif-tab-btn"
          :class="{ 'notif-tab-btn--active': activeTab === 'network' }"
          :aria-selected="activeTab === 'network'"
          @click="activeTab = 'network'"
        >
          🚨 {{ t('notifications.tab_network', 'Red') }}
        </button>
        <button
          id="notif-tab-ops"
          type="button"
          role="tab"
          class="notif-tab-btn"
          :class="{ 'notif-tab-btn--active': activeTab === 'ops' }"
          :aria-selected="activeTab === 'ops'"
          @click="activeTab = 'ops'"
        >
          🛠️ {{ t('notifications.tab_ops', 'Operaciones') }}
        </button>
      </div>

      <!-- Lista de Notificaciones -->
      <div v-if="filteredNotifications.length === 0" class="notif-empty-state">
        <div class="notif-empty-icon" aria-hidden="true">✅</div>
        <p class="notif-empty-title">
          {{ t('notifications.empty_title', 'Todo al día en tu organización') }}
        </p>
        <p class="notif-empty-sub">
          {{ t('notifications.empty_sub', 'No hay aprobaciones pendientes ni alertas activas sin atender.') }}
        </p>
      </div>

      <ul v-else class="notif-list">
        <li
          v-for="item in filteredNotifications"
          :key="item.id"
          class="notif-row"
          :class="{
            'notif-row--action-p1': item.requiresAction && item.priority === 'P1',
            'notif-row--action-p2': item.requiresAction && item.priority === 'P2',
          }"
          tabindex="0"
          @click="handleSelectNotification(item)"
          @keydown.enter.prevent="handleSelectNotification(item)"
        >
          <div class="notif-row-icon" aria-hidden="true">{{ item.icon }}</div>

          <div class="notif-row-body">
            <div class="notif-row-top">
              <span class="notif-row-title">{{ item.title }}</span>
              <span v-if="item.repeatCount > 1" class="notif-repeat-badge">
                ×{{ item.repeatCount }}
              </span>
              <span class="notif-row-time font-mono">{{ formatRelativeTime(item.timestamp) }}</span>
            </div>

            <p class="notif-row-subtitle">{{ item.subtitle }}</p>

            <!-- Botones de Triaje en Línea (Sin abandonar la vista actual) -->
            <div v-if="item.requiresAction" class="notif-inline-actions">
              <button
                v-if="canInlineApprove(item)"
                type="button"
                class="btn-inline-action btn-inline-action--approve"
                :disabled="approvingId === item.approvalId"
                @click="handleInlineApprove(item, $event)"
              >
                {{
                  approvingId === item.approvalId
                    ? t('common.loading', 'Cargando...')
                    : `✓ ${t('notifications.approve_now', 'Aprobar 1-Clic')}`
                }}
              </button>

              <button
                v-if="item.approvalId"
                type="button"
                class="btn-inline-action btn-inline-action--inspect"
                @click.stop="handleSelectNotification(item)"
              >
                🔍 {{ t('notifications.inspect_request', 'Revisar') }}
              </button>

              <button
                v-if="!item.approvalId"
                type="button"
                class="btn-inline-action btn-inline-action--ack"
                @click="handleAcknowledge(item, $event)"
              >
                👁️ {{ t('notifications.ack_alert', 'Reconocer (Ack)') }}
              </button>
            </div>
          </div>
        </li>
      </ul>

      <!-- Pie del Panel con Enlaces Rápidos -->
      <div class="notif-popover-footer">
        <button
          v-if="isCheckerAuthorized"
          type="button"
          class="btn-notif-footer-link"
          @click="
            isOpen = false;
            router.push('/approvals');
          "
        >
          🛡️ {{ t('notifications.go_approvals', 'Ir a Maker-Checker') }}
        </button>
        <button
          type="button"
          class="btn-notif-footer-link"
          @click="
            isOpen = false;
            router.push('/noc-wallboard');
          "
        >
          📊 {{ t('notifications.go_wallboard', 'Abrir Wallboard NOC') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .rg-notification-center {
    position: relative;
    display: inline-flex;
    align-items: center;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  .btn-notification-bell {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 32px;
    border-radius: var(--rg-radius-md, 6px);
    background: var(--rg-bg-panel);
    border: 1px solid var(--rg-border-subtle);
    color: var(--rg-text-secondary);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-notification-bell:hover,
  .btn-notification-bell--open {
    color: var(--rg-text-primary);
    border-color: var(--rg-accent-cyan);
    background: rgba(0, 229, 255, 0.08);
  }

  .btn-notification-bell--p1 {
    border-color: var(--rg-status-offline);
    box-shadow: 0 0 10px rgba(255, 23, 68, 0.35);
  }

  .btn-notification-bell--p2 {
    border-color: var(--rg-status-warning);
  }

  .bell-icon {
    font-size: 0.95rem;
    line-height: 1;
  }

  .bell-badge {
    position: absolute;
    top: -5px;
    right: -6px;
    min-width: 18px;
    height: 18px;
    padding: 0 4px;
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    border: 1.5px solid var(--rg-bg-canvas);
  }

  .bell-badge--p1 {
    background: var(--rg-status-offline, #ff1744);
  }

  .bell-badge--p2 {
    background: #d97706;
  }

  .bell-unread-dot {
    position: absolute;
    top: 3px;
    right: 4px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--rg-accent-cyan, #00e5ff);
    box-shadow: 0 0 6px rgba(0, 229, 255, 0.8);
  }

  .rg-notification-popover {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    width: 400px;
    max-width: calc(100vw - 24px);
    background: var(--rg-bg-panel);
    border: 1px solid var(--rg-border-strong, var(--rg-border-subtle));
    border-radius: var(--rg-radius-lg, 10px);
    box-shadow: 0 14px 36px rgba(0, 0, 0, 0.55);
    z-index: 1200;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .notif-popover-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 10px 12px;
    border-bottom: 1px solid var(--rg-border-subtle);
    background: rgba(0, 0, 0, 0.18);
  }

  .notif-header-title-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }

  .notif-header-title {
    margin: 0;
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--rg-text-primary);
  }

  .notif-pending-pill {
    font-size: 0.68rem;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 999px;
    background: rgba(245, 158, 11, 0.16);
    color: var(--rg-status-warning);
    border: 1px solid rgba(245, 158, 11, 0.35);
  }

  .notif-header-controls {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .btn-notif-ctrl {
    padding: 3px 7px;
    border-radius: 5px;
    font-size: 0.72rem;
    font-weight: 600;
    background: transparent;
    border: 1px solid var(--rg-border-subtle);
    color: var(--rg-text-secondary);
    cursor: pointer;
  }

  .btn-notif-ctrl:hover,
  .btn-notif-ctrl--active {
    color: var(--rg-accent-cyan);
    border-color: var(--rg-accent-cyan);
    background: rgba(0, 229, 255, 0.08);
  }

  .notif-tabs-bar {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 4px;
    padding: 6px 10px;
    border-bottom: 1px solid var(--rg-border-subtle);
    background: rgba(0, 0, 0, 0.1);
  }

  .notif-tab-btn {
    padding: 5px 4px;
    border-radius: 5px;
    font-size: 0.72rem;
    font-weight: 600;
    background: transparent;
    border: 1px solid transparent;
    color: var(--rg-text-secondary);
    cursor: pointer;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .notif-tab-btn--active {
    background: rgba(0, 229, 255, 0.12);
    color: var(--rg-accent-cyan);
    border-color: rgba(0, 229, 255, 0.3);
  }

  .notif-list {
    list-style: none;
    margin: 0;
    padding: 0;
    max-height: 360px;
    overflow-y: auto;
  }

  .notif-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 12px;
    border-bottom: 1px solid var(--rg-border-subtle);
    cursor: pointer;
    transition: background 0.12s ease;
  }

  .notif-row:hover {
    background: rgba(0, 229, 255, 0.05);
  }

  .notif-row--action-p1 {
    border-left: 3px solid var(--rg-status-offline);
    background: rgba(255, 23, 68, 0.06);
  }

  .notif-row--action-p2 {
    border-left: 3px solid var(--rg-status-warning);
    background: rgba(245, 158, 11, 0.06);
  }

  .notif-row-icon {
    font-size: 1.05rem;
    line-height: 1.2;
    flex-shrink: 0;
  }

  .notif-row-body {
    flex: 1;
    min-width: 0;
  }

  .notif-row-top {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .notif-row-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--rg-text-primary);
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .notif-repeat-badge {
    font-size: 0.68rem;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 4px;
    background: rgba(0, 229, 255, 0.14);
    color: var(--rg-accent-cyan);
  }

  .notif-row-time {
    font-size: 0.7rem;
    color: var(--rg-text-muted);
    flex-shrink: 0;
  }

  .notif-row-subtitle {
    margin: 3px 0 0;
    font-size: 0.75rem;
    color: var(--rg-text-secondary);
    line-height: 1.35;
  }

  .notif-inline-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 7px;
  }

  .btn-inline-action {
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    cursor: pointer;
    border: 1px solid var(--rg-border-subtle);
    background: var(--rg-bg-canvas);
    color: var(--rg-text-primary);
  }

  .btn-inline-action--approve {
    border-color: rgba(16, 185, 129, 0.5);
    color: var(--rg-status-online);
    background: rgba(16, 185, 129, 0.12);
  }

  .btn-inline-action--inspect {
    border-color: rgba(0, 229, 255, 0.4);
    color: var(--rg-accent-cyan);
  }

  .btn-inline-action--ack {
    border-color: rgba(245, 158, 11, 0.45);
    color: var(--rg-status-warning);
  }

  .notif-empty-state {
    padding: 28px 16px;
    text-align: center;
  }

  .notif-empty-icon {
    font-size: 1.5rem;
    margin-bottom: 6px;
  }

  .notif-empty-title {
    margin: 0;
    font-size: 0.84rem;
    font-weight: 700;
    color: var(--rg-text-primary);
  }

  .notif-empty-sub {
    margin: 4px 0 0;
    font-size: 0.75rem;
    color: var(--rg-text-secondary);
  }

  .notif-popover-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-top: 1px solid var(--rg-border-subtle);
    background: rgba(0, 0, 0, 0.15);
  }

  .btn-notif-footer-link {
    background: transparent;
    border: none;
    color: var(--rg-accent-cyan);
    font-size: 0.74rem;
    font-weight: 600;
    cursor: pointer;
    padding: 2px 4px;
  }

  .btn-notif-footer-link:hover {
    text-decoration: underline;
  }
</style>
```

---

### Paso 2: Integrar `RgNotificationCenterBell.vue` en `vue3/src/components/common/RgResponsiveShell.vue`

1. Importar `RgNotificationCenterBell` en `<script setup lang="ts">` de `vue3/src/components/common/RgResponsiveShell.vue`:

**`Target` en `vue3/src/components/common/RgResponsiveShell.vue` (líneas 18–24):**
```ts
  import RgBrandLogo from './RgBrandLogo.vue';
  import RgContextualHelpDrawer from './RgContextualHelpDrawer.vue';
  import ChangePasswordModal from '@/components/common/ChangePasswordModal.vue';
  import RgStepUp2FAModal from '@/components/common/RgStepUp2FAModal.vue';
  import RgMcpTokenModal from '@/components/admin/RgMcpTokenModal.vue';
  import RgTenantSwitcher from '@/components/admin/RgTenantSwitcher.vue';
```

**`Replacement` en `vue3/src/components/common/RgResponsiveShell.vue`:**
```ts
  import RgBrandLogo from './RgBrandLogo.vue';
  import RgContextualHelpDrawer from './RgContextualHelpDrawer.vue';
  import RgNotificationCenterBell from './RgNotificationCenterBell.vue';
  import ChangePasswordModal from '@/components/common/ChangePasswordModal.vue';
  import RgStepUp2FAModal from '@/components/common/RgStepUp2FAModal.vue';
  import RgMcpTokenModal from '@/components/admin/RgMcpTokenModal.vue';
  import RgTenantSwitcher from '@/components/admin/RgTenantSwitcher.vue';
```

2. Colocar `<RgNotificationCenterBell />` en `.header-right` de `vue3/src/components/common/RgResponsiveShell.vue`, justo entre el botón `#btn-contextual-help` y `.user-menu-container`:

**`Target` en `vue3/src/components/common/RgResponsiveShell.vue` (líneas 371–388):**
```html
        <!-- Botón de Ayuda Contextual In-App (Hito 27.14) -->
        <button
          id="btn-contextual-help"
          type="button"
          class="btn-contextual-help"
          :aria-expanded="isHelpOpen"
          aria-controls="rg-contextual-help-drawer"
          :title="t('shell.help_title', 'Ayuda de esta pantalla (F1 / Alt+H)')"
          :aria-label="t('shell.help_aria', 'Abrir ayuda contextual de esta pantalla')"
          @click="toggleHelp()"
        >
          <span aria-hidden="true">❓</span>
          <span class="help-btn-label">{{ t('shell.help_label', 'Ayuda') }}</span>
        </button>

        <!-- Menú Desplegable Táctico de Usuario -->
        <div v-if="authStore.user" ref="userMenuRef" class="user-menu-container">
```

**`Replacement` en `vue3/src/components/common/RgResponsiveShell.vue`:**
```html
        <!-- Botón de Ayuda Contextual In-App (Hito 27.14) -->
        <button
          id="btn-contextual-help"
          type="button"
          class="btn-contextual-help"
          :aria-expanded="isHelpOpen"
          aria-controls="rg-contextual-help-drawer"
          :title="t('shell.help_title', 'Ayuda de esta pantalla (F1 / Alt+H)')"
          :aria-label="t('shell.help_aria', 'Abrir ayuda contextual de esta pantalla')"
          @click="toggleHelp()"
        >
          <span aria-hidden="true">❓</span>
          <span class="help-btn-label">{{ t('shell.help_label', 'Ayuda') }}</span>
        </button>

        <!-- Centro Táctico de Notificaciones In-App (Hito 30.4) -->
        <RgNotificationCenterBell v-if="authStore.user" />

        <!-- Menú Desplegable Táctico de Usuario -->
        <div v-if="authStore.user" ref="userMenuRef" class="user-menu-container">
```

---

### Paso 3: Añadir Claves de Internacionalización en `vue3/src/locales/es.json` y `vue3/src/locales/en.json`

1. En `vue3/src/locales/es.json`, añadir el bloque `"notifications"` justo debajo de `"shell"` (verificando 0 claves duplicadas con `python3 .agents/scripts/verify_json_no_duplicate_keys.py`):

**`Target` en `vue3/src/locales/es.json` (líneas 31–44):**
```json
  "shell": {
    "search_label": "Buscar...",
    "search_aria": "Buscar recursos y comandos (Ctrl+K)",
    "show_sidebar": "Mostrar barra lateral",
    "hide_sidebar": "Ocultar barra lateral",
    "clock_aria": "Hora actual del sistema",
    "search": "Buscar...",
    "theme": "Tema visual",
    "language": "Idioma",
    "logout": "Salir",
    "switch_to_en": "Switch to English",
    "switch_to_es": "Cambiar a Español"
  },
```

**`Replacement` en `vue3/src/locales/es.json`:**
```json
  "shell": {
    "search_label": "Buscar...",
    "search_aria": "Buscar recursos y comandos (Ctrl+K)",
    "show_sidebar": "Mostrar barra lateral",
    "hide_sidebar": "Ocultar barra lateral",
    "clock_aria": "Hora actual del sistema",
    "search": "Buscar...",
    "theme": "Tema visual",
    "language": "Idioma",
    "logout": "Salir",
    "switch_to_en": "Switch to English",
    "switch_to_es": "Cambiar a Español"
  },
  "notifications": {
    "bell_title": "Centro de Notificaciones y Atención Táctica (Alt+N)",
    "bell_aria": "Centro de notificaciones",
    "panel_title": "Centro de Notificaciones",
    "require_attention": "requieren atención",
    "sound_on": "Aviso sonoro activado",
    "sound_off": "Activar aviso sonoro",
    "snooze_30m_title": "Silenciar alertas visuales y sonoras por 30 minutos",
    "mark_all_read": "Marcar avisos como vistos",
    "mark_read_short": "Vistas",
    "tab_all": "Todas",
    "tab_action": "Acción",
    "tab_network": "Red",
    "tab_ops": "Operaciones",
    "empty_title": "Todo al día en tu organización",
    "empty_sub": "No hay aprobaciones pendientes ni alertas activas sin atender.",
    "approval_title": "Aprobación 4 Ojos",
    "by": "por",
    "router_in_maintenance": "Equipo en ventana de mantenimiento activa (alertas silenciadas)",
    "router_unreachable": "Pérdida de conectividad REST/ICMP detectada",
    "tofu_alert": "Alerta TOFU SSL",
    "tofu_mismatch": "Discrepancia de certificado TLS SHA-256 detectada",
    "approve_now": "Aprobar 1-Clic",
    "inspect_request": "Revisar",
    "ack_alert": "Reconocer (Ack)",
    "approved_inline_sr": "Solicitud aprobada correctamente",
    "go_approvals": "Ir a Maker-Checker",
    "go_wallboard": "Abrir Wallboard NOC"
  },
```

2. En `vue3/src/locales/en.json`, añadir el bloque `"notifications"` equivalente debajo de `"shell"`:

**`Target` en `vue3/src/locales/en.json` (líneas 31–44):**
```json
  "shell": {
    "search_label": "Search...",
    "search_aria": "Search resources and commands (Ctrl+K)",
    "show_sidebar": "Show navigation sidebar",
    "hide_sidebar": "Hide navigation sidebar",
    "clock_aria": "Current system time",
    "search": "Search...",
    "theme": "Theme",
    "language": "Language",
    "logout": "Log out",
    "switch_to_en": "Switch to English",
    "switch_to_es": "Cambiar a Español"
  },
```

**`Replacement` en `vue3/src/locales/en.json`:**
```json
  "shell": {
    "search_label": "Search...",
    "search_aria": "Search resources and commands (Ctrl+K)",
    "show_sidebar": "Show navigation sidebar",
    "hide_sidebar": "Hide navigation sidebar",
    "clock_aria": "Current system time",
    "search": "Search...",
    "theme": "Theme",
    "language": "Language",
    "logout": "Log out",
    "switch_to_en": "Switch to English",
    "switch_to_es": "Cambiar a Español"
  },
  "notifications": {
    "bell_title": "Tactical Notification & Attention Center (Alt+N)",
    "bell_aria": "Notification center",
    "panel_title": "Notification Center",
    "require_attention": "require attention",
    "sound_on": "Sound alerts enabled",
    "sound_off": "Enable sound alerts",
    "snooze_30m_title": "Snooze visual and audio alerts for 30 minutes",
    "mark_all_read": "Mark informational notices as seen",
    "mark_read_short": "Seen",
    "tab_all": "All",
    "tab_action": "Action",
    "tab_network": "Network",
    "tab_ops": "Operations",
    "empty_title": "You are all caught up",
    "empty_sub": "No pending approvals or unacknowledged active alerts.",
    "approval_title": "4-Eyes Approval",
    "by": "by",
    "router_in_maintenance": "Router in active maintenance window (alerts suppressed)",
    "router_unreachable": "REST/ICMP reachability loss detected",
    "tofu_alert": "SSL TOFU Alert",
    "tofu_mismatch": "TLS SHA-256 certificate fingerprint mismatch detected",
    "approve_now": "1-Click Approve",
    "inspect_request": "Review",
    "ack_alert": "Acknowledge (Ack)",
    "approved_inline_sr": "Request approved successfully",
    "go_approvals": "Go to Maker-Checker",
    "go_wallboard": "Open NOC Wallboard"
  },
```

---

### Paso 4: Crear la Suite Unitaria Dedicada `vue3/src/components/common/RgNotificationCenterBell.unit.ts` (Invariante Cero Componentes Huérfanos)

Crear el archivo `vue3/src/components/common/RgNotificationCenterBell.unit.ts` verificando:
1. Separación entre *Read State* (`✓ Vistas`) y *Action Completion* (las aprobaciones Maker-Checker pendientes y routers `OFFLINE` sin `Ack` siguen fijados en `⚡ Acción`).
2. Triaje en línea 1-clic (`POST /api/v1/operations/approvals/{id}/approve`) y reconocimiento (`👁️ Reconocer (Ack)`) de caídas de red.
3. Deduplicación `[×N]` de eventos repetidos y filtrado de ruido administrativo (`SESSION_REFRESHED`, `Session token renewed`).
4. Conmutador de modo *Snooze* (`🔕 30m`) y navegación directa (*Deep-Linking*):

```ts
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import RgNotificationCenterBell from './RgNotificationCenterBell.vue';
import { useAuthStore } from '@/stores/useAuthStore';
import { useInventoryStore } from '@/stores/useInventoryStore';
import { useNocEventsStore } from '@/stores/useNocEventsStore';
import { http } from '@/api/httpClient';

const pushMock = vi.fn();
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

vi.mock('@/api/httpClient', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('RgNotificationCenterBell.vue — Centro Táctico de Notificaciones In-App 11X', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    pushMock.mockClear();
    vi.clearAllMocks();
    localStorage.clear();

    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-checker-1',
      username: 'sinfallas',
      email: 'sinfallas@rosgrid.local',
      role: 'SUPERADMIN_GLOBAL',
      tenant_id: 't-1',
      tenant_slug: 'sistemas',
      totp_enabled: true,
    });
  });

  it('muestra insignia con conteo de ítems que requieren acción (Maker-Checker + Router OFFLINE) y filtra ruido de sesión', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 'app-101',
            status: 'PENDING',
            summary: 'Eliminar regla de firewall crítica',
            router_id: 'r-1',
            router_name: 'Borde-Caracas',
            requested_by: 'usr-maker-2',
            requested_by_username: 'operador_l2',
            created_at: '2026-11-04T18:00:00Z',
          },
        ],
      },
    } as never);

    const inventoryStore = useInventoryStore();
    inventoryStore.routers = [
      {
        id: 'r-down-1',
        display_name: 'Core-Valencia',
        ip_address: '10.250.3.9',
        rest_port: 443,
        use_ssl: true,
        admin_state: 'PRODUCTION',
        last_reachability_status: 'OFFLINE',
        tags: [],
      },
    ] as never;

    const nocStore = useNocEventsStore();
    nocStore.recentEvents = [
      {
        id: 'ev-noise-1',
        type: 'MAINTENANCE',
        router_name: 'sinfallas',
        summary: 'Session token renewed (por sinfallas)',
        timestamp: '2026-11-04T18:01:00Z',
      },
      {
        id: 'ev-bgp-1',
        type: 'WARNING',
        router_id: 'r-1',
        router_name: 'Borde-Caracas',
        summary: 'Sesión BGP caída con upstream',
        timestamp: '2026-11-04T18:02:00Z',
      },
      {
        id: 'ev-bgp-2',
        type: 'WARNING',
        router_id: 'r-1',
        router_name: 'Borde-Caracas',
        summary: 'Sesión BGP caída con upstream',
        timestamp: '2026-11-04T18:03:00Z',
      },
    ];

    const wrapper = mount(RgNotificationCenterBell);
    await flushPromises();

    // 1 solicitud Maker-Checker + 1 router OFFLINE = 2 acciones requeridas
    const badge = wrapper.find('#notification-bell-badge');
    expect(badge.exists()).toBe(true);
    expect(badge.text()).toBe('2');

    await wrapper.find('#btn-notification-bell').trigger('click');
    await flushPromises();

    const text = wrapper.find('#rg-notification-popover').text();
    expect(text).toContain('Borde-Caracas');
    expect(text).toContain('Core-Valencia');
    // El ruido de "Session token renewed" jamás debe aparecer
    expect(text).not.toContain('Session token renewed');
    // Los 2 eventos BGP del mismo router se deduplican con ×2
    expect(text).toContain('×2');
  });

  it('permite aprobar en 1 clic desde la campana y reconocer (Ack) una caída sin borrar ítems no resueltos al marcar vistas', async () => {
    vi.mocked(http.get).mockResolvedValue({
      data: {
        items: [
          {
            id: 'app-202',
            status: 'PENDING',
            summary: 'Reinicio programado de nodo',
            router_id: 'r-1',
            router_name: 'r111',
            requested_by: 'usr-maker-9',
            requested_by_username: 'tecnico_noc',
            created_at: '2026-11-04T18:05:00Z',
          },
        ],
      },
    } as never);
    vi.mocked(http.post).mockResolvedValueOnce({ data: { status: 'APPROVED' } } as never);

    const inventoryStore = useInventoryStore();
    inventoryStore.routers = [
      {
        id: 'r-down-2',
        display_name: 'Nodo-Maracay',
        ip_address: '10.250.3.20',
        rest_port: 443,
        use_ssl: true,
        admin_state: 'PRODUCTION',
        last_reachability_status: 'OFFLINE',
        tags: [],
      },
    ] as never;

    const wrapper = mount(RgNotificationCenterBell);
    await flushPromises();

    await wrapper.find('#btn-notification-bell').trigger('click');
    await flushPromises();

    // Al hacer clic en "✓ Vistas", se reconocen las alertas de red pero la aprobación Maker-Checker sigue requiriendo firma
    await wrapper.find('#btn-notif-mark-all-read').trigger('click');
    expect(wrapper.find('#notification-bell-badge').text()).toBe('1');

    // Aprobar en 1 clic desde la fila de la campana
    const approveBtn = wrapper.find('.btn-inline-action--approve');
    expect(approveBtn.exists()).toBe(true);
    await approveBtn.trigger('click');
    await flushPromises();

    expect(http.post).toHaveBeenCalledWith(
      '/api/v1/operations/approvals/app-202/approve',
      expect.objectContaining({
        review_comment: expect.any(String),
      }),
    );
    expect(wrapper.find('#notification-bell-badge').exists()).toBe(false);
  });

  it('permite activar el modo Snooze de 30 minutos (🔕 30m) y navegar al hacer clic en una notificación', async () => {
    vi.mocked(http.get).mockResolvedValue({ data: { items: [] } } as never);
    const inventoryStore = useInventoryStore();
    inventoryStore.routers = [
      {
        id: 'r-maint-1',
        display_name: 'r111',
        ip_address: '10.250.3.8',
        rest_port: 443,
        use_ssl: true,
        admin_state: 'MAINTENANCE',
        last_reachability_status: 'ONLINE',
        tags: [],
      },
    ] as never;

    const wrapper = mount(RgNotificationCenterBell);
    await flushPromises();

    await wrapper.find('#btn-notification-bell').trigger('click');
    await wrapper.find('#btn-notif-snooze-30m').trigger('click');
    expect(wrapper.find('#btn-notification-bell').text()).toContain('🔕');

    const firstRow = wrapper.find('.notif-row');
    await firstRow.trigger('click');
    expect(pushMock).toHaveBeenCalledWith('/inventory/maintenance-windows');
  });
});
```

---

### Paso 5: Actualizar Escenario BDD en Karate Labs (`vue3/test/ui_business_flow.feature` y `docs/examples/vue3/test/ui_business_flow.feature.example`)

Añadir el **Escenario 89** al final de `vue3/test/ui_business_flow.feature` y replicarlo en `docs/examples/vue3/test/ui_business_flow.feature.example`:

```gherkin
  Scenario: 89. Centro Táctico de Notificaciones In-App en Barra Superior, Triaje Rápido y Reactividad Maker-Checker (Hito 30.3 y 30.4)
    Given driver baseUrl + '/inventory'
    And waitFor(".rg-header")
    And waitFor("#btn-notification-bell")
    When click("#btn-notification-bell")
    Then waitFor("#rg-notification-popover")
    And waitFor("#notif-tab-all")
    And waitFor("#notif-tab-action")
    And waitFor("#btn-notif-snooze-30m")
```

---

## 3. Comandos de Verificación en Contenedores Efímeros (`Rule Zero`)

```bash
# 1. Validar 0 componentes Vue huérfanos y 0 claves JSON duplicadas
python3 .agents/scripts/verify_zero_orphan_vue_components.py
python3 .agents/scripts/verify_json_no_duplicate_keys.py
python3 .agents/scripts/verify_no_orphan_api_endpoints.py

# 2. Ejecutar Vitest y vue-tsc en contenedor efímero
docker compose -f vue3/docker-compose.qa.yml run --rm --entrypoint sh vue3-qa -c \
  "pnpm exec vitest run src/components/common/RgNotificationCenterBell.unit.ts src/components/common/RgResponsiveShell.unit.ts && pnpm exec vue-tsc --noEmit"
```
