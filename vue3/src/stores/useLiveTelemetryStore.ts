// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { defineStore } from 'pinia';
import { computed, shallowRef, triggerRef } from 'vue';
import type { TelemetryPoint } from '@/types';

export const MAX_POINTS = 5400; // 3 horas de telemetría a 1 tick cada 2s

export class TelemetryRingBuffer {
  private buffer: TelemetryPoint[] = [];
  private readonly maxCapacity: number;

  constructor(capacity = MAX_POINTS) {
    this.maxCapacity = capacity;
  }

  public push(point: TelemetryPoint): void {
    if (this.buffer.length >= this.maxCapacity) {
      this.buffer.shift();
    }
    this.buffer.push(point);
  }

  public getPoints(): TelemetryPoint[] {
    return this.buffer;
  }

  public clear(): void {
    this.buffer = [];
  }

  public length(): number {
    return this.buffer.length;
  }
}

export const useLiveTelemetryStore = defineStore('liveTelemetry', () => {
  // Almacenamiento 100% en memoria RAM mediante shallowRef para evitar Proxies anidados
  const ringBuffer = new TelemetryRingBuffer(MAX_POINTS);
  const telemetryPoints = shallowRef<TelemetryPoint[]>([]);

  const latestPoint = computed<TelemetryPoint | null>(() => {
    const pts = telemetryPoints.value;
    return pts.length > 0 ? pts[pts.length - 1] : null;
  });

  function pushTelemetryPoint(point: TelemetryPoint): void {
    ringBuffer.push(point);
    telemetryPoints.value = [...ringBuffer.getPoints()];
    triggerRef(telemetryPoints);
  }

  function resetChartsBuffer(): void {
    ringBuffer.clear();
    telemetryPoints.value = [];
    triggerRef(telemetryPoints);
  }

  return {
    telemetryPoints,
    latestPoint,
    pushTelemetryPoint,
    resetChartsBuffer,
  };
});
