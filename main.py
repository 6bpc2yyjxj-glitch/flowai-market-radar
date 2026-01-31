"""
FlowAI Market Radar v3.0
"""

import os
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import aiohttp

# 配置
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Grok API
async def call_grok(prompt: str) -> str:
    if not GROK_API_KEY:
        return "❌ Grok API 未配置"
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "grok-3-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=60) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                return f"❌ API 錯誤: {resp.status}"
    except asyncio.TimeoutError:
        return "❌ 請求超時"
    except Exception as e:
        return f"❌ 錯誤: {str(e)}"

# 命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """
🎯 *FlowAI 市場雷達 v3.0*
━━━━━━━━━━━━━━━━━━━━━

📊 *情緒分析：*
/btc - BTC 即時情緒
/meme - MEME 熱幣 TOP 5
/ethsol - ETH/SOL 對比

🥇 *外匯黃金：*
/gold - 黃金避險雷達
/calendar - 經濟日曆

💰 *套利工具：*
/funding - 資金費率
/arb - 套利機會
/liq - 清算地圖

🔥 *Order Flow：*
/flow - 訂單流分析
/signal - 交易信號

⚡ *綜合：*
/radar - 全景報告

━━━━━━━━━━━━━━━━━━━━━
_FlowAI v3.0 - 讓你比市場快一步_
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔶 正在分析 BTC...")
    prompt = """分析目前 Bitcoin 的市場情緒和價格走勢。

請用以下格式回覆（繁體中文）：
🔶 BTC 情緒分析
━━━━━━━━━━━━━━━━
📊 情緒：[看漲/看跌/中性]
💰 目前價格：約 $[price]
🔥 熱門話題：[最近的新聞或話題]
💡 建議：[一句話建議]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐸 正在掃描 MEME...")
    prompt = """列出目前最熱門的 5 個 MEME 幣。

請用以下格式回覆（繁體中文）：
🐸 MEME 熱幣 TOP 5
━━━━━━━━━━━━━━━━
1️⃣ $[TICKER] - [為什麼熱門]
2️⃣ $[TICKER] - [為什麼熱門]
3️⃣ $[TICKER] - [為什麼熱門]
4️⃣ $[TICKER] - [為什麼熱門]
5️⃣ $[TICKER] - [為什麼熱門]

💡 提醒：MEME 波動大，控制倉位！"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🥇 正在分析黃金...")
    prompt = """分析目前黃金 XAU/USD 的走勢。

請用以下格式回覆（繁體中文）：
🥇 黃金避險雷達
━━━━━━━━━━━━━━━━
💰 現價：約 $[price]
📊 趨勢：[上漲/下跌/盤整]
📰 驅動因素：[影響金價的因素]
🎯 短線觀點：[建議]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 正在獲取資金費率...")
    prompt = """說明目前加密貨幣永續合約的資金費率狀況（BTC、ETH、SOL）。

請用以下格式回覆（繁體中文）：
💰 資金費率雷達
━━━━━━━━━━━━━━━━
🔶 BTC：[正/負費率，多空傾向]
🔷 ETH：[正/負費率，多空傾向]
🟣 SOL：[正/負費率，多空傾向]

💡 套利提示：[如果有套利機會]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 正在獲取經濟日曆...")
    prompt = """列出近期重要的經濟事件和數據發布。

請用以下格式回覆（繁體中文）：
📅 經濟日曆
━━━━━━━━━━━━━━━━
🗓 近期重要事件：
- [事件1] - [日期] [重要性：高/中/低]
- [事件2] - [日期] [重要性：高/中/低]
- [事件3] - [日期] [重要性：高/中/低]

⚠️ 重點關注：[最重要的事件]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 正在生成全景報告...")
    prompt = """提供一份簡短的市場全景報告。

請用以下格式回覆（繁體中文）：
🌐 FlowAI 全景報告
━━━━━━━━━━━━━━━━
📊 市場情緒：[恐懼/貪婪/中性]

🔶 BTC：[簡短趨勢]
🔷 ETH：[簡短趨勢]
🟣 SOL：[簡短趨勢]

🔥 熱點：[目前市場焦點]
⚠️ 風險：[需要注意的風險]

💡 建議：[一句話建議]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 正在分析訂單流...")
    prompt = """分析 BTC 的訂單流和市場結構。

請用以下格式回覆（繁體中文）：
📊 BTC Order Flow 分析
━━━━━━━━━━━━━━━━
📕 訂單簿狀態：[買盤強/賣盤強/平衡]
💥 清算狀況：[近期清算情況]
📈 大戶動向：[鯨魚是買還是賣]

💡 結論：[看漲/看跌/中性，原因]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 正在生成信號...")
    prompt = """基於技術分析，給出 BTC 的交易建議。

請用以下格式回覆（繁體中文）：
🎯 FlowAI 交易信號
━━━━━━━━━━━━━━━━
📊 BTCUSDT

📈 趨勢：[上漲/下跌/盤整]
🎚 技術指標：[RSI、KD 等狀態]

📍 關鍵價位：
- 支撐：$[price]
- 壓力：$[price]

🎯 建議：[做多/做空/觀望]
- 進場參考：$[price]
- 止損參考：$[price]
- 目標參考：$[price]

⚠️ 僅供參考，風險自負！"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def liq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 正在獲取清算數據...")
    prompt = """分析 BTC 的清算數據和清算熱點。

請用以下格式回覆（繁體中文）：
🔥 BTC 清算地圖
━━━━━━━━━━━━━━━━
💰 目前價格：約 $[price]

⬆️ 上方清算區：$[price range] - 空單清算
⬇️ 下方清算區：$[price range] - 多單清算

📊 24h 清算：
- 多單：約 $[amount]
- 空單：約 $[amount]

💡 解讀：[價格可能往哪個方向獵殺]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def arb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 正在掃描套利...")
    prompt = """分析目前加密貨幣市場的套利機會。

請用以下格式回覆（繁體中文）：
🎯 套利機會掃描
━━━━━━━━━━━━━━━━
💰 資金費率套利：[有無機會]
📊 期現套利：[有無機會]
🔄 跨所價差：[有無機會]

⚠️ 注意手續費和滑點成本！"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def ethsol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔷 正在對比 ETH/SOL...")
    prompt = """比較 ETH 和 SOL 目前的表現。

請用以下格式回覆（繁體中文）：
🔷 ETH vs SOL 對比
━━━━━━━━━━━━━━━━
🔷 ETH：
- 價格：約 $[price]
- 趨勢：[上漲/下跌/盤整]

🟣 SOL：
- 價格：約 $[price]
- 趨勢：[上漲/下跌/盤整]

🆚 結論：[哪個比較強，為什麼]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

# 主程序
def main():
    if not TELEGRAM_TOKEN:
        print("❌ 請設置 TELEGRAM_TOKEN")
        return
    
    logger.info("🚀 FlowAI Bot v3.0 啟動中...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("meme", meme))
    app.add_handler(CommandHandler("gold", gold))
    app.add_handler(CommandHandler("funding", funding))
    app.add_handler(CommandHandler("calendar", calendar))
    app.add_handler(CommandHandler("radar", radar))
    app.add_handler(CommandHandler("flow", flow))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("liq", liq))
    app.add_handler(CommandHandler("arb", arb))
    app.add_handler(CommandHandler("ethsol", ethsol))
    
    logger.info("✅ Bot 運行中！")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
