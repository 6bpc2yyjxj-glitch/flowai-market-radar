"""
FlowAI 市場雷達 PRO - Telegram Bot
Version: 2.0 (Arbitrage Edition)
新增：資金費率套利模組 + 跨所機會 + 清算地圖

GitHub: 6bpc2yyjxj-glitch/flowai-market-radar
Hosting: Railway
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import urllib3
urllib3.disable_warnings()

# ========== 配置 ==========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")

# 日誌設置
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== Grok API ==========
def call_grok(prompt, use_web_search=False):
    """調用 Grok API"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }
    
    tools = [{"type": "x_search"}]
    if use_web_search:
        tools.append({"type": "web_search"})
    
    data = {
        "model": "grok-4-1-fast",
        "input": prompt,
        "tools": tools
    }
    
    try:
        response = requests.post(
            "https://api.x.ai/v1/responses",
            headers=headers,
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'output' in result:
                for item in result['output']:
                    if item.get('type') == 'message':
                        for content in item.get('content', []):
                            if content.get('type') == 'output_text':
                                return content.get('text', '')
            return "無法解析回應"
        else:
            return f"API 錯誤: {response.status_code}"
    except Exception as e:
        logger.error(f"Grok API error: {e}")
        return f"連接錯誤: {str(e)}"

# ============================================================
# 🆕 模組：資金費率套利 (FUNDING RATE ARBITRAGE)
# ============================================================

def get_funding_rates():
    """獲取即時資金費率"""
    prompt = """Search web for current cryptocurrency funding rates across major exchanges.

Focus on:
- BTC, ETH, SOL perpetual funding rates on Binance, Bybit, OKX
- Current 8-hour funding rate
- Annualized APR calculation
- Historical comparison (is it high or low?)

Format in Chinese:

💰 資金費率雷達 (Funding Rate)
⏰ 更新時間：即時

📊 主流幣資金費率：

🔶 BTC 永續合約
├ Binance: [rate]% (年化 [APR]%)
├ Bybit: [rate]% (年化 [APR]%)
└ OKX: [rate]% (年化 [APR]%)
📈 趨勢：[多頭/空頭主導]

🔷 ETH 永續合約
├ Binance: [rate]%
├ Bybit: [rate]%
└ OKX: [rate]%

🟣 SOL 永續合約
├ Binance: [rate]%
├ Bybit: [rate]%
└ OKX: [rate]%

📉 市場狀態判斷：
- 正費率（多頭付空頭）= 市場偏多
- 負費率（空頭付多頭）= 市場偏空
- 極端費率 > 0.1% = 可能反轉信號

⚠️ 當前風險等級：[低/中/高]

💡 套利提示：
[根據費率給出套利建議]"""
    
    return call_grok(prompt, use_web_search=True)


def get_arbitrage_opportunities():
    """掃描套利機會"""
    prompt = """Search web for cryptocurrency arbitrage opportunities right now.

Find:
1. Funding rate arbitrage opportunities (positive funding > 0.03%)
2. Cross-exchange price differences > 0.5%
3. Basis spread opportunities (spot vs futures)
4. Any unusual funding rate spikes

For each opportunity, calculate:
- Estimated APR
- Required capital
- Risk level
- Specific execution steps

Format in Chinese:

🎯 套利機會掃描
⏰ 即時更新

═══════════════════════════════
📈 資金費率套利 (Delta-Neutral)
═══════════════════════════════

【機會 1】
幣種：[COIN]
當前費率：[rate]%/8hr
年化收益：[APR]%
執行方式：
├ 1. 現貨買入 $[amount]
├ 2. 永續做空等量
├ 3. 每8小時收取費率
└ 4. 預計日收益：$[daily]

風險等級：🟢低 / 🟡中 / 🔴高
注意事項：[specific risks]

═══════════════════════════════
🔄 跨所價差套利
═══════════════════════════════

[If any price differences > 0.5% between exchanges]
幣種：[COIN]
價差：[spread]%
買入所：[exchange] @ $[price]
賣出所：[exchange] @ $[price]
潛在利潤：[profit]%

═══════════════════════════════
📊 基差套利 (Basis Trading)
═══════════════════════════════

[If futures premium/discount is significant]
期貨溢價：[premium]%
到期日：[date]
年化收益：[APR]%

═══════════════════════════════
⚠️ 風險警告
═══════════════════════════════

1. 清算風險：槓桿過高可能爆倉
2. 費率翻轉：正費率可能變負
3. 交易所風險：資產託管風險
4. 流動性風險：大額進出滑點

💡 AI 建議：
[根據當前市場給出具體建議]"""
    
    return call_grok(prompt, use_web_search=True)


def get_arbitrage_calculator():
    """套利收益計算器說明"""
    return """📱 套利收益計算器

═══════════════════════════════
💰 資金費率套利公式
═══════════════════════════════

【基本計算】
每8小時收益 = 本金 × 資金費率
每日收益 = 本金 × 資金費率 × 3
年化收益 = 費率 × 3 × 365 × 100%

【範例】本金 $10,000
- 費率 0.01%/8hr
  - 每8小時：$1
  - 每日：$3
  - 年化：10.95%

- 費率 0.05%/8hr（牛市常見）
  - 每8小時：$5
  - 每日：$15
  - 年化：54.75%

- 費率 0.1%/8hr（極端行情）
  - 每8小時：$10
  - 每日：$30
  - 年化：109.5%

═══════════════════════════════
⚙️ 操作步驟
═══════════════════════════════

【開倉】Delta-Neutral 建立
1️⃣ 現貨買入 X 數量的幣
2️⃣ 永續合約做空 X 數量（1倍）
3️⃣ 確保合約帳戶保證金充足
4️⃣ 設置自動減倉保護

【持倉】收取費率
- 正費率：多頭付給你（做空方）
- 負費率：你付給多頭（虧損）
- 結算時間：00:00/08:00/16:00 UTC

【平倉】退出策略
- 費率持續下降時
- 費率轉負時
- 達到目標收益時

═══════════════════════════════
⚠️ 風險控制
═══════════════════════════════

🔴 必須注意：
1. 只用 1x 槓桿（現貨全額對沖）
2. 預留 20% 保證金緩衝
3. 監控清算價格
4. 分散到多個幣種

🟡 何時退出：
- 連續 3 個週期負費率
- 費率 < 0.005%（不划算）
- 市場劇烈波動時

═══════════════════════════════
📊 真實案例
═══════════════════════════════

【2025-01-30 崩盤日觀察】
- BTC 崩盤前費率：+0.51% (70% APR)
- 崩盤中：費率歸零/轉負
- 套利者狀態：安全（對沖保護）
- 唯一風險：極端波動時強平

💡 結論：套利策略在崩盤中
反而比純持倉更安全！

---
使用 /funding 查看即時費率
使用 /arb 掃描套利機會"""


def get_liquidation_map():
    """獲取清算地圖"""
    prompt = """Search web and X for current cryptocurrency liquidation data and heatmap.

Find:
1. Total liquidations in last 24 hours
2. Long vs Short liquidation ratio
3. Key liquidation levels for BTC
4. Largest single liquidation events
5. Exchange breakdown of liquidations

Format in Chinese:

🔥 清算地圖 (Liquidation Map)
⏰ 24小時數據

═══════════════════════════════
💥 爆倉總覽
═══════════════════════════════

總爆倉金額：$[amount]
├ 多單爆倉：$[long] ([%])
└ 空單爆倉：$[short] ([%])

爆倉人數：[number] 人
最大單筆：$[largest] ([exchange])

═══════════════════════════════
📊 交易所分布
═══════════════════════════════

1. [Exchange 1]: $[amount]
2. [Exchange 2]: $[amount]
3. [Exchange 3]: $[amount]

═══════════════════════════════
🎯 BTC 清算價位
═══════════════════════════════

⬆️ 上方清算區（空單）：
- $[price1]: ~$[amount] 待清算
- $[price2]: ~$[amount] 待清算

⬇️ 下方清算區（多單）：
- $[price1]: ~$[amount] 待清算
- $[price2]: ~$[amount] 待清算

═══════════════════════════════
📈 市場解讀
═══════════════════════════════

[哪方爆倉多說明什麼？]
[價格接近哪個清算區？]
[可能的連鎖反應？]

💡 交易提示：
[根據清算數據給出建議]

---
數據來源：CoinGlass, Coinalyze"""
    
    return call_grok(prompt, use_web_search=True)


def get_market_risk():
    """市場風險評估"""
    prompt = """Search web and X for current crypto market risk indicators.

Analyze:
1. Funding rates extremes
2. Open interest changes
3. Exchange reserves
4. Whale movements
5. Fear & Greed Index
6. Recent liquidation cascade potential

Format in Chinese:

⚠️ 市場風險評估
⏰ 即時更新

═══════════════════════════════
🎚️ 風險儀表板
═══════════════════════════════

整體風險等級：[🟢低/🟡中/🔴高/🔴🔴極高]

📊 指標分解：
├ 恐懼貪婪指數：[score] ([狀態])
├ 資金費率：[正常/偏高/極端]
├ 未平倉量：[增加/減少]%
├ 交易所餘額：[流入/流出]
└ 巨鯨動向：[買入/賣出/觀望]

═══════════════════════════════
🔮 潛在風險
═══════════════════════════════

1️⃣ [風險1]
   發生概率：[低/中/高]
   影響程度：[輕微/中等/嚴重]
   
2️⃣ [風險2]
   發生概率：[低/中/高]
   影響程度：[輕微/中等/嚴重]

═══════════════════════════════
🛡️ 套利者風險提示
═══════════════════════════════

當前適合套利：[是/否/謹慎]

理由：
- [原因1]
- [原因2]

建議倉位：[全倉/半倉/觀望]

💡 AI 建議：
[具體操作建議]"""
    
    return call_grok(prompt, use_web_search=True)


# ============================================================
# 原有模組（保留）
# ============================================================

def get_btc_sentiment():
    """BTC 情緒分析"""
    prompt = """Search X for Bitcoin sentiment in the last 2 hours.

Provide in Chinese:
1. Sentiment score (0-100)
2. Bullish or Bearish
3. Top 3 topics
4. 2 notable KOL posts
5. Key price levels
6. Risk warnings

Format:
📊 BTC 情緒雷達
⏰ 更新時間：[now]

🎯 情緒分數：[score]/100 ([方向])

🔥 熱門話題：
1. ...
2. ...
3. ...

👤 KOL 觀點：
- @xxx：...
- @yyy：...

📈 關鍵價位：支撐 $xxx / 阻力 $xxx

⚠️ 風險提示：...

💡 AI 建議：..."""
    return call_grok(prompt)


def get_meme_trending():
    """MEME 熱幣"""
    prompt = """Search X for hottest trending MEME coins in last 24 hours.

List top 5 in Chinese:
- Ticker symbol
- Why trending
- Price change if known
- Risk level (🔴極高/🟡中高/🟢中)

Format:
🔥 MEME 熱幣 TOP 5

1. $XXX ⭐⭐⭐
   └ 漲幅：...
   └ 原因：...
   └ 風險：🔴

⚠️ MEME 幣高風險，DYOR"""
    return call_grok(prompt)


def get_eth_sol():
    """ETH/SOL 情緒"""
    prompt = """Search X for Ethereum and Solana sentiment in last 2 hours.

Provide in Chinese for both:
- Sentiment score
- Main topics
- Notable KOL views

Format:
📊 ETH/SOL 情緒

🔷 ETH：[score]/100
├ 話題：...
└ KOL：...

🟣 SOL：[score]/100
├ 話題：...
└ KOL：...

📈 對比：..."""
    return call_grok(prompt)


def get_gold_sentiment():
    """黃金情緒"""
    prompt = """Search X and web for Gold XAUUSD sentiment.

Provide in Chinese:
1. Sentiment score
2. Key drivers (Fed, inflation, geopolitics)
3. Technical levels
4. Upcoming events

Format:
🥇 黃金避險雷達

🎯 情緒：[score]/100

📰 驅動因素：
- ...

📈 技術價位：
- 支撐：$xxx
- 阻力：$xxx

📅 近期關注：...

💡 AI 建議：..."""
    return call_grok(prompt, use_web_search=True)


def get_calendar():
    """經濟日曆"""
    prompt = """Search web for today's important economic calendar.

Focus on 3+ star events affecting XAUUSD:
- Fed, CPI, NFP, GDP, PMI

Format in Chinese with Taiwan time (UTC+8):

📅 今日經濟日曆

For each event:
⏰ [時間] | [事件]
⭐ 重要性：[stars]
📊 前值：... | 預期：...
💰 影響：...

💡 交易提示：..."""
    return call_grok(prompt, use_web_search=True)


def get_kol_alerts():
    """KOL 異動"""
    prompt = """Search X for recent posts from major crypto KOLs in last 1 hour.

Focus on: price predictions, buy/sell calls, warnings

Format in Chinese:

⚡ KOL 異動警報

For each significant post:
👤 @handle
🕐 [time]
📝 內容：...
📊 情緒：看多/看空
⚠️ 影響：高/中/低"""
    return call_grok(prompt)


def get_full_radar():
    """全景報告"""
    prompt = """Create comprehensive market report by searching X and web.

Include:
1. Overall crypto sentiment
2. BTC/ETH/SOL summary
3. Top MEME coin
4. Gold outlook
5. Key risks

Format in Chinese:

🌐 FlowAI 市場雷達

📊 加密市場：[fear/greed]

🔶 主流幣：
- BTC: ...
- ETH: ...
- SOL: ...

🔥 熱幣：$XXX - ...

🥇 黃金：...

⚠️ 風險：...

💡 建議：...

---
FlowAI 市場雷達 PRO"""
    return call_grok(prompt, use_web_search=True)


# ============================================================
# Telegram 命令處理
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """開始命令"""
    await update.message.reply_text("""🎯 FlowAI 市場雷達 PRO v2.0
━━━━━━━━━━━━━━━━━━━━━

📊 情緒分析：
/btc - BTC 即時情緒
/meme - MEME 熱幣 TOP 5
/ethsol - ETH/SOL 情緒

🥇 外匯黃金：
/gold - 黃金避險雷達
/calendar - 經濟日曆

💰 【新】套利模組：
/funding - 💰 即時資金費率
/arb - 🎯 套利機會掃描
/arbcalc - 📱 套利計算教學
/liq - 🔥 清算地圖
/risk - ⚠️ 市場風險評估

⚡ 綜合：
/radar - 全景市場報告
/kol - KOL 異動警報

💡 每個命令需要 10-60 秒處理

━━━━━━━━━━━━━━━━━━━━━
FlowAI - 讓你比市場快一步
套利版 v2.0""")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


# === 套利模組命令 ===
async def funding_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """資金費率"""
    await update.message.reply_text("💰 正在獲取即時資金費率...")
    result = get_funding_rates()
    await update.message.reply_text(result)


async def arb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """套利機會"""
    await update.message.reply_text("🎯 正在掃描套利機會...")
    result = get_arbitrage_opportunities()
    await update.message.reply_text(result)


async def arbcalc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """套利計算器"""
    result = get_arbitrage_calculator()
    await update.message.reply_text(result)


async def liq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """清算地圖"""
    await update.message.reply_text("🔥 正在獲取清算數據...")
    result = get_liquidation_map()
    await update.message.reply_text(result)


async def risk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """風險評估"""
    await update.message.reply_text("⚠️ 正在評估市場風險...")
    result = get_market_risk()
    await update.message.reply_text(result)


# === 原有命令 ===
async def btc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 正在分析 BTC 情緒...")
    result = get_btc_sentiment()
    await update.message.reply_text(result)


async def meme_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 正在搜尋熱門 MEME...")
    result = get_meme_trending()
    await update.message.reply_text(result)


async def ethsol_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 正在分析 ETH/SOL...")
    result = get_eth_sol()
    await update.message.reply_text(result)


async def gold_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 正在分析黃金情緒...")
    result = get_gold_sentiment()
    await update.message.reply_text(result)


async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 正在獲取經濟日曆...")
    result = get_calendar()
    await update.message.reply_text(result)


async def kol_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 正在監控 KOL...")
    result = get_kol_alerts()
    await update.message.reply_text(result)


async def radar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 正在生成全景報告...")
    result = get_full_radar()
    await update.message.reply_text(result)


# ============================================================
# 主程式
# ============================================================

def main():
    """啟動 Bot"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN not set!")
        return
    if not GROK_API_KEY:
        logger.error("GROK_API_KEY not set!")
        return
    
    # 創建 Application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # 基礎命令
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # 套利模組命令（新增）
    app.add_handler(CommandHandler("funding", funding_command))
    app.add_handler(CommandHandler("arb", arb_command))
    app.add_handler(CommandHandler("arbcalc", arbcalc_command))
    app.add_handler(CommandHandler("liq", liq_command))
    app.add_handler(CommandHandler("risk", risk_command))
    
    # 原有命令
    app.add_handler(CommandHandler("btc", btc_command))
    app.add_handler(CommandHandler("meme", meme_command))
    app.add_handler(CommandHandler("ethsol", ethsol_command))
    app.add_handler(CommandHandler("gold", gold_command))
    app.add_handler(CommandHandler("calendar", calendar_command))
    app.add_handler(CommandHandler("kol", kol_command))
    app.add_handler(CommandHandler("radar", radar_command))
    
    # 啟動
    logger.info("FlowAI Bot v2.0 (Arbitrage Edition) 啟動中...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
