"""Build and export the curated causal graph."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import networkx as nx


def build_graph(asset_config: dict, relationship_config: dict) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph(name="macro_graph")
    for item in asset_config.get("assets", []):
        graph.add_node(
            item["id"],
            label=item["name"],
            node_type=item["asset_class"],
            public_status="public" if item["asset_class"] == "public_equity" else "n/a",
        )
    for item in asset_config.get("non_market_nodes", []):
        graph.add_node(
            item["id"],
            label=item["name"],
            node_type=item["node_type"],
            public_status=item.get("public_status", "n/a"),
        )
    for index, edge in enumerate(relationship_config.get("relationships", [])):
        source, target = edge["source"], edge["target"]
        if source not in graph or target not in graph:
            raise ValueError(f"Relationship references unknown node: {source} -> {target}")
        graph.add_edge(
            source,
            target,
            key=f"{edge['relationship']}:{index}",
            relationship=edge["relationship"],
            direction=edge["direction"],
            strength=float(edge["strength"]),
            confidence=float(edge["confidence"]),
            reason=edge["reason"],
            reason_zh=edge.get("reason_zh", edge["reason"]),
            source_reference=edge["source_reference"],
        )
    return graph


def export_graph(graph: nx.MultiDiGraph, output_dir: Path, as_of: datetime) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    graph_json = output_dir / "graph.json"
    graphml = output_dir / "graph.graphml"
    payload = nx.node_link_data(graph)
    payload["as_of"] = as_of.isoformat()
    _atomic_text(graph_json, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    temporary_graphml = graphml.with_suffix(".graphml.tmp")
    nx.write_graphml(graph, temporary_graphml)
    temporary_graphml.replace(graphml)
    return {"json": str(graph_json), "graphml": str(graphml)}


def _atomic_text(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content + "\n", encoding="utf-8")
    temporary.replace(path)
