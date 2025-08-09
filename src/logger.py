#!/usr/bin/env python3

import logging
import json
from datetime import datetime, timezone
import traceback
import os
from zoneinfo import ZoneInfo


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        tz_name = os.getenv("BOT_LOG_TZ", "Asia/Kolkata")
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = timezone.utc
        log_entry = {
            "timestamp": datetime.now(tz).isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        }
        
        # Add structured data if present
        if hasattr(record, 'data'):
            log_entry["data"] = record.data
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logger(name):
    """Setup structured logger"""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # File handler with JSON formatter
    file_handler = logging.FileHandler('bot.log')
    file_handler.setFormatter(JSONFormatter())
    
    # Console handler with simple formatter for readability
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def log_api_request(logger, action, params):
    """Log API request attempts"""
    logger.info(f"API request: {action}", extra={
        'data': {
            'action': action,
            'parameters': params
        }
    })


def log_api_response(logger, action, response_data):
    """Log API responses with order data"""
    logger.info(f"{action} successful", extra={
        'data': response_data
    })


def log_validation_error(logger, error_type, details):
    """Log input validation failures"""
    logger.error(f"Validation failed: {error_type}", extra={
        'data': {
            'error_type': error_type,
            'details': details
        }
    })


def log_execution_success(logger, order_type, order_data):
    """Log successful order execution"""
    logger.info(f"{order_type} order executed successfully", extra={
        'data': {
            'order_type': order_type,
            'symbol': order_data.get('symbol'),
            'side': order_data.get('side'),
            'quantity': order_data.get('origQty'),
            'order_id': order_data.get('orderId'),
            'status': order_data.get('status'),
            'executed_qty': order_data.get('executedQty'),
            'executed_price': order_data.get('fills', [{}])[0].get('price') if order_data.get('fills') else None
        }
    })


def log_execution_error(logger, error_type, error_details, api_code=None):
    """Log order execution errors"""
    error_data = {
        'error_type': error_type,
        'details': error_details
    }
    
    if api_code:
        error_data['api_code'] = api_code
    
    logger.error(f"Order execution failed: {error_type}", extra={
        'data': error_data
    })


def log_connection_success(logger, server_time):
    """Log successful API connection"""
    logger.info("Connected to Binance testnet", extra={
        'data': {
            'server_time': server_time,
            'connection_status': 'success'
        }
    })


def log_twap_execution(logger, chunk_num, total_chunks, order_data):
    """Log TWAP chunk execution"""
    logger.info(f"TWAP chunk {chunk_num}/{total_chunks} executed", extra={
        'data': {
            'order_type': 'TWAP_CHUNK',
            'chunk_number': chunk_num,
            'total_chunks': total_chunks,
            'symbol': order_data.get('symbol'),
            'side': order_data.get('side'),
            'quantity': order_data.get('origQty'),
            'order_id': order_data.get('orderId'),
            'status': order_data.get('status')
        }
    })


def log_grid_order(logger, level_num, total_levels, order_data, grid_price):
    """Log grid order placement"""
    logger.info(f"Grid order {level_num}/{total_levels} placed", extra={
        'data': {
            'order_type': 'GRID_ORDER',
            'grid_level': level_num,
            'total_levels': total_levels,
            'grid_price': grid_price,
            'symbol': order_data.get('symbol'),
            'side': order_data.get('side'),
            'quantity': order_data.get('origQty'),
            'order_id': order_data.get('orderId'),
            'status': order_data.get('status')
        }
    })