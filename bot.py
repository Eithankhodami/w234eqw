import os
import json
import base64
import logging
from flask import Flask, request
from google.oauth2.service_account import Credentials
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Environment variable validation at startup
required_vars = ["TELEGRAM_TOKEN", "GOOGLE_CREDS_B64"]
missing_vars = [var for var in required_vars if not os.environ.get(var)]

if missing_vars:
    error_message = f"Missing required environment variables: {', '.join(missing_vars)}"
    logger.error(f"❌ {error_message}")
    
    # We'll continue initialization to allow the app to start,
    # but the bot won't work until variables are set

# Initialize bot components with error handling
try:
    # Get credentials from environment
    if "GOOGLE_CREDS_B64" in os.environ:
        creds_json = base64.b64decode(os.environ["GOOGLE_CREDS_B64"]).decode("utf-8")
        creds_dict = json.loads(creds_json)
        
        # Initialize Google Sheets
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        from gspread import authorize
        client = authorize(creds)
        
        # Get sheet name from environment or use default
        sheet_name = os.environ.get("SHEET_NAME", "Secondment Sheet")
        spreadsheet = client.open(sheet_name)
        
        # Get the worksheet
        try:
            worksheet = spreadsheet.worksheet("Expenses")
        except:
            worksheet = spreadsheet.sheet1
        
        # Ensure headers exist
        if worksheet.row_count == 0:
            worksheet.append_row(["Date", "Location", "Amount", "Category", "Reference", "Type", "Receipt"])
            
        sheet = worksheet
        logger.info(f"✅ Connected to Google Sheet: {sheet_name}")
    else:
        sheet = None
        logger.error("❌ GOOGLE_CREDS_B64 environment variable is missing")
    
    # Initialize Telegram bot
    if "TELEGRAM_TOKEN" in os.environ:
        TOKEN = os.environ["TELEGRAM_TOKEN"]
        bot = Bot(token=TOKEN)
        logger.info("✅ Telegram bot initialized")
    else:
        TOKEN = None
        bot = None
        logger.error("❌ TELEGRAM_TOKEN environment variable is missing")
        
except Exception as e:
    logger.exception(f"❌ Error during initialization: {e}")
    sheet = None
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    bot = Bot(token=TOKEN) if TOKEN else None

# Define /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Expense Tracker Bot!\n\n"
        "Send your expense in this format:\n"
        "2025-04-04, Berlin, 15.50, Food, R123, work, upload_later\n\n"
        "Format: Date, Location, Amount, Category, Reference, Type, Receipt"
    )

# Handle normal messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not sheet:
        await update.message.reply_text(
            "⚠️ Bot is not properly connected to Google Sheets. Please try again later or contact the administrator."
        )
        return
    
    try:
        text = update.message.text.strip()
        parts = [x.strip() for x in text.split(",")]
        
        if len(parts) != 7:
            await update.message.reply_text(
                "⚠️ Please send exactly 7 comma-separated items.\n\n"
                "Format: Date, Location, Amount, Category, Reference, Type, Receipt\n\n"
                "For example: 2025-04-04, Berlin, 15.50, Food, R123, work, upload_later"
            )
            return
        
        sheet.append_row(parts)
        
        await update.message.reply_text(
            f"✅ Expense recorded successfully!\n\n"
            f"📅 Date: {parts[0]}\n"
            f"📍 Location: {parts[1]}\n"
            f"💰 Amount: {parts[2]}\n"
            f"🏷️ Category: {parts[3]}\n"
            f"🔢 Reference: {parts[4]}\n"
            f"📋 Type: {parts[5]}\n"
            f"🧾 Receipt: {parts[6]}"
        )
    except Exception as e:
        logger.exception("Error handling message:")
        await update.message.reply_text(
            "⚠️ Something went wrong while processing your input. Please try again later."
        )

# Create application with error handling
if TOKEN:
    try:
        application = Application.builder().token(TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("✅ Telegram application initialized")
    except Exception as e:
        logger.exception(f"❌ Failed to initialize Telegram application: {e}")
        application = None
else:
    application = None
    logger.error("❌ Cannot initialize Telegram application: missing token")

# Webhook for Railway
@app.route(f"/{TOKEN}" if TOKEN else "/webhook", methods=["POST"])
async def webhook():
    if not application or not bot:
        logger.error("❌ Webhook called but application is not initialized")
        return "bot not initialized", 500
        
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        await application.process_update(update)
        return "ok"
    except Exception as e:
        logger.exception(f"❌ Error processing webhook: {e}")
        return "error", 500

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    status = {
        "status": "healthy" if sheet and bot and application else "unhealthy",
        "google_sheets": "connected" if sheet else "disconnected",
        "telegram_bot": "connected" if bot else "disconnected",
        "application": "initialized" if application else "failed",
        "environment_variables": {
            "TELEGRAM_TOKEN": "set" if os.environ.get("TELEGRAM_TOKEN") else "missing",
            "GOOGLE_CREDS_B64": "set" if os.environ.get("GOOGLE_CREDS_B64") else "missing",
            "SHEET_NAME": os.environ.get("SHEET_NAME", "Secondment Sheet (default)")
        }
    }
    return json.dumps(status)

# Debug endpoint (disabled in production)
@app.route("/debug", methods=["GET"])
def debug():
    if os.environ.get("ENVIRONMENT") == "development":
        env_vars = {k: "***" if k in ["TELEGRAM_TOKEN", "GOOGLE_CREDS_B64"] else v[:10] + "..." 
                   for k, v in os.environ.items()}
        return json.dumps({"env": env_vars})
    return "Disabled in production", 403

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    logger.info(f"✅ Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)