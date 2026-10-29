// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

export interface RequestOptions extends RequestInit {
  idempotencyKey?: string;
  skipAuthRefresh?: boolean;
}

export interface ApiResponse<T = unknown> {
  data: T;
  status: number;
  headers: Headers;
  isMakerCheckerIntercepted?: boolean;
}

export class ApiError extends Error {
  public readonly detail?: string;

  constructor(
    public readonly status: number,
    public readonly statusText: string,
    public readonly data: unknown,
    message?: string,
  ) {
    let detailMsg: string | undefined;
    if (data && typeof data === 'object' && 'detail' in (data as Record<string, unknown>)) {
      const d = (data as Record<string, unknown>).detail;
      if (typeof d === 'string') {
        detailMsg = d;
      } else if (Array.isArray(d)) {
        detailMsg = (d as Array<Record<string, unknown>>)
          .map((item) => (typeof item?.msg === 'string' ? item.msg : JSON.stringify(item)))
          .join(', ');
      }
    }
    super(message || detailMsg || `HTTP ${status}: ${statusText}`);
    this.name = 'ApiError';
    this.detail = detailMsg;
  }
}

// ---------------------------------------------------------------------------
// Helpers Interceptores
// ---------------------------------------------------------------------------

export function readCsrfCookie(): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/(?:^|;\s*)rg_csrf=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

function readStoredCsrfToken(): string | null {
  if (typeof localStorage === 'undefined') return null;
  try {
    return localStorage.getItem('rosgrid_csrf');
  } catch {
    return null;
  }
}

export function generateUuidV7(): string {
  const bytes = new Uint8Array(16);
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    crypto.getRandomValues(bytes);
  }
  const now = Date.now();
  const high = Math.floor(now / 0x100000000);
  const low = now & 0xffffffff;

  bytes[0] = (high >> 8) & 0xff;
  bytes[1] = high & 0xff;
  bytes[2] = (low >> 24) & 0xff;
  bytes[3] = (low >> 16) & 0xff;
  bytes[4] = (low >> 8) & 0xff;
  bytes[5] = low & 0xff;

  bytes[6] = 0x70 | (bytes[6] & 0x0f);
  bytes[8] = 0x80 | (bytes[8] & 0x3f);

  const hex: string[] = [];
  for (let i = 0; i < 16; i++) {
    hex.push(bytes[i].toString(16).padStart(2, '0'));
  }
  return [
    hex.slice(0, 4).join(''),
    hex.slice(4, 6).join(''),
    hex.slice(6, 8).join(''),
    hex.slice(8, 10).join(''),
    hex.slice(10, 16).join(''),
  ].join('-');
}

function isMutableMethod(method?: string): boolean {
  if (!method) return false;
  const m = method.toUpperCase();
  return m === 'POST' || m === 'PUT' || m === 'PATCH' || m === 'DELETE';
}

function buildHeaders(method: string, options: RequestOptions, csrfToken?: string | null): Headers {
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }
  if (isMutableMethod(method)) {
    const token = csrfToken || readCsrfCookie() || readStoredCsrfToken();
    if (token) headers.set('X-CSRF-Token', token);
    if (!headers.has('Idempotency-Key')) {
      headers.set('Idempotency-Key', options.idempotencyKey || generateUuidV7());
    }
  }
  return headers;
}

// ---------------------------------------------------------------------------
// Singleton Refresh Token Handler
// ---------------------------------------------------------------------------

export function getBaseUrl(): string {
  if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) {
    return String(import.meta.env.VITE_API_BASE_URL).replace(/\/+$/, '');
  }
  return '';
}

export function resolveUrl(path: string): string {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const baseUrl = getBaseUrl();
  const normalizedPath = path.startsWith('/') ? path : '/' + path;
  return `${baseUrl}${normalizedPath}`;
}

let refreshPromiseSingleton: Promise<boolean> | null = null;

async function executeRefreshTokenRotation(): Promise<boolean> {
  try {
    const res = await fetch(resolveUrl('/api/v1/auth/refresh'), {
      method: 'POST',
      credentials: 'include',
      headers: { Accept: 'application/json' },
    });
    if (res.ok && typeof localStorage !== 'undefined' && typeof res.json === 'function') {
      try {
        const body = await res.json();
        if (body?.csrf_token) {
          localStorage.setItem('rosgrid_csrf', String(body.csrf_token));
        }
      } catch {
        // Ignora si la respuesta no contiene JSON
      }
    }
    return res.ok;
  } catch {
    return false;
  }
}

async function requestTokenRefresh(): Promise<boolean> {
  if (!refreshPromiseSingleton) {
    refreshPromiseSingleton = executeRefreshTokenRotation().finally(() => {
      refreshPromiseSingleton = null;
    });
  }
  return refreshPromiseSingleton;
}

function notifyMakerChecker(payload: unknown): void {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('rosgrid:maker-checker-intercepted', { detail: payload }));
  }
}

function triggerSessionExpiredRedirect(): void {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('rosgrid:session-expired'));
    if (window.location.pathname !== '/login') {
      window.location.href = '/login?reason=session_expired';
    }
  }
}

// ---------------------------------------------------------------------------
// Cliente Core HTTP
// ---------------------------------------------------------------------------

export async function request<T = unknown>(
  url: string,
  options: RequestOptions = {},
): Promise<ApiResponse<T>> {
  const method = (options.method || 'GET').toUpperCase();
  const headers = buildHeaders(method, options);

  const init: RequestInit = {
    ...options,
    method,
    headers,
    credentials: 'include',
  };

  const startTime = typeof performance !== 'undefined' ? performance.now() : Date.now();
  let response: Response;
  try {
    response = await fetch(resolveUrl(url), init);
  } catch (netErr) {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('rosgrid:api-health-event', {
          detail: { ok: false, status: 0, latencyMs: null, url },
        }),
      );
    }
    throw new ApiError(0, 'NetworkError', null, (netErr as Error).message);
  }

  const durationMs = Math.round(
    (typeof performance !== 'undefined' ? performance.now() : Date.now()) - startTime,
  );
  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent('rosgrid:api-health-event', {
        detail: { ok: response.ok, status: response.status, latencyMs: durationMs, url },
      }),
    );
  }

  // Interceptor 3: Manejo 401 con Singleton Refresh
  const isAuthEndpoint =
    url.includes('/api/v1/auth/login') ||
    url.includes('/api/v1/auth/2fa/verify') ||
    url.includes('/api/v1/auth/refresh');

  if (response.status === 401 && !isAuthEndpoint && !options.skipAuthRefresh) {
    const refreshed = await requestTokenRefresh();
    if (refreshed) {
      return request<T>(url, { ...options, skipAuthRefresh: true });
    }
    triggerSessionExpiredRedirect();
    throw new ApiError(401, 'Unauthorized', null, 'Sesión expirada o revocada');
  }

  let data: T;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    data = (await response.json()) as T;
  } else {
    data = (await response.text()) as unknown as T;
  }

  // Interceptor 4: HTTP 202 Accepted (Maker-Checker)
  const isIntercepted =
    response.status === 202 ||
    (typeof data === 'object' &&
      data !== null &&
      (data as Record<string, unknown>).status === 'INTERCEPTED_FOR_APPROVAL');

  if (isIntercepted) {
    notifyMakerChecker(data);
  }

  if (!response.ok && response.status !== 202) {
    throw new ApiError(response.status, response.statusText, data);
  }

  return {
    data,
    status: response.status,
    headers: response.headers,
    isMakerCheckerIntercepted: Boolean(isIntercepted),
  };
}

export const httpClient = {
  get<T = unknown>(url: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return request<T>(url, { ...options, method: 'GET' });
  },
  post<T = unknown>(
    url: string,
    body?: unknown,
    options?: RequestOptions,
  ): Promise<ApiResponse<T>> {
    const payload = body instanceof FormData ? body : JSON.stringify(body);
    return request<T>(url, { ...options, method: 'POST', body: payload });
  },
  put<T = unknown>(url: string, body?: unknown, options?: RequestOptions): Promise<ApiResponse<T>> {
    const payload = body instanceof FormData ? body : JSON.stringify(body);
    return request<T>(url, { ...options, method: 'PUT', body: payload });
  },
  patch<T = unknown>(
    url: string,
    body?: unknown,
    options?: RequestOptions,
  ): Promise<ApiResponse<T>> {
    const payload = body instanceof FormData ? body : JSON.stringify(body);
    return request<T>(url, { ...options, method: 'PATCH', body: payload });
  },
  delete<T = unknown>(url: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return request<T>(url, { ...options, method: 'DELETE' });
  },
};

export { request as fetchWithInterceptors, httpClient as http };
