# Date Prefix File Renamer

A desktop application that automatically renames files and folders by adding creation date prefixes. Organizes your files chronologically with a simple drag-and-drop interface.

## Features

- **Automatic Date Prefixing**: Adds creation dates in DDMMYYYY_ format
- **Drag-and-Drop Interface**: Simple GUI for directory selection
- **Safe Operations**: Zero data loss, skips existing prefixes and symbolic links
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Docker Support**: Run consistently across environments
- **Recursive Processing**: Renames folders at all levels, files only in root directory

## Quick Start

### GUI Application (Recommended)

```bash
# Install Python 3.11+ with tkinter support
# On macOS with Homebrew:
brew install python-tk@3.11

# Clone and setup
git clone <repository-url>
cd date-prefix-renamer

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch modern GUI (recommended)
python3.11 modern_gui.py

# Or launch simple GUI (fallback)
python3.11 super_simple_gui.py
```

### CLI Interface

```bash
# Same setup as above, then:
python src/main.py /path/to/directory --dry-run
```

### Docker Usage

```bash
# GUI mode (with X11 forwarding)
docker run -v /path/to/files:/data -e DISPLAY=$DISPLAY date-prefix-renamer

# CLI mode (headless)
docker run -v /path/to/files:/data date-prefix-renamer cli /data/target-directory
```

## Example

**Before:**
```
documents/
├── report.pdf
├── photos/
└── project.zip
```

**After:**
```
documents/
├── 07112025_report.pdf
├── 10022024_photos/
└── 05012024_project.zip
```

## Usage

### GUI Mode (Default)
1. Launch the modern GUI application (`python3.11 modern_gui.py`)
2. Drag and drop files or directories onto the interface
3. Review the preview of changes
4. Click "Execute" to apply date prefixes

**Features:**
- **Modern GUI**: Professional drag-and-drop interface with batch processing
- **Simple GUI**: Basic three-step workflow (Select → Preview → Execute)

### CLI Mode
```bash
# Basic usage
python src/main.py --cli /path/to/directory

# Docker CLI
docker run -v /host/path:/data date-prefix-renamer cli /data/directory
```

## What Gets Renamed

✅ **Processed:**
- Files in the root directory
- All folders (recursively)
- Uses creation date, falls back to modification date

❌ **Skipped:**
- Files in subdirectories (only folders are renamed in subdirs)
- Files already with DDMMYYYY_ prefixes
- Symbolic links (for security)
- Inaccessible files (permission errors)

## Requirements

- Python 3.11+
- tkinter (built-in)
- tkinterdnd2 (for drag-and-drop)

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Run with debugging
python src/main.py --debug
```

## Docker Development

```bash
# Build image
docker build -t date-prefix-renamer .

# Test GUI mode (requires X11)
docker run --rm -v $(pwd)/test-data:/data -e DISPLAY=$DISPLAY date-prefix-renamer

# Test CLI mode
docker run --rm -v $(pwd)/test-data:/data date-prefix-renamer cli /data
```

## Safety Features

- **Zero Data Loss**: Only renames files, never modifies contents
- **Atomic Operations**: Each rename completes fully or not at all
- **Validation**: Checks target names for conflicts and validity
- **Error Recovery**: Continues processing after individual failures
- **Rollback Support**: Maintains records for potential undo operations

## Architecture

```
├── modern_gui.py        # Modern drag-and-drop GUI (recommended)
├── super_simple_gui.py  # Simple fallback GUI
├── src/                 # Core application logic
│   ├── core/           # Business logic (scanning, renaming)
│   ├── gui/            # Modular GUI components  
│   ├── models/         # Data structures and entities
│   ├── utils/          # Validation and helper functions
│   └── main.py         # CLI entry point
├── tests/              # Test framework
├── docker/             # Container deployment
└── specs/              # Project specifications
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- Report issues: [GitHub Issues](https://github.com/example/date-prefix-renamer/issues)
- Documentation: See `docs/` directory
- Examples: Check `examples/` directory