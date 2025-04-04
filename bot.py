import logging
import os
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Logging for debugging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Setup Google API
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("expensebot-455818-95575d582770.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("Secondment Sheet").sheet1
drive_service = build("drive", "v3", credentials=creds)

# Replace this with your actual folder ID from Google Drive
FOLDER_ID = "10oET0doyJHwuF68Xi4su8A9xXHTPeRkN"

# Global to track last message data per user
last_expense_data = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Send me your expense in this format:\n"
        "<code>2025-04-04, Berlin, 15.50, Food, R123, work, upload_later</code>"
    )

# Handle plain text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_expense_data
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

# Handle photo uploads
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_expense_data
    chat_id = update.message.chat_id
    if chat_id not in last_expense_data:
        await update.message.reply_text("Please send the expense details first before sending the receipt.")
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = f"temp_{chat_id}.jpg"
    await file.download_to_drive(file_path)

    # Generate filename from date and amount
    date = last_expense_data[chat_id][0]
    amount = last_expense_data[chat_id][2].replace(".", "_")
    filename = f"{date}-{amount}.jpg"

    file_metadata = {
        "name": filename,
        "parents": [FOLDER_ID]
    }
    media = MediaFileUpload(file_path, mimetype="image/jpeg")
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = uploaded_file.get("id")
    file_link = f"https://drive.google.com/uc?id={file_id}"

    os.remove(file_path)

    # Update the last row's Upload column with the link
    records = sheet.get_all_values()
    last_row_index = len(records)
    hyperlink_formula = f'=HYPERLINK("{file_link}", "receipt")'
    sheet.update_cell(last_row_index, 7, hyperlink_formula)

    await update.message.reply_text("Receipt uploaded and linked in the sheet.")

# Main bot setup
if __name__ == "__main__":
    TOKEN = "7939992556:AAGUaWdemNJ31KiHBBvFhbuPFmZO1kUtWwo"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot is running...")
    app.run_polling()
