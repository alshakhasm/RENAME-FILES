"""
File and directory scanning functionality for the Date Prefix File Renamer.

This module provides the FileScanner interface and implementation for discovering
files and directories, extracting metadata, and preparing items for processing.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Iterator, Set, Callable
from datetime import datetime

from ..models import FileSystemItem, ProcessingSession
from ..models.enums import LogLevel
from ..core.date_extractor import DateExtractor
from ..utils.logging import get_operation_logger
from ..utils.exceptions import FileSystemError, ValidationError, PermissionError


class FileScannerInterface(ABC):
    """
    Abstract interface for file and directory scanning operations.
    
    This interface defines the contract for discovering filesystem items,
    extracting metadata, and filtering items based on various criteria.
    """
    
    @abstractmethod
    def scan_directory(self, directory_path: Path, recursive: bool = True) -> List[FileSystemItem]:
        """
        Scan a directory and return discovered filesystem items.
        
        Args:
            directory_path: Path to the directory to scan
            recursive: Whether to scan subdirectories recursively
            
        Returns:
            List of FileSystemItem objects representing discovered items
        """
        pass
    
    @abstractmethod
    def scan_single_item(self, item_path: Path) -> Optional[FileSystemItem]:
        """
        Scan a single file or directory item.
        
        Args:
            item_path: Path to the item to scan
            
        Returns:
            FileSystemItem object or None if item cannot be processed
        """
        pass


class FileScanner(FileScannerInterface):
    """
    Comprehensive file and directory scanner implementation.
    
    This class provides robust directory scanning with configurable filtering,
    symlink handling, permission checking, and metadata extraction.
    
    Attributes:
        date_extractor: DateExtractor for creation date extraction
        include_hidden: Whether to include hidden files/directories
        follow_symlinks: Whether to follow symbolic links
        max_depth: Maximum recursion depth (None for unlimited)
        file_extensions: Set of allowed file extensions (None for all)
        exclude_patterns: Set of glob patterns to exclude
        progress_callback: Optional callback for progress updates
        logger: Logger instance for operation tracking
    """
    
    def __init__(self,
                 date_extractor: Optional[DateExtractor] = None,
                 include_hidden: bool = False,
                 follow_symlinks: bool = False,
                 max_depth: Optional[int] = None,
                 file_extensions: Optional[Set[str]] = None,
                 exclude_patterns: Optional[Set[str]] = None,
                 progress_callback: Optional[Callable[[int, str], None]] = None):
        """
        Initialize the file scanner with configuration options.
        
        Args:
            date_extractor: DateExtractor for creation date operations
            include_hidden: Whether to include hidden files (starting with .)
            follow_symlinks: Whether to follow symbolic links during scanning
            max_depth: Maximum directory depth to scan (None for unlimited)
            file_extensions: Set of allowed file extensions (e.g., {'.txt', '.jpg'})
            exclude_patterns: Set of glob patterns to exclude from scanning
            progress_callback: Optional callback function(count, current_path)
        """
        self.date_extractor = date_extractor or DateExtractor()
        self.include_hidden = include_hidden
        self.follow_symlinks = follow_symlinks
        self.max_depth = max_depth
        self.file_extensions = set(ext.lower() for ext in (file_extensions or set()))
        self.exclude_patterns = exclude_patterns or set()
        self.progress_callback = progress_callback
        
        self.logger = get_operation_logger(__name__)
        
        # Statistics tracking
        self.scan_stats = {
            'files_found': 0,
            'directories_found': 0,
            'symlinks_skipped': 0,
            'hidden_skipped': 0,
            'permission_errors': 0,
            'excluded_items': 0
        }
    
    def scan_directory(self, directory_path: Path, recursive: bool = True) -> List[FileSystemItem]:
        """
        Scan a directory and return discovered filesystem items.
        
        This method performs comprehensive directory scanning with filtering,
        metadata extraction, and error handling.
        
        Args:
            directory_path: Path to the directory to scan
            recursive: Whether to scan subdirectories recursively
            
        Returns:
            List of FileSystemItem objects representing discovered items
            
        Raises:
            FileSystemError: If directory cannot be accessed or scanned
            ValidationError: If directory path is invalid
        """
        # Validate input
        if not directory_path.exists():
            raise FileSystemError(f"Directory does not exist: {directory_path}")
        
        if not directory_path.is_dir():
            raise ValidationError(f"Path is not a directory: {directory_path}")
        
        # Reset statistics
        self._reset_stats()
        
        operation_id = f"scan_{directory_path.name}_{datetime.now().strftime('%H%M%S')}"
        self.logger.start_operation(operation_id, f"Scanning directory: {directory_path}")
        
        try:
            discovered_items = []
            
            # Scan items using iterator for memory efficiency
            for item in self._scan_directory_iterator(directory_path, recursive, current_depth=0):
                discovered_items.append(item)
                
                # Progress callback
                if self.progress_callback:
                    self.progress_callback(len(discovered_items), str(item.path))
            
            # Log scan results
            self.logger.end_operation(
                success=True,
                result=f"Found {len(discovered_items)} items",
                files=self.scan_stats['files_found'],
                directories=self.scan_stats['directories_found'],
                skipped=self.scan_stats['symlinks_skipped'] + self.scan_stats['hidden_skipped']
            )
            
            return discovered_items
            
        except Exception as e:
            self.logger.end_operation(success=False, result=str(e))
            raise FileSystemError(f"Failed to scan directory: {directory_path}", details=str(e))
    
    def scan_single_item(self, item_path: Path) -> Optional[FileSystemItem]:
        """
        Scan a single file or directory item.
        
        Args:
            item_path: Path to the item to scan
            
        Returns:
            FileSystemItem object or None if item cannot be processed
        """
        try:
            # Check if item should be excluded
            if self._should_exclude_item(item_path):
                return None
            
            # Extract metadata
            return self._create_file_system_item(item_path)
            
        except Exception as e:
            self.logger.warning(f"Could not scan item {item_path}: {e}")
            return None
    
    def _scan_directory_iterator(self, directory_path: Path, recursive: bool, 
                                current_depth: int) -> Iterator[FileSystemItem]:
        """
        Internal iterator for directory scanning with depth control.
        
        Args:
            directory_path: Directory to scan
            recursive: Whether to recurse into subdirectories
            current_depth: Current recursion depth
            
        Yields:
            FileSystemItem objects for discovered items
        """
        # Check depth limit
        if self.max_depth is not None and current_depth > self.max_depth:
            return
        
        try:
            # Get directory contents
            items = list(directory_path.iterdir())
            
        except PermissionError as e:
            self.scan_stats['permission_errors'] += 1
            self.logger.warning(f"Permission denied accessing directory: {directory_path}")
            return
        
        except OSError as e:
            self.logger.warning(f"OS error accessing directory {directory_path}: {e}")
            return
        
        # Sort items for consistent ordering
        items.sort(key=lambda x: (x.is_dir(), x.name.lower()))
        
        # Process files first, then directories
        directories_to_recurse = []
        
        for item_path in items:
            try:
                # Check exclusion rules
                if self._should_exclude_item(item_path):
                    continue
                
                # Create FileSystemItem
                file_item = self._create_file_system_item(item_path)
                if file_item:
                    yield file_item
                    
                    # Queue directories for recursion
                    if recursive and item_path.is_dir() and not item_path.is_symlink():
                        directories_to_recurse.append(item_path)
            
            except Exception as e:
                self.logger.warning(f"Error processing item {item_path}: {e}")
                continue
        
        # Recurse into subdirectories
        if recursive:
            for subdir_path in directories_to_recurse:
                yield from self._scan_directory_iterator(subdir_path, recursive, current_depth + 1)
    
    def _create_file_system_item(self, item_path: Path) -> Optional[FileSystemItem]:
        """
        Create a FileSystemItem from a filesystem path.
        
        Args:
            item_path: Path to the filesystem item
            
        Returns:
            FileSystemItem object or None if creation fails
        """
        try:
            # Basic path information
            is_directory = item_path.is_dir()
            is_symlink = item_path.is_symlink()
            
            # Skip symlinks if not following them
            if is_symlink and not self.follow_symlinks:
                self.scan_stats['symlinks_skipped'] += 1
                return None
            
            # Extract timestamps
            creation_date = self.date_extractor.get_creation_date(item_path)
            
            # Get modification time
            try:
                mod_timestamp = item_path.stat().st_mtime
                modification_date = datetime.fromtimestamp(mod_timestamp)
            except OSError:
                modification_date = creation_date  # Fallback
            
            # Check for existing date prefix
            has_date_prefix = self.date_extractor.has_date_prefix(item_path.name)
            
            # Get file size
            try:
                size_bytes = item_path.stat().st_size if not is_directory else 0
            except OSError:
                size_bytes = 0
            
            # Update statistics
            if is_directory:
                self.scan_stats['directories_found'] += 1
            else:
                self.scan_stats['files_found'] += 1
            
            # Create FileSystemItem
            return FileSystemItem(
                path=item_path,
                name=item_path.name,
                creation_date=creation_date,
                modification_date=modification_date,
                is_directory=is_directory,
                is_symlink=is_symlink,
                has_date_prefix=has_date_prefix,
                size_bytes=size_bytes
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to create FileSystemItem for {item_path}: {e}")
            return None
    
    def _should_exclude_item(self, item_path: Path) -> bool:
        """
        Check if an item should be excluded based on configured filters.
        
        Args:
            item_path: Path to check
            
        Returns:
            True if item should be excluded, False otherwise
        """
        # Hidden file check
        if not self.include_hidden and item_path.name.startswith('.'):
            self.scan_stats['hidden_skipped'] += 1
            return True
        
        # File extension filter
        if self.file_extensions and not item_path.is_dir():
            file_ext = item_path.suffix.lower()
            if file_ext not in self.file_extensions:
                self.scan_stats['excluded_items'] += 1
                return True
        
        # Exclude pattern check
        if self.exclude_patterns:
            for pattern in self.exclude_patterns:
                if item_path.match(pattern):
                    self.scan_stats['excluded_items'] += 1
                    return True
        
        return False
    
    def _reset_stats(self):
        """Reset scan statistics."""
        for key in self.scan_stats:
            self.scan_stats[key] = 0
    
    def get_scan_summary(self) -> dict:
        """
        Get summary of the last scan operation.
        
        Returns:
            Dictionary containing scan statistics
        """
        total_found = self.scan_stats['files_found'] + self.scan_stats['directories_found']
        total_skipped = (self.scan_stats['symlinks_skipped'] + 
                        self.scan_stats['hidden_skipped'] + 
                        self.scan_stats['excluded_items'])
        
        return {
            **self.scan_stats,
            'total_found': total_found,
            'total_skipped': total_skipped,
            'total_processed': total_found + total_skipped
        }


class BatchScanner:
    """
    Utility class for scanning multiple directories in batch operations.
    
    This class provides functionality for scanning multiple directories
    and consolidating results for batch processing operations.
    """
    
    def __init__(self, file_scanner: Optional[FileScanner] = None):
        """
        Initialize the batch scanner.
        
        Args:
            file_scanner: FileScanner instance to use (creates default if None)
        """
        self.file_scanner = file_scanner or FileScanner()
        self.logger = get_operation_logger(__name__)
    
    def scan_multiple_directories(self, directory_paths: List[Path], 
                                 recursive: bool = True) -> List[FileSystemItem]:
        """
        Scan multiple directories and return consolidated results.
        
        Args:
            directory_paths: List of directory paths to scan
            recursive: Whether to scan recursively
            
        Returns:
            Consolidated list of FileSystemItem objects from all directories
        """
        all_items = []
        
        for directory_path in directory_paths:
            try:
                items = self.file_scanner.scan_directory(directory_path, recursive)
                all_items.extend(items)
                self.logger.info(f"Scanned {directory_path}: {len(items)} items")
                
            except Exception as e:
                self.logger.error(f"Failed to scan directory {directory_path}: {e}")
        
        return all_items
    
    def scan_with_progress_tracking(self, directory_path: Path, 
                                   progress_callback: Callable[[int, int, str], None]) -> List[FileSystemItem]:
        """
        Scan directory with enhanced progress tracking.
        
        Args:
            directory_path: Directory to scan
            progress_callback: Callback function(current, total, current_path)
            
        Returns:
            List of discovered FileSystemItem objects
        """
        # First pass: count items for progress tracking
        total_items = sum(1 for _ in directory_path.rglob('*'))
        
        discovered_items = []
        current_count = 0
        
        def progress_wrapper(count: int, current_path: str):
            nonlocal current_count
            current_count = count
            progress_callback(current_count, total_items, current_path)
        
        # Configure scanner with progress callback
        original_callback = self.file_scanner.progress_callback
        self.file_scanner.progress_callback = progress_wrapper
        
        try:
            # Perform scan
            discovered_items = self.file_scanner.scan_directory(directory_path, recursive=True)
            
        finally:
            # Restore original callback
            self.file_scanner.progress_callback = original_callback
        
        return discovered_items