from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")

def send_message(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

@app.get("/")
async def root():
    return {"message": "SARAH Bot is Live"}

@app.post("/webhook")
async def receive_webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    text = message.get("text", "")
    if text == "/start":
        send_message("👋 Hello BOSS! SARAH is online.\nUse `/alerts`, `/watchlist`, or `/help` anytime.")
    elif text == "/alerts":
        send_message("📡 No new alerts yet. SARAH will notify you if something critical happens.")
    elif text == "/watchlist":
        send_message("📋 Tracked Stocks: Divi’s Labs, Aurobindo, Natco Pharma")
    elif text == "/help":
        send_message("🛠 Available commands:\n/start\n/alerts\n/watchlist\n/last\n/help")
    elif text == "/last":
        send_message("🧠 Last Notion Entry: [placeholder]. Auto-sync will be added soon.")
    return {"ok": True}
