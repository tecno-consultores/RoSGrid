<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import FieldTechMobileView from '@/components/field/FieldTechMobileView.vue';
</script>

<template>
  <div class="field-tech-operations-view" role="region" aria-label="Operaciones de Campo">
    <FieldTechMobileView />
  </div>
</template>

<style scoped>
  .field-tech-operations-view {
    min-height: calc(100vh - 60px);
    background: #04070e;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 1rem 0;
  }
</style>
