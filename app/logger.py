"""
Logging Configuration Module

This module provides a centralized logging system for the Campaign Management Service.
It creates a singleton logger class that can be accessed dynamically from anywhere in the application.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json


class CampaignLogger:
    """
    Singleton Logger Class for Campaign Management Service.
    
    Provides centralized logging with file and console handlers,
    structured log formats, and dynamic access throughout the application.
    """
    
    _instance: Optional['CampaignLogger'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Ensure only one instance of logger exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(CampaignLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logger with file and console handlers."""
        if self._initialized:
            return
        
        # Create logs directory
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        self.logger = logging.getLogger("campaign_service")
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            # Create formatters
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            simple_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Console Handler (stdout)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(simple_formatter)
            self.logger.addHandler(console_handler)
            
            # File Handler - All logs
            all_logs_file = self.logs_dir / "campaign_service.log"
            file_handler = logging.FileHandler(all_logs_file, mode='a', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(file_handler)
            
            # File Handler - Error logs only
            error_logs_file = self.logs_dir / "errors.log"
            error_handler = logging.FileHandler(error_logs_file, mode='a', encoding='utf-8')
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(error_handler)
            
            # File Handler - API requests (JSON format for analytics)
            api_logs_file = self.logs_dir / "api_requests.log"
            self.api_handler = logging.FileHandler(api_logs_file, mode='a', encoding='utf-8')
            self.api_handler.setLevel(logging.INFO)
        
        self._initialized = True
        self.info("="*80)
        self.info("Campaign Management Service Logger Initialized")
        self.info(f"Logs Directory: {self.logs_dir.absolute()}")
        self.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.info("="*80)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message with optional exception traceback."""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message with optional exception traceback."""
        self.logger.critical(message, exc_info=exc_info, extra=kwargs)
    
    def log_request(self, method: str, path: str, status_code: int, 
                   process_time: float, client_ip: str, request_id: int):
        """
        Log API request in structured JSON format for analytics.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            status_code: Response status code
            process_time: Request processing time in seconds
            client_ip: Client IP address
            request_id: Unique request identifier
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "process_time": round(process_time, 3),
            "client_ip": client_ip,
            "level": "INFO" if status_code < 400 else "WARNING"
        }
        
        # Write JSON log entry
        self.api_handler.stream.write(json.dumps(log_data) + "\n")
        self.api_handler.stream.flush()
    
    def log_customer_operation(self, operation: str, customer_id: Optional[int], 
                              email: str, success: bool = True, error: Optional[str] = None):
        """
        Log customer-related operations.
        
        Args:
            operation: Operation type (create, get, update, delete)
            customer_id: Customer ID (if available)
            email: Customer email
            success: Whether operation succeeded
            error: Error message if operation failed
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"Customer {operation.upper()}: ID={customer_id}, Email={email}, Status={status}"
        
        if error:
            message += f", Error={error}"
            self.error(message)
        else:
            self.info(message)
    
    def log_campaign_operation(self, operation: str, campaign_id: Optional[int],
                              campaign_name: str, campaign_type: str = None,
                              success: bool = True, error: Optional[str] = None):
        """
        Log campaign-related operations.
        
        Args:
            operation: Operation type (create, get, update, delete)
            campaign_id: Campaign ID (if available)
            campaign_name: Campaign name
            campaign_type: Campaign discount type (cart/delivery)
            success: Whether operation succeeded
            error: Error message if operation failed
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"Campaign {operation.upper()}: ID={campaign_id}, Name={campaign_name}"
        
        if campaign_type:
            message += f", Type={campaign_type}"
        
        message += f", Status={status}"
        
        if error:
            message += f", Error={error}"
            self.error(message)
        else:
            self.info(message)
    
    def log_discount_operation(self, operation: str, campaign_id: int, customer_id: int,
                              discount_amount: float = None, cart_value: float = None,
                              success: bool = True, error: Optional[str] = None):
        """
        Log discount-related operations.
        
        Args:
            operation: Operation type (available, apply, usage)
            campaign_id: Campaign ID
            customer_id: Customer ID
            discount_amount: Calculated discount amount
            cart_value: Cart value
            success: Whether operation succeeded
            error: Error message if operation failed
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"Discount {operation.upper()}: CampaignID={campaign_id}, CustomerID={customer_id}"
        
        if cart_value is not None:
            message += f", CartValue={cart_value}"
        
        if discount_amount is not None:
            message += f", DiscountAmount={discount_amount}"
        
        message += f", Status={status}"
        
        if error:
            message += f", Error={error}"
            self.error(message)
        else:
            self.info(message)
    
    def log_validation_error(self, entity: str, field: str, value: any, reason: str):
        """
        Log validation errors.
        
        Args:
            entity: Entity being validated (customer, campaign, discount)
            field: Field that failed validation
            value: Value that failed
            reason: Reason for validation failure
        """
        self.warning(
            f"Validation Error: Entity={entity}, Field={field}, "
            f"Value={value}, Reason={reason}"
        )
    
    def log_business_rule_violation(self, rule: str, details: str):
        """
        Log business rule violations.
        
        Args:
            rule: Business rule that was violated
            details: Details of the violation
        """
        self.warning(f"Business Rule Violation: Rule={rule}, Details={details}")
    
    def log_database_operation(self, operation: str, table: str, 
                              success: bool = True, error: Optional[str] = None):
        """
        Log database operations.
        
        Args:
            operation: Database operation (select, insert, update, delete)
            table: Table name
            success: Whether operation succeeded
            error: Error message if operation failed
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"Database {operation.upper()}: Table={table}, Status={status}"
        
        if error:
            message += f", Error={error}"
            self.error(message, exc_info=True)
        else:
            self.debug(message)
    
    def get_logger(self, module_name: str) -> logging.Logger:
        """
        Get a logger instance for a specific module.
        
        Args:
            module_name: Name of the module requesting logger
            
        Returns:
            logging.Logger: Logger instance for the module
        """
        return logging.getLogger(f"campaign_service.{module_name}")


# Create singleton instance
campaign_logger = CampaignLogger()


def get_logger(module_name: str = None) -> CampaignLogger:
    """
    Get the campaign logger instance.
    
    This function can be called from anywhere in the application to access
    the centralized logger.
    
    Args:
        module_name: Optional module name for contextual logging
        
    Returns:
        CampaignLogger: The singleton logger instance
    
    Example:
        >>> from app.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("This is a log message")
    """
    return campaign_logger
