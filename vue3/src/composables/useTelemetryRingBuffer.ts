// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { ref, shallowRef, computed, onBeforeUnmount, triggerRef } from 'vue';
import type { TelemetryPoint } from '@/types';

export const MAX_POINTS = 5400; // 3 horas a 1 tick cada 2s

export type TelemetryWindowKey = '2m' | '15m' | '1h' | '3h';

export const WINDOW_POINTS_MAP: Record<TelemetryWindowKey, number> = {
  '2m': 60,
  '15m': 450,
  '1h': 1800,
  '3h': 5400,
};

/**
 * Clase pura TelemetryRingBuffer<T>
 * Buffer circular pre-alojado en memoria RAM para inserción y lectura O(1).
 */
export class TelemetryRingBuffer<T = TelemetryPoint> {
  private buffer: (T | null)[];
  private head: number = 0;
  private count: number = 0;
  private readonly capacity: number;

  constructor(capacity = MAX_POINTS) {
    this.capacity = capacity > 0 ? capacity : MAX_POINTS;
    this.buffer = new Array<T | null>(this.capacity).fill(null);
  }

  public push(item: T): void {
    this.buffer[this.head] = item;
    this.head = (this.head + 1) % this.capacity;
    if (this.count < this.capacity) {
      this.count++;
    }
  }

  public toArray(): T[] {
    if (this.count === 0) return [];
    const result: T[] = new Array<T>(this.count);
    const start = this.count < this.capacity ? 0 : this.head;
    for (let i = 0; i < this.count; i++) {
      const idx = (start + i) % this.capacity;
      result[i] = this.buffer[idx] as T;
    }
    return result;
  }

  public getRecent(n: number): T[] {
    if (this.count === 0 || n <= 0) return [];
    const take = Math.min(n, this.count);
    const result: T[] = new Array<T>(take);
    // Empezamos desde head - take
    let start = this.head - take;
    if (start < 0) {
      start += this.capacity;
    }
    for (let i = 0; i < take; i++) {
      const idx = (start + i) % this.capacity;
      result[i] = this.buffer[idx] as T;
    }
    return result;
  }

  public clear(): void {
    this.buffer = new Array<T | null>(this.capacity).fill(null);
    this.head = 0;
    this.count = 0;
  }

  public length(): number {
    return this.count;
  }

  public maxCapacity(): number {
    return this.capacity;
  }
}

/**
 * Composable useTelemetryRingBuffer
 * Maneja el estado reactivo del RingBuffer con shallowRef para rendimiento extremo.
 */
export function useTelemetryRingBuffer(capacity = MAX_POINTS) {
  const ringBuffer = new TelemetryRingBuffer<TelemetryPoint>(capacity);
  const rawPoints = shallowRef<TelemetryPoint[]>([]);
  const selectedWindow = ref<TelemetryWindowKey>('15m');

  function addPoint(pt: TelemetryPoint): void {
    ringBuffer.push(pt);
    rawPoints.value = ringBuffer.toArray();
    triggerRef(rawPoints);
  }

  const windowPoints = computed<TelemetryPoint[]>(() => {
    const limit = WINDOW_POINTS_MAP[selectedWindow.value] || 450;
    const all = rawPoints.value;
    if (all.length <= limit) return all;
    return all.slice(all.length - limit);
  });

  const latestPoint = computed<TelemetryPoint | null>(() => {
    const all = rawPoints.value;
    return all.length > 0 ? all[all.length - 1] : null;
  });

  function setWindow(w: TelemetryWindowKey): void {
    selectedWindow.value = w;
  }

  function clearBuffer(): void {
    ringBuffer.clear();
    rawPoints.value = [];
    triggerRef(rawPoints);
  }

  onBeforeUnmount(() => {
    clearBuffer();
  });

  return {
    rawPoints,
    windowPoints,
    latestPoint,
    selectedWindow,
    setWindow,
    addPoint,
    clearBuffer,
    ringBuffer,
  };
}
