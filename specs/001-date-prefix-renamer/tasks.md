# Tasks: Date Prefix File Renamer

**Input**: Design documents from `/specs/001-date-prefix-renamer/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single desktop application structure:
- **Source**: `src/` at repository root
- **Tests**: `tests/` at repository root  
- **Docker**: `docker/` at repository root

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure with src/, tests/, docker/ folders
- [x] T002 Initialize Python project with requirements.txt and setup.py
- [x] T003 [P] Create src/__init__.py and package structure
- [x] T004 [P] Create tests/unit/__init__.py and tests/integration/__init__.py
- [x] T005 [P] Create docker/Dockerfile for containerization
- [x] T006 [P] Create docker/entrypoint.sh for container startup script
- [x] T007 [P] Create README.md with basic project information

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008: ✅ Create core data models in src/models/__init__.py
**Description**: Implement FileSystemItem, RenameOperation, ProcessingSession, OperationResult classes with dataclasses and proper typing
**Acceptance Criteria**:
- [x] FileSystemItem: path, name, creation_date, is_directory, has_date_prefix fields
- [x] RenameOperation: item reference, original_name, target_name, status, error handling
- [x] ProcessingSession: progress tracking, session management, operation queuing  
- [x] OperationResult: outcome capture, rollback data, execution statistics
- [x] All models use proper type hints and validation
**Priority**: Critical
- [x] T009 Create enumerations in src/models/enums.py with OperationType, OperationStatus, SessionStatus
- [x] T010 [P] Implement DateExtractor interface in src/core/date_extractor.py with get_creation_date() and format_date_prefix() methods
- [x] T011 [P] Implement PrefixValidator interface in src/utils/validators.py with has_date_prefix(), generate_target_name(), validate_target_name() methods
- [x] T012 [P] Create base exception classes in src/utils/exceptions.py for application-specific errors
- [x] T013 [P] Create logging configuration in src/utils/logging.py for operation tracking
- [x] T014 [P] Create test fixtures in tests/fixtures/sample_files/ directory with known file structures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Rename Files with Creation Date Prefix (Priority: P1) 🎯 MVP

**Goal**: Core file/folder renaming functionality with date prefix generation

**Independent Test**: Create test directory with mixed files/folders, run renaming operation, verify all items get correct YYYY-MM-DD_ prefixes

### Implementation for User Story 1

- [x] T015 [P] [US1] Implement FileScanner interface in src/core/file_scanner.py with scan_directory() method for directory traversal
- [x] T016 [P] [US1] Implement FileRenamer interface in src/core/renamer.py with rename_item() and batch_rename() methods
- [x] T017 [US1] Create ProcessingSession manager in src/core/session.py to coordinate scanning and renaming operations
- [x] T018 [US1] Implement business logic for date prefix detection and skipping existing prefixes in src/core/renamer.py
- [x] T019 [US1] Add symlink detection and skipping logic in src/core/file_scanner.py
- [x] T020 [US1] Implement recursive folder processing (folders only in subdirectories) in src/core/file_scanner.py
- [x] T021 [US1] Add error handling for permission issues and locked files in src/core/renamer.py
- [x] T022 [US1] Create basic CLI interface in src/main.py for command-line testing

**Checkpoint**: At this point, User Story 1 should be fully functional via CLI and testable independently

---

## Phase 4: User Story 2 - Drag-and-Drop Directory Selection (Priority: P2)

**Goal**: GUI interface with drag-and-drop functionality for intuitive directory selection

**Independent Test**: Launch GUI application, drag various directories onto interface, verify correct processing and error handling

### Implementation for User Story 2

- [ ] T023 [P] [US2] Create main GUI window in src/gui/main_window.py with tkinter interface
- [ ] T024 [P] [US2] Implement drag-and-drop zone using tkinterdnd2 in src/gui/main_window.py
- [ ] T025 [US2] Add directory validation and error display dialogs in src/gui/main_window.py
- [ ] T026 [US2] Create progress dialog in src/gui/progress_dialog.py for operation feedback
- [ ] T027 [US2] Implement ProgressReporter interface in src/gui/progress_reporter.py for UI updates
- [ ] T028 [US2] Add threading support for background processing in src/gui/main_window.py
- [ ] T029 [US2] Create results display dialog in src/gui/results_dialog.py for operation summary
- [ ] T030 [US2] Integrate GUI with existing ProcessingSession from User Story 1
- [ ] T031 [US2] Add application icons and styling in src/gui/resources/
- [ ] T032 [US2] Update main.py to launch GUI by default with --cli flag for command-line mode

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (CLI and GUI modes)

---

## Phase 5: User Story 3 - Docker Container Execution (Priority: P3)

**Goal**: Containerized deployment with both GUI (X11 forwarding) and CLI modes

**Independent Test**: Build Docker container, test with mounted directories in both GUI and CLI modes, verify identical functionality to native execution

### Implementation for User Story 3

- [ ] T033 [P] [US3] Complete Dockerfile in docker/Dockerfile with Python 3.11+ base image and dependencies
- [ ] T034 [P] [US3] Implement container entrypoint logic in docker/entrypoint.sh for GUI/CLI mode detection
- [ ] T035 [US3] Add X11 forwarding configuration for GUI mode in docker/Dockerfile
- [ ] T036 [US3] Create CLI-only mode for headless containers in src/main.py
- [ ] T037 [US3] Add volume mounting validation for directory access in docker/entrypoint.sh
- [ ] T038 [US3] Implement container-specific logging and output in src/utils/logging.py
- [ ] T039 [US3] Add Docker build and run scripts in scripts/build.sh and scripts/run.sh
- [ ] T040 [US3] Create docker-compose.yml for easy container orchestration
- [ ] T041 [US3] Test and document X11 forwarding setup for different host OS (Linux/macOS/Windows)

**Checkpoint**: All user stories should now be independently functional in native and containerized environments

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Create comprehensive unit tests in tests/unit/test_date_extractor.py for date extraction logic
- [ ] T043 [P] Create unit tests in tests/unit/test_file_scanner.py for directory scanning functionality
- [ ] T044 [P] Create unit tests in tests/unit/test_renamer.py for rename operation logic
- [ ] T045 [P] Create unit tests in tests/unit/test_validators.py for prefix validation functions
- [ ] T046 [P] Create integration tests in tests/integration/test_full_workflow.py for end-to-end scenarios
- [ ] T047 [P] Create Docker integration tests in tests/integration/test_docker.py for container functionality
- [ ] T048 [P] Add performance benchmarking in tests/performance/test_large_directories.py for 1000+ file scenarios
- [ ] T049 [P] Update README.md with comprehensive usage instructions and examples
- [ ] T050 [P] Create user documentation in docs/user-guide.md based on quickstart.md
- [ ] T051 [P] Add code quality tools configuration (.flake8, .pylintrc, pyproject.toml)
- [ ] T052 [P] Implement rollback functionality for failed operations in src/core/rollback.py
- [ ] T053 [P] Add configuration file support in src/utils/config.py for customizable date formats
- [ ] T054 Perform security review for Docker container and filesystem operations
- [ ] T055 Run quickstart.md validation and update based on actual implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 ProcessingSession but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses existing CLI/GUI modes but independently testable

### Within Each User Story

- Core implementation components before integration
- Business logic before user interface
- Error handling after basic functionality
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Models and utilities within different modules marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch core components for User Story 1 together:
Task: "Implement FileScanner interface in src/core/file_scanner.py"
Task: "Implement FileRenamer interface in src/core/renamer.py"

# After core components, integrate:
Task: "Create ProcessingSession manager in src/core/session.py"
```

## Parallel Example: User Story 2

```bash
# Launch GUI components for User Story 2 together:
Task: "Create main GUI window in src/gui/main_window.py"  
Task: "Implement drag-and-drop zone using tkinterdnd2 in src/gui/main_window.py"
Task: "Create progress dialog in src/gui/progress_dialog.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (CLI-based renaming)
4. **STOP and VALIDATE**: Test CLI renaming functionality independently
5. Deploy/demo CLI version if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test CLI functionality independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test GUI functionality independently → Deploy/Demo
4. Add User Story 3 → Test Docker functionality independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Core renaming logic)
   - Developer B: User Story 2 (GUI interface)
   - Developer C: User Story 3 (Docker containerization)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies within same phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Focus on file safety and zero data loss throughout implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Test with various file types, permissions, and directory structures
- Validate cross-platform compatibility (Windows, macOS, Linux)