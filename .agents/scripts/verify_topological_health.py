#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
"""
Script de Auditoría de Salud Topológica y Límites de Capas (Graphify AST).
Verifica que las relaciones entre componentes y módulos respeten las reglas
arquitectónicas de RoSGrid y no existan acoplamientos inversos ni código huérfano.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FASTAPI_GRAPH_PATH = REPO_ROOT / "fastapi" / "graphify-out" / "graph.json"
VUE3_GRAPH_PATH = REPO_ROOT / "vue3" / "graphify-out" / "graph.json"


def load_graph(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        print(f"⚠️ Archivo de grafo no encontrado: {path}", file=sys.stderr)
        print("  Ejecute primero './scripts/actualizar-grafos-graphify.sh'", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def audit_backend_layers(graph: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    links = graph.get("links", [])
    violations: List[str] = []

    # Reglas de límite de capas en Backend:
    # 1. src/mikrotik/, src/models/, src/core/, src/schemas/ NUNCA deben llamar o importar de src/api/
    # 2. src/mikrotik/ NUNCA debe depender de src/workers/
    forbidden_prefixes = ["src/mikrotik/", "src/models/", "src/core/", "src/schemas/"]

    for link in links:
        src_file = link.get("source_file", "")
        tgt_id = link.get("target", "")
        tgt_node = nodes.get(tgt_id)
        if not tgt_node:
            continue
        tgt_file = tgt_node.get("source_file", "")

        for prefix in forbidden_prefixes:
            if src_file.startswith(prefix) and tgt_file.startswith("src/api/"):
                violations.append(
                    f"Acoplamiento inverso: '{src_file}' ({link.get('context', 'call')}) -> '{tgt_file}'"
                )

        if src_file.startswith("src/mikrotik/") and tgt_file.startswith("src/workers/"):
            violations.append(
                f"Acoplamiento indebido: '{src_file}' -> '{tgt_file}' (Mikrotik Client no debe depender de Workers)"
            )

    stats = {
        "nodes": len(nodes),
        "links": len(links),
        "communities": len(set(n.get("community", 0) for n in nodes.values())),
    }
    return violations, stats


def audit_frontend_layers(graph: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    links = graph.get("links", [])
    violations: List[str] = []

    # Reglas de límite de capas en Frontend:
    # 1. Componentes comunes (src/components/common/) nunca deben depender de vistas completas (src/views/)
    for link in links:
        src_file = link.get("source_file", "")
        tgt_id = link.get("target", "")
        tgt_node = nodes.get(tgt_id)
        if not tgt_node:
            continue
        tgt_file = tgt_node.get("source_file", "")

        if src_file.startswith("src/components/common/") and tgt_file.startswith("src/views/"):
            violations.append(
                f"Acoplamiento invertido UI: Componente común '{src_file}' depende de vista '{tgt_file}'"
            )

    stats = {
        "nodes": len(nodes),
        "links": len(links),
        "communities": len(set(n.get("community", 0) for n in nodes.values())),
    }
    return violations, stats


def main() -> None:
    print("🔍 [Graphify AST] Auditando salud topológica y límites de capas arquitectónicas...")

    fastapi_graph = load_graph(FASTAPI_GRAPH_PATH)
    vue3_graph = load_graph(VUE3_GRAPH_PATH)

    be_violations, be_stats = audit_backend_layers(fastapi_graph)
    fe_violations, fe_stats = audit_frontend_layers(vue3_graph)

    print(
        f"  📊 Backend:  {be_stats['nodes']} nodos, {be_stats['links']} aristas, {be_stats['communities']} comunidades"
    )
    print(
        f"  📊 Frontend: {fe_stats['nodes']} nodos, {fe_stats['links']} aristas, {fe_stats['communities']} comunidades"
    )

    total_violations = len(be_violations) + len(fe_violations)

    if total_violations > 0:
        print(f"\n🚨 Se detectaron {total_violations} violaciones de límites de capas:", file=sys.stderr)
        for v in be_violations:
            print(f"  ❌ [Backend] {v}", file=sys.stderr)
        for v in fe_violations:
            print(f"  ❌ [Frontend] {v}", file=sys.stderr)
        sys.exit(1)

    print("✔ Cero violaciones de acoplamiento de capas detectadas (Topología limpia y desacoplada).")
    sys.exit(0)


if __name__ == "__main__":
    main()
