import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from claude import extract_event_details, format_event_for_display, clean_event_data
from database import save_event

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- APP SETUP --- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command"""
    await update.message.reply_text(
        "Hi, start by forwarding me an event message and I'll extract it!\n Use /help for more info."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE): # Placeholder; add more commands later
    """Handles the /help command"""
    await update.message.reply_text(
        "How this works:\n"
        "1. Forward an event message to me\n"
        "2. I'll extract date, location, link, etc.\n\n"
        "Commands:\n"
        "/start - Start conversation\n"
        "/help - Show this message"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles any message or forwarded message"""
    message = update.message
    user = message.from_user
    text_content = message.text or message.caption # caption - for media with captions
    print("Message received.") # checkpoint; remove later
    
    # Check if it's a forwarded message
    if message.forward_origin and text_content:
        print("✅ Detected as forwarded message, extracting...") # checkpoint; remove later
        await message.reply_text("⏳ Extracting event details...")

        # Extract event details using Claude
        event_data = extract_event_details(text_content)
        cleaned_data = clean_event_data(event_data)

        # Save to database
        try:
            saved_event = save_event(
                event_data=cleaned_data,
                user_id=user.id,
                username=user.username or "unknown",
                raw_message=text_content
            )
            formatted_result = format_event_for_display(cleaned_data)
            await message.reply_text(formatted_result) # Reply with event details & save confirmation
        except Exception as e:
            print(f"❌ Database error: {e}")
            await message.reply_text(f"⚠️ Event extracted but couldn't save to database :( Please try again.")
    elif message.forward_origin:
        print("⚠️ Additional image detected") # Placeholder; might want to handle media later
    else:
        print("❌ Not detected as forwarded message")
        await message.reply_text("Please forward an event message to me :)")

# --- RUN APP --- #
def main():
    """Start the bot"""
    # Create the Application
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_message))

    # Start polling (start listening for messages)
    print("🤖 Bot is running... (Press Ctrl+C to stop)")
    app.run_polling()

if __name__ == "__main__":
    main()