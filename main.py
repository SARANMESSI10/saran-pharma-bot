from fastapi import FastAPI, Request
import requests
import os
import json
from datetime import datetime

app = FastAPI()

# ENV VARS
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")

watchlist = ["Divi’s Labs", "Aurobindo Pharma", "Natco Pharma"]

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload)

# 🔍 NOTION QUERY
def query_notion(filter_by=None, max_results=5):
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    body = {
        "page_size": max_results,
        "sorts": [{"timestamp": "created_time", "direction": "descending"}]
    }

    if filter_by == "risk_high":
        body["filter"] = {
            "property": "Risk Level",
            "select": {
                "equals": "High"
            }
        }

    res = requests.post(url, headers=headers, json=body)
    data = res.json()
    return data.get("results", [])

# 🔄 FORMAT ENTRY
def format_entry(entry):
    props = entry["properties"]
    company = props["Company"]["title"][0]["text"]["content"]
    event = props["Event Type"]["select"]["name"]
    date = props["Date"]["date"]["start"]
    risk = props["Risk Level"]["select"]["name"]
    source = props["Source"]["url"]
    action = props["Suggested Action"]["rich_text"][0]["text"]["content"]
    notes = props["SARAH Notes"]["rich_text"][0]["text"]["content"]

    return f"""
🧠 *Latest Alert Logged*

🏢 *Company*: {company}
📆 *Date*: {date}
📊 *Event*: {event}
⚠️ *Risk*: {risk}
🎯 *Action*: {action}
🔗 *Source*: [Link]({source})

📝 *Notes*: {notes}
""".strip()

# 📬 ROUTE
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    text = message.get("text", "").strip()
    
    if text == "/start":
        send_message("👋 Hello BOSS! SARAH is online.\nUse /help to see commands.")
    
    elif text == "/help":
        send_message("""🧠 *Available Commands*:
/start – Restart SARAH
/help – Show this menu
/watchlist – Show tracked stocks
/alerts – (soon)
/last – Last Notion alert
/summary – Last 5 alerts
/risk high – Show high-risk events
/nextbuy – Suggest buyable panic drops
/addstock XYZ – Add new stock to memory
""")

    elif text == "/watchlist":
        send_message("📋 Tracked Stocks:\n" + "\n".join([f"✅ {w}" for w in watchlist]))

    elif text.startswith("/addstock"):
        parts = text.split(" ", 1)
        if len(parts) == 2:
            stock = parts[1].strip()
            watchlist.append(stock)
            send_message(f"➕ Added *{stock}* to your tracked list.")
        else:
            send_message("⚠️ Use `/addstock StockName`")

    elif text == "/last":
        results = query_notion(max_results=1)
        if results:
            send_message(format_entry(results[0]))
        else:
            send_message("⚠️ No entries found in Notion.")

    elif text == "/summary":
        results = query_notion(max_results=5)
        if results:
            for entry in results:
                send_message(format_entry(entry))
        else:
            send_message("⚠️ No recent alerts found.")

    elif text == "/risk high":
        results = query_notion(filter_by="risk_high")
        if results:
            for entry in results:
                send_message(format_entry(entry))
        else:
            send_message("✅ No high-risk events currently logged.")

    elif text == "/nextbuy":
        results = query_notion(max_results=5)
        found = []
        for r in results:
            if "buy" in r["properties"]["Suggested Action"]["rich_text"][0]["text"]["content"].lower():
                found.append(format_entry(r))
        if found:
            for f in found:
                send_message(f)
        else:
            send_message("📉 No buy-worthy alerts found at the moment.")

    return {"ok": True}

@app.get("/")
def root():
    return {"message": "SARAH Pharma Bot is Live"}
