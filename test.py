import re
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Bot token from environment variables
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Regular expression to match your custom CA format
CA_PATTERN = r'[A-Za-z0-9]{40,}'

# Function to handle incoming messages and extract CAs
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

# Main function to run the bot
def main():
    # Set up the bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add a handler to process text messages
    application.add_handler(MessageHandler(filters.TEXT, message_handler))

    # Start polling for updates
    application.run_polling()

if __name__ == '__main__':
    main()

