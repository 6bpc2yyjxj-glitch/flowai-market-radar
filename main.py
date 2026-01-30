import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import urllib3
urllib3.disable_warnings()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def call_grok(prompt, use_web=False):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROK_API_KEY}"}
    tools = [{"type": "x_search"}]
    if use_web:
        tools.append({"type": "web_search"})
    data = {"model": "grok-4-1-fast", "input": prompt, "tools": tools}
    try:
        r = requests.post("https://api.x.ai/v1/responses", headers=headers, json=data, timeout=120)
        if r.status_code == 200:
            for item in r.json().get('output', []):
                if item.get('type') == 'message':
                    for c in item.get('content', []):
                        if c.get('type') == 'output_text':
                            return c.get('text', '')
        return f"Error: {r.status_code}"
    except Exception as e:
        return f"Error: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 FlowAI 市場雷達 PRO\n\n/btc - BTC情緒\n/meme - MEME熱幣\n/gold - 黃金情緒\n/radar - 全景報告")

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 分析中...")
    result = call_grok("Search X for Bitcoin sentiment in last 2 hours. Give: sentiment score 0-100, bullish/bearish, top 3 topics, 2 KOL posts. Format in Chinese with emojis.")
    await update.message.reply_text(result)

async def meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 搜尋中...")
    result = call_grok("Search X for top 5 trending MEME coins in last 24h. List ticker, why trending, risk level. Format in Chinese.")
    await update.message.reply_text(result)

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 分析中...")
    result = call_grok("Search X and web for Gold XAUUSD sentiment. Give sentiment score, key drivers, support/resistance levels. Format in Chinese.", use_web=True)
    await update.message.reply_text(result)

async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 生成報告...")
    result = call_grok("Create market report: crypto sentiment, BTC/ETH/SOL summary, top MEME, gold outlook, risks. Format in Chinese.", use_web=True)
    await update.message.reply_text(result)

def main():
    if not TELEGRAM_TOKEN or not GROK_API_KEY:
        logger.error("Missing TELEGRAM_TOKEN or GROK_API_KEY")
        return
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("meme", meme))
    app.add_handler(CommandHandler("gold", gold))
    app.add_handler(CommandHandler("radar", radar))
    logger.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
