"""
Core data models for the Date Prefix File Renamer application.

This module defines the primary data structures used throughout the application
for representing files, operations, and processing sessions.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from .enums import OperationType, OperationStatus, SessionStatus


@dataclass
class FileSystemItem:
    """
    Represents a file or directory in the filesystem with metadata for renaming operations.
    
    Attributes:
        path: Absolute filesystem path to the item
        name: Current filename or directory name (without path)
        creation_date: Creation timestamp (with fallback to modification date)
        modification_date: Last modification timestamp
        is_directory: Flag indicating if item is a directory
        is_symlink: Flag indicating if item is a symbolic link
        has_date_prefix: Flag indicating if name already has DDMMYYYY_ prefix
        size_bytes: File size in bytes (0 for directories)
    """
    path: Path
    name: str
    creation_date: datetime
    modification_date: datetime
    is_directory: bool
    is_symlink: bool
    has_date_prefix: bool
    size_bytes: int = 0
    
    def __post_init__(self):
        """Validate the FileSystemItem after creation."""
        if not self.path.exists():
            raise ValueError(f"Path does not exist: {self.path}")
        
        if self.creation_date > datetime.now() + timedelta(days=1):
            raise ValueError(f"Creation date cannot be in the future: {self.creation_date}")
    
    @property
    def parent_directory(self) -> Path:
        """Get the parent directory of this item."""
        return self.path.parent
    
    @property
    def file_extension(self) -> str:
        """Get the file extension (empty string for directories)."""
        return self.path.suffix if not self.is_directory else ""


@dataclass
class RenameOperation:
    """
    Represents a single file/folder rename operation with before/after state.
    
    Attributes:
        item: Reference to the FileSystemItem being renamed
        original_name: Original filename/directory name
        target_name: New name with date prefix (DDMMYYYY_originalname)
        operation_type: Type of operation (FILE_RENAME, FOLDER_RENAME, SKIPPED)
        status: Current status of the operation
        error_message: Error details if operation failed
        timestamp: When operation was executed
        rollback_possible: Whether operation can be undone
    """
    item: FileSystemItem
    original_name: str
    target_name: str
    operation_type: OperationType
    status: OperationStatus = OperationStatus.PENDING
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    rollback_possible: bool = True
    
    def __post_init__(self):
        """Validate the RenameOperation after creation."""
        # Ensure target name has the expected prefix format
        if not self.target_name.startswith(self.original_name) and "_" in self.target_name:
            prefix = self.target_name.split("_")[0]
            if len(prefix) == 8:  # DDMMYYYY format (default)
                try:
                    datetime.strptime(prefix, "%d%m%Y")
                except ValueError:
                    raise ValueError(f"Invalid date prefix format: {prefix}")
            elif len(prefix) == 10:  # YYYY-MM-DD format
                try:
                    datetime.strptime(prefix, "%Y-%m-%d")
                except ValueError:
                    raise ValueError(f"Invalid date prefix format: {prefix}")
    
    @property
    def target_path(self) -> Path:
        """Get the full target path after renaming."""
        return self.item.parent_directory / self.target_name
    
    def mark_completed(self, success: bool = True, error_msg: Optional[str] = None):
        """Mark the operation as completed or failed."""
        self.timestamp = datetime.now()
        if success:
            self.status = OperationStatus.COMPLETED
        else:
            self.status = OperationStatus.FAILED
            self.error_message = error_msg
            self.rollback_possible = False


@dataclass
class ProcessingSession:
    """
    Manages a complete directory processing workflow with progress tracking.
    
    Attributes:
        target_directory: Root directory being processed
        discovered_items: All items found during scan
        rename_operations: Operations to be performed
        session_id: Unique identifier for this processing session
        start_time: When processing began
        end_time: When processing completed (None if in progress)
        total_items: Count of all discovered items
        processed_count: Count of completed operations
        skipped_count: Count of skipped items
        error_count: Count of failed operations
        is_dry_run: Whether this is a preview mode (no actual renaming)
    """
    target_directory: Path
    session_id: str
    is_dry_run: bool = False
    discovered_items: List[FileSystemItem] = field(default_factory=list)
    rename_operations: List[RenameOperation] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    processed_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    
    def __post_init__(self):
        """Initialize session with current timestamp."""
        if self.start_time is None:
            self.start_time = datetime.now()
    
    @property
    def total_items(self) -> int:
        """Total count of all discovered items."""
        return len(self.discovered_items)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress as percentage of completed operations."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_count + self.skipped_count + self.error_count) / self.total_items * 100
    
    @property
    def completion_status(self) -> SessionStatus:
        """Determine the current status of the processing session."""
        if self.end_time is None:
            if len(self.rename_operations) == 0:
                return SessionStatus.SCANNING
            else:
                return SessionStatus.PROCESSING
        else:
            if self.error_count > 0 and self.processed_count == 0:
                return SessionStatus.FAILED
            else:
                return SessionStatus.COMPLETED
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Estimate remaining time based on current processing rate."""
        if self.start_time is None or self.processed_count == 0:
            return None
        
        elapsed = datetime.now() - self.start_time
        completed_operations = self.processed_count + self.skipped_count + self.error_count
        
        if completed_operations == 0:
            return None
        
        rate = completed_operations / elapsed.total_seconds()  # operations per second
        remaining_operations = self.total_items - completed_operations
        
        if rate > 0:
            return timedelta(seconds=remaining_operations / rate)
        return None
    
    def add_operation(self, operation: RenameOperation):
        """Add a rename operation to the session."""
        self.rename_operations.append(operation)
    
    def update_progress(self, completed: bool = False, skipped: bool = False, failed: bool = False):
        """Update progress counters."""
        if completed:
            self.processed_count += 1
        elif skipped:
            self.skipped_count += 1
        elif failed:
            self.error_count += 1
    
    def complete_session(self):
        """Mark the session as completed."""
        self.end_time = datetime.now()


@dataclass
class OperationResult:
    """
    Captures the outcome and details of a complete processing session.
    
    Attributes:
        session: Reference to the processing session
        successful_renames: Operations that completed successfully
        failed_operations: Operations that encountered errors
        skipped_items: Items that were skipped (prefixes, symlinks)
        execution_time: Total time taken for processing
        rollback_data: Original names for potential rollback
        summary_message: Human-readable summary of results
    """
    session: ProcessingSession
    successful_renames: List[RenameOperation] = field(default_factory=list)
    failed_operations: List[RenameOperation] = field(default_factory=list)
    skipped_items: List[FileSystemItem] = field(default_factory=list)
    rollback_data: Dict[str, str] = field(default_factory=dict)
    summary_message: str = ""
    
    def __post_init__(self):
        """Generate summary data from the session."""
        self._categorize_operations()
        self._generate_summary_message()
        self._prepare_rollback_data()
    
    @property
    def execution_time(self) -> timedelta:
        """Calculate total execution time."""
        if self.session.start_time and self.session.end_time:
            return self.session.end_time - self.session.start_time
        return timedelta(0)
    
    def _categorize_operations(self):
        """Categorize operations by their final status."""
        for operation in self.session.rename_operations:
            if operation.status == OperationStatus.COMPLETED:
                self.successful_renames.append(operation)
            elif operation.status == OperationStatus.FAILED:
                self.failed_operations.append(operation)
            elif operation.status == OperationStatus.SKIPPED:
                # Convert to FileSystemItem for consistency
                self.skipped_items.append(operation.item)
    
    def _generate_summary_message(self) -> str:
        """Generate human-readable summary of results."""
        total = len(self.session.rename_operations)
        successful = len(self.successful_renames)
        failed = len(self.failed_operations)
        skipped = len(self.skipped_items)
        
        self.summary_message = (
            f"Processing completed in {self.execution_time.total_seconds():.1f} seconds. "
            f"Total items: {total}, "
            f"Successful: {successful}, "
            f"Failed: {failed}, "
            f"Skipped: {skipped}"
        )
    
    def _prepare_rollback_data(self):
        """Prepare data for potential rollback operations."""
        for operation in self.successful_renames:
            original_path = str(operation.item.path)
            target_path = str(operation.target_path)
            self.rollback_data[target_path] = original_path
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        total = len(self.session.rename_operations)
        if total == 0:
            return 100.0
        return (len(self.successful_renames) / total) * 100
    
    @property
    def has_errors(self) -> bool:
        """Check if any operations failed."""
        return len(self.failed_operations) > 0
    
    def get_error_summary(self) -> List[str]:
        """Get a list of error messages for failed operations."""
        return [
            f"{op.original_name}: {op.error_message or 'Unknown error'}"
            for op in self.failed_operations
        ]