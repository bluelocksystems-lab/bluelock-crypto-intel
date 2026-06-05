"""
graph_builder.py
────────────────
Builds graph node and edge data from a transaction list.
Used to power the Cytoscape.js / D3 counterparty relationship map.

The target wallet is the center node. Every unique counterparty
becomes a connected node. Node type determines visual styling.
"""

from collections import defaultdict
from app.models import Transaction, GraphNode, GraphEdge
from app.services.label_engine import get_label


def build_graph(address: str, transactions: list[Transaction]):
    """
    Build a node/edge graph from a list of transactions.

    Returns:
        nodes: list[GraphNode]
        edges: list[GraphEdge]
    """
    address_lower = address.lower()

    # Track counterparties and their interaction counts
    counterparty_data: dict[str, dict] = defaultdict(lambda: {
        "in": 0, "out": 0, "total": 0, "label": None, "category": None
    })

    for tx in transactions:
        cp = tx.counterparty.lower() if tx.counterparty else None
        if not cp or cp == address_lower:
            continue

        lbl, cat = get_label(cp)
        counterparty_data[cp]["label"] = lbl or tx.counterparty_label
        counterparty_data[cp]["category"] = cat
        counterparty_data[cp][tx.direction] += 1
        counterparty_data[cp]["total"] += 1

    # ── Build nodes ───────────────────────────────────────────
    nodes: list[GraphNode] = []

    # Center node: the wallet being investigated
    nodes.append(GraphNode(
        id=address_lower,
        label=f"{address_lower[:6]}...{address_lower[-4:]}",
        node_type="target",
        tx_count=len(transactions),
    ))

    # Counterparty nodes
    for cp_addr, data in counterparty_data.items():
        cat = data["category"]
        lbl = data["label"]

        if cat == "exchange":
            node_type = "exchange"
        elif cat == "dex":
            node_type = "dex"
        elif cat == "bridge":
            node_type = "bridge"
        elif cat in ("stablecoin", "defi"):
            node_type = "contract"
        else:
            node_type = "counterparty"

        short_addr = f"{cp_addr[:6]}...{cp_addr[-4:]}"
        display_label = lbl if lbl else short_addr

        nodes.append(GraphNode(
            id=cp_addr,
            label=display_label,
            node_type=node_type,
            tx_count=data["total"],
        ))

    # ── Build edges ───────────────────────────────────────────
    edges: list[GraphEdge] = []

    # Aggregate edges by counterparty (one edge per pair with tx_count)
    for cp_addr, data in counterparty_data.items():
        edges.append(GraphEdge(
            source=address_lower,
            target=cp_addr,
            tx_count=data["total"],
        ))

    return nodes, edges
