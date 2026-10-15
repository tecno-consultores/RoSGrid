// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useLiveTelemetryStore, TelemetryRingBuffer } from './useLiveTelemetryStore';
import type { TelemetryPoint } from '@/types';

describe('useLiveTelemetryStore & TelemetryRingBuffer — 100% RAM Cero-DB', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  describe('TelemetryRingBuffer', () => {
    it('almacena puntos hasta la capacidad máxima y descarta los más antiguos', () => {
      const ring = new TelemetryRingBuffer(5);
      for (let i = 1; i <= 7; i++) {
        ring.push({
          timestampEpoch: i * 1000,
          timestampIso: new Date(i * 1000).toISOString(),
          cpuLoadPct: i * 10,
          freeMemoryPct: 50,
          rxBps: 1000,
          txBps: 2000,
          temperatureC: 40,
        });
      }

      expect(ring.length()).toBe(5);
      const points = ring.getPoints();
      expect(points.length).toBe(5);
      // El primero debe ser el 3 (descartó 1 y 2)
      expect(points[0].timestampEpoch).toBe(3000);
      expect(points[4].timestampEpoch).toBe(7000);
    });

    it('limpia el buffer correctamente', () => {
      const ring = new TelemetryRingBuffer(10);
      ring.push({
        timestampEpoch: 1000,
        timestampIso: new Date(1000).toISOString(),
        cpuLoadPct: 20,
        freeMemoryPct: 40,
        rxBps: 500,
        txBps: 500,
      });
      expect(ring.length()).toBe(1);
      ring.clear();
      expect(ring.length()).toBe(0);
      expect(ring.getPoints()).toEqual([]);
    });
  });

  describe('useLiveTelemetryStore', () => {
    it('inicia con buffer vacío', () => {
      const store = useLiveTelemetryStore();
      expect(store.telemetryPoints).toEqual([]);
      expect(store.latestPoint).toBeNull();
    });

    it('registra puntos de telemetría y actualiza latestPoint', () => {
      const store = useLiveTelemetryStore();
      const point: TelemetryPoint = {
        timestampEpoch: Date.now(),
        timestampIso: new Date().toISOString(),
        cpuLoadPct: 35,
        freeMemoryPct: 62,
        rxBps: 120000000,
        txBps: 50000000,
        temperatureC: 45,
      };

      store.pushTelemetryPoint(point);

      expect(store.telemetryPoints.length).toBe(1);
      expect(store.latestPoint).toEqual(point);
    });

    it('limpia el buffer reactivo con resetChartsBuffer', () => {
      const store = useLiveTelemetryStore();
      store.pushTelemetryPoint({
        timestampEpoch: Date.now(),
        timestampIso: new Date().toISOString(),
        cpuLoadPct: 10,
        freeMemoryPct: 80,
        rxBps: 0,
        txBps: 0,
      });
      expect(store.telemetryPoints.length).toBe(1);

      store.resetChartsBuffer();
      expect(store.telemetryPoints).toEqual([]);
      expect(store.latestPoint).toBeNull();
    });
  });
});
