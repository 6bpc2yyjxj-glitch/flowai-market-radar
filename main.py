"""
FlowAI 交易機器人 v4.0
即時價格 + AI 分析 + Bybit 交易
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
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY", "")
BYBIT_PRIVATE_KEY = os.getenv("BYBIT_PRIVATE_KEY", "")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

trader = BybitTrader()

async def get_crypto_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin,ethereum,solana", "vs_currencies": "usd", "include_24hr_change": "true"}
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

async def call_grok(prompt: str) -> str:
    if not GROK_API_KEY:
        return "❌ Grok API 未配置"
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"}
    payload = "model": "grok-4-1-fast-non-reasoning", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=90) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                return f"❌ API 錯誤: {resp.status}"
    except Exception as e:
        return f"❌ 錯誤: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """
🎯 *FlowAI 交易系統 v4.0*
━━━━━━━━━━━━━━━━━━━━━
⚡ 即時價格 + AI 分析 + 自動交易

📊 *市場分析：*
/btc - BTC 即時分析
/radar - 全景報告

💰 *交易功能：*
/balance - 查詢餘額
/position - 查詢持倉
/orders - 未成交訂單

🎯 *快速交易：*
/long - 做多 BTC
/short - 做空 BTC
/close - 平倉

⚙️ *設定：*
/leverage - 設置槓桿
/status - 系統狀態

━━━━━━━━━━━━━━━━━━━━━
_FlowAI v4.0 - 自動交易，智能決策_
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔶 正在獲取 BTC 數據...")
    ticker = await trader.get_ticker(symbol="BTCUSDT")
    funding = await trader.get_funding_rate(symbol="BTCUSDT")
    fng = await get_fear_greed_index()
    
    if ticker.get("retCode") == 0:
        data = ticker["result"]["list"][0]
        price = float(data["lastPrice"])
        change_24h = float(data["price24hPcnt"]) * 100
        high_24h = float(data["highPrice24h"])
        low_24h = float(data["lowPrice24h"])
        volume = float(data["volume24h"])
        
        funding_rate = "N/A"
        if funding.get("retCode") == 0 and funding["result"]["list"]:
            funding_rate = float(funding["result"]["list"][0]["fundingRate"]) * 100
        
        fng_value = fng.get("value", "N/A") if fng else "N/A"
        fng_text = fng.get("value_classification", "N/A") if fng else "N/A"
        
        prompt = f"""根據 Bybit 即時數據分析 BTC：
價格：${price:,.2f}
24h 漲跌：{change_24h:.2f}%
24h 高：${high_24h:,.2f}
24h 低：${low_24h:,.2f}
資金費率：{funding_rate}%
恐懼貪婪：{fng_value} ({fng_text})

用繁體中文簡短分析：市場情緒、短線建議、關鍵價位"""
        
        analysis = await call_grok(prompt)
        
        result = f"""🔶 BTC/USDT 即時分析 (Bybit)
━━━━━━━━━━━━━━━━
💰 價格：${price:,.2f}
📊 24h：{change_24h:+.2f}%
📈 高：${high_24h:,.2f}
📉 低：${low_24h:,.2f}
💸 資金費率：{funding_rate:.4f}%
😱 恐懼貪婪：{fng_value}
⏰ {datetime.now().strftime('%H:%M:%S')}

📝 AI 分析：
{analysis}"""
    else:
        result = f"❌ 錯誤: {ticker.get('retMsg', '未知錯誤')}"
    await update.message.reply_text(result)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    await update.message.reply_text("💰 正在查詢餘額...")
    result = await trader.get_wallet_balance()
    if result.get("retCode") == 0:
        coins = result.get("result", {}).get("list", [{}])[0].get("coin", [])
        msg = "💰 Bybit 帳戶餘額\n━━━━━━━━━━━━━━━━\n"
        total_usd = 0
        for coin in coins:
            bal = float(coin.get("walletBalance", 0))
            if bal > 0:
                usd_value = float(coin.get("usdValue", 0))
                total_usd += usd_value
                msg += f"💎 {coin['coin']}: {bal:.4f} (${usd_value:,.2f})\n"
        msg += f"\n💵 總資產：${total_usd:,.2f}"
    else:
        msg = f"❌ 錯誤: {result.get('retMsg', '未知錯誤')}"
    await update.message.reply_text(msg)

async def position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    await update.message.reply_text("📊 正在查詢持倉...")
    result = await trader.get_positions()
    if result.get("retCode") == 0:
        positions = result.get("result", {}).get("list", [])
        if not positions or all(float(p.get("size", 0)) == 0 for p in positions):
            msg = "📊 目前無持倉"
        else:
            msg = "📊 Bybit 持倉\n━━━━━━━━━━━━━━━━\n"
            for pos in positions:
                size = float(pos.get("size", 0))
                if size > 0:
                    symbol = pos.get("symbol")
                    side = pos.get("side")
                    entry = float(pos.get("avgPrice", 0))
                    pnl = float(pos.get("unrealisedPnl", 0))
                    emoji = "🟢" if pnl >= 0 else "🔴"
                    msg += f"{emoji} {symbol} {side}\n   數量：{size}\n   進場：${entry:,.2f}\n   盈虧：${pnl:,.2f}\n"
    else:
        msg = f"❌ 錯誤: {result.get('retMsg')}"
    await update.message.reply_text(msg)

async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    result = await trader.get_open_orders()
    if result.get("retCode") == 0:
        order_list = result.get("result", {}).get("list", [])
        if not order_list:
            msg = "📋 目前無未成交訂單"
        else:
            msg = "📋 未成交訂單\n━━━━━━━━━━━━━━━━\n"
            for order in order_list:
                msg += f"• {order['symbol']} {order['side']} {order['qty']}\n"
    else:
        msg = f"❌ 錯誤: {result.get('retMsg')}"
    await update.message.reply_text(msg)

async def long_btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    keyboard = [[InlineKeyboardButton("✅ 確認做多 0.001 BTC", callback_data="confirm_long_0.001"), InlineKeyboardButton("❌ 取消", callback_data="cancel_order")]]
    await update.message.reply_text("🟢 確認做多 BTC？\n數量：0.001 BTC\n類型：市價單", reply_markup=InlineKeyboardMarkup(keyboard))

async def short_btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    keyboard = [[InlineKeyboardButton("✅ 確認做空 0.001 BTC", callback_data="confirm_short_0.001"), InlineKeyboardButton("❌ 取消", callback_data="cancel_order")]]
    await update.message.reply_text("🔴 確認做空 BTC？\n數量：0.001 BTC\n類型：市價單", reply_markup=InlineKeyboardMarkup(keyboard))

async def close_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    keyboard = [[InlineKeyboardButton("✅ 確認平倉", callback_data="confirm_close"), InlineKeyboardButton("❌ 取消", callback_data="cancel_order")]]
    await update.message.reply_text("⚠️ 確認平掉所有 BTC 持倉？", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "cancel_order":
        await query.edit_message_text("❌ 已取消")
        return
    
    if data.startswith("confirm_long_"):
        qty = data.split("_")[-1]
        await query.edit_message_text("🔄 正在下單...")
        result = await trader.place_order(symbol="BTCUSDT", side="Buy", qty=qty, order_type="Market")
        if result.get("retCode") == 0:
            msg = f"✅ 做多成功！\n訂單ID: {result['result']['orderId']}"
        else:
            msg = f"❌ 下單失敗: {result.get('retMsg')}"
        await query.edit_message_text(msg)
    
    elif data.startswith("confirm_short_"):
        qty = data.split("_")[-1]
        await query.edit_message_text("🔄 正在下單...")
        result = await trader.place_order(symbol="BTCUSDT", side="Sell", qty=qty, order_type="Market")
        if result.get("retCode") == 0:
            msg = f"✅ 做空成功！\n訂單ID: {result['result']['orderId']}"
        else:
            msg = f"❌ 下單失敗: {result.get('retMsg')}"
        await query.edit_message_text(msg)
    
    elif data == "confirm_close":
        await query.edit_message_text("🔄 正在平倉...")
        positions = await trader.get_positions(symbol="BTCUSDT")
        if positions.get("retCode") == 0:
            pos_list = positions.get("result", {}).get("list", [])
            for pos in pos_list:
                size = float(pos.get("size", 0))
                if size > 0:
                    side = pos.get("side")
                    result = await trader.close_position(symbol="BTCUSDT", side=side, qty=str(size))
                    if result.get("retCode") == 0:
                        await query.edit_message_text("✅ 平倉成功！")
                    else:
                        await query.edit_message_text(f"❌ 平倉失敗: {result.get('retMsg')}")
                    return
            await query.edit_message_text("📊 目前無持倉")
        else:
            await query.edit_message_text(f"❌ 錯誤: {positions.get('retMsg')}")

async def set_leverage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    if not context.args:
        await update.message.reply_text("用法：/leverage 10")
        return
    lev = context.args[0]
    result = await trader.set_leverage(symbol="BTCUSDT", leverage=lev)
    if result.get("retCode") == 0:
        msg = f"✅ 槓桿已設置為 {lev}x"
    else:
        msg = f"❌ 設置失敗: {result.get('retMsg')}"
    await update.message.reply_text(msg)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_status = "✅" if BYBIT_API_KEY else "❌"
    key_status = "✅" if BYBIT_PRIVATE_KEY else "❌"
    grok_status = "✅" if GROK_API_KEY else "❌"
    msg = f"""⚙️ FlowAI 系統狀態
━━━━━━━━━━━━━━━━
🔑 Bybit API Key: {api_status}
🔐 RSA 私鑰: {key_status}
🤖 Grok API: {grok_status}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
版本：v4.0"""
    await update.message.reply_text(msg)

async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 正在生成全景報告...")
    btc_ticker = await trader.get_ticker(symbol="BTCUSDT")
    eth_ticker = await trader.get_ticker(symbol="ETHUSDT")
    sol_ticker = await trader.get_ticker(symbol="SOLUSDT")
    fng = await get_fear_greed_index()
    
    msg = "🌐 FlowAI 即時全景報告\n━━━━━━━━━━━━━━━━\n"
    fng_value = fng.get("value", "N/A") if fng else "N/A"
    msg += f"😱 恐懼貪婪：{fng_value}\n\n"
    
    for name, ticker in [("BTC", btc_ticker), ("ETH", eth_ticker), ("SOL", sol_ticker)]:
        if ticker.get("retCode") == 0:
            data = ticker["result"]["list"][0]
            price = float(data["lastPrice"])
            change = float(data["price24hPcnt"]) * 100
            emoji = "🟢" if change >= 0 else "🔴"
            msg += f"{emoji} {name}: ${price:,.2f} ({change:+.2f}%)\n"
    
    msg += f"\n⏰ {datetime.now().strftime('%H:%M:%S')}"
    await update.message.reply_text(msg)

def main():
    if not TELEGRAM_TOKEN:
        print("❌ 請設置 TELEGRAM_TOKEN")
        return
    logger.info("🚀 FlowAI Trading Bot v4.0 啟動中...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("radar", radar))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("position", position))
    app.add_handler(CommandHandler("orders", orders))
    app.add_handler(CommandHandler("long", long_btc))
    app.add_handler(CommandHandler("short", short_btc))
    app.add_handler(CommandHandler("close", close_position))
    app.add_handler(CommandHandler("leverage", set_leverage))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("✅ Bot 運行中！")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
