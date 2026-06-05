"""
models.py
─────────
Pydantic models used for request/response validation.
"""

from pydantic import BaseModel
from typing import Optional, List


class AnalyzeRequest(BaseModel):
    address: str
    chain: str = "ethereum"


class SaveCaseRequest(BaseModel):
    address: str
    chain: str
    notes: str = ""
    tags: List[str] = []
    label: str = ""


class Transaction(BaseModel):
    hash: str
    block: str
    timestamp: str
    from_addr: str
    to_addr: str
    value_eth: str
    token_symbol: Optional[str] = None
    token_name: Optional[str] = None
    direction: str          # "in" | "out" | "internal"
    tx_type: str            # "native" | "token" | "dex" | "contract"
    counterparty: str
    counterparty_label: Optional[str] = None
    usd_value: Optional[str] = None


class WalletSummary(BaseModel):
    address: str
    chain: str
    tx_count: int
    token_tx_count: int
    first_seen: Optional[str]
    last_seen: Optional[str]
    native_balance: Optional[str]
    symbol: str


class RiskNote(BaseModel):
    level: str          # "info" | "warning" | "alert"
    code: str
    message: str


class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str      # "target" | "counterparty" | "exchange" | "dex" | "contract"
    tx_count: int = 0


class GraphEdge(BaseModel):
    source: str
    target: str
    value: float = 0.0
    tx_count: int = 1


class AnalysisResult(BaseModel):
    address: str
    chain: str
    summary: Optional[WalletSummary] = None
    transactions: List[Transaction] = []
    graph_nodes: List[GraphNode] = []
    graph_edges: List[GraphEdge] = []
    risk_notes: List[RiskNote] = []
    error: Optional[str] = None
    warning: Optional[str] = None
