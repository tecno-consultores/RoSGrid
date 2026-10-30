// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { http } from '@/api/httpClient';
import IpAddressesAndDhcpView from './IpAddressesAndDhcpView.vue';
import Ipv6DualStackView from './Ipv6DualStackView.vue';

const mockPush = vi.fn();
vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { routerId: 'r-01' },
    path: '/routers/r-01/webfig/ip',
  }),
  useRouter: () => ({
    push: mockPush,
  }),
}));

vi.mock('@/composables/useI18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}));

describe('WebFig Layer 3: IpAddressesAndDhcpView & Ipv6DualStackView', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('IpAddressesAndDhcpView — gestiona Direcciones IP, Leases, Asistente DHCP y DNS', async () => {
    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('/ip/addresses')) {
        return {
          status: 200,
          data: [
            { id: '*1', address: '192.168.88.1/24', network: '192.168.88.0', interface: 'bridge1', disabled: false },
          ],
          headers: new Headers(),
        };
      } else if (url.includes('/dhcp-server/leases')) {
        return {
          status: 200,
          data: [
            { id: '*l1', address: '192.168.88.50', 'mac-address': '00:11:22:33:44:55', 'host-name': 'laptop-user', dynamic: true },
          ],
          headers: new Headers(),
        };
      } else if (url.includes('/dhcp-servers')) {
        return {
          status: 200,
          data: [
            { id: '*s1', name: 'dhcp-lan', interface: 'bridge1', 'address-pool': 'pool-lan', 'lease-time': '12h', disabled: false },
          ],
          headers: new Headers(),
        };
      } else if (url.includes('/dhcp-server/networks')) {
        return {
          status: 200,
          data: [
            { id: '*n1', address: '192.168.88.0/24', gateway: '192.168.88.1', 'dns-server': '8.8.8.8' },
          ],
          headers: new Headers(),
        };
      } else if (url.includes('/dhcp-clients')) {
        return {
          status: 200,
          data: [
            { id: '*c1', interface: 'ether1', address: '203.0.113.5/24', gateway: '203.0.113.1', status: 'bound' },
          ],
          headers: new Headers(),
        };
      } else if (url.includes('/pools')) {
        return {
          status: 200,
          data: [
            { id: '*p1', name: 'pool-lan', ranges: '192.168.88.10-192.168.88.254' },
          ],
          headers: new Headers(),
        };
      } else if (url.includes('/dns')) {
        return {
          status: 200,
          data: {
            config: { servers: '8.8.8.8,1.1.1.1', 'allow-remote-requests': 'yes' },
            static_records: [{ id: '*d1', name: 'router.lan', address: '192.168.88.1', ttl: '1d' }],
          },
          headers: new Headers(),
        };
      } else if (url.includes('/arp')) {
        return {
          status: 200,
          data: [
            { id: '*a1', address: '192.168.88.50', 'mac-address': '00:11:22:33:44:55', interface: 'bridge1', dynamic: true },
          ],
          headers: new Headers(),
        };
      }
      return { status: 200, data: [], headers: new Headers() };
    });

    vi.spyOn(http, 'post').mockResolvedValue({ status: 200, data: { ret: '*1' }, headers: new Headers() });
    vi.spyOn(http, 'delete').mockResolvedValue({ status: 200, data: {}, headers: new Headers() });

    const wrapper = mount(IpAddressesAndDhcpView);
    await flushPromises();

    expect(wrapper.text()).toContain('192.168.88.1/24');

    const vm = wrapper.vm as any;

    // 1. Asignar Dirección IP
    vm.newAddress = { address: '10.0.0.1/24', interface: 'ether2', comment: 'DMZ', disabled: false };
    await vm.handleCreateAddress();
    await flushPromises();
    expect(vm.actionMessage).toContain('10.0.0.1/24');

    // 2. Eliminar Dirección IP
    vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
    await vm.handleDeleteAddress({ id: '*1', address: '192.168.88.1/24' });
    await flushPromises();

    // 3. Conmutar a Servidor DHCP
    vm.setTab('dhcp-server');
    await flushPromises();
    expect(vm.activeTab).toBe('dhcp-server');

    // Make Lease Static
    await vm.handleMakeLeaseStatic({ id: '*l1', address: '192.168.88.50', 'mac-address': '00:11:22:33:44:55' });
    await flushPromises();

    // Delete Lease
    vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
    await vm.handleDeleteLease({ id: '*l1', address: '192.168.88.50' });
    await flushPromises();

    // Subpestaña Servidores
    vm.setDhcpSubtab('servers');
    await flushPromises();
    vm.newServer = { name: 'dhcp-wifi', interface: 'wlan1', address_pool: 'pool-wifi', lease_time: '6h', disabled: false };
    await vm.handleCreateServer();
    await flushPromises();

    vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
    await vm.handleDeleteServer({ id: '*s1', name: 'dhcp-lan' });
    await flushPromises();

    // Subpestaña Redes
    vm.setDhcpSubtab('networks');
    await flushPromises();
    vm.newNetwork = { address: '10.10.10.0/24', gateway: '10.10.10.1', dns_server: '8.8.8.8', domain: '', comment: '' };
    await vm.handleCreateNetwork();
    await flushPromises();

    vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
    await vm.handleDeleteNetwork({ id: '*n1', address: '192.168.88.0/24' });
    await flushPromises();

    // Asistente DHCP Setup Completo
    await vm.handleExecuteDhcpWizard();
    await flushPromises();

    // 4. Clientes DHCP WAN
    vm.setTab('dhcp-client');
    await flushPromises();
    vm.newClient = { interface: 'ether3', add_default_route: true, use_peer_dns: true, use_peer_ntp: true, comment: 'LTE' };
    await vm.handleCreateClient();
    await flushPromises();

    await vm.handleRenewClient({ id: '*c1', interface: 'ether1' });
    await flushPromises();

    await vm.handleReleaseClient({ id: '*c1', interface: 'ether1' });
    await flushPromises();

    vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
    await vm.handleDeleteClient({ id: '*c1', interface: 'ether1' });
    await flushPromises();

    // 5. Pools & DNS & ARP
    vm.setTab('pools');
    await flushPromises();
    vm.newPool = { name: 'pool-vpn', ranges: '172.16.0.10-172.16.0.50' };
    await vm.handleCreatePool();
    await flushPromises();

    // Editar y eliminar Pool IP
    vm.openEditPoolModal({ id: '*p1', name: 'pool-lan', ranges: '192.168.88.10-192.168.88.254', 'next-pool': '' });
    await vm.handleUpdatePool();
    await flushPromises();
    vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
    await vm.handleDeletePool({ id: '*p1', name: 'pool-lan' });
    await flushPromises();

    // Editar Red DHCP y Cliente DHCP
    vm.openEditNetworkModal({
      id: '*net1',
      address: '192.168.88.0/24',
      gateway: '192.168.88.1',
      'dns-server': '1.1.1.1',
      domain: 'lan.corp',
      'ntp-server': '192.168.88.1',
      comment: 'LAN',
    });
    await vm.handleUpdateNetwork();
    await flushPromises();

    vm.openEditClientModal({
      id: '*c1',
      interface: 'ether1',
      'add-default-route': 'yes',
      'use-peer-dns': true,
      'use-peer-ntp': true,
      'default-route-distance': 1,
      disabled: false,
      comment: 'WAN',
    });
    await vm.handleUpdateClient();
    await flushPromises();

    vm.setTab('dns');
    await flushPromises();
    await vm.handleFlushDnsCache();
    await flushPromises();

    // Editar parámetros DNS y registros DNS estáticos
    vm.openEditDnsModal();
    await vm.handleUpdateDnsSettings();
    await flushPromises();

    vm.newDnsStatic = { name: 'router.lan', address: '192.168.88.1', ttl: '1d', comment: 'Local' };
    await vm.handleCreateDnsStatic();
    await flushPromises();

    vm.openEditDnsStaticModal({ id: '*dns1', name: 'router.lan', address: '192.168.88.1', ttl: '1d', disabled: false, comment: 'Local' });
    await vm.handleUpdateDnsStatic();
    await flushPromises();

    vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
    await vm.handleDeleteDnsStatic({ id: '*dns1', name: 'router.lan' });
    await flushPromises();

    vm.setTab('arp');
    await flushPromises();
    await vm.handleMakeArpStatic({ address: '192.168.88.50', 'mac-address': '00:11:22:33:44:55', interface: 'bridge1' });
    await flushPromises();
  });

  it('Ipv6DualStackView — gestiona Direcciones IPv6, DHCPv6-PD, Servidores y Vecinos NDP', async () => {
    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('/ipv6/addresses')) {
        return {
          status: 200,
          data: [
            { id: '*v6_1', address: '2001:db8:acad::1/64', interface: 'bridge1', advertise: true, 'eui-64': false, disabled: false },
          ],
          headers: new Headers(),
        };
      } else if (url.includes('/ipv6/dhcp-clients')) {
        return {
          status: 200,
          data: [
            { id: '*v6_c1', interface: 'ether1', request: 'prefix', 'pool-name': 'pool-v6-delegated', 'pool-prefix-length': 64, prefix: '2800:bf0:80::/56', status: 'bound' },
          ],
          headers: new Headers(),
        };
      } else if (url.includes('/ipv6/dhcp-servers')) {
        return {
          status: 200,
          data: [
            { id: '*v6_s1', name: 'dhcp6-lan', interface: 'bridge1', 'address-pool': 'pool-v6-delegated', 'lease-time': '24h', disabled: false },
          ],
          headers: new Headers(),
        };
      } else if (url.includes('/ipv6/pools')) {
        return {
          status: 200,
          data: [
            { id: '*v6_p1', name: 'pool-v6-static', prefix: '2001:db8:cafe::/48', 'prefix-length': 64 },
          ],
          headers: new Headers(),
        };
      } else if (url.includes('/ipv6/neighbors')) {
        return {
          status: 200,
          data: [
            { id: '*neigh1', address: 'fe80::1', 'mac-address': '00:aa:bb:cc:dd:ee', interface: 'ether1', status: 'reachable' },
          ],
          headers: new Headers(),
        };
      } else if (url.includes('/ipv6/nd')) {
        return {
          status: 200,
          data: [
            { id: '*nd1', interface: 'bridge1', 'ra-interval': '3m-10m' },
          ],
          headers: new Headers(),
        };
      }
      return { status: 200, data: [], headers: new Headers() };
    });

    vi.spyOn(http, 'post').mockResolvedValue({ status: 200, data: { ret: '*1' }, headers: new Headers() });
    vi.spyOn(http, 'delete').mockResolvedValue({ status: 200, data: {}, headers: new Headers() });

    const wrapper = mount(Ipv6DualStackView);
    await flushPromises();

    expect(wrapper.text()).toContain('2001:db8:acad::1/64');

    const vm = wrapper.vm as any;

    // 1. Asignar IPv6
    vm.newAddress = { address: '2001:db8:beef::1/64', interface: 'ether2', advertise: true, eui_64: false, comment: 'DMZ IPv6', disabled: false };
    await vm.handleCreateAddress();
    await flushPromises();
    expect(vm.actionMessage).toContain('2001:db8:beef::1/64');

    // 2. Eliminar IPv6
    vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
    await vm.handleDeleteAddress({ id: '*v6_1', address: '2001:db8:acad::1/64' });
    await flushPromises();

    // 3. DHCPv6 Client & PD
    vm.setTab('dhcp-client');
    await flushPromises();
    vm.newClient = { interface: 'ether2', request: 'prefix', pool_name: 'pool-v6-isp2', pool_prefix_length: 64, add_default_route: true, comment: '' };
    await vm.handleCreateDhcpClient();
    await flushPromises();

    vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
    await vm.handleDeleteDhcpClient({ id: '*v6_c1', interface: 'ether1' });
    await flushPromises();

    // 4. DHCPv6 Server
    vm.setTab('dhcp-server');
    await flushPromises();
    vm.newServer = { name: 'dhcp6-dmz', interface: 'ether3', address_pool: 'pool-v6-dmz', lease_time: '12h', disabled: false };
    await vm.handleCreateDhcpServer();
    await flushPromises();

    vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
    await vm.handleDeleteDhcpServer({ id: '*v6_s1', name: 'dhcp6-lan' });
    await flushPromises();

    // 5. Pools IPv6
    vm.setTab('pools');
    await flushPromises();
    vm.newPool = { name: 'pool-v6-new', prefix: '2001:db8:dead::/48', prefix_length: 64 };
    await vm.handleCreatePool();
    await flushPromises();

    vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
    await vm.handleDeletePool({ id: '*v6_p1', name: 'pool-v6-static' });
    await flushPromises();

    // 6. Vecinos NDP
    vm.setTab('ndp');
    await flushPromises();
    expect(vm.ipv6Neighbors.length).toBe(1);

    // 7. Redirección a Firewall
    vm.goToFirewall();
    expect(mockPush).toHaveBeenCalledWith('/routers/r-01/webfig/firewall');
  });
});
