# HyperLiquid API Research

> Recherche-Stand: 2026-03-28

## 1. Was ist HyperLiquid?

HyperLiquid ist eine **dezentrale Börse (DEX)** und eine eigene **Layer-1 Blockchain**, die speziell für High-Performance-Trading konzipiert wurde.

### Kernmerkmale:
- **Eigene L1 Chain** — Custom Consensus-Mechanismus (HyperBFT) für Sub-Sekunden-Finality
- **Keine Gas-Fees** — Trading, Order-Platzierung, -Änderung und -Stornierung kosten kein Gas
- **Fully On-Chain Order Book** — Transparenz einer DEX mit der Performance einer CEX
- **Perpetual Futures** — Hauptprodukt sind Perp-Kontrakte (bis zu 50x Leverage)
- **Spot Trading** — Seit 2024 auch Spot-Märkte verfügbar
- **HyperEVM** — EVM-kompatible Execution-Umgebung für DeFi-Anwendungen

### Architektur:
- **HyperCore** — Native Trading-Engine (Perps + Spot)
- **HyperEVM** — Für Smart Contracts und DeFi
- Beide teilen sich den gleichen State und die gleiche Liquidität

## 2. Verfügbare Assets

### Perpetuals:
- **Major Pairs:** BTC, ETH, SOL, DOGE, XRP, AVAX, MATIC, ARB, OP, LINK, etc.
- **Über 150+ Perp-Märkte** verfügbar
- Alle gegen USDC als Collateral

### Spot:
- Diverse Spot-Paare (PURR/USDC, etc.)
- Spot-Pairs zwischen Quote-Assets haben 80% niedrigere Taker-Fees

## 3. API Dokumentation

### Basis-URLs:
- **Mainnet:** `https://api.hyperliquid.xyz`
- **Testnet:** `https://api.hyperliquid-testnet.xyz`

### Endpoints:

#### Info Endpoint (Public, Read-Only)
`POST https://api.hyperliquid.xyz/info`

| Methode | Beschreibung |
|---------|-------------|
| `meta` | Exchange-Metadaten (Assets, szDecimals) |
| `spotMeta` | Spot-Markt Metadaten |
| `allMids` | Aktuelle Mid-Preise aller Assets |
| `l2Book` | L2 Order Book Snapshot |
| `candleSnapshot` | Historische OHLCV-Kerzen (max 5000 pro Request) |
| `userState` | User-Positionen & Margin-Summary |
| `spotUserState` | Spot-Balances eines Users |
| `openOrders` | Offene Orders eines Users |
| `userFills` | Letzte Trade-Fills eines Users |
| `userFillsByTime` | Fills nach Zeitraum (ms Timestamps) |
| `fundingHistory` | Funding-Rate History pro Asset |
| `orderStatus` | Status einer einzelnen Order (by OID oder CLOID) |

#### Exchange Endpoint (Authenticated, Signed)
`POST https://api.hyperliquid.xyz/exchange`

| Action | Beschreibung |
|--------|-------------|
| `order` | Einzelne Order platzieren |
| `bulkOrders` | Mehrere Orders atomar platzieren |
| `cancel` | Order stornieren (by OID) |
| `cancelByCloid` | Order stornieren (by Client Order ID) |
| `bulkCancel` | Mehrere Orders atomar stornieren |
| `modify` | Bestehende Order ändern |
| `updateLeverage` | Leverage für ein Asset setzen |
| `updateIsolatedMargin` | Isolated Margin anpassen |
| `usdTransfer` | USDC zwischen HL-Accounts transferieren |
| `spotTransfer` | Spot-Assets transferieren |
| `withdraw` | USDC über Bridge auf L1 abheben |
| `approveAgent` | API-Wallet (Agent) erstellen |

#### WebSocket
- **Subscriptions:** `l2Book`, `trades`, `candle`, `orderUpdates`, `userEvents`
- Echtzeit-Streams für Order Book, Trades und User-Events

## 4. Python SDK

### Offizielles SDK: `hyperliquid-python-sdk`
- **GitHub:** https://github.com/hyperliquid-dex/hyperliquid-python-sdk
- **Installation:** `pip install hyperliquid-python-sdk`

### Klassen:

#### `Info` (Read-Only)
```python
from hyperliquid.info import Info
from hyperliquid.utils import constants

info = Info(constants.MAINNET_API_URL)

# Methoden:
info.user_state(address)           # Positionen & Margin
info.spot_user_state(address)      # Spot Balances
info.open_orders(address)          # Offene Orders
info.all_mids()                    # Alle Mid-Preise
info.user_fills(address)           # Letzte Fills
info.user_fills_by_time(addr, start, end)  # Fills nach Zeit
info.meta()                        # Exchange Metadata
info.spot_meta()                   # Spot Metadata
info.funding_history(name, start, end)     # Funding History
info.l2_snapshot(name)             # Order Book
info.candles_snapshot(name, interval, start, end)  # OHLCV
info.query_order_by_oid(user, oid) # Order Status
```

#### `Exchange` (Authenticated Trading)
```python
import eth_account
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

wallet = eth_account.Account.from_key("0x...")
exchange = Exchange(wallet, constants.MAINNET_API_URL)

# Order Placement:
exchange.order(name, is_buy, sz, limit_px, order_type)
exchange.bulk_orders(order_requests)
exchange.market_open(name, is_buy, sz, px, slippage=0.05)
exchange.market_close(coin, sz, px, slippage=0.05)

# Order Management:
exchange.cancel(name, oid)
exchange.cancel_by_cloid(name, cloid)
exchange.bulk_cancel(cancel_requests)
exchange.modify_order(oid, name, is_buy, sz, limit_px, order_type)

# Account Management:
exchange.update_leverage(leverage, name, is_cross=True)
exchange.update_isolated_margin(amount, name)
exchange.usd_transfer(amount, destination)
exchange.withdraw_from_bridge(amount, destination)
exchange.approve_agent()
```

### Weitere SDKs:
- **CCXT Integration:** `ccxt` unterstützt HyperLiquid nativ — vereinfacht Migration von Binance
- **Rust SDK:** https://github.com/infinitefield/hypersdk
- **TypeScript:** https://github.com/nktkas/hyperliquid

## 5. Order-Typen

| Typ | Beschreibung | TIF-Optionen |
|-----|-------------|-------------|
| **Limit** | Preis-gebundene Order | GTC, IOC, ALO (Post-Only) |
| **Market** | Sofortige Ausführung (via `market_open`/`market_close`) | IOC mit Slippage |
| **Trigger (Stop)** | Stop-Loss / Take-Profit | `tp` (Take Profit), `sl` (Stop Loss) |
| **TP/SL Grouping** | TP/SL an Position gebunden | `normalTpsl`, `positionTpsl` |

### TIF (Time-in-Force):
- **GTC** — Good Til Canceled (Standard)
- **IOC** — Immediate Or Cancel (nicht gefüllter Teil wird storniert)
- **ALO** — Add Liquidity Only / Post-Only (wird storniert statt sofort zu matchen)

### Features:
- **Client Order ID (CLOID)** — Eigene 128-bit Hex-ID für Order-Tracking
- **Reduce Only** — Order kann nur Position verkleinern
- **Bulk Orders** — Mehrere Orders in einer atomaren Transaktion
- **Order Modification** — Bestehende Orders ändern ohne Cancel/Replace

## 6. Fees-Struktur

### Perps Fees (Base Rate, Tier 0):
| Rolle | Fee |
|-------|-----|
| **Taker** | 0.045% |
| **Maker** | 0.015% |

### Fee-Tiers (basierend auf 14-Tage Rolling Volume):
| Tier | Volume | Taker | Maker |
|------|--------|-------|-------|
| 0 | < $5M | 0.045% | 0.015% |
| 1 | > $5M | 0.040% | 0.012% |
| 2 | > $25M | 0.035% | 0.008% |
| 3 | > $100M | 0.030% | 0.004% |
| 4 | > $500M | 0.028% | 0.000% |
| 5 | > $2B | 0.026% | 0.000% |
| 6 | > $7B | 0.024% | 0.000% |

### Staking-Rabatte:
- **Diamond:** bis 40% Rabatt
- **Platinum:** bis 30%
- **Gold:** bis 20%
- **Silver:** bis 15%
- **Bronze:** bis 10%
- **Wood:** bis 5%

### Spot Fees (höher als Perps):
| Tier 0 | Taker | Maker |
|--------|-------|-------|
| Spot | 0.070% | 0.040% |

### Besonderheiten:
- **Keine Gas Fees** — nur Trading-Fees bei Ausführung
- Maker-Rebates werden direkt pro Trade ausgezahlt
- Sub-Accounts teilen sich den Fee-Tier des Master-Accounts
- Referral-Rewards für erste $1B Volume
- Referral-Discounts für erste $25M Volume

## 7. Margin-System

### Cross Margin (Standard):
- Gesamtes Account-Balance wird als Collateral für alle Positionen verwendet
- Liquidation basiert auf Gesamt-Account-Margin-Ratio
- Einfacher zu managen, höheres Risiko bei vielen Positionen

### Isolated Margin:
- Jede Position hat eigenes, festgelegtes Margin
- Verlust begrenzt auf zugewiesenes Margin
- Kann pro Position angepasst werden (`update_isolated_margin`)

### Leverage:
- **Bis zu 50x** auf Major-Assets (BTC, ETH)
- **Bis zu 20-30x** auf Altcoins
- Per-Asset konfigurierbar via `update_leverage(leverage, name, is_cross)`
- Wechsel zwischen Cross/Isolated jederzeit möglich

### Collateral:
- **USDC** als einziges Collateral (auf Arbitrum)
- Onboarding via Bridge von Arbitrum USDC

## 8. Historische Daten (für Backtests)

### Native API:
```python
info.candles_snapshot(name="BTC", interval="15m", startTime=ts_start, endTime=ts_end)
```
- **Limit:** Max 5000 Kerzen pro Request
- **Intervals:** 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 8h, 12h, 1d, 3d, 1w, 1M
- Pagination nötig für längere Zeiträume

### Archiv-Daten:
- **S3 Bucket:** `hyperliquid-archive` (Third-Party, monatlich aktualisiert)
- Enthält: Trades, Order Book Snapshots, Funding Rates

### Drittanbieter:
- **Dwellir:** Historische OHLCV, Tick-by-Tick Trades, Order Book Diffs
- **Chainstack:** candleSnapshot Endpoint
- **CCXT:** Unified `fetch_ohlcv()` für HyperLiquid

### Empfehlung für Backtests:
1. **Binance-Daten** via CCXT für historische Analyse (7+ Jahre verfügbar)
2. **HyperLiquid candles_snapshot** für aktuelle Marktdaten
3. **Dwellir** für detaillierte historische Daten

## 9. Vergleich: HyperLiquid vs Binance Perps

| Feature | HyperLiquid | Binance Perps |
|---------|-------------|---------------|
| **Typ** | DEX (On-Chain) | CEX (Centralized) |
| **KYC** | Nein | Ja (für volle Features) |
| **Custody** | Self-Custody (eigener Wallet) | Centralized (Binance hält Funds) |
| **Gas Fees** | Keine | N/A (keine Blockchain) |
| **Trading Fees (Taker)** | 0.045% | 0.045% |
| **Trading Fees (Maker)** | 0.015% | 0.02% |
| **Max Leverage** | Bis 50x | Bis 125x |
| **Order Book** | Fully On-Chain | Off-Chain |
| **Latency** | ~200ms | ~5-10ms |
| **Assets** | 150+ Perps | 300+ Perps |
| **Collateral** | USDC only | USDT/BUSD/Multi-Asset |
| **API Auth** | Ethereum Wallet Signierung | API Key/Secret |
| **Historische Daten** | Begrenzt (~2023+) | 7+ Jahre |
| **Testnet** | Ja (kostenlos) | Ja |
| **Open Source** | SDK Open Source | Proprietär |
| **Regulatory Risk** | Gering (DeFi) | Hoch (CeFi/Regulierung) |

### Vorteile HyperLiquid:
- ✅ Kein KYC, Self-Custody
- ✅ Keine Gas Fees
- ✅ Maker-Fees oft günstiger
- ✅ Transparentes On-Chain Order Book
- ✅ Geringeres Counterparty-Risk
- ✅ CCXT-kompatibel (einfache Migration)

### Nachteile HyperLiquid:
- ❌ Höhere Latenz als CEXs
- ❌ Weniger Assets als Binance
- ❌ Nur USDC als Collateral
- ❌ Weniger historische Daten verfügbar
- ❌ Geringerer Max-Leverage (50x vs 125x)
- ❌ Onboarding via Arbitrum Bridge nötig

## 10. Fazit & Empfehlung für Bot-Entwicklung

### Architektur-Empfehlung:
1. **Backtests** über Binance OHLCV-Daten (via CCXT) — mehr historische Tiefe
2. **Live Trading** über HyperLiquid Python SDK — native Integration
3. **CCXT als Fallback** — HyperLiquid wird von CCXT unterstützt
4. **Testnet zuerst** — Alle Strategien auf `api.hyperliquid-testnet.xyz` testen
5. **Agent-Wallet** — `approve_agent()` für API-Trading-Key statt Main-Wallet

### Nächste Schritte:
- [ ] Backtest-Engine mit Binance-Daten aufbauen
- [ ] HyperLiquid Client-Wrapper implementieren
- [ ] Strategien (Regime-Adaptive, RSI/MACD, VWAP) codieren
- [ ] Paper-Trading auf Testnet
- [ ] Live-Trading mit kleinem Kapital starten
