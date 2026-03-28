# VWAP Mean Reversion — 7-Jahres Backtest

**Datum:** 2026-03-28
**Timeframe:** 15m | **Periode:** 7 Jahre (2019–2026)
**Strategie:** Rolling VWAP (96 Candles = 1 Tag) mit ±1.5σ Bands, RSI-Filter
**Kapital:** $10,000 | **Position Size:** 5% | **Fee:** 0.045%

---

## Ergebnisse

| Metrik | BTC/USDT | ETH/USDT |
|---|---|---|
| **Trades** | 4,762 | 4,805 |
| **Win Rate** | 52.94% | 51.80% |
| **Total PnL** | -$3,019 | -$4,095 |
| **Return** | -30.19% | -40.95% |
| **Avg Win** | $3.68 | $4.26 |
| **Avg Loss** | -$5.49 | -$6.34 |
| **Profit Factor** | 0.75 | 0.72 |
| **Sharpe Ratio** | -2.20 | -2.60 |
| **Max Drawdown** | -30.34% | -41.11% |
| **Trades/Monat** | 56.7 | 57.2 |

## Exit Reasons

| Reason | BTC | ETH |
|---|---|---|
| Take Profit (VWAP revert) | 1,744 (36.6%) | 1,594 (33.2%) |
| Stop Loss (-2%) | 788 (16.5%) | 1,132 (23.6%) |
| Timeout (6h) | 2,230 (46.8%) | 2,079 (43.3%) |

## Analyse

### Warum die Strategie verliert

1. **Asymmetrisches Risiko:** Avg Loss ($5.49/$6.34) deutlich größer als Avg Win ($3.68/$4.26) — trotz >50% Win Rate reicht das nicht
2. **Zu viele Timeouts (43-47%):** Fast die Hälfte der Trades erreicht weder TP noch SL innerhalb von 6h — Signal zu schwach für schnelle Reversion
3. **Profit Factor < 1.0:** Beides unter 0.75 — konsistenter Kapitalverlust
4. **Negativer Sharpe:** -2.2 / -2.6 — stark risikoadjustiert negativ
5. **Hohe Frequenz:** ~57 Trades/Monat generieren massiv Fees ohne Edge

### Mögliche Optimierungen

- **Engerer SL** (z.B. -1%) oder **weiterere Entry** (2.0σ statt 1.5σ)
- **Längerer Timeout** oder **Trailing TP** statt fixem VWAP-Revert
- **Volumen-Filter:** Nur bei überdurchschnittlichem Volumen traden
- **Trend-Filter verstärken:** EMA200 als zusätzlichen Richtungsfilter
- **Niedrigere Frequenz:** Weniger Trades = weniger Fee-Drag

## Bewertung

| Kriterium | Status |
|---|---|
| Profitabel | ❌ |
| Sharpe > 1.0 | ❌ |
| Max DD < 15% | ❌ |
| Profit Factor > 1.5 | ❌ |
| **HyperLiquid Ready** | **❌ Nicht empfohlen** |

> **Fazit:** VWAP Mean Reversion mit diesen Parametern ist über 7 Jahre konsistent unprofitabel. Die Win Rate >50% täuscht — das Risk/Reward-Verhältnis ist negativ. Strategie benötigt fundamentale Überarbeitung vor Live-Einsatz.
