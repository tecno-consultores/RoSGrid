<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { http } from '@/api/httpClient';
import { useI18n } from '@/composables/useI18n';
import type { FleetCveSummary, CveItem, CveSyncResponse } from '@/types';

const { t } = useI18n();
const router = useRouter();

const loading = ref(false);
const syncing = ref(false);
const errorMessage = ref<string | null>(null);
const successMessage = ref<string | null>(null);

const cveSummary = ref<FleetCveSummary | null>(null);
const searchQuery = ref('');
const selectedSeverity = ref<string>('ALL');
const expandedCveId = ref<string | null>(null);

const isCacheFresh = computed<boolean>(() => {
  return cveSummary.value?.is_cache_fresh ?? true;
});

const cacheStatusText = computed<string>(() => {
  if (!cveSummary.value) return t('cve_matrix.cache_checking', 'Consultando estado del catálogo...');
  if (!cveSummary.value.is_cache_fresh) {
    return t('cve_matrix.cache_expired', 'Caché de boletines vencido (> 24h)');
  }
  if (cveSummary.value.cache_ttl_seconds != null) {
    const hours = Math.floor(cveSummary.value.cache_ttl_seconds / 3600);
    const minutes = Math.floor((cveSummary.value.cache_ttl_seconds % 3600) / 60);
    const validStr = t('cve_matrix.cache_valid', 'Caché oficial vigente');
    const expStr = t('cve_matrix.expires_in', 'expira en');
    if (hours > 0) {
      return `${validStr} (${expStr} ${hours}h ${minutes}m)`;
    }
    return `${validStr} (${expStr} ${minutes}m)`;
  }
  return t('cve_matrix.cache_active_24h', 'Caché oficial de 24 horas activo');
});

const lastSyncFormatted = computed<string>(() => {
  if (!cveSummary.value?.last_synced_at) return '';
  try {
    const d = new Date(cveSummary.value.last_synced_at);
    return d.toLocaleString([], {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
});

async function loadCveSummary(): Promise<void> {
  loading.value = true;
  errorMessage.value = null;
  try {
    const res = await http.get<FleetCveSummary>('/api/v1/inventory/cves');
    cveSummary.value = res.data;
    if (res.data.auto_synced) {
      successMessage.value =
        'Boletines CVE sincronizados automáticamente al ingresar por primera vez en el día. Caché de 24 horas activado.';
      setTimeout(() => {
        if (successMessage.value?.includes('automáticamente')) {
          successMessage.value = null;
        }
      }, 7000);
    }
  } catch (err: unknown) {
    const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
    errorMessage.value =
      errorObj.response?.data?.detail || errorObj.message || 'Error al cargar la matriz de vulnerabilidades.';
  } finally {
    loading.value = false;
  }
}

async function syncCveDatabase(): Promise<void> {
  syncing.value = true;
  errorMessage.value = null;
  successMessage.value = null;
  try {
    const res = await http.post<CveSyncResponse>('/api/v1/inventory/cves/sync');
    successMessage.value =
      res.data.message ||
      `Catálogo actualizado manualmente (${res.data.total_cves} CVEs). Caché renovado por 24 horas.`;
    await loadCveSummary();
  } catch (err: unknown) {
    const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
    errorMessage.value =
      errorObj.response?.data?.detail || errorObj.message || 'Fallo al sincronizar base de datos CVE.';
  } finally {
    syncing.value = false;
    if (successMessage.value) {
      setTimeout(() => {
        successMessage.value = null;
      }, 7000);
    }
  }
}

interface FlattenedCveRow {
  cve: CveItem;
  affectedRouters: Array<{
    id: string;
    display_name: string;
    ros_version: string | null;
  }>;
}

const uniqueCveRows = computed<FlattenedCveRow[]>(() => {
  if (!cveSummary.value || !cveSummary.value.vulnerable_routers) return [];

  const cveMap = new Map<string, FlattenedCveRow>();

  for (const r of cveSummary.value.vulnerable_routers) {
    for (const v of r.vulnerabilities) {
      if (!cveMap.has(v.cve_id)) {
        cveMap.set(v.cve_id, {
          cve: v,
          affectedRouters: [],
        });
      }
      cveMap.get(v.cve_id)?.affectedRouters.push({
        id: r.router_id,
        display_name: r.display_name,
        ros_version: r.ros_version,
      });
    }
  }

  let list = Array.from(cveMap.values());

  if (selectedSeverity.value !== 'ALL') {
    list = list.filter((row) => row.cve.severity === selectedSeverity.value);
  }

  const query = searchQuery.value.trim().toLowerCase();
  if (query) {
    list = list.filter(
      (row) =>
        row.cve.cve_id.toLowerCase().includes(query) ||
        row.cve.title.toLowerCase().includes(query) ||
        row.cve.affected_versions_expr.toLowerCase().includes(query) ||
        row.affectedRouters.some((ar) => ar.display_name.toLowerCase().includes(query)),
    );
  }

  return list;
});

const recommendedFleetVersion = computed<string>(() => {
  if (!cveSummary.value || !cveSummary.value.vulnerable_routers) return '7.16.2';
  for (const r of cveSummary.value.vulnerable_routers) {
    if (r.recommended_target_version) {
      return r.recommended_target_version;
    }
  }
  return '7.16.2';
});

const maxFleetCvss = computed<number>(() => {
  if (!cveSummary.value || !cveSummary.value.vulnerable_routers.length) return 0.0;
  return Math.max(...cveSummary.value.vulnerable_routers.map((r) => r.max_cvss_score || 0));
});

function toggleExpandCve(cveId: string): void {
  expandedCveId.value = expandedCveId.value === cveId ? null : cveId;
}

function navigateToBulkUpdates(): void {
  router.push('/bulk-ops');
}

function openRouterWebFig(routerId: string): void {
  router.push(`/routers/${routerId}/webfig/live`);
}

onMounted(() => {
  loadCveSummary();
});
</script>

<template>
  <main class="cve-matrix-view" aria-labelledby="cve-matrix-title">
    <!-- Encabezado de Vista -->
    <header class="cve-header">
      <div class="cve-header-text">
        <h1 id="cve-matrix-title" class="cve-title">{{ t('cve_matrix.title', 'Matriz de Vulnerabilidades CVE — Flota MikroTik') }}</h1>
        <p class="cve-subtitle">
          {{ t('cve_matrix.subtitle', 'Auditoría proactiva de boletines RouterOS v7 | Fuentes oficiales:') }}
          <a
            href="https://mikrotik.com/supportsec"
            target="_blank"
            rel="noopener noreferrer"
            class="cve-source-link"
          >MikroTik Security Advisories</a>
          {{ t('common.and', 'y') }}
          <a
            href="https://nvd.nist.gov/vuln/search?keyword=mikrotik&resultType=records"
            target="_blank"
            rel="noopener noreferrer"
            class="cve-source-link"
          >NIST NVD MikroTik</a>
        </p>
      </div>

      <div class="cve-actions">
        <button
          type="button"
          class="btn-sync-cve"
          :disabled="syncing"
          :aria-label="t('cve_matrix.btn_sync', 'Sincronizar Boletines')"
          :title="t('cve_matrix.cache_active_24h', 'Caché oficial de 24 horas activo')"
          data-testid="btn-sync-cve"
          @click="syncCveDatabase"
        >
          <span v-if="syncing" class="spinner-inline" aria-hidden="true"></span>
          <span v-else aria-hidden="true">🔄</span>
          <span>{{ syncing ? t('cve_matrix.syncing', 'Sincronizando...') : t('cve_matrix.btn_sync', 'Sincronizar Boletines') }}</span>
        </button>

        <button
          type="button"
          class="btn-remediate-fleet"
          :aria-label="t('cve_matrix.btn_remediate', 'Actualizar Flota Afectada')"
          data-testid="btn-remediate-fleet"
          @click="navigateToBulkUpdates"
        >
          <span aria-hidden="true">⚡</span>
          <span>{{ t('cve_matrix.btn_remediate', 'Actualizar Flota Afectada') }}</span>
        </button>
      </div>
    </header>

    <!-- Franja Táctica Prominente de Estado de Caché 24h y Gobernanza de Boletines -->
    <section class="cve-cache-strip cve-cache-bar" role="status" aria-live="polite">
      <div class="cache-strip-info">
        <span
          class="cve-cache-badge"
          :class="{ 'cve-cache-badge--fresh': isCacheFresh, 'cve-cache-badge--stale': !isCacheFresh }"
          data-testid="cve-cache-badge"
        >
          <span class="cache-dot" aria-hidden="true"></span>
          <span class="cache-label">{{ cacheStatusText }}</span>
          <span v-if="lastSyncFormatted" class="cache-date">• {{ t('cve_matrix.last_download', 'Última descarga:') }} {{ lastSyncFormatted }}</span>
        </span>
      </div>
      <div class="cache-strip-policy">
        <span class="policy-tag">{{ t('cve_matrix.ttl_policy', 'TTL: 24 Horas (KeyDB)') }}</span>
        <span class="policy-desc">{{ t('cve_matrix.ttl_policy_desc', 'Descarga remota en primer acceso diario • Reutilización anti-saturación') }}</span>
      </div>
    </section>

    <!-- Banners de Estado -->
    <div v-if="successMessage" class="banner-success" role="alert">
      <span aria-hidden="true">✅</span>
      <span>{{ successMessage }}</span>
    </div>

    <div v-if="errorMessage" class="banner-error" role="alert">
      <span aria-hidden="true">🚨</span>
      <span>{{ errorMessage }}</span>
    </div>

    <!-- Tiras KPI Tácticas -->
    <section class="kpi-grid" aria-label="Resumen de métricas de seguridad">
      <div class="kpi-card">
        <span class="kpi-label">{{ t('cve_matrix.kpi_evaluated', 'Routers Evaluados') }}</span>
        <span class="kpi-val">{{ cveSummary?.total_evaluated_routers ?? 0 }}</span>
        <span class="kpi-meta">{{ t('cve_matrix.kpi_total_meta', 'Inventario total adoptado') }}</span>
      </div>

      <div class="kpi-card kpi-card--warning">
        <span class="kpi-label">{{ t('cve_matrix.kpi_vulnerable', 'Routers Vulnerables') }}</span>
        <span class="kpi-val kpi-val--warning">{{ cveSummary?.vulnerable_routers_count ?? 0 }}</span>
        <span class="kpi-meta">
          {{ t('cve_matrix.kpi_critical', 'Críticos:') }} {{ cveSummary?.critical_routers_count ?? 0 }} | {{ t('cve_matrix.kpi_high', 'Altos:') }} {{ cveSummary?.high_routers_count ?? 0 }}
        </span>
      </div>

      <div class="kpi-card kpi-card--danger">
        <span class="kpi-label">{{ t('cve_matrix.kpi_cvss', 'Score CVSS Máximo') }}</span>
        <span class="kpi-val kpi-val--danger">{{ maxFleetCvss.toFixed(1) }}</span>
        <span class="kpi-meta">{{ t('cve_matrix.kpi_unique_bulletins', 'Boletines únicos:') }} {{ cveSummary?.total_unique_cves ?? 0 }}</span>
      </div>

      <div class="kpi-card kpi-card--cyan">
        <span class="kpi-label">{{ t('cve_matrix.kpi_recommended', 'Versión ROS Recomendada') }}</span>
        <span class="kpi-val kpi-val--cyan tabular-nums">{{ recommendedFleetVersion }}</span>
        <span class="kpi-meta">{{ t('cve_matrix.kpi_remedy_meta', 'Subsana 100% de los CVEs detectados') }}</span>
      </div>
    </section>

    <!-- Barra de Filtros y Controles -->
    <section class="cve-filters" aria-label="Filtros de búsqueda de vulnerabilidades">
      <div class="filter-item">
        <label for="cve-search" class="filter-label">{{ t('inventory.filter_search_label', 'Buscar Router:') }}</label>
        <input
          id="cve-search"
          v-model="searchQuery"
          type="text"
          class="input-search"
          :placeholder="t('cve_matrix.search_placeholder', 'Buscar CVE o Router...')"
        />
      </div>

      <div class="filter-item">
        <label for="cve-severity-filter" class="filter-label">{{ t('cve_matrix.th_severity', 'Severidad CVSS:') }}</label>
        <select id="cve-severity-filter" v-model="selectedSeverity" class="select-filter">
          <option value="ALL">{{ t('cve_matrix.severity_all', 'Todas las severidades') }}</option>
          <option value="CRITICAL">CRITICAL (>= 9.0)</option>
          <option value="HIGH">HIGH (7.0 - 8.9)</option>
          <option value="MEDIUM">MEDIUM (4.0 - 6.9)</option>
          <option value="LOW">LOW (&lt; 4.0)</option>
        </select>
      </div>

      <button
        type="button"
        class="btn-refresh"
        :disabled="loading"
        aria-label="Refrescar matriz de vulnerabilidades"
        @click="loadCveSummary"
      >
        <span aria-hidden="true">↻</span>
        <span>{{ t('inventory.btn_refresh', 'Refrescar') }}</span>
      </button>
    </section>

    <!-- Tabla Táctica de Vulnerabilidades -->
    <section class="table-container" aria-label="Tabla de vulnerabilidades CVE detectadas">
      <div v-if="loading && !cveSummary" class="loading-state">
        <span class="spinner" aria-hidden="true"></span>
        <p>{{ t('cve_matrix.loading_eval', 'Evaluando flota contra catálogo de vulnerabilidades...') }}</p>
      </div>

      <div v-else-if="uniqueCveRows.length === 0" class="empty-state">
        <span class="empty-icon" aria-hidden="true">🛡️</span>
        <p class="empty-title">{{ t('cve_matrix.empty_title', 'Flota libre de vulnerabilidades conocidas') }}</p>
        <p class="empty-sub">
          {{ t('cve_matrix.empty_desc', 'No se identificaron boletines CVE activos para los filtros seleccionados o los equipos operan con versiones seguras.') }}
        </p>
      </div>

      <table v-else class="cve-table">
        <thead>
          <tr>
            <th scope="col">{{ t('cve_matrix.th_cve', 'CVE ID') }}</th>
            <th scope="col">{{ t('cve_matrix.th_severity', 'Severidad') }}</th>
            <th scope="col">{{ t('cve_matrix.th_affected', 'Versiones Afectadas') }}</th>
            <th scope="col">{{ t('cve_matrix.th_fix', 'Versión Corregida') }}</th>
            <th scope="col">{{ t('cve_matrix.th_routers', 'Equipos Afectados') }}</th>
            <th scope="col">{{ t('inventory.col_actions', 'Acción') }}</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="row in uniqueCveRows" :key="row.cve.cve_id">
            <tr class="cve-row" :class="{ 'cve-row--expanded': expandedCveId === row.cve.cve_id }">
              <td class="cell-id">
                <span class="cve-id-badge tabular-nums">{{ row.cve.cve_id }}</span>
              </td>
              <td>
                <span
                  class="badge-severity"
                  :class="`badge-severity--${row.cve.severity.toLowerCase()}`"
                >
                  {{ row.cve.severity }} ({{ row.cve.cvss_score.toFixed(1) }})
                </span>
              </td>
              <td class="tabular-nums cell-versions">
                <code>{{ row.cve.affected_versions_expr }}</code>
              </td>
              <td class="tabular-nums cell-fixed">
                <span class="badge-fixed">>= {{ row.cve.fixed_in_version }}</span>
              </td>
              <td>
                <span class="badge-count">
                  {{ row.affectedRouters.length }} {{ row.affectedRouters.length === 1 ? t('cve_matrix.one_router', 'equipo') : t('cve_matrix.many_routers', 'equipos') }}
                </span>
              </td>
              <td>
                <button
                  type="button"
                  class="btn-toggle-details"
                  :aria-expanded="expandedCveId === row.cve.cve_id"
                  :aria-label="`Ver detalle de ${row.cve.cve_id}`"
                  @click="toggleExpandCve(row.cve.cve_id)"
                >
                  {{ expandedCveId === row.cve.cve_id ? t('cve_matrix.btn_hide', '▲ Ocultar') : t('cve_matrix.btn_details', '▼ Detalle') }}
                </button>
              </td>
            </tr>

            <!-- Fila Desplegable de Detalles -->
            <tr v-if="expandedCveId === row.cve.cve_id" class="cve-details-row">
              <td colspan="6" class="cell-details">
                <div class="cve-card-detail">
                  <div class="cve-detail-header">
                    <h2 class="cve-detail-title">{{ row.cve.title }}</h2>
                    <span class="cve-published">{{ t('cve_matrix.published', 'Publicado:') }} {{ row.cve.published_date }}</span>
                  </div>

                  <p class="cve-desc">{{ row.cve.description_es }}</p>

                  <div class="cve-remediation-box">
                    <strong class="remediation-title">{{ t('cve_matrix.remediation_title', 'Mitigación y Remediación Sugerida:') }}</strong>
                    <p class="remediation-text">{{ row.cve.remediation }}</p>
                  </div>

                  <div class="affected-routers-list">
                    <strong>{{ t('cve_matrix.fleet_affected_title', 'Routers de tu Flota con esta Vulnerabilidad:') }}</strong>
                    <div class="router-chips-wrap">
                      <button
                        v-for="r in row.affectedRouters"
                        :key="r.id"
                        type="button"
                        class="router-chip"
                        :aria-label="`Abrir WebFig de ${r.display_name}`"
                        @click="openRouterWebFig(r.id)"
                      >
                        <span class="chip-name">{{ r.display_name }}</span>
                        <span class="chip-ver tabular-nums">ROS: {{ r.ros_version || t('common.unknown', 'Desconocida') }}</span>
                        <span class="chip-arrow" aria-hidden="true">→</span>
                      </button>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </section>
  </main>
</template>

<style scoped>
.cve-matrix-view {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem;
  background-color: var(--rg-bg-canvas, #0b0f19);
  color: var(--rg-text-primary, #f8fafc);
  min-height: calc(100vh - 4rem);
}

.cve-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--rg-border-grid, #1e293b);
  padding-bottom: 1rem;
}

.cve-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--rg-text-primary, #f8fafc);
  margin: 0 0 0.25rem 0;
  letter-spacing: -0.01em;
}

.cve-subtitle {
  font-size: 0.875rem;
  color: var(--rg-text-secondary, #cbd5e1);
  margin: 0;
}

.cve-source-link {
  color: var(--rg-accent-cyan, #22d3ee);
  text-decoration: underline;
  text-underline-offset: 2px;
  font-weight: 500;
  transition: color 0.15s ease;
}

.cve-source-link:hover {
  color: var(--rg-cyan-300, #67e8f9);
}

.cve-cache-strip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.85rem;
  padding: 0.75rem 1.15rem;
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(34, 211, 238, 0.3);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
}

.cache-strip-info {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  flex-wrap: wrap;
}

.cache-strip-policy {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--rg-text-muted, #94a3b8);
}

.policy-tag {
  background: rgba(30, 41, 59, 0.95);
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  border: 1px solid var(--rg-border-grid, #334155);
  font-family: var(--rg-font-mono, monospace);
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--rg-accent-cyan, #22d3ee);
}

.policy-desc {
  font-size: 0.75rem;
  color: var(--rg-text-secondary, #94a3b8);
}

.cve-cache-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.3rem 0.75rem;
  border-radius: 9999px;
  background-color: rgba(30, 41, 59, 0.9);
  border: 1px solid var(--rg-border-grid, #334155);
  color: var(--rg-text-secondary, #cbd5e1);
  letter-spacing: 0.01em;
}

.cve-cache-badge--fresh {
  border-color: rgba(34, 211, 238, 0.35);
  color: var(--rg-accent-cyan, #22d3ee);
  background-color: rgba(6, 78, 59, 0.25);
}

.cve-cache-badge--stale {
  border-color: rgba(245, 158, 11, 0.4);
  color: #f59e0b;
}

.cache-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: var(--rg-accent-cyan, #22d3ee);
  box-shadow: 0 0 6px rgba(34, 211, 238, 0.6);
}

.cve-cache-badge--stale .cache-dot {
  background-color: #f59e0b;
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.6);
}

.cache-date {
  opacity: 0.85;
  font-size: 0.7rem;
  font-weight: 400;
}

.cve-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.btn-sync-cve,
.btn-remediate-fleet,
.btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid transparent;
}

.btn-sync-cve {
  background-color: var(--rg-bg-elevated, #1e293b);
  border-color: var(--rg-border-grid, #334155);
  color: var(--rg-accent-cyan, #22d3ee);
}

.btn-sync-cve:hover:not(:disabled) {
  background-color: var(--rg-border-grid, #334155);
  border-color: var(--rg-accent-cyan, #22d3ee);
}

.btn-remediate-fleet {
  background-color: #0284c7;
  color: #ffffff;
}

.btn-remediate-fleet:hover {
  background-color: #0369a1;
}

.btn-refresh {
  background-color: var(--rg-bg-surface, #111827);
  border-color: var(--rg-border-grid, #1e293b);
  color: var(--rg-text-secondary, #cbd5e1);
}

.btn-refresh:hover {
  border-color: var(--rg-accent-cyan, #22d3ee);
  color: var(--rg-accent-cyan, #22d3ee);
}

.banner-success,
.banner-error {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
}

.banner-success {
  background-color: rgba(16, 185, 129, 0.15);
  border: 1px solid #10b981;
  color: #34d399;
}

.banner-error {
  background-color: rgba(239, 68, 68, 0.15);
  border: 1px solid #ef4444;
  color: #f87171;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.kpi-card {
  background-color: var(--rg-bg-surface, #111827);
  border: 1px solid var(--rg-border-grid, #1e293b);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
}

.kpi-card--warning {
  border-color: rgba(245, 158, 11, 0.4);
}

.kpi-card--danger {
  border-color: rgba(239, 68, 68, 0.4);
}

.kpi-card--cyan {
  border-color: rgba(34, 211, 238, 0.4);
}

.kpi-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--rg-text-muted, #94a3b8);
}

.kpi-val {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0.25rem 0;
  color: var(--rg-text-primary, #f8fafc);
  font-variant-numeric: tabular-nums;
}

.kpi-val--warning {
  color: #f59e0b;
}

.kpi-val--danger {
  color: #ef4444;
}

.kpi-val--cyan {
  color: var(--rg-accent-cyan, #22d3ee);
}

.kpi-meta {
  font-size: 0.75rem;
  color: var(--rg-text-secondary, #cbd5e1);
}

.cve-filters {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  flex-wrap: wrap;
  background-color: var(--rg-bg-surface, #111827);
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid var(--rg-border-grid, #1e293b);
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.filter-label {
  font-size: 0.75rem;
  color: var(--rg-text-secondary, #cbd5e1);
}

.input-search,
.select-filter {
  background-color: var(--rg-bg-canvas, #0b0f19);
  border: 1px solid var(--rg-border-grid, #1e293b);
  border-radius: 6px;
  color: var(--rg-text-primary, #f8fafc);
  padding: 0.45rem 0.75rem;
  font-size: 0.875rem;
  outline: none;
}

.input-search:focus,
.select-filter:focus {
  border-color: var(--rg-accent-cyan, #22d3ee);
}

.table-container {
  background-color: var(--rg-bg-surface, #111827);
  border: 1px solid var(--rg-border-grid, #1e293b);
  border-radius: 8px;
  overflow-x: auto;
}

.cve-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.875rem;
}

.cve-table th {
  background-color: var(--rg-bg-elevated, #1e293b);
  color: var(--rg-text-secondary, #cbd5e1);
  padding: 0.65rem 1rem;
  border-bottom: 1px solid var(--rg-border-grid, #334155);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
}

.cve-row {
  border-bottom: 1px solid var(--rg-border-grid, #1e293b);
  transition: background-color 0.15s ease;
}

.cve-row:hover {
  background-color: rgba(34, 211, 238, 0.04);
}

.cve-row td {
  padding: 0.75rem 1rem;
  vertical-align: middle;
}

.cve-id-badge {
  font-weight: 700;
  color: var(--rg-accent-cyan, #22d3ee);
  font-family: 'JetBrains Mono', monospace;
}

.badge-severity {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  text-transform: uppercase;
}

.badge-severity--critical {
  background-color: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border: 1px solid #ef4444;
}

.badge-severity--high {
  background-color: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  border: 1px solid #f59e0b;
}

.badge-severity--medium {
  background-color: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border: 1px solid #3b82f6;
}

.badge-severity--low {
  background-color: rgba(148, 163, 184, 0.2);
  color: #cbd5e1;
  border: 1px solid #94a3b8;
}

.badge-fixed {
  background-color: rgba(16, 185, 129, 0.15);
  color: #34d399;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
}

.badge-count {
  background-color: var(--rg-bg-canvas, #0b0f19);
  border: 1px solid var(--rg-border-grid, #1e293b);
  color: var(--rg-text-primary, #f8fafc);
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
}

.btn-toggle-details {
  background: transparent;
  border: 1px solid var(--rg-border-grid, #334155);
  color: var(--rg-accent-cyan, #22d3ee);
  border-radius: 4px;
  padding: 0.3rem 0.6rem;
  font-size: 0.75rem;
  cursor: pointer;
}

.btn-toggle-details:hover {
  background-color: var(--rg-border-grid, #334155);
}

.cve-details-row {
  background-color: var(--rg-bg-canvas, #0b0f19);
}

.cell-details {
  padding: 1.25rem;
}

.cve-card-detail {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  border-left: 3px solid var(--rg-accent-cyan, #22d3ee);
  padding-left: 1rem;
}

.cve-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cve-detail-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--rg-text-primary, #f8fafc);
  margin: 0;
}

.cve-published {
  font-size: 0.75rem;
  color: var(--rg-text-muted, #94a3b8);
}

.cve-desc {
  font-size: 0.875rem;
  color: var(--rg-text-secondary, #cbd5e1);
  margin: 0;
  line-height: 1.4;
}

.cve-remediation-box {
  background-color: rgba(34, 211, 238, 0.05);
  border: 1px solid rgba(34, 211, 238, 0.2);
  border-radius: 6px;
  padding: 0.75rem;
}

.remediation-title {
  color: var(--rg-accent-cyan, #22d3ee);
  display: block;
  font-size: 0.8rem;
  margin-bottom: 0.25rem;
}

.remediation-text {
  font-size: 0.825rem;
  margin: 0;
  color: var(--rg-text-primary, #f8fafc);
}

.affected-routers-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.router-chips-wrap {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.router-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background-color: var(--rg-bg-surface, #111827);
  border: 1px solid var(--rg-border-grid, #334155);
  color: var(--rg-text-primary, #f8fafc);
  padding: 0.35rem 0.65rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.15s ease;
}

.router-chip:hover {
  border-color: var(--rg-accent-cyan, #22d3ee);
  color: var(--rg-accent-cyan, #22d3ee);
}

.chip-ver {
  color: var(--rg-text-muted, #94a3b8);
  font-size: 0.75rem;
}

.chip-arrow {
  color: var(--rg-accent-cyan, #22d3ee);
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid rgba(34, 211, 238, 0.2);
  border-top-color: var(--rg-accent-cyan, #22d3ee);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 1rem;
}

.spinner-inline {
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
  font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
}
</style>
