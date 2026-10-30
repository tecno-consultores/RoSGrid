// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

export interface Layer2TemplatePreset {
  id: string;
  label: string;
  description: string;
  values: Record<string, unknown>;
}

/**
 * Catálogo de plantillas rápidas en 1 clic por submenú de Capa 2 (Spec 54 — 27.16.7).
 */
export const LAYER2_PRESETS_CATALOG: Record<string, Layer2TemplatePreset[]> = {
  certificate: [
    {
      id: 'cert-ca-root',
      label: '🏛️ CA Interna Corporativa (RSA 4096 / 10 años)',
      description: 'Autoridad Certificadora raíz para túneles IPSec y API-SSL.',
      values: {
        name: 'rosgrid-corp-ca',
        'common-name': 'RoSGrid Root CA',
        'key-type': 'rsa',
        'key-size': '4096',
        'days-valid': 3650,
        trusted: true,
      },
    },
    {
      id: 'cert-api-ssl-node',
      label: '🔒 Certificado Nodo API-SSL (ECDSA P-256 / 1 año)',
      description: 'Certificado de servidor ligero para gestión REST HTTPS Zero-Trust.',
      values: {
        name: 'node-api-ssl',
        'common-name': 'router.noc.internal',
        'key-type': 'prime256v1',
        'days-valid': 365,
        trusted: true,
      },
    },
  ],
  'snmp/community': [
    {
      id: 'snmp-v3-aes-sha',
      label: '🛡️ SNMPv3 Privado (AES-128 + SHA1 Solo Lectura)',
      description: 'Perfil endurecido para monitoreo NOC sin exponer cadenas en texto plano.',
      values: {
        name: 'noc-v3-ro',
        addresses: '10.255.0.0/24',
        security: 'private',
        'read-access': true,
        'write-access': false,
        'authentication-protocol': 'SHA1',
        'encryption-protocol': 'AES',
      },
    },
  ],
  'mpls/interface': [
    {
      id: 'mpls-jumbo-core',
      label: '🚀 Enlace Core MPLS (MTU 1530)',
      description: 'Interfaz MPLS habilitada con margen para etiquetas VPLS/L3VPN.',
      values: {
        interface: 'ether1',
        'mpls-mtu': 1530,
        disabled: false,
      },
    },
  ],
  'ip/ipsec/profile': [
    {
      id: 'ipsec-ikev2-gcm',
      label: '🔐 Perfil IKEv2 Suite-B (SHA256 + AES-256 + modp2048)',
      description: 'Fase 1 endurecida compatible con sitios corporativos y nube.',
      values: {
        name: 'noc-ike2-profile',
        'hash-algorithm': 'sha256',
        'enc-algorithm': 'aes-256',
        'dh-group': 'modp2048',
        lifetime: '8h',
        'nat-traversal': true,
      },
    },
  ],
  container: [
    {
      id: 'container-netshoot',
      label: '🐳 Sonda Diagnóstica Alpine Netshoot',
      description: 'Contenedor OCI aislado en veth para pruebas de red desde el router.',
      values: {
        'remote-image': 'nicolaka/netshoot:latest',
        interface: 'veth1',
        'root-dir': 'disk1/netshoot',
        'start-on-boot': false,
        logging: true,
      },
    },
  ],
};

export function getPresetsForRosPath(rosPath: string): Layer2TemplatePreset[] {
  const clean = rosPath.replace(/^\/+|\/+$/g, '');
  const found = Object.entries(LAYER2_PRESETS_CATALOG).find(([k]) => k === clean);
  return found ? found[1] : [];
}
