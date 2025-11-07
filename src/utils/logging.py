"""
Logging configuration and utilities for the Date Prefix File Renamer application.

This module provides centralized logging setup, custom formatters, and
operation tracking capabilities for debugging and monitoring application behavior.
"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, TextIO

from ..models.enums import LogLevel


class OperationFormatter(logging.Formatter):
    """
    Custom formatter for operation tracking with structured output.
    
    This formatter provides consistent, structured log messages that include
    operation context, timing information, and relevant metadata.
    """
    
    def __init__(self, include_thread: bool = False, include_process: bool = False):
        """
        Initialize the operation formatter.
        
        Args:
            include_thread: Whether to include thread information
            include_process: Whether to include process information
        """
        # Define format string with optional components
        format_parts = [
            "%(asctime)s",
            "%(levelname)-8s",
            "%(name)s"
        ]
        
        if include_process:
            format_parts.append("PID:%(process)d")
        
        if include_thread:
            format_parts.append("TID:%(thread)d")
        
        format_parts.extend([
            "%(funcName)s:%(lineno)d",
            "%(message)s"
        ])
        
        format_string = " | ".join(format_parts)
        
        super().__init__(
            fmt=format_string,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record with additional context.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted log message string
        """
        # Add custom fields if present
        if hasattr(record, 'operation_id'):
            record.message = f"[{record.operation_id}] {record.getMessage()}"
        else:
            record.message = record.getMessage()
        
        # Add duration if present
        if hasattr(record, 'duration_ms'):
            record.message += f" (took {record.duration_ms:.1f}ms)"
        
        return super().format(record)


class OperationLogger:
    """
    Specialized logger for tracking file operations and processing sessions.
    
    This class provides methods for logging operation lifecycle events,
    performance metrics, and error conditions with consistent formatting.
    
    Attributes:
        logger: Underlying Python logger instance
        operation_id: Current operation identifier for context
        start_time: Start time for duration tracking
    """
    
    def __init__(self, name: str, operation_id: Optional[str] = None):
        """
        Initialize the operation logger.
        
        Args:
            name: Logger name (typically module or class name)
            operation_id: Optional operation identifier for context
        """
        self.logger = logging.getLogger(name)
        self.operation_id = operation_id
        self.start_time: Optional[datetime] = None
    
    def start_operation(self, operation_id: str, description: str, **kwargs):
        """
        Log the start of an operation.
        
        Args:
            operation_id: Unique identifier for the operation
            description: Human-readable description
            **kwargs: Additional context to include
        """
        self.operation_id = operation_id
        self.start_time = datetime.now()
        
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        message = f"Starting: {description}"
        if context:
            message += f" | {context}"
        
        self._log_with_context(logging.INFO, message)
    
    def end_operation(self, success: bool = True, result: Optional[str] = None, **kwargs):
        """
        Log the completion of an operation.
        
        Args:
            success: Whether the operation succeeded
            result: Optional result description
            **kwargs: Additional context to include
        """
        if self.start_time:
            duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000
        else:
            duration_ms = 0
        
        status = "Completed" if success else "Failed"
        message = f"{status}: {self.operation_id or 'operation'}"
        
        if result:
            message += f" | Result: {result}"
        
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        if context:
            message += f" | {context}"
        
        level = logging.INFO if success else logging.ERROR
        self._log_with_context(level, message, duration_ms=duration_ms)
        
        # Reset operation context
        self.operation_id = None
        self.start_time = None
    
    def log_file_operation(self, operation: str, file_path: Path, success: bool = True, 
                          error: Optional[str] = None, **kwargs):
        """
        Log a file-specific operation.
        
        Args:
            operation: Type of operation (rename, scan, validate, etc.)
            file_path: Path of the file being operated on
            success: Whether the operation succeeded
            error: Error message if operation failed
            **kwargs: Additional context
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"{operation.upper()}: {file_path.name} [{status}]"
        
        if error:
            message += f" | Error: {error}"
        
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        if context:
            message += f" | {context}"
        
        level = logging.INFO if success else logging.ERROR
        self._log_with_context(level, message, file_path=str(file_path))
    
    def log_batch_progress(self, completed: int, total: int, current_file: Optional[str] = None):
        """
        Log batch operation progress.
        
        Args:
            completed: Number of completed operations
            total: Total number of operations
            current_file: Currently processing file name
        """
        percentage = (completed / total * 100) if total > 0 else 0
        message = f"Progress: {completed}/{total} ({percentage:.1f}%)"
        
        if current_file:
            message += f" | Processing: {current_file}"
        
        self._log_with_context(logging.INFO, message)
    
    def log_validation_result(self, item_name: str, valid: bool, reason: Optional[str] = None):
        """
        Log validation results for files or operations.
        
        Args:
            item_name: Name of item being validated
            valid: Whether validation passed
            reason: Reason for validation failure
        """
        status = "VALID" if valid else "INVALID"
        message = f"Validation: {item_name} [{status}]"
        
        if reason:
            message += f" | Reason: {reason}"
        
        level = logging.DEBUG if valid else logging.WARNING
        self._log_with_context(level, message)
    
    def _log_with_context(self, level: int, message: str, **extra):
        """
        Log a message with operation context.
        
        Args:
            level: Logging level
            message: Log message
            **extra: Additional fields to include in log record
        """
        # Add operation context if available
        if self.operation_id:
            extra['operation_id'] = self.operation_id
        
        self.logger.log(level, message, extra=extra)
    
    # Convenience methods for different log levels
    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log an info message."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log an error message."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log a critical message."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)


def setup_logging(
    level: LogLevel = LogLevel.INFO,
    log_file: Optional[Path] = None,
    console_output: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    include_thread_info: bool = False,
    include_process_info: bool = False
) -> Dict[str, logging.Handler]:
    """
    Configure application-wide logging with file and console handlers.
    
    Args:
        level: Minimum logging level
        log_file: Path to log file (optional)
        console_output: Whether to enable console logging
        max_file_size: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        include_thread_info: Include thread information in logs
        include_process_info: Include process information in logs
        
    Returns:
        Dictionary of configured handlers by name
    """
    # Convert LogLevel to Python logging level
    py_level = level.numeric_level
    
    # Create custom formatter
    formatter = OperationFormatter(
        include_thread=include_thread_info,
        include_process=include_process_info
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(py_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    handlers = {}
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(py_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        handlers['console'] = console_handler
    
    # File handler with rotation
    if log_file:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(py_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        handlers['file'] = file_handler
    
    return handlers


def get_operation_logger(name: str, operation_id: Optional[str] = None) -> OperationLogger:
    """
    Get a configured operation logger instance.
    
    Args:
        name: Logger name (typically __name__ from calling module)
        operation_id: Optional operation identifier
        
    Returns:
        Configured OperationLogger instance
    """
    return OperationLogger(name, operation_id)


def configure_logger_for_gui(log_widget_callback: Optional[callable] = None) -> logging.Handler:
    """
    Configure logging for GUI applications with optional widget output.
    
    Args:
        log_widget_callback: Optional callback function for sending logs to GUI widget
        
    Returns:
        GUI-specific log handler
    """
    if log_widget_callback:
        # Create custom handler that sends to GUI widget
        class GUILogHandler(logging.Handler):
            def __init__(self, callback):
                super().__init__()
                self.callback = callback
            
            def emit(self, record):
                try:
                    message = self.format(record)
                    self.callback(message, record.levelname)
                except Exception:
                    # Prevent logging errors from crashing the application
                    pass
        
        gui_handler = GUILogHandler(log_widget_callback)
        gui_handler.setFormatter(OperationFormatter())
        
        # Add to root logger
        logging.getLogger().addHandler(gui_handler)
        
        return gui_handler
    
    return None


def set_log_level(level: LogLevel):
    """
    Change the logging level for all handlers.
    
    Args:
        level: New logging level to set
    """
    py_level = level.numeric_level
    
    # Update root logger
    logging.getLogger().setLevel(py_level)
    
    # Update all handlers
    for handler in logging.getLogger().handlers:
        handler.setLevel(py_level)


def create_operation_context(operation_type: str, target_path: Optional[Path] = None) -> str:
    """
    Create a unique operation identifier for tracking.
    
    Args:
        operation_type: Type of operation (scan, rename, validate, etc.)
        target_path: Optional path being operated on
        
    Returns:
        Unique operation identifier
    """
    timestamp = datetime.now().strftime("%H%M%S")
    
    if target_path:
        path_part = target_path.name[:10]  # First 10 chars of filename
        return f"{operation_type}_{path_part}_{timestamp}"
    else:
        return f"{operation_type}_{timestamp}"


# Default logging configuration for the application
def initialize_default_logging(log_directory: Optional[Path] = None) -> Dict[str, logging.Handler]:
    """
    Initialize logging with sensible defaults for the application.
    
    Args:
        log_directory: Directory for log files (optional)
        
    Returns:
        Dictionary of configured handlers
    """
    log_file = None
    if log_directory:
        log_file = log_directory / "date_prefix_renamer.log"
    
    return setup_logging(
        level=LogLevel.INFO,
        log_file=log_file,
        console_output=True,
        include_thread_info=False,
        include_process_info=False
    )