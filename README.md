# HyperLiquid Trading Bot

Algorithmic trading bot for [HyperLiquid](https://hyperliquid.xyz) — a decentralized perpetual futures exchange built on its own L1 blockchain.

## Features

- **3 Trading Strategies:**
  - **Regime-Adaptive Hybrid** — Switches between trend-following (EMA + MACD) and mean-reversion (RSI + Bollinger) based on ADX
  - **RSI + MACD + Volume Triple Confirmation** — Requires all three indicators to agree
  - **VWAP Mean Reversion** — Trades deviation from VWAP with Williams %R confirmation

- **Backtest Engine** — Test strategies on 7+ years of Binance data
- **Live Trading** — Real-time execution on HyperLiquid (mainnet or testnet)
- **HyperLiquid API Wrapper** — Simplified interface over the official Python SDK
- **Modular Architecture** — Easy to add new strategies and indicators

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run a backtest
python main.py backtest --symbol BTC/USDT --strategy regime_adaptive --years 3

# Run live trading (testnet)
cp config/config.example.json config/config.json
# Edit config.json with your private key
python main.py live --config config/config.json
```

## Project Structure

```
├── src/
│   ├── client/          # HyperLiquid API wrapper
│   ├── strategies/      # Trading strategies
│   ├── signals/         # Technical indicators
│   ├── backtest/        # Backtest engine + data loader
│   ├── live/            # Live trading daemon
│   └── utils/           # Logger, helpers
├── backtests/results/   # Backtest result reports
├── config/              # Configuration files
├── docs/                # API research & documentation
├── requirements.txt
└── main.py              # CLI entry point
```

## Configuration

Copy `config/config.example.json` to `config/config.json` and set:
- `hyperliquid.private_key` — Your wallet private key (use agent wallet for safety)
- `trading.symbols` — Assets to trade
- `trading.trade_size_usd` — Position size per trade
- `strategies` — Strategy assignment per symbol

## HyperLiquid API

See [docs/HYPERLIQUID_API.md](docs/HYPERLIQUID_API.md) for comprehensive API documentation.

Key points:
- **No KYC** — Self-custody, connect with ETH wallet
- **No gas fees** — Only trading fees (0.045% taker / 0.015% maker)
- **Testnet available** — `api.hyperliquid-testnet.xyz`
- **Official Python SDK:** `pip install hyperliquid-python-sdk`
- **CCXT support:** HyperLiquid is integrated in CCXT

## License

MIT
