# FlowAI Trading System

> AI-Powered Multi-Dimensional Market Analysis Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://t.me/FlowAI_TradeBot)

## 🎯 Overview

FlowAI is an intelligent trading system that combines **price action analysis**, **order flow verification**, and **AI-driven market sentiment** to generate high-probability trading signals for cryptocurrency perpetual contracts.

### Core Philosophy: Four-Dimensional Battlefield (四維戰場)

|Dimension|Name       |Analysis Focus                           |
|---------|-----------|-----------------------------------------|
|1st      |**K-Bar**  |Single candlestick emotion expression    |
|2nd      |**Pattern**|Multi-candle story (W-bottom, M-top, ABC)|
|3rd      |**Space**  |Key levels (Support/Resistance/Fibonacci)|
|4th      |**Time**   |Multi-timeframe confluence (D1+H1+M15)   |
|5th      |**Flow**   |Order flow verification (NEW)            |

## 🔧 Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FlowAI Trading Engine                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Data Layer  │  │  Decision   │  │  Execution  │         │
│  │             │  │   Layer     │  │   Layer     │         │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤         │
│  │ Bybit WS    │→ │ 4D Analysis │→ │ Auto Order  │         │
│  │ Order Book  │  │ KD Filter   │  │ Stop Loss   │         │
│  │ Liquidation │  │ Order Flow  │  │ Take Profit │         │
│  │ Trade Stream│  │ Risk Check  │  │ Position    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Trading Strategy

### Entry Conditions (10-Point Checklist)

```
□ 1. Key Level Marked (Support/Resistance/Trendline)
□ 2. Structure Confirmed (Uptrend/Downtrend/Consolidation)
□ 3. Pattern Identified (Reversal/Continuation/None)
□ 4. Multi-Timeframe Confluence (Direction aligned)
□ 5. Price at Key Level
□ 6. Candlestick Confirmation Signal
□ 7. Risk-Reward Ratio ≥ 2.5
□ 8. Position Size Calculated (Risk ≤ 2%)
□ 9. Stop Loss & Take Profit Set
□ 10. Worst-Case Scenario Planned

Pass ≥ 7/10 → Execute Trade
```

### KD Oscillator Filter

|Condition |Value      |Interpretation                      |
|----------|-----------|------------------------------------|
|Overbought|K > 80     |Potential reversal zone (Short bias)|
|Oversold  |K < 20     |Potential reversal zone (Long bias) |
|Neutral   |20 < K < 80|Wait for extreme values             |

### Entry Patterns

|Pattern     |Code Name       |Market Emotion      |Entry Point     |
|------------|----------------|--------------------|----------------|
|W-Bottom    |Double Slingshot|Higher low → Bullish|Neckline break  |
|M-Top       |Double Ceiling  |Lower high → Bearish|Neckline break  |
|ABC Pullback|Slingshot Tactic|Trend continuation  |C-point reversal|
|Box Breakout|Cage Break      |Consolidation end   |Boundary break  |

## 🔄 Order Flow Integration (V2.0)

### Bybit V5 API Data Sources

|Data Type   |Endpoint                 |Update Frequency|Purpose                      |
|------------|-------------------------|----------------|-----------------------------|
|Order Book  |`/v5/market/orderbook`   |200ms           |Large order detection        |
|Liquidations|`allLiquidation.{symbol}`|500ms           |Reversal point identification|
|Trade Stream|`publicTrade.{symbol}`   |Real-time       |CVD calculation              |

### Order Flow Verification Logic

```python
def verify_with_orderflow(signal, orderbook, liquidations, trades):
    """
    Verify trading signal with order flow data
    Returns: confidence_boost (0.0 to 0.2)
    """
    score = 0.0
    
    # 1. Order Book Imbalance
    bid_volume = sum(orderbook['bids'][:50])
    ask_volume = sum(orderbook['asks'][:50])
    imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
    
    if signal == 'LONG' and imbalance > 0.15:
        score += 0.07  # Strong bid support
    elif signal == 'SHORT' and imbalance < -0.15:
        score += 0.07  # Strong ask pressure
    
    # 2. Liquidation Cluster
    recent_liq = get_recent_liquidations(liquidations, minutes=5)
    if signal == 'LONG' and recent_liq['short_liquidated'] > threshold:
        score += 0.07  # Short squeeze potential
    elif signal == 'SHORT' and recent_liq['long_liquidated'] > threshold:
        score += 0.07  # Long capitulation
    
    # 3. CVD Confirmation
    cvd_trend = calculate_cvd_trend(trades, periods=20)
    if signal == 'LONG' and cvd_trend > 0:
        score += 0.06  # Buying pressure
    elif signal == 'SHORT' and cvd_trend < 0:
        score += 0.06  # Selling pressure
    
    return score
```

## 📈 Expected Performance

|Metric        |Target |Notes                       |
|--------------|-------|----------------------------|
|Win Rate      |60-70% |With Order Flow verification|
|Profit Factor |1.5-2.0|Win > Loss                  |
|Max Drawdown  |< 15%  |Risk management priority    |
|Trades/Day    |10-20  |Competition minimum: 10     |
|Risk per Trade|1-2%   |Capital preservation        |

## 🚀 Competition Configuration

### Bybit AI vs Human Competition Settings

```yaml
competition:
  initial_capital: 1000 USDT
  max_leverage: 10x  # Conservative (Bybit recommends ≤15x)
  trading_pairs:
    - BTCUSDT
    - ETHUSDT
  
risk_management:
  max_position_size: 20%  # Per trade
  daily_loss_limit: 5%
  trailing_stop: enabled
  
execution:
  order_type: limit  # Reduce slippage
  min_trades_per_day: 10
  max_trades_per_day: 50
```

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Framework**: asyncio + aiohttp
- **Exchange API**: Bybit V5 (REST + WebSocket)
- **Data Processing**: pandas, numpy
- **Telegram Integration**: python-telegram-bot
- **Deployment**: Railway

## 📁 Project Structure

```
flowai-trading-bot/
├── src/
│   ├── core/
│   │   ├── engine.py          # Main trading engine
│   │   ├── strategy.py        # 4D analysis + KD filter
│   │   └── risk_manager.py    # Position sizing & risk
│   ├── data/
│   │   ├── bybit_client.py    # Bybit V5 API wrapper
│   │   ├── orderbook.py       # Order book analysis
│   │   ├── liquidations.py    # Liquidation tracking
│   │   └── cvd.py             # CVD calculation
│   ├── execution/
│   │   ├── order_manager.py   # Order placement
│   │   └── position_tracker.py
│   └── telegram/
│       └── bot.py             # TG notifications
├── config/
│   └── settings.yaml
├── tests/
├── requirements.txt
└── README.md
```

## 🔐 Risk Disclosure

```
⚠️ IMPORTANT RISK WARNING

1. Past performance ≠ Future results
2. Live trading involves slippage, latency, and psychological factors
3. Market conditions change; strategies require periodic adjustment
4. Never trade with money you cannot afford to lose
5. Single trade risk controlled at 1-2% is critical
```

## 👥 Team: FlowAI

|Role       |Description                                    |
|-----------|-----------------------------------------------|
|Founder    |10+ years trading experience, systematic trader|
|AI Partner |Claude (Strategy analysis & code generation)   |
|Data Source|Grok API (Market sentiment)                    |

## 📞 Contact

- **Telegram Bot**: [@FlowAI_TradeBot](https://t.me/FlowAI_TradeBot)
- **X (Twitter)**: [@FlowAI_Trade](https://x.com/FlowAI_Trade)
- **GitHub**: [flowai-market-radar](https://github.com/6bpc2yyjxj-glitch/flowai-market-radar)

-----

## License

MIT License - See <LICENSE> for details.

-----

*“Read market emotion, flow with the trend”*
*— FlowAI*
