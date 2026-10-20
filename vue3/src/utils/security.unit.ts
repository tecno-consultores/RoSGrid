// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect } from 'vitest';
import { isSafeUrl, sanitizeUrl, sanitizeObject, createSafeRecord } from './security';

describe('Security Utilities (XSS and Prototype Pollution Defense)', () => {
  describe('isSafeUrl', () => {
    it('permits secure absolute HTTPS and HTTP URLs', () => {
      expect(isSafeUrl('https://www.tecnoconsultores.net')).toBe(true);
      expect(isSafeUrl('http://router.lan:8080/rest/system')).toBe(true);
    });

    it('permits safe communication schemes mailto: and tel:', () => {
      expect(isSafeUrl('mailto:noc@rosgrid.org')).toBe(true);
      expect(isSafeUrl('tel:+582125550100')).toBe(true);
    });

    it('permits internal relative paths and fragment identifiers', () => {
      expect(isSafeUrl('/operations/bulk')).toBe(true);
      expect(isSafeUrl('#main-content')).toBe(true);
    });

    it('strictly blocks javascript: execution payloads', () => {
      expect(isSafeUrl('javascript:alert(document.cookie)')).toBe(false);
      expect(isSafeUrl('JAVASCRIPT:console.log(1)')).toBe(false);
      expect(isSafeUrl(' javascript:void(0)')).toBe(false);
    });

    it('strictly blocks data: URIs and vbscript:', () => {
      expect(isSafeUrl('data:text/html,<script>alert(1)</script>')).toBe(false);
      expect(isSafeUrl('vbscript:msgbox(1)')).toBe(false);
      expect(isSafeUrl('file:///etc/passwd')).toBe(false);
    });

    it('blocks protocol-relative URLs that could lead to open redirects', () => {
      expect(isSafeUrl('//evil.attacker.com/exploit.js')).toBe(false);
    });

    it('handles null, undefined, and empty inputs gracefully', () => {
      expect(isSafeUrl(null)).toBe(false);
      expect(isSafeUrl(undefined)).toBe(false);
      expect(isSafeUrl('')).toBe(false);
      expect(isSafeUrl('   ')).toBe(false);
    });
  });

  describe('sanitizeUrl', () => {
    it('returns original URL when safe', () => {
      expect(sanitizeUrl('https://mikrotik.com')).toBe('https://mikrotik.com');
      expect(sanitizeUrl('/dashboard')).toBe('/dashboard');
    });

    it('returns fallback when malicious URL is detected', () => {
      expect(sanitizeUrl('javascript:stealToken()')).toBe('#');
      expect(sanitizeUrl('data:text/plain,malicious', '/safe-fallback')).toBe('/safe-fallback');
    });
  });

  describe('sanitizeObject (Prototype Pollution Defense)', () => {
    it('strips __proto__, constructor, and prototype from parsed objects', () => {
      const maliciousJson = JSON.parse(
        '{"name": "Valid", "__proto__": {"polluted": true}, "constructor": "bad", "prototype": "bad"}',
      );
      const sanitized = sanitizeObject(maliciousJson);

      expect(sanitized.name).toBe('Valid');
      expect(Object.prototype.hasOwnProperty.call(sanitized, '__proto__')).toBe(false);
      expect(Object.prototype.hasOwnProperty.call(sanitized, 'constructor')).toBe(false);
      expect(Object.prototype.hasOwnProperty.call(sanitized, 'prototype')).toBe(false);
      expect((Object.prototype as Record<string, unknown>).polluted).toBeUndefined();
    });

    it('recursively sanitizes nested objects and arrays', () => {
      const complexData = {
        routers: [{ identity: 'Core-01', __proto__: { admin: true } }, { identity: 'Edge-02' }],
      };
      const cleaned = sanitizeObject(complexData);
      expect(cleaned.routers[0].identity).toBe('Core-01');
      expect((Object.prototype as Record<string, unknown>).admin).toBeUndefined();
    });

    it('passes through primitives and null safely', () => {
      expect(sanitizeObject('text')).toBe('text');
      expect(sanitizeObject(1234)).toBe(1234);
      expect(sanitizeObject(null)).toBe(null);
    });
  });

  describe('createSafeRecord', () => {
    it('creates an object with no prototype (null prototype)', () => {
      const record = createSafeRecord<string>();
      expect(Object.getPrototypeOf(record)).toBeNull();
      record['key'] = 'val';
      expect(record['key']).toBe('val');
      expect(record['toString']).toBeUndefined();
    });
  });
});
