import logging
import sys
import os
from datetime import datetime
from typing import Optional
from contextvars import ContextVar
import uuid
from pathlib import Path

# Context variable to store request ID across async calls
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)

class RequestIDFilter(logging.Filter):
    """Filter to add request ID to log records"""
    
    def filter(self, record):
        record.request_id = request_id_context.get() or "no-request-id"
        return True

def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_file_path: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    Setup logging configuration for the FastAPI application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        log_file_path: Custom log file path (defaults to logs/app.log)
        max_file_size: Maximum log file size in bytes before rotation
        backup_count: Number of backup files to keep
    """
    
    # Convert string level to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    if log_to_file:
        if log_file_path is None:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_file_path = str(log_dir / "app.log")
        else:
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create request ID filter
    request_filter = RequestIDFilter()
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(request_filter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_to_file and log_file_path:
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(request_filter)
        root_logger.addHandler(file_handler)
    
    # Configure uvicorn logger
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(numeric_level)
    
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(numeric_level)
    
    # Configure FastAPI logger
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(numeric_level)
    
    # Configure SQLAlchemy logger (set to WARNING to reduce noise)
    sqlalchemy_logger = logging.getLogger("sqlalchemy")
    sqlalchemy_logger.setLevel(logging.WARNING)
    
    logging.info(f"Logging configured - Level: {log_level}, File: {log_to_file}, Console: {log_to_console}")

def get_request_id() -> str:
    """Get current request ID from context"""
    return request_id_context.get() or "no-request-id"

def set_request_id(request_id: str):
    """Set request ID in context"""
    request_id_context.set(request_id)

def generate_request_id() -> str:
    """Generate a new request ID"""
    return str(uuid.uuid4())[:8]

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name"""
    return logging.getLogger(name)

# Default configuration from environment variables
def configure_from_env():
    """Configure logging from environment variables"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    log_to_console = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
    log_file_path = os.getenv("LOG_FILE_PATH")
    max_file_size = int(os.getenv("LOG_MAX_FILE_SIZE", "10485760"))  # 10MB
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    setup_logging(
        log_level=log_level,
        log_to_file=log_to_file,
        log_to_console=log_to_console,
        log_file_path=log_file_path,
        max_file_size=max_file_size,
        backup_count=backup_count
    ) 