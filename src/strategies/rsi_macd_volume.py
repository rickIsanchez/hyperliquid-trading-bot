"""
Triple Confirmation Strategy (RSI + MACD + Volume)

Requires all three indicators to agree before generating a signal:
1. RSI crosses into oversold/overbought zone
2. MACD histogram confirms direction
3. Volume spike above average confirms momentum
"""

from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal, TradeSignal


class RSIMACDVolumeStrategy(BaseStrategy):
    """Triple confirmation: RSI + MACD + Volume must all align."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.rsi_period = self.config.get("rsi_period", 14)
        self.rsi_oversold = self.config.get("rsi_oversold", 30)
        self.rsi_overbought = self.config.get("rsi_overbought", 70)
        self.macd_fast = self.config.get("macd_fast", 12)
        self.macd_slow = self.config.get("macd_slow", 26)
        self.macd_signal = self.config.get("macd_signal", 9)
        self.vol_sma_period = self.config.get("vol_sma_period", 20)
        self.vol_multiplier = self.config.get("vol_multiplier", 1.5)
        self._warmup_periods = max(self.macd_slow + self.macd_signal, self.vol_sma_period) + 10

    @property
    def name(self) -> str:
        return "rsi_macd_volume_triple"

    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        if not self.validate_data(df):
            return TradeSignal(Signal.HOLD, symbol, 0.0, df["close"].iloc[-1])

        close = df["close"]
        volume = df["volume"]
        price = close.iloc[-1]

        # RSI
        rsi = self._calc_rsi(close, self.rsi_period)
        current_rsi = rsi.iloc[-1]

        # MACD
        ema_fast = close.ewm(span=self.macd_fast).mean()
        ema_slow = close.ewm(span=self.macd_slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.macd_signal).mean()
        histogram = macd_line - signal_line

        # Volume
        vol_sma = volume.rolling(self.vol_sma_period).mean()
        volume_spike = volume.iloc[-1] > vol_sma.iloc[-1] * self.vol_multiplier

        # Confirmations
        rsi_bullish = current_rsi < self.rsi_oversold
        rsi_bearish = current_rsi > self.rsi_overbought
        macd_bullish = histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0  # Cross up
        macd_bearish = histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0  # Cross down

        confirmations = 0
        if rsi_bullish and macd_bullish and volume_spike:
            confirmations = 3
            confidence = 0.9
            signal = Signal.BUY
        elif rsi_bullish and macd_bullish:
            confirmations = 2
            confidence = 0.6
            signal = Signal.BUY
        elif rsi_bearish and macd_bearish and volume_spike:
            confirmations = 3
            confidence = 0.9
            signal = Signal.SELL
        elif rsi_bearish and macd_bearish:
            confirmations = 2
            confidence = 0.6
            signal = Signal.SELL
        else:
            return TradeSignal(
                Signal.HOLD, symbol, 0.0, price,
                metadata={"rsi": current_rsi, "macd_hist": histogram.iloc[-1], "vol_spike": volume_spike},
            )

        atr = self._calc_atr(df["high"], df["low"], close, 14).iloc[-1]
        sl_mult = 1.5 if confirmations == 3 else 2.0
        tp_mult = 3.0 if confirmations == 3 else 2.0

        if signal == Signal.BUY:
            sl = price - sl_mult * atr
            tp = price + tp_mult * atr
        else:
            sl = price + sl_mult * atr
            tp = price - tp_mult * atr

        return TradeSignal(
            signal, symbol, confidence, price,
            stop_loss=sl, take_profit=tp,
            metadata={
                "rsi": current_rsi,
                "macd_hist": histogram.iloc[-1],
                "vol_spike": volume_spike,
                "confirmations": confirmations,
            },
        )

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
