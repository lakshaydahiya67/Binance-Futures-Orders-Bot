#!/usr/bin/env python3

import sys
import os
from dotenv import load_dotenv
from binance.um_futures import UMFutures
from binance.exceptions import BinanceAPIException
from logger import (setup_logger, log_api_request, log_api_response, 
                   log_validation_error, log_execution_success, 
                   log_execution_error, log_connection_success)

load_dotenv()


def validate_inputs(symbol, side, quantity, stop_price, limit_price):
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
        stop_price_val = float(stop_price)
        limit_price_val = float(limit_price)
        
        if stop_price_val <= 0 or limit_price_val <= 0:
            return False, "All prices must be positive"
            
        # Validate stop/limit price relationship
        if side == 'BUY':
            if stop_price_val <= limit_price_val:
                return False, "For BUY orders: stop price must be higher than limit price"
        else:  # SELL
            if stop_price_val >= limit_price_val:
                return False, "For SELL orders: stop price must be lower than limit price"
                
    except ValueError:
        return False, "Invalid price format"
    
    return True, "Valid"

def place_stop_limit_order(symbol, side, quantity, stop_price, limit_price):
    logger = setup_logger(__name__)
    
    # Get API credentials from environment
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("API credentials not found in environment variables")
        print("Error: Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
        return False
    
    # Validate inputs
    is_valid, error_msg = validate_inputs(symbol, side, quantity, stop_price, limit_price)
    if not is_valid:
        log_validation_error(logger, "stop_limit_order_validation", {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "stop_price": stop_price,
            "limit_price": limit_price,
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
        
        # Place stop-limit order
        order_params = {
            'symbol': symbol,
            'side': side,
            'type': 'STOP',
            'quantity': float(quantity),
            'price': float(limit_price),
            'stopPrice': float(stop_price),
            'timeInForce': 'GTC'
        }
        
        log_api_request(logger, "place_stop_limit_order", order_params)
        result = client.new_order(**order_params)
        
        # Log success
        log_execution_success(logger, "Stop-Limit", result)
        
        # Display results
        print("Stop-Limit Order Placed Successfully:")
        print(f"Symbol: {result.get('symbol')}")
        print(f"Order ID: {result.get('orderId')}")
        print(f"Side: {result.get('side')}")
        print(f"Type: {result.get('type')}")
        print(f"Quantity: {result.get('origQty')}")
        print(f"Stop Price: {result.get('stopPrice')}")
        print(f"Price: {result.get('price')}")
        print(f"Status: {result.get('status')}")
        print(f"Time in Force: {result.get('timeInForce')}")
        
        return True
        
    except BinanceAPIException as e:
        log_execution_error(logger, "BinanceAPIException", e.message, e.code)
        print(f"Error: {e.message}")
        return False
    except Exception as e:
        log_execution_error(logger, "UnexpectedException", str(e))
        print(f"Error: {str(e)}")
        return False

def main():
    if len(sys.argv) != 6:
        print("Usage: python src/advanced/stop_limit.py <SYMBOL> <SIDE> <QUANTITY> <STOP_PRICE> <LIMIT_PRICE>")
        print("Example: python src/advanced/stop_limit.py BTCUSDT BUY 0.01 44000.00 45000.00")
        print("Note: For BUY - stop price > limit price, For SELL - stop price < limit price")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    side = sys.argv[2].upper()
    quantity = sys.argv[3]
    stop_price = sys.argv[4]
    limit_price = sys.argv[5]
    
    success = place_stop_limit_order(symbol, side, quantity, stop_price, limit_price)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()