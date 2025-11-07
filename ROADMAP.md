# Project Roadmap

## Current Status ✅
- **Version**: 1.0.0
- **Status**: Production-ready with working GUIs
- **Date Format**: DDMMYYYY_ (uses actual file creation dates)
- **Features**: Drag-and-drop, batch processing, modern UI

## Known Limitations

### GUI Architecture
- `modern_gui.py` and `super_simple_gui.py` bypass core logic
- Direct file renaming without SessionManager integration
- No validation, conflict handling, or rollback support
- `src/gui/main_window.py` properly integrates with SessionManager (reference implementation)

### Testing
- Test structure exists but minimal implementation
- Core modules (date_extractor, file_scanner, renamer) lack unit tests
- No integration tests for end-to-end workflows

### Docker
- Docker GUI support not implemented (entrypoint shows "not yet implemented")
- README implies GUI usage via Docker but not functional
- X11 forwarding not configured

---

## Phase 1: GUI Alignment 🎯 **High Priority**

**Goal**: Align all GUIs with core workflow for consistency and reliability

### Tasks:
- [ ] **Refactor `modern_gui.py`** to use `SessionManager.run_complete_workflow`
  - Replace direct file stat reading with DateExtractor
  - Add proper validation and conflict detection
  - Implement preview/execute semantics from core
  - Maintain drag-and-drop and batch processing features
  
- [ ] **Refactor `super_simple_gui.py`** to use SessionManager
  - Integrate with core workflow
  - Add validation and error handling
  - Keep simple three-step UI intact
  
- [ ] **Decision**: Retire quick GUIs or keep as lightweight alternatives?
  - **Option A**: Keep as "simple mode" with clear limitations documented
  - **Option B**: Retire and direct all users to `src/gui/main_window.py`
  - **Option C**: Refactor to use core logic (recommended)

**Benefits**:
- Consistent behavior across all interfaces
- Proper validation and conflict handling
- Undo/rollback support
- Better error messages and user feedback

---

## Phase 2: Test Implementation 🧪 **High Priority**

**Goal**: Comprehensive test coverage for core functionality

### Core Module Tests:
- [ ] **`src/core/date_extractor.py`**
  - Test date extraction from file metadata
  - Test format conversions (DDMMYYYY, ISO_DATE, etc.)
  - Test edge cases (invalid dates, future dates)
  - Test fallback mechanisms
  
- [ ] **`src/core/file_scanner.py`**
  - Test directory scanning
  - Test file filtering and exclusion
  - Test recursive folder traversal
  - Test symbolic link handling
  
- [ ] **`src/core/renamer.py`**
  - Test rename operations
  - Test conflict detection
  - Test prefix validation
  - Test error handling and recovery

### Integration Tests:
- [ ] Complete workflow tests (scan → preview → execute)
- [ ] GUI integration tests (if possible with tkinter testing)
- [ ] CLI integration tests with various flags
- [ ] Edge case scenarios (permissions, conflicts, etc.)

### Test Infrastructure:
- [ ] Set up pytest configuration
- [ ] Create comprehensive test fixtures
- [ ] Add CI/CD pipeline (GitHub Actions)
- [ ] Achieve >80% code coverage

**Benefits**:
- Confidence in core functionality
- Catch regressions early
- Safe refactoring
- Documentation through tests

---

## Phase 3: Docker Enhancement 🐳 **Medium Priority**

**Goal**: Clarify and improve Docker support

### Decision Required:
**Option A: CLI-Only Docker** (Recommended for simplicity)
- Update README to state "CLI only in Docker"
- Remove GUI references from Docker documentation
- Focus on headless batch processing
- Provide clear CLI examples

**Option B: Full GUI Docker with X11**
- Implement proper X11 forwarding
- Update `docker/entrypoint.sh` to launch GUI
- Document X11 setup for macOS, Linux, Windows
- Test cross-platform GUI in Docker

### Tasks:
- [ ] Choose Docker strategy (CLI-only vs GUI)
- [ ] Update `docker/entrypoint.sh` accordingly
- [ ] Update README Docker section with accurate instructions
- [ ] Test Docker workflow on all platforms
- [ ] Add Docker Compose file for easier setup

**Benefits**:
- Clear user expectations
- Consistent cross-platform experience
- Avoid confusion about GUI support

---

## Phase 4: Undo/Rollback Support 🔄 **Medium Priority**

**Goal**: Implement safe undo functionality

### Architecture:
- [ ] Integrate `RollbackManager` into `SessionManager`
- [ ] Store operation history in session
- [ ] Add undo command to CLI
- [ ] Add undo button to GUIs
- [ ] Implement rollback validation (ensure files still exist)

### Features:
- [ ] Single-operation undo
- [ ] Batch undo (undo entire session)
- [ ] Undo history viewer
- [ ] Confirmation prompts for undo operations
- [ ] Undo log persistence (optional)

### GUI Integration:
- [ ] Add "Undo Last Operation" button
- [ ] Show operation history in preview
- [ ] Visual feedback for undo actions
- [ ] Disable undo when not applicable

**Benefits**:
- User confidence (mistakes can be reversed)
- Safe experimentation
- Professional-grade feature
- Better user experience

---

## Phase 5: Polish & Documentation 📚 **Low Priority**

### Documentation:
- [ ] Add comprehensive API documentation
- [ ] Create user guide with screenshots
- [ ] Add troubleshooting section
- [ ] Document all configuration options
- [ ] Create video tutorial (optional)

### Code Quality:
- [ ] Add type hints throughout codebase
- [ ] Run static analysis (mypy, pylint)
- [ ] Improve error messages
- [ ] Add logging throughout application
- [ ] Performance profiling and optimization

### Features:
- [ ] Configuration file support (~/.renamerrc)
- [ ] Preset date formats
- [ ] Custom naming patterns
- [ ] Batch processing from file list
- [ ] Export/import settings

---

## Phase 6: Advanced Features 🚀 **Future**

### Potential Enhancements:
- [ ] Multi-language support (i18n)
- [ ] Plugin system for custom formatters
- [ ] Cloud storage integration (Dropbox, Google Drive)
- [ ] Scheduled/automated renaming
- [ ] File content-based dating (EXIF, metadata)
- [ ] Regex-based renaming rules
- [ ] Bulk undo across multiple sessions
- [ ] Integration with file managers (context menu)

---

## Priority Matrix

| Phase | Priority | Impact | Effort | Status |
|-------|----------|--------|--------|--------|
| **Phase 1: GUI Alignment** | 🔴 High | High | Medium | Recommended |
| **Phase 2: Testing** | 🔴 High | High | High | Recommended |
| **Phase 3: Docker** | 🟡 Medium | Medium | Low | Clarification needed |
| **Phase 4: Undo/Rollback** | 🟡 Medium | High | Medium | Nice to have |
| **Phase 5: Polish** | 🟢 Low | Medium | Medium | Future |
| **Phase 6: Advanced** | 🟢 Low | Low | High | Future |

---

## Quick Wins (Immediate Actions)

1. **Add basic unit tests** for date_extractor (1-2 hours)
2. **Document Docker limitations** in README (30 minutes)
3. **Add type hints** to core modules (2-3 hours)
4. **Create GitHub Issues** for each phase task (1 hour)

---

## Version Planning

### v1.1.0 (Next Release)
- GUI alignment with SessionManager
- Basic test coverage (>50%)
- Docker clarification

### v1.2.0
- Comprehensive test coverage (>80%)
- Undo/rollback support
- CLI enhancements

### v2.0.0
- Advanced features
- Plugin system
- Multi-language support

---

## Contributing

To contribute to these roadmap items:

1. Check existing GitHub Issues
2. Comment on the issue you want to work on
3. Fork the repository
4. Create a feature branch
5. Submit a Pull Request

---

**Last Updated**: November 7, 2025  
**Maintainer**: @alshakhasm
