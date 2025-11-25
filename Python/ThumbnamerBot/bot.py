import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)

# ============================
TOKEN = "8418888891:AAEJ8EcVeh6N6TJkFX8J0bLKmBBnRdcLIng"
DATA_FILE = "user_data.json"
DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- ডাটা হ্যান্ডলার ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data_store = load_data()

def get_user_record(user_id):
    key = str(user_id)
    if key not in data_store:
        data_store[key] = {
            "last_pdf_id": None,
            "custom_name": None,
            "thumbnail_file_id": None,
            "awaiting_name": False,
            "awaiting_thumb": False
        }
    return data_store[key]

def set_user_thumbnail(user_id, file_id):
    rec = get_user_record(user_id)
    rec["thumbnail_file_id"] = file_id
    rec["awaiting_thumb"] = False
    save_data(data_store)

def set_user_custom_name(user_id, filename):
    rec = get_user_record(user_id)
    rec["custom_name"] = filename
    rec["awaiting_name"] = False
    save_data(data_store)
    return rec

def set_last_pdf(user_id, file_id):
    rec = get_user_record(user_id)
    rec["last_pdf_id"] = file_id
    save_data(data_store)

# --- হ্যান্ডলারস ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "স্বাগতম! \n\n"
        "PDF পাঠান → তারপর নাম বা থাম্বনেইল পরিবর্তন করতে পারবেন।"
    )

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        return
    if "pdf" not in (doc.mime_type or "").lower() and not (doc.file_name and doc.file_name.lower().endswith(".pdf")):
        await update.message.reply_text("দয়া করে একটি PDF ফাইল আপলোড করুন।")
        return

    user_id = update.effective_user.id
    set_last_pdf(user_id, doc.file_id)

    keyboard = [
        [InlineKeyboardButton("নাম পরিবর্তন করো ✏️", callback_data="rename")],
        [InlineKeyboardButton("থাম্বনেইল পরিবর্তন করো 🖼️", callback_data="thumbnail")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("আপনি কি এই PDF এর নাম বা থাম্বনেইল পরিবর্তন করতে চান?", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    rec = get_user_record(user_id)

    if query.data == "rename":
        rec["awaiting_name"] = True
        save_data(data_store)
        await query.message.reply_text("নতুন PDF নাম পাঠান:")

    elif query.data == "thumbnail":
        rec["awaiting_thumb"] = True
        save_data(data_store)
        await query.message.reply_text("নতুন থাম্বনেইল ছবি পাঠান:")

# --- PDF পাঠানোর ফাংশন ---
async def send_updated_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE, rec):
    if not rec.get("last_pdf_id"):
        return

    user_id = update.effective_user.id
    pdf_file_id = rec["last_pdf_id"]
    pdf_file = await context.bot.get_file(pdf_file_id)
    pdf_path = os.path.join(DOWNLOAD_DIR, f"{user_id}_original.pdf")
    await pdf_file.download_to_drive(pdf_path)

    thumbnail_path = None
    if rec.get("thumbnail_file_id"):
        thumb_file = await context.bot.get_file(rec["thumbnail_file_id"])
        thumbnail_path = os.path.join(DOWNLOAD_DIR, f"{user_id}_thumb.jpg")
        await thumb_file.download_to_drive(thumbnail_path)

    # ✅ এখানে 'with' ব্লক ঠিকভাবে ব্যবহার
    with open(pdf_path, "rb") as f:
        kwargs = {"chat_id": update.effective_chat.id, "document": InputFile(f, filename=rec.get("custom_name") or "Updated.pdf")}
        if thumbnail_path:
            with open(thumbnail_path, "rb") as t:
                kwargs["thumbnail"] = InputFile(t)
                await context.bot.send_document(**kwargs)
        else:
            await context.bot.send_document(**kwargs)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rec = get_user_record(user_id)

    if rec.get("awaiting_name"):
        text = update.message.text.strip()
        if not text.lower().endswith(".pdf"):
            text += ".pdf"
        rec = set_user_custom_name(user_id, text)
        await update.message.reply_text(f"PDF এর নতুন নাম সংরক্ষিত হলো: {text}")

        await send_updated_pdf(update, context, rec)
        await update.message.reply_text("আপডেটকৃত PDF পাঠানো হয়েছে।")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rec = get_user_record(user_id)

    if rec.get("awaiting_thumb"):
        photo_sizes = update.message.photo
        if photo_sizes:
            file_id = photo_sizes[-1].file_id
            set_user_thumbnail(user_id, file_id)
            await update.message.reply_text("থাম্বনেইল সংরক্ষিত হয়েছে।")

            await send_updated_pdf(update, context, rec)
            await update.message.reply_text("আপডেটকৃত PDF আপনার থাম্বনেইল সহ পাঠানো হয়েছে।")

# --- Main ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    print("🤖 Bot polling started...")
    app.run_polling()

if __name__ == "__main__":
    main()
