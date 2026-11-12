// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { useAuthStore } from '@/stores/useAuthStore';

export interface VersionCheckStatus {
  enabled: boolean;
  current_version: string;
  latest_version: string | null;
  update_available: boolean;
  release_url: string;
  release_name: string | null;
  published_at: string | null;
  last_checked_at: string | null;
  last_status: string;
}

export const useVersionCheckStore = defineStore('versionCheck', () => {
  const authStore = useAuthStore();

  const currentVersion = ref('1.3.0');
  const latestVersion = ref<string | null>(null);
  const updateAvailable = ref(false);
  const releaseUrl = ref('https://github.com/tecno-consultores/RoSGrid/releases');
  const releaseName = ref<string | null>(null);
  const publishedAt = ref<string | null>(null);
  const lastCheckedAt = ref<string | null>(null);
  const lastStatus = ref('pending');
  const isRefreshing = ref(false);

  const canSeeUpdateNotice = computed(() => {
    const role = authStore.currentRole || authStore.user?.role || '';
    return updateAvailable.value && ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR'].includes(role);
  });

  const canTriggerManualCheck = computed(() => {
    const role = authStore.currentRole || authStore.user?.role || '';
    return ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN'].includes(role);
  });

  function applyStatus(data: VersionCheckStatus): void {
    if (data.current_version) currentVersion.value = data.current_version;
    latestVersion.value = data.latest_version ?? null;
    updateAvailable.value = Boolean(data.update_available);
    if (data.release_url) releaseUrl.value = data.release_url;
    releaseName.value = data.release_name ?? null;
    publishedAt.value = data.published_at ?? null;
    lastCheckedAt.value = data.last_checked_at ?? null;
    lastStatus.value = data.last_status ?? 'ok';
  }

  async function fetchVersionStatus(): Promise<void> {
    try {
      const { http } = await import('@/api/httpClient');
      const res = await http.get<VersionCheckStatus>('/api/v1/system/version-check');
      if (res?.data) {
        applyStatus(res.data);
      }
    } catch {
      // Fail-silent en entornos aislados o tests sin backend
    }
  }

  async function refreshVersionCheck(): Promise<void> {
    isRefreshing.value = true;
    try {
      const { http } = await import('@/api/httpClient');
      const res = await http.post<VersionCheckStatus>('/api/v1/system/version-check/refresh', {});
      if (res?.data) {
        applyStatus(res.data);
      }
    } catch {
      // Fail-silent
    } finally {
      isRefreshing.value = false;
    }
  }

  return {
    currentVersion,
    latestVersion,
    updateAvailable,
    releaseUrl,
    releaseName,
    publishedAt,
    lastCheckedAt,
    lastStatus,
    isRefreshing,
    canSeeUpdateNotice,
    canTriggerManualCheck,
    applyStatus,
    fetchVersionStatus,
    refreshVersionCheck,
  };
});
