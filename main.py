"""
FlowAI Market Radar v3.1 - 即時搜尋版
使用 Grok Agent Tools API
"""

import os
import asyncio
import logging
import json
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

# Grok Agent Tools API（即時搜尋）
async def call_grok_realtime(prompt: str) -> str:
    if not GROK_API_KEY:
        return "❌ Grok API 未配置"
    
    # 使用 Responses API endpoint
    url = "https://api.x.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "grok-4-1-fast-non-reasoning",
        "messages": [{"role": "user", "content": prompt}],
        "tools": [
            {"type": "web_search"},
            {"type": "x_search"}
        ],
        "temperature": 0.7
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=120) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Responses API 格式
                    if "output" in data:
                        for item in data["output"]:
                            if item.get("type") == "message":
                                content = item.get("content", [])
                                for c in content:
                                    if c.get("type") == "text":
                                        return c.get("text", "無回應")
                    # 備用格式
                    if "choices" in data:
                        return data["choices"][0]["message"]["content"]
                    return "無法解析回應"
                else:
                    error_text = await resp.text()
                    logger.error(f"API Error {resp.status}: {error_text}")
                    return f"❌ API 錯誤: {resp.status}"
    except asyncio.TimeoutError:
        return "❌ 請求超時（搜尋中，請稍後再試）"
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return f"❌ 錯誤: {str(e)}"

# 命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """
🎯 *FlowAI 市場雷達 v3.1*
━━━━━━━━━━━━━━━━━━━━━
⚡ 即時搜尋版 - 資料來自網路與 X

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
_FlowAI v3.1 - 即時資訊，快人一步_
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔶 正在搜尋 BTC 最新資訊...")
    prompt = """搜尋網路和 X (Twitter) 上關於 Bitcoin 的最新資訊。

請用以下格式回覆（繁體中文）：
🔶 BTC 即時情緒分析
━━━━━━━━━━━━━━━━
💰 目前價格：$[搜尋到的即時價格]
📊 24h 漲跌：[百分比]
🔥 X 熱門話題：[Twitter 上討論什麼]
📰 最新新聞：[重要新聞]
💡 建議：[一句話建議]
⏰ 更新時間：[現在時間]"""
    result = await call_grok_realtime(prompt)
    await update.message.reply_text(result)

async def meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐸 正在搜尋 MEME 幣最新動態...")
    prompt = """搜尋網路和 X 上目前最熱門的 5 個 MEME 幣。

請用以下格式回覆（繁體中文）：
🐸 MEME 熱幣 TOP 5（即時）
━━━━━━━━━━━━━━━━
1️⃣ $[TICKER] - 價格 $[price] - [為什麼熱門]
2️⃣ $[TICKER] - 價格 $[price] - [為什麼熱門]
3️⃣ $[TICKER] - 價格 $[price] - [為什麼熱門]
4️⃣ $[TICKER] - 價格 $[price] - [為什麼熱門]
5️⃣ $[TICKER] - 價格 $[price] - [為什麼熱門]

💡 提醒：MEME 波動大，控制倉位！"""
    result = await call_grok_realtime(prompt)
    await update.message.reply_text(result)

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🥇 正在搜尋黃金最新資訊...")
    prompt = """搜尋黃金 XAU/USD 的最新價格和市場分析。

請用以下格式回覆（繁體中文）：
🥇 黃金即時雷達
━━━━━━━━━━━━━━━━
💰 現價：$[即時價格]/盎司
📊 24h 漲跌：[百分比]
📈 趨勢：[上漲/下跌/盤整]
📰 驅動因素：[最新影響金價的因素]
🎯 短線觀點：[建議]"""
    result = await call_grok_realtime(prompt)
    await update.message.reply_text(result)

async def funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 正在搜尋資金費率...")
    prompt = """搜尋 BTC、ETH、SOL 在 Binance、Bybit、OKX 的最新永續合約資金費率。

請用以下格式回覆（繁體中文）：
💰 資金費率即時雷達
━━━━━━━━━━━━━━━━
🔶 BTC：
  Binance [x]% | Bybit [x]% | OKX [x]%
🔷 ETH：
  Binance [x]% | Bybit [x]% | OKX [x]%
🟣 SOL：
  Binance [x]% | Bybit [x]% | OKX [x]%

💡 套利提示：[如果有費率差異可套利]"""
    result = await call_grok_realtime(prompt)
    await update.message.reply_text(result)

async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 正在搜尋經濟日曆...")
    prompt = """搜尋今天和明天的重要經濟數據發布時間（美國、歐洲、亞洲）。

請用以下格式回覆（繁體中文，時間轉換為台灣時間 UTC+8）：
📅 經濟日曆（台灣時間）
━━━━━━━━━━━━━━━━
🗓 今日：
⏰ [時間] - [事件] [🔴高/🟡中/🟢低]

🗓 明日：
⏰ [時間] - [事件] [重要性]

⚠️ 重點關注：[最重要的事件]"""
    result = await call_grok_realtime(prompt)
    await update.message.reply_text(result)

async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 正在生成全景報告...")
    prompt = """搜尋加密貨幣市場的最新狀況，包括 BTC、ETH、SOL 價格和市場情緒。

請用以下格式回覆（繁體中文）：
🌐 FlowAI 即時全景報告
━━━━━━━━━━━━━━━━
📊 恐懼貪婪指數：[數值] [恐懼/貪婪/中性]

🔶 BTC：$[價格] ([24h%]) - [趨勢]
🔷 ETH：$[價格] ([24h%]) - [趨勢]
🟣 SOL：$[價格] ([24h%]) - [趨勢]

🔥 市場熱點：[目前焦點]
⚠️ 風險提醒：[需要注意的]

💡 建議：[一句話建議]
⏰ 更新：[現在時間]"""
    result = await call_grok_realtime(prompt)
    await update.message.reply_text(result)

async def flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 正在搜尋訂單流資訊...")
    prompt = """搜尋 BTC 的訂單流數據，包括清算、大戶動向、CVD 等。

請用以下格式回覆（繁體中文）：
📊 BTC Order Flow 即時分析
━━━━━━━━━━━━━━━━
💰 現價：$[價格]
📕 訂單簿：[買盤強/賣盤強/平衡]
💥 24h 清算：多 $[x]M | 空 $[x]M
📈 大戶動向：[鯨魚在買/賣/觀望]

💡 結論：[看漲/看跌/中性]"""
    result = await call_grok_realtime(prompt)
    await update.message.reply_text(result)

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 正在生成交易信號...")
    prompt = """基於 BTC 目前的價格和技術分析，給出交易建議。先搜尋最新價格。

請用以下格式回覆（繁體中文）：
🎯 FlowAI 即時交易信號
━━━━━━━━━━━━━━━━
📊 BTCUSDT | 現價：$[即時價格]

📈 趨勢：[上漲/下跌/盤整]
🎚 技術指標：[RSI、KD 狀態]

📍 關鍵價位：
- 支撐：$[price]
- 壓力：$[price]

🎯 建議：[做多/做空/觀望]
- 進場參考：$[price]
- 止損參考：$[price]
- 目標參考：$[price]

⚠️ 僅供參考，風險自負！"""
    result = await call_grok_realtime(prompt)
    await update.message.reply_text(result)

async def liq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 正在搜尋清算數據...")
    prompt = """搜尋 BTC 的清算數據和清算熱點價位。

請用以下格式回覆（繁體中文）：
🔥 BTC 清算地圖（即時）
━━━━━━━━━━━━━━━━
💰 目前價格：$[即時價格]

⬆️ 上方清算區：$[price] - 約 $[x]M 空單
⬇️ 下方清算區：$[price] - 約 $[x]M 多單

📊 24h 清算總額：
- 多單：$[amount]
- 空單：$[amount]

💡 解讀：[價格可能往哪獵殺]"""
    result = await call_grok_realtime(prompt)
    await update.message.reply_text(result)

async def arb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 正在掃描套利機會...")
    prompt = """搜尋目前加密貨幣市場的套利機會，包括資金費率套利、期現價差。

請用以下格式回覆（繁體中文）：
🎯 套利機會掃描（即時）
━━━━━━━━━━━━━━━━
💰 資金費率套利：
  [有無機會，哪個幣種]

📊 期現價差：
  [現貨 vs 期貨價差]

🔄 跨所價差：
  [交易所間價差]

⚠️ 注意手續費和滑點！"""
    result = await call_grok_realtime(prompt)
    await update.message.reply_text(result)

async def ethsol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔷 正在搜尋 ETH/SOL 最新資訊...")
    prompt = """搜尋 ETH 和 SOL 的最新價格和市場表現比較。

請用以下格式回覆（繁體中文）：
🔷 ETH vs SOL 即時對比
━━━━━━━━━━━━━━━━
🔷 ETH：
- 價格：$[即時價格]
- 24h：[漲跌%]
- 趨勢：[上漲/下跌/盤整]

🟣 SOL：
- 價格：$[即時價格]
- 24h：[漲跌%]
- 趨勢：[上漲/下跌/盤整]

🆚 結論：[哪個比較強，為什麼]"""
    result = await call_grok_realtime(prompt)
    await update.message.reply_text(result)

# 主程序
def main():
    if not TELEGRAM_TOKEN:
        print("❌ 請設置 TELEGRAM_TOKEN")
        return
    
    logger.info("🚀 FlowAI Bot v3.1 即時版啟動中...")
    
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
    
    logger.info("✅ Bot 運行中！即時搜尋已啟用")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
