"""
Test fixtures and sample data for the Date Prefix File Renamer application.

This module provides utilities for creating consistent test data, sample files,
and mock objects for use in unit and integration tests.
"""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from ...src.models import FileSystemItem, RenameOperation, ProcessingSession
from ...src.models.enums import OperationType, OperationStatus


@dataclass
class TestFile:
    """
    Represents a test file to be created in fixtures.
    
    Attributes:
        name: Filename including extension
        content: File content (empty for directories)
        is_directory: Whether this is a directory
        creation_date: Simulated creation date
        modification_date: Simulated modification date
        subdirectory: Optional subdirectory path within fixture
    """
    name: str
    content: str = ""
    is_directory: bool = False
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    subdirectory: str = ""


class TestFixtureManager:
    """
    Manages creation and cleanup of test fixtures.
    
    This class provides methods for creating temporary test directories
    with known file structures and predictable metadata for testing.
    
    Attributes:
        fixture_root: Root directory for all test fixtures
        temp_directories: List of created temporary directories for cleanup
    """
    
    def __init__(self, fixture_root: Optional[Path] = None):
        """
        Initialize the fixture manager.
        
        Args:
            fixture_root: Base directory for fixtures (uses temp if not provided)
        """
        self.fixture_root = fixture_root or Path(tempfile.gettempdir()) / "date_renamer_tests"
        self.temp_directories: List[Path] = []
        
        # Ensure fixture root exists
        self.fixture_root.mkdir(parents=True, exist_ok=True)
    
    def create_test_directory(self, name: str, files: List[TestFile]) -> Path:
        """
        Create a test directory with specified files and structure.
        
        Args:
            name: Name of the test directory
            files: List of TestFile objects to create
            
        Returns:
            Path to the created test directory
        """
        test_dir = self.fixture_root / name
        
        # Clean up if directory already exists
        if test_dir.exists():
            shutil.rmtree(test_dir)
        
        test_dir.mkdir(parents=True, exist_ok=True)
        self.temp_directories.append(test_dir)
        
        # Create all specified files and directories
        for test_file in files:
            # Handle subdirectory structure
            if test_file.subdirectory:
                file_parent = test_dir / test_file.subdirectory
                file_parent.mkdir(parents=True, exist_ok=True)
                file_path = file_parent / test_file.name
            else:
                file_path = test_dir / test_file.name
            
            # Create file or directory
            if test_file.is_directory:
                file_path.mkdir(parents=True, exist_ok=True)
            else:
                file_path.write_text(test_file.content, encoding='utf-8')
            
            # Set timestamps if specified
            self._set_file_timestamps(file_path, test_file.creation_date, test_file.modification_date)
        
        return test_dir
    
    def _set_file_timestamps(self, file_path: Path, creation_date: Optional[datetime], 
                           modification_date: Optional[datetime]):
        """
        Set file timestamps to specific values.
        
        Args:
            file_path: Path to the file
            creation_date: Creation date to set
            modification_date: Modification date to set
        """
        if modification_date:
            # Set modification time
            mod_timestamp = modification_date.timestamp()
            os.utime(file_path, (mod_timestamp, mod_timestamp))
        
        # Note: Setting creation time is platform-specific and may not work on all systems
        # This is a limitation of the test fixtures, but modification time is sufficient
        # for most testing scenarios
    
    def cleanup(self):
        """Clean up all created temporary directories."""
        for temp_dir in self.temp_directories:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        self.temp_directories.clear()
    
    def __enter__(self):
        """Support for context manager usage."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up when exiting context manager."""
        self.cleanup()


# Predefined test scenarios
def create_basic_test_files() -> List[TestFile]:
    """
    Create a basic set of test files for common scenarios.
    
    Returns:
        List of TestFile objects representing a typical test scenario
    """
    base_date = datetime(2024, 1, 15, 10, 30, 0)
    
    return [
        # Regular files
        TestFile("document.txt", "Sample document content", 
                creation_date=base_date, modification_date=base_date),
        TestFile("image.jpg", "fake image data", 
                creation_date=base_date + timedelta(hours=1)),
        TestFile("script.py", "print('hello world')", 
                creation_date=base_date + timedelta(hours=2)),
        TestFile("data.csv", "name,value\ntest,123", 
                creation_date=base_date + timedelta(hours=3)),
        
        # Directories
        TestFile("empty_folder", "", is_directory=True, 
                creation_date=base_date + timedelta(hours=4)),
        TestFile("documents", "", is_directory=True, 
                creation_date=base_date + timedelta(hours=5)),
        
        # Files in subdirectories
        TestFile("readme.txt", "README content", 
                creation_date=base_date + timedelta(hours=6), 
                subdirectory="documents"),
        TestFile("nested_folder", "", is_directory=True, 
                creation_date=base_date + timedelta(hours=7), 
                subdirectory="documents"),
    ]


def create_edge_case_files() -> List[TestFile]:
    """
    Create files that test edge cases and special scenarios.
    
    Returns:
        List of TestFile objects for edge case testing
    """
    base_date = datetime(2024, 1, 15, 10, 30, 0)
    
    return [
        # Files with existing date prefixes
        TestFile("2024-01-10_already_prefixed.txt", "content", 
                creation_date=base_date),
        TestFile("2023-12-25_old_prefix.doc", "content", 
                creation_date=base_date),
        
        # Files with special characters
        TestFile("file with spaces.txt", "content", 
                creation_date=base_date),
        TestFile("file-with-dashes.txt", "content", 
                creation_date=base_date),
        TestFile("file_with_underscores.txt", "content", 
                creation_date=base_date),
        
        # Very long filename
        TestFile("very_long_filename_" + "x" * 200 + ".txt", "content", 
                creation_date=base_date),
        
        # Files without extensions
        TestFile("no_extension", "content", 
                creation_date=base_date),
        TestFile("README", "readme content", 
                creation_date=base_date),
        
        # Hidden files (Unix-style)
        TestFile(".hidden_file", "hidden content", 
                creation_date=base_date),
        TestFile(".config", "", is_directory=True, 
                creation_date=base_date),
    ]


def create_large_directory_structure() -> List[TestFile]:
    """
    Create a large directory structure for performance testing.
    
    Returns:
        List of TestFile objects for stress testing
    """
    files = []
    base_date = datetime(2024, 1, 1, 0, 0, 0)
    
    # Create 100 files in root
    for i in range(100):
        files.append(TestFile(
            name=f"file_{i:03d}.txt",
            content=f"Content for file {i}",
            creation_date=base_date + timedelta(minutes=i)
        ))
    
    # Create 10 directories with 20 files each
    for dir_num in range(10):
        dir_name = f"folder_{dir_num:02d}"
        files.append(TestFile(
            name=dir_name,
            is_directory=True,
            creation_date=base_date + timedelta(hours=dir_num)
        ))
        
        for file_num in range(20):
            files.append(TestFile(
                name=f"nested_file_{file_num:02d}.dat",
                content=f"Nested content {dir_num}-{file_num}",
                subdirectory=dir_name,
                creation_date=base_date + timedelta(hours=dir_num, minutes=file_num)
            ))
    
    return files


def create_conflict_test_files() -> List[TestFile]:
    """
    Create files that will test naming conflict resolution.
    
    Returns:
        List of TestFile objects for conflict testing
    """
    base_date = datetime(2024, 1, 15, 10, 30, 0)
    
    return [
        # Files that would create conflicts after prefixing
        TestFile("document.txt", "content 1", creation_date=base_date),
        TestFile("Document.txt", "content 2", creation_date=base_date),  # Case conflict
        TestFile("DOCUMENT.TXT", "content 3", creation_date=base_date),  # Case conflict
        
        # Files with same creation date (same prefix)
        TestFile("file1.txt", "content 1", creation_date=base_date),
        TestFile("file2.txt", "content 2", creation_date=base_date),
        TestFile("file3.txt", "content 3", creation_date=base_date),
        
        # Existing prefixed file that would conflict
        TestFile("2024-01-15_target.txt", "existing prefixed", creation_date=base_date),
        TestFile("target.txt", "would conflict", creation_date=base_date),
    ]


# Mock data creation functions
def create_mock_file_system_items(count: int = 5) -> List[FileSystemItem]:
    """
    Create mock FileSystemItem objects for testing.
    
    Args:
        count: Number of items to create
        
    Returns:
        List of mock FileSystemItem objects
    """
    items = []
    base_date = datetime(2024, 1, 15, 10, 0, 0)
    
    for i in range(count):
        # Create a temporary file path (won't actually exist)
        temp_path = Path(f"/tmp/test_file_{i}.txt")
        
        item = FileSystemItem(
            path=temp_path,
            name=f"test_file_{i}.txt",
            creation_date=base_date + timedelta(minutes=i * 10),
            modification_date=base_date + timedelta(minutes=i * 10 + 5),
            is_directory=i % 4 == 0,  # Every 4th item is a directory
            is_symlink=False,
            has_date_prefix=i % 3 == 0,  # Every 3rd item has prefix
            size_bytes=1024 * i if i % 4 != 0 else 0  # Directories have size 0
        )
        items.append(item)
    
    return items


def create_mock_rename_operations(file_items: Optional[List[FileSystemItem]] = None) -> List[RenameOperation]:
    """
    Create mock RenameOperation objects for testing.
    
    Args:
        file_items: Optional list of FileSystemItem objects to use
        
    Returns:
        List of mock RenameOperation objects
    """
    if file_items is None:
        file_items = create_mock_file_system_items(5)
    
    operations = []
    
    for item in file_items:
        if item.has_date_prefix:
            operation_type = OperationType.SKIPPED
            target_name = item.name  # No change needed
            status = OperationStatus.SKIPPED
        else:
            operation_type = OperationType.FILE_RENAME if not item.is_directory else OperationType.FOLDER_RENAME
            date_prefix = item.creation_date.strftime("%Y-%m-%d")
            target_name = f"{date_prefix}_{item.name}"
            status = OperationStatus.PENDING
        
        operation = RenameOperation(
            item=item,
            original_name=item.name,
            target_name=target_name,
            operation_type=operation_type,
            status=status
        )
        operations.append(operation)
    
    return operations


def create_mock_processing_session(directory_path: Optional[Path] = None) -> ProcessingSession:
    """
    Create a mock ProcessingSession for testing.
    
    Args:
        directory_path: Optional directory path (uses temp if not provided)
        
    Returns:
        Mock ProcessingSession object
    """
    if directory_path is None:
        directory_path = Path("/tmp/test_directory")
    
    session = ProcessingSession(
        target_directory=directory_path,
        session_id="test_session_001",
        is_dry_run=True
    )
    
    # Add some mock items and operations
    items = create_mock_file_system_items(10)
    operations = create_mock_rename_operations(items)
    
    session.discovered_items = items
    session.rename_operations = operations
    
    return session


# Test data constants
SAMPLE_FILE_EXTENSIONS = [
    '.txt', '.doc', '.pdf', '.jpg', '.png', '.mp4', '.csv', '.json', '.xml', '.py'
]

SAMPLE_DIRECTORY_NAMES = [
    'Documents', 'Images', 'Videos', 'Projects', 'Archive', 'Backup', 'Temp'
]

SAMPLE_PROBLEMATIC_NAMES = [
    'file with spaces.txt',
    'file:with:colons.txt',
    'file<with>brackets.txt',
    'very_long_filename_that_exceeds_normal_limits_and_might_cause_issues.txt',
    '.hidden_file',
    'file.',  # Ends with dot
    ' file_with_leading_space.txt',
    'file_with_trailing_space.txt ',
]