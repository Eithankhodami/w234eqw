import os
import json
import base64
import logging
import gspread
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import CommandHandler, Dispatcher, CallbackContext

# Decode and set up Google credentials
if "GOOGLE_CREDS_B64" in os.environ:
    creds_b64 = os.environ["GOOGLE_CREDS_B64"]
    creds_json = base64.b64decode(creds_b64).decode("utf-8")
    with open("credentials.json", "w") as f:
        f.write(creds_json)
else:
    print("❌ GOOGLE_CREDS_B64 is missing in the environment.")
    print("🔍 Available environment variables:", list(os.environ.keys()))
    raise RuntimeError("GOOGLE_CREDS_B64 not found. Deployment aborted.")

gc = gspread.service_account(filename="credentials.json")
sheet = gc.open("Spendings").sheet1  # Adjust if your sheet has a different name

# Set up Flask and Telegram bot
app = Flask(__name__)
bot = Bot(token=os.environ["TOKEN"])
dispatcher = Dispatcher(bot, None, workers=0)

# Define /start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to SpendBot! Send your expense in the format:\n`Coffee 3.5`")

# Define handler for messages
def handle_message(update: Update, context: CallbackContext):
    try:
        parts = update.message.text.strip().split(" ", 1)
        item = parts[0]
        cost = float(parts[1])
        sheet.append_row([item, cost])
        update.message.reply_text(f"✅ Logged: {item} - ${cost}")
    except Exception as e:
        update.message.reply_text("⚠️ Please use format: `Item 9.99`")

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", start))
dispatcher.add_handler(CommandHandler("expense", handle_message))

# Set up webhook endpoint
@app.route(f"/{os.environ['TOKEN']}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# For Railway, use this PORT
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=PORT)
