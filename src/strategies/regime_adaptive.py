"""
Regime-Adaptive Hybrid Strategy

Detects market regime (trending vs ranging) via ADX and adapts
signal generation accordingly:
- Trending: Uses EMA crossover + MACD confirmation
- Ranging: Uses RSI mean-reversion + Bollinger Band bounces
"""

from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal, TradeSignal


class RegimeAdaptiveStrategy(BaseStrategy):
    """Switches between trend-following and mean-reversion based on ADX."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.adx_period = self.config.get("adx_period", 14)
        self.adx_threshold = self.config.get("adx_threshold", 25)
        self.ema_fast = self.config.get("ema_fast", 9)
        self.ema_slow = self.config.get("ema_slow", 21)
        self.rsi_period = self.config.get("rsi_period", 14)
        self.rsi_oversold = self.config.get("rsi_oversold", 30)
        self.rsi_overbought = self.config.get("rsi_overbought", 70)
        self.bb_period = self.config.get("bb_period", 20)
        self.bb_std = self.config.get("bb_std", 2.0)
        self._warmup_periods = max(self.adx_period, self.ema_slow, self.bb_period) + 50

    @property
    def name(self) -> str:
        return "regime_adaptive_hybrid"

    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        if not self.validate_data(df):
            return TradeSignal(Signal.HOLD, symbol, 0.0, df["close"].iloc[-1])

        close = df["close"]
        high = df["high"]
        low = df["low"]

        # Calculate ADX for regime detection
        adx = self._calc_adx(high, low, close, self.adx_period)
        current_adx = adx.iloc[-1]

        if current_adx > self.adx_threshold:
            return self._trending_signal(df, symbol, current_adx)
        else:
            return self._ranging_signal(df, symbol, current_adx)

    def _trending_signal(self, df: pd.DataFrame, symbol: str, adx: float) -> TradeSignal:
        """EMA crossover + MACD confirmation for trending markets."""
        close = df["close"]
        ema_f = close.ewm(span=self.ema_fast).mean()
        ema_s = close.ewm(span=self.ema_slow).mean()

        # MACD
        macd_line = close.ewm(span=12).mean() - close.ewm(span=26).mean()
        signal_line = macd_line.ewm(span=9).mean()

        price = close.iloc[-1]
        ema_cross_up = ema_f.iloc[-1] > ema_s.iloc[-1] and ema_f.iloc[-2] <= ema_s.iloc[-2]
        ema_cross_down = ema_f.iloc[-1] < ema_s.iloc[-1] and ema_f.iloc[-2] >= ema_s.iloc[-2]
        macd_bullish = macd_line.iloc[-1] > signal_line.iloc[-1]
        macd_bearish = macd_line.iloc[-1] < signal_line.iloc[-1]

        confidence = min(adx / 50.0, 1.0)

        if ema_cross_up and macd_bullish:
            atr = self._calc_atr(df["high"], df["low"], close, 14).iloc[-1]
            return TradeSignal(
                Signal.BUY, symbol, confidence, price,
                stop_loss=price - 2 * atr,
                take_profit=price + 3 * atr,
                metadata={"regime": "trending", "adx": adx},
            )
        elif ema_cross_down and macd_bearish:
            atr = self._calc_atr(df["high"], df["low"], close, 14).iloc[-1]
            return TradeSignal(
                Signal.SELL, symbol, confidence, price,
                stop_loss=price + 2 * atr,
                take_profit=price - 3 * atr,
                metadata={"regime": "trending", "adx": adx},
            )

        return TradeSignal(Signal.HOLD, symbol, 0.0, price, metadata={"regime": "trending", "adx": adx})

    def _ranging_signal(self, df: pd.DataFrame, symbol: str, adx: float) -> TradeSignal:
        """RSI + Bollinger Band mean-reversion for ranging markets."""
        close = df["close"]
        price = close.iloc[-1]

        # RSI
        rsi = self._calc_rsi(close, self.rsi_period).iloc[-1]

        # Bollinger Bands
        sma = close.rolling(self.bb_period).mean()
        std = close.rolling(self.bb_period).std()
        upper = sma + self.bb_std * std
        lower = sma - self.bb_std * std

        confidence = 0.5 + (1 - adx / self.adx_threshold) * 0.5

        if rsi < self.rsi_oversold and price <= lower.iloc[-1]:
            return TradeSignal(
                Signal.BUY, symbol, confidence, price,
                stop_loss=lower.iloc[-1] - (upper.iloc[-1] - lower.iloc[-1]) * 0.2,
                take_profit=sma.iloc[-1],
                metadata={"regime": "ranging", "rsi": rsi, "adx": adx},
            )
        elif rsi > self.rsi_overbought and price >= upper.iloc[-1]:
            return TradeSignal(
                Signal.SELL, symbol, confidence, price,
                stop_loss=upper.iloc[-1] + (upper.iloc[-1] - lower.iloc[-1]) * 0.2,
                take_profit=sma.iloc[-1],
                metadata={"regime": "ranging", "rsi": rsi, "adx": adx},
            )

        return TradeSignal(Signal.HOLD, symbol, 0.0, price, metadata={"regime": "ranging", "rsi": rsi, "adx": adx})

    @staticmethod
    def _calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    @staticmethod
    def _calc_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ], axis=1).max(axis=1)

        atr = tr.ewm(span=period, min_periods=period).mean()
        plus_di = 100 * (plus_dm.ewm(span=period, min_periods=period).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(span=period, min_periods=period).mean() / atr)

        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.ewm(span=period, min_periods=period).mean()
        return adx
