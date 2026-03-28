"""
Backtest Engine

Simulates strategy execution on historical data with:
- Configurable fees, slippage, and position sizing
- Support for long and short positions
- Trade logging and metric calculation
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import pandas as pd
import numpy as np

from ..strategies.base import BaseStrategy, Signal, TradeSignal
from .metrics import calculate_metrics

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a completed trade."""
    symbol: str
    side: str  # "LONG" or "SHORT"
    entry_price: float
    exit_price: float
    entry_time: Any
    exit_time: Any
    size: float
    pnl: float
    pnl_pct: float
    fees: float
    exit_reason: str  # "signal", "stop_loss", "take_profit"


@dataclass
class BacktestResult:
    """Complete backtest result."""
    strategy_name: str
    symbol: str
    timeframe: str
    start_date: Any
    end_date: Any
    trades: List[Trade]
    equity_curve: pd.Series
    metrics: Dict[str, float]


class BacktestEngine:
    """Event-driven backtest engine."""

    def __init__(
        self,
        initial_capital: float = 10000.0,
        fee_rate: float = 0.00045,  # 0.045% taker fee (HyperLiquid Tier 0)
        slippage: float = 0.0001,   # 0.01% slippage
        position_size_pct: float = 0.1,  # 10% of capital per trade
        max_positions: int = 1,
    ):
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage = slippage
        self.position_size_pct = position_size_pct
        self.max_positions = max_positions

    def run(
        self,
        strategy: BaseStrategy,
        df: pd.DataFrame,
        symbol: str = "BTC",
        timeframe: str = "15m",
    ) -> BacktestResult:
        """Run backtest on historical data.

        Args:
            strategy: Strategy instance
            df: OHLCV DataFrame
            symbol: Asset symbol
            timeframe: Candle timeframe

        Returns:
            BacktestResult with trades, equity curve, and metrics
        """
        if not strategy.validate_data(df):
            raise ValueError(f"Insufficient data for {strategy.name} (need {strategy.warmup_periods} candles)")

        capital = self.initial_capital
        position: Optional[Dict] = None  # Current open position
        trades: List[Trade] = []
        equity = []

        logger.info(f"Running backtest: {strategy.name} on {symbol} {timeframe} ({len(df)} candles)")

        pending_signal: Optional[TradeSignal] = None  # Signal from previous bar, execute on next bar

        for i in range(strategy.warmup_periods, len(df)):
            current_data = df.iloc[: i + 1]
            current_bar = df.iloc[i]
            timestamp = df.index[i]
            price = current_bar["close"]

            # Check stop-loss / take-profit for open position
            if position is not None:
                exit_price, exit_reason = self._check_exits(position, current_bar)
                if exit_price is not None:
                    trade = self._close_position(position, exit_price, timestamp, exit_reason)
                    capital += trade.pnl - trade.fees
                    trades.append(trade)
                    position = None

            # Execute pending signal from previous bar at current bar's open (no look-ahead)
            if pending_signal is not None and position is None:
                open_price = current_bar["open"]
                entry_price = open_price * (1 + self.slippage if pending_signal.signal == Signal.BUY else 1 - self.slippage)
                size_usd = capital * self.position_size_pct * pending_signal.size_pct
                size = size_usd / entry_price

                position = {
                    "side": "LONG" if pending_signal.signal == Signal.BUY else "SHORT",
                    "entry_price": entry_price,
                    "entry_time": timestamp,
                    "size": size,
                    "size_usd": size_usd,
                    "stop_loss": pending_signal.stop_loss,
                    "take_profit": pending_signal.take_profit,
                }
                pending_signal = None

            # Generate signal (will be executed on NEXT bar's open)
            signal = strategy.generate_signal(current_data, symbol)
            pending_signal = signal if signal.is_actionable else None

            # Calculate equity
            unrealized_pnl = 0.0
            if position is not None:
                if position["side"] == "LONG":
                    unrealized_pnl = (price - position["entry_price"]) * position["size"]
                else:
                    unrealized_pnl = (position["entry_price"] - price) * position["size"]

            equity.append(capital + unrealized_pnl)

        # Close any remaining position at last price
        if position is not None:
            trade = self._close_position(position, df["close"].iloc[-1], df.index[-1], "end_of_data")
            capital += trade.pnl - trade.fees
            trades.append(trade)

        equity_series = pd.Series(equity, index=df.index[strategy.warmup_periods:])
        metrics = calculate_metrics(trades, equity_series, self.initial_capital)

        logger.info(f"Backtest complete: {len(trades)} trades, Sharpe={metrics.get('sharpe_ratio', 0):.2f}")

        return BacktestResult(
            strategy_name=strategy.name,
            symbol=symbol,
            timeframe=timeframe,
            start_date=df.index[strategy.warmup_periods],
            end_date=df.index[-1],
            trades=trades,
            equity_curve=equity_series,
            metrics=metrics,
        )

    def _check_exits(self, position: Dict, bar: pd.Series) -> tuple[Optional[float], str]:
        """Check if SL/TP hit on current bar."""
        high = bar["high"]
        low = bar["low"]

        if position["side"] == "LONG":
            if position.get("stop_loss") and low <= position["stop_loss"]:
                return position["stop_loss"], "stop_loss"
            if position.get("take_profit") and high >= position["take_profit"]:
                return position["take_profit"], "take_profit"
        else:  # SHORT
            if position.get("stop_loss") and high >= position["stop_loss"]:
                return position["stop_loss"], "stop_loss"
            if position.get("take_profit") and low <= position["take_profit"]:
                return position["take_profit"], "take_profit"

        return None, ""

    def _close_position(self, position: Dict, exit_price: float, exit_time: Any, reason: str) -> Trade:
        """Close position and create Trade record."""
        if position["side"] == "LONG":
            pnl = (exit_price - position["entry_price"]) * position["size"]
        else:
            pnl = (position["entry_price"] - exit_price) * position["size"]

        pnl_pct = pnl / position["size_usd"]
        fees = position["size_usd"] * self.fee_rate * 2  # Entry + exit fee

        return Trade(
            symbol="",
            side=position["side"],
            entry_price=position["entry_price"],
            exit_price=exit_price,
            entry_time=position["entry_time"],
            exit_time=exit_time,
            size=position["size"],
            pnl=pnl,
            pnl_pct=pnl_pct,
            fees=fees,
            exit_reason=reason,
        )
