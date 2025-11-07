# Data Model: Date Prefix File Renamer

**Generated**: 2025-11-05  
**Feature**: 001-date-prefix-renamer  
**Purpose**: Define core entities and their relationships for file renaming operations

## Core Entities

### FileSystemItem

**Purpose**: Base representation of files and directories in the target location

**Attributes**:
- `path: Path` - Absolute filesystem path to the item
- `name: str` - Current filename or directory name (without path)
- `creation_date: datetime` - Creation timestamp (with fallback to modification date)
- `modification_date: datetime` - Last modification timestamp  
- `is_directory: bool` - Flag indicating if item is a directory
- `is_symlink: bool` - Flag indicating if item is a symbolic link
- `has_date_prefix: bool` - Flag indicating if name already has YYYY-MM-DD_ prefix
- `size_bytes: int` - File size in bytes (0 for directories)

**Validation Rules**:
- Path must exist and be accessible
- Creation date cannot be in the future
- Symlinks are flagged but not processed
- Date prefix detection follows YYYY-MM-DD_ pattern exactly

**State Transitions**:
- `Discovered` → `Analyzed` (after date extraction and validation)
- `Analyzed` → `Queued` (when scheduled for renaming)  
- `Queued` → `Renamed` (after successful rename operation)
- `Queued` → `Skipped` (if already has prefix or is symlink)
- `Queued` → `Failed` (if rename operation encounters error)

### RenameOperation

**Purpose**: Represents a single file/folder rename operation with before/after state

**Attributes**:
- `item: FileSystemItem` - Reference to the item being renamed
- `original_name: str` - Original filename/directory name  
- `target_name: str` - New name with date prefix (YYYY-MM-DD_originalname)
- `operation_type: OperationType` - Enum: FILE_RENAME, FOLDER_RENAME, SKIPPED
- `status: OperationStatus` - Enum: PENDING, IN_PROGRESS, COMPLETED, FAILED, SKIPPED
- `error_message: str | None` - Error details if operation failed
- `timestamp: datetime` - When operation was executed
- `rollback_possible: bool` - Whether operation can be undone

**Validation Rules**:
- Target name must not already exist in the same directory
- Target name must be valid for the filesystem (length, characters)
- Original item must be accessible for rename operation
- Date prefix format must be exactly YYYY-MM-DD_

**Business Rules**:
- Skip items that already have correct date prefix format
- Skip symbolic links entirely for safety
- Use creation date when available, fallback to modification date
- Process files in root directory, only folders in subdirectories

### ProcessingSession

**Purpose**: Manages a complete directory processing workflow with progress tracking

**Attributes**:
- `target_directory: Path` - Root directory being processed
- `discovered_items: List[FileSystemItem]` - All items found during scan
- `rename_operations: List[RenameOperation]` - Operations to be performed
- `session_id: str` - Unique identifier for this processing session
- `start_time: datetime` - When processing began
- `end_time: datetime | None` - When processing completed (None if in progress)
- `total_items: int` - Count of all discovered items
- `processed_count: int` - Count of completed operations
- `skipped_count: int` - Count of skipped items (existing prefixes, symlinks)
- `error_count: int` - Count of failed operations
- `is_dry_run: bool` - Whether this is a preview mode (no actual renaming)

**Calculated Properties**:
- `progress_percentage: float` - (processed_count / total_items) * 100
- `completion_status: SessionStatus` - SCANNING, PROCESSING, COMPLETED, CANCELLED, FAILED
- `estimated_remaining_time: timedelta` - Based on current processing rate

### OperationResult

**Purpose**: Captures the outcome and details of the complete processing session

**Attributes**:
- `session: ProcessingSession` - Reference to the processing session
- `successful_renames: List[RenameOperation]` - Operations that completed successfully
- `failed_operations: List[RenameOperation]` - Operations that encountered errors  
- `skipped_items: List[FileSystemItem]` - Items that were skipped (prefixes, symlinks)
- `execution_time: timedelta` - Total time taken for processing
- `rollback_data: Dict[str, str]` - Original names for potential rollback
- `summary_message: str` - Human-readable summary of results

## Entity Relationships

```
ProcessingSession (1) ──────── (many) RenameOperation
       │                              │
       │                              │
       └─── (many) FileSystemItem ────┘
                   │
                   └─── (1) OperationResult
```

**Relationship Rules**:
- Each ProcessingSession contains multiple FileSystemItems discovered in target directory
- Each FileSystemItem may have zero or one RenameOperation (none if skipped)
- Each ProcessingSession produces exactly one OperationResult upon completion
- RenameOperations maintain references to their source FileSystemItem

## Enumerations

### OperationType
- `FILE_RENAME` - Renaming a regular file
- `FOLDER_RENAME` - Renaming a directory
- `SKIPPED` - Item was skipped (already has prefix or is symlink)

### OperationStatus  
- `PENDING` - Operation queued but not yet started
- `IN_PROGRESS` - Operation currently being executed
- `COMPLETED` - Operation finished successfully  
- `FAILED` - Operation encountered an error
- `SKIPPED` - Operation was skipped by business rules

### SessionStatus
- `SCANNING` - Discovering and analyzing items in target directory
- `PROCESSING` - Executing rename operations
- `COMPLETED` - All operations finished (successfully or with errors)
- `CANCELLED` - User cancelled the operation
- `FAILED` - Critical error prevented completion

## Data Flow

1. **Discovery Phase**: Scan target directory → Create FileSystemItem entities
2. **Analysis Phase**: Extract dates, detect existing prefixes → Update FileSystemItem properties  
3. **Planning Phase**: Create RenameOperation entities for eligible items
4. **Execution Phase**: Process operations → Update OperationStatus
5. **Completion Phase**: Generate OperationResult with summary data

## Validation and Constraints

### Filesystem Constraints
- Maximum path length varies by OS (260 chars Windows, 4096 chars Linux/macOS)
- Invalid filename characters: `< > : " | ? * \0` and control characters
- Reserved names (Windows): CON, PRN, AUX, NUL, COM1-9, LPT1-9
- Case sensitivity varies by filesystem

### Date Format Constraints  
- Prefix format: `YYYY-MM-DD_` (exactly 11 characters including underscore)
- Valid date range: 1900-01-01 to current date + 1 day (future tolerance)
- Timezone handling: Use local filesystem timezone for consistency

### Performance Constraints
- Memory usage: Stream processing for directories with >10,000 items
- UI responsiveness: Update progress every 50 operations or 500ms intervals
- Cancellation: Check for user cancellation every 10 operations