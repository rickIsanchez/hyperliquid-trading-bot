# Backtest: RSI+MACD+Volume Triple

**Zeitraum:** 2019-03-30 – 2026-03-28 | **Timeframe:** 15m | **Assets:** BTC/USDT, ETH/USDT
**Parameter:** RSI(14) Cross 30/70, MACD(12,26,9) Hist ≷ 0, Volume > 1.5x MA20
**Trade-Setup:** SL 1.5%, TP 3.0%, Fee 0.045%, Trade Size 5% of Capital

## Ergebnisse

### BTC/USDT

| Metrik | Wert |
|---|---|
| Trades (7 Jahre) | 74 |
| Trades/Monat | 0.88 |
| Win Rate | 35.14% |
| Total Return | -0.17% |
| Profit Factor | 0.96 |
| Sharpe Ratio | -0.05 |
| Max Drawdown | -1.11% |
| Avg Win | $18.03 |
| Avg Loss | -$10.13 |

### ETH/USDT

| Metrik | Wert |
|---|---|
| Trades (7 Jahre) | 85 |
| Trades/Monat | 1.01 |
| Win Rate | 27.06% |
| Total Return | -2.23% |
| Profit Factor | 0.62 |
| Sharpe Ratio | -0.65 |
| Max Drawdown | -2.52% |
| Avg Win | $15.97 |
| Avg Loss | -$9.52 |

## Bewertung

### Zusammenfassung
Die RSI+MACD+Volume Triple Strategie ist auf 15m Timeframe über 7 Jahre **nicht profitabel**.

**Kernprobleme:**
- **Zu wenige Signals:** ~1 Trade/Monat — die Triple-Confirmation (RSI Cross + MACD Hist + Volume Spike) ist extrem restriktiv
- **Niedrige Win Rate:** 35% BTC, 27% ETH — das 2:1 TP/SL Ratio (3% vs 1.5%) reicht nicht aus um die niedrige Trefferquote zu kompensieren
- **Profit Factor < 1:** Beide Assets verlieren Geld (BTC: 0.96, ETH: 0.62)
- **Negativer Sharpe:** Kein risikoadjustierter Ertrag

**Positiv:**
- Max Drawdown sehr gering (-1.1% BTC, -2.5% ETH) — aber nur weil Trade Size bei 5% liegt und kaum getradet wird
- Kein katastrophaler Verlust

### Skalierbarkeit auf 300k€
❌ **Nicht empfohlen.** Bei 300k€ Kapital und 5% Trade Size (15k€/Trade) würde die Strategie ca. $520–$6,700 über 7 Jahre verlieren — plus Opportunity Cost.

### Eignung für HyperLiquid
❌ **Nicht geeignet** in dieser Form. Die Strategie generiert zu wenige Signale und hat eine zu niedrige Win Rate. Für HyperLiquid mit niedrigen Fees wäre eine Strategie mit höherer Frequenz und besserer Edge nötig.

### Mögliche Optimierungen
- RSI-Threshold lockern (z.B. 35/65 statt 30/70)
- Volume-Threshold senken (1.2x statt 1.5x)
- Kürzerer Timeframe (5m) für mehr Signale
- Trailing Stop statt fixem TP
- MACD-Histogram-Trend statt einfachem > 0
