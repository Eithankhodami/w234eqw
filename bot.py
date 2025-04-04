import os
import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Load credentials
creds_info = json.loads(os.environ["GOOGLE_CREDS_JSON"])
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("Secondment Sheet").sheet1

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received /start command from %s", update.effective_user.username)
    await update.message.reply_text(
        "Hi! Send your expense like:\n2025-04-04, Berlin, 10.50, Food, R1, tag, upload_later"
    )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received message: %s", update.message.text)
    parts = [x.strip() for x in update.message.text.strip().split(",")]
    if len(parts) != 7:
        await update.message.reply_text("Send exactly 7 items separated by commas.")
        return

    sheet.append_row(parts)
    await update.message.reply_text("Expense recorded.")

if __name__ == "__main__":
    TOKEN = os.environ["TOKEN"]
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running with polling...")
    app.run_polling()
