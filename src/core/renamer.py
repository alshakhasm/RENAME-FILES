"""
Core file renaming functionality for the Date Prefix File Renamer application.

This module provides the FileRenamer interface and implementation for performing
safe file and directory rename operations with comprehensive error handling.
"""

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable
from datetime import datetime

from ..models import FileSystemItem, RenameOperation, OperationResult
from ..models.enums import OperationType, OperationStatus, ValidationLevel
from ..core.date_extractor import DateExtractor
from ..utils.validators import PrefixValidator
from ..utils.logging import get_operation_logger
from ..utils.exceptions import (
    RenameOperationError, FileConflictError, ValidationError, 
    FileSystemError, PermissionError, BatchOperationError
)


class FileRenamerInterface(ABC):
    """
    Abstract interface for file and directory renaming operations.
    
    This interface defines the contract for performing safe rename operations
    with proper validation, conflict resolution, and error handling.
    """
    
    @abstractmethod
    def rename_item(self, operation: RenameOperation) -> RenameOperation:
        """
        Perform a single rename operation.
        
        Args:
            operation: RenameOperation object describing the rename
            
        Returns:
            Updated RenameOperation with result status
        """
        pass
    
    @abstractmethod
    def batch_rename(self, operations: List[RenameOperation]) -> List[RenameOperation]:
        """
        Perform multiple rename operations as a batch.
        
        Args:
            operations: List of RenameOperation objects
            
        Returns:
            List of updated RenameOperation objects with results
        """
        pass
    
    @abstractmethod
    def preview_rename(self, item: FileSystemItem) -> RenameOperation:
        """
        Preview what a rename operation would do without executing it.
        
        Args:
            item: FileSystemItem to preview rename for
            
        Returns:
            RenameOperation showing proposed changes
        """
        pass


class FileRenamer(FileRenamerInterface):
    """
    Comprehensive file and directory renamer implementation.
    
    This class provides safe, validated file renaming operations with support
    for batch processing, conflict resolution, and rollback capabilities.
    
    Attributes:
        date_extractor: DateExtractor for date operations
        validator: PrefixValidator for validation operations
        validation_level: Level of validation to perform
        create_backups: Whether to create backup copies before renaming
        allow_overwrites: Whether to allow overwriting existing files
        dry_run_mode: Whether to simulate operations without actually renaming
        progress_callback: Optional callback for progress updates
        logger: Logger instance for operation tracking
    """
    
    def __init__(self,
                 date_extractor: Optional[DateExtractor] = None,
                 validator: Optional[PrefixValidator] = None,
                 validation_level: ValidationLevel = ValidationLevel.NORMAL,
                 create_backups: bool = False,
                 allow_overwrites: bool = False,
                 dry_run_mode: bool = False,
                 progress_callback: Optional[Callable[[int, int, str], None]] = None):
        """
        Initialize the file renamer with configuration options.
        
        Args:
            date_extractor: DateExtractor for date operations
            validator: PrefixValidator for validation
            validation_level: How strict to be with validation
            create_backups: Whether to create backups before renaming
            allow_overwrites: Whether to allow overwriting existing files
            dry_run_mode: Whether to simulate operations without executing
            progress_callback: Optional callback function(current, total, filename)
        """
        self.date_extractor = date_extractor or DateExtractor()
        self.validator = validator or PrefixValidator(validation_level)
        self.validation_level = validation_level
        self.create_backups = create_backups
        self.allow_overwrites = allow_overwrites
        self.dry_run_mode = dry_run_mode
        self.progress_callback = progress_callback
        
        self.logger = get_operation_logger(__name__)
        
        # Statistics tracking
        self.rename_stats = {
            'successful_renames': 0,
            'failed_renames': 0,
            'skipped_items': 0,
            'conflicts_resolved': 0,
            'backups_created': 0
        }
    
    def rename_item(self, operation: RenameOperation) -> RenameOperation:
        """
        Perform a single rename operation with full validation and error handling.
        
        Args:
            operation: RenameOperation object describing the rename
            
        Returns:
            Updated RenameOperation with result status
        """
        operation_id = f"rename_{operation.item.name}_{datetime.now().strftime('%H%M%S')}"
        
        self.logger.start_operation(
            operation_id, 
            f"Renaming {operation.item.name} -> {operation.target_name}"
        )
        
        try:
            # Validate operation
            if not self._validate_operation(operation):
                operation.mark_completed(success=False, error_msg="Validation failed")
                self.rename_stats['failed_renames'] += 1
                self.logger.end_operation(success=False, result="Validation failed")
                return operation
            
            # Check if item already has correct prefix
            if operation.item.has_date_prefix and operation.original_name == operation.target_name:
                operation.status = OperationStatus.SKIPPED
                operation.operation_type = OperationType.SKIPPED
                self.rename_stats['skipped_items'] += 1
                self.logger.end_operation(success=True, result="Already has correct prefix")
                return operation
            
            # Handle conflicts
            conflict_resolved = self._resolve_conflicts(operation)
            if not conflict_resolved:
                operation.mark_completed(success=False, error_msg="Could not resolve naming conflict")
                self.rename_stats['failed_renames'] += 1
                self.logger.end_operation(success=False, result="Naming conflict")
                return operation
            
            # Create backup if requested
            if self.create_backups and not self.dry_run_mode:
                try:
                    self._create_backup(operation.item.path)
                    self.rename_stats['backups_created'] += 1
                except Exception as e:
                    self.logger.warning(f"Failed to create backup: {e}")
            
            # Perform the actual rename
            if self.dry_run_mode:
                # Simulate the rename
                operation.mark_completed(success=True)
                self.logger.info(f"DRY RUN: Would rename {operation.original_name} -> {operation.target_name}")
            else:
                success = self._execute_rename(operation)
                operation.mark_completed(success=success)
                
                if success:
                    self.rename_stats['successful_renames'] += 1
                else:
                    self.rename_stats['failed_renames'] += 1
            
            self.logger.end_operation(
                success=operation.status == OperationStatus.COMPLETED,
                result=f"Rename {'successful' if operation.status == OperationStatus.COMPLETED else 'failed'}"
            )
            
            return operation
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            operation.mark_completed(success=False, error_msg=error_msg)
            self.rename_stats['failed_renames'] += 1
            self.logger.end_operation(success=False, result=error_msg)
            return operation
    
    def batch_rename(self, operations: List[RenameOperation]) -> List[RenameOperation]:
        """
        Perform multiple rename operations as a batch with rollback support.
        
        Args:
            operations: List of RenameOperation objects
            
        Returns:
            List of updated RenameOperation objects with results
        """
        if not operations:
            return []
        
        operation_id = f"batch_rename_{len(operations)}_{datetime.now().strftime('%H%M%S')}"
        self.logger.start_operation(operation_id, f"Batch renaming {len(operations)} items")
        
        # Reset statistics
        self._reset_stats()
        
        completed_operations = []
        failed_operations = []
        
        try:
            # Pre-validate all operations
            validation_errors = self._validate_batch_operations(operations)
            if validation_errors:
                # Mark all operations as failed due to batch validation
                for operation in operations:
                    operation.mark_completed(success=False, error_msg="Batch validation failed")
                    failed_operations.append(operation)
                
                raise BatchOperationError(
                    "Batch validation failed",
                    failed_operations=[op.original_name for op in operations],
                    rollback_possible=False
                )
            
            # Execute operations
            for i, operation in enumerate(operations):
                try:
                    # Progress callback
                    if self.progress_callback:
                        self.progress_callback(i, len(operations), operation.item.name)
                    
                    # Perform single rename
                    updated_operation = self.rename_item(operation)
                    
                    if updated_operation.status == OperationStatus.COMPLETED:
                        completed_operations.append(updated_operation)
                    elif updated_operation.status == OperationStatus.FAILED:
                        failed_operations.append(updated_operation)
                        
                        # Stop on first failure if rollback needed
                        if not self.allow_overwrites and len(failed_operations) > 0:
                            break
                    
                except Exception as e:
                    operation.mark_completed(success=False, error_msg=str(e))
                    failed_operations.append(operation)
                    break
            
            # Handle partial failures
            if failed_operations and completed_operations:
                if not self.dry_run_mode:
                    self.logger.warning(f"Batch partially failed. {len(failed_operations)} failures, {len(completed_operations)} successes")
                    # Could implement rollback logic here if needed
            
            success_rate = len(completed_operations) / len(operations) * 100 if operations else 100
            
            self.logger.end_operation(
                success=len(failed_operations) == 0,
                result=f"{len(completed_operations)}/{len(operations)} operations completed ({success_rate:.1f}%)",
                successful=len(completed_operations),
                failed=len(failed_operations)
            )
            
            return operations
            
        except Exception as e:
            # Mark remaining operations as cancelled
            for operation in operations:
                if operation.status == OperationStatus.PENDING:
                    operation.status = OperationStatus.CANCELLED
            
            self.logger.end_operation(success=False, result=f"Batch operation failed: {e}")
            raise BatchOperationError(
                str(e),
                failed_operations=[op.original_name for op in failed_operations],
                completed_operations=[op.original_name for op in completed_operations],
                rollback_possible=not self.dry_run_mode
            )
    
    def preview_rename(self, item: FileSystemItem) -> RenameOperation:
        """
        Preview what a rename operation would do without executing it.
        
        Args:
            item: FileSystemItem to preview rename for
            
        Returns:
            RenameOperation showing proposed changes
        """
        # Determine operation type
        if item.has_date_prefix:
            operation_type = OperationType.SKIPPED
            target_name = item.name
        else:
            operation_type = OperationType.FILE_RENAME if not item.is_directory else OperationType.FOLDER_RENAME
            target_name = self.date_extractor.generate_target_name(item.name, item.creation_date)
        
        # Create preview operation
        operation = RenameOperation(
            item=item,
            original_name=item.name,
            target_name=target_name,
            operation_type=operation_type,
            status=OperationStatus.PENDING
        )
        
        # Validate preview operation
        if not self._validate_operation(operation):
            operation.status = OperationStatus.FAILED
            operation.error_message = "Preview validation failed"
        
        return operation
    
    def _validate_operation(self, operation: RenameOperation) -> bool:
        """
        Validate a single rename operation.
        
        Args:
            operation: RenameOperation to validate
            
        Returns:
            True if operation is valid, False otherwise
        """
        try:
            # Basic validation
            if not operation.item.path.exists():
                operation.error_message = f"Source path does not exist: {operation.item.path}"
                return False
            
            # Target name validation
            if not self.validator.validate_target_name(operation.target_name, operation.item.path):
                operation.error_message = f"Invalid target name: {operation.target_name}"
                return False
            
            # Permission check
            try:
                # Check if we can rename in the parent directory
                parent_dir = operation.item.path.parent
                if not os.access(parent_dir, os.W_OK):
                    operation.error_message = f"No write permission in directory: {parent_dir}"
                    return False
            except Exception as e:
                operation.error_message = f"Permission check failed: {e}"
                return False
            
            return True
            
        except Exception as e:
            operation.error_message = f"Validation error: {e}"
            return False
    
    def _validate_batch_operations(self, operations: List[RenameOperation]) -> List[str]:
        """
        Validate a batch of operations for conflicts and issues.
        
        Args:
            operations: List of operations to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check for duplicate target names within the batch
        target_names = {}
        
        for operation in operations:
            target_lower = operation.target_name.lower()
            if target_lower in target_names:
                errors.append(
                    f"Duplicate target name in batch: '{operation.target_name}' "
                    f"(conflicts with '{target_names[target_lower]}')"
                )
            else:
                target_names[target_lower] = operation.original_name
        
        # Use validator for additional batch checks
        batch_tuples = [
            (op.original_name, op.target_name, op.item.path)
            for op in operations
        ]
        
        validation_errors = self.validator.validate_batch_operations(batch_tuples)
        errors.extend(validation_errors)
        
        return errors
    
    def _resolve_conflicts(self, operation: RenameOperation) -> bool:
        """
        Resolve naming conflicts for an operation.
        
        Args:
            operation: RenameOperation with potential conflicts
            
        Returns:
            True if conflicts were resolved, False otherwise
        """
        target_path = operation.target_path
        
        # No conflict if target doesn't exist
        if not target_path.exists():
            return True
        
        # If target exists and is the same file (case change), allow it
        if target_path.samefile(operation.item.path):
            return True
        
        # Handle overwrite policy
        if self.allow_overwrites:
            self.logger.warning(f"Will overwrite existing file: {target_path}")
            return True
        
        # Try to find alternative name
        alternative = self.validator.suggest_alternative_name(
            operation.target_name,
            operation.item.path.parent
        )
        
        if alternative:
            operation.target_name = alternative
            self.rename_stats['conflicts_resolved'] += 1
            self.logger.info(f"Resolved conflict with alternative name: {alternative}")
            return True
        
        # Could not resolve conflict
        operation.error_message = f"Naming conflict: {target_path} already exists"
        return False
    
    def _execute_rename(self, operation: RenameOperation) -> bool:
        """
        Execute the actual filesystem rename operation.
        
        Args:
            operation: RenameOperation to execute
            
        Returns:
            True if rename was successful, False otherwise
        """
        try:
            source_path = operation.item.path
            target_path = operation.target_path
            
            # Perform the rename
            source_path.rename(target_path)
            
            # Log successful rename
            self.logger.log_file_operation(
                "RENAME",
                source_path,
                success=True,
                new_name=target_path.name
            )
            
            return True
            
        except FileExistsError:
            operation.error_message = f"Target already exists: {operation.target_path}"
            return False
            
        except PermissionError as e:
            operation.error_message = f"Permission denied: {e}"
            return False
            
        except OSError as e:
            operation.error_message = f"OS error during rename: {e}"
            return False
            
        except Exception as e:
            operation.error_message = f"Unexpected error during rename: {e}"
            return False
    
    def _create_backup(self, file_path: Path) -> Path:
        """
        Create a backup copy of a file before renaming.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Path to the created backup file
            
        Raises:
            FileSystemError: If backup creation fails
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.backup_{timestamp}"
        backup_path = file_path.parent / backup_name
        
        try:
            if file_path.is_file():
                shutil.copy2(file_path, backup_path)
            else:
                shutil.copytree(file_path, backup_path)
            
            self.logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            raise FileSystemError(f"Failed to create backup: {e}", path=file_path)
    
    def _reset_stats(self):
        """Reset rename statistics."""
        for key in self.rename_stats:
            self.rename_stats[key] = 0
    
    def get_rename_summary(self) -> Dict[str, int]:
        """
        Get summary of rename operations performed.
        
        Returns:
            Dictionary containing rename statistics
        """
        total_operations = (self.rename_stats['successful_renames'] + 
                          self.rename_stats['failed_renames'] + 
                          self.rename_stats['skipped_items'])
        
        return {
            **self.rename_stats,
            'total_operations': total_operations,
            'success_rate': (self.rename_stats['successful_renames'] / total_operations * 100) 
                           if total_operations > 0 else 100.0
        }


class RollbackManager:
    """
    Utility class for managing rollback operations.
    
    This class provides functionality for undoing rename operations
    by restoring original filenames from operation history.
    """
    
    def __init__(self):
        """Initialize the rollback manager."""
        self.logger = get_operation_logger(__name__)
    
    def create_rollback_data(self, operations: List[RenameOperation]) -> Dict[str, str]:
        """
        Create rollback data from completed operations.
        
        Args:
            operations: List of completed rename operations
            
        Returns:
            Dictionary mapping current paths to original paths
        """
        rollback_data = {}
        
        for operation in operations:
            if operation.status == OperationStatus.COMPLETED and operation.rollback_possible:
                current_path = str(operation.target_path)
                original_path = str(operation.item.path)
                rollback_data[current_path] = original_path
        
        return rollback_data
    
    def execute_rollback(self, rollback_data: Dict[str, str]) -> Tuple[int, int, List[str]]:
        """
        Execute rollback operations to restore original names.
        
        Args:
            rollback_data: Dictionary mapping current paths to original paths
            
        Returns:
            Tuple of (successful_rollbacks, failed_rollbacks, error_messages)
        """
        successful = 0
        failed = 0
        errors = []
        
        for current_path_str, original_path_str in rollback_data.items():
            try:
                current_path = Path(current_path_str)
                original_path = Path(original_path_str)
                
                if current_path.exists():
                    current_path.rename(original_path)
                    successful += 1
                    self.logger.info(f"Rolled back: {current_path.name} -> {original_path.name}")
                else:
                    errors.append(f"File not found for rollback: {current_path}")
                    failed += 1
                    
            except Exception as e:
                errors.append(f"Rollback failed for {current_path_str}: {e}")
                failed += 1
        
        return successful, failed, errors