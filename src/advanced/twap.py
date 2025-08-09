#!/usr/bin/env python3

import sys
import os
import time
from dotenv import load_dotenv
from binance.um_futures import UMFutures
from binance.error import ClientError, ServerError
from logger import (setup_logger, log_api_request, log_api_response, 
                   log_validation_error, log_execution_success, 
                   log_execution_error, log_connection_success, log_twap_execution)

load_dotenv()


def validate_inputs(symbol, side, total_quantity, time_duration, chunk_size):
    if not symbol or not isinstance(symbol, str):
        return False, "Invalid symbol"
    
    if side not in ['BUY', 'SELL']:
        return False, "Side must be BUY or SELL"
    
    try:
        total_qty = float(total_quantity)
        chunk_qty = float(chunk_size)
        duration = int(time_duration)
        
        if total_qty <= 0 or chunk_qty <= 0:
            return False, "Quantities must be positive"
        
        if duration <= 0:
            return False, "Time duration must be positive"
        
        if chunk_qty > total_qty:
            return False, "Chunk size cannot be larger than total quantity"
            
    except ValueError:
        return False, "Invalid numeric format"
    
    return True, "Valid"

def place_twap_order(symbol, side, total_quantity, time_duration, chunk_size):
    logger = setup_logger(__name__)
    
    # Get API credentials from environment
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("API credentials not found in environment variables")
        print("Error: Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
        return False
    
    # Validate inputs
    is_valid, error_msg = validate_inputs(symbol, side, total_quantity, time_duration, chunk_size)
    if not is_valid:
        log_validation_error(logger, "twap_order_validation", {
            "symbol": symbol,
            "side": side,
            "total_quantity": total_quantity,
            "time_duration": time_duration,
            "chunk_size": chunk_size,
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
        
        # Calculate execution parameters
        total_qty = float(total_quantity)
        chunk_qty = float(chunk_size)
        duration = int(time_duration)
        
        num_chunks = int(total_qty / chunk_qty)
        remaining_qty = total_qty % chunk_qty
        interval = duration / (num_chunks + (1 if remaining_qty > 0 else 0))
        
        logger.info("TWAP execution plan initialized", extra={
            'data': {
                'order_type': 'TWAP',
                'symbol': symbol,
                'side': side,
                'total_quantity': total_qty,
                'chunk_size': chunk_qty,
                'num_chunks': num_chunks,
                'remaining_quantity': remaining_qty,
                'interval_seconds': interval
            }
        })
        
        print(f"TWAP Order Execution Plan:")
        print(f"Total Quantity: {total_quantity}")
        print(f"Chunk Size: {chunk_size}")
        print(f"Number of Chunks: {num_chunks}")
        print(f"Remaining Quantity: {remaining_qty}")
        print(f"Interval: {interval:.2f} seconds")
        print(f"Starting execution...\n")
        
        executed_orders = []
        
        # Execute chunks
        for i in range(num_chunks):
            try:
                order_params = {
                    'symbol': symbol,
                    'side': side,
                    'type': 'MARKET',
                    'quantity': chunk_qty
                }
                
                log_api_request(logger, f"place_twap_chunk_{i+1}", order_params)
                result = client.new_order(**order_params)
                executed_orders.append(result)
                log_twap_execution(logger, i+1, num_chunks, result)
                
                print(f"Chunk {i+1}/{num_chunks} executed:")
                print(f"  Order ID: {result.get('orderId')}")
                print(f"  Quantity: {result.get('origQty')}")
                print(f"  Status: {result.get('status')}")
                
                if i < num_chunks - 1 or remaining_qty > 0:
                    print(f"  Waiting {interval:.2f} seconds...")
                    time.sleep(interval)
                
            except Exception as e:
                log_execution_error(logger, f"TWAP_Chunk_{i+1}_Error", str(e))
                print(f"Error executing chunk {i+1}: {str(e)}")
                break
        
        # Execute remaining quantity if any
        if remaining_qty > 0:
            try:
                order_params = {
                    'symbol': symbol,
                    'side': side,
                    'type': 'MARKET',
                    'quantity': remaining_qty
                }
                
                log_api_request(logger, "place_twap_remaining", order_params)
                result = client.new_order(**order_params)
                executed_orders.append(result)
                log_twap_execution(logger, "remaining", "remaining", result)
                
                print(f"Remaining quantity executed:")
                print(f"  Order ID: {result.get('orderId')}")
                print(f"  Quantity: {result.get('origQty')}")
                print(f"  Status: {result.get('status')}")
                
            except Exception as e:
                log_execution_error(logger, "TWAP_Remaining_Error", str(e))
                print(f"Error executing remaining quantity: {str(e)}")
        
        logger.info("TWAP order execution completed", extra={
            'data': {
                'order_type': 'TWAP',
                'symbol': symbol,
                'side': side,
                'total_orders_executed': len(executed_orders),
                'planned_orders': num_chunks + (1 if remaining_qty > 0 else 0),
                'success_rate': len(executed_orders) / (num_chunks + (1 if remaining_qty > 0 else 0))
            }
        })
        print(f"\nTWAP Order Complete: {len(executed_orders)} orders executed")
        
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
        print("Usage: python src/advanced/twap.py <SYMBOL> <SIDE> <TOTAL_QUANTITY> <TIME_DURATION_SECONDS> <CHUNK_SIZE>")
        print("Example: python src/advanced/twap.py BTCUSDT BUY 0.1 300 0.01")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    side = sys.argv[2].upper()
    total_quantity = sys.argv[3]
    time_duration = sys.argv[4]
    chunk_size = sys.argv[5]
    
    success = place_twap_order(symbol, side, total_quantity, time_duration, chunk_size)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()