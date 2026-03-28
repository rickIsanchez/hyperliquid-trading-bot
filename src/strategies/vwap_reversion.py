"""
VWAP Mean Reversion Strategy

Trades reversion to VWAP when price deviates significantly:
- BUY when price drops below VWAP - threshold (oversold)
- SELL when price rises above VWAP + threshold (overbought)
- Uses Williams %R for confirmation
"""

from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal, TradeSignal


class VWAPReversionStrategy(BaseStrategy):
    """Mean-reversion strategy based on VWAP deviation + Williams %R."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.vwap_deviation = self.config.get("vwap_deviation", 0.02)  # 2% from VWAP
        self.williams_period = self.config.get("williams_period", 14)
        self.williams_oversold = self.config.get("williams_oversold", -80)
        self.williams_overbought = self.config.get("williams_overbought", -20)
        self.atr_period = self.config.get("atr_period", 14)
        self._warmup_periods = max(self.williams_period, self.atr_period) + 20

    @property
    def name(self) -> str:
        return "vwap_mean_reversion"

    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        if not self.validate_data(df):
            return TradeSignal(Signal.HOLD, symbol, 0.0, df["close"].iloc[-1])

        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]
        price = close.iloc[-1]

        # VWAP (session-based, rolling)
        vwap = self._calc_vwap(df)
        current_vwap = vwap.iloc[-1]

        # Williams %R
        williams_r = self._calc_williams_r(high, low, close, self.williams_period)
        current_wr = williams_r.iloc[-1]

        # Deviation from VWAP
        deviation = (price - current_vwap) / current_vwap

        # ATR for SL/TP
        atr = self._calc_atr(high, low, close, self.atr_period).iloc[-1]

        # Signal logic
        if deviation < -self.vwap_deviation and current_wr < self.williams_oversold:
            confidence = min(abs(deviation) / (self.vwap_deviation * 2), 1.0)
            return TradeSignal(
                Signal.BUY, symbol, confidence, price,
                stop_loss=price - 1.5 * atr,
                take_profit=current_vwap,  # Target: reversion to VWAP
                metadata={
                    "vwap": current_vwap,
                    "deviation": deviation,
                    "williams_r": current_wr,
                },
            )
        elif deviation > self.vwap_deviation and current_wr > self.williams_overbought:
            confidence = min(abs(deviation) / (self.vwap_deviation * 2), 1.0)
            return TradeSignal(
                Signal.SELL, symbol, confidence, price,
                stop_loss=price + 1.5 * atr,
                take_profit=current_vwap,
                metadata={
                    "vwap": current_vwap,
                    "deviation": deviation,
                    "williams_r": current_wr,
                },
            )

        return TradeSignal(
            Signal.HOLD, symbol, 0.0, price,
            metadata={"vwap": current_vwap, "deviation": deviation, "williams_r": current_wr},
        )

    @staticmethod
    def _calc_vwap(df: pd.DataFrame) -> pd.Series:
        """Calculate rolling VWAP."""
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        cum_tp_vol = (typical_price * df["volume"]).cumsum()
        cum_vol = df["volume"].cumsum()
        return cum_tp_vol / cum_vol.replace(0, np.nan)

    @staticmethod
    def _calc_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Williams %R."""
        highest_high = high.rolling(period).max()
        lowest_low = low.rolling(period).min()
        wr = -100 * (highest_high - close) / (highest_high - lowest_low).replace(0, np.nan)
        return wr

    @staticmethod
    def _calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ], axis=1).max(axis=1)
        return tr.rolling(period).mean()
