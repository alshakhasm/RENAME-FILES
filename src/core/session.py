"""
Processing session management for coordinating file scanning and renaming operations.

This module provides the SessionManager class that orchestrates the complete workflow
of scanning directories, generating rename operations, and executing batch renames
while maintaining session state and progress tracking.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import threading

from ..models import FileSystemItem, RenameOperation, ProcessingSession, OperationResult
from ..models.enums import SessionStatus, OperationType, OperationStatus, ValidationLevel
from ..core.file_scanner import FileScanner
from ..core.renamer import FileRenamer
from ..core.date_extractor import DateExtractor
from ..utils.validators import PrefixValidator
from ..utils.logging import get_operation_logger, create_operation_context
from ..utils.exceptions import ProcessingSessionError, ValidationError, FileSystemError


class SessionManager:
    """
    Manages complete processing sessions from directory scanning to rename execution.
    
    This class coordinates the entire workflow:
    1. Initialize session with target directory
    2. Scan directory for files and folders
    3. Generate rename operations based on creation dates
    4. Validate operations for conflicts and safety
    5. Execute renames with progress tracking
    6. Generate comprehensive results report
    
    Attributes:
        file_scanner: FileScanner instance for directory scanning
        file_renamer: FileRenamer instance for rename operations
        date_extractor: DateExtractor for date operations
        validator: PrefixValidator for validation operations
        current_session: Currently active ProcessingSession
        session_history: List of completed sessions
        logger: Logger instance for operation tracking
    """
    
    def __init__(self,
                 file_scanner: Optional[FileScanner] = None,
                 file_renamer: Optional[FileRenamer] = None,
                 date_extractor: Optional[DateExtractor] = None,
                 validator: Optional[PrefixValidator] = None,
                 validation_level: ValidationLevel = ValidationLevel.NORMAL):
        """
        Initialize the session manager with component instances.
        
        Args:
            file_scanner: FileScanner for directory operations
            file_renamer: FileRenamer for rename operations
            date_extractor: DateExtractor for date operations
            validator: PrefixValidator for validation
            validation_level: Validation strictness level
        """
        # Initialize components with consistent configuration
        self.date_extractor = date_extractor or DateExtractor()
        self.validator = validator or PrefixValidator(validation_level)
        self.file_scanner = file_scanner or FileScanner(
            date_extractor=self.date_extractor,
            include_hidden=False,
            follow_symlinks=False
        )
        self.file_renamer = file_renamer or FileRenamer(
            date_extractor=self.date_extractor,
            validator=self.validator,
            validation_level=validation_level
        )
        
        # Session state
        self.current_session: Optional[ProcessingSession] = None
        self.session_history: List[ProcessingSession] = []
        
        # Threading support
        self._session_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="SessionManager")
        
        # Callbacks
        self.progress_callback: Optional[Callable[[int, int, str], None]] = None
        self.status_callback: Optional[Callable[[SessionStatus, str], None]] = None
        
        self.logger = get_operation_logger(__name__)
    
    def create_session(self, target_directory: Path, is_dry_run: bool = False, 
                      session_id: Optional[str] = None) -> ProcessingSession:
        """
        Create a new processing session for the specified directory.
        
        Args:
            target_directory: Directory to process
            is_dry_run: Whether to simulate operations without executing
            session_id: Optional custom session identifier
            
        Returns:
            New ProcessingSession instance
            
        Raises:
            ProcessingSessionError: If session creation fails
            ValidationError: If target directory is invalid
        """
        with self._session_lock:
            # Validate target directory
            if not target_directory.exists():
                raise ValidationError(f"Target directory does not exist: {target_directory}")
            
            if not target_directory.is_dir():
                raise ValidationError(f"Target path is not a directory: {target_directory}")
            
            # Generate session ID if not provided
            if session_id is None:
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
            
            # Create new session
            session = ProcessingSession(
                target_directory=target_directory,
                session_id=session_id,
                is_dry_run=is_dry_run
            )
            
            # Archive current session if exists
            if self.current_session:
                self._archive_current_session()
            
            self.current_session = session
            
            # Notify status change
            self._notify_status_change(SessionStatus.INITIALIZING, f"Created session: {session_id}")
            
            self.logger.info(f"Created processing session: {session_id} for {target_directory}")
            
            return session
    
    def scan_directory(self, recursive: bool = True, 
                      progress_callback: Optional[Callable[[int, str], None]] = None) -> List[FileSystemItem]:
        """
        Scan the target directory and discover items for processing.
        
        Args:
            recursive: Whether to scan subdirectories recursively
            progress_callback: Optional callback for scan progress updates
            
        Returns:
            List of discovered FileSystemItem objects
            
        Raises:
            ProcessingSessionError: If no active session or scan fails
        """
        if not self.current_session:
            raise ProcessingSessionError("No active session for directory scanning")
        
        with self._session_lock:
            self.current_session.start_time = datetime.now()
            self._notify_status_change(SessionStatus.SCANNING, "Scanning directory for files and folders")
        
        operation_id = create_operation_context("scan", self.current_session.target_directory)
        self.logger.start_operation(operation_id, f"Scanning {self.current_session.target_directory}")
        
        try:
            # Configure scanner with progress callback
            if progress_callback:
                self.file_scanner.progress_callback = progress_callback
            
            # Perform directory scan
            discovered_items = self.file_scanner.scan_directory(
                self.current_session.target_directory,
                recursive=recursive
            )
            
            # Update session with discovered items
            with self._session_lock:
                self.current_session.discovered_items = discovered_items
                scan_summary = self.file_scanner.get_scan_summary()
            
            self.logger.end_operation(
                success=True,
                result=f"Discovered {len(discovered_items)} items",
                **scan_summary
            )
            
            self._notify_status_change(
                SessionStatus.READY, 
                f"Scan complete: {len(discovered_items)} items found"
            )
            
            return discovered_items
            
        except Exception as e:
            self.logger.end_operation(success=False, result=str(e))
            self._notify_status_change(SessionStatus.FAILED, f"Scan failed: {e}")
            raise ProcessingSessionError(f"Directory scan failed: {e}", 
                                       session_id=self.current_session.session_id)
    
    def generate_rename_operations(self) -> List[RenameOperation]:
        """
        Generate rename operations for all discovered items.
        
        Returns:
            List of RenameOperation objects ready for execution
            
        Raises:
            ProcessingSessionError: If no active session or generation fails
        """
        if not self.current_session:
            raise ProcessingSessionError("No active session for operation generation")
        
        if not self.current_session.discovered_items:
            raise ProcessingSessionError("No items discovered - run scan_directory first")
        
        operation_id = create_operation_context("generate_ops", self.current_session.target_directory)
        self.logger.start_operation(operation_id, "Generating rename operations")
        
        try:
            operations = []
            
            for item in self.current_session.discovered_items:
                # Generate preview operation to determine what would happen
                operation = self.file_renamer.preview_rename(item)
                operations.append(operation)
                
                # Log operation type
                if operation.operation_type == OperationType.SKIPPED:
                    self.logger.debug(f"Will skip {item.name} (already has prefix or excluded)")
                else:
                    self.logger.debug(f"Will rename {item.name} -> {operation.target_name}")
            
            # Update session with operations
            with self._session_lock:
                self.current_session.rename_operations = operations
            
            # Categorize operations for summary
            rename_count = sum(1 for op in operations if op.operation_type in [OperationType.FILE_RENAME, OperationType.FOLDER_RENAME])
            skip_count = sum(1 for op in operations if op.operation_type == OperationType.SKIPPED)
            
            self.logger.end_operation(
                success=True,
                result=f"Generated {len(operations)} operations",
                renames=rename_count,
                skipped=skip_count
            )
            
            self._notify_status_change(
                SessionStatus.READY,
                f"Operations ready: {rename_count} renames, {skip_count} skipped"
            )
            
            return operations
            
        except Exception as e:
            self.logger.end_operation(success=False, result=str(e))
            raise ProcessingSessionError(f"Operation generation failed: {e}",
                                       session_id=self.current_session.session_id)
    
    def execute_operations(self, 
                          progress_callback: Optional[Callable[[int, int, str], None]] = None) -> OperationResult:
        """
        Execute all generated rename operations.
        
        Args:
            progress_callback: Optional callback for execution progress
            
        Returns:
            OperationResult with comprehensive execution results
            
        Raises:
            ProcessingSessionError: If no active session or execution fails
        """
        if not self.current_session:
            raise ProcessingSessionError("No active session for operation execution")
        
        if not self.current_session.rename_operations:
            raise ProcessingSessionError("No operations to execute - run generate_rename_operations first")
        
        with self._session_lock:
            self._notify_status_change(SessionStatus.PROCESSING, "Executing rename operations")
        
        operation_id = create_operation_context("execute", self.current_session.target_directory)
        self.logger.start_operation(operation_id, f"Executing {len(self.current_session.rename_operations)} operations")
        
        try:
            # Configure renamer with progress callback
            if progress_callback:
                self.file_renamer.progress_callback = progress_callback
            
            # Execute batch rename
            updated_operations = self.file_renamer.batch_rename(self.current_session.rename_operations)
            
            # Update session with results
            with self._session_lock:
                self.current_session.rename_operations = updated_operations
                
                # Update counters
                for operation in updated_operations:
                    if operation.status == OperationStatus.COMPLETED:
                        self.current_session.processed_count += 1
                    elif operation.status == OperationStatus.SKIPPED:
                        self.current_session.skipped_count += 1
                    elif operation.status == OperationStatus.FAILED:
                        self.current_session.error_count += 1
                
                # Mark session as completed
                self.current_session.complete_session()
            
            # Generate operation result
            operation_result = OperationResult(session=self.current_session)
            
            # Log completion
            rename_summary = self.file_renamer.get_rename_summary()
            self.logger.end_operation(
                success=self.current_session.error_count == 0,
                result=operation_result.summary_message,
                **rename_summary
            )
            
            final_status = SessionStatus.COMPLETED if self.current_session.error_count == 0 else SessionStatus.FAILED
            self._notify_status_change(final_status, operation_result.summary_message)
            
            return operation_result
            
        except Exception as e:
            with self._session_lock:
                self.current_session.complete_session()
            
            self.logger.end_operation(success=False, result=str(e))
            self._notify_status_change(SessionStatus.FAILED, f"Execution failed: {e}")
            raise ProcessingSessionError(f"Operation execution failed: {e}",
                                       session_id=self.current_session.session_id)
    
    def run_complete_workflow(self, target_directory: Path, 
                             is_dry_run: bool = False,
                             recursive: bool = True,
                             progress_callback: Optional[Callable[[str, int, int, str], None]] = None) -> OperationResult:
        """
        Run the complete workflow from directory scan to rename execution.
        
        Args:
            target_directory: Directory to process
            is_dry_run: Whether to simulate operations
            recursive: Whether to process subdirectories
            progress_callback: Optional callback for progress updates (phase, current, total, message)
            
        Returns:
            OperationResult with comprehensive results
        """
        # Create session
        session = self.create_session(target_directory, is_dry_run)
        
        try:
            # Phase 1: Scan directory
            if progress_callback:
                progress_callback("Scanning", 0, 100, "Discovering files and folders...")
            
            discovered_items = self.scan_directory(recursive=recursive)
            
            if progress_callback:
                progress_callback("Scanning", 33, 100, f"Found {len(discovered_items)} items")
            
            # Phase 2: Generate operations
            if progress_callback:
                progress_callback("Planning", 33, 100, "Generating rename operations...")
            
            operations = self.generate_rename_operations()
            
            if progress_callback:
                progress_callback("Planning", 66, 100, f"Generated {len(operations)} operations")
            
            # Phase 3: Execute operations
            if progress_callback:
                progress_callback("Executing", 66, 100, "Performing rename operations...")
            
            result = self.execute_operations()
            
            if progress_callback:
                progress_callback("Complete", 100, 100, result.summary_message)
            
            return result
            
        except Exception as e:
            if progress_callback:
                progress_callback("Failed", 0, 100, str(e))
            raise
    
    def get_current_session(self) -> Optional[ProcessingSession]:
        """Get the currently active processing session."""
        return self.current_session
    
    def get_session_history(self) -> List[ProcessingSession]:
        """Get list of all completed sessions."""
        return self.session_history.copy()
    
    def cancel_current_session(self) -> bool:
        """
        Cancel the currently active session.
        
        Returns:
            True if session was cancelled, False if no active session
        """
        if not self.current_session:
            return False
        
        with self._session_lock:
            # Mark operations as cancelled
            if self.current_session.rename_operations:
                for operation in self.current_session.rename_operations:
                    if operation.status == OperationStatus.PENDING:
                        operation.status = OperationStatus.CANCELLED
            
            self.current_session.complete_session()
            self._notify_status_change(SessionStatus.CANCELLED, "Session cancelled by user")
            
            self._archive_current_session()
        
        return True
    
    def _archive_current_session(self):
        """Archive the current session to history."""
        if self.current_session:
            self.session_history.append(self.current_session)
            self.current_session = None
    
    def _notify_status_change(self, status: SessionStatus, message: str):
        """Notify listeners of session status changes."""
        if self.status_callback:
            try:
                self.status_callback(status, message)
            except Exception as e:
                self.logger.warning(f"Status callback failed: {e}")
        
        self.logger.info(f"Session status: {status} - {message}")
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Set the progress callback for operation updates."""
        self.progress_callback = callback
    
    def set_status_callback(self, callback: Callable[[SessionStatus, str], None]):
        """Set the status callback for session state changes."""
        self.status_callback = callback
    
    def cleanup(self):
        """Clean up resources and shut down the session manager."""
        with self._session_lock:
            if self.current_session:
                self.cancel_current_session()
            
            # Shutdown thread pool
            self._executor.shutdown(wait=True)
        
        self.logger.info("Session manager shutdown complete")
    
    def __enter__(self):
        """Support for context manager usage."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up when exiting context manager."""
        self.cleanup()


class SessionFactory:
    """
    Factory class for creating configured SessionManager instances.
    
    This factory provides convenience methods for creating SessionManager
    instances with common configurations for different use cases.
    """
    
    @staticmethod
    def create_default_session_manager(validation_level: ValidationLevel = ValidationLevel.NORMAL) -> SessionManager:
        """
        Create a SessionManager with default configuration.
        
        Args:
            validation_level: Validation strictness level
            
        Returns:
            Configured SessionManager instance
        """
        return SessionManager(validation_level=validation_level)
    
    @staticmethod
    def create_safe_session_manager() -> SessionManager:
        """
        Create a SessionManager configured for maximum safety.
        
        Returns:
            SessionManager configured with strict validation and safety features
        """
        date_extractor = DateExtractor()
        validator = PrefixValidator(ValidationLevel.STRICT)
        
        scanner = FileScanner(
            date_extractor=date_extractor,
            include_hidden=False,
            follow_symlinks=False,
            max_depth=10  # Limit recursion depth
        )
        
        renamer = FileRenamer(
            date_extractor=date_extractor,
            validator=validator,
            validation_level=ValidationLevel.STRICT,
            create_backups=True,
            allow_overwrites=False
        )
        
        return SessionManager(
            file_scanner=scanner,
            file_renamer=renamer,
            date_extractor=date_extractor,
            validator=validator,
            validation_level=ValidationLevel.STRICT
        )
    
    @staticmethod
    def create_batch_session_manager(max_workers: int = 4) -> SessionManager:
        """
        Create a SessionManager optimized for batch processing.
        
        Args:
            max_workers: Maximum number of worker threads
            
        Returns:
            SessionManager optimized for large batch operations
        """
        session_manager = SessionManager()
        # Configure for batch processing
        session_manager._executor = ThreadPoolExecutor(max_workers=max_workers)
        return session_manager