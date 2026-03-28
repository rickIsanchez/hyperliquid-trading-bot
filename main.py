#!/usr/bin/env python3
"""
HyperLiquid Trading Bot — Main Entry Point

Usage:
    python main.py backtest --symbol BTC/USDT --strategy regime_adaptive
    python main.py live --config config/config.json
"""

import argparse
import json
import logging
import sys

from src.utils.logger import setup_logger


def cmd_backtest(args):
    """Run a backtest."""
    from src.backtest import BacktestEngine, load_binance_ohlcv
    from src.strategies.regime_adaptive import RegimeAdaptiveStrategy
    from src.strategies.rsi_macd_volume import RSIMACDVolumeStrategy
    from src.strategies.vwap_reversion import VWAPReversionStrategy

    logger = logging.getLogger("backtest")

    strategies_map = {
        "regime_adaptive": RegimeAdaptiveStrategy,
        "rsi_macd_volume": RSIMACDVolumeStrategy,
        "vwap_reversion": VWAPReversionStrategy,
    }

    strategy_cls = strategies_map.get(args.strategy)
    if not strategy_cls:
        logger.error(f"Unknown strategy: {args.strategy}. Available: {list(strategies_map.keys())}")
        sys.exit(1)

    # Load data
    logger.info(f"Loading {args.symbol} {args.timeframe} data ({args.years}y)...")
    df = load_binance_ohlcv(args.symbol, args.timeframe, years=args.years)

    if df.empty:
        logger.error("No data loaded.")
        sys.exit(1)

    # Run backtest
    strategy = strategy_cls()
    engine = BacktestEngine(
        initial_capital=args.capital,
        fee_rate=0.00045,
    )
    result = engine.run(strategy, df, symbol=args.symbol.split("/")[0], timeframe=args.timeframe)

    # Print results
    print(f"\n{'='*60}")
    print(f"BACKTEST RESULTS: {result.strategy_name}")
    print(f"{'='*60}")
    print(f"Symbol:     {result.symbol}")
    print(f"Timeframe:  {result.timeframe}")
    print(f"Period:     {result.start_date} → {result.end_date}")
    print(f"{'─'*60}")
    for key, value in result.metrics.items():
        if key == "exit_reasons":
            print(f"  Exit Reasons: {value}")
        else:
            print(f"  {key:30s}: {value}")
    print(f"{'='*60}")

    # Save results
    if args.output:
        output_path = args.output
    else:
        output_path = f"backtests/results/{result.strategy_name}_{result.symbol}_{args.timeframe}.md"

    with open(output_path, "w") as f:
        f.write(f"# Backtest: {result.strategy_name}\n\n")
        f.write(f"- **Symbol:** {result.symbol}\n")
        f.write(f"- **Timeframe:** {result.timeframe}\n")
        f.write(f"- **Period:** {result.start_date} → {result.end_date}\n")
        f.write(f"- **Initial Capital:** ${args.capital:,.0f}\n\n")
        f.write("## Metrics\n\n")
        f.write("| Metric | Value |\n|--------|-------|\n")
        for key, value in result.metrics.items():
            if key != "exit_reasons":
                f.write(f"| {key} | {value} |\n")
        f.write(f"\n## Exit Reasons\n\n{result.metrics.get('exit_reasons', {})}\n")

    logger.info(f"Results saved to {output_path}")


def cmd_live(args):
    """Run live trading."""
    from src.client import HyperLiquidClient
    from src.live import LiveTrader
    from src.strategies.regime_adaptive import RegimeAdaptiveStrategy
    from src.strategies.rsi_macd_volume import RSIMACDVolumeStrategy
    from src.strategies.vwap_reversion import VWAPReversionStrategy

    logger = logging.getLogger("live")

    with open(args.config) as f:
        config = json.load(f)

    hl_config = config["hyperliquid"]
    client = HyperLiquidClient(
        private_key=hl_config["private_key"],
        testnet=hl_config.get("use_testnet", True),
    )

    strategies_map = {
        "regime_adaptive": RegimeAdaptiveStrategy,
        "rsi_macd_volume": RSIMACDVolumeStrategy,
        "vwap_reversion": VWAPReversionStrategy,
    }

    symbol_strategies = {}
    for symbol, strat_config in config.get("strategies", {}).items():
        cls = strategies_map.get(strat_config["name"])
        if cls:
            symbol_strategies[symbol] = cls(strat_config.get("params", {}))
        else:
            logger.warning(f"Unknown strategy {strat_config['name']} for {symbol}")

    trader = LiveTrader(client, symbol_strategies, config["trading"])
    trader.start()


def main():
    parser = argparse.ArgumentParser(description="HyperLiquid Trading Bot")
    subparsers = parser.add_subparsers(dest="command")

    # Backtest command
    bt = subparsers.add_parser("backtest", help="Run a backtest")
    bt.add_argument("--symbol", default="BTC/USDT", help="Trading pair")
    bt.add_argument("--strategy", default="regime_adaptive", help="Strategy name")
    bt.add_argument("--timeframe", default="15m", help="Candle timeframe")
    bt.add_argument("--years", type=int, default=7, help="Years of historical data")
    bt.add_argument("--capital", type=float, default=10000, help="Initial capital")
    bt.add_argument("--output", help="Output file path")

    # Live command
    lv = subparsers.add_parser("live", help="Run live trading")
    lv.add_argument("--config", default="config/config.json", help="Config file path")

    args = parser.parse_args()
    setup_logger(level="INFO")

    if args.command == "backtest":
        cmd_backtest(args)
    elif args.command == "live":
        cmd_live(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
