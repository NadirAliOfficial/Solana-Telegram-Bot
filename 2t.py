import requests
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.keypair import Keypair
from base64 import b64decode
from dotenv import load_dotenv
import asyncio
import os
import base58

# Load environment variables
load_dotenv()

# Configuration Variables
SOL_MINT = "So11111111111111111111111111111111111111112"  # Native SOL token
INPUT_TOKEN = SOL_MINT  # Replace with your input token mint address
OUTPUT_TOKEN = os.getenv("MINT_ADDRESS")  # Replace with your output token mint address
SWAP_AMOUNT = 100000000  # Amount of SOL to swap (in Lamports)
SLIPPAGE = 0.5  # Slippage tolerance in percentage

# API Endpoints
PRIORITY_FEE_URL = "https://api.raydium.io/v2/main/priority-fee"
SWAP_COMPUTE_URL = "https://api.raydium.io/v2/compute/swap-base-in"
SWAP_TRANSACTION_URL = "https://api.raydium.io/v2/transaction/swap-base-in"

# Wallet Keys
WALLET_PUBLIC_KEY = os.getenv("SOL_WALLET")  # Replace with your wallet public key
PRIVATE_KEY = base58.b58decode(os.getenv("PRIVATE_KEY"))  # Replace with private key in hex format
wallet_keypair = Keypair.from_seed(PRIVATE_KEY[:32])

async def perform_swap():
    async with AsyncClient("https://api.mainnet-beta.solana.com") as connection:
        # Step 1: Fetch Priority Fees
        priority_fee_response = requests.get(PRIORITY_FEE_URL)
        if priority_fee_response.status_code != 200:
            print("Failed to fetch priority fees")
            return
        priority_fee_data = priority_fee_response.json()["data"]["default"]["h"]

        # Step 2: Get Swap Compute Details
        compute_swap_response = requests.get(
            f"{SWAP_COMPUTE_URL}?inputMint={INPUT_TOKEN}&outputMint={OUTPUT_TOKEN}&amount={SWAP_AMOUNT}"
            f"&slippageBps={int(SLIPPAGE * 100)}&txVersion=V0"
        )
        if compute_swap_response.status_code != 200:
            print("Failed to fetch swap compute details")
            return
        compute_data = compute_swap_response.json()

        # Step 3: Get Swap Transaction
        transaction_response = requests.post(
            SWAP_TRANSACTION_URL,
            json={
                "computeUnitPriceMicroLamports": str(priority_fee_data),
                "swapResponse": compute_data,
                "txVersion": "V0",
                "wallet": WALLET_PUBLIC_KEY,
                "wrapSol": INPUT_TOKEN == SOL_MINT,
                "unwrapSol": OUTPUT_TOKEN == SOL_MINT,
                "inputAccount": None,
                "outputAccount": None,
            },
        )
        if transaction_response.status_code != 200:
            print("Failed to fetch swap transaction")
            return
        transaction_data = transaction_response.json()

        # Step 4: Decode and Sign Transaction
        transactions = [
            Transaction.deserialize(b64decode(tx["transaction"]))
            for tx in transaction_data["data"]["transaction"]
        ]
        for idx, transaction in enumerate(transactions, start=1):
            transaction.sign(wallet_keypair)
            try:
                print(f"Sending transaction {idx}...")
                tx_signature = await connection.send_transaction(transaction, wallet_keypair, skip_preflight=True)
                print(f"Transaction {idx} sent: {tx_signature}")
                await connection.confirm_transaction(tx_signature)
                print(f"Transaction {idx} confirmed!")
            except Exception as e:
                print(f"Transaction {idx} failed: {e}")

# Run the swap
asyncio.run(perform_swap())
