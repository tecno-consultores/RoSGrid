<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores) -->

<script setup lang="ts">
  withDefaults(
    defineProps<{
      size?: number;
      imgClass?: string;
    }>(),
    {
      size: 28,
      imgClass: 'brand-logo',
    },
  );
</script>

<template>
  <span class="rg-brand-logo-wrap" :style="{ width: `${size}px`, height: `${size}px` }">
    <svg
      :width="size"
      :height="size"
      viewBox="0 0 512 512"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      class="rg-brand-logo-svg"
      aria-hidden="true"
    >
      <defs>
        <radialGradient id="rgBgGrad" cx="50%" cy="50%" r="70%">
          <stop offset="0%" stop-color="#111C33" />
          <stop offset="100%" stop-color="#0B111E" />
        </radialGradient>
        <linearGradient id="rgCyberBlue" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#00F0FF" />
          <stop offset="55%" stop-color="var(--rg-brand-cyber-blue, #00D2FF)" />
          <stop offset="100%" stop-color="#0066FF" />
        </linearGradient>
        <linearGradient id="rgElectricOrange" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#FFCC00" />
          <stop offset="50%" stop-color="var(--rg-brand-electric-orange, #FF8400)" />
          <stop offset="100%" stop-color="#FF4500" />
        </linearGradient>
        <filter id="rgNeonGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <!-- Contenedor Táctico Redondeado Deep Navy -->
      <rect
        x="12"
        y="12"
        width="488"
        height="488"
        rx="96"
        ry="96"
        fill="url(#rgBgGrad)"
        stroke="var(--rg-brand-cyber-blue, #00D2FF)"
        stroke-width="6"
        stroke-opacity="0.55"
      />

      <!-- Retícula Táctica de Fondo -->
      <g stroke="#1A2942" stroke-width="1.5" opacity="0.55">
        <line x1="128" y1="20" x2="128" y2="492" />
        <line x1="256" y1="20" x2="256" y2="492" />
        <line x1="384" y1="20" x2="384" y2="492" />
        <line x1="20" y1="128" x2="492" y2="128" />
        <line x1="20" y1="256" x2="492" y2="256" />
        <line x1="20" y1="384" x2="492" y2="384" />
      </g>

      <!-- Letra 'R': Malla Poligonal Cyber Blue de Alta Definición -->
      <g class="rg-constellation-r" filter="url(#rgNeonGlow)">
        <g stroke="url(#rgCyberBlue)" stroke-width="2.5" opacity="0.65">
          <line x1="76" y1="126" x2="124" y2="170" />
          <line x1="76" y1="126" x2="175" y2="126" />
          <line x1="124" y1="170" x2="175" y2="126" />
          <line x1="124" y1="170" x2="76" y2="230" />
          <line x1="76" y1="230" x2="124" y2="262" />
          <line x1="124" y1="170" x2="215" y2="170" />
          <line x1="175" y1="126" x2="242" y2="152" />
          <line x1="215" y1="170" x2="246" y2="205" />
          <line x1="215" y1="218" x2="246" y2="205" />
          <line x1="175" y1="262" x2="215" y2="218" />
          <line x1="124" y1="262" x2="76" y2="318" />
          <line x1="76" y1="318" x2="124" y2="386" />
          <line x1="124" y1="262" x2="124" y2="330" />
          <line x1="168" y1="262" x2="208" y2="386" />
          <line x1="168" y1="262" x2="248" y2="386" />
          <line x1="195" y1="325" x2="248" y2="386" />
        </g>
        <path
          d="M 76 126 L 184 126 C 226 126 250 152 250 194 C 250 230 228 254 194 260 L 252 386 L 198 386 L 146 266 L 124 266 L 124 386 L 76 386 Z M 124 168 L 124 226 L 178 226 C 198 226 208 214 208 197 C 208 180 198 168 178 168 Z"
          fill="var(--rg-brand-cyber-blue, #00D2FF)"
          fill-opacity="0.14"
          stroke="url(#rgCyberBlue)"
          stroke-width="6.5"
          stroke-linejoin="round"
        />
        <g fill="#00F0FF">
          <circle cx="76" cy="126" r="7.5" />
          <circle cx="175" cy="126" r="6.5" />
          <circle cx="242" cy="152" r="6.5" />
          <circle cx="248" cy="202" r="7" />
          <circle cx="194" cy="260" r="6.5" />
          <circle cx="252" cy="386" r="7.5" />
          <circle cx="198" cy="386" r="6" />
          <circle cx="124" cy="386" r="6.5" />
          <circle cx="76" cy="386" r="7.5" />
          <circle cx="76" cy="256" r="6" />
          <circle cx="124" cy="170" r="5.5" />
          <circle cx="124" cy="226" r="5.5" />
          <circle cx="206" cy="197" r="5.5" />
          <circle cx="196" cy="324" r="5.5" />
        </g>
      </g>

      <!-- Letra 'G': Malla Poligonal Electric Orange de Alta Definición -->
      <g class="rg-constellation-g" filter="url(#rgNeonGlow)">
        <g stroke="url(#rgElectricOrange)" stroke-width="2.5" opacity="0.65">
          <line x1="356" y1="120" x2="310" y2="165" />
          <line x1="356" y1="120" x2="428" y2="162" />
          <line x1="310" y1="165" x2="395" y2="188" />
          <line x1="252" y1="190" x2="310" y2="165" />
          <line x1="252" y1="190" x2="282" y2="256" />
          <line x1="238" y1="256" x2="282" y2="256" />
          <line x1="252" y1="322" x2="282" y2="256" />
          <line x1="252" y1="322" x2="310" y2="348" />
          <line x1="310" y1="348" x2="356" y2="392" />
          <line x1="356" y1="392" x2="436" y2="352" />
          <line x1="392" y1="344" x2="436" y2="252" />
          <line x1="344" y1="252" x2="436" y2="296" />
          <line x1="344" y1="252" x2="392" y2="344" />
        </g>
        <g stroke="#00D2FF" stroke-width="2" opacity="0.7">
          <line x1="282" y1="256" x2="356" y2="165" />
          <line x1="282" y1="256" x2="352" y2="344" />
          <circle cx="282" cy="256" r="5" fill="#00F0FF" />
          <circle cx="356" cy="165" r="4.5" fill="#00F0FF" />
        </g>
        <path
          d="M 432 168 L 392 196 C 378 176 358 166 334 166 C 292 166 266 202 266 256 C 266 310 294 346 338 346 C 368 346 388 332 392 296 L 342 296 L 342 252 L 438 252 L 438 352 C 414 378 380 392 338 392 C 266 392 218 336 218 256 C 218 176 268 120 338 120 C 380 120 412 138 432 168 Z"
          fill="var(--rg-brand-electric-orange, #FF8400)"
          fill-opacity="0.14"
          stroke="url(#rgElectricOrange)"
          stroke-width="6.5"
          stroke-linejoin="round"
        />
        <g fill="#FFB800">
          <circle cx="356" cy="120" r="7.5" />
          <circle cx="432" cy="168" r="7.5" />
          <circle cx="392" cy="196" r="6" />
          <circle cx="252" cy="176" r="6.5" />
          <circle cx="218" cy="256" r="7" />
          <circle cx="252" cy="336" r="6.5" />
          <circle cx="356" cy="392" r="7.5" />
          <circle cx="438" cy="352" r="7.5" />
          <circle cx="438" cy="252" r="7" />
          <circle cx="342" cy="252" r="6" />
          <circle cx="342" cy="296" r="5.5" />
          <circle cx="392" cy="296" r="5.5" />
        </g>
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
    filter: drop-shadow(0 0 8px rgba(0, 240, 255, 0.45));
  }

  .brand-logo-fallback {
    position: absolute;
    width: 1px;
    height: 1px;
    opacity: 0;
    pointer-events: none;
  }
</style>
