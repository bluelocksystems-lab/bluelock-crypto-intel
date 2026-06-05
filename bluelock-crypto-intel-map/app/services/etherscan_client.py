"""
etherscan_client.py
───────────────────
Handles all HTTP calls to Etherscan API V2.

Etherscan API V2 uses:
    https://api.etherscan.io/v2/api
with a required chainid parameter.

All calls are read-only. No transactions are ever submitted.
"""

import asyncio
import httpx

from app.config import settings


class BlockExplorerClient:
    """
    Thin async client for Etherscan API V2.
    Uses one unified endpoint and injects chainid on every request.
    """

    def __init__(self, chain: str):
        cfg = settings.CHAIN_CONFIG.get(chain)
        if not cfg:
            raise ValueError(f"Unknown chain: {chain}")

        self.chain = chain
        self.chainid = cfg["chainid"]
        self.base_url = cfg["api_url"]
        self.api_key = settings.get_api_key(chain)
        self.symbol = cfg["symbol"]

    async def _get(self, params: dict) -> dict:
        """
        Internal GET helper. Injects chainid + API key and handles errors.
        Returns the parsed JSON response or a dict with an 'error' key.
        """
        query = dict(params)
        query["chainid"] = self.chainid

        if self.api_key:
            query["apikey"] = self.api_key

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=query)
                response.raise_for_status()
                data = response.json()

            # Etherscan returns status "0" with message on failure.
            if data.get("status") == "0":
                msg = data.get("message", "Unknown error")
                result = data.get("result", "")

                # These are normal empty responses, not hard failures.
                if "No transactions found" in str(result):
                    return {"status": "1", "message": "OK", "result": []}
                if "No records found" in str(result):
                    return {"status": "1", "message": "OK", "result": []}

                return {"error": f"API: {msg} — {result}"}

            return data

        except httpx.TimeoutException:
            return {"error": "Request timed out. Check your internet connection or API rate limit."}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except ValueError:
            return {"error": "Explorer returned non-JSON data. Check API endpoint or key."}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    # ── Public methods ────────────────────────────────────────

    async def get_balance(self, address: str) -> dict:
        """Fetch native token balance for an address."""
        return await self._get({
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
        })

    async def get_normal_txs(self, address: str, limit: int = None) -> dict:
        """Fetch normal native-token transactions for an address."""
        limit = limit or settings.MAX_TX_FETCH
        return await self._get({
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": "0",
            "endblock": "99999999",
            "page": "1",
            "offset": str(limit),
            "sort": "desc",
        })

    async def get_token_txs(self, address: str, limit: int = None) -> dict:
        """Fetch ERC-20 token transfer events for an address."""
        limit = limit or settings.MAX_TX_FETCH
        return await self._get({
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": "0",
            "endblock": "99999999",
            "page": "1",
            "offset": str(limit),
            "sort": "desc",
        })

    async def get_internal_txs(self, address: str, limit: int = None) -> dict:
        """Fetch internal contract-generated transactions."""
        limit = limit or min(settings.MAX_TX_FETCH, 25)
        return await self._get({
            "module": "account",
            "action": "txlistinternal",
            "address": address,
            "startblock": "0",
            "endblock": "99999999",
            "page": "1",
            "offset": str(limit),
            "sort": "desc",
        })

    async def fetch_all(self, address: str) -> dict:
        """
        Fetch normal txs, token txs, internal txs, and balance concurrently.
        Returns a combined dict with all results.
        """
        results = await asyncio.gather(
            self.get_normal_txs(address),
            self.get_token_txs(address),
            self.get_internal_txs(address),
            self.get_balance(address),
            return_exceptions=True,
        )

        normal_resp, token_resp, internal_resp, balance_resp = results

        return {
            "normal": normal_resp if isinstance(normal_resp, dict) else {"error": str(normal_resp)},
            "tokens": token_resp if isinstance(token_resp, dict) else {"error": str(token_resp)},
            "internal": internal_resp if isinstance(internal_resp, dict) else {"error": str(internal_resp)},
            "balance": balance_resp if isinstance(balance_resp, dict) else {"error": str(balance_resp)},
        }
