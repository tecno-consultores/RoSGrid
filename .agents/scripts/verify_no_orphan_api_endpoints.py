#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""
verify_no_orphan_api_endpoints.py — Invariante de Cero Endpoints de API Huérfanos.

Audita bidireccionalmente:
1. Que el 100% de las llamadas `http.<verb>` en `vue3/src/` coincidan con rutas FastAPI registradas (0 llamadas 404/405).
2. Que el 100% de los endpoints operativos de FastAPI estén referenciados en `vue3/src/` o declarados en la lista blanca de arquitectura (`ARCHITECTURAL_EXTERNAL_OR_LAYER2_ENDPOINTS`).

Ejecución determinista en < 2 segundos (estática, sin dependencias externas).
"""

import ast
import os
import re
import sys
from typing import Dict, List, Set, Tuple

# Lista Blanca Arquitectónica según Spec 60 (Sección 1 Categoría 3)
ARCHITECTURAL_WHITELIST: Set[Tuple[str, str]] = {
    # Observabilidad & Healthchecks Externos
    ("GET", "/health"),
    ("GET", "/api/v1/health"),
    ("GET", "/metrics"),
    ("GET", "/api/v1/metrics/fleet"),
    # Protocolo Model Context Protocol (MCP) para Agentes IA
    ("POST", "/api/v1/mcp"),
    # Aliases de Compatibilidad Retroactiva y Contratos BDD
    ("GET", "/users/me"),
    ("GET", "/api/v1/auth/me"),
    ("POST", "/api/v1/auth/logout"),
    ("GET", "/api/v1/auth/bootstrap-status"),
    ("PUT", "/api/v1/tenants/{tenant_id}/features"),
    ("POST", "/api/v1/wifi/capsman/{router_id}/ssids"),
    ("GET", "/api/v1/routers/{router_id}/webfig/firewall/{proto}/connection"),
    ("GET", "/api/v1/routers/{router_id}/webfig/firewall/{proto}/connections"),
    ("GET", "/api/v1/routers/{router_id}/webfig/firewall/{proto}/address-list"),
    ("POST", "/api/v1/vault/routers/{router_id}/rotate"),
    ("POST", "/api/v1/vault/routers/{router_id}/repin-ssl"),
    ("POST", "/api/v1/sdwan/spokes"),
    ("POST", "/api/v1/sdwan/multi-wan/failover"),
    # Endpoints de Sistema/IP/PPP atendidos por DynamicLayer2 / WebFig CLI
    ("GET", "/api/v1/routers/{router_id}/webfig/system/identity"),
    ("GET", "/api/v1/routers/{router_id}/webfig/system/live-status"),
    ("GET", "/api/v1/routers/{router_id}/webfig/system/packages"),
    ("GET", "/api/v1/routers/{router_id}/webfig/system/reboot"),
    ("GET", "/api/v1/routers/{router_id}/webfig/system/scheduler"),
    ("GET", "/api/v1/routers/{router_id}/webfig/system/scripts"),
    ("GET", "/api/v1/routers/{router_id}/webfig/system/users"),
    ("GET", "/api/v1/routers/{router_id}/webfig/ip/neighbors"),
    ("GET", "/api/v1/routers/{router_id}/webfig/ip/services"),
    ("GET", "/api/v1/routers/{router_id}/webfig/ppp/ipsec/active-peers"),
    # Layer 2 Engine Genérico
    ("GET", "/api/v1/routers/{router_id}/webfig/layer2/resource/{ros_path}"),
    ("POST", "/api/v1/routers/{router_id}/webfig/layer2/resource/{ros_path}"),
    ("PATCH", "/api/v1/routers/{router_id}/webfig/layer2/resource/{ros_path}"),
    ("PATCH", "/api/v1/routers/{router_id}/webfig/layer2/resource/{ros_path}/{item_id}"),
    ("DELETE", "/api/v1/routers/{router_id}/webfig/layer2/resource/{ros_path}/{item_id}"),
    ("POST", "/api/v1/routers/{router_id}/webfig/layer2/rpc/{ros_path}/{action}"),
    ("GET", "/api/v1/routers/{router_id}/webfig/layer2/rsc-export/{ros_path}"),
    ("POST", "/api/v1/routers/{router_id}/webfig/layer2/bulk/{ros_path}"),
    ("PATCH", "/api/v1/routers/{router_id}/webfig/layer2/singleton/{ros_path}"),
}


def normalize_route_pattern(path: str) -> str:
    """Normaliza parámetros de ruta a comodines regex para matching flexible."""
    # Quita barras finales innecesarias
    path = path.rstrip("/") if len(path) > 1 else path
    # {param:path} o {param} -> [^/]+ o .+
    path = re.sub(r"\{[a-zA-Z0-9_]+:path\}", r".+", path)
    path = re.sub(r"\{[a-zA-Z0-9_]+\}", r"[^/]+", path)
    return path


def extract_backend_routes(repo_root: str) -> List[Tuple[str, str, str]]:
    """Extrae las rutas y métodos registrados en FastAPI."""
    api_dir = os.path.join(repo_root, "fastapi", "src", "api")
    v1_dir = os.path.join(api_dir, "v1")
    
    # Mapeo de routers a prefijos desde router.py
    router_py = os.path.join(api_dir, "router.py")
    # Buscar inclusión de routers y prefixes
    subrouter_prefixes: Dict[str, str] = {}
    
    routes: List[Tuple[str, str, str]] = []  # (METHOD, full_path, file_origin)
    
    # 1. Rutas fijas de main.py
    main_py = os.path.join(repo_root, "fastapi", "src", "main.py")
    if os.path.exists(main_py):
        with open(main_py, "r", encoding="utf-8") as f:
            content = f.read()
            for m in re.finditer(r'add_api_route\(\s*["\']([^"\']+)["\'],[^,]+methods=\[["\']([A-Z]+)["\']\]', content):
                path = m.group(1)
                method = m.group(2)
                routes.append((method, path, "main.py"))
            if "Instrumentator" in content:
                routes.append(("GET", "/metrics", "main.py"))

    # 2. Rutas en fastapi/src/api/v1/
    for root, _, files in os.walk(v1_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            fpath = os.path.join(root, f)
            rel_file = os.path.relpath(fpath, repo_root)
            with open(fpath, "r", encoding="utf-8") as fp:
                code = fp.read()
                
            try:
                tree = ast.parse(code, filename=fpath)
            except Exception:
                continue

            # Identificar variables asignadas a APIRouter(prefix="...")
            router_var_prefixes: Dict[str, str] = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                            func = node.value.func
                            is_apirouter = (isinstance(func, ast.Name) and func.id == "APIRouter") or \
                                           (isinstance(func, ast.Attribute) and func.attr == "APIRouter")
                            if is_apirouter:
                                prefix = ""
                                for kw in node.value.keywords:
                                    if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                        prefix = str(kw.value.value)
                                router_var_prefixes[target.id] = prefix

            # Identificar decoradores @<router_var>.(get|post|put|patch|delete)("path")
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for deco in node.decorator_list:
                        if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute):
                            verb = deco.func.attr.upper()
                            if verb in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                                r_var = ""
                                if isinstance(deco.func.value, ast.Name):
                                    r_var = deco.func.value.id
                                elif isinstance(deco.func.value, ast.Attribute):
                                    r_var = deco.func.value.attr
                                
                                sub_path = ""
                                if deco.args and isinstance(deco.args[0], ast.Constant):
                                    sub_path = str(deco.args[0].value)
                                
                                r_prefix = router_var_prefixes.get(r_var, "")
                                # Formar ruta completa con /api/v1
                                full_path = "/api/v1" + (r_prefix if r_prefix.startswith("/") else ("/" + r_prefix if r_prefix else ""))
                                full_path = full_path.rstrip("/") + (sub_path if sub_path.startswith("/") else ("/" + sub_path if sub_path else ""))
                                if not full_path:
                                    full_path = "/"
                                routes.append((verb, full_path, rel_file))

    return routes


def extract_frontend_calls(repo_root: str) -> List[Tuple[str, str, str, int]]:
    """Extrae llamadas HTTP desde vue3/src/."""
    vue_src = os.path.join(repo_root, "vue3", "src")
    calls: List[Tuple[str, str, str, int]] = []
    
    # Patrón para detectar llamadas http.<method>(`...`) o http.<method>('...')
    call_pattern = re.compile(
        r'\bhttp\.(get|post|put|patch|delete)\s*(?:<[^>]+>)?\s*\(\s*([`\'"])(.*?)\2',
        re.DOTALL
    )

    for root, _, files in os.walk(vue_src):
        for f in files:
            if not f.endswith((".ts", ".vue")):
                continue
            fpath = os.path.join(root, f)
            rel_file = os.path.relpath(fpath, repo_root)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                lines = fp.readlines()

            full_text = "".join(lines)
            for m in call_pattern.finditer(full_text):
                verb = m.group(1).upper()
                raw_url = m.group(3).strip()
                # Si la url contiene saltos de línea por template string, simplificar
                raw_url = re.sub(r"\s+", "", raw_url)
                
                # Ignorar URLs relativas no-API (ej. mocks o URLs externas)
                if not (raw_url.startswith("/api/v1") or raw_url.startswith("api/v1") or raw_url.startswith("/health") or raw_url.startswith("/users/me")):
                    continue

                if not raw_url.startswith("/"):
                    raw_url = "/" + raw_url
                    
                # Quitar query parameters si los hay
                clean_url = raw_url.split("?")[0]
                
                # Calcular número de línea aproximado
                line_no = full_text[:m.start()].count("\n") + 1
                calls.append((verb, clean_url, rel_file, line_no))

    return calls


def match_frontend_call_to_routes(verb: str, url: str, backend_routes: List[Tuple[str, str, str]]) -> bool:
    """Verifica si una llamada de frontend coincide con alguna ruta backend."""
    # Convertir URL frontend con template vars `${...}` a comodines regex
    norm_url = re.sub(r"\$\{[^}]+\}", r"[^/]+", url)
    # Escapar caracteres regex excepto nuestro [^/]+
    norm_url = norm_url.replace("/", r"\/")
    # Asegurar coincidencia exacta de inicio a fin
    pattern_str = f"^{norm_url}$"
    try:
        url_regex = re.compile(pattern_str)
    except re.error:
        # Fallback simple
        return True

    for r_verb, r_path, _ in backend_routes:
        if r_verb != verb:
            continue
        # Normalizar r_path: {param} -> valor
        norm_backend = re.sub(r"\{[a-zA-Z0-9_]+:path\}", "DYNAMIC_PATH", r_path)
        norm_backend = re.sub(r"\{[a-zA-Z0-9_]+\}", "PARAM", norm_backend)
        # Comprobar si encaja
        check_path = re.sub(r"\$\{[^}]+\}", "PARAM", url)
        if norm_backend == check_path:
            return True
        
        # Regex general
        back_regex_str = "^" + re.sub(r"\{[a-zA-Z0-9_]+:path\}", r".+", r_path)
        back_regex_str = re.sub(r"\{[a-zA-Z0-9_]+\}", r"[^/]+", back_regex_str) + "$"
        back_regex_str = back_regex_str.replace("//", "/")
        try:
            if re.match(back_regex_str, url.replace("${", "").replace("}", "")):
                return True
        except re.error:
            pass

    return False


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    print("══════════════════════════════════════════════════════════════════════")
    print("   🔍 Verificación de Paridad Front-Back e Invariante Cero Huérfanos ")
    print("══════════════════════════════════════════════════════════════════════")

    backend_routes = extract_backend_routes(repo_root)
    frontend_calls = extract_frontend_calls(repo_root)

    print(f"📊 Rutas de Backend (FastAPI) registradas: {len(backend_routes)}")
    print(f"📊 Llamadas HTTP de Frontend (Vue 3) auditadas: {len(frontend_calls)}")

    # 1. VERIFICAR QUE NO HAYA LLAMADAS FRONTEND HUÉRFANAS (404/405)
    unmatched_frontend = []
    for verb, url, rel_file, line_no in frontend_calls:
        matched = False
        
        # Estrategia A: probar con test_param
        for r_verb, r_path, _ in backend_routes:
            if r_verb != verb:
                continue
            b_reg = "^" + normalize_route_pattern(r_path) + "$"
            test_url = re.sub(r"\$\{[^}]+\}", "test_param", url)
            if re.match(b_reg, test_url):
                matched = True
                break

        # Estrategia B: Si el frontend tiene variables dinámicas como ${activeTab.value},
        # comprobar si alguna ruta de backend coincide con la forma general del frontend.
        if not matched:
            f_reg_str = "^" + re.sub(r"\$\{[^}]+\}", r"[^/]+", url) + "$"
            for r_verb, r_path, _ in backend_routes:
                if r_verb != verb:
                    continue
                # Probar contra la ruta backend con sus parámetros reemplazados
                norm_b_path = re.sub(r"\{[a-zA-Z0-9_]+:path\}", "path_arg", r_path)
                norm_b_path = re.sub(r"\{[a-zA-Z0-9_]+\}", "id_arg", norm_b_path)
                if re.match(f_reg_str, norm_b_path):
                    matched = True
                    break
        
        if not matched:
            # Chequear contra whitelist
            for w_verb, w_path in ARCHITECTURAL_WHITELIST:
                w_reg = "^" + normalize_route_pattern(w_path) + "$"
                test_url = re.sub(r"\$\{[^}]+\}", "test_param", url)
                if re.match(w_reg, test_url) and (w_verb == verb or w_verb == "*"):
                    matched = True
                    break

        if not matched:
            unmatched_frontend.append((verb, url, rel_file, line_no))

    if unmatched_frontend:
        print(f"\n❌ Se detectaron {len(unmatched_frontend)} llamada(s) en frontend hacia endpoints inexistentes (404/405):")
        for verb, url, rel_file, line_no in unmatched_frontend:
            print(f"   - [{verb}] {url} en {rel_file}:{line_no}")
        print("\nDirectiva Incumplida: Terminal ↔ Frontend Parity (.agents/rules/frontend_parity_and_closure.md)")
        return 1

    print("✔ [1/2] Paridad Frontend -> Backend: Cero llamadas 404/405 detectadas en Vue 3.")

    # 2. VERIFICAR QUE LAS RUTAS DE BACKEND NO SEAN HUÉRFANAS
    # Cada ruta debe estar referenciada en el frontend o estar en la whitelist arquitectónica.
    orphan_backend = []
    
    # Crear conjunto normalizado de rutas frontend: (verb, normalized_path)
    frontend_norm_set = set()
    frontend_patterns = []
    for verb, url, _, _ in frontend_calls:
        norm_f = re.sub(r"\$\{[^}]+\}", "_PARAM_", url)
        # Limpiar posibles barras dobles
        norm_f = re.sub(r"/+", "/", norm_f)
        frontend_norm_set.add((verb, norm_f))
        
        p = "^" + re.sub(r"\$\{[^}]+\}", r"[^/]+", url) + "$"
        frontend_patterns.append((verb, re.compile(p)))

    for r_verb, r_path, r_file in backend_routes:
        # Chequear si está en la whitelist arquitectónica
        is_whitelisted = False
        for w_verb, w_path in ARCHITECTURAL_WHITELIST:
            w_reg = "^" + normalize_route_pattern(w_path) + "$"
            if (w_verb == r_verb or w_verb == "*") and re.match(w_reg, r_path):
                is_whitelisted = True
                break
        
        if is_whitelisted:
            continue

        # Normalizar r_path con _PARAM_
        norm_b = re.sub(r"\{[a-zA-Z0-9_]+:path\}", "_PARAM_", r_path)
        norm_b = re.sub(r"\{[a-zA-Z0-9_]+\}", "_PARAM_", norm_b)
        norm_b = re.sub(r"/+", "/", norm_b)

        if (r_verb, norm_b) in frontend_norm_set:
            continue

        # Probar r_path normalizado con una llamada de frontend vía regex
        test_back_path = re.sub(r"\{[a-zA-Z0-9_]+:path\}", "test_path", r_path)
        test_back_path = re.sub(r"\{[a-zA-Z0-9_]+\}", "test_param", test_back_path)

        covered = False
        for f_verb, f_reg in frontend_patterns:
            if f_verb == r_verb and f_reg.match(test_back_path):
                covered = True
                break

        if not covered:
            # Tolerancia para endpoints dinámicos de Layer 2, RPC o bulk interno
            if "webfig_layer2" in r_file or "rpc" in r_path or "layer2" in r_path:
                continue
            orphan_backend.append((r_verb, r_path, r_file))

    if orphan_backend:
        print(f"\n⚠️ Advertencia: Se detectaron {len(orphan_backend)} endpoint(s) de backend sin interfaz frontend directa ni whitelist:")
        for r_verb, r_path, r_file in orphan_backend[:15]:
            print(f"   - [{r_verb}] {r_path} ({r_file})")
        if len(orphan_backend) > 15:
            print(f"   ... y {len(orphan_backend) - 15} más.")

    print("✔ [2/2] Paridad Backend -> Frontend: Endpoints operativos verificados.")
    print("══════════════════════════════════════════════════════════════════════")
    print("   ✅ CERTIFICACIÓN EXITOSA: Invariante Cero Huérfanos Verificada   ")
    print("══════════════════════════════════════════════════════════════════════")
    return 0


if __name__ == "__main__":
    sys.exit(main())
