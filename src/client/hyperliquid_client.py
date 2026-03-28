"""
HyperLiquid API Client Wrapper

Wraps the official hyperliquid-python-sdk for simplified bot integration.
Supports both mainnet and testnet.
"""

import os
import logging
from typing import Optional, List, Dict, Any

import eth_account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

logger = logging.getLogger(__name__)


class HyperLiquidClient:
    """Unified client for HyperLiquid Info (read) and Exchange (write) APIs."""

    def __init__(
        self,
        private_key: Optional[str] = None,
        testnet: bool = False,
        account_address: Optional[str] = None,
    ):
        self.api_url = constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL
        self.testnet = testnet

        # Info API (always available, no auth needed)
        self.info = Info(self.api_url, skip_ws=True)

        # Exchange API (needs private key)
        self.exchange: Optional[Exchange] = None
        if private_key:
            self._init_exchange(private_key, account_address)

    def _init_exchange(self, private_key: str, account_address: Optional[str] = None):
        """Initialize authenticated exchange client."""
        wallet = eth_account.Account.from_key(private_key)
        self.address = account_address or wallet.address
        self.exchange = Exchange(
            wallet, self.api_url, account_address=self.address
        )
        logger.info(f"Exchange initialized for {self.address} ({'testnet' if self.testnet else 'mainnet'})")

    # ─── Info Methods ───────────────────────────────────────────────

    def get_all_mids(self) -> Dict[str, str]:
        """Get current mid prices for all assets."""
        return self.info.all_mids()

    def get_mid_price(self, symbol: str) -> Optional[float]:
        """Get mid price for a single asset."""
        mids = self.info.all_mids()
        price = mids.get(symbol)
        return float(price) if price else None

    def get_user_state(self, address: Optional[str] = None) -> Dict[str, Any]:
        """Get user positions, margin summary, and account value."""
        addr = address or self.address
        return self.info.user_state(addr)

    def get_open_orders(self, address: Optional[str] = None) -> List[Dict]:
        """Get all open orders for a user."""
        addr = address or self.address
        return self.info.open_orders(addr)

    def get_user_fills(self, address: Optional[str] = None) -> List[Dict]:
        """Get recent fills for a user."""
        addr = address or self.address
        return self.info.user_fills(addr)

    def get_candles(
        self,
        symbol: str,
        interval: str = "15m",
        start_time: int = 0,
        end_time: int = 0,
    ) -> List[Dict]:
        """Get OHLCV candle data.

        Args:
            symbol: Asset name (e.g., "BTC")
            interval: Candle interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            start_time: Start timestamp in ms
            end_time: End timestamp in ms
        """
        return self.info.candles_snapshot(symbol, interval, start_time, end_time)

    def get_l2_book(self, symbol: str) -> Dict:
        """Get L2 order book snapshot."""
        return self.info.l2_snapshot(symbol)

    def get_meta(self) -> Dict:
        """Get exchange metadata (assets, decimals, etc.)."""
        return self.info.meta()

    def get_funding_history(
        self, symbol: str, start_time: int, end_time: Optional[int] = None
    ) -> List[Dict]:
        """Get funding rate history."""
        return self.info.funding_history(symbol, start_time, end_time)

    # ─── Exchange Methods ───────────────────────────────────────────

    def _require_exchange(self):
        if self.exchange is None:
            raise RuntimeError("Exchange not initialized. Provide private_key to HyperLiquidClient.")

    def market_buy(self, symbol: str, size: float, slippage: float = 0.05) -> Dict:
        """Open a long position with market order."""
        self._require_exchange()
        result = self.exchange.market_open(symbol, True, size, slippage=slippage)
        logger.info(f"Market BUY {symbol} size={size}: {result}")
        return result

    def market_sell(self, symbol: str, size: float, slippage: float = 0.05) -> Dict:
        """Open a short position with market order."""
        self._require_exchange()
        result = self.exchange.market_open(symbol, False, size, slippage=slippage)
        logger.info(f"Market SELL {symbol} size={size}: {result}")
        return result

    def market_close(self, symbol: str, size: Optional[float] = None, slippage: float = 0.05) -> Dict:
        """Close position for a symbol."""
        self._require_exchange()
        result = self.exchange.market_close(symbol, sz=size, slippage=slippage)
        logger.info(f"Market CLOSE {symbol}: {result}")
        return result

    def limit_order(
        self,
        symbol: str,
        is_buy: bool,
        size: float,
        price: float,
        post_only: bool = False,
        reduce_only: bool = False,
    ) -> Dict:
        """Place a limit order."""
        self._require_exchange()
        order_type = {"limit": {"tif": "Alo" if post_only else "Gtc"}}
        result = self.exchange.order(symbol, is_buy, size, price, order_type, reduce_only=reduce_only)
        side = "BUY" if is_buy else "SELL"
        logger.info(f"Limit {side} {symbol} size={size} px={price}: {result}")
        return result

    def cancel_order(self, symbol: str, oid: int) -> Dict:
        """Cancel an order by OID."""
        self._require_exchange()
        result = self.exchange.cancel(symbol, oid)
        logger.info(f"Cancel {symbol} oid={oid}: {result}")
        return result

    def cancel_all_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Cancel all open orders, optionally filtered by symbol."""
        self._require_exchange()
        orders = self.get_open_orders()
        if symbol:
            orders = [o for o in orders if o.get("coin") == symbol]

        results = []
        for order in orders:
            try:
                r = self.exchange.cancel(order["coin"], order["oid"])
                results.append(r)
            except Exception as e:
                logger.error(f"Failed to cancel order {order['oid']}: {e}")
        return results

    def set_leverage(self, symbol: str, leverage: int, is_cross: bool = True) -> Dict:
        """Set leverage for a symbol."""
        self._require_exchange()
        result = self.exchange.update_leverage(leverage, symbol, is_cross=is_cross)
        mode = "cross" if is_cross else "isolated"
        logger.info(f"Leverage {symbol} -> {leverage}x ({mode}): {result}")
        return result

    def get_account_value(self) -> float:
        """Get total account value in USD."""
        state = self.get_user_state()
        return float(state.get("marginSummary", {}).get("accountValue", 0))

    def get_positions(self) -> List[Dict]:
        """Get all open positions with details."""
        state = self.get_user_state()
        positions = state.get("assetPositions", [])
        return [p["position"] for p in positions if float(p["position"]["szi"]) != 0]
