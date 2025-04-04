import os
import json
import base64
import logging
from pathlib import Path
import gspread
from flask import Flask, request
from google.oauth2.service_account import Credentials
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Credentials handling - with multiple fallback options
def get_google_creds():
    # Option 1: Try environment variable (your current approach)
    if "GOOGLE_CREDS_B64" in os.environ:
        try:
            creds_json = base64.b64decode(os.environ["GOOGLE_CREDS_B64"]).decode("utf-8")
            creds_dict = json.loads(creds_json)
            logger.info("✅ Using credentials from GOOGLE_CREDS_B64 environment variable")
            return creds_dict
        except Exception as e:
            logger.warning(f"⚠️ Failed to decode GOOGLE_CREDS_B64: {e}")
    
    # Option 2: Try to load from credentials.json in the project root
    creds_path = Path("credentials.json")
    if creds_path.exists():
        try:
            with open(creds_path, "r") as f:
                creds_dict = json.load(f)
            logger.info("✅ Using credentials from credentials.json file")
            return creds_dict
        except Exception as e:
            logger.warning(f"⚠️ Failed to load credentials.json: {e}")
    
    # Option 3: Look for credentials in a 'secrets' directory
    creds_path = Path("secrets/google-credentials.json")
    if creds_path.exists():
        try:
            with open(creds_path, "r") as f:
                creds_dict = json.load(f)
            logger.info("✅ Using credentials from secrets/google-credentials.json file")
            return creds_dict
        except Exception as e:
            logger.warning(f"⚠️ Failed to load from secrets directory: {e}")
    
    # No valid credentials found
    logger.error("❌ No valid Google credentials found. Please provide credentials via environment variable or file.")
    raise RuntimeError("Google credentials are required to run this application.")

# Helper function to initialize the Google Sheet connection
def init_sheet():
    creds_dict = get_google_creds()
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    # Get the spreadsheet name from environment or use default
    sheet_name = os.environ.get("SHEET_NAME", "Secondment Sheet")
    try:
        spreadsheet = client.open(sheet_name)
        logger.info(f"✅ Connected to Google Sheet: {sheet_name}")
        # Get the first sheet or the one named "Expenses" if it exists
        try:
            worksheet = spreadsheet.worksheet("Expenses")
        except:
            worksheet = spreadsheet.sheet1
        
        # Ensure the sheet has headers
        if worksheet.row_count == 0:
            worksheet.append_row(["Date", "Location", "Amount", "Category", "Reference", "Type", "Receipt"])
            logger.info("✅ Added headers to empty sheet")
            
        return worksheet
    except Exception as e:
        logger.error(f"❌ Failed to open Google Sheet '{sheet_name}': {e}")
        raise

# Get Telegram token with fallbacks
def get_telegram_token():
    # Try multiple environment variable names
    for env_var in ["TOKEN", "TELEGRAM_TOKEN", "BOT_TOKEN", "TELEGRAM_BOT_TOKEN"]:
        if env_var in os.environ and os.environ[env_var]:
            logger.info(f"✅ Using Telegram token from {env_var} environment variable")
            return os.environ[env_var]
    
    # Try loading from token.txt
    token_path = Path("token.txt")
    if token_path.exists():
        try:
            token = token_path.read_text().strip()
            if token:
                logger.info("✅ Using Telegram token from token.txt file")
                return token
        except Exception as e:
            logger.warning(f"⚠️ Failed to read token.txt: {e}")
    
    logger.error("❌ No Telegram token found. Please set TOKEN environment variable or create token.txt file.")
    raise RuntimeError("Telegram token is required to run this application.")

# Initialize Flask and Telegram bot
app = Flask(__name__)

try:
    # Initialize the sheet connection at startup
    sheet = init_sheet()
    TOKEN = get_telegram_token()
    bot = Bot(token=TOKEN)
    logger.info("✅ Bot initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize: {e}")
    # Let the application start anyway to show the error in logs
    sheet = None
    bot = None

# Define /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Expense Tracker Bot!\n\n"
        "Send your expense in this format:\n"
        "2025-04-04, Berlin, 15.50, Food, R123, work, upload_later\n\n"
        "Format: Date, Location, Amount, Category, Reference, Type, Receipt"
    )

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not sheet:
        await update.message.reply_text(
            "⚠️ Bot is not properly connected to Google Sheets. Please contact the administrator."
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
        
        # Add the data to the sheet
        sheet.append_row(parts)
        
        # Provide detailed confirmation
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
            "⚠️ Something went wrong while processing your input. Please try again or contact support."
        )

# Create application with error handling
def create_application():
    try:
        application = Application.builder().token(TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", start))
        
        # Add a message handler for processing expenses
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("✅ Telegram application created successfully")
        return application
    except Exception as e:
        logger.error(f"❌ Failed to create Telegram application: {e}")
        return None

# Initialize the application
application = create_application()

# Webhook for Railway
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    if application:
        update = Update.de_json(request.get_json(force=True), bot)
        await application.process_update(update)
    else:
        logger.error("❌ Webhook called but application is not initialized")
    return "ok"

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    status = {
        "status": "healthy" if sheet and bot and application else "unhealthy",
        "google_sheets": "connected" if sheet else "disconnected",
        "telegram_bot": "connected" if bot else "disconnected",
        "application": "initialized" if application else "failed"
    }
    return json.dumps(status)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    logger.info(f"✅ Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)