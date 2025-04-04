import logging
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Load Google service account credentials from environment variable
creds_info = json.loads(os.environ["GOOGLE_CREDS_JSON"])
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

# Connect to Sheets and Drive
client = gspread.authorize(creds)
sheet = client.open("Secondment Sheet").sheet1
drive_service = build("drive", "v3", credentials=creds)
FOLDER_ID = "10oET0doyJHwuF68Xi4su8A9xXHTPeRkN"  # your receipt folder ID

# In-memory store for tracking last expense before image
last_expense_data = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Send me your expense in this format:\n"
        "<code>2025-04-04, Berlin, 15.50, Food, R123, work, upload_later</code>"
    )

# Expense message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message.text.strip()
        parts = [x.strip() for x in message.split(",")]
        if len(parts) != 7:
            await update.message.reply_text("Invalid format. Please send exactly 7 items separated by commas.")
            return

        sheet.append_row(parts)
        last_expense_data[update.message.chat_id] = parts
        await update.message.reply_text("Expense recorded. You can now send the receipt image.")
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await update.message.reply_text("Something went wrong. Check the format or try again.")

# Photo upload
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in last_expense_data:
        await update.message.reply_text("Please send the expense details first before sending the receipt.")
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = f"/tmp/temp_{chat_id}.jpg"
    await file.download_to_drive(file_path)

    # Build filename and upload
    date = last_expense_data[chat_id][0]
    amount = last_expense_data[chat_id][2].replace(".", "_")
    filename = f"{date}-{amount}.jpg"

    file_metadata = {"name": filename, "parents": [FOLDER_ID]}
    media = MediaFileUpload(file_path, mimetype="image/jpeg")
    uploaded = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = uploaded.get("id")
    file_link = f"https://drive.google.com/uc?id={file_id}"

    os.remove(file_path)

    # Update Upload column with clickable link
    row = len(sheet.get_all_values())
    hyperlink = f'=HYPERLINK("{file_link}", "receipt")'
    sheet.update_cell(row, 7, hyperlink)

    await update.message.reply_text("Receipt uploaded and linked to the sheet.")

# Main
if __name__ == "__main__":
    TOKEN = os.environ["TOKEN"]
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot is running...")
    app.run_polling()
