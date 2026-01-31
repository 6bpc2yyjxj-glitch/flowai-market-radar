"""
FlowAI Market Radar v3.2
即時價格（CoinGecko）+ AI 分析（Grok）
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

# CoinGecko API（免費即時價格）
async def get_crypto_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,solana",
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_market_cap": "true"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        logger.error(f"CoinGecko Error: {e}")
    return None

async def get_fear_greed_index():
    url = "https://api.alternative.me/fng/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", [{}])[0]
    except Exception as e:
        logger.error(f"Fear/Greed Error: {e}")
    return None

# Grok API（分析）
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
🎯 *FlowAI 市場雷達 v3.2*
━━━━━━━━━━━━━━━━━━━━━
⚡ 即時價格 + AI 分析

📊 *情緒分析：*
/btc - BTC 即時分析
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
_FlowAI v3.2 - 即時資訊，快人一步_
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔶 正在獲取 BTC 即時數據...")
    
    prices = await get_crypto_prices()
    fng = await get_fear_greed_index()
    
    if prices and "bitcoin" in prices:
        btc_price = prices["bitcoin"]["usd"]
        btc_change = prices["bitcoin"].get("usd_24h_change", 0)
        fng_value = fng.get("value", "N/A") if fng else "N/A"
        fng_text = fng.get("value_classification", "N/A") if fng else "N/A"
        
        prompt = f"""根據以下即時數據分析 BTC：
即時價格：${btc_price:,.2f}
24h 漲跌：{btc_change:.2f}%
恐懼貪婪指數：{fng_value} ({fng_text})

請用繁體中文簡短分析：
1. 目前市場情緒
2. 短線建議
3. 關鍵支撐壓力位"""
        
        analysis = await call_grok(prompt)
        
        result = f"""🔶 BTC 即時分析
━━━━━━━━━━━━━━━━
💰 價格：${btc_price:,.2f}
📊 24h：{btc_change:+.2f}%
😱 恐懼貪婪：{fng_value} ({fng_text})
⏰ 更新：{datetime.now().strftime('%H:%M')}

📝 AI 分析：
{analysis}"""
    else:
        result = "❌ 無法獲取價格數據"
    
    await update.message.reply_text(result)

async def ethsol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔷 正在獲取 ETH/SOL 數據...")
    
    prices = await get_crypto_prices()
    
    if prices:
        eth_price = prices.get("ethereum", {}).get("usd", 0)
        eth_change = prices.get("ethereum", {}).get("usd_24h_change", 0)
        sol_price = prices.get("solana", {}).get("usd", 0)
        sol_change = prices.get("solana", {}).get("usd_24h_change", 0)
        
        prompt = f"""比較 ETH 和 SOL：
ETH：${eth_price:,.2f}（24h: {eth_change:+.2f}%）
SOL：${sol_price:,.2f}（24h: {sol_change:+.2f}%）
請用繁體中文簡短分析：哪個比較強？"""
        
        analysis = await call_grok(prompt)
        
        result = f"""🔷 ETH vs SOL 即時對比
━━━━━━━━━━━━━━━━
🔷 ETH：${eth_price:,.2f} ({eth_change:+.2f}%)
🟣 SOL：${sol_price:,.2f} ({sol_change:+.2f}%)
⏰ 更新：{datetime.now().strftime('%H:%M')}

📝 AI 分析：
{analysis}"""
    else:
        result = "❌ 無法獲取價格數據"
    
    await update.message.reply_text(result)

async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 正在生成全景報告...")
    
    prices = await get_crypto_prices()
    fng = await get_fear_greed_index()
    
    if prices:
        btc = prices.get("bitcoin", {})
        eth = prices.get("ethereum", {})
        sol = prices.get("solana", {})
        fng_value = fng.get("value", "N/A") if fng else "N/A"
        fng_text = fng.get("value_classification", "N/A") if fng else "N/A"
        
        result = f"""🌐 FlowAI 即時全景報告
━━━━━━━━━━━━━━━━
📊 恐懼貪婪：{fng_value} ({fng_text})

🔶 BTC：${btc.get('usd', 0):,.0f} ({btc.get('usd_24h_change', 0):+.1f}%)
🔷 ETH：${eth.get('usd', 0):,.0f} ({eth.get('usd_24h_change', 0):+.1f}%)
🟣 SOL：${sol.get('usd', 0):,.0f} ({sol.get('usd_24h_change', 0):+.1f}%)

⏰ 更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━
💡 輸入 /btc 查看詳細分析"""
    else:
        result = "❌ 無法獲取數據"
    
    await update.message.reply_text(result)

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🥇 正在分析黃金...")
    prompt = """請分析目前黃金 XAU/USD 的走勢，用繁體中文簡短回覆：
1. 大約價格
2. 趨勢分析
3. 短線建議"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐸 正在分析 MEME 幣...")
    prompt = """列出目前最熱門的 5 個 MEME 幣，用繁體中文回覆"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 正在分析資金費率...")
    prompt = """說明 BTC、ETH、SOL 永續合約資金費率的狀況，用繁體中文簡短回覆"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 正在獲取經濟日曆...")
    prompt = f"""今天是 {datetime.now().strftime('%Y-%m-%d')}，列出近期重要經濟事件，用繁體中文回覆，時間轉為台灣時間"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 正在分析訂單流...")
    prices = await get_crypto_prices()
    btc_price = prices.get("bitcoin", {}).get("usd", 0) if prices else 0
    prompt = f"""BTC 現價 ${btc_price:,.0f}，分析訂單流和市場結構，用繁體中文簡短回覆"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 正在生成交易信號...")
    prices = await get_crypto_prices()
    fng = await get_fear_greed_index()
    
    if prices:
        btc = prices.get("bitcoin", {})
        fng_value = fng.get("value", "N/A") if fng else "N/A"
        prompt = f"""根據數據生成 BTC 交易信號：
現價：${btc.get('usd', 0):,.2f}
24h：{btc.get('usd_24h_change', 0):.2f}%
恐懼貪婪：{fng_value}

用繁體中文回覆：建議、進場、止損、止盈"""
        result = await call_grok(prompt)
    else:
        result = "❌ 無法獲取數據"
    await update.message.reply_text(result)

async def liq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 正在分析清算數據...")
    prices = await get_crypto_prices()
    btc_price = prices.get("bitcoin", {}).get("usd", 0) if prices else 0
    prompt = f"""BTC 現價 ${btc_price:,.0f}，分析清算數據，用繁體中文回覆"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

async def arb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 正在掃描套利...")
    prompt = """分析目前加密貨幣套利機會，用繁體中文簡短回覆"""
    result = await call_grok(prompt)
    await update.message.reply_text(result)

def main():
    if not TELEGRAM_TOKEN:
        print("❌ 請設置 TELEGRAM_TOKEN")
        return
    
    logger.info("🚀 FlowAI Bot v3.2 啟動中...")
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
