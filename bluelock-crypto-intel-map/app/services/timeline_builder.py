"""
timeline_builder.py
───────────────────
Organizes transactions into a timeline suitable for display.
Sorts by block number (most recent first) and groups by date.
Also flags large movements for the "large movement alerts" panel.
"""

from app.models import Transaction


# Threshold in native token units to flag as "large movement"
LARGE_MOVEMENT_THRESHOLD = 5.0  # e.g., 5 ETH / 5 BNB


def build_timeline(transactions: list[Transaction]) -> list[dict]:
    """
    Returns a list of dicts ready for frontend rendering.
    Each item contains all transaction fields plus a 'flagged' bool.
    """
    timeline = []

    for tx in transactions:
        # Try to determine if value is large
        try:
            val = float(tx.value_eth)
        except (ValueError, TypeError):
            val = 0.0

        flagged = val >= LARGE_MOVEMENT_THRESHOLD

        timeline.append({
            "hash": tx.hash,
            "hash_short": f"{tx.hash[:10]}...{tx.hash[-6:]}" if tx.hash else "",
            "block": tx.block,
            "timestamp": tx.timestamp,
            "from": tx.from_addr,
            "to": tx.to_addr,
            "value": tx.value_eth,
            "token_symbol": tx.token_symbol,
            "token_name": tx.token_name,
            "direction": tx.direction,
            "tx_type": tx.tx_type,
            "counterparty": tx.counterparty,
            "counterparty_label": tx.counterparty_label,
            "flagged": flagged,
        })

    return timeline
