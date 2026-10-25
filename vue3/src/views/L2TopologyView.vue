<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRouter } from 'vue-router';
import { http } from '@/api/httpClient';
import { useI18n } from '@/composables/useI18n';
import type { L2TopologyResponse, TopologyNode, TopologyEdge } from '@/types';

const router = useRouter();
const { t } = useI18n();

const loading = ref(false);
const errorMessage = ref<string | null>(null);
const topologyData = ref<L2TopologyResponse | null>(null);

const searchQuery = ref('');
const onlyPoeFilter = ref(false);

const selectedNode = ref<TopologyNode | null>(null);
const selectedEdge = ref<TopologyEdge | null>(null);

const canvasRef = ref<HTMLCanvasElement | null>(null);
let animationFrameId: number | null = null;

// Parámetros de transformación del Canvas (Pan y Zoom)
const zoomLevel = ref(1.0);
const panOffset = ref({ x: 0, y: 0 });
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const draggedNode = ref<TopologyNode | null>(null);

async function loadTopology(forceRefresh = false): Promise<void> {
  loading.value = true;
  errorMessage.value = null;
  try {
    const url = forceRefresh ? '/api/v1/topology/l2?refresh=true' : '/api/v1/topology/l2';
    const res = await http.get<L2TopologyResponse>(url);
    topologyData.value = res.data;
    initNodePositions();
    requestDraw();
  } catch (err: unknown) {
    const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
    errorMessage.value = errorObj.response?.data?.detail || errorObj.message || 'Error al cargar la topología física Layer 2.';
  } finally {
    loading.value = false;
  }
}

function initNodePositions(): void {
  if (!topologyData.value || topologyData.value.nodes.length === 0) return;
  const nodes = topologyData.value.nodes;
  const canvas = canvasRef.value;
  const width = canvas ? canvas.clientWidth : 800;
  const height = canvas ? canvas.clientHeight : 600;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.38;

  // Organizar jerárquicamente o en círculo
  nodes.forEach((node, idx) => {
    if (node.x === undefined || node.y === undefined) {
      const angle = (idx / nodes.length) * 2 * Math.PI;
      // Los PSE tienden al centro superior, las hojas abajo
      if (node.is_pse) {
        node.x = centerX + (radius * 0.5) * Math.cos(angle);
        node.y = centerY * 0.7 + (radius * 0.5) * Math.sin(angle);
      } else {
        node.x = centerX + radius * Math.cos(angle);
        node.y = centerY + radius * Math.sin(angle);
      }
    }
  });
}

const filteredNodes = computed<TopologyNode[]>(() => {
  if (!topologyData.value) return [];
  const q = searchQuery.value.trim().toLowerCase();
  return topologyData.value.nodes.filter((n) => {
    const matchesQ =
      !q ||
      n.display_name.toLowerCase().includes(q) ||
      n.ros_identity.toLowerCase().includes(q) ||
      n.ip_address.includes(q);
    if (!matchesQ) return false;
    if (onlyPoeFilter.value) {
      // Mostrar solo si es PSE o si está conectado a un enlace PoE
      return (
        n.is_pse ||
        topologyData.value?.edges.some(
          (e) => (e.source_router_id === n.id || e.target_router_id === n.id) && e.is_poe_delivering,
        )
      );
    }
    return true;
  });
});

const filteredEdges = computed<TopologyEdge[]>(() => {
  if (!topologyData.value) return [];
  const validNodeIds = new Set(filteredNodes.value.map((n) => n.id));
  return topologyData.value.edges.filter((e) => {
    const connectsVisible = validNodeIds.has(e.source_router_id) && validNodeIds.has(e.target_router_id);
    return connectsVisible && (!onlyPoeFilter.value || e.is_poe_delivering);
  });
});

function requestDraw(): void {
  if (typeof window === 'undefined') return;
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId);
  }
  animationFrameId = requestAnimationFrame(drawCanvas);
}

function drawEdgePoeBadge(
  ctx: CanvasRenderingContext2D,
  watts: number,
  midX: number,
  midY: number,
): void {
  ctx.fillStyle = '#111827';
  ctx.fillRect(midX - 28, midY - 10, 56, 18);
  ctx.strokeStyle = '#FACC15';
  ctx.lineWidth = 1;
  ctx.strokeRect(midX - 28, midY - 10, 56, 18);

  ctx.fillStyle = '#FACC15';
  ctx.font = '10px "JetBrains Mono", monospace';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(`⚡ ${watts.toFixed(1)}W`, midX, midY - 1);
}

function drawTopologyEdge(
  ctx: CanvasRenderingContext2D,
  edge: TopologyEdge,
  src: TopologyNode,
  dst: TopologyNode,
  isSelected: boolean,
): void {
  const sx = src.x ?? 0;
  const sy = src.y ?? 0;
  const dx = dst.x ?? 0;
  const dy = dst.y ?? 0;

  ctx.beginPath();
  ctx.moveTo(sx, sy);
  ctx.lineTo(dx, dy);

  if (edge.is_poe_delivering) {
    ctx.strokeStyle = isSelected ? '#38BDF8' : '#FACC15';
    ctx.lineWidth = isSelected ? 3.5 : 2.5;
  } else {
    ctx.strokeStyle = isSelected ? '#22D3EE' : '#334155';
    ctx.lineWidth = isSelected ? 3 : 1.5;
  }
  ctx.stroke();

  if (edge.is_poe_delivering && edge.poe_power_watts) {
    drawEdgePoeBadge(ctx, edge.poe_power_watts, (sx + dx) / 2, (sy + dy) / 2);
  }
}

function drawTopologyNode(
  ctx: CanvasRenderingContext2D,
  node: TopologyNode,
  isSelected: boolean,
): void {
  const x = node.x ?? 0;
  const y = node.y ?? 0;
  const isOnline = node.status === 'ONLINE';
  const radius = node.is_pse ? 32 : 28;

  if (isSelected) {
    ctx.beginPath();
    ctx.arc(x, y, radius + 6, 0, 2 * Math.PI);
    ctx.fillStyle = 'rgba(34, 211, 238, 0.25)';
    ctx.fill();
  }

  ctx.beginPath();
  ctx.arc(x, y, radius, 0, 2 * Math.PI);
  ctx.fillStyle = '#111827';
  ctx.fill();

  ctx.strokeStyle = isSelected ? '#22D3EE' : node.is_pse ? '#F59E0B' : '#1E293B';
  ctx.lineWidth = node.is_pse ? 2.5 : 2;
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(x + radius * 0.7, y - radius * 0.7, 5, 0, 2 * Math.PI);
  ctx.fillStyle = isOnline ? '#10B981' : '#EF4444';
  ctx.fill();
  ctx.strokeStyle = '#0B0F19';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  ctx.fillStyle = node.is_pse ? '#F59E0B' : '#E2E8F0';
  ctx.font = '14px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(node.is_pse ? '⚡' : '🔀', x, y - 2);

  ctx.fillStyle = '#F8FAFC';
  ctx.font = 'bold 11px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  ctx.fillText(node.ros_identity || node.display_name, x, y + radius + 4);

  ctx.fillStyle = '#94A3B8';
  ctx.font = '9px "JetBrains Mono", monospace';
  ctx.fillText(node.ip_address, x, y + radius + 18);
}

function drawCanvas(): void {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;

  if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
    canvas.width = width * dpr;
    canvas.height = height * dpr;
  }

  ctx.save();
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width, height);

  ctx.translate(panOffset.value.x, panOffset.value.y);
  ctx.scale(zoomLevel.value, zoomLevel.value);

  drawTacticalGrid(ctx, width, height);

  const nodeMap = new Map<string, TopologyNode>();
  for (const n of filteredNodes.value) {
    nodeMap.set(n.id, n);
  }

  for (const edge of filteredEdges.value) {
    const src = nodeMap.get(edge.source_router_id);
    const dst = nodeMap.get(edge.target_router_id);
    if (src && dst && src.x !== undefined && src.y !== undefined && dst.x !== undefined && dst.y !== undefined) {
      drawTopologyEdge(ctx, edge, src, dst, selectedEdge.value?.id === edge.id);
    }
  }

  for (const node of filteredNodes.value) {
    if (node.x !== undefined && node.y !== undefined) {
      drawTopologyNode(ctx, node, selectedNode.value?.id === node.id);
    }
  }

  ctx.restore();
}

function drawTacticalGrid(ctx: CanvasRenderingContext2D, width: number, height: number): void {
  const gridSize = 40;
  ctx.strokeStyle = 'rgba(30, 41, 59, 0.4)';
  ctx.lineWidth = 0.5;

  const startX = -panOffset.value.x / zoomLevel.value;
  const startY = -panOffset.value.y / zoomLevel.value;
  const endX = startX + width / zoomLevel.value;
  const endY = startY + height / zoomLevel.value;

  const firstGridX = Math.floor(startX / gridSize) * gridSize;
  const firstGridY = Math.floor(startY / gridSize) * gridSize;

  ctx.beginPath();
  for (let x = firstGridX; x < endX; x += gridSize) {
    ctx.moveTo(x, startY);
    ctx.lineTo(x, endY);
  }
  for (let y = firstGridY; y < endY; y += gridSize) {
    ctx.moveTo(startX, y);
    ctx.lineTo(endX, y);
  }
  ctx.stroke();
}

// Eventos de Puntero / Ratón para Drag, Pan y Selección
function handleMouseDown(e: MouseEvent): void {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  const mouseX = (e.clientX - rect.left - panOffset.value.x) / zoomLevel.value;
  const mouseY = (e.clientY - rect.top - panOffset.value.y) / zoomLevel.value;

  // Buscar si se pulsó sobre un nodo
  const clicked = filteredNodes.value.find((n) => {
    if (n.x === undefined || n.y === undefined) return false;
    const dist = Math.hypot(n.x - mouseX, n.y - mouseY);
    return dist <= 32;
  });

  if (clicked) {
    draggedNode.value = clicked;
    selectedNode.value = clicked;
    selectedEdge.value = null;
    isDragging.value = true;
  } else {
    // Buscar si se pulsó sobre una arista
    const clickedEdge = findEdgeAt(mouseX, mouseY);
    if (clickedEdge) {
      selectedEdge.value = clickedEdge;
      selectedNode.value = null;
    } else {
      selectedNode.value = null;
      selectedEdge.value = null;
    }
    isDragging.value = true;
    dragStart.value = { x: e.clientX - panOffset.value.x, y: e.clientY - panOffset.value.y };
  }
  requestDraw();
}

function handleMouseMove(e: MouseEvent): void {
  if (!isDragging.value) return;

  if (draggedNode.value) {
    const canvas = canvasRef.value;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    draggedNode.value.x = (e.clientX - rect.left - panOffset.value.x) / zoomLevel.value;
    draggedNode.value.y = (e.clientY - rect.top - panOffset.value.y) / zoomLevel.value;
    requestDraw();
  } else {
    panOffset.value = {
      x: e.clientX - dragStart.value.x,
      y: e.clientY - dragStart.value.y,
    };
    requestDraw();
  }
}

function handleMouseUp(): void {
  isDragging.value = false;
  draggedNode.value = null;
}

function handleWheel(e: WheelEvent): void {
  e.preventDefault();
  const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
  const newZoom = Math.max(0.4, Math.min(2.5, zoomLevel.value * zoomFactor));
  zoomLevel.value = newZoom;
  requestDraw();
}

function findEdgeAt(x: number, y: number): TopologyEdge | null {
  const nodeMap = new Map(filteredNodes.value.map((n) => [n.id, n]));
  for (const edge of filteredEdges.value) {
    const src = nodeMap.get(edge.source_router_id);
    const dst = nodeMap.get(edge.target_router_id);
    if (!src || !dst || src.x === undefined || src.y === undefined || dst.x === undefined || dst.y === undefined) {
      continue;
    }
    const dist = distanceToSegment(x, y, src.x, src.y, dst.x, dst.y);
    if (dist <= 8) {
      return edge;
    }
  }
  return null;
}

function distanceToSegment(x: number, y: number, x1: number, y1: number, x2: number, y2: number): number {
  const A = x - x1;
  const B = y - y1;
  const C = x2 - x1;
  const D = y2 - y1;
  const dot = A * C + B * D;
  const lenSq = C * C + D * D;
  let param = -1;
  if (lenSq !== 0) param = dot / lenSq;
  let xx: number;
  let yy: number;
  if (param < 0) {
    xx = x1;
    yy = y1;
  } else if (param > 1) {
    xx = x2;
    yy = y2;
  } else {
    xx = x1 + param * C;
    yy = y1 + param * D;
  }
  return Math.hypot(x - xx, y - yy);
}

function resetZoomAndPan(): void {
  zoomLevel.value = 1.0;
  panOffset.value = { x: 0, y: 0 };
  initNodePositions();
  requestDraw();
}

function openRouterWebFig(routerId: string): void {
  router.push(`/routers/${routerId}/webfig/live`);
}

onMounted(() => {
  loadTopology();
  window.addEventListener('resize', requestDraw);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', requestDraw);
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId);
  }
});

watch([searchQuery, onlyPoeFilter], () => {
  requestDraw();
});
</script>

<template>
  <main class="l2-topology-view" aria-labelledby="topology-title">
    <header class="topo-header">
      <div>
        <h1 id="topology-title" class="topo-title">{{ t('l2_topology.title') }}</h1>
        <p class="topo-subtitle">
          {{ t('l2_topology.subtitle') }}
        </p>
      </div>

      <div class="header-controls">
        <button
          type="button"
          class="btn-refresh-topo"
          :disabled="loading"
          :aria-label="t('l2_topology.btn_refresh')"
          @click="loadTopology(true)"
        >
          <span v-if="loading" class="spinner-sm" aria-hidden="true"></span>
          <span v-else aria-hidden="true">🔄</span>
          <span>{{ loading ? t('l2_topology.discovering') : t('l2_topology.btn_refresh') }}</span>
        </button>

        <button
          type="button"
          class="btn-reset-view"
          :aria-label="t('l2_topology.btn_center')"
          @click="resetZoomAndPan"
        >
          <span>{{ t('l2_topology.btn_center') }}</span>
        </button>
      </div>
    </header>

    <!-- Barra de Filtros y Leyenda Táctica -->
    <section class="topo-toolbar" aria-label="Herramientas y filtros de topología">
      <div class="search-wrap">
        <label for="topo-search" class="visually-hidden">Buscar router o switch</label>
        <input
          id="topo-search"
          v-model="searchQuery"
          type="text"
          class="input-search"
          :placeholder="t('l2_topology.search_placeholder')"
        />
      </div>

      <label class="checkbox-poe-label">
        <input v-model="onlyPoeFilter" type="checkbox" class="checkbox-poe" />
        <span>{{ t('l2_topology.filter_only_poe') }}</span>
      </label>

      <!-- Leyenda Rápida -->
      <div class="legend-wrap" aria-label="Leyenda de símbolos">
        <span class="legend-item"><span class="led led--online"></span> {{ t('l2_topology.legend_online') }}</span>
        <span class="legend-item"><span class="led led--pse">⚡</span> {{ t('l2_topology.legend_pse') }}</span>
        <span class="legend-item"><span class="line-sample line--poe"></span> {{ t('l2_topology.legend_poe_delivery') }}</span>
        <span class="legend-item"><span class="line-sample line--data"></span> {{ t('l2_topology.legend_data_link') }}</span>
      </div>
    </section>

    <!-- Error Banner -->
    <div v-if="errorMessage" class="banner-error" role="alert">
      <span>🚨 {{ errorMessage }}</span>
    </div>

    <!-- Área del Canvas Interactivo y Drawer Lateral -->
    <div class="canvas-wrapper">
      <canvas
        ref="canvasRef"
        class="topology-canvas"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @mouseleave="handleMouseUp"
        @wheel="handleWheel"
      ></canvas>

      <!-- Panel Lateral de Detalles de Selección -->
      <aside v-if="selectedNode" class="detail-drawer" aria-label="Detalles del equipo seleccionado">
        <div class="drawer-header">
          <h2 class="drawer-title">{{ selectedNode.ros_identity || selectedNode.display_name }}</h2>
          <button
            type="button"
            class="btn-close-drawer"
            aria-label="Cerrar panel de detalles"
            @click="selectedNode = null"
          >
            ✕
          </button>
        </div>

        <div class="drawer-body">
          <div class="drawer-kpi-row">
            <span class="drawer-kpi-label">{{ t('l2_topology.drawer_node_status') }}</span>
            <span
              class="status-tag"
              :class="selectedNode.status === 'ONLINE' ? 'status-tag--online' : 'status-tag--offline'"
            >
              {{ selectedNode.status }}
            </span>
          </div>

          <div class="drawer-kpi-row">
            <span class="drawer-kpi-label">{{ t('l2_topology.drawer_node_ip') }}</span>
            <span class="tabular-nums font-mono">{{ selectedNode.ip_address }}</span>
          </div>

          <div class="drawer-kpi-row">
            <span class="drawer-kpi-label">{{ t('l2_topology.drawer_node_model') }}</span>
            <span>{{ selectedNode.model_name || selectedNode.board_name || 'MikroTik Router' }}</span>
          </div>

          <div class="drawer-kpi-row">
            <span class="drawer-kpi-label">{{ t('l2_topology.drawer_node_ros') }}</span>
            <span class="tabular-nums font-mono">v{{ selectedNode.ros_version || '7' }}</span>
          </div>

          <div class="drawer-kpi-row">
            <span class="drawer-kpi-label">{{ t('l2_topology.drawer_node_poe') }}</span>
            <span v-if="selectedNode.is_pse" class="badge-pse">{{ t('l2_topology.badge_pse') }}</span>
            <span v-else class="badge-pd">{{ t('l2_topology.badge_pd') }}</span>
          </div>

          <button
            type="button"
            class="btn-open-webfig"
            :aria-label="`Abrir consola WebFig de ${selectedNode.display_name}`"
            @click="openRouterWebFig(selectedNode.id)"
          >
            {{ t('l2_topology.btn_open_webfig') }}
          </button>
        </div>
      </aside>

      <!-- Panel Lateral de Detalles de Enlace -->
      <aside v-else-if="selectedEdge" class="detail-drawer" aria-label="Detalles del enlace Layer 2">
        <div class="drawer-header">
          <h2 class="drawer-title">{{ t('l2_topology.drawer_edge_title') }}</h2>
          <button
            type="button"
            class="btn-close-drawer"
            aria-label="Cerrar panel de detalles"
            @click="selectedEdge = null"
          >
            ✕
          </button>
        </div>

        <div class="drawer-body">
          <div class="drawer-kpi-row">
            <span class="drawer-kpi-label">{{ t('l2_topology.drawer_edge_source') }}</span>
            <span class="font-mono">{{ selectedEdge.source_interface }}</span>
          </div>

          <div class="drawer-kpi-row">
            <span class="drawer-kpi-label">{{ t('l2_topology.drawer_edge_target') }}</span>
            <span class="font-mono">{{ selectedEdge.target_interface }}</span>
          </div>

          <div class="drawer-kpi-row">
            <span class="drawer-kpi-label">{{ t('l2_topology.drawer_edge_speed') }}</span>
            <span class="font-mono">{{ selectedEdge.link_speed || '1Gbps' }}</span>
          </div>

          <div class="drawer-kpi-row">
            <span class="drawer-kpi-label">{{ t('l2_topology.drawer_edge_proto') }}</span>
            <span>{{ selectedEdge.protocol }}</span>
          </div>

          <div v-if="selectedEdge.is_poe_delivering" class="poe-details-box">
            <span class="poe-title">{{ t('l2_topology.poe_active_supply') }}</span>
            <p class="poe-watts tabular-nums font-mono">
              {{ t('l2_topology.poe_measured_consumption', { watts: (selectedEdge.poe_power_watts ?? 0).toFixed(1) }) }}
            </p>
          </div>
        </div>
      </aside>
    </div>

    <!-- Resumen Accesible para Lectores de Pantalla (WCAG 2.1 AA) -->
    <section class="visually-hidden" aria-label="Resumen textual de topología física">
      <h2>Lista de Equipos y Conexiones</h2>
      <ul>
        <li v-for="node in filteredNodes" :key="node.id">
          {{ node.ros_identity || node.display_name }} ({{ node.ip_address }}) - {{ node.status }} -
          {{ node.is_pse ? 'Inyector PSE' : 'Equipo estándar' }}
        </li>
      </ul>
    </section>
  </main>
</template>

<style scoped>
.l2-topology-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  background-color: var(--rg-bg-canvas, #0b0f19);
  color: var(--rg-text-primary, #f8fafc);
  height: calc(100vh - 4.5rem);
  box-sizing: border-box;
}

.topo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.topo-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.25rem 0;
  color: var(--rg-text-primary, #f8fafc);
}

.topo-subtitle {
  font-size: 0.875rem;
  color: var(--rg-text-secondary, #cbd5e1);
  margin: 0;
}

.header-controls {
  display: flex;
  gap: 0.5rem;
}

.btn-refresh-topo,
.btn-reset-view {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.45rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid var(--rg-border-grid, #334155);
  background-color: var(--rg-bg-surface, #111827);
  color: var(--rg-text-primary, #f8fafc);
  transition: all 0.15s ease;
}

.btn-refresh-topo:hover:not(:disabled),
.btn-reset-view:hover {
  border-color: var(--rg-accent-cyan, #22d3ee);
  color: var(--rg-accent-cyan, #22d3ee);
}

.topo-toolbar {
  display: flex;
  gap: 1.5rem;
  align-items: center;
  flex-wrap: wrap;
  background-color: var(--rg-bg-surface, #111827);
  border: 1px solid var(--rg-border-grid, #1e293b);
  border-radius: 8px;
  padding: 0.65rem 1rem;
}

.input-search {
  background-color: var(--rg-bg-canvas, #0b0f19);
  border: 1px solid var(--rg-border-grid, #334155);
  border-radius: 6px;
  color: var(--rg-text-primary, #f8fafc);
  padding: 0.35rem 0.75rem;
  font-size: 0.875rem;
  width: 280px;
  outline: none;
}

.input-search:focus {
  border-color: var(--rg-accent-cyan, #22d3ee);
}

.checkbox-poe-label {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.825rem;
  cursor: pointer;
  color: #facc15;
}

.legend-wrap {
  display: flex;
  gap: 1rem;
  margin-left: auto;
  align-items: center;
  font-size: 0.75rem;
  color: var(--rg-text-secondary, #cbd5e1);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.led {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.led--online {
  background-color: #10b981;
  box-shadow: 0 0 6px #10b981;
}

.led--pse {
  color: #f59e0b;
  font-weight: 700;
}

.line-sample {
  width: 16px;
  height: 3px;
  display: inline-block;
  border-radius: 2px;
}

.line--poe {
  background-color: #facc15;
}

.line--data {
  background-color: #334155;
}

.canvas-wrapper {
  position: relative;
  flex: 1;
  border: 1px solid var(--rg-border-grid, #1e293b);
  border-radius: 8px;
  overflow: hidden;
  background-color: var(--rg-bg-canvas, #0b0f19);
}

.topology-canvas {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
}

.topology-canvas:active {
  cursor: grabbing;
}

.detail-drawer {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 300px;
  background-color: var(--rg-bg-surface, #111827);
  border: 1px solid var(--rg-border-grid, #334155);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  border-radius: 8px;
  overflow: hidden;
  z-index: 10;
  display: flex;
  flex-direction: column;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background-color: var(--rg-bg-elevated, #1e293b);
  border-bottom: 1px solid var(--rg-border-grid, #334155);
}

.drawer-title {
  font-size: 0.95rem;
  font-weight: 700;
  margin: 0;
  color: var(--rg-text-primary, #f8fafc);
}

.btn-close-drawer {
  background: transparent;
  border: none;
  color: var(--rg-text-muted, #94a3b8);
  font-size: 1rem;
  cursor: pointer;
}

.btn-close-drawer:hover {
  color: var(--rg-text-primary, #f8fafc);
}

.drawer-body {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  font-size: 0.85rem;
}

.drawer-kpi-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.drawer-kpi-label {
  color: var(--rg-text-secondary, #cbd5e1);
}

.status-tag {
  font-size: 0.75rem;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  font-weight: 600;
}

.status-tag--online {
  background-color: rgba(16, 185, 129, 0.2);
  color: #34d399;
}

.status-tag--offline {
  background-color: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.badge-pse {
  color: #f59e0b;
  font-weight: 600;
  font-size: 0.75rem;
}

.badge-pd {
  color: var(--rg-text-muted, #94a3b8);
  font-size: 0.75rem;
}

.poe-details-box {
  background-color: rgba(250, 204, 21, 0.1);
  border: 1px solid rgba(250, 204, 21, 0.3);
  border-radius: 6px;
  padding: 0.6rem;
  margin-top: 0.5rem;
}

.poe-title {
  color: #facc15;
  font-size: 0.8rem;
  font-weight: 700;
  display: block;
}

.poe-watts {
  font-size: 0.85rem;
  color: #f8fafc;
  margin: 0.25rem 0 0 0;
}

.btn-open-webfig {
  margin-top: 0.5rem;
  background-color: #0284c7;
  color: #ffffff;
  border: none;
  padding: 0.5rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-open-webfig:hover {
  background-color: #0369a1;
}

.spinner-sm {
  width: 0.875rem;
  height: 0.875rem;
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
}

.font-mono {
  font-family: 'JetBrains Mono', 'Ubuntu Mono', monospace;
}

.visually-hidden {
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
</style>
