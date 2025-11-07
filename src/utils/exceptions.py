"""
Custom exception classes for the Date Prefix File Renamer application.

This module defines application-specific exceptions to provide clear error
handling and meaningful error messages for different failure scenarios.
"""

from pathlib import Path
from typing import Optional, List


class DatePrefixRenamerError(Exception):
    """
    Base exception class for all Date Prefix File Renamer errors.
    
    This serves as the root exception that can catch any application-specific
    error. All other exceptions in this module inherit from this class.
    
    Attributes:
        message: Human-readable error message
        details: Additional context or technical details
        error_code: Optional error code for programmatic handling
    """
    
    def __init__(self, message: str, details: Optional[str] = None, error_code: Optional[str] = None):
        """
        Initialize the base exception.
        
        Args:
            message: Primary error message
            details: Additional context or technical details
            error_code: Optional error code for programmatic handling
        """
        super().__init__(message)
        self.message = message
        self.details = details
        self.error_code = error_code
    
    def __str__(self) -> str:
        """Return formatted error message."""
        if self.details:
            return f"{self.message} Details: {self.details}"
        return self.message


class FileSystemError(DatePrefixRenamerError):
    """
    Exception for filesystem-related errors.
    
    Raised when operations fail due to filesystem issues such as permissions,
    disk space, or file system limitations.
    
    Attributes:
        path: The filesystem path that caused the error
        operation: The operation that was attempted
    """
    
    def __init__(self, message: str, path: Optional[Path] = None, 
                 operation: Optional[str] = None, **kwargs):
        """
        Initialize filesystem error.
        
        Args:
            message: Error message
            path: The path that caused the error
            operation: The operation that failed
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.path = path
        self.operation = operation
    
    def __str__(self) -> str:
        """Return formatted error message with path context."""
        parts = [self.message]
        if self.path:
            parts.append(f"Path: {self.path}")
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class FileNotFoundError(FileSystemError):
    """
    Exception for when a required file or directory cannot be found.
    
    This exception is raised when the application attempts to access a file
    or directory that does not exist.
    """
    
    def __init__(self, path: Path, operation: str = "access", **kwargs):
        """
        Initialize file not found error.
        
        Args:
            path: The path that was not found
            operation: The operation that was attempted
            **kwargs: Additional arguments for base class
        """
        message = f"File or directory not found: {path}"
        super().__init__(message, path=path, operation=operation, 
                        error_code="FILE_NOT_FOUND", **kwargs)


class PermissionError(FileSystemError):
    """
    Exception for permission-related filesystem errors.
    
    Raised when the application lacks necessary permissions to perform
    filesystem operations such as reading, writing, or renaming files.
    """
    
    def __init__(self, path: Path, operation: str, required_permission: str = "read/write", **kwargs):
        """
        Initialize permission error.
        
        Args:
            path: The path that lacks permissions
            operation: The operation that was denied
            required_permission: Description of required permissions
            **kwargs: Additional arguments for base class
        """
        message = f"Permission denied for {operation} on {path}"
        details = f"Required permission: {required_permission}"
        super().__init__(message, path=path, operation=operation, 
                        details=details, error_code="PERMISSION_DENIED", **kwargs)


class DiskSpaceError(FileSystemError):
    """
    Exception for insufficient disk space errors.
    
    Raised when filesystem operations fail due to insufficient available
    disk space on the target volume.
    """
    
    def __init__(self, path: Path, required_space: Optional[int] = None, 
                 available_space: Optional[int] = None, **kwargs):
        """
        Initialize disk space error.
        
        Args:
            path: The path where space is needed
            required_space: Required space in bytes
            available_space: Available space in bytes
            **kwargs: Additional arguments for base class
        """
        message = "Insufficient disk space for operation"
        
        details_parts = []
        if required_space:
            details_parts.append(f"Required: {required_space:,} bytes")
        if available_space:
            details_parts.append(f"Available: {available_space:,} bytes")
        
        details = " | ".join(details_parts) if details_parts else None
        
        super().__init__(message, path=path, operation="write", 
                        details=details, error_code="DISK_SPACE", **kwargs)


class ValidationError(DatePrefixRenamerError):
    """
    Exception for validation failures.
    
    Raised when input validation fails, such as invalid filenames,
    unsupported file types, or constraint violations.
    
    Attributes:
        field: The field or input that failed validation
        value: The invalid value
        constraint: Description of the violated constraint
    """
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 value: Optional[str] = None, constraint: Optional[str] = None, **kwargs):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: The field that failed validation
            value: The invalid value
            constraint: Description of constraint that was violated
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, error_code="VALIDATION_FAILED", **kwargs)
        self.field = field
        self.value = value
        self.constraint = constraint
    
    def __str__(self) -> str:
        """Return formatted validation error message."""
        parts = [self.message]
        if self.field:
            parts.append(f"Field: {self.field}")
        if self.value:
            parts.append(f"Value: {self.value}")
        if self.constraint:
            parts.append(f"Constraint: {self.constraint}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class InvalidFilenameError(ValidationError):
    """
    Exception for invalid filename errors.
    
    Raised when a filename violates naming conventions, contains
    forbidden characters, or exceeds length limits.
    """
    
    def __init__(self, filename: str, reason: str, **kwargs):
        """
        Initialize invalid filename error.
        
        Args:
            filename: The invalid filename
            reason: Reason why filename is invalid
            **kwargs: Additional arguments for base class
        """
        message = f"Invalid filename: {filename}"
        super().__init__(message, field="filename", value=filename, 
                        constraint=reason, error_code="INVALID_FILENAME", **kwargs)


class DateExtractionError(DatePrefixRenamerError):
    """
    Exception for date extraction failures.
    
    Raised when the application cannot extract or parse creation dates
    from files, or when date formatting operations fail.
    
    Attributes:
        path: The file path where date extraction failed
        date_source: The source of date information (creation_time, modification_time, etc.)
    """
    
    def __init__(self, message: str, path: Optional[Path] = None, 
                 date_source: Optional[str] = None, **kwargs):
        """
        Initialize date extraction error.
        
        Args:
            message: Error message
            path: Path where extraction failed
            date_source: Source of date information
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, error_code="DATE_EXTRACTION", **kwargs)
        self.path = path
        self.date_source = date_source
    
    def __str__(self) -> str:
        """Return formatted date extraction error message."""
        parts = [self.message]
        if self.path:
            parts.append(f"Path: {self.path}")
        if self.date_source:
            parts.append(f"Date source: {self.date_source}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class RenameOperationError(DatePrefixRenamerError):
    """
    Exception for rename operation failures.
    
    Raised when file or directory rename operations fail, including
    conflicts, locks, or other rename-specific issues.
    
    Attributes:
        source_path: Original path of the item being renamed
        target_path: Intended destination path
        operation_id: Optional identifier for the failed operation
    """
    
    def __init__(self, message: str, source_path: Optional[Path] = None,
                 target_path: Optional[Path] = None, operation_id: Optional[str] = None, **kwargs):
        """
        Initialize rename operation error.
        
        Args:
            message: Error message
            source_path: Original path
            target_path: Intended destination path
            operation_id: Operation identifier
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, error_code="RENAME_FAILED", **kwargs)
        self.source_path = source_path
        self.target_path = target_path
        self.operation_id = operation_id
    
    def __str__(self) -> str:
        """Return formatted rename operation error message."""
        parts = [self.message]
        if self.source_path:
            parts.append(f"Source: {self.source_path}")
        if self.target_path:
            parts.append(f"Target: {self.target_path}")
        if self.operation_id:
            parts.append(f"Operation: {self.operation_id}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class FileConflictError(RenameOperationError):
    """
    Exception for filename conflicts.
    
    Raised when a rename operation would create a naming conflict
    with an existing file or directory.
    """
    
    def __init__(self, source_path: Path, target_path: Path, 
                 conflict_type: str = "file_exists", **kwargs):
        """
        Initialize file conflict error.
        
        Args:
            source_path: Source file path
            target_path: Target path that conflicts
            conflict_type: Type of conflict (file_exists, case_conflict, etc.)
            **kwargs: Additional arguments for base class
        """
        message = f"File conflict: {target_path.name} already exists"
        details = f"Conflict type: {conflict_type}"
        super().__init__(message, source_path=source_path, target_path=target_path,
                        details=details, error_code="FILE_CONFLICT", **kwargs)


class ProcessingSessionError(DatePrefixRenamerError):
    """
    Exception for processing session management errors.
    
    Raised when session operations fail, such as initialization,
    state management, or session corruption.
    
    Attributes:
        session_id: Identifier of the failed session
        session_state: Current state of the session
    """
    
    def __init__(self, message: str, session_id: Optional[str] = None,
                 session_state: Optional[str] = None, **kwargs):
        """
        Initialize processing session error.
        
        Args:
            message: Error message
            session_id: Session identifier
            session_state: Current session state
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, error_code="SESSION_ERROR", **kwargs)
        self.session_id = session_id
        self.session_state = session_state
    
    def __str__(self) -> str:
        """Return formatted session error message."""
        parts = [self.message]
        if self.session_id:
            parts.append(f"Session: {self.session_id}")
        if self.session_state:
            parts.append(f"State: {self.session_state}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class BatchOperationError(DatePrefixRenamerError):
    """
    Exception for batch operation failures.
    
    Raised when batch processing operations encounter errors that
    affect multiple files or require rollback operations.
    
    Attributes:
        failed_operations: List of operations that failed
        completed_operations: List of operations that succeeded before failure
        rollback_possible: Whether the batch can be rolled back
    """
    
    def __init__(self, message: str, failed_operations: Optional[List[str]] = None,
                 completed_operations: Optional[List[str]] = None, 
                 rollback_possible: bool = False, **kwargs):
        """
        Initialize batch operation error.
        
        Args:
            message: Error message
            failed_operations: List of failed operation identifiers
            completed_operations: List of completed operation identifiers
            rollback_possible: Whether rollback is possible
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, error_code="BATCH_ERROR", **kwargs)
        self.failed_operations = failed_operations or []
        self.completed_operations = completed_operations or []
        self.rollback_possible = rollback_possible
    
    def __str__(self) -> str:
        """Return formatted batch operation error message."""
        parts = [self.message]
        if self.failed_operations:
            parts.append(f"Failed: {len(self.failed_operations)} operations")
        if self.completed_operations:
            parts.append(f"Completed: {len(self.completed_operations)} operations")
        parts.append(f"Rollback possible: {self.rollback_possible}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class ConfigurationError(DatePrefixRenamerError):
    """
    Exception for configuration and settings errors.
    
    Raised when application configuration is invalid, missing,
    or contains conflicting settings.
    
    Attributes:
        config_key: The configuration key that caused the error
        config_value: The invalid configuration value
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None,
                 config_value: Optional[str] = None, **kwargs):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Configuration key that caused error
            config_value: Invalid configuration value
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)
        self.config_key = config_key
        self.config_value = config_value
    
    def __str__(self) -> str:
        """Return formatted configuration error message."""
        parts = [self.message]
        if self.config_key:
            parts.append(f"Key: {self.config_key}")
        if self.config_value:
            parts.append(f"Value: {self.config_value}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


# Convenience function for error handling
def handle_filesystem_error(operation: str, path: Path, original_error: Exception) -> FileSystemError:
    """
    Convert generic filesystem errors to application-specific exceptions.
    
    Args:
        operation: The operation that failed
        path: The path where the error occurred
        original_error: The original exception that was caught
        
    Returns:
        Appropriate FileSystemError subclass
    """
    error_message = str(original_error)
    
    if "No such file or directory" in error_message or "cannot find the path" in error_message:
        return FileNotFoundError(path, operation, details=error_message)
    elif "Permission denied" in error_message or "Access is denied" in error_message:
        return PermissionError(path, operation, details=error_message)
    elif "No space left" in error_message or "disk full" in error_message:
        return DiskSpaceError(path, details=error_message)
    else:
        return FileSystemError(f"Filesystem error during {operation}", 
                             path=path, operation=operation, details=error_message)