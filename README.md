# Solana Auto Buy/Sell Telegram Bot

A Solana trading bot controlled via Telegram — supports auto buy/sell based on configurable triggers.

## Features
- Buy/sell Solana tokens via Telegram commands
- Real-time price monitoring
- Configurable slippage and transaction fees
- Transaction confirmation and logging

## Requirements
```
pip install solana python-telegram-bot
```

## Configuration
Set your wallet private key and Telegram bot token in `.env`.

## Commands
- `/buy <token> <amount>` — buy token
- `/sell <token> <amount>` — sell token
- `/price <token>` — get current price
- `/balance` — check wallet balance

## License
MIT
