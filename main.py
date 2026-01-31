"""
FlowAI Market Radar + Trading Signal Bot v3.0
整合版：市場情緒 + Order Flow 交易信號
"""

import os
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import aiohttp

# ═══════════════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════════════

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# Grok API
# ═══════════════════════════════════════════════════════════════════════

async def call_grok(prompt: str, use_search: bool = True) -> str:
    if not GROK_API_KEY:
        return "❌ Grok API 未配置"
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": ""model": "grok-beta",",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
        # 搜尋功能已停用
    # if use_search:
    #     payload["search_parameters"] = {
    #         "mode": "auto",
    #         "return_citations": True,
    #         "from_date": datetime.now().strftime("%Y-%m-%d")
    #     }

    
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

# ═══════════════════════════════════════════════════════════════════════
# 命令
# ═══════════════════════════════════════════════════════════════════════

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
    prompt = """Search X and web for Bitcoin sentiment now.

Format in Chinese:
🔶 BTC 情緒分析
━━━━━━━━━━━━━━━━
📊 情緒：[看漲/看跌] [分數/100]
💰 價格：$[price]
🔥 熱門話題：[topics]
🐋 大戶動態：[whale news]
💡 建議：[advice]
⏰ 更新：[time]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐸 正在掃描 MEME...")
    prompt = """Search for top 5 trending meme coins now.

Format in Chinese:
🐸 MEME 熱幣 TOP 5
━━━━━━━━━━━━━━━━
1️⃣ $[TICKER] - [why trending] ⚠️[risk]
2️⃣ ...
3️⃣ ...
4️⃣ ...
5️⃣ ...
💡 提醒：MEME 波動大，控制倉位！"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🥇 正在分析黃金...")
    prompt = """Search for gold XAU/USD analysis.

Format in Chinese:
🥇 黃金避險雷達
━━━━━━━━━━━━━━━━
💰 現價：$[price] ([change]%)
📊 支撐：$[support] | 壓力：$[resistance]
📰 驅動：[factors]
🎯 觀點：[outlook]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 正在獲取資金費率...")
    prompt = """Search crypto funding rates BTC ETH SOL on Binance Bybit OKX.

Format in Chinese:
💰 資金費率雷達
━━━━━━━━━━━━━━━━
🔶 BTC: Binance [x]% | Bybit [x]% | OKX [x]%
🔷 ETH: Binance [x]% | Bybit [x]% | OKX [x]%
🟣 SOL: Binance [x]% | Bybit [x]% | OKX [x]%
💡 套利提示：[opportunity]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 正在獲取經濟日曆...")
    prompt = """Search important economic events today/tomorrow. Convert to UTC+8.

Format in Chinese:
📅 經濟日曆 (台灣時間)
━━━━━━━━━━━━━━━━
🗓 今日：
⏰ [time] - [event] [🔴高/🟡中/🟢低]
🗓 明日：
⏰ [time] - [event]
⚠️ 重點：[most important]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 正在生成全景報告...")
    prompt = """Create market report: Fear/Greed, BTC/ETH/SOL, top meme, gold, risks.

Format in Chinese:
🌐 FlowAI 全景報告
━━━━━━━━━━━━━━━━
📊 情緒：[Fear/Greed] [score]/100
🔶 BTC: [trend]
🔷 ETH: [trend]
🟣 SOL: [trend]
🔥 MEME: $[ticker]
🥇 黃金: [status]
⚠️ 風險: [risks]
💡 建議: [advice]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 正在分析訂單流...")
    prompt = """Search BTC order flow: order book imbalance, liquidations, CVD, whales.

Format in Chinese:
📊 BTC Order Flow
━━━━━━━━━━━━━━━━
📕 訂單簿：[bid heavy/ask heavy/balanced]
💥 24h清算：多$[x]M | 空$[x]M
📈 CVD：[買壓/賣壓]
🐋 大戶：[movements]
💡 結論：[bullish/bearish/neutral]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 正在生成信號...")
    prompt = """Analyze BTC: trend H1/H4/D1, RSI, KD, support/resistance, recommendation.

Format in Chinese:
🎯 FlowAI 交易信號
━━━━━━━━━━━━━━━━
📊 BTCUSDT | H1
📈 趨勢：H1[?] H4[?] D1[?]
🎚 KD: [超買/超賣/中性]
📍 支撐: $[x] | 壓力: $[x]
🎯 建議：[做多/做空/觀望]
• 進場：$[x]
• 止損：$[x]
• 止盈：$[x]
• 信心：[x]%
⚠️ 僅供參考，風險自負！"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def liq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 正在獲取清算數據...")
    prompt = """Search BTC liquidation data and heatmap levels.

Format in Chinese:
🔥 BTC 清算地圖
━━━━━━━━━━━━━━━━
💰 現價：$[price]
⬆️ 上方清算：$[level] (~$[x]M空單)
⬇️ 下方清算：$[level] (~$[x]M多單)
📊 24h：多$[x]M | 空$[x]M
💡 解讀：[where price might hunt]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def arb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 正在掃描套利...")
    prompt = """Search crypto arbitrage: funding rate arb, spot-futures basis.

Format in Chinese:
🎯 套利機會
━━━━━━━━━━━━━━━━
💰 資金費率套利：[opportunity]
📊 期現套利：基差[x]% 年化[x]%
🔄 跨所價差：[any opportunity]
⚠️ 注意手續費和滑點！"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def ethsol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔷 正在對比 ETH/SOL...")
    prompt = """Compare ETH vs SOL: price, sentiment, news.

Format in Chinese:
🔷 ETH vs SOL
━━━━━━━━━━━━━━━━
🔷 ETH: $[price] ([change]%) - [sentiment]
🟣 SOL: $[price] ([change]%) - [sentiment]
🆚 結論：[which stronger]"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

# ═══════════════════════════════════════════════════════════════════════
# 主程序
# ═══════════════════════════════════════════════════════════════════════

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
