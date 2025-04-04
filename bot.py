import os
import json
import sys
import logging
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Load environment variables ===

# Get Google credentials from environment
GOOGLE_CREDS_ENV = os.environ.get("GOOGLE_CREDS_JSON")

if not GOOGLE_CREDS_ENV:
    print("❌ GOOGLE_CREDS_JSON is missing in the environment.", file=sys.stderr)
    print("🔍 Available environment variables:", list(os.environ.keys()), file=sys.stderr)
    raise RuntimeError("GOOGLE_CREDS_JSON not found. Deployment aborted.")

# Parse credentials and set up Google Sheets
creds_info = json.loads(GOOGLE_CREDS_ENV)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("Secondment Sheet").sheet1

# === Telegram Bot Handlers ===

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("✅ Received /start command from %s", update.effective_user.username)
    await update.message.reply_text(
        "Hi! Send your expense in this format:\n"
        "2025-04-04, Berlin, 15.50, Food, R123, work, upload_later"
    )

# Text message handler for adding data
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    logger.info("📥 Received message: %s", text)
    parts = [x.strip() for x in text.split(",")]
    
    if len(parts) != 7:
        await update.message.reply_text("⚠️ Invalid format. Please send 7 comma-separated values.")
        return

    try:
        sheet.append_row(parts)
        await update.message.reply_text("✅ Expense recorded.")
    except Exception as e:
        logger.error("❌ Failed to append to sheet: %s", e)
        await update.message.reply_text("❌ Failed to record expense. Please try again.")

# === Main bot entry ===

if __name__ == "__main__":
    TOKEN = os.environ.get("TOKEN")

    if not TOKEN:
        print("❌ TOKEN not set in environment variables.", file=sys.stderr)
        sys.exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 Bot is running via polling...")
    app.run_polling()
