# Regime-Adaptive Hybrid Strategy — 7-Year Backtest

**Zeitraum:** 2019-03-30 → 2026-03-28 (7 Jahre)  
**Timeframe:** 15m  
**Initial Capital:** $10,000  
**Position Size:** 5% pro Trade  
**Fee:** 0.045% (Taker)  
**Regime-Erkennung:** ADX + Coefficient of Variation (CV-Proxy für Hurst)

---

## Ergebnisse

| Metrik | BTC/USDT | ETH/USDT |
|---|---|---|
| **Trades** | 5,828 | 6,418 |
| **Win Rate** | 46.41% | 45.23% |
| **Return** | -34.63% | -48.44% |
| **Final Capital** | $6,536.56 | $5,155.66 |
| **Profit Factor** | 0.77 | 0.73 |
| **Sharpe Ratio** | -2.04 | -2.71 |
| **Max Drawdown** | -34.64% | -48.42% |
| **Avg Win** | $4.27 | $4.53 |
| **Avg Loss** | -$4.81 | -$5.12 |
| **Trades/Monat** | 69.4 | 76.4 |

---

## Regime-Breakdown

| Regime | BTC Trades | BTC WR | ETH Trades | ETH WR |
|---|---|---|---|---|
| **Trend** | 923 | 42.36% | 1,041 | 40.83% |
| **Mean Reversion** | 4,905 | 47.18% | 5,377 | 46.09% |

---

## Exit Reasons

| Reason | BTC | ETH |
|---|---|---|
| **Take Profit** | 319 (5.5%) | 494 (7.7%) |
| **Stop Loss** | 1,174 (20.1%) | 1,769 (27.6%) |
| **Timeout** | 4,335 (74.4%) | 4,155 (64.7%) |

---

## Analyse & Probleme

### ❌ Strategie ist NICHT profitabel

1. **Zu viele Trades** — 70-76 Trades/Monat ist extrem hoch für 15m. Viele davon sind Noise-Trades.
2. **74% Timeout-Exits** — Die Signale führen nicht zu signifikanten Preisbewegungen innerhalb des Haltefensters.
3. **Win Rate < 50%** — Beide Regime-Modi performen unter 50%, Trend-Regime sogar nur ~41%.
4. **Negative Sharpe** — -2.04 (BTC) und -2.71 (ETH) zeigen konsistente Underperformance.
5. **Profit Factor < 1** — Verluste überwiegen Gewinne in beiden Assets.

### Mögliche Optimierungen

- **Strengere Signal-Filter:** Weniger, aber qualitativ bessere Entries (z.B. Multi-Timeframe Confirmation)
- **Regime-Schwellen anpassen:** ADX > 30 statt 25 für Trend, engere BB für MR
- **Größere TP/SL Ratios:** Aktuell 2:1 (Trend) und 1.67:1 (MR) — zu eng
- **Weniger Trades:** Max 1-2 Trades/Tag als Filter
- **Volume-Filter:** Nur bei überdurchschnittlichem Volume traden

---

## Bewertung

| Kriterium | Status |
|---|---|
| Win Rate > 55% | ❌ |
| Profit Factor > 1.3 | ❌ |
| Sharpe > 1.0 | ❌ |
| Max DD < 20% | ❌ |
| **HyperLiquid Ready** | **❌ NICHT BEREIT** |

> Die Regime-Adaptive Hybrid Strategie in ihrer aktuellen Konfiguration ist **nicht für Live-Trading geeignet**. Signifikante Parameter-Optimierung oder ein grundlegend anderer Ansatz ist erforderlich.

---

*Backtest durchgeführt am 2026-03-28 | Datenquelle: Binance via CCXT*
