import re

# Example dynamic text (replace this with your input)
text = """
generational dip on $neroboss imo

dev has been COOKING

https://x.com/nerobossai

nerocity launched and its pretty much like dasha which went to 200m, it can create music, videos, ai agents, doesnt fucking matter

this guy is a monster and the coin went from 30m to 6m, if this isnt a good ape then its a scam lol

im fully allocated

the dev = https://x.com/utksn15


Chart: https://dexscreener.com/solana/bcpmp9qsqtvwe9iaduxvzyf2jcgghytnryb3s9wkjktr

CA: 5HTp1ebDeBcuRaP4J6cG3r4AffbP4dtcrsS7YYT7pump

"""

# Regular expression to extract the CA (general pattern for alphanumeric CAs)
pattern =  r'\b([1-9A-HJ-NP-Za-km-z]{32,44})\b(?!\S)'


# Find all matches in the text
matches = re.findall(pattern, text)

if matches:
    for i, ca in enumerate(matches, start=1):
        print(f"Contract Address {i}: {ca}")
else:
    print("No Contract Address found!")
    
    
    # CA_PATTERN = r'(?:CA:\s*)?([1-9A-HJ-NP-Za-km-z]{32,44}pump)'

# async def message_handler(update: Update, context):
#     # Get the text of the incoming message
#     message_text = update.message.text
#     if message_text:  # Ensure message contains text
#         # Search for contract addresses in the message
#         mint_addresses = re.findall(CA_PATTERN, message_text)

#         if mint_addresses:
#             print(f"Mint Addresses Found: {mint_addresses}")

#             # Log the contract addresses to a file
#             with open('mint.txt', 'a') as f:  # Use append mode to save multiple entries
#                 for address in mint_addresses:
#                     f.write(f"{address}\n")
