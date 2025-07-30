"""
Logging configuration for Teams Agent Bot.

This module provides a centralized logging system with structured logging,
multiple output formats, and configurable log levels. It uses structlog
for enhanced logging capabilities and supports both console and file output.
"""

import logging
import sys
from typing import Optional, Dict, Any
from datetime import datetime
import structlog
from structlog.stdlib import LoggerFactory

from config.settings import settings


class StructuredLogger:
    """
    Structured logger wrapper for Teams Agent Bot.
    
    This class provides a unified logging interface with structured logging
    capabilities, making it easier to debug and monitor the application.
    """
    
    def __init__(self, name: str):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (usually module name)
        """
        self.name = name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> structlog.stdlib.BoundLogger:
        """
        Set up structured logger with proper configuration.
        
        Returns:
            Configured structured logger instance
        """
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer() if settings.logging.enable_file else structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            logger_factory=LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Get standard library logger
        stdlib_logger = logging.getLogger(self.name)
        stdlib_logger.setLevel(getattr(logging, settings.logging.level.upper()))
        
        # Add handlers based on configuration
        if settings.logging.enable_console:
            self._add_console_handler(stdlib_logger)
        
        if settings.logging.enable_file and settings.logging.file_path:
            self._add_file_handler(stdlib_logger)
        
        # Return structured logger
        return structlog.get_logger(self.name)
    
    def _add_console_handler(self, logger: logging.Logger):
        """Add console handler to logger."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, settings.logging.level.upper()))
        
        # Use structured format for console
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    def _add_file_handler(self, logger: logging.Logger):
        """Add file handler to logger."""
        try:
            file_handler = logging.FileHandler(settings.logging.file_path)
            file_handler.setLevel(getattr(logging, settings.logging.level.upper()))
            
            # Use JSON format for file logging
            formatter = logging.Formatter(
                fmt='{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Fallback to console if file logging fails
            print(f"Warning: Could not set up file logging: {e}")
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data."""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with structured data."""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception message with structured data and traceback."""
        self.logger.exception(message, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structured logger instance
    """
    return StructuredLogger(name)


# Convenience function for common logging patterns
def log_function_call(logger: StructuredLogger, func_name: str, **kwargs):
    """
    Log function call with parameters.
    
    Args:
        logger: Logger instance
        func_name: Name of the function being called
        **kwargs: Function parameters to log
    """
    logger.info(f"Function call: {func_name}", function=func_name, parameters=kwargs)


def log_function_result(logger: StructuredLogger, func_name: str, result: Any, **kwargs):
    """
    Log function result.
    
    Args:
        logger: Logger instance
        func_name: Name of the function
        result: Function result
        **kwargs: Additional context
    """
    logger.info(f"Function result: {func_name}", function=func_name, result=result, **kwargs)


def log_error_with_context(logger: StructuredLogger, error: Exception, context: Dict[str, Any] = None):
    """
    Log error with additional context.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context information
    """
    context = context or {}
    logger.error(
        f"Error occurred: {str(error)}",
        error_type=type(error).__name__,
        error_message=str(error),
        **context
    )


# Example usage:
# logger = get_logger(__name__)
# logger.info("Application started", version="1.0.0", environment="production")
# log_function_call(logger, "process_message", user_id="123", message="Hello") 