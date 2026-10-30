<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  withDefaults(
    defineProps<{
      size?: number;
      imgClass?: string;
    }>(),
    {
      size: 22,
      imgClass: 'brand-logo',
    },
  );
</script>

<template>
  <span class="rg-brand-logo-wrap" :style="{ width: `${size}px`, height: `${size}px` }">
    <svg
      :width="size"
      :height="size"
      viewBox="0 0 140 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      class="rg-brand-logo-svg"
      aria-hidden="true"
    >
      <!-- Letra 'R': Constelación Cyber Blue reactiva al tema -->
      <g class="rg-constellation-r">
        <line
          x1="16"
          y1="14"
          x2="16"
          y2="86"
          stroke="var(--rg-brand-cyber-blue, #00D2FF)"
          stroke-width="3"
        />
        <line
          x1="16"
          y1="14"
          x2="44"
          y2="14"
          stroke="var(--rg-brand-cyber-blue, #00D2FF)"
          stroke-width="3"
        />
        <line
          x1="44"
          y1="14"
          x2="56"
          y2="28"
          stroke="var(--rg-brand-cyber-blue, #00D2FF)"
          stroke-width="3"
        />
        <line
          x1="56"
          y1="28"
          x2="54"
          y2="48"
          stroke="var(--rg-brand-cyber-blue, #00D2FF)"
          stroke-width="3"
        />
        <line
          x1="54"
          y1="48"
          x2="16"
          y2="48"
          stroke="var(--rg-brand-cyber-blue, #00D2FF)"
          stroke-width="3"
        />
        <line
          x1="34"
          y1="48"
          x2="58"
          y2="86"
          stroke="var(--rg-brand-cyber-blue, #00D2FF)"
          stroke-width="3"
        />
        <circle cx="16" cy="14" r="4" fill="var(--rg-brand-cyber-blue, #00D2FF)" />
        <circle cx="16" cy="48" r="4" fill="var(--rg-brand-cyber-blue, #00D2FF)" />
        <circle cx="16" cy="86" r="4" fill="var(--rg-brand-cyber-blue, #00D2FF)" />
        <circle cx="44" cy="14" r="3.5" fill="var(--rg-brand-cyber-blue, #00D2FF)" />
        <circle cx="56" cy="28" r="3.5" fill="var(--rg-brand-cyber-blue, #00D2FF)" />
        <circle cx="54" cy="48" r="3.5" fill="var(--rg-brand-cyber-blue, #00D2FF)" />
        <circle cx="58" cy="86" r="4" fill="var(--rg-brand-cyber-blue, #00D2FF)" />
      </g>

      <!-- Letra 'G': Constelación Electric Orange reactiva al tema -->
      <g class="rg-constellation-g">
        <line
          x1="112"
          y1="24"
          x2="94"
          y2="14"
          stroke="var(--rg-brand-electric-orange, #FF8400)"
          stroke-width="3"
        />
        <line
          x1="94"
          y1="14"
          x2="78"
          y2="24"
          stroke="var(--rg-brand-electric-orange, #FF8400)"
          stroke-width="3"
        />
        <line
          x1="78"
          y1="24"
          x2="70"
          y2="46"
          stroke="var(--rg-brand-electric-orange, #FF8400)"
          stroke-width="3"
        />
        <line
          x1="70"
          y1="46"
          x2="70"
          y2="66"
          stroke="var(--rg-brand-electric-orange, #FF8400)"
          stroke-width="3"
        />
        <line
          x1="70"
          y1="66"
          x2="80"
          y2="84"
          stroke="var(--rg-brand-electric-orange, #FF8400)"
          stroke-width="3"
        />
        <line
          x1="80"
          y1="84"
          x2="102"
          y2="88"
          stroke="var(--rg-brand-electric-orange, #FF8400)"
          stroke-width="3"
        />
        <line
          x1="102"
          y1="88"
          x2="120"
          y2="76"
          stroke="var(--rg-brand-electric-orange, #FF8400)"
          stroke-width="3"
        />
        <line
          x1="120"
          y1="76"
          x2="120"
          y2="52"
          stroke="var(--rg-brand-electric-orange, #FF8400)"
          stroke-width="3"
        />
        <line
          x1="120"
          y1="52"
          x2="96"
          y2="52"
          stroke="var(--rg-brand-electric-orange, #FF8400)"
          stroke-width="3"
        />
        <circle cx="112" cy="24" r="4" fill="var(--rg-brand-electric-orange, #FF8400)" />
        <circle cx="94" cy="14" r="4" fill="var(--rg-brand-electric-orange, #FF8400)" />
        <circle cx="70" cy="46" r="3.5" fill="var(--rg-brand-electric-orange, #FF8400)" />
        <circle cx="80" cy="84" r="3.5" fill="var(--rg-brand-electric-orange, #FF8400)" />
        <circle cx="102" cy="88" r="4" fill="var(--rg-brand-electric-orange, #FF8400)" />
        <circle cx="120" cy="76" r="4" fill="var(--rg-brand-electric-orange, #FF8400)" />
        <circle cx="120" cy="52" r="4" fill="var(--rg-brand-electric-orange, #FF8400)" />
      </g>
    </svg>
    <img
      src="/favicon.svg"
      alt=""
      :class="['brand-icon', imgClass, 'brand-logo-fallback']"
      :width="size"
      :height="size"
      aria-hidden="true"
    />
  </span>
</template>

<style scoped>
  .rg-brand-logo-wrap {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    position: relative;
    flex-shrink: 0;
  }

  .rg-brand-logo-svg {
    display: block;
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 0 6px rgba(0, 210, 255, 0.3));
  }

  .brand-logo-fallback {
    position: absolute;
    width: 1px;
    height: 1px;
    opacity: 0;
    pointer-events: none;
  }
</style>
