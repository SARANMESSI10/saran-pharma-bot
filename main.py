from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Alerts"

AIRTABLE_ENDPOINT = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"

headers = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

watchlist = ["Divi’s Labs", "Aurobindo Pharma", "Natco Pharma"]

# Telegram messenger
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload)

# Query Airtable
def fetch_records(max_records=5, risk_filter=None):
    params = {
        "maxRecords": max_records,
        "sort[0][field]": "Date",
        "sort[0][direction]": "desc"
    }
    if risk_filter:
        params["filterByFormula"] = f"{{Risk Level}}='{risk_filter}'"

    res = requests.get(AIRTABLE_ENDPOINT, headers=headers, params=params)
    return res.json().get("records", [])

def format_entry(entry):
    f = entry["fields"]
    return f"""
🧠 *SARAH Alert*

🏢 *Company*: {f.get('Company', 'N/A')}
📆 *Date*: {f.get('Date', 'N/A')}
📊 *Event*: {f.get('Event Type', 'N/A')}
⚠️ *Risk Level*: {f.get('Risk Level', 'N/A')}
🎯 *Suggested Action*: {f.get('Suggested Action', 'N/A')}
🔗 *Source*: [View]({f.get('Source', '')})

📝 *Notes*: {f.get('SARAH Notes', 'N/A')}
""".strip()

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    text = message.get("text", "").strip()

    if text == "/start":
        send_message("👋 Hello BOSS! SARAH is online. Use /help to see all commands.")
    elif text == "/help":
        send_message("""🧠 *SARAH Commands*:
/start – Restart SARAH
/help – List commands
/watchlist – Tracked stocks
/last – Last alert from Airtable
/summary – Last 5 alerts
/risk high – High-risk events
/nextbuy – Buy-worthy entries
/addstock XYZ – Add a stock""")

    elif text == "/watchlist":
        send_message("📋 Your Watchlist:\n" + "\n".join(f"✅ {s}" for s in watchlist))

    elif text.startswith("/addstock"):
        parts = text.split(" ", 1)
        if len(parts) == 2:
            stock = parts[1].strip()
            watchlist.append(stock)
            send_message(f"➕ Added *{stock}* to watchlist.")
        else:
            send_message("⚠️ Usage: `/addstock StockName`")

    elif text == "/last":
        records = fetch_records(1)
        if records:
            send_message(format_entry(records[0]))
        else:
            send_message("⚠️ No alerts found in Airtable.")

    elif text == "/summary":
        records = fetch_records(5)
        if records:
            for r in records:
                send_message(format_entry(r))
        else:
            send_message("⚠️ No alerts found.")

    elif text == "/risk high":
        records = fetch_records(10, risk_filter="High")
        if records:
            for r in records:
                send_message(format_entry(r))
        else:
            send_message("✅ No *high-risk* alerts at the moment.")

    elif text == "/nextbuy":
        records = fetch_records(10)
        found = []
        for r in records:
            action = r["fields"].get("Suggested Action", "").lower()
            if "buy" in action:
                found.append(r)
        if found:
            for r in found:
                send_message(format_entry(r))
        else:
            send_message("📉 No buy-worthy alerts currently.")

    return {"ok": True}

@app.get("/")
def root():
    return {"message": "SARAH Airtable Bot is Live"}
