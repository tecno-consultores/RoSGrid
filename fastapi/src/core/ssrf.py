# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

"""Validador Anti-SSRF unificado (síncrono y asíncrono) para webhooks, colectores SIEM y canales SMTP."""

import asyncio
import ipaddress
import socket
import urllib.parse

from src.core.config import settings

BLOCKED_OUTBOUND_HOSTS: frozenset[str] = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "127.0.0.1",
        "::1",
        "0.0.0.0",  # nosec B104
        "169.254.169.254",
        "metadata.google.internal",
        "localtest.me",
        "rosgrid-db",
        "rosgrid_db",
        "rosgrid-redis",
        "rosgrid_redis",
        "rosgrid-api",
        "rosgrid_api",
        "rosgrid-worker",
        "rosgrid_worker",
        "rosgrid-frontend",
        "rosgrid_frontend",
        "db",
        "redis",
        "keydb",
        "postgres",
    }
)

BLOCKED_DOMAIN_SUFFIXES: tuple[str, ...] = (
    ".localhost",
    ".internal",
    ".localtest.me",
    ".nip.io",
    ".sslip.io",
    ".xip.io",
)

ALLOWED_SMTP_PORTS: frozenset[int] = frozenset({25, 465, 587, 2525})


def _is_ip_allowed_by_cidrs(
    ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address,
    allow_cidrs: list[str] | None = None,
) -> bool:
    cidrs = allow_cidrs if allow_cidrs is not None else settings.outbound_allowed_cidrs_list
    for cidr_str in cidrs:
        try:
            if ip_obj in ipaddress.ip_network(cidr_str.strip(), strict=False):
                return True
        except ValueError:
            continue
    return False


def _is_ip_safe(
    ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address,
    *,
    allow_private_cidrs: list[str] | None = None,
) -> bool:
    if ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_unspecified or ip_obj.is_multicast:
        return False
    if ip_obj.is_private or ip_obj.is_reserved:
        return _is_ip_allowed_by_cidrs(ip_obj, allow_private_cidrs)
    return True


def _validate_hostname_structure(hostname: str) -> bool:
    clean = hostname.strip().lower().rstrip(".")
    norm = clean.replace("_", "-")
    if (
        not clean
        or clean in BLOCKED_OUTBOUND_HOSTS
        or norm in BLOCKED_OUTBOUND_HOSTS
        or norm.startswith("rosgrid-")
        or clean.endswith(BLOCKED_DOMAIN_SUFFIXES)
    ):
        return False
    return True


def is_safe_outbound_url(
    url: str,
    *,
    allow_private_cidrs: list[str] | None = None,
    resolve_dns: bool = True,
) -> bool:
    """Valida de forma síncrona que una URL HTTP/HTTPS saliente sea segura frente a SSRF."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = (parsed.hostname or "").strip().lower().rstrip(".")
        if not _validate_hostname_structure(hostname):
            return False
        try:
            ip_obj = ipaddress.ip_address(hostname)
            return _is_ip_safe(ip_obj, allow_private_cidrs=allow_private_cidrs)
        except ValueError:
            if resolve_dns:
                try:
                    infos = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
                    for info in infos:
                        resolved_str = str(info[4][0]).split("%")[0]
                        resolved_ip = ipaddress.ip_address(resolved_str)
                        if not _is_ip_safe(resolved_ip, allow_private_cidrs=allow_private_cidrs):
                            return False
                except OSError:
                    pass
        return True
    except Exception:
        return False


async def is_safe_outbound_url_async(
    url: str,
    *,
    allow_private_cidrs: list[str] | None = None,
) -> bool:
    """Valida de forma asíncrona (sin bloquear el event loop) una URL saliente frente a SSRF."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = (parsed.hostname or "").strip().lower().rstrip(".")
        if not _validate_hostname_structure(hostname):
            return False
        try:
            ip_obj = ipaddress.ip_address(hostname)
            return _is_ip_safe(ip_obj, allow_private_cidrs=allow_private_cidrs)
        except ValueError:
            try:
                infos = await asyncio.to_thread(
                    socket.getaddrinfo,
                    hostname,
                    None,
                    0,
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP,
                )
                for info in infos:
                    resolved_str = str(info[4][0]).split("%")[0]
                    resolved_ip = ipaddress.ip_address(resolved_str)
                    if not _is_ip_safe(resolved_ip, allow_private_cidrs=allow_private_cidrs):
                        return False
            except OSError:
                pass
        return True
    except Exception:
        return False


def is_safe_smtp_target(
    host: str,
    port: int,
    *,
    allow_localhost_fallback: bool = False,
) -> bool:
    """Valida que un servidor y puerto SMTP no apunten a servicios internos no autorizados."""
    try:
        port_int = int(port)
    except (TypeError, ValueError):
        return False
    if port_int not in ALLOWED_SMTP_PORTS:
        return False
    clean_host = (host or "").strip().lower().rstrip(".")
    if allow_localhost_fallback and clean_host == "localhost":
        return True
    if not _validate_hostname_structure(clean_host):
        return False
    try:
        ip_obj = ipaddress.ip_address(clean_host)
        return _is_ip_safe(ip_obj, allow_private_cidrs=[])
    except ValueError:
        try:
            infos = socket.getaddrinfo(clean_host, None, proto=socket.IPPROTO_TCP)
            for info in infos:
                resolved_str = str(info[4][0]).split("%")[0]
                resolved_ip = ipaddress.ip_address(resolved_str)
                if not _is_ip_safe(resolved_ip, allow_private_cidrs=[]):
                    return False
        except OSError:
            pass
    return True
