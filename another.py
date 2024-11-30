import os
import asyncio
import base64
from dotenv import load_dotenv
import aiohttp
from solana.rpc.async_api import AsyncClient
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler
)
from solders.keypair import Keypair  # type: ignore
from solders.transaction import Transaction  # type: ignore

# Load environment variables
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

# Define stages of the conversation
ASK_AMOUNT = 1

user_state = {}

# Function to perform the swap
async def perform_swap(amount: float, user_id: int):
    async with AsyncClient("https://api.mainnet-beta.solana.com") as client:
        keypair = Keypair.from_base58_string(PRIVATE_KEY)
        balance_response = await client.get_balance(keypair.pubkey())
        wallet_balance = balance_response.value

        required_balance = 2039280  # Adjust based on expected fees
        if wallet_balance < required_balance:
            await send_message(user_id, "Insufficient SOL balance. Please top up your wallet.")
            return

        params = {
            "from": "So11111111111111111111111111111111111111112",  # SOL
            "to": "2qEHjDLDLbuBgRYvsxhc5D6uDWAivNFZGan56P1tpump",  # Other Token
            "amount": amount,
            "slip": 15,
            "payer": str(keypair.pubkey()),
            "fee": 0.0001,
            "txType": "legacy",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://swap.solxtence.com/swap", params=params) as response:
                    data = await response.json()
                    if "transaction" not in data:
                        await send_message(user_id, "Error: Invalid transaction data received.")
                        return

                    serialized_tx = base64.b64decode(data["transaction"]["serializedTx"])
                    tx_type = data["transaction"]["txType"]

            recent_blockhash = await client.get_latest_blockhash()
            blockhash = recent_blockhash.value.blockhash

            if tx_type == "legacy":
                transaction = Transaction.from_bytes(serialized_tx)
                transaction.sign([keypair], blockhash)
            else:
                await send_message(user_id, "TX type not supported :/")
                return

            response = await client.send_raw_transaction(bytes(transaction))
            await send_message(user_id, f"Swap successful! Transaction signature: {response.value}")

        except Exception as error:
            await send_message(user_id, f"Error performing swap: {error}")

# Function to send messages (asynchronous)
async def send_message(user_id: int, text: str):
    application = Application.builder().token(TOKEN).build()  # Now no 'await' here
    await application.bot.send_message(user_id, text)

# Start command to introduce the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    await update.message.reply_text(
        "Welcome to the Solana Swap Bot! Use /buy to initiate a swap."
    )

# Start the buy process
async def start_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    await update.message.reply_text("How much SOL would you like to swap? Please enter the amount.")
    user_state[user_id] = ASK_AMOUNT

# Handle user input for the amount to swap
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    if user_state.get(user_id) == ASK_AMOUNT:
        try:
            amount = float(update.message.text)
            if amount <= 0:
                await update.message.reply_text("Amount must be greater than zero. Please enter a valid amount.")
                return

            await update.message.reply_text(f"Initiating swap for {amount} SOL. Please wait...")
            await perform_swap(amount, user_id)
            user_state.pop(user_id, None)  # Reset user state

        except ValueError:
            await update.message.reply_text("Invalid input. Please enter a numeric value for the amount.")

# Conversation Handler to manage user interaction
conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('buy', start_buy)],
    states={
        ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
    },
    fallbacks=[],
)

# Main function to set up the bot
async def main():
    application = Application.builder().token(TOKEN).build()

    # Command handler for /start and /help
    application.add_handler(CommandHandler('start', start))
    application.add_handler(conversation_handler)

    # Start polling
    await application.run_polling()
    
# Use asyncio.run() which automatically handles event loops
if __name__ == '__main__':
    try:
        asyncio.run(main())  # Use asyncio.run() for proper event loop handling
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            asyncio.ensure_future(main())  # If already running, ensure the main task is scheduled
        else:
            raise

