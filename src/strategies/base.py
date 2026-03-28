"""
Abstract Base Strategy

All trading strategies must inherit from BaseStrategy and implement
the `generate_signal` method.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

import pandas as pd


class Signal(Enum):
    """Trading signal types."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradeSignal:
    """Structured trade signal with metadata."""
    signal: Signal
    symbol: str
    confidence: float  # 0.0 to 1.0
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    size_pct: float = 1.0  # % of max position size
    metadata: Optional[Dict[str, Any]] = None

    @property
    def is_actionable(self) -> bool:
        return self.signal != Signal.HOLD and self.confidence > 0.0


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies.

    Subclasses must implement:
        - name: Strategy identifier
        - generate_signal: Core signal logic
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._warmup_periods = 0

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique strategy identifier."""
        ...

    @property
    def warmup_periods(self) -> int:
        """Number of candles needed before strategy can generate signals."""
        return self._warmup_periods

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> TradeSignal:
        """Generate a trading signal from OHLCV data.

        Args:
            df: DataFrame with columns [open, high, low, close, volume]
                indexed by timestamp. Must have at least `warmup_periods` rows.
            symbol: Trading pair symbol (e.g., "BTC")

        Returns:
            TradeSignal with direction, confidence, and optional SL/TP levels.
        """
        ...

    def validate_data(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame has enough data for signal generation."""
        required_cols = {"open", "high", "low", "close", "volume"}
        if not required_cols.issubset(df.columns):
            return False
        if len(df) < self.warmup_periods:
            return False
        return True

    def __repr__(self) -> str:
        return f"<Strategy: {self.name}>"
