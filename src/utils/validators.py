"""
Validation utilities for file naming and prefix operations.

This module provides validation functions for ensuring safe and consistent
file renaming operations, including prefix detection, name generation, and
target name validation.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union

from ..models.enums import DateFormatStyle, ValidationLevel
from ..core.date_extractor import DateExtractor


class ValidationError(Exception):
    """Raised when validation fails for file naming operations."""
    pass


class PrefixValidatorInterface:
    """
    Abstract interface for prefix validation operations.
    
    This interface defines methods for validating existing prefixes,
    generating new target names, and ensuring safe rename operations.
    """
    
    def has_date_prefix(self, filename: str) -> bool:
        """Check if filename has a valid date prefix."""
        raise NotImplementedError
    
    def generate_target_name(self, original_name: str, creation_date: datetime) -> str:
        """Generate a valid target name with date prefix."""
        raise NotImplementedError
    
    def validate_target_name(self, target_name: str, original_path: Path) -> bool:
        """Validate that a target name is safe for renaming."""
        raise NotImplementedError


class PrefixValidator(PrefixValidatorInterface):
    """
    Comprehensive validation system for date prefix operations.
    
    This class provides robust validation for file renaming operations,
    including prefix detection, name collision checking, and filesystem
    safety validations.
    
    Attributes:
        date_extractor: DateExtractor instance for date operations
        validation_level: Strictness level for validation checks
        allowed_extensions: Set of allowed file extensions (if restricted)
        max_filename_length: Maximum allowed filename length
        forbidden_patterns: Regex patterns for forbidden filename content
    """
    
    # Common problematic filename patterns
    FORBIDDEN_PATTERNS = [
        r'[\x00-\x1f]',           # Control characters
        r'[<>:"|?*]',             # Windows reserved characters
        r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)',  # Windows reserved names
        r'^\.',                   # Hidden files starting with dot (optional restriction)
        r'\.$',                   # Ending with dot
        r'\s+$',                  # Trailing whitespace
    ]
    
    # Maximum filename lengths for different filesystems
    MAX_FILENAME_LENGTHS = {
        'ntfs': 255,      # Windows NTFS
        'ext4': 255,      # Linux ext4
        'apfs': 255,      # macOS APFS
        'fat32': 255,     # FAT32 (compatibility)
        'default': 255    # Conservative default
    }
    
    def __init__(self, 
                 validation_level: ValidationLevel = ValidationLevel.NORMAL,
                 date_extractor: Optional[DateExtractor] = None,
                 allowed_extensions: Optional[List[str]] = None,
                 max_filename_length: int = 255):
        """
        Initialize the prefix validator with configuration options.
        
        Args:
            validation_level: How strict to be with validation
            date_extractor: DateExtractor for date operations
            allowed_extensions: Whitelist of allowed file extensions
            max_filename_length: Maximum filename length to allow
        """
        self.validation_level = validation_level
        self.date_extractor = date_extractor or DateExtractor()
        self.allowed_extensions = set(allowed_extensions or [])
        self.max_filename_length = max_filename_length
        
        # Compile forbidden patterns for efficiency
        self.forbidden_regexes = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.FORBIDDEN_PATTERNS
        ]
    
    def has_date_prefix(self, filename: str) -> bool:
        """
        Check if filename has a valid date prefix.
        
        Delegates to DateExtractor for actual prefix detection and validation.
        
        Args:
            filename: The filename to check
            
        Returns:
            True if filename has a valid date prefix, False otherwise
        """
        return self.date_extractor.has_date_prefix(filename)
    
    def generate_target_name(self, original_name: str, creation_date: datetime,
                           style: DateFormatStyle = DateFormatStyle.ISO_DATE) -> str:
        """
        Generate a valid target name with date prefix.
        
        This method creates a new filename with the date prefix while ensuring
        the result passes all validation checks.
        
        Args:
            original_name: Original filename or directory name
            creation_date: Creation date for prefix generation
            style: Date formatting style to use
            
        Returns:
            New filename with date prefix
            
        Raises:
            ValidationError: If generated name would be invalid
        """
        # Generate base target name using DateExtractor
        target_name = self.date_extractor.generate_target_name(
            original_name, creation_date, style
        )
        
        # Validate the generated name
        if not self._validate_filename_structure(target_name):
            raise ValidationError(f"Generated filename is invalid: {target_name}")
        
        # Check length constraints
        if len(target_name) > self.max_filename_length:
            # Try to truncate the original name part while keeping extension
            path_obj = Path(target_name)
            extension = path_obj.suffix
            prefix_part = target_name[:target_name.find('_') + 1]  # Include underscore
            name_part = path_obj.stem[len(prefix_part) - 1:]  # Remove underscore from count
            
            # Calculate available space for name part
            available_length = self.max_filename_length - len(prefix_part) - len(extension)
            
            if available_length < 1:
                raise ValidationError(
                    f"Cannot create valid filename: prefix + extension too long"
                )
            
            # Truncate name part
            truncated_name = name_part[:available_length]
            target_name = f"{prefix_part}{truncated_name}{extension}"
        
        # Extension validation if restricted
        if self.allowed_extensions:
            extension = Path(target_name).suffix.lower()
            if extension and extension not in self.allowed_extensions:
                raise ValidationError(
                    f"File extension {extension} not in allowed list: {self.allowed_extensions}"
                )
        
        return target_name
    
    def validate_target_name(self, target_name: str, original_path: Path) -> bool:
        """
        Validate that a target name is safe for renaming operations.
        
        Performs comprehensive validation including filesystem compatibility,
        name collision checking, and security validations.
        
        Args:
            target_name: Proposed new filename
            original_path: Current path of the file being renamed
            
        Returns:
            True if target name is safe, False otherwise
        """
        try:
            # Basic filename structure validation
            if not self._validate_filename_structure(target_name):
                return False
            
            # Length validation
            if len(target_name) > self.max_filename_length:
                return False
            
            # Extension validation
            if self.allowed_extensions:
                extension = Path(target_name).suffix.lower()
                if extension and extension not in self.allowed_extensions:
                    return False
            
            # Path collision validation
            target_path = original_path.parent / target_name
            if self._check_path_collision(target_path, original_path):
                return False
            
            # Platform-specific validations
            if not self._validate_platform_compatibility(target_name):
                return False
            
            return True
            
        except Exception:
            # Any unexpected error during validation means unsafe
            return False
    
    def _validate_filename_structure(self, filename: str) -> bool:
        """
        Validate basic filename structure and content.
        
        Args:
            filename: Filename to validate
            
        Returns:
            True if structure is valid, False otherwise
        """
        if not filename or filename.isspace():
            return False
        
        # Check for forbidden patterns based on validation level
        if self.validation_level == ValidationLevel.DISABLED:
            return True
        
        patterns_to_check = []
        if self.validation_level in [ValidationLevel.STRICT, ValidationLevel.NORMAL]:
            patterns_to_check.extend(self.forbidden_regexes[:4])  # Basic patterns
        
        if self.validation_level == ValidationLevel.STRICT:
            patterns_to_check.extend(self.forbidden_regexes[4:])  # All patterns
        
        for pattern in patterns_to_check:
            if pattern.search(filename):
                return False
        
        return True
    
    def _check_path_collision(self, target_path: Path, original_path: Path) -> bool:
        """
        Check if target path would create a naming collision.
        
        Args:
            target_path: Proposed new path
            original_path: Current path
            
        Returns:
            True if collision detected, False if safe
        """
        # Skip check if target is same as original (no rename needed)
        if target_path == original_path:
            return False
        
        # Check if target already exists
        if target_path.exists():
            return True
        
        # Case-insensitive collision check on case-insensitive filesystems
        if self._is_case_insensitive_filesystem(target_path.parent):
            for existing_item in target_path.parent.iterdir():
                if existing_item.name.lower() == target_path.name.lower():
                    if existing_item != original_path:  # Don't count self
                        return True
        
        return False
    
    def _validate_platform_compatibility(self, filename: str) -> bool:
        """
        Validate filename for cross-platform compatibility.
        
        Args:
            filename: Filename to validate
            
        Returns:
            True if compatible across platforms, False otherwise
        """
        # Windows reserved names check
        name_part = Path(filename).stem.upper()
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        if name_part in reserved_names:
            return False
        
        # Check for characters problematic on Windows
        problematic_chars = set('<>:"|?*')
        if any(char in filename for char in problematic_chars):
            return False
        
        # Control characters check
        if any(ord(char) < 32 for char in filename):
            return False
        
        return True
    
    def _is_case_insensitive_filesystem(self, directory: Path) -> bool:
        """
        Detect if the filesystem is case-insensitive.
        
        Args:
            directory: Directory to test
            
        Returns:
            True if filesystem is case-insensitive, False otherwise
        """
        try:
            # Create test files with different cases
            test_lower = directory / "test_case_sensitivity.tmp"
            test_upper = directory / "TEST_CASE_SENSITIVITY.TMP"
            
            # If both exist as same file, filesystem is case-insensitive
            if test_lower.exists() and test_upper.exists():
                return test_lower.samefile(test_upper)
            
            # Fallback: common filesystem detection
            import platform
            system = platform.system().lower()
            if system == 'windows':
                return True
            elif system == 'darwin':  # macOS
                return True  # Most macOS installations use case-insensitive APFS/HFS+
            else:
                return False  # Linux typically case-sensitive
                
        except Exception:
            # Conservative fallback
            return True
    
    def validate_batch_operations(self, operations: List[Tuple[str, str, Path]]) -> List[str]:
        """
        Validate a batch of rename operations for conflicts.
        
        Args:
            operations: List of (original_name, target_name, path) tuples
            
        Returns:
            List of error messages (empty if all valid)
        """
        errors = []
        target_names = set()
        
        for original_name, target_name, path in operations:
            # Individual name validation
            if not self.validate_target_name(target_name, path):
                errors.append(f"Invalid target name: {target_name}")
                continue
            
            # Batch collision detection
            target_lower = target_name.lower()
            if target_lower in target_names:
                errors.append(f"Duplicate target name in batch: {target_name}")
            else:
                target_names.add(target_lower)
        
        return errors
    
    def suggest_alternative_name(self, target_name: str, directory: Path, max_attempts: int = 100) -> Optional[str]:
        """
        Suggest an alternative filename if the target name has conflicts.
        
        Args:
            target_name: Desired filename that has conflicts
            directory: Directory where file will be placed
            max_attempts: Maximum number of alternatives to try
            
        Returns:
            Alternative filename, or None if no suitable alternative found
        """
        path_obj = Path(target_name)
        stem = path_obj.stem
        suffix = path_obj.suffix
        
        for i in range(1, max_attempts + 1):
            alternative = f"{stem}_{i:03d}{suffix}"
            alternative_path = directory / alternative
            
            if not alternative_path.exists():
                if self.validate_target_name(alternative, directory / "dummy"):
                    return alternative
        
        return None