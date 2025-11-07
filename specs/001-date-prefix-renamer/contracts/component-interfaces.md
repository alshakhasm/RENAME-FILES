# Internal Component Contracts

**Generated**: 2025-11-05  
**Feature**: 001-date-prefix-renamer  
**Purpose**: Define interfaces and contracts between core application components

## FileScanner Interface

**Purpose**: Discovers and analyzes files/folders in the target directory

### Method: `scan_directory(directory_path: Path) -> List[FileSystemItem]`

**Input**:
```python
directory_path: Path  # Target directory to scan
```

**Output**:
```python
List[FileSystemItem]  # All discovered items with metadata
```

**Behavior**:
- Recursively traverse directory structure
- Extract creation/modification dates for each item
- Detect existing date prefixes in names
- Flag symbolic links for skipping
- Return items in deterministic order (alphabetical by path)

**Error Conditions**:
- `PermissionError`: Directory not accessible
- `FileNotFoundError`: Directory doesn't exist  
- `OSError`: General filesystem errors

---

## DateExtractor Interface

**Purpose**: Extracts creation dates from filesystem items with platform-specific handling

### Method: `get_creation_date(path: Path) -> datetime`

**Input**:
```python
path: Path  # Path to file or directory
```

**Output**:
```python
datetime  # Creation date (or modification date as fallback)
```

**Behavior**:
- Windows: Use `st_ctime` (creation time)
- macOS: Use `st_birthtime` when available  
- Linux: Fall back to `st_mtime` (modification time)
- Handle timezone conversion to local time
- Return timezone-naive datetime for consistency

**Error Conditions**:
- `PermissionError`: Cannot access file metadata
- `FileNotFoundError`: File no longer exists
- `OSError`: Filesystem corruption or other issues

### Method: `format_date_prefix(date: datetime) -> str`

**Input**:
```python
date: datetime  # Date to format as prefix
```

**Output**:
```python
str  # Formatted as "YYYY-MM-DD_"
```

**Behavior**:
- Format as exactly "YYYY-MM-DD_" (11 characters)
- Use local date (not UTC) for user expectations
- Include underscore separator

---

## PrefixValidator Interface  

**Purpose**: Validates filenames and detects existing date prefixes

### Method: `has_date_prefix(filename: str) -> bool`

**Input**:
```python
filename: str  # Filename to check for existing prefix
```

**Output**:
```python
bool  # True if filename already has YYYY-MM-DD_ prefix
```

**Behavior**:
- Match exact pattern: 4 digits, hyphen, 2 digits, hyphen, 2 digits, underscore
- Validate that date components form a real date
- Return False for partial matches or invalid dates

### Method: `generate_target_name(original_name: str, date_prefix: str) -> str`

**Input**:
```python
original_name: str  # Current filename/directory name
date_prefix: str    # Formatted date prefix (YYYY-MM-DD_)
```

**Output**:
```python
str  # New name with date prefix
```

**Behavior**:
- Concatenate date_prefix + original_name  
- Preserve file extensions and capitalization
- Handle edge cases (empty names, leading/trailing spaces)

### Method: `validate_target_name(name: str, parent_directory: Path) -> bool`

**Input**:
```python
name: str              # Proposed new filename
parent_directory: Path # Directory where file will be renamed
```

**Output**:
```python
bool  # True if name is valid and doesn't conflict
```

**Behavior**:
- Check for invalid filename characters per OS
- Verify name length within filesystem limits
- Ensure no existing file/folder with same name
- Handle case-sensitivity per filesystem type

---

## FileRenamer Interface

**Purpose**: Executes file and folder rename operations safely

### Method: `rename_item(operation: RenameOperation) -> OperationStatus`

**Input**:
```python
operation: RenameOperation  # Details of rename operation to execute
```

**Output**:  
```python
OperationStatus  # COMPLETED, FAILED, or SKIPPED
```

**Behavior**:
- Perform atomic rename operation using `Path.rename()`
- Update operation status and timestamp  
- Log successful operations for potential rollback
- Handle platform-specific rename limitations

**Error Conditions**:
- `FileExistsError`: Target name already exists
- `PermissionError`: Insufficient permissions for rename
- `OSError`: Filesystem errors (disk full, etc.)

### Method: `batch_rename(operations: List[RenameOperation], progress_callback: Callable) -> List[OperationStatus]`

**Input**:
```python
operations: List[RenameOperation]     # All operations to execute
progress_callback: Callable[[int]]   # Function to report progress
```

**Output**:
```python
List[OperationStatus]  # Status for each operation in order
```

**Behavior**:
- Process operations in dependency order (folders before contained items)
- Call progress_callback every 10 operations  
- Stop on first critical error, continue on individual failures
- Support cancellation via thread interruption

---

## ProgressReporter Interface

**Purpose**: Provides progress updates and user feedback during processing

### Method: `report_progress(current: int, total: int, message: str) -> None`

**Input**:
```python
current: int  # Number of completed operations
total: int    # Total number of operations  
message: str  # Current activity description
```

**Behavior**:
- Update GUI progress bar and percentage display
- Show current operation message to user
- Estimate remaining time based on processing rate
- Handle UI thread safety for updates from background threads

### Method: `report_completion(result: OperationResult) -> None`

**Input**:
```python
result: OperationResult  # Final results of processing session
```

**Behavior**:
- Display summary dialog with success/failure counts
- Show detailed error list if any operations failed
- Provide option to view full operation log
- Enable rollback option if applicable

---

## GUI Event Contracts

**Purpose**: Define drag-and-drop and user interaction contracts

### Event: `on_directory_dropped(directory_path: Path) -> None`

**Trigger**: User drags and drops a directory onto the application window

**Behavior**:
- Validate that dropped item is a directory
- Display confirmation dialog with directory path
- Start background scanning process
- Show progress indicator during scan

### Event: `on_process_clicked() -> None`  

**Trigger**: User clicks "Process" button after directory selection

**Behavior**:
- Validate that directory is still accessible
- Create ProcessingSession with current parameters
- Start background rename operations
- Switch UI to progress monitoring mode

### Event: `on_cancel_clicked() -> None`

**Trigger**: User clicks "Cancel" during processing

**Behavior**:
- Set cancellation flag for background thread
- Wait for current operation to complete safely  
- Display partial results and cleanup status
- Return UI to ready state

---

## Error Handling Contracts

### Critical Errors (Stop Processing)
- Directory becomes inaccessible during processing
- Filesystem corruption detected
- Insufficient disk space for operations

### Recoverable Errors (Log and Continue)  
- Individual file permission errors
- Single file locked by another process
- Invalid characters in specific filenames

### User Errors (Immediate Feedback)
- Invalid directory selection (not a directory)  
- Directory with no accessible items
- Attempting to process system directories

---

## Thread Safety Contracts

### GUI Thread Responsibilities
- All tkinter widget updates
- User event handling 
- Progress display updates

### Worker Thread Responsibilities  
- All filesystem operations
- Date extraction and analysis
- Rename operation execution

### Shared State Protection
- Use thread-safe queues for communication
- Protect shared data structures with locks
- Ensure atomic updates to operation status