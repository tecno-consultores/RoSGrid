#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
"""
Script de Inspección Rápida de Radio de Impacto (Blast Radius) mediante Graphify AST.
Permite evaluar matemáticamente antes de refactorizar cuántos y cuáles archivos
o funciones dependen directa o indirectamente de un símbolo o archivo en Backend o Frontend.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FASTAPI_GRAPH_PATH = REPO_ROOT / "fastapi" / "graphify-out" / "graph.json"
VUE3_GRAPH_PATH = REPO_ROOT / "vue3" / "graphify-out" / "graph.json"


def load_graph(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        print(f"⚠️ Archivo de grafo no encontrado: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_matching_nodes(graph: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    query_lower = query.lower()
    matches = []
    for node in graph.get("nodes", []):
        label = node.get("label", "").lower()
        node_id = node.get("id", "").lower()
        source_file = node.get("source_file", "").lower()
        if query_lower == label or query_lower == node_id or query_lower in source_file:
            matches.append(node)
        elif query_lower in label:
            matches.append(node)
    return matches


def compute_blast_radius(graph: Dict[str, Any], target_node_id: str) -> Dict[str, Any]:
    nodes_by_id = {n["id"]: n for n in graph.get("nodes", [])}
    links = graph.get("links", [])

    # Aristas entrantes directas (quién llama al target)
    direct_callers = []
    direct_caller_files: Set[str] = set()
    impacted_communities: Set[str] = set()

    for link in links:
        if link.get("target") == target_node_id:
            src_id = link.get("source")
            src_node = nodes_by_id.get(src_id, {})
            src_file = link.get("source_file") or src_node.get("source_file", "unknown")
            direct_caller_files.add(src_file)
            comm_name = src_node.get("community_name")
            if comm_name:
                impacted_communities.add(comm_name)

            direct_callers.append(
                {
                    "source_id": src_id,
                    "label": src_node.get("label", src_id),
                    "file": src_file,
                    "location": link.get("source_location") or src_node.get("source_location", ""),
                    "relation": link.get("relation", "calls"),
                    "context": link.get("context", ""),
                }
            )

    return {
        "direct_callers_count": len(direct_callers),
        "unique_files_count": len(direct_caller_files),
        "impacted_communities": list(impacted_communities),
        "direct_callers": direct_callers,
    }


def assess_risk_level(query: str, callers_count: int, files_count: int) -> str:
    critical_keywords = ["vault", "auth", "token", "rls", "safemode", "csrf", "secret", "session"]
    is_security_critical = any(kw in query.lower() for kw in critical_keywords)

    if is_security_critical or callers_count >= 15 or files_count >= 8:
        return "🔴 ALTO / CRÍTICO (Requiere suite completa de regresión y revisión minuciosa)"
    elif callers_count >= 5 or files_count >= 3:
        return "🟡 MODERADO (Requiere verificación de contratos y pruebas unitarias de llamadores)"
    else:
        return "🟢 BAJO (Impacto acotado o localizado)"


def inspect_symbol(query: str) -> None:
    print(f"🎯 [Graphify Blast Radius] Analizando radio de impacto para: '{query}'\n")

    be_graph = load_graph(FASTAPI_GRAPH_PATH)
    fe_graph = load_graph(VUE3_GRAPH_PATH)

    be_matches = find_matching_nodes(be_graph, query)
    fe_matches = find_matching_nodes(fe_graph, query)

    total_matches = len(be_matches) + len(fe_matches)
    if total_matches == 0:
        print(f"ℹ️ No se encontraron nodos coincidentes con '{query}' en los grafos.")
        print("  Sugerencia: especifique el nombre exacto de la función, clase o archivo.")
        return

    print(f"Se encontraron {total_matches} coincidencias:")

    # Mostrar Backend
    for node in be_matches[:5]:
        node_id = node["id"]
        label = node.get("label", node_id)
        file_path = node.get("source_file", "unknown")
        loc = node.get("source_location", "")
        comm = node.get("community_name", "general")

        blast = compute_blast_radius(be_graph, node_id)
        risk = assess_risk_level(label, blast["direct_callers_count"], blast["unique_files_count"])

        print(f"\n📦 [Backend] {label} ({file_path}:{loc})")
        print(f"   Comunidad AST: {comm}")
        print(f"   Nivel de Riesgo: {risk}")
        print(
            f"   Consumidores directos: {blast['direct_callers_count']} llamadas en {blast['unique_files_count']} archivos distintos"
        )

        if blast["impacted_communities"]:
            print(f"   Comunidades impactadas: {', '.join(blast['impacted_communities'][:6])}")

        if blast["direct_callers"]:
            print("   Llamadores inmediatos:")
            for caller in blast["direct_callers"][:8]:
                print(f"     - {caller['file']}:{caller['location']} -> {caller['label']} ({caller['relation']})")
            if len(blast["direct_callers"]) > 8:
                print(f"     ... y {len(blast['direct_callers']) - 8} llamadores adicionales.")

    # Mostrar Frontend
    for node in fe_matches[:5]:
        node_id = node["id"]
        label = node.get("label", node_id)
        file_path = node.get("source_file", "unknown")
        loc = node.get("source_location", "")
        comm = node.get("community_name", "general")

        blast = compute_blast_radius(fe_graph, node_id)
        risk = assess_risk_level(label, blast["direct_callers_count"], blast["unique_files_count"])

        print(f"\n🎨 [Frontend] {label} ({file_path}:{loc})")
        print(f"   Comunidad AST: {comm}")
        print(f"   Nivel de Riesgo: {risk}")
        print(
            f"   Consumidores directos: {blast['direct_callers_count']} llamadas en {blast['unique_files_count']} archivos distintos"
        )

        if blast["impacted_communities"]:
            print(f"   Comunidades impactadas: {', '.join(blast['impacted_communities'][:6])}")

        if blast["direct_callers"]:
            print("   Llamadores inmediatos:")
            for caller in blast["direct_callers"][:8]:
                print(f"     - {caller['file']}:{caller['location']} -> {caller['label']} ({caller['relation']})")
            if len(blast["direct_callers"]) > 8:
                print(f"     ... y {len(blast['direct_callers']) - 8} llamadores adicionales.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Auditoría de Radio de Impacto mediante Graphify AST")
    parser.add_argument("query", help="Nombre del símbolo, función, clase o archivo a auditar")
    args = parser.parse_args()

    inspect_symbol(args.query)


if __name__ == "__main__":
    main()
