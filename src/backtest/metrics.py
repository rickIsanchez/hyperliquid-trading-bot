"""
Backtest Performance Metrics

Calculates key trading metrics:
- Win Rate, Profit Factor
- Sharpe Ratio, Sortino Ratio
- Max Drawdown, Average Trade Duration
"""

from typing import List, Dict
import numpy as np
import pandas as pd


def calculate_metrics(
    trades: List,
    equity_curve: pd.Series,
    initial_capital: float,
) -> Dict[str, float]:
    """Calculate comprehensive trading metrics.

    Args:
        trades: List of Trade objects
        equity_curve: Equity curve as pd.Series
        initial_capital: Starting capital

    Returns:
        Dictionary of metric name -> value
    """
    if not trades:
        return {"total_trades": 0}

    pnls = [t.pnl for t in trades]
    pnl_pcts = [t.pnl_pct for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]

    # Basic metrics
    total_trades = len(trades)
    win_rate = len(wins) / total_trades if total_trades > 0 else 0
    total_pnl = sum(pnls)
    total_fees = sum(t.fees for t in trades)

    # Profit factor
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Average metrics
    avg_win = np.mean(wins) if wins else 0
    avg_loss = np.mean(losses) if losses else 0
    avg_pnl = np.mean(pnls)
    avg_pnl_pct = np.mean(pnl_pcts)

    # Expectancy
    expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

    # Max drawdown
    peak = equity_curve.expanding().max()
    drawdown = (equity_curve - peak) / peak
    max_drawdown = drawdown.min()
    max_drawdown_pct = abs(max_drawdown)

    # Sharpe ratio (annualized, assuming 15m candles)
    # ~35,040 fifteen-minute candles per year
    periods_per_year = 35040
    returns = equity_curve.pct_change().dropna()
    if len(returns) > 1 and returns.std() > 0:
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(periods_per_year)
    else:
        sharpe_ratio = 0.0

    # Sortino ratio
    downside_returns = returns[returns < 0]
    if len(downside_returns) > 1 and downside_returns.std() > 0:
        sortino_ratio = (returns.mean() / downside_returns.std()) * np.sqrt(periods_per_year)
    else:
        sortino_ratio = 0.0

    # Return
    total_return = (equity_curve.iloc[-1] - initial_capital) / initial_capital

    # Consecutive wins/losses
    max_consecutive_wins = _max_consecutive(pnls, positive=True)
    max_consecutive_losses = _max_consecutive(pnls, positive=False)

    # Exit reason breakdown
    exit_reasons = {}
    for t in trades:
        exit_reasons[t.exit_reason] = exit_reasons.get(t.exit_reason, 0) + 1

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 4),
        "total_pnl": round(total_pnl, 2),
        "total_fees": round(total_fees, 2),
        "net_pnl": round(total_pnl - total_fees, 2),
        "profit_factor": round(profit_factor, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "avg_pnl": round(avg_pnl, 2),
        "avg_pnl_pct": round(avg_pnl_pct, 4),
        "expectancy": round(expectancy, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 4),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "sortino_ratio": round(sortino_ratio, 2),
        "total_return": round(total_return, 4),
        "max_consecutive_wins": max_consecutive_wins,
        "max_consecutive_losses": max_consecutive_losses,
        "exit_reasons": exit_reasons,
    }


def _max_consecutive(pnls: List[float], positive: bool = True) -> int:
    """Count max consecutive wins or losses."""
    max_count = 0
    count = 0
    for pnl in pnls:
        if (positive and pnl > 0) or (not positive and pnl <= 0):
            count += 1
            max_count = max(max_count, count)
        else:
            count = 0
    return max_count
