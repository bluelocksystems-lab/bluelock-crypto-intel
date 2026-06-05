"""
risk_engine.py
──────────────
Produces a set of RiskNote observations based on wallet behavior.

IMPORTANT: These are observational notes only.
No note constitutes proof of illicit activity.
All findings require manual verification by a qualified analyst.

Language is intentionally hedged — we state what was observed
in public on-chain data, not conclusions about intent.
"""

from app.models import Transaction, WalletSummary, RiskNote
from app.services.label_engine import get_label


def analyze_risk(
    summary: WalletSummary,
    transactions: list[Transaction],
) -> list[RiskNote]:
    """
    Run heuristic checks and return a list of RiskNote objects.
    """
    notes: list[RiskNote] = []
    if not summary or not transactions:
        return notes

    address_lower = summary.address.lower()
    total_txs = len(transactions)

    # ── Counters ──────────────────────────────────────────────
    exchange_interactions = 0
    dex_interactions = 0
    bridge_interactions = 0
    fresh_wallet_interactions = 0  # counterparties with very few txs (unknown)
    incoming_count = 0
    outgoing_count = 0
    large_movement_count = 0
    unique_counterparties = set()

    for tx in transactions:
        cp = tx.counterparty.lower() if tx.counterparty else ""
        if not cp:
            continue

        unique_counterparties.add(cp)
        _, cat = get_label(cp)

        if cat == "exchange":
            exchange_interactions += 1
        elif cat == "dex":
            dex_interactions += 1
        elif cat == "bridge":
            bridge_interactions += 1

        if tx.direction == "in":
            incoming_count += 1
        else:
            outgoing_count += 1

        try:
            val = float(tx.value_eth)
            if val >= 5.0:
                large_movement_count += 1
        except (ValueError, TypeError):
            pass

    # ── Heuristic checks ──────────────────────────────────────

    # New / low-activity wallet
    if total_txs < 5:
        notes.append(RiskNote(
            level="warning",
            code="NEW_WALLET",
            message=(
                "Low transaction history observed. "
                "This wallet has fewer than 5 recorded transactions. "
                "Requires manual verification — may be a newly created wallet."
            ),
        ))

    # High-volume wallet
    if total_txs >= 200:
        notes.append(RiskNote(
            level="info",
            code="HIGH_VOLUME",
            message=(
                f"High transaction volume observed ({total_txs} txs). "
                "This may indicate an active trading wallet, bot, or service account."
            ),
        ))

    # Many unique counterparties — potential mixing or distribution
    if len(unique_counterparties) > 50:
        notes.append(RiskNote(
            level="warning",
            code="MANY_COUNTERPARTIES",
            message=(
                f"Observed interactions with {len(unique_counterparties)} unique addresses. "
                "High counterparty count may indicate distribution activity. "
                "Requires manual verification."
            ),
        ))

    # Possible exchange interaction
    if exchange_interactions > 0:
        notes.append(RiskNote(
            level="info",
            code="EXCHANGE_INTERACTION",
            message=(
                f"Possible exchange interaction detected ({exchange_interactions} txs). "
                "One or more counterparties are labeled as known exchange wallets. "
                "This is common for normal trading activity."
            ),
        ))

    # Possible DEX interaction
    if dex_interactions > 0:
        notes.append(RiskNote(
            level="info",
            code="DEX_INTERACTION",
            message=(
                f"Possible DEX router interaction detected ({dex_interactions} txs). "
                "One or more counterparties appear to be known DEX routers "
                "(Uniswap, SushiSwap, PancakeSwap, 1inch, etc.)."
            ),
        ))

    # Possible bridge interaction
    if bridge_interactions > 0:
        notes.append(RiskNote(
            level="info",
            code="BRIDGE_INTERACTION",
            message=(
                f"Possible bridge interaction detected ({bridge_interactions} txs). "
                "Funds may have been moved cross-chain. "
                "Trace continued on destination chain is recommended."
            ),
        ))

    # Large movements
    if large_movement_count > 0:
        notes.append(RiskNote(
            level="warning",
            code="LARGE_MOVEMENT",
            message=(
                f"Large value movements observed ({large_movement_count} txs ≥ 5 native tokens). "
                "Flagged for analyst review."
            ),
        ))

    # Heavily outgoing vs incoming ratio (possible drainer pattern — needs verification)
    if total_txs >= 10 and outgoing_count > 0 and incoming_count == 0:
        notes.append(RiskNote(
            level="warning",
            code="OUTGOING_ONLY",
            message=(
                "Only outgoing transactions observed in this dataset. "
                "No incoming native transfers detected. "
                "Requires manual verification of full transaction history."
            ),
        ))

    # All incoming, no outgoing (possible accumulator / deposit wallet)
    if total_txs >= 10 and incoming_count > 0 and outgoing_count == 0:
        notes.append(RiskNote(
            level="info",
            code="INCOMING_ONLY",
            message=(
                "Only incoming transactions observed in this dataset. "
                "May be a deposit or accumulation wallet. "
                "Requires manual verification."
            ),
        ))

    return notes
