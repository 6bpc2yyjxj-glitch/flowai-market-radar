"""
FlowAI 交易機器人 v4.0
"""

import os
import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import aiohttp

from bybit_trader import BybitTrader

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

trader = BybitTrader()

async def get_fear_greed_index():
    url = "https://api.alternative.me/fng/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", [{}])[0]
    except:
        pass
    return None

async def call_grok(prompt: str) -> str:
    if not GROK_API_KEY:
        return "❌ Grok API 未配置"
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "grok-4-1-fast-non-reasoning", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=60) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                return f"❌ API 錯誤: {resp.status}"
    except Exception as e:
        return f"❌ 錯誤: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """🎯 *FlowAI 交易系統 v4.0*
━━━━━━━━━━━━━━━━━━━━━
📊 /btc - BTC 分析
🌐 /radar - 全景報告
💰 /balance - 查餘額
📊 /position - 查持倉
🟢 /long - 做多
🔴 /short - 做空
⚙️ /status - 系統狀態
━━━━━━━━━━━━━━━━━━━━━"""
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔶 正在獲取 BTC 數據...")
    
    ticker = await trader.get_ticker(symbol="BTCUSDT")
    fng = await get_fear_greed_index()
    
    if ticker.get("retCode") == 0:
        data = ticker["result"]["list"][0]
        price = float(data["lastPrice"])
        change = float(data["price24hPcnt"]) * 100
        high = float(data["highPrice24h"])
        low = float(data["lowPrice24h"])
        
        fng_value = fng.get("value", "N/A") if fng else "N/A"
        
        prompt = f"""BTC 即時數據：
價格：${price:,.2f}
24h：{change:+.2f}%
高：${high:,.2f}
低：${low:,.2f}
恐懼貪婪：{fng_value}

用繁體中文簡短分析（50字內）"""
        
        analysis = await call_grok(prompt)
        
        result = f"""🔶 BTC/USDT
━━━━━━━━━━━━━━━━
💰 ${price:,.2f}
📊 {change:+.2f}%
📈 高 ${high:,.2f}
📉 低 ${low:,.2f}
😱 恐懼貪婪：{fng_value}

📝 {analysis}"""
    else:
        result = f"❌ 錯誤: {ticker.get('retMsg', '未知')}"
    
    await update.message.reply_text(result)

async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 正在獲取數據...")
    
    btc = await trader.get_ticker(symbol="BTCUSDT")
    eth = await trader.get_ticker(symbol="ETHUSDT")
    sol = await trader.get_ticker(symbol="SOLUSDT")
    fng = await get_fear_greed_index()
    
    msg = "🌐 FlowAI 全景報告\n━━━━━━━━━━━━━━━━\n"
    
    if fng:
        msg += f"😱 恐懼貪婪：{fng.get('value', 'N/A')}\n\n"
    
    for name, ticker in [("BTC", btc), ("ETH", eth), ("SOL", sol)]:
        if ticker.get("retCode") == 0:
            data = ticker["result"]["list"][0]
            price = float(data["lastPrice"])
            change = float(data["price24hPcnt"]) * 100
            emoji = "🟢" if change >= 0 else "🔴"
            msg += f"{emoji} {name}: ${price:,.2f} ({change:+.1f}%)\n"
        else:
            msg += f"❌ {name}: 獲取失敗\n"
    
    msg += f"\n⏰ {datetime.now().strftime('%H:%M:%S')}"
    await update.message.reply_text(msg)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    
    await update.message.reply_text("💰 正在查詢...")
    result = await trader.get_wallet_balance()
    
    if result.get("retCode") == 0:
        coins = result.get("result", {}).get("list", [{}])[0].get("coin", [])
        msg = "💰 Bybit 餘額\n━━━━━━━━━━━━━━━━\n"
        total = 0
        for coin in coins:
            bal = float(coin.get("walletBalance", 0))
            if bal > 0:
                usd = float(coin.get("usdValue", 0))
                total += usd
                msg += f"💎 {coin['coin']}: {bal:.4f} (${usd:,.2f})\n"
        msg += f"\n💵 總計：${total:,.2f}"
    else:
        msg = f"❌ {result.get('retMsg', '錯誤')}"
    
    await update.message.reply_text(msg)

async def position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    
    result = await trader.get_positions()
    
    if result.get("retCode") == 0:
        positions = result.get("result", {}).get("list", [])
        has_pos = False
        msg = "📊 持倉\n━━━━━━━━━━━━━━━━\n"
        for pos in positions:
            size = float(pos.get("size", 0))
            if size > 0:
                has_pos = True
                pnl = float(pos.get("unrealisedPnl", 0))
                emoji = "🟢" if pnl >= 0 else "🔴"
                msg += f"{emoji} {pos['symbol']} {pos['side']}\n   數量:{size} 盈虧:${pnl:.2f}\n"
        if not has_pos:
            msg = "📊 目前無持倉"
    else:
        msg = f"❌ {result.get('retMsg')}"
    
    await update.message.reply_text(msg)

async def long_btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    keyboard = [[InlineKeyboardButton("✅ 確認做多", callback_data="long_0.001"), InlineKeyboardButton("❌ 取消", callback_data="cancel")]]
    await update.message.reply_text("🟢 做多 0.001 BTC？", reply_markup=InlineKeyboardMarkup(keyboard))

async def short_btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    keyboard = [[InlineKeyboardButton("✅ 確認做空", callback_data="short_0.001"), InlineKeyboardButton("❌ 取消", callback_data="cancel")]]
    await update.message.reply_text("🔴 做空 0.001 BTC？", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "cancel":
        await query.edit_message_text("❌ 已取消")
        return
    
    if data.startswith("long_"):
        qty = data.split("_")[1]
        await query.edit_message_text("🔄 下單中...")
        result = await trader.place_order(symbol="BTCUSDT", side="Buy", qty=qty)
        msg = f"✅ 做多成功！" if result.get("retCode") == 0 else f"❌ {result.get('retMsg')}"
        await query.edit_message_text(msg)
    
    elif data.startswith("short_"):
        qty = data.split("_")[1]
        await query.edit_message_text("🔄 下單中...")
        result = await trader.place_order(symbol="BTCUSDT", side="Sell", qty=qty)
        msg = f"✅ 做空成功！" if result.get("retCode") == 0 else f"❌ {result.get('retMsg')}"
        await query.edit_message_text(msg)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"""⚙️ 系統狀態
━━━━━━━━━━━━━━━━
🔑 Bybit API: {"✅" if os.getenv("BYBIT_API_KEY") else "❌"}
🔐 私鑰: {"✅" if os.getenv("BYBIT_PRIVATE_KEY") else "❌"}
🤖 Grok: {"✅" if GROK_API_KEY else "❌"}
👤 Admin: {ADMIN_CHAT_ID}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
版本：v4.0"""
    await update.message.reply_text(msg)

def main():
    if not TELEGRAM_TOKEN:
        print("❌ 請設置 TELEGRAM_TOKEN")
        return
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("radar", radar))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("position", position))
    app.add_handler(CommandHandler("long", long_btc))
    app.add_handler(CommandHandler("short", short_btc))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("🚀 FlowAI v4.0 啟動！")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
