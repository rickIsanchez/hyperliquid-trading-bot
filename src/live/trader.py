"""
Live Trading Daemon

Runs strategies in real-time against HyperLiquid:
- Fetches live candle data at configurable intervals
- Generates signals and executes trades
- Manages positions, SL/TP, and risk limits
"""

import logging
import time
import json
from datetime import datetime
from typing import Optional, Dict, List, Any

from ..client import HyperLiquidClient
from ..strategies.base import BaseStrategy, Signal

logger = logging.getLogger(__name__)


class LiveTrader:
    """Live trading daemon for HyperLiquid."""

    def __init__(
        self,
        client: HyperLiquidClient,
        strategies: Dict[str, BaseStrategy],
        config: Dict[str, Any],
    ):
        """
        Args:
            client: Authenticated HyperLiquidClient
            strategies: Map of symbol -> strategy instance
            config: Trading configuration
        """
        self.client = client
        self.strategies = strategies
        self.config = config
        self.running = False

        # Trading params
        self.trade_size_usd = config.get("trade_size_usd", 1000)
        self.max_positions = config.get("max_positions", 5)
        self.tick_interval = config.get("tick_interval_seconds", 900)  # 15m default
        self.leverage = config.get("leverage", 5)
        self.symbols = list(strategies.keys())

    def start(self):
        """Start the trading loop."""
        self.running = True
        logger.info(f"LiveTrader starting: symbols={self.symbols}, tick={self.tick_interval}s")

        # Set leverage for all symbols
        for symbol in self.symbols:
            try:
                self.client.set_leverage(symbol, self.leverage)
            except Exception as e:
                logger.error(f"Failed to set leverage for {symbol}: {e}")

        while self.running:
            try:
                self._tick()
            except KeyboardInterrupt:
                logger.info("Stopping LiveTrader (KeyboardInterrupt)")
                self.running = False
            except Exception as e:
                logger.error(f"Tick error: {e}", exc_info=True)

            if self.running:
                logger.debug(f"Sleeping {self.tick_interval}s until next tick...")
                time.sleep(self.tick_interval)

        logger.info("LiveTrader stopped.")

    def stop(self):
        """Stop the trading loop."""
        self.running = False

    def _tick(self):
        """Single trading tick: fetch data, generate signals, execute."""
        positions = self.client.get_positions()
        position_symbols = {p["coin"] for p in positions}
        account_value = self.client.get_account_value()

        logger.info(f"Tick @ {datetime.now()} | Account: ${account_value:.2f} | Positions: {len(positions)}")

        for symbol, strategy in self.strategies.items():
            try:
                self._process_symbol(symbol, strategy, positions, position_symbols, account_value)
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}", exc_info=True)

    def _process_symbol(
        self,
        symbol: str,
        strategy: BaseStrategy,
        positions: List[Dict],
        position_symbols: set,
        account_value: float,
    ):
        """Process a single symbol: get data, signal, and execute."""
        import pandas as pd

        # Fetch recent candles
        candles = self.client.get_candles(
            symbol,
            interval=self.config.get("timeframe", "15m"),
            start_time=int((datetime.now().timestamp() - 86400 * 7) * 1000),  # 7 days
            end_time=int(datetime.now().timestamp() * 1000),
        )

        if not candles:
            logger.warning(f"No candle data for {symbol}")
            return

        # Convert to DataFrame
        df = pd.DataFrame(candles)
        rename_map = {"t": "timestamp", "T": "timestamp", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"}
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col])
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df = df.set_index("timestamp")

        # Generate signal
        signal = strategy.generate_signal(df, symbol)
        logger.info(f"{symbol} | {strategy.name} -> {signal.signal.value} (conf={signal.confidence:.2f})")

        if not signal.is_actionable:
            return

        has_position = symbol in position_symbols

        # Execute
        if signal.signal == Signal.BUY and not has_position:
            if len(positions) >= self.max_positions:
                logger.info(f"Max positions ({self.max_positions}) reached, skipping BUY {symbol}")
                return
            size_usd = min(self.trade_size_usd, account_value * 0.2)
            price = signal.price
            size = size_usd / price
            result = self.client.market_buy(symbol, size)
            logger.info(f"OPENED LONG {symbol}: size={size:.6f} (~${size_usd:.0f}) | {result}")

        elif signal.signal == Signal.SELL and not has_position:
            if len(positions) >= self.max_positions:
                logger.info(f"Max positions ({self.max_positions}) reached, skipping SELL {symbol}")
                return
            size_usd = min(self.trade_size_usd, account_value * 0.2)
            price = signal.price
            size = size_usd / price
            result = self.client.market_sell(symbol, size)
            logger.info(f"OPENED SHORT {symbol}: size={size:.6f} (~${size_usd:.0f}) | {result}")

        elif has_position:
            # Check if signal is opposite to current position -> close
            current_pos = next((p for p in positions if p["coin"] == symbol), None)
            if current_pos:
                is_long = float(current_pos["szi"]) > 0
                if (signal.signal == Signal.SELL and is_long) or (signal.signal == Signal.BUY and not is_long):
                    result = self.client.market_close(symbol)
                    logger.info(f"CLOSED {symbol}: {result}")
