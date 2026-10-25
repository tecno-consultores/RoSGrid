<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { computed, ref } from 'vue';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';
  import type { TenantFeatureFlags } from '@/types';

  const authStore = useAuthStore();

  const emit = defineEmits<{
    (e: 'completed'): void;
  }>();

  type Archetype = 'CORPORATE' | 'ISP' | 'CUSTOM';
  const selectedArchetype = ref<Archetype>('CORPORATE');
  const saving = ref(false);
  const errorMessage = ref('');

  // Formulario reactivo de feature flags
  const form = ref<TenantFeatureFlags>({
    isp_module_enabled: false,
    bgp_looking_glass_enabled: false,
    sfp_ddm_telemetry_enabled: false,
    ipfix_analytics_enabled: false,
    enforce_maker_checker: true,
    auto_safemode_enforced: true,
    ai_mcp_integration_enabled: true,
    nightly_backups_enabled: true,
    outbound_webhooks_enabled: true,
    config_drift_monitoring_enabled: true,
    cis_audit_enabled: true,
    sdwan_orchestrator_enabled: true,
    capsman_wifi_enabled: true,
    sla_tracker_enabled: true,
    mass_outage_threshold: 3,
    default_locale: 'es',
    l2_topology_enabled: true,
    syslog_collector_enabled: true,
    cve_scanner_enabled: true,
    prometheus_fleet_exporter_enabled: true,
    onboarding_completed: true,
  });

  function selectArchetype(archetype: Archetype) {
    selectedArchetype.value = archetype;
    if (archetype === 'CORPORATE') {
      form.value.isp_module_enabled = false;
      form.value.bgp_looking_glass_enabled = false;
      form.value.sfp_ddm_telemetry_enabled = false;
      form.value.ipfix_analytics_enabled = false;
      form.value.config_drift_monitoring_enabled = true;
      form.value.cis_audit_enabled = true;
      form.value.sdwan_orchestrator_enabled = true;
      form.value.capsman_wifi_enabled = true;
      form.value.sla_tracker_enabled = true;
      form.value.auto_safemode_enforced = true;
      form.value.enforce_maker_checker = true;
    } else if (archetype === 'ISP') {
      form.value.isp_module_enabled = true;
      form.value.bgp_looking_glass_enabled = true;
      form.value.sfp_ddm_telemetry_enabled = true;
      form.value.ipfix_analytics_enabled = true;
      form.value.config_drift_monitoring_enabled = true;
      form.value.cis_audit_enabled = true;
      form.value.sdwan_orchestrator_enabled = true;
      form.value.capsman_wifi_enabled = false;
      form.value.sla_tracker_enabled = true;
      form.value.auto_safemode_enforced = true;
      form.value.enforce_maker_checker = false;
    }
  }

  const tenantName = computed(() => authStore.user?.tenant_slug || 'Tenant Principal');

  async function handleCompleteOnboarding() {
    const tid = authStore.user?.tenant_id;
    if (!tid) return;

    saving.value = true;
    errorMessage.value = '';

    try {
      const payload = {
        ...form.value,
        onboarding_completed: true,
      };

      await http.patch(`/api/v1/tenants/${tid}/features`, payload);
      authStore.updateTenantFeatures(payload);
      emit('completed');
    } catch (err: any) {
      console.error('Error completando onboarding:', err);
      errorMessage.value =
        err?.response?.data?.detail || 'Error al persistir la configuración inicial del tenant.';
    } finally {
      saving.value = false;
    }
  }
</script>

<template>
  <div
    class="onboarding-backdrop"
    role="dialog"
    aria-modal="true"
    aria-labelledby="onboarding-modal-title"
  >
    <div class="onboarding-card">
      <header class="onboarding-header">
        <div class="header-icon-wrap">
          <span class="header-icon" aria-hidden="true">🌐</span>
        </div>
        <div>
          <h2 id="onboarding-modal-title" class="onboarding-title">
            Configuración Inicial de Despliegue — RoSGrid
          </h2>
          <p class="onboarding-subtitle">
            Bienvenido, Administrador. Configura los módulos y políticas operativas activas para
            <strong>{{ tenantName }}</strong>.
          </p>
        </div>
      </header>

      <div class="onboarding-body">
        <div v-if="errorMessage" class="onboarding-alert-error" role="alert">
          <span>⚠️</span>
          <span>{{ errorMessage }}</span>
        </div>

        <section class="archetype-section">
          <h3 class="section-title">1. Selecciona el Tipo de Operación de tu Red</h3>
          <div class="archetype-grid" role="radiogroup" aria-label="Arquetipo de red">
            <!-- Corporación -->
            <button
              type="button"
              class="archetype-card"
              :class="{ 'is-selected': selectedArchetype === 'CORPORATE' }"
              role="radio"
              :aria-checked="selectedArchetype === 'CORPORATE'"
              @click="selectArchetype('CORPORATE')"
            >
              <div class="archetype-badge">Recomendado</div>
              <span class="archetype-emoji" aria-hidden="true">🏢</span>
              <strong class="archetype-name">Corporativo / Empresa</strong>
              <p class="archetype-desc">
                Ideal para sucursales, campus y oficinas. Optimizado para seguridad de control plane,
                Wi-Fi CAPsMAN, túneles SD-WAN, auditoría WORM y Drift.
              </p>
              <ul class="feature-bullets">
                <li>✓ CIS Hardening & WORM</li>
                <li>✓ Config Drift & Baselines</li>
                <li>✓ Wi-Fi CAPsMAN & SD-WAN</li>
                <li>✓ Matriz de CVEs en Flota</li>
              </ul>
            </button>

            <!-- ISP -->
            <button
              type="button"
              class="archetype-card"
              :class="{ 'is-selected': selectedArchetype === 'ISP' }"
              role="radio"
              :aria-checked="selectedArchetype === 'ISP'"
              @click="selectArchetype('ISP')"
            >
              <div class="archetype-badge">Proveedores</div>
              <span class="archetype-emoji" aria-hidden="true">🌐</span>
              <strong class="archetype-name">Proveedor ISP / WISP</strong>
              <p class="archetype-desc">
                Optimizado para distribución de ancho de banda masivo, gestión de clientes,
                Looking Glass BGP, telemetría óptica SFP DDM y analítica IPFIX.
              </p>
              <ul class="feature-bullets">
                <li>✓ Gestión de Clientes ISP & Planes</li>
                <li>✓ BGP Looking Glass & Prefix Limits</li>
                <li>✓ Telemetría Óptica SFP DDM</li>
                <li>✓ Analítica de Flujo IPFIX</li>
              </ul>
            </button>

            <!-- Personalizado -->
            <button
              type="button"
              class="archetype-card"
              :class="{ 'is-selected': selectedArchetype === 'CUSTOM' }"
              role="radio"
              :aria-checked="selectedArchetype === 'CUSTOM'"
              @click="selectArchetype('CUSTOM')"
            >
              <span class="archetype-emoji" aria-hidden="true">⚙️</span>
              <strong class="archetype-name">Personalizado</strong>
              <p class="archetype-desc">
                Configura manualmente cada módulo y feature flag de la plataforma para adaptar
                exactamente el ecosistema a requerimientos específicos.
              </p>
              <ul class="feature-bullets">
                <li>✓ Ajuste fino de 15+ módulos</li>
                <li>✓ Configuración de Gobernanza</li>
                <li>✓ Safe Mode & Maker-Checker</li>
                <li>✓ Monitoreo y Telemetría</li>
              </ul>
            </button>
          </div>
        </section>

        <!-- Detalle de Feature Flags si es personalizado o inspección -->
        <section v-if="selectedArchetype === 'CUSTOM'" class="custom-flags-section">
          <h3 class="section-title">2. Personalización Fina de Feature Flags</h3>
          <div class="flags-grid">
            <label class="flag-item">
              <input v-model="form.isp_module_enabled" type="checkbox" class="tactical-checkbox" />
              <div>
                <strong>Módulo de Clientes ISP & Suscripciones</strong>
                <small>Habilita la administración de abonados y planes de velocidad</small>
              </div>
            </label>

            <label class="flag-item">
              <input v-model="form.bgp_looking_glass_enabled" type="checkbox" class="tactical-checkbox" />
              <div>
                <strong>BGP Looking Glass</strong>
                <small>Consultas en vivo de tablas BGP y estado de peers</small>
              </div>
            </label>

            <label class="flag-item">
              <input v-model="form.sfp_ddm_telemetry_enabled" type="checkbox" class="tactical-checkbox" />
              <div>
                <strong>Telemetría Óptica SFP DDM</strong>
                <small>Monitoreo de potencia óptica Rx/Tx y temperatura</small>
              </div>
            </label>

            <label class="flag-item">
              <input v-model="form.ipfix_analytics_enabled" type="checkbox" class="tactical-checkbox" />
              <div>
                <strong>Analítica IPFIX / NetFlow</strong>
                <small>Recopilación y visualización de flujos de tráfico L3/L4</small>
              </div>
            </label>

            <label class="flag-item">
              <input v-model="form.cis_audit_enabled" type="checkbox" class="tactical-checkbox" />
              <div>
                <strong>Auditoría CIS Hardening</strong>
                <small>Escaneo y auto-endurecimiento de directivas CIS en routers</small>
              </div>
            </label>

            <label class="flag-item">
              <input v-model="form.config_drift_monitoring_enabled" type="checkbox" class="tactical-checkbox" />
              <div>
                <strong>Monitoreo de Config Drift</strong>
                <small>Detección de desvíos contra plantillas homologadas Golden</small>
              </div>
            </label>

            <label class="flag-item">
              <input v-model="form.sdwan_orchestrator_enabled" type="checkbox" class="tactical-checkbox" />
              <div>
                <strong>Orquestador SD-WAN WireGuard</strong>
                <small>Topologías Hub-and-Spoke automáticas y túneles cifrados</small>
              </div>
            </label>

            <label class="flag-item">
              <input v-model="form.capsman_wifi_enabled" type="checkbox" class="tactical-checkbox" />
              <div>
                <strong>Gestor Wi-Fi CAPsMAN</strong>
                <small>Aprovisionamiento de SSIDs centralizado y monitoreo de APs</small>
              </div>
            </label>

            <label class="flag-item">
              <input v-model="form.enforce_maker_checker" type="checkbox" class="tactical-checkbox" />
              <div>
                <strong>Gobernanza Maker-Checker (4 Ojos)</strong>
                <small>Requiere aprobación de segundo operador para comandos críticos</small>
              </div>
            </label>

            <label class="flag-item">
              <input v-model="form.auto_safemode_enforced" type="checkbox" class="tactical-checkbox" />
              <div>
                <strong>Safe Mode Automático (60 segundos)</strong>
                <small>Protección contra cortes de conectividad accidental</small>
              </div>
            </label>
          </div>
        </section>
      </div>

      <footer class="onboarding-footer">
        <div class="footer-note text-subtle text-xs">
          Podrás modificar estas configuraciones posteriormente desde <em>Administración → Tenants</em>.
        </div>
        <button
          id="btn-confirm-onboarding"
          type="button"
          class="onboarding-submit-btn"
          :disabled="saving"
          @click="handleCompleteOnboarding"
        >
          <span v-if="saving">⏳ Aplicando configuración...</span>
          <span v-else>🚀 Comenzar con Perfil {{ selectedArchetype === 'CORPORATE' ? 'Corporativo' : selectedArchetype === 'ISP' ? 'ISP' : 'Personalizado' }}</span>
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
  .onboarding-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(2, 5, 11, 0.88);
    backdrop-filter: blur(8px);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1.5rem;
    animation: fadeIn 0.25s ease-out;
  }

  .onboarding-card {
    background: #080f1d;
    border: 1px solid #1a2a40;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7), 0 0 30px rgba(0, 229, 255, 0.1);
    border-radius: 12px;
    width: 100%;
    max-width: 920px;
    max-height: 92vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .onboarding-header {
    display: flex;
    align-items: center;
    gap: 1.25rem;
    padding: 1.5rem 2rem;
    background: #050a14;
    border-bottom: 1px solid #1a2a40;
  }

  .header-icon-wrap {
    width: 52px;
    height: 52px;
    background: rgba(0, 229, 255, 0.1);
    border: 1px solid rgba(0, 229, 255, 0.3);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .header-icon {
    font-size: 1.75rem;
  }

  .onboarding-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0;
  }

  .onboarding-subtitle {
    font-size: 0.85rem;
    color: #94a3b8;
    margin: 0.25rem 0 0 0;
  }

  .onboarding-subtitle strong {
    color: #00e5ff;
  }

  .onboarding-body {
    padding: 1.75rem 2rem;
    overflow-y: auto;
    flex: 1;
  }

  .onboarding-alert-error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1.25rem;
  }

  .section-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #cbd5e1;
    margin: 0 0 1rem 0;
  }

  .archetype-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .archetype-card {
    background: #04070e;
    border: 1px solid #1a2a40;
    border-radius: 8px;
    padding: 1.25rem;
    text-align: left;
    cursor: pointer;
    position: relative;
    display: flex;
    flex-direction: column;
    transition: all 0.2s ease;
  }

  .archetype-card:hover {
    border-color: #00e5ff;
    transform: translateY(-2px);
    background: #070e1b;
  }

  .archetype-card.is-selected {
    border-color: #00e5ff;
    background: rgba(0, 229, 255, 0.05);
    box-shadow: 0 0 15px rgba(0, 229, 255, 0.2);
  }

  .archetype-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    background: rgba(0, 229, 255, 0.15);
    color: #00e5ff;
    border: 1px solid rgba(0, 229, 255, 0.3);
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
  }

  .archetype-emoji {
    font-size: 2rem;
    margin-bottom: 0.75rem;
  }

  .archetype-name {
    font-size: 0.95rem;
    color: #e2e8f0;
    margin-bottom: 0.4rem;
  }

  .archetype-desc {
    font-size: 0.75rem;
    color: #94a3b8;
    line-height: 1.35;
    margin-bottom: 0.75rem;
    flex: 1;
  }

  .feature-bullets {
    list-style: none;
    padding: 0;
    margin: 0;
    font-size: 0.75rem;
    color: #38bdf8;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    border-top: 1px solid #1a2a40;
    padding-top: 0.6rem;
  }

  .custom-flags-section {
    background: #04070e;
    border: 1px solid #1a2a40;
    border-radius: 8px;
    padding: 1.25rem;
    margin-top: 1rem;
  }

  .flags-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  .flag-item {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    background: #080f1d;
    border: 1px solid #1a2a40;
    border-radius: 6px;
    padding: 0.6rem 0.75rem;
    cursor: pointer;
    font-size: 0.8rem;
  }

  .flag-item strong {
    display: block;
    color: #e2e8f0;
  }

  .flag-item small {
    display: block;
    color: #94a3b8;
    font-size: 0.7rem;
    line-height: 1.2;
    margin-top: 0.15rem;
  }

  .tactical-checkbox {
    width: 1.1rem;
    height: 1.1rem;
    cursor: pointer;
    accent-color: #00e5ff;
    margin-top: 0.1rem;
  }

  .onboarding-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem 2rem;
    background: #050a14;
    border-top: 1px solid #1a2a40;
  }

  .onboarding-submit-btn {
    background: #00e5ff;
    color: #04070e;
    font-weight: 700;
    font-size: 0.9rem;
    padding: 0.65rem 1.5rem;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .onboarding-submit-btn:hover:not(:disabled) {
    background: #38bdf8;
    box-shadow: 0 0 15px rgba(0, 229, 255, 0.4);
  }

  .onboarding-submit-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @media (max-width: 768px) {
    .archetype-grid {
      grid-template-columns: 1fr;
    }
    .flags-grid {
      grid-template-columns: 1fr;
    }
    .onboarding-footer {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;
    }
    .onboarding-submit-btn {
      width: 100%;
    }
  }
</style>
