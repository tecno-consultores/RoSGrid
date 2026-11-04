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

  function populateApprovalNotifications(itemsMap: Map<string, TacticalNotificationItem>): void {
    if (!isCheckerAuthorized.value) return;
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

  function createRouterNotification(r: (typeof inventoryStore.routers)[number]): TacticalNotificationItem | null {
    if (r.admin_state === 'MAINTENANCE') {
      const dedupKey = `router-maint:${r.id}`;
      return {
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
      };
    }

    const isOffline =
      r.last_reachability_status === 'OFFLINE' ||
      (!r.is_reachable && r.operational_status !== 'ONLINE');
    if (isOffline) {
      const dedupKey = `router-offline:${r.id}`;
      return {
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
        requiresAction: !ackedKeys.value.has(dedupKey),
        routerId: r.id,
      };
    }

    const isTofu =
      r.last_reachability_status === 'TOFU_ALERT' ||
      r.ssl_trust_status === 'FINGERPRINT_MISMATCH';
    if (isTofu) {
      const dedupKey = `router-tofu:${r.id}`;
      return {
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
        requiresAction: !ackedKeys.value.has(dedupKey),
        routerId: r.id,
      };
    }

    return null;
  }

  function populateInventoryNotifications(itemsMap: Map<string, TacticalNotificationItem>): void {
    for (const r of inventoryStore.routers) {
      const item = createRouterNotification(r);
      if (item) {
        itemsMap.set(item.dedupKey, item);
      }
    }
  }

  function isNocNoise(rawAction: string, rawSummary: string): boolean {
    return NOISE_ACTIONS.has(rawAction) || rawSummary.toLowerCase().includes('session token renewed');
  }

  function resolveNocRouterLabel(ev: (typeof nocStore.recentEvents)[number]): string {
    if (ev.routerDisplayName && !isUuidLike(ev.routerDisplayName)) {
      return ev.routerDisplayName;
    }
    if (ev.router_name && !isUuidLike(ev.router_name)) {
      return ev.router_name;
    }
    return 'Sistema RoSGrid';
  }

  function isNocCritical(ev: (typeof nocStore.recentEvents)[number], rawAction: string): boolean {
    if (ev.severity === 'CRITICAL' || ev.type === 'CRITICAL') return true;
    return rawAction.includes('DOWN') || rawAction.includes('OUTAGE');
  }

  function createNocEventNotification(
    ev: (typeof nocStore.recentEvents)[number],
    rawAction: string,
    rawSummary: string,
    dedupKey: string,
  ): TacticalNotificationItem {
    const isCritical = isNocCritical(ev, rawAction);
    const isMaintenance = ev.type === 'MAINTENANCE' || rawAction.includes('MAINTENANCE');
    const isAcked = ackedKeys.value.has(dedupKey);
    const routerLabel = resolveNocRouterLabel(ev);
    const eventTimestamp = ev.timestampIso || ev.timestamp || new Date().toISOString();

    let category: 'network' | 'ops' = 'ops';
    let priority: 'P1' | 'P2' | 'P3' = 'P3';
    let icon = '📡';
    let targetPath = '/inventory';

    if (isCritical) {
      category = 'network';
      priority = 'P1';
      icon = '🚨';
      targetPath = '/noc-wallboard';
    } else if (isMaintenance) {
      priority = 'P2';
      icon = '🛠️';
      targetPath = '/inventory/maintenance-windows';
    }

    return {
      id: ev.id || dedupKey,
      dedupKey,
      category,
      priority,
      icon,
      title: routerLabel,
      subtitle: rawSummary,
      timestamp: eventTimestamp,
      repeatCount: 1,
      targetPath,
      requiresAction: isCritical && !isAcked,
      routerId: ev.routerId || ev.router_id || undefined,
    };
  }

  function populateNocEventNotifications(itemsMap: Map<string, TacticalNotificationItem>): void {
    for (const ev of nocStore.recentEvents) {
      const rawAction = String(ev.eventName || ev.type || '').toUpperCase();
      const rawSummary = String(ev.message || ev.summary || '');
      if (isNocNoise(rawAction, rawSummary)) continue;

      const routerLabel = resolveNocRouterLabel(ev);
      const routerId = ev.routerId || ev.router_id || '';
      const eventTimestamp = ev.timestampIso || ev.timestamp || new Date().toISOString();
      const dedupKey = `ev:${rawAction}:${routerId || routerLabel}`;
      const existing = itemsMap.get(dedupKey);

      if (existing) {
        existing.repeatCount += 1;
        if (eventTimestamp > existing.timestamp) {
          existing.timestamp = eventTimestamp;
        }
        continue;
      }

      itemsMap.set(dedupKey, createNocEventNotification(ev, rawAction, rawSummary, dedupKey));
    }
  }

  function compareNotificationItems(a: TacticalNotificationItem, b: TacticalNotificationItem): number {
    if (a.requiresAction !== b.requiresAction) {
      return a.requiresAction ? -1 : 1;
    }
    const prioOrder = { P1: 0, P2: 1, P3: 2 };
    if (prioOrder[a.priority] !== prioOrder[b.priority]) {
      return prioOrder[a.priority] - prioOrder[b.priority];
    }
    return b.timestamp.localeCompare(a.timestamp);
  }

  const allNotifications = computed<TacticalNotificationItem[]>(() => {
    const itemsMap = new Map<string, TacticalNotificationItem>();
    populateApprovalNotifications(itemsMap);
    populateInventoryNotifications(itemsMap);
    populateNocEventNotifications(itemsMap);
    return Array.from(itemsMap.values()).sort(compareNotificationItems);
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
