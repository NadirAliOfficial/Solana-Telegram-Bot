import os
import re
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from solana.rpc.api import Client
from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey  # type: ignore
from solana.rpc.types import TxOpts
from solana.transaction import Transaction
from solders.system_program import TransferParams, transfer  
import base58

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Load environment variables from the .env file
load_dotenv()
RAYDIUM_API_URL = "https://api.raydium.io/v2/mainnet/ammV3-pools"
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
        "/withdraw - Withdraw funds\n"
    )


# Buy Logic Starts
# Function to read mint addresses from 'mint.txt'
def read_mint_addresses_from_file(file_path="mint.txt"):
    if not os.path.exists(file_path):
        logger.error(f"Mint file '{file_path}' does not exist.")
        return []

    with open(file_path, "r") as file:
        mint_addresses = file.readlines()

    # Clean up any extra whitespace or newline characters
    mint_addresses = [address.strip() for address in mint_addresses]
    
    return mint_addresses

# Command to handle the buy logic
async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Read mint addresses from the file
    mint_addresses_from_file = read_mint_addresses_from_file()

    if not mint_addresses_from_file:
        await update.message.reply_text("No mint addresses found in the file.")
        return

    # Log the mint addresses found from the file for debugging
    logger.info(f"Mint Addresses from file: {mint_addresses_from_file}")

    # Check if the mint address in the message is valid (use the first address in the file)
    mint_address = mint_addresses_from_file[0]  # You can adjust logic to select different mint address
    logger.info(f"Using mint address: '{mint_address}'")

    # Trim any extra whitespace or newlines from the mint address
    mint_address = mint_address.strip()
    # Validate the mint address format
    if not re.match(CA_PATTERN, mint_address):
        await update.message.reply_text(f"The mint address '{mint_address}' is not valid.")
        logger.error(f"Invalid mint address: '{mint_address}'")
        return

    logger.info(f"Buying token with mint address: {mint_address}")
    await update.message.reply_text(
        f"Buying token with mint address: {mint_address}"
    )

    # Load the wallet's private key from environment variables (make sure this is securely handled)
    load_dotenv()
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    if not PRIVATE_KEY:
        logger.error("Private key not found in environment.")
        await update.message.reply_text("Private key not configured. Please set the PRIVATE_KEY.")
        return

    try:
        # Decode the private key and create the wallet keypair
        private_key_bytes = base58.b58decode(PRIVATE_KEY)
        wallet = Keypair.from_bytes(private_key_bytes)
    except Exception as e:
        logger.error(f"Error loading wallet from private key: {e}")
        await update.message.reply_text("Error loading wallet. Please check the private key.")
        return

    # Initialize Solana client
    client = Client("https://api.mainnet-beta.solana.com")

    # Fetch Raydium pools to find the correct pool for the token mint address
    response = requests.get(RAYDIUM_API_URL)
    pools = response.json()

    # Search for the correct liquidity pool
    target_pool = next(
        (pool for pool in pools if pool['tokenMintA'] == mint_address or pool['tokenMintB'] == mint_address),
        None
    )
    if not target_pool:
        logger.error("No liquidity pool found for the given mint address.")
        await update.message.reply_text("No liquidity pool found for the provided mint address.")
        return

    # Extract pool details
    pool_id = Pubkey.from_string(target_pool['id'])
    pool_authority = Pubkey.from_string(target_pool['authority'])
    pool_token_account_a = Pubkey.from_string(target_pool['tokenAccountA'])
    pool_token_account_b = Pubkey.from_string(target_pool['tokenAccountB'])

    # Define the amount of SOL to swap (e.g., 0.1 SOL)
    swap_amount_sol = 0.1  # Adjust based on your requirement
    sol_in_lamports = int(swap_amount_sol * 1_000_000_000)  # Convert SOL to lamports

    # Build the transaction to buy the token
    transaction = Transaction()

    transaction.add(transfer(TransferParams(
        from_pubkey=wallet.public_key(),
        to_pubkey=pool_token_account_a,
        lamports=sol_in_lamports
    )))

    # Send the transaction
    try:
        response = await client.send_transaction(transaction, wallet, opts=TxOpts(skip_confirmation=False))
        logger.info(f"Transaction sent: {response}")
        await update.message.reply_text(f"Successfully sent {swap_amount_sol} SOL to buy token from pool.")
    except Exception as e:
        logger.error(f"Transaction failed: {e}")
        await update.message.reply_text(f"Error during transaction: {e}")
# End


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



# Run the bot
if __name__ == "__main__":
    main()
