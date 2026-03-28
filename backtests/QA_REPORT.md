# QA Report — Backtest Engine

**Date:** 2026-03-28
**Tester:** DevAimani QA Agent

## Data Loading
- Status: ✅
- Rows geladen: 35,040 (1 Jahr BTC/USDT 15m)
- Zeitraum: 2025-03-28 08:45 — 2026-03-28 08:30
- NaN-Werte: 0 in allen Spalten
- Issues: Keine. Binance CCXT Loader funktioniert korrekt mit Pagination und Rate-Limiting.

## Signal Generation
- Status: ✅
- RSI: ✅ korrekt (Range: 3.08 – 93.44, innerhalb 0–100)
- MACD: ✅ korrekt (Line, Signal, Histogram berechnet)
- VWAP: ✅ korrekt (Abweichung vom Close: 2.67% — cumulative Implementierung)
- ATR: ✅ korrekt (0.39% vom Preis — plausibel für 15m BTC)
- ADX: ✅ korrekt (Range: 9.99 – 78.85)
- Williams %R: ✅ korrekt (Range: -100 bis 0)
- Bollinger Bands: ✅ korrekt (upper ≥ middle ≥ lower)
- Issues: Keine. Alle Indikatoren im erwarteten Bereich.

## Look-Ahead-Bias Check
- Status: ✅ Kein Bias (nach Fix)
- Details:
  - **BUG GEFUNDEN (behoben):** Originaler Code generierte Signal auf Kerze[i] und eröffnete Trade auf Kerze[i]'s Close-Preis. Das ist Look-Ahead-Bias, da in Realzeit der Close erst nach Kerzenschluss bekannt ist.
  - **FIX:** Signal auf Kerze[i] wird als `pending_signal` gespeichert und erst auf Kerze[i+1]'s Open-Preis ausgeführt. Das ist realistisch: Signal bei Kerzenschluss → Order bei nächster Kerze.

## P&L Berechnung
- Status: ✅
- Details:
  - LONG P&L: `(exit_price - entry_price) * size` → korrekt
  - SHORT P&L: `(entry_price - exit_price) * size` → korrekt
  - Fees: `size_usd * fee_rate * 2` (Entry + Exit) → korrekt
  - P&L %: `pnl / size_usd` → korrekt relativ zum Positionswert
  - Net P&L in Metrics: `total_pnl - total_fees` → korrekt
  - SL/TP Check: Verwendet High/Low der aktuellen Kerze → korrekt (simuliert Intrabar-Execution)

## Metrics Berechnung
- Status: ✅ (nach Fix)
- **BUG GEFUNDEN (behoben):** `periods_per_year` war nur im Sharpe-`if`-Block definiert. Wenn Sharpe-Bedingung nicht erfüllt (std == 0), crasht Sortino mit `NameError`.
- **FIX:** `periods_per_year = 35040` vor den `if`-Block verschoben.
- Sharpe Ratio: Annualisiert mit √35040 → korrekt für 15m
- Sortino Ratio: Verwendet nur Downside-Returns → korrekt
- Max Drawdown: Peak-to-trough auf Equity Curve → korrekt

## Mini-Backtest Ergebnis (30 Tage BTC 15m)
- Win Rate: 50.0%
- Total Trades: 8
- Gross P&L: $1.51
- Net P&L (nach Fees): -$5.69
- Total Fees: $7.20
- Profit Factor: 1.04
- Sharpe: -0.97
- Sortino: -0.16
- Max Drawdown: 0.29%
- Avg Win: $9.34
- Avg Loss: -$8.97
- Exit Reasons: 4x Take Profit, 4x Stop Loss

**Bewertung:** Ergebnisse sind plausibel. Niedriges Handelsvolumen (8 Trades / 30 Tage) wegen strenger Triple-Confirmation. Leichter Netto-Verlust hauptsächlich durch Fees. Win Rate 50% mit leicht positivem Gross P&L zeigt, dass die Strategie nicht random handelt.

## Gefundene Bugs
1. **Look-Ahead-Bias in Engine (P0 — KRITISCH):** Signal und Trade-Eintritt auf gleicher Kerze am Close-Preis. Unrealistisch, da Close erst nach Kerzenschluss bekannt.
2. **Sortino NameError (P1):** `periods_per_year` nur im Sharpe-`if`-Block definiert → Crash wenn Sharpe-Bedingung nicht erfüllt.
3. **`--years` nur int (P2):** main.py erlaubte nur ganzzahlige Jahre, kein `--days` Parameter für kürzere Tests.
4. **`years` Type-Hint int statt float (P2):** data_loader akzeptierte formal nur int, obwohl float funktioniert.

## Fixes angewendet
1. **Engine: Next-bar execution** — Signal wird als `pending_signal` gespeichert, Ausführung auf nächster Kerze's Open-Preis (statt same-candle Close).
2. **Metrics: `periods_per_year` scope fix** — Variable vor `if`-Block definiert, sodass Sortino immer funktioniert.
3. **main.py: `--days` Flag hinzugefügt** — Erlaubt `--days 30` statt `--years 0.08`. `--years` jetzt float statt int.
4. **data_loader: `years` Type-Hint float** — Konsistent mit tatsächlicher Verwendung.

## Empfehlung
Bereit für 7-Jahres Backtest: ✅
Grund: Alle kritischen Bugs behoben. Daten laden korrekt (35k+ Candles/Jahr). Engine ist jetzt look-ahead-frei. Metriken berechnen sich korrekt. E2E-Test bestanden mit plausiblen Ergebnissen.
