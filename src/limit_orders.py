#!/usr/bin/env python3

import sys
import os
from dotenv import load_dotenv
from binance.um_futures import UMFutures
from binance.error import ClientError, ServerError
from logger import (setup_logger, log_api_request, log_api_response, 
                   log_validation_error, log_execution_success, 
                   log_execution_error, log_connection_success)

load_dotenv()


def validate_inputs(symbol, side, quantity, price):
    if not symbol or not isinstance(symbol, str):
        return False, "Invalid symbol"
    
    if side not in ['BUY', 'SELL']:
        return False, "Side must be BUY or SELL"
    
    try:
        qty = float(quantity)
        if qty <= 0:
            return False, "Quantity must be positive"
    except ValueError:
        return False, "Invalid quantity format"
    
    try:
        price_val = float(price)
        if price_val <= 0:
            return False, "Price must be positive"
    except ValueError:
        return False, "Invalid price format"
    
    return True, "Valid"

def place_limit_order(symbol, side, quantity, price):
    logger = setup_logger(__name__)
    
    # Get API credentials from environment
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("API credentials not found in environment variables")
        print("Error: Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
        return False
    
    # Validate inputs
    is_valid, error_msg = validate_inputs(symbol, side, quantity, price)
    if not is_valid:
        log_validation_error(logger, "limit_order_validation", {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "error_message": error_msg
        })
        print(f"Error: {error_msg}")
        return False
    
    try:
        # Initialize Binance client for testnet
        client = UMFutures(
            key=api_key,
            secret=api_secret,
            base_url="https://testnet.binancefuture.com"
        )
        
        # Test connection
        server_time = client.time()
        log_connection_success(logger, server_time)
        
        # Place limit order
        order_params = {
            'symbol': symbol,
            'side': side,
            'type': 'LIMIT',
            'quantity': float(quantity),
            'price': float(price),
            'timeInForce': 'GTC'
        }
        
        log_api_request(logger, "place_limit_order", order_params)
        result = client.new_order(**order_params)
        
        # Log success
        log_execution_success(logger, "Limit", result)
        
        # Display results
        print("Limit Order Placed Successfully:")
        print(f"Symbol: {result.get('symbol')}")
        print(f"Order ID: {result.get('orderId')}")
        print(f"Side: {result.get('side')}")
        print(f"Type: {result.get('type')}")
        print(f"Quantity: {result.get('origQty')}")
        print(f"Price: {result.get('price')}")
        print(f"Status: {result.get('status')}")
        print(f"Time in Force: {result.get('timeInForce')}")
        
        return True
        
    except ClientError as e:
        log_execution_error(logger, "ClientError", e.error_message, e.error_code)
        print(f"Error: {e.error_message}")
        return False
    except ServerError as e:
        log_execution_error(logger, "ServerError", e.error_message)
        print(f"Error: {e.error_message}")
        return False
    except Exception as e:
        log_execution_error(logger, "UnexpectedException", str(e))
        print(f"Error: {str(e)}")
        return False

def main():
    if len(sys.argv) != 5:
        print("Usage: python src/limit_orders.py <SYMBOL> <SIDE> <QUANTITY> <PRICE>")
        print("Example: python src/limit_orders.py BTCUSDT BUY 0.01 45000.00")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    side = sys.argv[2].upper()
    quantity = sys.argv[3]
    price = sys.argv[4]
    
    success = place_limit_order(symbol, side, quantity, price)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()