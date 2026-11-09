# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

# Especificación 79: Unificación del Isotipo de Alta Definición (`512×512` Mesh + Glow) en `RgBrandLogo.vue` para Cabecera Global (`RgResponsiveShell.vue`) y Pantalla de Acceso (`LoginView.vue`) (Hito 30.1)

> **Estado:** Aprobado para Ejecución (*Flash-Ready Specification*)  
> **Motor de Ejecución Objetivo:** Gemini 3.8 Flash (High)  
> **Hito Asociado:** Hito 30 — Subhito `30.1` (`ROADMAP.md`)  
> **Archivos Afectados:**
> 1. `vue3/src/components/common/RgBrandLogo.vue`
> 2. `vue3/src/components/common/RgResponsiveShell.vue`
> 3. `vue3/src/components/common/RgBrandLogo.unit.ts`

---

## 1. Diagnóstico Forense de Discrepancia Visual del Logo

1. **Por qué el logo del NOC Wallboard (`NocWallboardView.vue`) luce superior y detallado:**
   - En [`vue3/src/views/NocWallboardView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/NocWallboardView.vue#L382-L389), el encabezado renderiza directamente [`vue3/public/favicon.svg`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/public/favicon.svg) a `32×32px` con `filter: drop-shadow(0 0 8px rgba(0, 240, 255, 0.5))`.
   - Dicho archivo `favicon.svg` (`viewBox="0 0 512 512"`) contiene el arte oficial completo de **RoSGrid**: contenedor azul marino redondeado (`rx="96"`) con gradiente radial `#111C33 -> #0B111E`, cuadrícula táctica de fondo, malla poligonal de nodos interconectados para la **`R`** (`cyberBlue` `#00F0FF -> #0066FF`) y la **`G`** (`electricOrange` `#FFCC00 -> #FF4500`), contornos tipográficos sólidos y filtro de resplandor `neonGlow`.
2. **Por qué en la Cabecera Global (`RgResponsiveShell.vue`) y en la Pantalla de Login (`LoginView.vue`) se veía un SVG simple de líneas rectas:**
   - Ambos componentes utilizan [`vue3/src/components/common/RgBrandLogo.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/common/RgBrandLogo.vue).
   - Sin embargo, `RgBrandLogo.vue` contenía un `<svg viewBox="0 0 140 100">` simplificado compuesto únicamente por 15 segmentos `<line>` sin relleno tipográfico, sin contenedor redondeado ni malla de alta densidad, mientras que la etiqueta `<img src="/favicon.svg">` estaba oculta mediante `.brand-logo-fallback { opacity: 0; width: 1px; height: 1px; }`.
3. **Solución:**
   - Incorporar en [`RgBrandLogo.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/common/RgBrandLogo.vue) el arte vectorial completo `viewBox="0 0 512 512"` de alta definición (idéntico al del NOC Wallboard, con contenedor redondeado, cuadrícula, malla poligonal, trazos tipográficos `R`/`G`, degradados `cyberBlue`/`electricOrange` y resplandor `drop-shadow(0 0 8px rgba(0, 240, 255, 0.45))`), preservando las clases `.rg-brand-logo-svg`, `.rg-constellation-r` y `.rg-constellation-g`.
   - Aumentar el tamaño del logo en la cabecera global ([`RgResponsiveShell.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/common/RgResponsiveShell.vue#L327)) de `:size="22"` a `:size="28"` para que sus detalles brillen con total nitidez junto al texto `RoSGrid`.

---

## 2. Instrucciones Literales de Implementación Paso a Paso (Flash-Ready)

### Paso 1: Actualizar `vue3/src/components/common/RgBrandLogo.vue` con el Arte Vectorial Completo `512×512`

Reemplazar el contenido de [`vue3/src/components/common/RgBrandLogo.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/common/RgBrandLogo.vue):

#### `Target` en `vue3/src/components/common/RgBrandLogo.vue`:
```vue
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores) -->

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
```

#### `Replacement` en `vue3/src/components/common/RgBrandLogo.vue`:
```vue
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
```

---

### Paso 2: Ajustar el Tamaño del Logo en la Cabecera Global (`vue3/src/components/common/RgResponsiveShell.vue`)

En [`vue3/src/components/common/RgResponsiveShell.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/common/RgResponsiveShell.vue#L326-L330), aumentar `:size` de `22` a `28` para que la malla vectorial y el contenedor redondeado luzcan con la misma presencia visual del NOC Wallboard:

#### `Target` en `vue3/src/components/common/RgResponsiveShell.vue`:
```html
        <router-link to="/" class="brand" :aria-label="t('nav.dashboard', 'Ir al Centro de Mando')">
          <RgBrandLogo :size="22" img-class="brand-logo" />
          <span class="brand-name">RoSGrid</span>
          <span class="brand-version">v1.0</span>
        </router-link>
```

#### `Replacement` en `vue3/src/components/common/RgResponsiveShell.vue`:
```html
        <router-link to="/" class="brand" :aria-label="t('nav.dashboard', 'Ir al Centro de Mando')">
          <RgBrandLogo :size="28" img-class="brand-logo" />
          <span class="brand-name">RoSGrid</span>
          <span class="brand-version">v1.0</span>
        </router-link>
```

---

## 3. Verificación en Contenedor Efímero (`Rule Zero`)

```bash
docker compose -f vue3/docker-compose.qa.yml run --rm -T frontend-qa npx vitest run src/components/common/RgBrandLogo.unit.ts src/components/common/RgResponsiveShell.unit.ts src/views/auth/loginView.unit.ts
```
