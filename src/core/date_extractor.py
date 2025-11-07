"""
Date extraction and formatting utilities for the Date Prefix File Renamer.

This module provides the DateExtractor interface and implementation for extracting
creation dates from files and formatting them as prefixes for renaming operations.
"""

import os
import platform
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from ..models.enums import DateFormatStyle


class DateExtractorInterface(ABC):
    """
    Abstract interface for date extraction and formatting operations.
    
    This interface defines the contract for extracting creation dates from filesystem
    items and formatting them as prefixes suitable for file renaming.
    """
    
    @abstractmethod
    def get_creation_date(self, file_path: Path) -> datetime:
        """
        Extract the creation date from a filesystem item.
        
        Args:
            file_path: Path to the file or directory
            
        Returns:
            Creation datetime with fallback to modification time
            
        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If the file cannot be accessed
            OSError: If filesystem metadata cannot be read
        """
        pass
    
    @abstractmethod
    def format_date_prefix(self, date: datetime, style: DateFormatStyle = DateFormatStyle.ISO_DATE) -> str:
        """
        Format a datetime as a prefix string for file renaming.
        
        Args:
            date: The datetime to format
            style: The formatting style to use
            
        Returns:
            Formatted date string with trailing underscore (e.g., "2024-03-15_")
        """
        pass
    
    @abstractmethod
    def extract_prefix_from_name(self, filename: str) -> Optional[str]:
        """
        Extract an existing date prefix from a filename if present.
        
        Args:
            filename: The filename to analyze
            
        Returns:
            The date prefix without underscore if found, None otherwise
        """
        pass


class DateExtractor(DateExtractorInterface):
    """
    Cross-platform implementation of date extraction and formatting.
    
    This implementation handles platform-specific differences in file metadata
    access and provides consistent date extraction across Windows, macOS, and Linux.
    
    Attributes:
        default_style: Default date formatting style to use
        use_birth_time: Whether to prefer birth time over creation time (macOS)
    """
    
    def __init__(self, default_style: DateFormatStyle = DateFormatStyle.ISO_DATE, use_birth_time: bool = True):
        """
        Initialize the date extractor with configuration options.
        
        Args:
            default_style: Default date formatting style
            use_birth_time: Use birth time on macOS when available
        """
        self.default_style = default_style
        self.use_birth_time = use_birth_time
        self._platform = platform.system().lower()
    
    def get_creation_date(self, file_path: Path) -> datetime:
        """
        Extract the creation date from a filesystem item.
        
        Implementation strategy:
        1. On Windows: Use st_ctime (creation time)
        2. On macOS: Use st_birthtime if available, fallback to st_ctime
        3. On Linux: Use st_ctime (inode change time), fallback to st_mtime
        4. Always fallback to modification time if creation time unavailable
        
        Args:
            file_path: Path to the file or directory
            
        Returns:
            Creation datetime with fallback to modification time
            
        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If the file cannot be accessed
            OSError: If filesystem metadata cannot be read
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Path does not exist: {file_path}")
        
        try:
            stat_result = file_path.stat()
            
            # Platform-specific creation time extraction
            creation_timestamp = None
            
            if self._platform == 'windows':
                # Windows: st_ctime is creation time
                creation_timestamp = stat_result.st_ctime
                
            elif self._platform == 'darwin':  # macOS
                # macOS: Prefer st_birthtime if available and use_birth_time is True
                if self.use_birth_time and hasattr(stat_result, 'st_birthtime'):
                    birth_time = getattr(stat_result, 'st_birthtime')
                    if birth_time > 0:  # Valid birth time
                        creation_timestamp = birth_time
                    else:
                        creation_timestamp = stat_result.st_ctime
                else:
                    creation_timestamp = stat_result.st_ctime
                    
            else:  # Linux and other Unix-like systems
                # Linux: st_ctime is inode change time (closest to creation)
                creation_timestamp = stat_result.st_ctime
            
            # Fallback to modification time if creation time seems invalid
            if creation_timestamp is None or creation_timestamp <= 0:
                creation_timestamp = stat_result.st_mtime
            
            # Convert timestamp to datetime
            creation_date = datetime.fromtimestamp(creation_timestamp)
            
            # Sanity check: creation date should not be in the future
            now = datetime.now()
            if creation_date > now:
                # Use modification time instead
                creation_date = datetime.fromtimestamp(stat_result.st_mtime)
            
            return creation_date
            
        except (OSError, PermissionError, ValueError) as e:
            raise OSError(f"Could not read metadata for {file_path}: {e}")
    
    def format_date_prefix(self, date: datetime, style: DateFormatStyle = None) -> str:
        """
        Format a datetime as a prefix string for file renaming.
        
        Args:
            date: The datetime to format
            style: The formatting style to use (defaults to instance default)
            
        Returns:
            Formatted date string with trailing underscore (e.g., "2024-03-15_")
        """
        if style is None:
            style = self.default_style
        
        # Format the date according to the specified style
        formatted_date = date.strftime(style.strftime_format)
        
        # Always append underscore for consistent prefix format
        return f"{formatted_date}_"
    
    def extract_prefix_from_name(self, filename: str) -> Optional[str]:
        """
        Extract an existing date prefix from a filename if present.
        
        This method looks for date patterns at the beginning of filenames that match
        the supported formatting styles. It validates the extracted date to ensure
        it represents a real date.
        
        Args:
            filename: The filename to analyze
            
        Returns:
            The date prefix without underscore if found, None otherwise
        """
        # Check for various date prefix patterns
        date_patterns = [
            ("%Y-%m-%d", DateFormatStyle.ISO_DATE),
            ("%m-%d-%Y", DateFormatStyle.US_DATE),
            ("%Y%m%d", DateFormatStyle.COMPACT),
            ("%Y-%m", DateFormatStyle.YEAR_MONTH)
        ]
        
        for pattern, style in date_patterns:
            # Try to find pattern at start of filename
            expected_length = len(datetime.now().strftime(pattern))
            
            if len(filename) > expected_length and filename[expected_length] == '_':
                candidate_prefix = filename[:expected_length]
                
                try:
                    # Validate that the prefix is actually a valid date
                    parsed_date = datetime.strptime(candidate_prefix, pattern)
                    
                    # Additional validation: date should be reasonable (not too far in future)
                    now = datetime.now()
                    if parsed_date <= now and parsed_date.year >= 1970:
                        return candidate_prefix
                        
                except ValueError:
                    # Not a valid date, continue checking other patterns
                    continue
        
        return None
    
    def has_date_prefix(self, filename: str) -> bool:
        """
        Check if a filename already has a date prefix.
        
        Args:
            filename: The filename to check
            
        Returns:
            True if filename has a valid date prefix, False otherwise
        """
        return self.extract_prefix_from_name(filename) is not None
    
    def generate_target_name(self, original_name: str, creation_date: datetime, 
                           style: DateFormatStyle = None) -> str:
        """
        Generate a target filename with date prefix.
        
        If the original name already has a date prefix, this method will replace
        it with the new creation date. Otherwise, it prepends the date prefix.
        
        Args:
            original_name: The current filename
            creation_date: The creation date to use for the prefix
            style: The date formatting style to use
            
        Returns:
            New filename with date prefix
        """
        if style is None:
            style = self.default_style
        
        # Remove existing date prefix if present
        existing_prefix = self.extract_prefix_from_name(original_name)
        if existing_prefix:
            # Strip the existing prefix and underscore
            name_without_prefix = original_name[len(existing_prefix) + 1:]
        else:
            name_without_prefix = original_name
        
        # Generate new prefix and combine
        date_prefix = self.format_date_prefix(creation_date, style)
        return f"{date_prefix}{name_without_prefix}"
    
    def get_date_from_prefix(self, prefix: str) -> Optional[datetime]:
        """
        Parse a date from a prefix string.
        
        Args:
            prefix: The date prefix string (without underscore)
            
        Returns:
            Parsed datetime if valid, None otherwise
        """
        date_patterns = [
            "%Y-%m-%d",   # ISO format
            "%m-%d-%Y",   # US format  
            "%Y%m%d",     # Compact format
            "%Y-%m"       # Year-month format
        ]
        
        for pattern in date_patterns:
            try:
                return datetime.strptime(prefix, pattern)
            except ValueError:
                continue
        
        return None
    
    def validate_date_range(self, date: datetime, min_year: int = 1970, max_future_days: int = 30) -> bool:
        """
        Validate that a date falls within reasonable bounds.
        
        Args:
            date: The date to validate
            min_year: Minimum allowed year
            max_future_days: Maximum days in the future allowed
            
        Returns:
            True if date is within valid range, False otherwise
        """
        from datetime import timedelta
        
        now = datetime.now()
        min_date = datetime(min_year, 1, 1)
        max_date = now + timedelta(days=max_future_days)
        
        return min_date <= date <= max_date