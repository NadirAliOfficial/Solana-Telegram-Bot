import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Load environment variables from the .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO, filename="bot.log"
)
logger = logging.getLogger(__name__)

# Get the bot token from the .env file
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    logger.error("Telegram bot token not found in .env file.")
    exit(1)

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Responds to the /start command with a welcome message
    user = update.effective_user
    logger.info(f"Command '/start' received from user {user.username}")
    await update.message.reply_html(
        f"Hi {user.mention_html()}! Welcome to the bot."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Responds to the /help command with a list of available commands
    logger.info(f"Command '/help' received.")
    await update.message.reply_text(
        "Here are the available commands:\n"
        "/start - Start the bot\n"
        "/help - List available commands\n"
        "/buy - Buy the target token\n"
        "/sell - Sell the target token\n"
        "/limit - Place a limit order\n"
        "/balance - Check account balance\n"
        "/withdraw - Withdraw funds"
    )


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Placeholder for the /buy command
    logger.info("Command '/buy' received.")
    await update.message.reply_text("Buy command received. Functionality coming soon!")


async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Placeholder for the /sell command
    logger.info("Command '/sell' received.")
    await update.message.reply_text("Sell command received. Functionality coming soon!")


async def limit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Placeholder for the /limit command
    logger.info("Command '/limit' received.")
    await update.message.reply_text("Limit order command received. Functionality coming soon!")


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Placeholder for the /balance command
    logger.info("Command '/balance' received.")
    await update.message.reply_text("Balance command received. Functionality coming soon!")


async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Placeholder for the /withdraw command
    logger.info("Command '/withdraw' received.")
    await update.message.reply_text("Withdraw command received. Functionality coming soon!")


# Message Handlers
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Echoes back any text message sent by the user
    logger.info(f"Echoing message: {update.message.text}")
    await update.message.reply_text(update.message.text)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Saves received photos locally
    photo = update.message.photo[-1]  # Get the highest resolution photo
    file = await photo.get_file()
    file_path = f"downloads/{photo.file_unique_id}.jpg"
    os.makedirs("downloads", exist_ok=True)  # Ensure the downloads directory exists
    await file.download_to_drive(file_path)
    logger.info(f"Photo received and saved: {file_path}")
    await update.message.reply_text("Photo received and saved!")


# Error Handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Logs errors caused by updates
    logger.warning(f"Update '{update}' caused error '{context.error}'")


# Main Function
def main() -> None:
    # Sets up the bot, registers handlers, and starts polling for updates
    application = Application.builder().token(TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("sell", sell_command))
    application.add_handler(CommandHandler("limit", limit_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("withdraw", withdraw_command))

    # Register message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Register the error handler
    application.add_error_handler(error_handler)

    # Start polling for updates
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
