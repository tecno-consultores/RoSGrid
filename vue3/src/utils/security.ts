// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

/**
 * Módulo de Utilidades de Seguridad para Vue 3 (RoSGrid)
 * Proporciona defensas en profundidad contra XSS, inyección de URLs maliciosas
 * y Prototype Pollution en el frontend.
 */

const ALLOWED_PROTOCOLS = new Set(['http:', 'https:', 'mailto:', 'tel:']);
const DANGEROUS_PROTOCOLS_REGEX = /^(javascript|data|vbscript|file):/i;

/**
 * Valida si una URL es segura para ser enlazada en atributos :href o :src.
 * Rechaza esquemas ejecutables como javascript: o data:
 */
export function isSafeUrl(url: string | null | undefined): boolean {
  if (!url || typeof url !== 'string') {
    return false;
  }

  const trimmed = url.trim();
  if (trimmed === '' || DANGEROUS_PROTOCOLS_REGEX.test(trimmed)) {
    return false;
  }

  // Rutas relativas seguras (ej. /inventory, #main-content)
  if (trimmed.startsWith('/') || trimmed.startsWith('#')) {
    return !trimmed.startsWith('//'); // Evitar Protocol-Relative URLs externas si no están autorizadas
  }

  try {
    const parsed = new URL(trimmed);
    return ALLOWED_PROTOCOLS.has(parsed.protocol);
  } catch {
    return false;
  }
}

/**
 * Sanitiza una URL devolviendo un fallback seguro si no pasa la validación.
 */
export function sanitizeUrl(url: string | null | undefined, fallback = '#'): string {
  if (isSafeUrl(url)) {
    return (url as string).trim();
  }
  return fallback;
}

const FORBIDDEN_KEYS = new Set(['__proto__', 'constructor', 'prototype']);

/**
 * Sanitiza recursivamente un objeto o diccionario eliminando llaves peligrosas
 * que causan Prototype Pollution (__proto__, constructor, prototype).
 */
export function sanitizeObject<T>(input: T): T {
  if (input === null || typeof input !== 'object') {
    return input;
  }

  if (Array.isArray(input)) {
    return input.map((item) => sanitizeObject(item)) as unknown as T;
  }

  const result = Object.create(null) as Record<string, unknown>;
  const source = input as Record<string, unknown>;

  for (const [key, value] of Object.entries(source)) {
    if (!FORBIDDEN_KEYS.has(key)) {
      // eslint-disable-next-line security/detect-object-injection
      result[key] = sanitizeObject(value);
    }
  }

  return result as T;
}

/**
 * Crea un diccionario de datos puro con prototipo nulo (Object.create(null)),
 * completamente inmune a ataques de contaminación de prototipo.
 */
export function createSafeRecord<V = unknown>(): Record<string, V> {
  return Object.create(null) as Record<string, V>;
}

/**
 * Sanitiza y escapa caracteres especiales HTML para prevenir Cross-Site Scripting (XSS)
 * en inyecciones directas de DOM (ej. Popups de Leaflet, tooltips o manipulación innerHTML).
 */
export function escapeHtml(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }
  const str = typeof value === 'string' ? value : String(value);
  return str
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}
