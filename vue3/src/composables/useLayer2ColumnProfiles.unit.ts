// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach } from 'vitest';
import { useLayer2ColumnProfiles } from './useLayer2ColumnProfiles';

const CERT_PATH = 'certificate';
const SNMP_PATH = 'snmp/community';

describe('useLayer2ColumnProfiles composable (Spec 54 — 27.16.7)', () => {
  beforeEach(() => {
    const { clearColumnProfile } = useLayer2ColumnProfiles();
    clearColumnProfile(CERT_PATH);
    clearColumnProfile(SNMP_PATH);
  });

  it('genera la clave normalizada por tenant y ruta RouterOS', () => {
    const { getStorageKey } = useLayer2ColumnProfiles();
    expect(getStorageKey('/certificate/', 'acme')).toBe('rg_l2_cols:acme:certificate');
    expect(getStorageKey('ip/dhcp-server/lease')).toBe(
      'rg_l2_cols:default:ip/dhcp-server/lease',
    );
  });

  it('guarda, carga y limpia perfiles de columnas en almacenamiento persistente', () => {
    const { saveColumnProfile, loadSavedColumns, clearColumnProfile, hasSavedProfile } =
      useLayer2ColumnProfiles();

    expect(hasSavedProfile(CERT_PATH)).toBe(false);
    expect(loadSavedColumns(CERT_PATH)).toEqual([]);

    saveColumnProfile(CERT_PATH, ['name', 'common-name', 'expires-after', 'name']);
    expect(hasSavedProfile(CERT_PATH)).toBe(true);
    expect(loadSavedColumns(CERT_PATH)).toEqual(['name', 'common-name', 'expires-after']);

    clearColumnProfile(CERT_PATH);
    expect(hasSavedProfile(CERT_PATH)).toBe(false);
    expect(loadSavedColumns(CERT_PATH)).toEqual([]);
  });

  it('maneja JSON corrupto retornando arreglo vacío', () => {
    const { loadSavedColumns, getStorageKey, writeRawProfileForTesting } =
      useLayer2ColumnProfiles();
    writeRawProfileForTesting(getStorageKey(SNMP_PATH), '{corrupted-json');
    expect(loadSavedColumns(SNMP_PATH)).toEqual([]);
  });
});
