import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- APP SETUP --- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command"""
    await update.message.reply_text(
        "Greeting message here"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    # Check if it's a forwarded message
    if message.forward_origin:
        await message.reply_text(
            "✅ Received forwarded message!\n\n"
        )
        print("Message received:\n", message.text)
    else:
        await message.reply_text(
            "Please forward an event message to me :)"
        )

# --- RUN APP --- #
def main():
    """Start the bot"""
    # Create the Application
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling (start listening for messages)
    print("🤖 Bot is running... (Press Ctrl+C to stop)")
    app.run_polling()

if __name__ == "__main__":
    main()