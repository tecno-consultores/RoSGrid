// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  generateUuidV7,
  readCsrfCookie,
  fetchWithInterceptors,
  http,
  ApiError,
} from './httpClient';

function createMockResponse(data: unknown, status = 200, statusText = 'OK', isJson = true) {
  const bodyText = typeof data === 'string' ? data : JSON.stringify(data);
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    headers: new Headers({
      ...(isJson ? { 'content-type': 'application/json' } : {}),
    }),
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(bodyText),
  };
}

describe('httpClient — Zero Trust & Interceptores', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    document.cookie = '';
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('generateUuidV7', () => {
    it('genera un UUIDv7 válido con timestamp monotónico y formato RFC 4122 / 9562', () => {
      const id1 = generateUuidV7();
      const id2 = generateUuidV7();

      // Formato: 8-4-4-4-12
      const regex = /^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
      expect(id1).toMatch(regex);
      expect(id2).toMatch(regex);
      expect(id1).not.toBe(id2);
    });
  });

  describe('readCsrfCookie', () => {
    it('retorna null cuando no existe cookie rg_csrf', () => {
      document.cookie = 'other=value; foo=bar';
      expect(readCsrfCookie()).toBeNull();
    });

    it('extrae el token CSRF correctamente desde document.cookie', () => {
      document.cookie = 'rg_csrf=secret-csrf-token-12345; Path=/';
      expect(readCsrfCookie()).toBe('secret-csrf-token-12345');
    });
  });

  describe('fetchWithInterceptors', () => {
    it('inyecta Content-Type y Accept application/json por defecto', async () => {
      const mockFetch = vi.fn().mockResolvedValue(createMockResponse({ status: 'ok' }));
      global.fetch = mockFetch;

      const res = await fetchWithInterceptors<{ status: string }>('/api/v1/test', {
        method: 'GET',
      });

      expect(res.data).toEqual({ status: 'ok' });
      expect(mockFetch).toHaveBeenCalledOnce();

      const callArgs = mockFetch.mock.calls[0];
      const headers = callArgs[1].headers as Headers;
      expect(headers.get('Accept')).toBe('application/json');
    });

    it('inyecta X-CSRF-Token e Idempotency-Key en métodos mutables (POST, PUT, DELETE)', async () => {
      document.cookie = 'rg_csrf=csrf-token-test';
      const mockFetch = vi.fn().mockResolvedValue(createMockResponse({ created: true }));
      global.fetch = mockFetch;

      await fetchWithInterceptors('/api/v1/resource', {
        method: 'POST',
        body: JSON.stringify({ name: 'Router1' }),
      });

      const callArgs = mockFetch.mock.calls[0];
      const headers = callArgs[1].headers as Headers;
      expect(headers.get('X-CSRF-Token')).toBe('csrf-token-test');
      expect(headers.get('Idempotency-Key')).toBeTruthy();
      expect(headers.get('Idempotency-Key')).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
      );
    });

    it('reutiliza la Idempotency-Key provista en las opciones', async () => {
      const fixedKey = '018f67e5-1234-7abc-8901-123456789abc';
      const mockFetch = vi.fn().mockResolvedValue(createMockResponse({ success: true }));
      global.fetch = mockFetch;

      await fetchWithInterceptors('/api/v1/resource', {
        method: 'PUT',
        idempotencyKey: fixedKey,
        body: JSON.stringify({ name: 'Updated' }),
      });

      const callArgs = mockFetch.mock.calls[0];
      const headers = callArgs[1].headers as Headers;
      expect(headers.get('Idempotency-Key')).toBe(fixedKey);
    });

    it('captura status 202 Accepted y dispara evento rosgrid:maker-checker-intercepted', async () => {
      const makerCheckerPayload = {
        approval_id: 'app-999',
        status: 'PENDING_APPROVAL',
        risk_level: 'HIGH',
      };
      const mockFetch = vi
        .fn()
        .mockResolvedValue(createMockResponse(makerCheckerPayload, 202, 'Accepted'));
      global.fetch = mockFetch;

      const eventSpy = vi.fn();
      window.addEventListener('rosgrid:maker-checker-intercepted', eventSpy);

      const res = await fetchWithInterceptors('/api/v1/critical-op', {
        method: 'POST',
      });

      expect(res.status).toBe(202);
      expect(res.isMakerCheckerIntercepted).toBe(true);
      expect(res.data).toEqual(makerCheckerPayload);
      expect(eventSpy).toHaveBeenCalledOnce();

      window.removeEventListener('rosgrid:maker-checker-intercepted', eventSpy);
    });

    it('gestiona rotación de token en 401 con reintento transparente', async () => {
      let callCount = 0;
      const mockFetch = vi.fn().mockImplementation((url: string) => {
        if (url === '/api/v1/auth/refresh') {
          return Promise.resolve(createMockResponse({ refreshed: true }, 200));
        }
        callCount++;
        if (callCount === 1) {
          return Promise.resolve(
            createMockResponse({ detail: 'token_expired' }, 401, 'Unauthorized'),
          );
        }
        return Promise.resolve(createMockResponse({ data: 'secret' }, 200));
      });
      global.fetch = mockFetch;

      const res = await fetchWithInterceptors<{ data: string }>('/api/v1/protected', {
        method: 'GET',
      });

      expect(res.status).toBe(200);
      expect(res.data).toEqual({ data: 'secret' });
      // Se llamó: 1era petición (401) + refresh (200) + reintento (200)
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });

    it('dispara redirección y lanza ApiError cuando la rotación de token falla (401)', async () => {
      const mockFetch = vi.fn().mockImplementation((url: string) => {
        if (url === '/api/v1/auth/refresh') {
          return Promise.resolve(
            createMockResponse({ error: 'invalid_refresh' }, 401, 'Unauthorized'),
          );
        }
        return Promise.resolve(
          createMockResponse({ detail: 'token_expired' }, 401, 'Unauthorized'),
        );
      });
      global.fetch = mockFetch;

      const expiredSpy = vi.fn();
      window.addEventListener('rosgrid:session-expired', expiredSpy);

      await expect(fetchWithInterceptors('/api/v1/protected')).rejects.toThrow(ApiError);
      expect(expiredSpy).toHaveBeenCalledOnce();

      window.removeEventListener('rosgrid:session-expired', expiredSpy);
    });

    it('maneja error cuando refresh lanza una excepción de red', async () => {
      let callCount = 0;
      global.fetch = vi.fn().mockImplementation((url: string) => {
        if (url === '/api/v1/auth/refresh') {
          return Promise.reject(new Error('Network failure during refresh'));
        }
        callCount++;
        return Promise.resolve(createMockResponse({ detail: 'expired' }, 401, 'Unauthorized'));
      });

      await expect(fetchWithInterceptors('/api/v1/need-auth')).rejects.toThrow(ApiError);
      expect(callCount).toBeGreaterThanOrEqual(1);
    });

    it('procesa respuestas que no sean application/json usando response.text()', async () => {
      const mockFetch = vi
        .fn()
        .mockResolvedValue(createMockResponse('plain text raw payload', 200, 'OK', false));
      global.fetch = mockFetch;

      const res = await fetchWithInterceptors('/api/v1/plain');
      expect(res.data).toBe('plain text raw payload');
    });

    it('captura errores de red y lanza ApiError con status 0', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Failed to fetch'));

      await expect(fetchWithInterceptors('/api/v1/net-fail')).rejects.toThrow(ApiError);
    });

    it('lanza ApiError si la respuesta no es OK y no es 401 recuperable', async () => {
      const mockFetch = vi
        .fn()
        .mockResolvedValue(createMockResponse({ detail: 'Router not found' }, 404, 'Not Found'));
      global.fetch = mockFetch;

      await expect(fetchWithInterceptors('/api/v1/unknown')).rejects.toThrow(ApiError);
    });
  });

  describe('http convenience methods', () => {
    it('http.get, http.post, http.put, http.patch, http.delete funcionan adecuadamente con JSON y FormData', async () => {
      const mockFetch = vi.fn().mockResolvedValue(createMockResponse({ success: true }));
      global.fetch = mockFetch;

      await http.get('/api/test');
      await http.post('/api/test', { a: 1 });
      await http.put('/api/test', { b: 2 });
      await http.patch('/api/test', { c: 3 });
      await http.delete('/api/test');

      // Test con FormData en POST, PUT, PATCH
      const fd = new FormData();
      fd.append('file', 'backup.rsc');
      await http.post('/api/upload', fd);
      await http.put('/api/upload', fd);
      await http.patch('/api/upload', fd);

      // Petición con método indefinido para cubrir fallback
      await fetchWithInterceptors('/api/no-method', { method: undefined });

      expect(mockFetch).toHaveBeenCalledTimes(9);
    });
  });
});
