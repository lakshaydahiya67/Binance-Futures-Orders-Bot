# Binance Futures Trading Bot

A CLI-based trading bot for Binance USDT-M Futures that supports multiple order types with robust logging, validation, and documentation.

## Features

### Core Order Types (Mandatory)
- **Market Orders**: Execute immediate buy/sell orders at current market price
- **Limit Orders**: Place orders at specific price levels

### Advanced Order Types (Bonus)
- **Stop-Limit Orders**: Trigger orders when stop price is reached
- **OCO Orders**: One-Cancels-the-Other order pairs
- **TWAP Orders**: Time-Weighted Average Price strategy
- **Grid Orders**: Automated buy-low/sell-high within price range

## Prerequisites

1. **Python 3.7+** installed
2. **Binance Testnet Account**: Register at https://testnet.binancefuture.com
3. **API Credentials**: Generate API key and secret from testnet

## Installation

1. Clone or download the project
2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Set your Binance testnet API credentials as environment variables:
```bash
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
```

The bot reads credentials only from environment variables.

## Usage

### Basic CLI Commands

All order types can be executed directly using their respective Python files.

### Market Orders
```bash
python src/market_orders.py BTCUSDT BUY 0.01
python src/market_orders.py ETHUSDT SELL 0.1
```

### Limit Orders
```bash
python src/limit_orders.py BTCUSDT BUY 0.01 45000.00
python src/limit_orders.py ETHUSDT SELL 0.1 3500.00
```

### Advanced Orders

**Stop-Limit Orders:**
```bash
python src/advanced/stop_limit.py BTCUSDT BUY 0.01 44000.00 45000.00
```

**OCO Orders:**
```bash
python src/advanced/oco.py BTCUSDT SELL 0.01 46000.00 44000.00 43500.00
```

**TWAP Orders:**
```bash
python src/advanced/twap.py BTCUSDT BUY 0.1 300 0.01
# Parameters: SYMBOL SIDE TOTAL_QUANTITY TIME_DURATION_SECONDS CHUNK_SIZE
```

**Grid Orders:**
```bash
python src/advanced/grid.py BTCUSDT 44000.00 46000.00 5 0.01
# Parameters: SYMBOL PRICE_LOW PRICE_HIGH GRID_LEVELS QUANTITY_PER_LEVEL
```

## File Structure

```
├── src/                    # All source code
│   ├── market_orders.py    # Market order logic
│   ├── limit_orders.py     # Limit order logic
│   ├── advanced/           # Advanced order types
│   │   ├── stop_limit.py   # Stop-limit order logic
│   │   ├── oco.py          # OCO order logic
│   │   ├── twap.py         # TWAP strategy
│   │   └── grid.py         # Grid order logic
├── bot.log                 # Logs (API calls, errors, executions)
├── README.md               # This file
├── requirements.txt        # Python dependencies
└── venv/                   # Virtual environment
```

## Input Validation

The bot performs basic input validation before placing orders:

- **Side Validation**: Ensures BUY/SELL parameters are correct
- **Quantity Validation**: Ensures quantities are positive numbers
- **Price Validation**: Ensures prices are positive numbers (where applicable)
- **Stop/Limit Relationship**: For stop-limit orders, validates the expected relation between stop and limit prices

## Logging

All operations are logged to `bot.log` with structured JSON format:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "message": "Market order placed successfully",
  "data": {
    "symbol": "BTCUSDT",
    "side": "BUY",
    "quantity": "0.01",
    "order_id": "12345678",
    "status": "FILLED"
  }
}
```

## Error Handling

The bot handles various error scenarios:
- Network connectivity issues
- API rate limiting
- Invalid API credentials
- Insufficient balance errors
- Invalid symbol/parameter errors
- Order rejection by exchange

## Important Notes

1. **Testnet Only**: This bot is configured for Binance testnet environment
2. **No Real Money**: All trades are executed with testnet funds
3. **OCO in Futures**: Binance USDT-M Futures does not support native OCO; this project implements OCO-style behavior by placing a limit and a stop order separately. Manual management is required to cancel the remaining order when one executes.
4. **Rate Limits**: Be aware of API rate limits to avoid restrictions

## Dependencies

- `binance-futures-connector>=3.6.0`: Official Binance futures connector
- `python-dotenv>=1.0.0`: Environment variable loader

## Testing

To test the bot functionality:

1. Ensure API credentials are set
2. Execute test orders with small quantities using the CLI commands above

## License

This project is for educational purposes only. Use at your own risk.