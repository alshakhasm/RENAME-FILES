# Feature Specification: Date Prefix File Renamer

**Feature Branch**: `001-date-prefix-renamer`  
**Created**: 2025-11-05  
**Status**: Draft  
**Input**: User description: "i want an app that rename file / folder by adding prefix to exitinf name based on date of creation of folder . it runs in docker eventually . it detects filder path and rename it after excustion ."

## Clarifications

### Session 2025-11-05

- Q: When renaming files that already have a date prefix in the same format (YYYY-MM-DD_filename), how should the application behave? → A: Skip files that already have correct date prefix format
- Q: Should the application process files and folders recursively (including all subdirectories) or only process items in the top-level directory specified? → A: Process recursively but only rename folders, not files in subdirectories
- Q: When the system cannot determine a file or folder's creation date (due to filesystem limitations or corrupted metadata), what should happen? → A: Use last modified date as fallback
- Q: How should the application handle symbolic links (symlinks) encountered in the directory? → A: Skip symbolic links entirely (do not rename or follow them)
- Q: How should users provide the target directory path to the application? → A: with dnd

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rename Files with Creation Date Prefix (Priority: P1)

As a user, I want to run a command that automatically renames all files and folders in a specified directory by adding their creation date as a prefix to their existing names, so that I can organize my files chronologically without manually checking and renaming each item.

**Why this priority**: This is the core functionality that delivers immediate value - users can organize their files chronologically with a single command execution.

**Independent Test**: Can be fully tested by running the application on a directory with mixed files/folders and verifying all items are renamed with correct date prefixes, delivering immediate file organization value.

**Acceptance Scenarios**:

1. **Given** a directory contains files and folders created on different dates, **When** I run the renamer application on that directory, **Then** all files and folders are renamed with their creation date as a prefix (e.g., "document.pdf" becomes "2025-11-05_document.pdf")
2. **Given** a file named "report.docx" created on 2025-10-15, **When** the application processes it, **Then** it becomes "2025-10-15_report.docx"
3. **Given** a folder named "photos" created on 2025-09-20, **When** the application processes it, **Then** it becomes "2025-09-20_photos"

---

### User Story 2 - Drag-and-Drop Directory Selection (Priority: P2)

As a user, I want to drag and drop a directory onto the application interface to automatically select and process that directory, so that I can easily specify which folder to rename without typing file paths.

**Why this priority**: Essential for usability - users need an intuitive way to specify which directory to process without manual path entry.

**Independent Test**: Can be tested independently by dragging various directories onto the application and confirming it correctly identifies and processes the target location.

**Acceptance Scenarios**:

1. **Given** I drag a valid directory onto the application interface, **When** I drop it, **Then** the application detects and processes all files and folders within that directory
2. **Given** I drag a non-existent or invalid item onto the application, **When** I drop it, **Then** it displays an appropriate error message
3. **Given** I drag a directory without read/write permissions onto the application, **When** I drop it, **Then** it displays a permission error message

---

### User Story 3 - Docker Container Execution (Priority: P3)

As a user, I want to run the file renamer application within a Docker container, so that I can use it consistently across different environments without worrying about system dependencies or installation requirements.

**Why this priority**: Enables consistent deployment and execution across different systems, but the core functionality works without Docker.

**Independent Test**: Can be tested by building and running the Docker container with a mounted directory, verifying the renaming functionality works identically to native execution.

**Acceptance Scenarios**:

1. **Given** I have a Docker environment available, **When** I run the application container with a mounted directory, **Then** it processes and renames files exactly as it would in native execution
2. **Given** I mount a host directory to the container, **When** the application completes execution, **Then** the renamed files are visible and accessible from the host system
3. **Given** the Docker container finishes processing, **When** I check the container logs, **Then** I can see a summary of the renaming operations performed

---

### Edge Cases

- Files with existing YYYY-MM-DD_ prefixes are skipped to prevent duplicate prefixes
- Files with unavailable creation dates use last modified date as fallback for prefix generation
- What occurs when there are permission issues with specific files or folders?
- Symbolic links are skipped entirely to avoid security risks and circular references
- What happens when disk space is insufficient for renaming operations?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect the creation date of each file and folder, using last modified date as fallback when creation date is unavailable
- **FR-002**: System MUST add the creation date as a prefix to the existing name using YYYY-MM-DD format followed by an underscore
- **FR-003**: System MUST preserve the original file extension and folder structure
- **FR-004**: System MUST accept directory input via drag-and-drop functionality for user-friendly path specification
- **FR-005**: System MUST process files in the specified directory and folders recursively through all subdirectories, but only rename folders in subdirectories (not files within them)
- **FR-006**: System MUST handle errors gracefully when files cannot be accessed or renamed
- **FR-007**: System MUST provide feedback about the renaming operations performed
- **FR-008**: System MUST run successfully within a Docker container environment
- **FR-009**: System MUST skip renaming items that already have the correct YYYY-MM-DD_ date prefix format to avoid duplicate prefixes and maintain idempotency
- **FR-010**: System MUST validate directory path existence before attempting to process contents
- **FR-011**: System MUST rename all files and folders in the root directory, but in subdirectories only rename folder names (not individual files)
- **FR-012**: System MUST skip symbolic links entirely without renaming or following them to avoid security risks and circular references
- **FR-013**: System MUST provide a graphical interface that accepts directories via drag-and-drop for intuitive user interaction

### Key Entities

- **File**: Represents individual files with creation date, current name, and file extension
- **Folder**: Represents directories with creation date and current name
- **Directory Path**: The target location specified by the user for processing
- **Rename Operation**: The transformation from original name to date-prefixed name

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully rename all files and folders in a directory with a single command execution
- **SC-002**: Application processes directories containing up to 1000 files/folders within 30 seconds
- **SC-003**: 100% of successfully renamed items follow the YYYY-MM-DD_originalname format consistently
- **SC-004**: Application runs successfully in Docker containers across Linux, Windows, and macOS host systems
- **SC-005**: Zero data loss occurs during renaming operations - all original files remain intact with only names changed
- **SC-006**: Application provides clear feedback showing the number of items processed and any errors encountered