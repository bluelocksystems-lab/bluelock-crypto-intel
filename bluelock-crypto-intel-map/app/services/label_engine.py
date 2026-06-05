"""
label_engine.py
───────────────
Assigns human-readable labels to wallet addresses based on a
curated list of known exchange hot wallets, DEX routers,
bridge contracts, and other labeled addresses.

Labels are informational only. They indicate what an address
is commonly associated with — not proof of any specific activity.

Sources: public blockchain intelligence databases, on-chain labels.
"""

import json
import os

# ── Known address labels ──────────────────────────────────────
# These are well-known, publicly documented contract/wallet addresses.
# Format: "0xlowercase": ("Label", "category")
# Categories: exchange | dex | bridge | stablecoin | nft | defi | system

KNOWN_LABELS: dict = {
    # ── Ethereum: Exchanges (hot/deposit wallets) ─────────────
    "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be": ("Binance Hot Wallet", "exchange"),
    "0xd551234ae421e3bcba99a0da6d736074f22192ff": ("Binance Hot Wallet 2", "exchange"),
    "0x564286362092d8e7936f0549571a803b203aaced": ("Binance Hot Wallet 3", "exchange"),
    "0x0681d8db095565fe8a346fa0277bffde9c0edbbf": ("Binance Hot Wallet 4", "exchange"),
    "0xfe9e8709d3215310075d67e3ed32a380ccf451c8": ("Binance Hot Wallet 5", "exchange"),
    "0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67": ("Binance Hot Wallet 6", "exchange"),
    "0xa09871aeadf4994ca12f5c0b6056bbd1d343c029": ("Coinbase", "exchange"),
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": ("Coinbase 2", "exchange"),
    "0x503828976d22510aad0201ac7ec88293211d23da": ("Coinbase 3", "exchange"),
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": ("Coinbase 4", "exchange"),
    "0x3cd751e6b0078be393132286c442345e5dc49699": ("Coinbase 5", "exchange"),
    "0xb5d85cbf7cb3ee0d56b3bb207d5fc4b82f43f511": ("Coinbase 6", "exchange"),
    "0xeb2629a2734e272bcc07bda959863f316f4bd4cf": ("Coinbase 7", "exchange"),
    "0x2b5634c42055806a59e9107ed44d43c426e58258": ("KuCoin", "exchange"),
    "0x689c56aef474df92d44a1b70850f808488f9769c": ("KuCoin 2", "exchange"),
    "0xa1d8d972560c2f8144af871db508f0b0b10a3fbf": ("KuCoin 3", "exchange"),
    "0xd6216fc19db775df9774a6e33526131da7d19a2c": ("KuCoin 4", "exchange"),
    "0xab5c66752a9e8167967685f1450532fb96d5d24f": ("Huobi", "exchange"),
    "0x6748f50f686bfbca6fe8ad62b22228b87f31ff2b": ("Huobi 2", "exchange"),
    "0xfdb16996831753d5331ff813c29a93c76834a0ad": ("Huobi 3", "exchange"),
    "0x0c0dee82c83274570d6a2b9e2e4a36d8a34dea4b": ("OKX", "exchange"),
    "0x98ec059dc3adfbdd63429454aeb0c990fba4a128": ("OKX 2", "exchange"),
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": ("OKX 3", "exchange"),
    "0x236f9f97e0e62388479bf9e5ba4889e46b0273c3": ("Bitfinex", "exchange"),
    "0x1151314c646ce4e0efd76d1af4760ae66a9fe30f": ("Bitfinex 2", "exchange"),

    # ── Ethereum: DEX Routers ────────────────────────────────
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": ("Uniswap V2 Router", "dex"),
    "0xe592427a0aece92de3edee1f18e0157c05861564": ("Uniswap V3 Router", "dex"),
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": ("Uniswap Universal Router", "dex"),
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": ("SushiSwap Router", "dex"),
    "0x1111111254fb6c44bac0bed2854e76f90643097d": ("1inch V4 Router", "dex"),
    "0x1111111254eeb25477b68fb85ed929f73a960582": ("1inch V5 Router", "dex"),
    "0xdef1c0ded9bec7f1a1670819833240f027b25eff": ("0x Exchange Proxy", "dex"),
    "0xba12222222228d8ba445958a75a0704d566bf2c8": ("Balancer Vault", "dex"),
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": ("Uniswap Universal Router 2", "dex"),

    # ── Ethereum: Bridges ────────────────────────────────────
    "0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf": ("Polygon Bridge", "bridge"),
    "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1": ("Optimism Bridge", "bridge"),
    "0x8eb8a3b98659cce290402893d0123abb75e3ab28": ("Avalanche Bridge", "bridge"),
    "0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f": ("Arbitrum Bridge", "bridge"),
    "0xa0c68c638235ee32657e8f720a23cec1bfc77c77": ("Polygon Plasma Bridge", "bridge"),

    # ── Ethereum: Stablecoins & Tokens ───────────────────────
    "0xdac17f958d2ee523a2206206994597c13d831ec7": ("USDT Contract", "stablecoin"),
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": ("USDC Contract", "stablecoin"),
    "0x6b175474e89094c44da98b954eedeac495271d0f": ("DAI Contract", "stablecoin"),
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": ("WBTC Contract", "stablecoin"),
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": ("WETH Contract", "defi"),

    # ── BNB Chain: DEX Routers ───────────────────────────────
    "0x10ed43c718714eb63d5aa57b78b54704e256024e": ("PancakeSwap Router V2", "dex"),
    "0x13f4ea83d0bd40e75c8222255bc855a974568dd4": ("PancakeSwap Router V3", "dex"),
    "0x05ff2b0db69458a0750badebc4f9e13add608c7f": ("PancakeSwap Router V1", "dex"),

    # ── Polygon: DEX Routers ─────────────────────────────────
    "0xa5e0829caced8ffdd4de3c43696c57f7d7a678ff": ("QuickSwap Router", "dex"),

    # ── Arbitrum: DEX Routers ────────────────────────────────
    "0x1b02da8cb0d097eb8d57a175b88c7d8b47997506": ("SushiSwap Arbitrum Router", "dex"),
}


def load_labels_from_file() -> dict:
    """
    Load additional labels from data/labels.json if it exists.
    Useful for adding custom labels without modifying this file.
    Format: {"0xaddress": ["Label Name", "category"]}
    """
    labels_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "labels.json"
    )
    if not os.path.exists(labels_path):
        return {}
    try:
        with open(labels_path, "r") as f:
            raw = json.load(f)
            return {k.lower(): tuple(v) for k, v in raw.items()}
    except Exception:
        return {}


# Merge built-in labels with file-based labels at import time
_ALL_LABELS = {**KNOWN_LABELS, **load_labels_from_file()}


def get_label(address: str) -> tuple:
    """
    Look up a label for a given address.
    Returns (label_text, category) or (None, None) if unknown.
    """
    if not address:
        return None, None
    key = address.lower()
    result = _ALL_LABELS.get(key)
    if result:
        return result[0], result[1]
    return None, None


def is_known_dex(address: str) -> bool:
    _, cat = get_label(address)
    return cat == "dex"


def is_known_exchange(address: str) -> bool:
    _, cat = get_label(address)
    return cat == "exchange"


def is_known_bridge(address: str) -> bool:
    _, cat = get_label(address)
    return cat == "bridge"


def label_summary(address: str) -> str:
    """Return a short display label or None."""
    lbl, _ = get_label(address)
    return lbl
