"""
config.py
─────────
Central configuration loaded from .env via python-dotenv.
Etherscan API V2 uses one unified API endpoint plus a chainid parameter.
"""

import os
from dotenv import load_dotenv

# Load .env from the project root (one level above app/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


class Settings:
    # ── API Keys ──────────────────────────────────────────────
    # Etherscan V2 can use ONE key across supported EVM chains.
    ETHERSCAN_API_KEY: str = os.getenv("ETHERSCAN_API_KEY", "")
    BSCSCAN_API_KEY: str = os.getenv("BSCSCAN_API_KEY", "")
    POLYGONSCAN_API_KEY: str = os.getenv("POLYGONSCAN_API_KEY", "")
    ARBISCAN_API_KEY: str = os.getenv("ARBISCAN_API_KEY", "")
    BASESCAN_API_KEY: str = os.getenv("BASESCAN_API_KEY", "")

    # ── API Base URLs ─────────────────────────────────────────
    # IMPORTANT:
    # Etherscan V1 endpoints such as https://api.etherscan.io/api are deprecated.
    # V2 uses the unified endpoint below plus chainid.
    ETHERSCAN_V2_API_URL: str = "https://api.etherscan.io/v2/api"

    CHAIN_CONFIG: dict = {
        "ethereum": {
            "name": "Ethereum",
            "chainid": "1",
            "api_url": ETHERSCAN_V2_API_URL,
            "explorer": "https://etherscan.io",
            "key_env": "ETHERSCAN_API_KEY",
            "symbol": "ETH",
        },
        "bsc": {
            "name": "BNB Chain",
            "chainid": "56",
            "api_url": ETHERSCAN_V2_API_URL,
            "explorer": "https://bscscan.com",
            "key_env": "BSCSCAN_API_KEY",
            "symbol": "BNB",
        },
        "polygon": {
            "name": "Polygon",
            "chainid": "137",
            "api_url": ETHERSCAN_V2_API_URL,
            "explorer": "https://polygonscan.com",
            "key_env": "POLYGONSCAN_API_KEY",
            "symbol": "MATIC",
        },
        "arbitrum": {
            "name": "Arbitrum",
            "chainid": "42161",
            "api_url": ETHERSCAN_V2_API_URL,
            "explorer": "https://arbiscan.io",
            "key_env": "ARBISCAN_API_KEY",
            "symbol": "ETH",
        },
        "base": {
            "name": "Base",
            "chainid": "8453",
            "api_url": ETHERSCAN_V2_API_URL,
            "explorer": "https://basescan.org",
            "key_env": "BASESCAN_API_KEY",
            "symbol": "ETH",
        },
    }

    # ── General settings ──────────────────────────────────────
    MAX_TX_FETCH: int = int(os.getenv("MAX_TX_FETCH", "50"))
    # Resolve DB path relative to project root (parent of this app/ dir)
    _PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        os.getenv("DB_PATH", "data/cases.db")
    )

    def get_api_key(self, chain: str) -> str:
        """
        Return the API key for the given chain identifier.

        Etherscan V2 supports one unified API key across supported EVM chains.
        Chain-specific env vars are still supported for compatibility, but if
        those are blank we fall back to ETHERSCAN_API_KEY.
        """
        cfg = self.CHAIN_CONFIG.get(chain, {})
        env_var = cfg.get("key_env", "")

        chain_specific = os.getenv(env_var, "").strip() if env_var else ""
        unified = os.getenv("ETHERSCAN_API_KEY", "").strip()

        return chain_specific or unified

    def has_api_key(self, chain: str) -> bool:
        return bool(self.get_api_key(chain))


# Singleton instance used throughout the app
settings = Settings()
