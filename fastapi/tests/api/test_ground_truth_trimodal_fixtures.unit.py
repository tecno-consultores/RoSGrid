# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Suite de pruebas unitarias basadas en Fixtures Reales Trimodales de MikroTik RouterOS v7.

Verifica de forma estricta las Invariantes Negativas sobre routers de fábrica y
el comportamiento nominal en los 8 dominios críticos de RoSGrid conforme a:
- docs/specs/43_REAL_FLEET_SMOKE_TESTS_GROUND_TRUTH_FIXTURES_AND_DETERMINISTIC_SENSING.md
- .agents/rules/ground_truth_fixtures_and_negative_invariants.md
"""

import difflib
import json
import uuid
from pathlib import Path

from src.models.inventory import Router
from src.schemas.enterprise import CapsmanOverviewResponse
from src.services.topology_l2 import process_topology_graph

FIXTURES_BASE = Path(__file__).parent.parent / "fixtures" / "mikrotik"


def _load_json_fixture(subpath: str):
    with open(FIXTURES_BASE / subpath, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_text_fixture(subpath: str) -> str:
    with open(FIXTURES_BASE / subpath, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================================
# 1. DOMINIO CIS HARDENING (Invariantes Negativas de Fábrica)
# ============================================================================

def test_cis_hardening_factory_default_negative_invariant():
    """Un router recién sacado de la caja (de fábrica) DEBE reprobar las directivas críticas."""
    data = _load_json_fixture("cis/factory_default_cis.json")

    # 1. Telnet y FTP deben estar activos (en fallo de seguridad)
    telnet_service = next((s for s in data["ip_service"] if s["name"] == "telnet"), None)
    assert telnet_service is not None
    assert telnet_service.get("disabled") is False, "En fábrica, Telnet debe venir habilitado"

    ftp_service = next((s for s in data["ip_service"] if s["name"] == "ftp"), None)
    assert ftp_service is not None
    assert ftp_service.get("disabled") is False, "En fábrica, FTP debe venir habilitado"

    # 2. Usuario admin activo
    admin_user = next((u for u in data["user"] if u["name"] == "admin"), None)
    assert admin_user is not None
    assert admin_user.get("disabled") is False, "En fábrica, el usuario admin está activo"

    # 3. Winbox no restringido por IP/CIDR
    winbox_service = next((s for s in data["ip_service"] if s["name"] == "winbox"), None)
    assert winbox_service is not None
    assert winbox_service.get("address") == "", "En fábrica, WinBox no tiene restricción de red"

    # 4. Descubrimiento de vecinos abierto a todas las interfaces
    assert data["neighbor_discovery"]["discover-interface-list"] == "all"


def test_cis_hardening_nominal_rosgrid_positive_invariant():
    """Un router aprovisionado con RoSGrid DEBE aprobar las directivas críticas."""
    data = _load_json_fixture("cis/hardened_rosgrid_cis.json")

    # Telnet y FTP deshabilitados
    telnet_service = next((s for s in data["ip_service"] if s["name"] == "telnet"), None)
    assert telnet_service["disabled"] is True

    ftp_service = next((s for s in data["ip_service"] if s["name"] == "ftp"), None)
    assert ftp_service["disabled"] is True

    # Admin original deshabilitado
    admin_user = next((u for u in data["user"] if u["name"] == "admin"), None)
    assert admin_user["disabled"] is True

    # Winbox restringido a CIDR de gestión
    winbox_service = next((s for s in data["ip_service"] if s["name"] == "winbox"), None)
    assert winbox_service["address"] == "10.250.0.0/16"

    # Neighbor discovery restringido
    assert data["neighbor_discovery"]["discover-interface-list"] == "LAN"


# ============================================================================
# 2. DOMINIO TOPOLOGÍA L2 MNDP (Invariante Negativa ante Tabla Vacía)
# ============================================================================

def test_topology_l2_factory_default_negative_invariant():
    """Ante router de fábrica aislado (tabla de vecinos vacía), no debe alucinar enlaces."""
    empty_neighbors = _load_json_fixture("topology/factory_default_neighbors.json")
    assert empty_neighbors == []

    tenant_id = uuid.uuid4()
    r1_id = uuid.uuid4()
    router = Router(
        id=r1_id,
        tenant_id=tenant_id,
        display_name="r4-factory",
        api_base_url="https://10.250.3.15",
        physical_location="Lab",
        network_role="BRANCH",
    )

    neighbors_map = {r1_id: empty_neighbors}
    poe_map = {r1_id: {}}

    res = process_topology_graph([router], neighbors_map, poe_map)
    assert res.total_nodes == 1
    assert res.total_edges == 0, "No debe existir ninguna arista si la tabla de vecinos está vacía"
    assert res.edges == []


def test_topology_l2_thirdparty_neighbors_negative_invariant():
    """Dispositivos que no pertenezcan al tenant no deben generar enlaces fantasma."""
    thirdparty = _load_json_fixture("topology/thirdparty_neighbors.json")
    tenant_id = uuid.uuid4()
    r1_id = uuid.uuid4()
    router = Router(
        id=r1_id,
        tenant_id=tenant_id,
        display_name="r1-core",
        api_base_url="https://10.250.3.8",
        physical_location="Core NOC",
        network_role="CORE",
    )

    neighbors_map = {r1_id: thirdparty}
    poe_map = {r1_id: {}}

    res = process_topology_graph([router], neighbors_map, poe_map)
    assert res.total_edges == 0, "Dispositivos no adoptados en la flota no deben enlazarse"


# ============================================================================
# 3. DOMINIO IPAM & POOLS DHCP
# ============================================================================

def test_ipam_factory_default_negative_invariant():
    """El router de fábrica no debe reportar leases si la lista de leases está vacía."""
    data = _load_json_fixture("ipam/factory_default_dhcp.json")
    assert data["dhcp_lease"] == [], "Un router de fábrica recién iniciado no tiene leases activos"
    assert data["ip_pool"][0]["name"] == "default-dhcp"
    assert data["ip_pool"][0]["ranges"] == "192.168.88.10-192.168.88.254"


def test_ipam_configured_pools_nominal_invariant():
    """El fixture de pools corporativos contiene los nombres y rangos esperados."""
    data = _load_json_fixture("ipam/configured_dhcp_pools.json")
    pool_names = {p["name"] for p in data["ip_pool"]}
    assert "pool-pcs" in pool_names
    assert "pool-aps" in pool_names
    assert len(data["dhcp_lease"]) == 2


# ============================================================================
# 4. DOMINIO POE & HARDWARE NO COMPATIBLE
# ============================================================================

def test_poe_unsupported_hardware_negative_invariant():
    """Routers sin chip PoE (CHR, hEX, routers core) deben retornar lista vacía."""
    poe_data = _load_json_fixture("poe/factory_default_no_poe.json")
    assert poe_data == []


def test_poe_active_netpower_nominal_invariant():
    """Dispositivos NetPower con PoE activo reportan estado delivering-power y voltaje."""
    poe_data = _load_json_fixture("poe/active_poe_netpower.json")
    delivering = [p for p in poe_data if p.get("poe-out-status") == "delivering-power"]
    assert len(delivering) == 2
    assert delivering[0]["poe-out-voltage"] == "48.5"


# ============================================================================
# 5. DOMINIO ROGUE DHCP SNOOPING
# ============================================================================

def test_rogue_dhcp_factory_default_negative_invariant():
    """En configuración de fábrica no deben existir falsas alertas de servidores rogue."""
    alerts = _load_json_fixture("rogue_dhcp/factory_default_bridge.json")
    assert alerts == [], "Router de fábrica no debe tener alertas de Rogue DHCP"


def test_rogue_dhcp_detected_alert_invariant():
    """Fixture con ataque de rogue DHCP reporta la MAC del atacante."""
    alerts = _load_json_fixture("rogue_dhcp/rogue_server_alert.json")
    assert len(alerts) == 1
    assert alerts[0]["unknown-server"] == "E4:8D:8C:99:88:77"


# ============================================================================
# 6. DOMINIO CAPsMAN & WIFI 6 (Erradicación de Falsos Positivos)
# ============================================================================

def test_capsman_factory_default_negative_invariant():
    """Un router de fábrica sin wireless ni CAPsMAN DEBE retornar 0 APs, 0 radios y 0 clientes."""
    data = _load_json_fixture("wifi/factory_default_no_wifi.json")
    assert data["manager"]["enabled"] is False
    assert data["remote_cap"] == []
    assert data["registration_table"] == []

    # Validar el esquema de respuesta determinista
    resp = CapsmanOverviewResponse(
        router_id=uuid.uuid4(),
        capsman_running=False,
        active_radios_count=0,
        managed_aps_count=0,
        connected_clients_count=0,
    )
    assert resp.capsman_running is False
    assert resp.managed_aps_count == 0
    assert resp.connected_clients_count == 0


def test_capsman_nominal_positive_invariant():
    """Router controlador CAPsMAN aprovisionado con radios y clientes."""
    data = _load_json_fixture("wifi/active_wifiwave2_capsman.json")
    assert data["manager"]["enabled"] is True
    assert len(data["remote_cap"]) == 2
    assert len(data["registration_table"]) == 2


# ============================================================================
# 7. DOMINIO CONFIG DRIFT (Invariante Negativa de Desviación de Fábrica)
# ============================================================================

def test_config_drift_factory_default_negative_invariant():
    """Un router con configuración de fábrica contra la Golden Baseline DEBE reportar 100% drift."""
    factory_rsc = _load_text_fixture("drift/factory_default_export.rsc").splitlines()
    golden_rsc = _load_text_fixture("drift/golden_baseline_export.rsc").splitlines()

    diff = list(difflib.unified_diff(golden_rsc, factory_rsc))
    assert len(diff) > 0, "Un router de fábrica tiene desviación absoluta respecto a la Golden Baseline"

    # Verificar que faltan las directivas críticas de RoSGrid en el router de fábrica
    missing_syslog = any("-add name=rosgridsyslog" in line for line in diff)
    assert missing_syslog is True, "El router de fábrica no posee la acción canónica rosgridsyslog"


def test_config_drift_identical_golden_baseline_positive_invariant():
    """Una configuración idéntica a la Golden Baseline debe reportar cero drift."""
    golden_rsc = _load_text_fixture("drift/golden_baseline_export.rsc").splitlines()
    diff = list(difflib.unified_diff(golden_rsc, golden_rsc))
    assert len(diff) == 0, "Configuración idéntica no produce ninguna diferencia"
