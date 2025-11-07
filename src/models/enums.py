"""
Enumerations for the Date Prefix File Renamer application.

This module defines the various enumerated types used throughout the application
for operation types, status tracking, and session management.
"""

from enum import Enum, auto


class OperationType(Enum):
    """
    Enumeration of different types of rename operations supported by the application.
    
    Values:
        FILE_RENAME: Renaming a regular file
        FOLDER_RENAME: Renaming a directory/folder
        SKIPPED: Item was skipped (already has prefix, is symlink, etc.)
        BATCH_RENAME: Multiple items processed as a batch operation
    """
    FILE_RENAME = auto()
    FOLDER_RENAME = auto()
    SKIPPED = auto()
    BATCH_RENAME = auto()
    
    def __str__(self) -> str:
        """Return human-readable string representation."""
        return self.name.replace('_', ' ').title()


class OperationStatus(Enum):
    """
    Enumeration of possible states for a rename operation.
    
    Values:
        PENDING: Operation has been queued but not yet executed
        IN_PROGRESS: Operation is currently being executed
        COMPLETED: Operation completed successfully
        FAILED: Operation encountered an error and could not complete
        SKIPPED: Operation was intentionally skipped
        CANCELLED: Operation was cancelled by user request
    """
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()
    CANCELLED = auto()
    
    def __str__(self) -> str:
        """Return human-readable string representation."""
        return self.name.replace('_', ' ').title()
    
    @property
    def is_terminal(self) -> bool:
        """Check if this status represents a finished operation."""
        return self in {
            OperationStatus.COMPLETED,
            OperationStatus.FAILED,
            OperationStatus.SKIPPED,
            OperationStatus.CANCELLED
        }
    
    @property
    def is_successful(self) -> bool:
        """Check if this status represents a successful operation."""
        return self in {OperationStatus.COMPLETED, OperationStatus.SKIPPED}


class SessionStatus(Enum):
    """
    Enumeration of possible states for a processing session.
    
    Values:
        INITIALIZING: Session is being set up
        SCANNING: Discovering items in the target directory
        READY: Ready to begin processing operations
        PROCESSING: Currently executing rename operations
        PAUSED: Processing has been paused by user
        COMPLETED: All operations finished successfully
        FAILED: Session failed due to critical error
        CANCELLED: Session was cancelled by user
    """
    INITIALIZING = auto()
    SCANNING = auto()
    READY = auto()
    PROCESSING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    
    def __str__(self) -> str:
        """Return human-readable string representation."""
        return self.name.replace('_', ' ').title()
    
    @property
    def is_active(self) -> bool:
        """Check if the session is currently active (can continue processing)."""
        return self in {
            SessionStatus.INITIALIZING,
            SessionStatus.SCANNING,
            SessionStatus.READY,
            SessionStatus.PROCESSING,
            SessionStatus.PAUSED
        }
    
    @property
    def is_finished(self) -> bool:
        """Check if the session has reached a terminal state."""
        return self in {
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
            SessionStatus.CANCELLED
        }
    
    @property
    def allows_new_operations(self) -> bool:
        """Check if new operations can be added to the session."""
        return self in {
            SessionStatus.INITIALIZING,
            SessionStatus.SCANNING,
            SessionStatus.READY
        }


class ValidationLevel(Enum):
    """
    Enumeration of validation strictness levels for file operations.
    
    Values:
        STRICT: Perform all validation checks, reject any suspicious operations
        NORMAL: Standard validation with warnings for potential issues
        PERMISSIVE: Minimal validation, allow most operations
        DISABLED: Skip validation entirely (not recommended)
    """
    STRICT = auto()
    NORMAL = auto()
    PERMISSIVE = auto()
    DISABLED = auto()
    
    def __str__(self) -> str:
        """Return human-readable string representation."""
        return self.name.title()


class LogLevel(Enum):
    """
    Enumeration of logging levels for application debugging and monitoring.
    
    Values:
        DEBUG: Detailed information for diagnosing problems
        INFO: General information about application operation
        WARNING: Warning messages for potential issues
        ERROR: Error messages for operation failures
        CRITICAL: Critical errors that may cause application shutdown
    """
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()
    
    def __str__(self) -> str:
        """Return human-readable string representation."""
        return self.name.title()
    
    @property
    def numeric_level(self) -> int:
        """Return numeric level compatible with Python logging module."""
        level_mapping = {
            LogLevel.DEBUG: 10,
            LogLevel.INFO: 20,
            LogLevel.WARNING: 30,
            LogLevel.ERROR: 40,
            LogLevel.CRITICAL: 50
        }
        return level_mapping[self]


class DateFormatStyle(Enum):
    """
    Enumeration of supported date prefix formatting styles.
    
    Values:
        ISO_DATE: YYYY-MM-DD format
        US_DATE: MM-DD-YYYY format
        COMPACT: YYYYMMDD format (no separators)
        DDMMYYYY: DDMMYYYY format (default)
        YEAR_MONTH: YYYY-MM format (day omitted)
    """
    ISO_DATE = "YYYY-MM-DD"
    US_DATE = "MM-DD-YYYY"
    COMPACT = "YYYYMMDD"
    DDMMYYYY = "DDMMYYYY"
    YEAR_MONTH = "YYYY-MM"
    
    def __str__(self) -> str:
        """Return the format string."""
        return self.value
    
    @property
    def strftime_format(self) -> str:
        """Return the corresponding strftime format string."""
        format_mapping = {
            DateFormatStyle.ISO_DATE: "%Y-%m-%d",
            DateFormatStyle.US_DATE: "%m-%d-%Y",
            DateFormatStyle.COMPACT: "%Y%m%d",
            DateFormatStyle.DDMMYYYY: "%d%m%Y",
            DateFormatStyle.YEAR_MONTH: "%Y-%m"
        }
        return format_mapping[self]
    
    @property
    def example(self) -> str:
        """Return an example of this format style."""
        examples = {
            DateFormatStyle.ISO_DATE: "2024-03-15",
            DateFormatStyle.US_DATE: "03-15-2024",
            DateFormatStyle.COMPACT: "20240315",
            DateFormatStyle.DDMMYYYY: "15032024",
            DateFormatStyle.YEAR_MONTH: "2024-03"
        }
        return examples[self]
    
    @property
    def description(self) -> str:
        """Return a human-readable description of this format style."""
        descriptions = {
            DateFormatStyle.ISO_DATE: "ISO standard format (YYYY-MM-DD)",
            DateFormatStyle.US_DATE: "US format (MM-DD-YYYY)",
            DateFormatStyle.COMPACT: "Compact format (YYYYMMDD)",
            DateFormatStyle.DDMMYYYY: "Day-first format (DDMMYYYY)",
            DateFormatStyle.YEAR_MONTH: "Year and month only (YYYY-MM)"
        }
        return descriptions[self]