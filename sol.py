from solana.rpc.api import Client
from solders.pubkey import Pubkey  # Correct import for public keys
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Initialize the Solana client
client = Client("https://api.mainnet-beta.solana.com")

# Get the wallet address from the environment variable
wallet_address = os.getenv('SOL_WALLET')

if wallet_address:
    try:
        # Convert the wallet address to a Pubkey object
        public_key = Pubkey.from_string(wallet_address)

        # Fetch the balance
        response = client.get_balance(public_key)
        
        # Access the balance value
        lamports = response.value
        print(f"Balance: {lamports} lamports")
    except ValueError as e:
        print(f"Invalid wallet address: {wallet_address}. Error: {e}")
else:
    print("Error: SOL_WALLET environment variable not found.")

# Print the wallet address
print(f"Wallet Address: {wallet_address}")
