// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    // FRONTERA ESTRICTA (TOOL BOUNDARY): Vitest solo ejecuta pruebas unitarias rápidas.
    include: ['src/**/*.unit.{ts,tsx}', 'src/**/*.spec.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      thresholds: {
        lines: 95,
        functions: 95,
        branches: 95,
        statements: 95,
      },
      exclude: [
        'coverage/**',
        'dist/**',
        'playwright-report/**',
        'lhci-reports/**',
        '.stryker-tmp/**',
        'e2e/**',
        'test/**',
        '**/*.d.ts',
        '*.config.ts',
        '*.config.js',
        'lighthouserc.js',
        'src/main.ts',
      ],
    },
  },
});
