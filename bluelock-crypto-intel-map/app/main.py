"""
main.py
───────
FastAPI application entry point.
Defines all API routes and serves the static frontend.
"""

import os
import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, get_db, save_case, get_case, list_cases, delete_case
from app.models import AnalyzeRequest, SaveCaseRequest, AnalysisResult
from app.services.etherscan_client import BlockExplorerClient
from app.services.wallet_profiler import build_summary, parse_normal_txs, parse_token_txs
from app.services.graph_builder import build_graph
from app.services.timeline_builder import build_timeline
from app.services.risk_engine import analyze_risk


# ── Startup / Shutdown ────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup."""
    await init_db()
    print("[BlueLock] Database initialized.")
    print("[BlueLock] Dashboard ready at http://127.0.0.1:8000")
    yield


app = FastAPI(
    title="BlueLock Crypto Intel Dashboard",
    description="Defensive public-chain forensics platform",
    version="1.0.0",
    lifespan=lifespan,
)


# ── CORS (localhost-only; this tool never runs publicly) ─────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

# ── Static files ──────────────────────────────────────────────
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """Serve the main dashboard HTML."""
    return FileResponse(os.path.join(static_dir, "index.html"))


# ── Helper: validate Ethereum-style address ───────────────────
def is_valid_address(address: str) -> bool:
    """Basic validation: 0x prefix + 40 hex chars."""
    if not address:
        return False
    addr = address.strip()
    if not addr.startswith("0x"):
        return False
    if len(addr) != 42:
        return False
    try:
        int(addr, 16)
        return True
    except ValueError:
        return False


# ── API Routes ────────────────────────────────────────────────

@app.get("/api/status")
async def get_status():
    """
    Returns which chains have API keys configured.
    Used by the frontend to show/hide the API key warning.
    """
    key_status = {}
    for chain, cfg in settings.CHAIN_CONFIG.items():
        key_status[chain] = {
            "name": cfg["name"],
            "has_key": settings.has_api_key(chain),
        }
    return {"chains": key_status}


@app.post("/api/analyze")
async def analyze_wallet(req: AnalyzeRequest):
    """
    Main analysis endpoint. Fetches public on-chain data for a
    wallet address and returns a structured AnalysisResult.

    This is a read-only endpoint. No transactions are submitted.
    """
    address = req.address.strip()
    chain = req.chain.lower()

    # ── Validate address format ───────────────────────────────
    if not is_valid_address(address):
        return JSONResponse(status_code=400, content={
            "error": (
                f"'{address}' does not appear to be a valid wallet address. "
                "Expected format: 0x followed by 40 hexadecimal characters."
            )
        })

    # ── Validate chain ────────────────────────────────────────
    if chain not in settings.CHAIN_CONFIG:
        return JSONResponse(status_code=400, content={
            "error": f"Unknown chain '{chain}'. Supported: {list(settings.CHAIN_CONFIG.keys())}"
        })

    # ── Check API key ─────────────────────────────────────────
    if not settings.has_api_key(chain):
        chain_name = settings.CHAIN_CONFIG[chain]["name"]
        env_var = settings.CHAIN_CONFIG[chain]["key_env"]
        return JSONResponse(status_code=200, content={
            "error": None,
            "warning": (
                f"No API key configured for {chain_name}. "
                f"Add your {chain_name} explorer API key to the .env file as {env_var}. "
                f"Free keys available at: {settings.CHAIN_CONFIG[chain]['explorer']}/apis"
            ),
            "address": address,
            "chain": chain,
            "transactions": [],
            "graph_nodes": [],
            "graph_edges": [],
            "risk_notes": [],
            "summary": None,
        })

    # ── Fetch data from block explorer ────────────────────────
    client = BlockExplorerClient(chain)
    raw = await client.fetch_all(address)

    # Check for errors in the normal transactions fetch
    normal_data = raw.get("normal", {})
    if "error" in normal_data:
        return JSONResponse(status_code=200, content={
            "error": f"Failed to fetch transaction data: {normal_data['error']}",
            "address": address,
            "chain": chain,
            "transactions": [],
            "graph_nodes": [],
            "graph_edges": [],
            "risk_notes": [],
            "summary": None,
        })

    # ── Parse raw data ────────────────────────────────────────
    normal_txs = normal_data.get("result", []) or []
    token_data = raw.get("tokens", {})
    token_txs = token_data.get("result", []) if "error" not in token_data else []
    balance_data = raw.get("balance", {})
    balance_wei = balance_data.get("result", "0") if "error" not in balance_data else "0"

    symbol = settings.CHAIN_CONFIG[chain]["symbol"]

    # Build summary
    summary = build_summary(address, chain, symbol, normal_txs, token_txs, balance_wei)

    # Parse transactions
    parsed_normal = parse_normal_txs(address, normal_txs)
    parsed_tokens = parse_token_txs(address, token_txs)
    all_transactions = parsed_normal + parsed_tokens

    # Sort by block number descending (most recent first)
    all_transactions.sort(key=lambda t: int(t.block) if t.block.isdigit() else 0, reverse=True)

    # Build graph
    nodes, edges = build_graph(address, all_transactions)

    # Build timeline (for display)
    timeline = build_timeline(all_transactions)

    # Analyze risk notes
    risk_notes = analyze_risk(summary, all_transactions)

    return {
        "address": address,
        "chain": chain,
        "summary": summary.model_dump(),
        "transactions": timeline,
        "graph_nodes": [n.model_dump() for n in nodes],
        "graph_edges": [e.model_dump() for e in edges],
        "risk_notes": [r.model_dump() for r in risk_notes],
        "error": None,
        "warning": None,
    }


@app.post("/api/cases/save")
async def save_case_endpoint(req: SaveCaseRequest):
    """Save or update an investigation case with analyst notes."""
    async for db in get_db():
        await save_case(
            db,
            address=req.address.strip(),
            chain=req.chain,
            notes=req.notes,
            tags=req.tags,
            label=req.label,
        )
        return {"status": "saved", "address": req.address, "chain": req.chain}


@app.get("/api/cases")
async def list_cases_endpoint():
    """List all saved investigation cases."""
    async for db in get_db():
        cases = await list_cases(db)
        return {"cases": cases}


@app.get("/api/cases/{address}/{chain}")
async def get_case_endpoint(address: str, chain: str):
    """Retrieve a specific case by address and chain."""
    async for db in get_db():
        case = await get_case(db, address, chain)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        return case


@app.delete("/api/cases/{case_id}")
async def delete_case_endpoint(case_id: int):
    """Delete a case by ID."""
    async for db in get_db():
        await delete_case(db, case_id)
        return {"status": "deleted", "id": case_id}


@app.get("/api/chains")
async def get_chains():
    """Return the list of supported chains for the chain selector."""
    return {
        "chains": [
            {"id": k, "name": v["name"], "symbol": v["symbol"], "explorer": v["explorer"]}
            for k, v in settings.CHAIN_CONFIG.items()
        ]
    }
