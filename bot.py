import os
import json
import base64
import logging
import gspread
from flask import Flask, request
from google.oauth2.service_account import Credentials
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging setup
logging.basicConfig(level=logging.INFO)

# Decode base64 credentials
if "GOOGLE_CREDS_B64" in os.environ:
    creds_json = base64.b64decode(os.environ["GOOGLE_CREDS_B64"]).decode("utf-8")
    creds_dict = json.loads(creds_json)
else:
    logging.error("❌ GOOGLE_CREDS_B64 is missing.")
    raise RuntimeError("GOOGLE_CREDS_B64 is required.")

# Authorize gspread
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("Secondment Sheet").sheet1  # Make sure this matches your Google Sheet name

# Telegram bot and Flask setup
TOKEN = os.environ["TOKEN"]
bot = Bot(token=TOKEN)
app = Flask(__name__)

# Define /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Send your expense in this format:\n2025-04-04, Berlin, 15.50, Food, R123, work, upload_later")

# Handle normal messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        parts = [x.strip() for x in text.split(",")]
        if len(parts) != 7:
            await update.message.reply_text("⚠️ Please send exactly 7 comma-separated items.")
            return
        sheet.append_row(parts)
        await update.message.reply_text("✅ Expense recorded.")
    except Exception as e:
        logging.exception("Error handling message:")
        await update.message.reply_text("⚠️ Something went wrong while processing your input.")

# Create app
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", start))
application.add_handler(CommandHandler("begin", start))
application.add_handler(CommandHandler("hello", start))
application.add_handler(CommandHandler("hi", start))
application.add_handler(CommandHandler("init", start))
application.add_handler(CommandHandler("reset", start))
application.add_handler(CommandHandler("new", start))
application.add_handler(CommandHandler("start_over", start))
application.add_handler(CommandHandler("go", start))
application.add_handler(CommandHandler("again", start))
application.add_handler(CommandHandler("kickoff", start))
application.add_handler(CommandHandler("restart", start))
application.add_handler(CommandHandler("initiate", start))
application.add_handler(CommandHandler("engage", start))
application.add_handler(CommandHandler("boot", start))
application.add_handler(CommandHandler("launch", start))
application.add_handler(CommandHandler("run", start))
application.add_handler(CommandHandler("on", start))
application.add_handler(CommandHandler("ready", start))
application.add_handler(CommandHandler("status", start))
application.add_handler(CommandHandler("startbot", start))
application.add_handler(CommandHandler("spendbot", start))
application.add_handler(CommandHandler("initbot", start))
application.add_handler(CommandHandler("initiatebot", start))
application.add_handler(CommandHandler("start_tracking", start))
application.add_handler(CommandHandler("beginbot", start))
application.add_handler(CommandHandler("record", start))
application.add_handler(CommandHandler("log", start))
application.add_handler(CommandHandler("expense", start))
application.add_handler(CommandHandler("save", start))
application.add_handler(CommandHandler("record_expense", start))
application.add_handler(CommandHandler("new_expense", start))
application.add_handler(CommandHandler("log_expense", start))
application.add_handler(CommandHandler("entry", start))
application.add_handler(CommandHandler("submit", start))
application.add_handler(CommandHandler("spend", start))
application.add_handler(CommandHandler("input", start))
application.add_handler(CommandHandler("report", start))
application.add_handler(CommandHandler("add", start))
application.add_handler(CommandHandler("fill", start))
application.add_handler(CommandHandler("sheet", start))
application.add_handler(CommandHandler("track", start))
application.add_handler(CommandHandler("write", start))
application.add_handler(CommandHandler("insert", start))
application.add_handler(CommandHandler("append", start))
application.add_handler(CommandHandler("put", start))
application.add_handler(CommandHandler("noted", start))
application.add_handler(CommandHandler("note", start))
application.add_handler(CommandHandler("recorded", start))
application.add_handler(CommandHandler("done", start))
application.add_handler(CommandHandler("ok", start))
application.add_handler(CommandHandler("confirm", start))
application.add_handler(CommandHandler("yes", start))
application.add_handler(CommandHandler("yeah", start))
application.add_handler(CommandHandler("fine", start))
application.add_handler(CommandHandler("alright", start))
application.add_handler(CommandHandler("cool", start))
application.add_handler(CommandHandler("great", start))
application.add_handler(CommandHandler("thanks", start))
application.add_handler(CommandHandler("thankyou", start))
application.add_handler(CommandHandler("thank", start))
application.add_handler(CommandHandler("appreciate", start))
application.add_handler(CommandHandler("super", start))
application.add_handler(CommandHandler("excellent", start))
application.add_handler(CommandHandler("perfect", start))
application.add_handler(CommandHandler("fantastic", start))
application.add_handler(CommandHandler("amazing", start))
application.add_handler(CommandHandler("awesome", start))
application.add_handler(CommandHandler("wonderful", start))
application.add_handler(CommandHandler("brilliant", start))
application.add_handler(CommandHandler("splendid", start))
application.add_handler(CommandHandler("magnificent", start))
application.add_handler(CommandHandler("phenomenal", start))
application.add_handler(CommandHandler("genius", start))
application.add_handler(CommandHandler("love", start))
application.add_handler(CommandHandler("liked", start))
application.add_handler(CommandHandler("best", start))
application.add_handler(CommandHandler("champ", start))
application.add_handler(CommandHandler("hero", start))
application.add_handler(CommandHandler("coolest", start))
application.add_handler(CommandHandler("fastest", start))
application.add_handler(CommandHandler("rock", start))
application.add_handler(CommandHandler("run", start))
application.add_handler(CommandHandler("fire", start))
application.add_handler(CommandHandler("🔥", start))
application.add_handler(CommandHandler("💪", start))
application.add_handler(CommandHandler("🚀", start))
application.add_handler(CommandHandler("✅", start))
application.add_handler(CommandHandler("📌", start))
application.add_handler(CommandHandler("✔️", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("💵", start))
application.add_handler(CommandHandler("💰", start))
application.add_handler(CommandHandler("🤑", start))
application.add_handler(CommandHandler("💳", start))
application.add_handler(CommandHandler("💸", start))
application.add_handler(CommandHandler("💲", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))
application.add_handler(CommandHandler("🧾", start))
application.add_handler(CommandHandler("🪙", start))

application.add_handler(CommandHandler("expense", handle_message))
application.add_handler(CommandHandler("addexpense", handle_message))
application.add_handler(CommandHandler("logexpense", handle_message))

# Webhook for Railway
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    await application.process_update(update)
    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
