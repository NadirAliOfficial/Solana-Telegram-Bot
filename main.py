import os
import re
import logging
from dotenv import load_dotenv
from telegram import Update
from solana.rpc.api import Client
from solders.pubkey import Pubkey  # type: ignore

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
    level=logging.INFO, filename="bot.log", filemode="w"
)
logger = logging.getLogger(__name__)

# Get the bot token from the .env file
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# CA Pattern to match contract addresses
CA_PATTERN = r'[A-Za-z0-9]{40,}'


if not TOKEN:
    logger.error("Telegram bot token not found in .env file.")
    exit(1)

async def message_handler(update: Update, context):
    # Get the text of the incoming message
    message_text = update.message.text
    if message_text:  # Ensure message contains text
        # Search for contract addresses in the message
        contract_addresses = re.findall(CA_PATTERN, message_text)

        if contract_addresses:
            print(f"Contract Address Found: {contract_addresses}")

            # Log the contract addresses to a file
            with open('parsed_contract_addresses.txt', 'a') as f:
                for address in contract_addresses:
                    f.write(f"{address}\n")
# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Responds to the /start command with a welcome message
    user = update.effective_user
    logger.info(f"Command '/start' received from user {user.username}")
    await update.message.reply_html(
        f"Hi {user.mention_html()}! Welcome to the RenAI bot."
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
        "/withdraw - Withdraw funds\n"
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

    # Responds to the /balance command by fetching and displaying the Solana wallet balance.
    
    logger.info("Command '/balance' received.") 
    

    # Get the wallet address from environment variables.
    wallet_address = os.getenv('SOL_WALLET')
    if not wallet_address:
        logger.error("SOL_WALLET environment variable not found.")  # Log if the wallet address is missing.
        await update.message.reply_text("Error: Wallet address not configured.")  # Inform the user.
        return

    try:
        # Initialize the Solana client.
        client = Client("https://api.mainnet-beta.solana.com")

        # Convert the wallet address to a Pubkey object.
        public_key = Pubkey.from_string(wallet_address)

        # Fetch the wallet balance from the Solana blockchain.
        response = client.get_balance(public_key)

        # Extract balance in lamports and convert to SOL.
        lamports = response.value
        sol_balance = lamports / 1_000_000_000  # 1 SOL = 10^9 lamports.

        # Respond to the user with the wallet balance.
        await update.message.reply_text(
            f"Wallet Address: {wallet_address}\n"  # Display the wallet address.
            f"Balance: {sol_balance:.9f} SOL"  # Display the balance in SOL.
        )
        logger.info(f"Balance retrieved: {sol_balance:.9f} SOL for {wallet_address}")  # Log the successful response.
    except ValueError as e:
        # Handle invalid wallet address errors.
        logger.error(f"Invalid wallet address: {wallet_address}. Error: {e}")
        await update.message.reply_text("Error: Invalid wallet address configured.")  # Inform the user.
    except Exception as e:
        # Handle other unexpected errors.
        logger.error(f"Failed to fetch balance: {e}")
        await update.message.reply_text("Error: Unable to fetch wallet balance. Please try again later.")  # Inform the user.


async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Placeholder for the /withdraw command
    logger.info("Command '/withdraw' received.")
    await update.message.reply_text("Withdraw command received. Functionality coming soon!")
    
    

# Message Handlers
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Echoes back any text message sent by the user
    logger.info(f"Echoing message: {update.message.text}")
    await update.message.reply_text(update.message.text)

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
    application.add_handler(MessageHandler(filters.TEXT, message_handler))
    

    # Register message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Register the error handler
    application.add_error_handler(error_handler)

    # Start polling for updates
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
