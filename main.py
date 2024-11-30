import os
import re
import logging
import asyncio
import requests
from solana.rpc.async_api import AsyncClient
import json
import aiohttp
from telegram.ext import ConversationHandler
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ConversationHandler
from solana.rpc.api import Client
from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey  # type: ignore
from datetime import datetime
from solana.rpc.types import TxOpts
from solders.system_program import TransferParams, transfer  
import base58
import base64
from solders.transaction import Transaction # type: ignore
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Load environment variables from the .env file
load_dotenv()

# Define states for the conversation
AMOUNT = 1

MAX_TRIAL_REQUESTS = 15
PAID_REQUESTS = 1000  # Monthly paid requests
SUBSCRIPTION_COST = 29  # Subscription cost in dollars
USAGE_FILE = 'usage.json'

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO, filename="bot.log", filemode="w"
)
logger = logging.getLogger(__name__)

# Get the bot token from the .env file
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# CA Pattern to match contract addresses
CA_PATTERN = r'^[1-9A-HJ-NP-Za-km-z]{32,44}pump$'


if not TOKEN:
    logger.error("Telegram bot token not found in .env file.")
    exit(1)

async def message_handler(update: Update, context):
    # Get the text of the incoming message
    message_text = update.message.text
    if message_text:  # Ensure message contains text
        # Search for contract addresses in the message
        mint_addresses = re.findall(CA_PATTERN, message_text)

        if mint_addresses:
            print(f"Mint Address Found: {mint_addresses}")

            # Log the contract addresses to a file
            with open('mint.txt', 'w') as f:
                for address in mint_addresses:
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
    )


# Buy Logic Starts
async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /buy command and starts the conversation."""
    await update.message.reply_text(f"Welcome! to the RenAI bot, Please enter the amount of SOL you want to buy:")
    return AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the amount input from the user."""
    try:
        # Parse the amount input by the user
        amount = float(update.message.text)
        
        # Validate the amount
        if amount <= 0:
            await update.message.reply_text("Please enter a valid positive amount of SOL.")
            return AMOUNT
        
        context.user_data['amount'] = amount  # Store the amount in user data
        
        await update.message.reply_text(f"Got it! You are buying {amount} SOL. Now I will check your wallet balance...")
        
        # Proceed with the transaction
        await process_transaction(update, context, amount)
        
        return ConversationHandler.END  # End the conversation

    except ValueError:
        await update.message.reply_text("Please enter a valid number for the amount of SOL.")
        return AMOUNT


# Initialize or load usage data
def load_usage_data():
    if not os.path.exists(USAGE_FILE):
        usage_data = {
            "requests_count": 0,
            "trial_completed": False,
            "subscription_end": None
        }
        save_usage_data(usage_data)
    else:
        with open(USAGE_FILE, 'r') as file:
            usage_data = json.load(file)
    return usage_data

def save_usage_data(usage_data):
    with open(USAGE_FILE, 'w') as file:
        json.dump(usage_data, file)

async def increment_request_count():
    usage_data = load_usage_data()
    usage_data['requests_count'] += 1
    if usage_data['requests_count'] >= MAX_TRIAL_REQUESTS and not usage_data["trial_completed"]:
        usage_data["trial_completed"] = True
    save_usage_data(usage_data)

async def check_user_access():
    usage_data = load_usage_data()
    now = datetime.now()
    
    if usage_data["trial_completed"]:
        # Check subscription
        if not usage_data["subscription_end"] or datetime.fromisoformat(usage_data["subscription_end"]) < now:
            return False  # Subscription expired or not started
        elif usage_data['requests_count'] >= PAID_REQUESTS:
            return False  # Monthly request limit reached
    
    return True

async def process_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE, amount_in_sol: float) -> None:
    """Process the transaction after the amount is received."""
    usage_data = load_usage_data()
    
    # Free trial or subscription status check
    if not await check_user_access():
        if usage_data["trial_completed"]:
            await update.message.reply_text("Subscription expired or request limit reached. Please renew for $29/month.")
        else:
            await update.message.reply_text(
                f"Free trial completed: You used {usage_data['requests_count']} requests out of {MAX_TRIAL_REQUESTS}."
            )
        return
    
    if not usage_data["trial_completed"]:
        remaining_free_requests = MAX_TRIAL_REQUESTS - usage_data['requests_count']
        await update.message.reply_text(
            f"Free trial in progress: {usage_data['requests_count']} of {MAX_TRIAL_REQUESTS} requests used. "
            f"{remaining_free_requests} remaining."
        )
    else:
        remaining_requests = PAID_REQUESTS - usage_data['requests_count']
        remaining_days = (datetime.fromisoformat(usage_data["subscription_end"]) - datetime.now()).days
        await update.message.reply_text(
            f"Subscription active: {remaining_requests} requests and {remaining_days} days remaining."
        )

    # Process swap transaction
    mint_file_path = 'mint.txt'
    try:
        with open(mint_file_path, 'r') as file:
            mint_addresses = file.readlines()
            if not mint_addresses:
                await update.message.reply_text("No mint addresses found in the file.")
                return
            mint_address = mint_addresses[0].strip()
    except FileNotFoundError:
        await update.message.reply_text(f"The file {mint_file_path} was not found.")
        return

    async with AsyncClient("https://api.mainnet-beta.solana.com") as client:
        keypair = Keypair.from_base58_string(os.getenv('PRIVATE_KEY'))
        balance_response = await client.get_balance(keypair.pubkey())
        wallet_balance = balance_response.value
        await update.message.reply_text(f"Wallet balance: {wallet_balance} lamports")

        required_balance = 2039280
        if wallet_balance < required_balance:
            await update.message.reply_text("Insufficient SOL balance. Please top up your wallet.")
            return

        required_lamports = int(amount_in_sol * 1e9) + required_balance
        await update.message.reply_text(f"Required lamports for transaction: {required_lamports} lamports.")

        params = {
            "from": "So11111111111111111111111111111111111111112",
            "to": mint_address,
            "amount": amount_in_sol,
            "slip": 15,
            "payer": str(keypair.pubkey()),
            "fee": 0.0001,
            "txType": "legacy",
        }

        await update.message.reply_text(f"Initiating swap with mint address: {mint_address} for {amount_in_sol} SOL.")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://swap.solxtence.com/swap", params=params) as response:
                    data = await response.json()
                    if "transaction" not in data:
                        await update.message.reply_text("Error: Invalid transaction data received.")
                        return

                    serialized_tx = base64.b64decode(data["transaction"]["serializedTx"])
                    tx_type = data["transaction"]["txType"]

            recent_blockhash = await client.get_latest_blockhash()
            blockhash = recent_blockhash.value.blockhash

            if tx_type == "legacy":
                transaction = Transaction.from_bytes(serialized_tx)
                transaction.sign([keypair], blockhash)
            else:
                await update.message.reply_text("TX type not supported :/")
                return

            response = await client.send_raw_transaction(bytes(transaction))
            await update.message.reply_text(
                f"Swap successful! Transaction signature: `{response.value}`", parse_mode="Markdown"
            )

        except Exception as error:
            if "insufficient lamports" in str(error):
                await update.message.reply_text("Insufficient funds to cover the transaction. Please ensure your wallet has enough SOL.")
            else:
                await update.message.reply_text(f"Error performing swap: {error}")

        finally:
            # Increment the request count regardless of success or failure
            await increment_request_count()
                
# Define the conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('buy', buy_command)],
    states={
        AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
    },
    fallbacks=[],
)
 
# Buy End

# Sell Command Starts
# Command to handle the sell logic
async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Log the sell command invocation
    logger.info("Command '/sell' received.")
    await update.message.reply_text("This command is not implemented yet.")
#  Sell Command End

# Limit Command Starts
async def limit_command(update: Update, context: ContextTypes.DEFAULT_TYPE)-> None:
    # Log the limit command invocation
    logger.info("Command '/limit' received.")
    await update.message.reply_text("This command is not implemented yet.")
    

# Limit Command End


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


# Error Handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Logs errors caused by updates
    logger.warning(f"Update '{update}' caused error '{context.error}'")


# Main Function
def main() -> None:
    # Sets up the bot, registers handlers, and starts polling for updates
    application = Application.builder().token(TOKEN).build()

    # Register command handlers
    application.add_handler(conv_handler)  # Register the conversation handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("sell", sell_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("limit", limit_command))
    # application.add_handler(CommandHandler("buy", get_amount))
    application.add_handler(MessageHandler(filters.TEXT, message_handler))
    
    
    # Register the error handler
    application.add_error_handler(error_handler)

    # Start polling for updates
    application.run_polling(allowed_updates=Update.ALL_TYPES)




# Run the bot
if __name__ == "__main__":
    asyncio.run(main())


#  This Bot is created by Team Nadir Ali Khan.
# Telegram : https://t.me/NAKProgrammer