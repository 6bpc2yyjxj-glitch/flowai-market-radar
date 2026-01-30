"""
FlowAI 市場雷達 PRO - Telegram Bot
Version: 2.0 (完整版)
Commands: /start, /btc, /meme, /gold, /radar, /calendar, /kol, /ethsol
"""

import os
import json
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import urllib3
urllib3.disable_warnings()

# ========== 日誌設定 ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== 配置 ==========
GROK_API_KEY = os.environ.get("GROK_API_KEY", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")

# ========== Grok API 調用 ==========
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
            timeout=120,
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'output' in result:
                for item in result['output']:
                    if item.get('type') == 'message':
                        for content in item.get('content', []):
                            if content.get('type') == 'output_text':
                                return content.get('text', '')
            return "⚠️ 無法解析回應"
        else:
            logger.error(f"API Error: {response.status_code}")
            return f"⚠️ API 錯誤: {response.status_code}"
    except Exception as e:
        logger.error(f"Exception: {e}")
        return f"⚠️ 連線錯誤，請稍後再試"

# ========== 命令處理器 ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """歡迎訊息"""
    welcome = """🎯 FlowAI 市場雷達 PRO

📋 可用命令：

/btc - 📊 BTC 即時情緒分析
/meme - 🔥 MEME 熱幣 TOP 5
/gold - 🥇 黃金避險雷達
/calendar - 📅 今日經濟日曆
/kol - ⚡ KOL 異動警報
/ethsol - 🔷 ETH/SOL 情緒對比
/radar - 🌐 全景市場報告

💡 提示：每個命令需要 10-30 秒處理

---
FlowAI 市場雷達 - 讓你比市場快一步
"""
    await update.message.reply_text(welcome)

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """BTC 情緒分析"""
    await update.message.reply_text("📊 正在分析 BTC 情緒，請稍候...")
    
    prompt = """Search X for Bitcoin sentiment in the last 2 hours.

Analyze and provide in Chinese:
1. Overall sentiment score (0-100)
2. Bullish or Bearish?
3. Top 3 topics being discussed
4. 2 notable KOL posts
5. Key price levels

Format:
📊 BTC 情緒雷達
⏰ 更新時間：[now]

🎯 情緒分數：[score]/100 ([方向])

🔥 熱門話題：
1. ...
2. ...
3. ...

👤 KOL 觀點：
• @xxx：...
• @yyy：...

📈 關鍵價位：
• 支撐：$xxx
• 阻力：$xxx

💡 AI 建議：
[一句話建議]"""
    
    result = call_grok(prompt)
    await update.message.reply_text(result)

async def meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """MEME 熱幣"""
    await update.message.reply_text("🔥 正在搜尋熱門 MEME 幣...")
    
    prompt = """Search X for hottest MEME coins in last 24 hours.

Find Top 5 trending MEME coins. For each:
- Ticker symbol
- Why trending
- Risk level

Format in Chinese:
🔥 MEME 熱幣 TOP 5

1. $[TICKER] ⭐⭐⭐
   └ 熱度原因：...
   └ 風險：🔴極高/🟡中高

2. ...

⚠️ 警告：MEME 幣高風險，DYOR"""
    
    result = call_grok(prompt)
    await update.message.reply_text(result)

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """黃金情緒"""
    await update.message.reply_text("🥇 正在分析黃金市場...")
    
    prompt = """Search X and web for Gold (XAUUSD) sentiment.

Provide in Chinese:
1. Safe-haven index (0-100)
2. Key drivers (Fed, geopolitics, inflation)
3. Technical levels
4. Upcoming events

Format:
🥇 黃金避險雷達

🎯 避險指數：[score]/100

📰 驅動因素：
• [factor 1]
• [factor 2]

📈 技術價位：
• 支撐：$[level]
• 阻力：$[level]

📅 近期關注：
[upcoming events]

💡 AI 解讀：
[outlook]"""
    
    result = call_grok(prompt, use_web_search=True)
    await update.message.reply_text(result)

async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """經濟日曆"""
    await update.message.reply_text("📅 正在獲取今日經濟數據...")
    
    prompt = """Search web for today's important economic calendar events.

Focus on:
- US data (CPI, NFP, GDP, PMI, Jobless Claims)
- Fed speeches, FOMC
- High-impact events (3+ stars)

Format in Chinese with Taiwan time (UTC+8):

📅 今日經濟日曆

For each event:
⏰ [Taiwan time] | [Event]
⭐ 重要性：[1-5 stars]
📊 前值：[prev] | 預期：[forecast]
💰 影響：[assets affected]

If no major events today, show next 2-3 important ones.

💡 交易提示：
[when to be cautious]"""
    
    result = call_grok(prompt, use_web_search=True)
    await update.message.reply_text(result)

async def kol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """KOL 異動"""
    await update.message.reply_text("⚡ 正在追蹤 KOL 動態...")
    
    prompt = """Search X for recent posts from crypto KOLs in last 2 hours.

Track: @elonmusk, @caborehbot, @WuBlockchain, @lookonchain, @CryptoKaleo, @AshCrypto, @VitalikButerin

Find posts about:
- Price predictions
- Buy/sell calls
- Major news
- Warnings

Format in Chinese:
⚡ KOL 異動警報

For each significant post:
👤 @[handle]
🕐 [time ago]
📝 摘要：[summary]
📊 情緒：[看多/看空/中性]
🎯 提及：[coins/assets]

If nothing significant, say "過去2小時無重大 KOL 異動"

💡 觀察：[brief commentary]"""
    
    result = call_grok(prompt)
    await update.message.reply_text(result)

async def ethsol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ETH/SOL 對比"""
    await update.message.reply_text("🔷 正在對比 ETH 和 SOL...")
    
    prompt = """Search X for Ethereum and Solana sentiment.

For BOTH ETH and SOL:
1. Sentiment score (0-100)
2. Main topics
3. Ecosystem updates

Format in Chinese:
📊 ETH/SOL 情緒對比

🔷 Ethereum (ETH)
├ 情緒：[score]/100
├ 話題：...
└ 動態：...

🟣 Solana (SOL)
├ 情緒：[score]/100
├ 話題：...
└ 動態：...

🆚 對比結論：
[which looks stronger]"""
    
    result = call_grok(prompt)
    await update.message.reply_text(result)

async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """全景報告"""
    await update.message.reply_text("🌐 正在生成全景報告...")
    
    prompt = """Create a brief market report searching X and web.

Include:
1. Crypto market sentiment (fear/greed)
2. BTC/ETH/SOL one-liner each
3. Top MEME coin
4. Gold outlook
5. Key risk

Format in Chinese:
🌐 FlowAI 市場雷達

📊 市場情緒：[Fear/Greed + score]

🔶 主流幣：
• BTC: [trend]
• ETH: [trend]
• SOL: [trend]

🔥 熱幣：$[TICKER] - [why]

🥇 黃金：[outlook]

⚠️ 風險：[key risk]

💡 建議：[one sentence]"""
    
    result = call_grok(prompt, use_web_search=True)
    await update.message.reply_text(result)

# ========== 主程式 ==========
def main():
    """啟動 Bot"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN not set!")
        return
    if not GROK_API_KEY:
        logger.error("GROK_API_KEY not set!")
        return
    
    logger.info("Starting FlowAI Bot v2.0...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # 註冊命令
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("meme", meme))
    app.add_handler(CommandHandler("gold", gold))
    app.add_handler(CommandHandler("calendar", calendar))
    app.add_handler(CommandHandler("kol", kol))
    app.add_handler(CommandHandler("ethsol", ethsol))
    app.add_handler(CommandHandler("radar", radar))
    
    logger.info("Bot is running!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
