"""
wallet_profiler.py
──────────────────
Processes raw API responses into structured WalletSummary and
Transaction objects. Normalizes values, timestamps, and directions.
"""

from datetime import datetime, timezone
from app.models import Transaction, WalletSummary
from app.services.label_engine import get_label, label_summary


def wei_to_eth(wei_str: str, decimals: int = 18) -> str:
    """Convert a wei string to a human-readable decimal string."""
    try:
        value = int(wei_str) / (10 ** decimals)
        if value == 0:
            return "0"
        if value < 0.0001:
            return f"{value:.8f}"
        return f"{value:.6f}"
    except (ValueError, TypeError):
        return "0"


def ts_to_datetime(ts_str: str) -> str:
    """Convert a Unix timestamp string to a readable UTC datetime."""
    try:
        ts = int(ts_str)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, TypeError):
        return "Unknown"


def build_summary(address: str, chain: str, symbol: str,
                  normal_txs: list, token_txs: list,
                  balance_wei: str) -> WalletSummary:
    """
    Build a WalletSummary from raw transaction lists and balance.
    """
    all_ts = []
    for tx in normal_txs:
        ts = tx.get("timeStamp", "")
        if ts:
            try:
                all_ts.append(int(ts))
            except ValueError:
                pass

    first_seen = ts_to_datetime(str(min(all_ts))) if all_ts else None
    last_seen = ts_to_datetime(str(max(all_ts))) if all_ts else None

    return WalletSummary(
        address=address,
        chain=chain,
        tx_count=len(normal_txs),
        token_tx_count=len(token_txs),
        first_seen=first_seen,
        last_seen=last_seen,
        native_balance=wei_to_eth(balance_wei) if balance_wei else None,
        symbol=symbol,
    )


def parse_normal_txs(address: str, raw_txs: list) -> list[Transaction]:
    """
    Parse normal (native) transactions into Transaction objects.
    Identifies direction (in/out) relative to the target address.
    """
    address_lower = address.lower()
    transactions = []

    for tx in raw_txs:
        from_addr = tx.get("from", "").lower()
        to_addr = tx.get("to", "").lower()
        value = tx.get("value", "0")
        is_error = tx.get("isError", "0") == "1"

        if is_error:
            continue  # Skip failed transactions

        direction = "out" if from_addr == address_lower else "in"
        counterparty = to_addr if direction == "out" else from_addr

        # Detect if this looks like a contract interaction
        tx_type = "native"
        if tx.get("input", "0x") not in ("0x", "0x0", ""):
            tx_type = "contract"

        lbl = label_summary(counterparty)

        transactions.append(Transaction(
            hash=tx.get("hash", ""),
            block=tx.get("blockNumber", ""),
            timestamp=ts_to_datetime(tx.get("timeStamp", "0")),
            from_addr=from_addr,
            to_addr=to_addr,
            value_eth=wei_to_eth(value),
            direction=direction,
            tx_type=tx_type,
            counterparty=counterparty,
            counterparty_label=lbl,
        ))

    return transactions


def parse_token_txs(address: str, raw_txs: list) -> list[Transaction]:
    """
    Parse ERC-20 token transfer events into Transaction objects.
    """
    address_lower = address.lower()
    transactions = []

    for tx in raw_txs:
        from_addr = tx.get("from", "").lower()
        to_addr = tx.get("to", "").lower()
        value = tx.get("value", "0")
        decimals = int(tx.get("tokenDecimal", "18"))
        symbol = tx.get("tokenSymbol", "?")
        name = tx.get("tokenName", "Unknown Token")
        contract = tx.get("contractAddress", "").lower()

        direction = "out" if from_addr == address_lower else "in"
        counterparty = to_addr if direction == "out" else from_addr

        # Is the counterparty a known DEX router?
        _, cat = get_label(counterparty)
        tx_type = "dex" if cat == "dex" else "token"

        lbl = label_summary(counterparty)

        transactions.append(Transaction(
            hash=tx.get("hash", ""),
            block=tx.get("blockNumber", ""),
            timestamp=ts_to_datetime(tx.get("timeStamp", "0")),
            from_addr=from_addr,
            to_addr=to_addr,
            value_eth=wei_to_eth(value, decimals),
            token_symbol=symbol,
            token_name=name,
            direction=direction,
            tx_type=tx_type,
            counterparty=counterparty,
            counterparty_label=lbl,
        ))

    return transactions
