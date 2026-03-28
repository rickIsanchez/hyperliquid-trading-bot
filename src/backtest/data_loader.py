"""
Data Loader for Backtesting

Loads OHLCV data from:
1. Binance (via CCXT) — 7+ years of historical data
2. HyperLiquid (via native API) — recent data
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import ccxt
import pandas as pd

logger = logging.getLogger(__name__)


def load_binance_ohlcv(
    symbol: str = "BTC/USDT",
    timeframe: str = "15m",
    years: int = 7,
    since: Optional[int] = None,
) -> pd.DataFrame:
    """Load historical OHLCV data from Binance.

    Args:
        symbol: Trading pair (e.g., "BTC/USDT", "ETH/USDT")
        timeframe: Candle interval (1m, 5m, 15m, 1h, 4h, 1d)
        years: How many years of history to fetch
        since: Start timestamp in ms (overrides years)

    Returns:
        DataFrame with columns [open, high, low, close, volume] indexed by timestamp
    """
    exchange = ccxt.binance({"enableRateLimit": True})

    if since is None:
        since = int((datetime.now() - timedelta(days=365 * years)).timestamp() * 1000)

    all_candles = []
    batch = 0

    logger.info(f"Loading {symbol} {timeframe} from Binance (since {datetime.fromtimestamp(since/1000)})")

    while True:
        try:
            candles = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        except ccxt.RateLimitExceeded:
            logger.warning("Rate limit hit, sleeping 10s...")
            time.sleep(10)
            continue
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            break

        if not candles:
            break

        all_candles.extend(candles)
        since = candles[-1][0] + 1
        batch += 1

        if batch % 50 == 0:
            logger.info(f"  Loaded {len(all_candles)} candles so far...")

        if len(candles) < 1000:
            break

        # Respect rate limits
        time.sleep(0.1)

    if not all_candles:
        logger.warning(f"No data returned for {symbol}")
        return pd.DataFrame()

    df = pd.DataFrame(all_candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("timestamp")
    df = df[~df.index.duplicated(keep="first")]

    logger.info(f"Loaded {len(df)} candles for {symbol} ({df.index[0]} to {df.index[-1]})")
    return df


def load_hyperliquid_candles(
    symbol: str = "BTC",
    interval: str = "15m",
    days: int = 30,
) -> pd.DataFrame:
    """Load candle data from HyperLiquid native API.

    Note: Max 5000 candles per request, pagination needed for longer periods.

    Args:
        symbol: Asset name (e.g., "BTC", "ETH")
        interval: Candle interval
        days: Number of days to fetch

    Returns:
        DataFrame with OHLCV data
    """
    from hyperliquid.info import Info
    from hyperliquid.utils import constants

    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

    all_candles = []
    current_start = start_time

    while current_start < end_time:
        try:
            candles = info.candles_snapshot(symbol, interval, current_start, end_time)
        except Exception as e:
            logger.error(f"Error fetching HL candles: {e}")
            break

        if not candles:
            break

        all_candles.extend(candles)

        # Move start forward
        last_ts = candles[-1].get("t", candles[-1].get("T", 0))
        if isinstance(last_ts, str):
            last_ts = int(last_ts)
        current_start = last_ts + 1

        if len(candles) < 5000:
            break

        time.sleep(0.2)

    if not all_candles:
        return pd.DataFrame()

    df = pd.DataFrame(all_candles)
    # Normalize column names
    rename_map = {"t": "timestamp", "T": "timestamp", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.set_index("timestamp")

    df = df[~df.index.duplicated(keep="first")]
    logger.info(f"Loaded {len(df)} HL candles for {symbol}")
    return df
