"""
FlowAI 交易機器人 v5.0
完整版：即時價格 + AI 分析 + Bybit 交易 + 資金費率套利
"""

import os
import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import aiohttp

from bybit_trader import BybitTrader

# ═══════════════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════════════

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
    """黃金價格"""
    url = "https://api.metals.live/v1/spot/gold"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        return data[0] if isinstance(data, list) else data
    except:
        pass
    return None

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
    welcome = """🎯 *FlowAI 交易系統 v5.0*
━━━━━━━━━━━━━━━━━━━━━
📊 *市場分析*
/btc - BTC 即時分析
/eth - ETH 分析
/sol - SOL 分析
/radar - 全景報告
/gold - 黃金價格

📈 *進階分析*
/flow - Order Flow 分析
/signal - 交易信號
/funding - 資金費率
/arb - 套利計算器
/liq - 清算地圖
/calendar - 財經日曆

💰 *交易功能*
/balance - 查詢餘額
/position - 查詢持倉
/long - 做多 BTC
/short - 做空 BTC

⚙️ *系統*
/status - 系統狀態
/help - 完整說明
━━━━━━━━━━━━━━━━━━━━━
_FlowAI v5.0 - Order Flow 交易系統_"""
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """完整說明"""
    help_text = """📖 *FlowAI 完整功能說明*

🔹 **/btc** - BTC 即時價格 + AI 分析
🔹 **/eth** - ETH 即時價格 + AI 分析
🔹 **/sol** - SOL 即時價格 + AI 分析
🔹 **/radar** - 多幣種全景報告
🔹 **/gold** - XAUUSD 黃金價格

🔸 **/flow** - Order Flow 大單分析
🔸 **/signal** - 綜合交易信號
🔸 **/funding** - 多交易所資金費率
🔸 **/arb [本金]** - 資金費率套利計算
🔸 **/liq** - 清算風險分析
🔸 **/calendar** - 本週財經事件

💰 **/balance** - 查詢 Bybit 餘額
💰 **/position** - 查詢當前持倉
💰 **/long** - 做多 BTC
💰 **/short** - 做空 BTC

_所有分析由 Grok AI 提供_"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════════════════
# 價格查詢
# ═══════════════════════════════════════════════════════════════════════

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔶 正在獲取 BTC 數據...")
    
    ticker = await trader.get_ticker(symbol="BTCUSDT")
    funding = await trader.get_funding_rate(symbol="BTCUSDT")
    fng = await get_fear_greed_index()
    
    if ticker.get("retCode") == 0:
        data = ticker["result"]["list"][0]
        price = float(data["lastPrice"])
        change = float(data["price24hPcnt"]) * 100
        high = float(data["highPrice24h"])
        low = float(data["lowPrice24h"])
        
        funding_rate = "N/A"
        if funding.get("retCode") == 0 and funding["result"].get("list"):
            funding_rate = f"{float(funding['result']['list'][0]['fundingRate']) * 100:.4f}%"
        
        fng_value = fng.get("value", "N/A") if fng else "N/A"
        
        prompt = f"""BTC 即時數據：
價格：${price:,.2f}
24h 漲跌：{change:+.2f}%
24h 高：${high:,.2f}
24h 低：${low:,.2f}
資金費率：{funding_rate}
恐懼貪婪：{fng_value}

用繁體中文簡短分析（100字內）：
1. 市場情緒
2. 短線方向
3. 關鍵價位"""
        
        analysis = await call_grok(prompt)
        
        result = f"""🔶 *BTC/USDT 即時分析*
━━━━━━━━━━━━━━━━
💰 價格：${price:,.2f}
📊 24h：{change:+.2f}%
📈 高：${high:,.2f}
📉 低：${low:,.2f}
💸 資金費率：{funding_rate}
😱 恐懼貪婪：{fng_value}
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
    gold = await get_gold_price()
    
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
    
    # 黃金
    if gold:
        gold_price = float(gold.get("price", 0))
        msg += f"🥇 GOLD: ${gold_price:,.2f}\n"
    
    msg += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """黃金價格"""
    await update.message.reply_text("🥇 正在獲取黃金數據...")
    
    gold_data = await get_gold_price()
    
    if gold_data:
        price = float(gold_data.get("price", 0))
        
        prompt = f"黃金 XAUUSD 價格 ${price:,.2f}。用繁體中文分析：1. 避險需求 2. 美元走勢影響 3. 短線方向（80字內）"
        analysis = await call_grok(prompt)
        
        result = f"""🥇 *XAUUSD 黃金*
━━━━━━━━━━━━━━━━
💰 ${price:,.2f}
⏰ {datetime.now().strftime('%H:%M:%S')}

📝 *分析：*
{analysis}"""
    else:
        result = "❌ 無法獲取黃金價格"
    
    await update.message.reply_text(result, parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════════════════
# 進階分析
# ═══════════════════════════════════════════════════════════════════════

async def flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Order Flow 分析"""
    await update.message.reply_text("📊 正在分析 Order Flow...")
    
    ticker = await trader.get_ticker(symbol="BTCUSDT")
    funding = await trader.get_funding_rate(symbol="BTCUSDT")
    fng = await get_fear_greed_index()
    
    if ticker.get("retCode") == 0:
        data = ticker["result"]["list"][0]
        price = float(data["lastPrice"])
        volume = float(data.get("volume24h", 0))
        
        funding_rate = 0
        if funding.get("retCode") == 0 and funding["result"].get("list"):
            funding_rate = float(funding['result']['list'][0]['fundingRate']) * 100
        
        fng_value = int(fng.get("value", 50)) if fng else 50
        
        prompt = f"""作為 Order Flow 交易專家，分析 BTC：

數據：
- 價格：${price:,.2f}
- 24h 成交量：{volume:,.0f}
- 資金費率：{funding_rate:.4f}%
- 恐懼貪婪：{fng_value}

用繁體中文分析（150字內）：
1. 大單動向推測（機構買/賣壓力）
2. 資金流向（多/空主導）
3. 短線建議（具體價位）"""
        
        analysis = await call_grok(prompt)
        
        result = f"""📊 *Order Flow 分析*
━━━━━━━━━━━━━━━━
💰 BTC: ${price:,.2f}
📦 24h 量: {volume:,.0f}
💸 資金費率: {funding_rate:.4f}%
😱 恐懼貪婪: {fng_value}

🔍 *大單分析：*
{analysis}"""
    else:
        result = "❌ 獲取數據失敗"
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """交易信號"""
    await update.message.reply_text("🎯 正在生成交易信號...")
    
    btc = await trader.get_ticker(symbol="BTCUSDT")
    eth = await trader.get_ticker(symbol="ETHUSDT")
    fng = await get_fear_greed_index()
    
    if btc.get("retCode") == 0:
        btc_price = float(btc["result"]["list"][0]["lastPrice"])
        btc_change = float(btc["result"]["list"][0]["price24hPcnt"]) * 100
        eth_price = float(eth["result"]["list"][0]["lastPrice"]) if eth.get("retCode") == 0 else 0
        fng_value = int(fng.get("value", 50)) if fng else 50
        
        prompt = f"""作為交易信號分析師，給出具體建議：

BTC: ${btc_price:,.2f} ({btc_change:+.2f}%)
ETH: ${eth_price:,.2f}
恐懼貪婪: {fng_value}

用繁體中文給出（100字內）：
1. 信號：🟢做多 / 🔴做空 / 🟡觀望
2. 進場價位
3. 止損價位
4. 目標價位
5. 信心指數 (1-10)"""
        
        analysis = await call_grok(prompt)
        
        result = f"""🎯 *交易信號*
━━━━━━━━━━━━━━━━
💰 BTC: ${btc_price:,.2f} ({btc_change:+.2f}%)
😱 恐懼貪婪: {fng_value}
⏰ {datetime.now().strftime('%H:%M:%S')}

📡 *信號分析：*
{analysis}

⚠️ _僅供參考，請自行判斷風險_"""
    else:
        result = "❌ 獲取數據失敗"
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """資金費率"""
    await update.message.reply_text("💸 正在獲取資金費率...")
    
    btc_funding = await trader.get_funding_rate(symbol="BTCUSDT")
    eth_funding = await trader.get_funding_rate(symbol="ETHUSDT")
    
    msg = "💸 *資金費率 (Funding Rate)*\n━━━━━━━━━━━━━━━━\n"
    
    for name, funding in [("BTC", btc_funding), ("ETH", eth_funding)]:
        if funding.get("retCode") == 0 and funding["result"].get("list"):
            rate = float(funding['result']['list'][0]['fundingRate']) * 100
            annual = rate * 3 * 365  # 每8小時一次，一天3次
            emoji = "🟢" if rate > 0 else "🔴" if rate < 0 else "⚪"
            msg += f"{emoji} {name}: {rate:.4f}% (年化 {annual:.1f}%)\n"
        else:
            msg += f"⚪ {name}: N/A\n"
    
    msg += f"""
📖 *解讀：*
🟢 正費率 = 多頭付空頭（做空有利）
🔴 負費率 = 空頭付多頭（做多有利）

⏰ 每 8 小時結算一次
💡 用 /arb [本金] 計算套利收益"""
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def arb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """資金費率套利計算器"""
    # 獲取本金參數
    principal = 300000  # 預設 NT$300K
    if context.args:
        try:
            principal = float(context.args[0])
        except:
            pass
    
    await update.message.reply_text(f"💰 計算 NT${principal:,.0f} 套利收益...")
    
    btc_funding = await trader.get_funding_rate(symbol="BTCUSDT")
    
    if btc_funding.get("retCode") == 0 and btc_funding["result"].get("list"):
        rate = float(btc_funding['result']['list'][0]['fundingRate']) * 100
        
        # 計算
        daily_rate = abs(rate) * 3  # 每天3次
        monthly_rate = daily_rate * 30
        annual_rate = daily_rate * 365
        
        # 收益（假設 1:1 對沖）
        daily_profit = principal * (daily_rate / 100)
        monthly_profit = principal * (monthly_rate / 100)
        annual_profit = principal * (annual_rate / 100)
        
        # 轉換 USD (假設匯率 32)
        usd_principal = principal / 32
        
        result = f"""💰 *資金費率套利計算器*
━━━━━━━━━━━━━━━━
📊 當前 BTC 資金費率：{rate:.4f}%

💵 *本金：NT${principal:,.0f}* (≈${usd_principal:,.0f})

📈 *預估收益：*
├ 日收益：NT${daily_profit:,.0f}
├ 月收益：NT${monthly_profit:,.0f}
└ 年收益：NT${annual_profit:,.0f}

📊 *年化報酬率：{annual_rate:.1f}%*

⚠️ *注意事項：*
1. 需開等值多空對沖倉位
2. 費率會變動，收益不固定
3. 需扣除交易手續費
4. 建議在費率 >0.01% 時操作

💡 用法：/arb 500000 （計算50萬本金）"""
    else:
        result = "❌ 無法獲取資金費率"
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def liq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """清算地圖"""
    await update.message.reply_text("💥 正在分析清算風險...")
    
    ticker = await trader.get_ticker(symbol="BTCUSDT")
    
    if ticker.get("retCode") == 0:
        price = float(ticker["result"]["list"][0]["lastPrice"])
        
        prompt = f"""BTC 當前價格 ${price:,.2f}，分析清算風險：

用繁體中文回答（100字內）：
1. 上方主要清算區（多單）
2. 下方主要清算區（空單）
3. 哪邊清算量大
4. 價格可能往哪邊移動"""
        
        analysis = await call_grok(prompt)
        
        result = f"""💥 *清算風險分析*
━━━━━━━━━━━━━━━━
💰 BTC: ${price:,.2f}

🔍 *清算地圖：*
{analysis}

⚠️ _基於 AI 推測，非即時數據_"""
    else:
        result = "❌ 獲取數據失敗"
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """財經日曆"""
    await update.message.reply_text("📅 正在獲取財經事件...")
    
    prompt = f"""今天是 {datetime.now().strftime('%Y-%m-%d')}，列出本週重要財經事件：

用繁體中文回答，格式：
📅 日期 | 事件 | 重要性⭐

包含：
1. 美國經濟數據（CPI、就業、GDP等）
2. 聯準會相關
3. 加密貨幣相關（解鎖、會議等）

最多列出 8 個最重要的"""
    
    analysis = await call_grok(prompt)
    
    result = f"""📅 *本週財經日曆*
━━━━━━━━━━━━━━━━
{analysis}

⏰ 更新時間：{datetime.now().strftime('%H:%M')}
💡 重大事件可能影響市場波動"""
    
    await update.message.reply_text(result, parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════════════════
# 交易功能
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
        msg = f"❌ {result.get('retMsg', '錯誤')}\n\n💡 如在雲端運行，Bybit 可能封鎖 IP"
    
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
                entry = float(pos.get("avgPrice", 0))
                emoji = "🟢" if pnl >= 0 else "🔴"
                msg += f"""{emoji} *{pos['symbol']}* {pos['side']}
   數量: {size}
   進場: ${entry:,.2f}
   盈虧: ${pnl:,.2f}
"""
        if not has_pos:
            msg = "📊 目前無持倉"
    else:
        msg = f"❌ {result.get('retMsg')}\n\n💡 如在雲端運行，Bybit 可能封鎖 IP"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def long_btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    keyboard = [[
        InlineKeyboardButton("✅ 確認做多 0.001 BTC", callback_data="long_0.001"),
        InlineKeyboardButton("❌ 取消", callback_data="cancel")
    ]]
    await update.message.reply_text("🟢 確認做多 BTC？\n數量：0.001 BTC\n類型：市價單", reply_markup=InlineKeyboardMarkup(keyboard))

async def short_btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ 僅管理員可用")
        return
    keyboard = [[
        InlineKeyboardButton("✅ 確認做空 0.001 BTC", callback_data="short_0.001"),
        InlineKeyboardButton("❌ 取消", callback_data="cancel")
    ]]
    await update.message.reply_text("🔴 確認做空 BTC？\n數量：0.001 BTC\n類型：市價單", reply_markup=InlineKeyboardMarkup(keyboard))

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
        msg = f"✅ 做多成功！訂單ID: {result.get('result', {}).get('orderId', 'N/A')}" if result.get("retCode") == 0 else f"❌ {result.get('retMsg')}"
        await query.edit_message_text(msg)
    
    elif data.startswith("short_"):
        qty = data.split("_")[1]
        await query.edit_message_text("🔄 下單中...")
        result = await trader.place_order(symbol="BTCUSDT", side="Sell", qty=qty)
        msg = f"✅ 做空成功！訂單ID: {result.get('result', {}).get('orderId', 'N/A')}" if result.get("retCode") == 0 else f"❌ {result.get('retMsg')}"
        await query.edit_message_text(msg)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"""⚙️ *FlowAI 系統狀態*
━━━━━━━━━━━━━━━━
🔑 Bybit API: {"✅" if os.getenv("BYBIT_API_KEY") else "❌"}
🔐 RSA 私鑰: {"✅" if os.getenv("BYBIT_PRIVATE_KEY") else "❌"}
🤖 Grok API: {"✅" if GROK_API_KEY else "❌"}
👤 Admin ID: {ADMIN_CHAT_ID}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 *版本：v5.0*
🌐 價格來源：Binance
💹 交易執行：Bybit"""
    await update.message.reply_text(msg, parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════════════════
# 主程序
# ═══════════════════════════════════════════════════════════════════════

def main():
    if not TELEGRAM_TOKEN:
        print("❌ 請設置 TELEGRAM_TOKEN")
        return
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # 基本命令
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status))
    
    # 價格查詢
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("eth", eth))
    app.add_handler(CommandHandler("sol", sol))
    app.add_handler(CommandHandler("radar", radar))
    app.add_handler(CommandHandler("gold", gold))
    
    # 進階分析
    app.add_handler(CommandHandler("flow", flow))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("funding", funding))
    app.add_handler(CommandHandler("arb", arb))
    app.add_handler(CommandHandler("liq", liq))
    app.add_handler(CommandHandler("calendar", calendar))
    
    # 交易功能
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("position", position))
    app.add_handler(CommandHandler("long", long_btc))
    app.add_handler(CommandHandler("short", short_btc))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("🚀 FlowAI v5.0 啟動！")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
