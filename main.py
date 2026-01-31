"""
FlowAI 交易機器人 v5.1
雲端友好版：CoinCap 價格 + Grok AI 分析
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

# ═══════════════════════════════════════════════════════════════════════
# API 函數
# ═══════════════════════════════════════════════════════════════════════

async def get_fear_greed_index():
    """恐懼貪婪指數"""
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

async def get_gold_price():
    """黃金價格 - 用 Grok 搜尋"""
    # 直接用 AI 獲取最新價格
    return None  # 改用 AI 分析

async def call_grok(prompt: str) -> str:
    """Grok AI 分析"""
    if not GROK_API_KEY:
        return "❌ Grok API 未配置"
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "grok-4-1-fast-reasoning",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=90) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                return f"❌ API 錯誤: {resp.status}"
    except Exception as e:
        return f"❌ 錯誤: {str(e)}"

# ═══════════════════════════════════════════════════════════════════════
# 基本命令
# ═══════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """🎯 *FlowAI 交易系統 v5.1*
━━━━━━━━━━━━━━━━━━━━━
📊 *市場分析*
/btc - BTC 即時分析
/eth - ETH 分析
/sol - SOL 分析
/radar - 全景報告
/gold - 黃金分析

📈 *進階分析*
/flow - Order Flow 分析
/signal - 交易信號
/funding - 資金費率
/arb - 套利計算器
/liq - 清算地圖
/calendar - 財經日曆

💰 *交易功能* ⚠️需VPS
/balance - 查詢餘額
/position - 查詢持倉

⚙️ *系統*
/status - 系統狀態
━━━━━━━━━━━━━━━━━━━━━
_FlowAI v5.1 - Order Flow 交易系統_"""
    await update.message.reply_text(welcome, parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════════════════
# 價格查詢
# ═══════════════════════════════════════════════════════════════════════

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔶 正在獲取 BTC 數據...")
    
    ticker = await trader.get_ticker(symbol="BTCUSDT")
    fng = await get_fear_greed_index()
    
    if ticker.get("retCode") == 0:
        data = ticker["result"]["list"][0]
        price = float(data["lastPrice"])
        change = float(data["price24hPcnt"]) * 100
        
        fng_value = fng.get("value", "N/A") if fng else "N/A"
        fng_text = fng.get("value_classification", "") if fng else ""
        
        prompt = f"""BTC 即時數據：
價格：${price:,.2f}
24h 漲跌：{change:+.2f}%
恐懼貪婪指數：{fng_value} ({fng_text})

用繁體中文分析（100字內）：
1. 市場情緒解讀
2. 短線方向判斷
3. 關鍵支撐/阻力價位"""
        
        analysis = await call_grok(prompt)
        
        result = f"""🔶 *BTC/USDT*
━━━━━━━━━━━━━━━━
💰 價格：${price:,.2f}
📊 24h：{change:+.2f}%
😱 恐懼貪婪：{fng_value} ({fng_text})
⏰ {datetime.now().strftime('%H:%M:%S')}

📝 *AI 分析：*
{analysis}"""
    else:
        result = f"❌ 錯誤: {ticker.get('retMsg', '未知')}"
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def eth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔷 正在獲取 ETH 數據...")
    
    ticker = await trader.get_ticker(symbol="ETHUSDT")
    
    if ticker.get("retCode") == 0:
        data = ticker["result"]["list"][0]
        price = float(data["lastPrice"])
        change = float(data["price24hPcnt"]) * 100
        
        prompt = f"ETH 價格 ${price:,.2f}，24h {change:+.2f}%。用繁體中文簡短分析市場情緒和短線方向（50字內）"
        analysis = await call_grok(prompt)
        
        result = f"""🔷 *ETH/USDT*
━━━━━━━━━━━━━━━━
💰 ${price:,.2f}
📊 {change:+.2f}%

📝 {analysis}"""
    else:
        result = f"❌ 錯誤: {ticker.get('retMsg')}"
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def sol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🟣 正在獲取 SOL 數據...")
    
    ticker = await trader.get_ticker(symbol="SOLUSDT")
    
    if ticker.get("retCode") == 0:
        data = ticker["result"]["list"][0]
        price = float(data["lastPrice"])
        change = float(data["price24hPcnt"]) * 100
        
        prompt = f"SOL 價格 ${price:,.2f}，24h {change:+.2f}%。用繁體中文簡短分析（50字內）"
        analysis = await call_grok(prompt)
        
        result = f"""🟣 *SOL/USDT*
━━━━━━━━━━━━━━━━
💰 ${price:,.2f}
📊 {change:+.2f}%

📝 {analysis}"""
    else:
        result = f"❌ 錯誤: {ticker.get('retMsg')}"
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """全景報告"""
    await update.message.reply_text("🌐 正在生成全景報告...")
    
    btc_ticker = await trader.get_ticker(symbol="BTCUSDT")
    eth_ticker = await trader.get_ticker(symbol="ETHUSDT")
    sol_ticker = await trader.get_ticker(symbol="SOLUSDT")
    fng = await get_fear_greed_index()
    
    msg = "🌐 *FlowAI 全景報告*\n━━━━━━━━━━━━━━━━\n"
    
    # 恐懼貪婪
    if fng:
        value = int(fng.get("value", 50))
        classification = fng.get("value_classification", "Neutral")
        emoji = "😱" if value < 25 else "😰" if value < 50 else "😐" if value < 75 else "🤑"
        msg += f"{emoji} 恐懼貪婪：{value} ({classification})\n\n"
    
    # 加密貨幣
    for name, ticker in [("BTC", btc_ticker), ("ETH", eth_ticker), ("SOL", sol_ticker)]:
        if ticker.get("retCode") == 0:
            data = ticker["result"]["list"][0]
            price = float(data["lastPrice"])
            change = float(data["price24hPcnt"]) * 100
            emoji = "🟢" if change >= 0 else "🔴"
            msg += f"{emoji} {name}: ${price:,.2f} ({change:+.1f}%)\n"
        else:
            msg += f"⚪ {name}: 獲取中...\n"
    
    msg += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """黃金分析 - 用 AI 獲取"""
    await update.message.reply_text("🥇 正在分析黃金...")
    
    prompt = """查詢現在 XAUUSD 黃金的即時價格，並用繁體中文分析：
1. 當前價格（美元/盎司）
2. 今日漲跌
3. 避險需求分析
4. 與美元/利率的關係
5. 短線方向建議

控制在 150 字內"""
    
    analysis = await call_grok(prompt)
    
    result = f"""🥇 *XAUUSD 黃金分析*
━━━━━━━━━━━━━━━━
{analysis}

⏰ {datetime.now().strftime('%H:%M:%S')}"""
    
    await update.message.reply_text(result, parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════════════════
# 進階分析
# ═══════════════════════════════════════════════════════════════════════

async def flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Order Flow 分析"""
    await update.message.reply_text("📊 正在分析 Order Flow...")
    
    ticker = await trader.get_ticker(symbol="BTCUSDT")
    fng = await get_fear_greed_index()
    
    if ticker.get("retCode") == 0:
        data = ticker["result"]["list"][0]
        price = float(data["lastPrice"])
        change = float(data["price24hPcnt"]) * 100
        fng_value = int(fng.get("value", 50)) if fng else 50
        
        prompt = f"""作為 Order Flow 交易專家，分析 BTC：

數據：
- 價格：${price:,.2f}
- 24h 漲跌：{change:+.2f}%
- 恐懼貪婪：{fng_value}

用繁體中文分析（150字內）：
1. 大單動向推測（機構買/賣壓力）
2. 資金流向（多/空主導）
3. 關鍵價位（支撐/阻力）
4. 短線操作建議"""
        
        analysis = await call_grok(prompt)
        
        result = f"""📊 *Order Flow 分析*
━━━━━━━━━━━━━━━━
💰 BTC: ${price:,.2f} ({change:+.2f}%)
😱 恐懼貪婪: {fng_value}

🔍 *大單分析：*
{analysis}"""
    else:
        result = f"❌ 錯誤: {ticker.get('retMsg')}"
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """交易信號"""
    await update.message.reply_text("🎯 正在生成交易信號...")
    
    btc = await trader.get_ticker(symbol="BTCUSDT")
    fng = await get_fear_greed_index()
    
    if btc.get("retCode") == 0:
        btc_price = float(btc["result"]["list"][0]["lastPrice"])
        btc_change = float(btc["result"]["list"][0]["price24hPcnt"]) * 100
        fng_value = int(fng.get("value", 50)) if fng else 50
        
        prompt = f"""作為交易信號分析師，給出 BTC 具體建議：

BTC: ${btc_price:,.2f} ({btc_change:+.2f}%)
恐懼貪婪: {fng_value}

用繁體中文給出：
1. 信號方向：🟢做多 / 🔴做空 / 🟡觀望
2. 建議進場價位
3. 止損價位
4. 目標價位（TP1, TP2）
5. 倉位建議（輕倉/中倉/重倉）
6. 信心指數 (1-10)

格式清晰，100字內"""
        
        analysis = await call_grok(prompt)
        
        result = f"""🎯 *交易信號*
━━━━━━━━━━━━━━━━
💰 BTC: ${btc_price:,.2f} ({btc_change:+.2f}%)
😱 恐懼貪婪: {fng_value}
⏰ {datetime.now().strftime('%H:%M:%S')}

📡 *信號：*
{analysis}

⚠️ _僅供參考，DYOR_"""
    else:
        result = f"❌ 錯誤: {btc.get('retMsg')}"
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """資金費率"""
    await update.message.reply_text("💸 正在分析資金費率...")
    
    prompt = """查詢現在 BTC 和 ETH 在 Binance/Bybit 的永續合約資金費率，並分析：

用繁體中文回答：
1. BTC 資金費率（%）
2. ETH 資金費率（%）
3. 費率解讀（正=多頭付空頭，負=空頭付多頭）
4. 套利機會分析
5. 費率異常警示（如有）

100字內"""
    
    analysis = await call_grok(prompt)
    
    result = f"""💸 *資金費率分析*
━━━━━━━━━━━━━━━━
{analysis}

📖 *套利說明：*
正費率 → 做空收錢
負費率 → 做多收錢

💡 用 /arb [本金] 計算收益
⏰ {datetime.now().strftime('%H:%M:%S')}"""
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def arb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """資金費率套利計算器"""
    principal = 300000  # 預設 NT$300K
    if context.args:
        try:
            principal = float(context.args[0])
        except:
            pass
    
    await update.message.reply_text(f"💰 計算 NT${principal:,.0f} 套利收益...")
    
    # 假設平均費率 0.01%
    rate = 0.01
    
    daily_rate = rate * 3
    monthly_rate = daily_rate * 30
    annual_rate = daily_rate * 365
    
    daily_profit = principal * (daily_rate / 100)
    monthly_profit = principal * (monthly_rate / 100)
    annual_profit = principal * (annual_rate / 100)
    
    usd_principal = principal / 32
    
    result = f"""💰 *資金費率套利計算器*
━━━━━━━━━━━━━━━━
📊 假設 BTC 資金費率：{rate:.4f}%/8h

💵 *本金：NT${principal:,.0f}* (≈${usd_principal:,.0f})

📈 *預估收益：*
├ 日收益：NT${daily_profit:,.0f}
├ 月收益：NT${monthly_profit:,.0f}
└ 年收益：NT${annual_profit:,.0f}

📊 *年化報酬率：{annual_rate:.1f}%*

⚠️ *注意事項：*
1. 需開等值多空對沖倉位
2. 費率會變動，收益不固定
3. 需扣除交易手續費 (~0.1%)
4. 高費率時機會更好

💡 用法：`/arb 500000`"""
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def liq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """清算地圖"""
    await update.message.reply_text("💥 正在分析清算風險...")
    
    ticker = await trader.get_ticker(symbol="BTCUSDT")
    
    if ticker.get("retCode") == 0:
        price = float(ticker["result"]["list"][0]["lastPrice"])
        
        prompt = f"""BTC 當前價格 ${price:,.2f}，分析清算風險：

用繁體中文回答（100字內）：
1. 上方主要清算區（空單清算價位）
2. 下方主要清算區（多單清算價位）
3. 哪邊清算量可能更大
4. 價格可能被吸引的方向
5. 風險警示"""
        
        analysis = await call_grok(prompt)
        
        result = f"""💥 *清算風險分析*
━━━━━━━━━━━━━━━━
💰 BTC: ${price:,.2f}

🔍 *清算地圖：*
{analysis}

⚠️ _基於 AI 推測，非即時數據_"""
    else:
        result = f"❌ 錯誤: {ticker.get('retMsg')}"
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """財經日曆"""
    await update.message.reply_text("📅 正在獲取財經事件...")
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    prompt = f"""今天是 {today}，列出本週重要財經事件：

用繁體中文，格式：
📅 日期 | 事件 | 重要性(1-5星)

包含：
1. 美國經濟數據（CPI、非農、GDP、PMI）
2. 聯準會相關（利率決議、官員講話）
3. 加密貨幣（代幣解鎖、重大會議、ETF）
4. 其他重大事件

最多 8 個，按重要性排序"""
    
    analysis = await call_grok(prompt)
    
    result = f"""📅 *本週財經日曆*
━━━━━━━━━━━━━━━━
{analysis}

⏰ 更新：{datetime.now().strftime('%H:%M')}
💡 重大事件可能引發波動"""
    
    await update.message.reply_text(result, parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════════════════
# 交易功能（需 VPS）
# ═══════════════════════════════════════════════════════════════════════

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    
    await update.message.reply_text("💰 正在查詢餘額...")
    result = await trader.get_wallet_balance()
    
    if result.get("retCode") == 0:
        coins = result.get("result", {}).get("list", [{}])[0].get("coin", [])
        msg = "💰 *Bybit 帳戶餘額*\n━━━━━━━━━━━━━━━━\n"
        total = 0
        for coin in coins:
            bal = float(coin.get("walletBalance", 0))
            if bal > 0:
                usd = float(coin.get("usdValue", 0))
                total += usd
                msg += f"💎 {coin['coin']}: {bal:.4f} (${usd:,.2f})\n"
        msg += f"\n💵 *總資產：${total:,.2f}*"
    else:
        msg = f"""❌ {result.get('retMsg', '錯誤')}

💡 *解決方案：*
雲端平台 IP 被 Bybit 封鎖
請使用 VPS 部署（如 DigitalOcean $4/月）"""
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    
    result = await trader.get_positions()
    
    if result.get("retCode") == 0:
        positions = result.get("result", {}).get("list", [])
        has_pos = False
        msg = "📊 *當前持倉*\n━━━━━━━━━━━━━━━━\n"
        for pos in positions:
            size = float(pos.get("size", 0))
            if size > 0:
                has_pos = True
                pnl = float(pos.get("unrealisedPnl", 0))
                emoji = "🟢" if pnl >= 0 else "🔴"
                msg += f"{emoji} {pos['symbol']} {pos['side']}: {size}\n   盈虧: ${pnl:,.2f}\n"
        if not has_pos:
            msg = "📊 目前無持倉"
    else:
        msg = f"""❌ {result.get('retMsg')}

💡 雲端 IP 被封鎖，請用 VPS 部署"""
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def long_btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    
    await update.message.reply_text("""⚠️ *交易功能需要 VPS 部署*

雲端平台 (Railway/Render) 的 IP 被 Bybit 封鎖

💡 *解決方案：*
使用 VPS（如 DigitalOcean $4/月）
詳見部署指南""", parse_mode='Markdown')

async def short_btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    
    await update.message.reply_text("""⚠️ *交易功能需要 VPS 部署*

雲端平台 IP 被 Bybit 封鎖

💡 使用 VPS 解鎖完整功能""", parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"""⚙️ *FlowAI 系統狀態*
━━━━━━━━━━━━━━━━
🤖 Grok API: {"✅" if GROK_API_KEY else "❌"}
📊 價格來源: CoinCap ✅
💹 交易 API: Bybit ⚠️需VPS

👤 Admin: {ADMIN_CHAT_ID}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 *版本：v5.1 (雲端版)*

💡 *功能狀態：*
✅ 價格查詢（BTC/ETH/SOL）
✅ AI 分析（Grok）
✅ 資金費率分析
✅ 套利計算器
⚠️ 餘額/持倉/下單 (需VPS)"""
    await update.message.reply_text(msg, parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════════════════
# 主程序
# ═══════════════════════════════════════════════════════════════════════

def main():
    if not TELEGRAM_TOKEN:
        print("❌ 請設置 TELEGRAM_TOKEN")
        return
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # 基本
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    
    # 價格
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("eth", eth))
    app.add_handler(CommandHandler("sol", sol))
    app.add_handler(CommandHandler("radar", radar))
    app.add_handler(CommandHandler("gold", gold))
    
    # 進階
    app.add_handler(CommandHandler("flow", flow))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("funding", funding))
    app.add_handler(CommandHandler("arb", arb))
    app.add_handler(CommandHandler("liq", liq))
    app.add_handler(CommandHandler("calendar", calendar))
    
    # 交易
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("position", position))
    app.add_handler(CommandHandler("long", long_btc))
    app.add_handler(CommandHandler("short", short_btc))
    
    print("🚀 FlowAI v5.1 啟動！")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
