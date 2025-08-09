#!/usr/bin/env python3

import sys
import os
from dotenv import load_dotenv
from binance.um_futures import UMFutures
from binance.error import ClientError, ServerError
from logger import (setup_logger, log_api_request, log_api_response, 
                   log_validation_error, log_execution_success, 
                   log_execution_error, log_connection_success, log_grid_order)

load_dotenv()


def validate_inputs(symbol, price_low, price_high, grid_levels, quantity_per_level):
    if not symbol or not isinstance(symbol, str):
        return False, "Invalid symbol"
    
    try:
        price_low_val = float(price_low)
        price_high_val = float(price_high)
        levels = int(grid_levels)
        qty_per_level = float(quantity_per_level)
        
        if price_low_val <= 0 or price_high_val <= 0:
            return False, "Prices must be positive"
        
        if price_low_val >= price_high_val:
            return False, "Low price must be less than high price"
        
        if levels < 2:
            return False, "Grid levels must be at least 2"
        
        if qty_per_level <= 0:
            return False, "Quantity per level must be positive"
            
    except ValueError:
        return False, "Invalid numeric format"
    
    return True, "Valid"

def place_grid_orders(symbol, price_low, price_high, grid_levels, quantity_per_level):
    logger = setup_logger(__name__)
    
    # Get API credentials from environment
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("API credentials not found in environment variables")
        print("Error: Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
        return False
    
    # Validate inputs
    is_valid, error_msg = validate_inputs(symbol, price_low, price_high, grid_levels, quantity_per_level)
    if not is_valid:
        log_validation_error(logger, "grid_order_validation", {
            "symbol": symbol,
            "price_low": price_low,
            "price_high": price_high,
            "grid_levels": grid_levels,
            "quantity_per_level": quantity_per_level,
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
        
        # Get current market price
        ticker = client.ticker_price(symbol=symbol)
        current_price = float(ticker['price'])

        # Calculate grid parameters (before logging derived values)
        price_low_val = float(price_low)
        price_high_val = float(price_high)
        levels = int(grid_levels)
        qty_per_level = float(quantity_per_level)

        logger.info("Grid strategy market data retrieved", extra={
            'data': {
                'symbol': symbol,
                'current_price': current_price,
                'grid_range_low': price_low_val,
                'grid_range_high': price_high_val
            }
        })
        
        price_step = (price_high_val - price_low_val) / (levels - 1)
        
        print(f"Grid Order Execution Plan:")
        print(f"Symbol: {symbol}")
        print(f"Current Price: {current_price}")
        print(f"Price Range: {price_low_val} - {price_high_val}")
        print(f"Grid Levels: {levels}")
        print(f"Price Step: {price_step:.2f}")
        print(f"Quantity per Level: {qty_per_level}")
        print(f"Starting execution...\n")
        
        executed_orders = []
        
        # Place orders at each grid level
        for i in range(levels):
            grid_price = price_low_val + (i * price_step)
            
            # Determine order side based on current market price
            if grid_price < current_price:
                # Place buy order below current price
                order_side = 'BUY'
            else:
                # Place sell order above current price
                order_side = 'SELL'
            
            try:
                order_params = {
                    'symbol': symbol,
                    'side': order_side,
                    'type': 'LIMIT',
                    'quantity': qty_per_level,
                    'price': grid_price,
                    'timeInForce': 'GTC'
                }
                
                log_api_request(logger, f"place_grid_order_{i+1}", order_params)
                result = client.new_order(**order_params)
                executed_orders.append(result)
                log_grid_order(logger, i+1, levels, result, grid_price)
                
                print(f"Grid Level {i+1}/{levels} - {order_side} Order:")
                print(f"  Order ID: {result.get('orderId')}")
                print(f"  Price: {grid_price}")
                print(f"  Quantity: {result.get('origQty')}")
                print(f"  Status: {result.get('status')}")
                
            except Exception as e:
                log_execution_error(logger, f"Grid_Order_{i+1}_Error", str(e))
                print(f"Error placing grid order {i+1}: {str(e)}")
                continue
        
        logger.info("Grid order execution completed", extra={
            'data': {
                'order_type': 'GRID',
                'symbol': symbol,
                'current_price': current_price,
                'price_range_low': price_low_val,
                'price_range_high': price_high_val,
                'total_levels': levels,
                'orders_placed': len(executed_orders),
                'success_rate': len(executed_orders) / levels
            }
        })
        print(f"\nGrid Orders Complete: {len(executed_orders)}/{levels} orders placed successfully")
        
        if executed_orders:
            print(f"\nGrid Strategy Active:")
            print(f"- Buy orders below {current_price}")
            print(f"- Sell orders above {current_price}")
            print(f"- Monitor and manage orders as market moves")
        
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
    if len(sys.argv) != 6:
        print("Usage: python src/advanced/grid.py <SYMBOL> <PRICE_LOW> <PRICE_HIGH> <GRID_LEVELS> <QUANTITY_PER_LEVEL>")
        print("Example: python src/advanced/grid.py BTCUSDT 44000.00 46000.00 5 0.01")
        print("Note: Creates buy orders below current price, sell orders above current price")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    price_low = sys.argv[2]
    price_high = sys.argv[3]
    grid_levels = sys.argv[4]
    quantity_per_level = sys.argv[5]
    
    success = place_grid_orders(symbol, price_low, price_high, grid_levels, quantity_per_level)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()