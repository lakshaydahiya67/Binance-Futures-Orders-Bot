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


def validate_inputs(symbol, side, quantity, price, stop_price, stop_limit_price):
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
        stop_price_val = float(stop_price)
        stop_limit_price_val = float(stop_limit_price)
        
        if price_val <= 0 or stop_price_val <= 0 or stop_limit_price_val <= 0:
            return False, "All prices must be positive"
    except ValueError:
        return False, "Invalid price format"
    
    return True, "Valid"

def place_oco_order(symbol, side, quantity, price, stop_price, stop_limit_price):
    logger = setup_logger(__name__)
    
    # Get API credentials from environment
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("API credentials not found in environment variables")
        print("Error: Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
        return False
    
    # Validate inputs
    is_valid, error_msg = validate_inputs(symbol, side, quantity, price, stop_price, stop_limit_price)
    if not is_valid:
        log_validation_error(logger, "oco_order_validation", {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "stop_price": stop_price,
            "stop_limit_price": stop_limit_price,
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
        
        # OCO orders are not directly supported in futures, so we place two separate orders
        logger.warning("OCO orders require manual management in futures - placing two separate orders", extra={
            'data': {
                'order_type': 'OCO',
                'implementation': 'manual_management',
                'note': 'placing_separate_orders'
            }
        })
        
        # Place limit order
        limit_order_params = {
            'symbol': symbol,
            'side': side,
            'type': 'LIMIT',
            'quantity': float(quantity),
            'price': float(price),
            'timeInForce': 'GTC'
        }
        
        log_api_request(logger, "place_oco_limit_order", limit_order_params)
        limit_result = client.new_order(**limit_order_params)
        
        # Place stop order
        stop_order_params = {
            'symbol': symbol,
            'side': side,
            'type': 'STOP_MARKET',
            'quantity': float(quantity),
            'stopPrice': float(stop_price)
        }
        
        log_api_request(logger, "place_oco_stop_order", stop_order_params)
        stop_result = client.new_order(**stop_order_params)
        
        # Log success
        logger.info("OCO-style orders placed successfully", extra={
            'data': {
                'order_type': 'OCO',
                'limit_order_id': limit_result.get('orderId'),
                'stop_order_id': stop_result.get('orderId'),
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'limit_price': price,
                'stop_price': stop_price
            }
        })
        
        # Display results
        print("OCO-style Orders Placed Successfully:")
        print(f"\nLimit Order:")
        print(f"  Symbol: {limit_result.get('symbol')}")
        print(f"  Order ID: {limit_result.get('orderId')}")
        print(f"  Side: {limit_result.get('side')}")
        print(f"  Type: {limit_result.get('type')}")
        print(f"  Quantity: {limit_result.get('origQty')}")
        print(f"  Price: {limit_result.get('price')}")
        print(f"  Status: {limit_result.get('status')}")
        
        print(f"\nStop Order:")
        print(f"  Symbol: {stop_result.get('symbol')}")
        print(f"  Order ID: {stop_result.get('orderId')}")
        print(f"  Side: {stop_result.get('side')}")
        print(f"  Type: {stop_result.get('type')}")
        print(f"  Quantity: {stop_result.get('origQty')}")
        print(f"  Stop Price: {stop_result.get('stopPrice')}")
        print(f"  Status: {stop_result.get('status')}")
        
        print(f"\nNote: Manual management required - cancel one order when the other executes")
        
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
    if len(sys.argv) != 7:
        print("Usage: python src/advanced/oco.py <SYMBOL> <SIDE> <QUANTITY> <PRICE> <STOP_PRICE> <STOP_LIMIT_PRICE>")
        print("Example: python src/advanced/oco.py BTCUSDT SELL 0.01 46000.00 44000.00 43500.00")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    side = sys.argv[2].upper()
    quantity = sys.argv[3]
    price = sys.argv[4]
    stop_price = sys.argv[5]
    stop_limit_price = sys.argv[6]
    
    success = place_oco_order(symbol, side, quantity, price, stop_price, stop_limit_price)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()