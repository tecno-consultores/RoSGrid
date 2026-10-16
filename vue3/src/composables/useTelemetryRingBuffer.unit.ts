// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { defineComponent } from 'vue';
import { TelemetryRingBuffer, useTelemetryRingBuffer } from './useTelemetryRingBuffer';
import type { TelemetryPoint } from '@/types';

function createSamplePoint(i: number): TelemetryPoint {
  return {
    timestampEpoch: 1700000000 + i * 2,
    timestampIso: new Date(1700000000000 + i * 2000).toISOString(),
    cpuLoadPct: (i * 7) % 100,
    freeMemoryPct: 60 - ((i * 3) % 40),
    rxBps: i * 1024,
    txBps: i * 512,
    temperatureC: 40 + (i % 10),
  };
}

describe('TelemetryRingBuffer — Clase Pura en Memoria RAM', () => {
  it('inicializa con capacidad por defecto y personalizada', () => {
    const defaultBuffer = new TelemetryRingBuffer<number>();
    expect(defaultBuffer.maxCapacity()).toBe(5400);
    expect(defaultBuffer.length()).toBe(0);
    expect(defaultBuffer.toArray()).toEqual([]);

    const customBuffer = new TelemetryRingBuffer<number>(5);
    expect(customBuffer.maxCapacity()).toBe(5);
  });

  it('inserta elementos sin superar la capacidad y rota de manera circular', () => {
    const buffer = new TelemetryRingBuffer<number>(3);
    buffer.push(10);
    buffer.push(20);
    expect(buffer.length()).toBe(2);
    expect(buffer.toArray()).toEqual([10, 20]);

    buffer.push(30);
    expect(buffer.length()).toBe(3);
    expect(buffer.toArray()).toEqual([10, 20, 30]);

    // Sobrepasar capacidad: debe expulsar el 10 y quedar [20, 30, 40]
    buffer.push(40);
    expect(buffer.length()).toBe(3);
    expect(buffer.toArray()).toEqual([20, 30, 40]);

    buffer.push(50);
    expect(buffer.toArray()).toEqual([30, 40, 50]);
  });

  it('obtiene los N elementos más recientes correctamente', () => {
    const buffer = new TelemetryRingBuffer<number>(4);
    expect(buffer.getRecent(2)).toEqual([]);

    buffer.push(1);
    buffer.push(2);
    buffer.push(3);
    expect(buffer.getRecent(2)).toEqual([2, 3]);
    expect(buffer.getRecent(10)).toEqual([1, 2, 3]);
    expect(buffer.getRecent(0)).toEqual([]);

    buffer.push(4);
    buffer.push(5); // [2, 3, 4, 5]
    expect(buffer.getRecent(2)).toEqual([4, 5]);
    expect(buffer.getRecent(4)).toEqual([2, 3, 4, 5]);
  });

  it('limpia el buffer por completo', () => {
    const buffer = new TelemetryRingBuffer<number>(3);
    buffer.push(1);
    buffer.push(2);
    buffer.clear();
    expect(buffer.length()).toBe(0);
    expect(buffer.toArray()).toEqual([]);
  });
});

describe('useTelemetryRingBuffer Composable', () => {
  it('acumula telemetría, calcula latestPoint y recorta según la ventana seleccionada', () => {
    const TestComponent = defineComponent({
      setup() {
        return useTelemetryRingBuffer(100);
      },
      template: '<div>{{ rawPoints.length }}</div>',
    });

    const wrapper = mount(TestComponent);
    const vm = wrapper.vm;

    expect(vm.rawPoints.length).toBe(0);
    expect(vm.latestPoint).toBeNull();

    // Agregar 70 puntos
    for (let i = 0; i < 70; i++) {
      vm.addPoint(createSamplePoint(i));
    }

    expect(vm.rawPoints.length).toBe(70);
    expect(vm.latestPoint).not.toBeNull();
    expect(vm.latestPoint?.cpuLoadPct).toBe(createSamplePoint(69).cpuLoadPct);

    // Ventana 2m (límite 60)
    vm.setWindow('2m');
    expect(vm.selectedWindow).toBe('2m');
    expect(vm.windowPoints.length).toBe(60);

    // Ventana 15m (límite 450, pero solo hay 70)
    vm.setWindow('15m');
    expect(vm.windowPoints.length).toBe(70);

    // Ventanas 1h y 3h
    vm.setWindow('1h');
    expect(vm.windowPoints.length).toBe(70);
    vm.setWindow('3h');
    expect(vm.windowPoints.length).toBe(70);

    // Limpiar buffer
    vm.clearBuffer();
    expect(vm.rawPoints.length).toBe(0);
    expect(vm.windowPoints.length).toBe(0);
    expect(vm.latestPoint).toBeNull();

    wrapper.unmount();
  });
});
