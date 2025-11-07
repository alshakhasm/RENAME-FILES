# Quickstart Guide: Date Prefix File Renamer

**Version**: 1.0  
**Last Updated**: 2025-11-05  
**Target Audience**: End users and developers

## Overview

Date Prefix File Renamer is a desktop application that automatically adds creation date prefixes to files and folders. It provides a simple drag-and-drop interface for selecting directories and processes them safely with comprehensive error handling.

## Quick Start (End Users)

### Installation

**Option 1: Direct Python Installation**
```bash
# Clone or download the application
git clone <repository-url>
cd date-prefix-renamer

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

**Option 2: Docker Container**
```bash
# For GUI mode (Linux/macOS with X11)
docker run -v /path/to/your/files:/data -e DISPLAY=$DISPLAY date-prefix-renamer

# For CLI mode (headless environments)  
docker run -v /path/to/your/files:/data date-prefix-renamer --cli /data/target-directory
```

### Basic Usage

1. **Launch Application**: Run `python src/main.py` or use Docker command
2. **Select Directory**: Drag and drop a folder onto the application window
3. **Review Preview**: Check the list of files that will be renamed
4. **Process Files**: Click "Rename Files" to apply date prefixes  
5. **View Results**: Review the summary of successful and failed operations

### Example Results

**Before Processing**:
```
my-documents/
├── report.pdf
├── presentation.pptx  
├── photos/
│   ├── vacation.jpg
│   └── family.png
└── projects/
    └── code.zip
```

**After Processing**:
```
my-documents/
├── 2024-03-15_report.pdf
├── 2024-03-20_presentation.pptx
├── 2024-02-10_photos/
│   ├── vacation.jpg          # Files in subdirs not renamed
│   └── family.png            # Files in subdirs not renamed  
└── 2024-01-05_projects/
    └── code.zip               # Files in subdirs not renamed
```

## Advanced Usage

### Dry Run Mode
Test renaming operations without making changes:
```bash
python src/main.py --dry-run /path/to/directory
```

### CLI Mode  
Use without GUI for scripting or automation:
```bash
python src/main.py --cli /path/to/directory --format "YYYY-MM-DD_"
```

### Docker with Volume Mounting
Process directories while maintaining file ownership:
```bash
docker run -v /host/path:/container/path date-prefix-renamer --cli /container/path
```

## What Gets Renamed

### ✅ Processed Items
- **Files in root directory**: All regular files get date prefixes
- **All folders**: Both root and nested folders get prefixes recursively  
- **Creation date priority**: Uses filesystem creation date when available
- **Modification date fallback**: Uses last modified date on Linux systems

### ❌ Skipped Items  
- **Files in subdirectories**: Only renamed if in the root directory
- **Already prefixed items**: Files/folders with existing YYYY-MM-DD_ prefixes
- **Symbolic links**: Skipped entirely to avoid security risks
- **Inaccessible items**: Files without read/write permissions

## Configuration Options

### Date Format
- **Default**: `YYYY-MM-DD_` (e.g., "2024-03-15_document.pdf")
- **Timezone**: Uses local system timezone for consistency
- **Fallback**: Modification date when creation date unavailable

### Processing Behavior
- **Recursive folders**: Renames folders at all directory levels
- **File scope**: Only renames files in the target directory root  
- **Conflict handling**: Skips items if target name already exists
- **Error recovery**: Continues processing other items after individual failures

## Safety Features

### Data Protection
- **Zero data loss**: Only renames files, never modifies contents
- **Atomic operations**: Each rename completes fully or not at all
- **Rollback capability**: Maintains record of original names
- **Preview mode**: Shows intended changes before applying them

### Error Handling
- **Permission errors**: Gracefully skips files without access
- **Locked files**: Reports conflicts with other applications
- **Invalid names**: Validates target names for filesystem compatibility
- **Disk space**: Checks available space before operations

## Troubleshooting

### Common Issues

**Problem**: "Permission denied" errors
```
Solution: Run as administrator or check file permissions
Windows: Right-click → "Run as administrator"  
Linux/macOS: Use sudo or change file ownership
```

**Problem**: Files already have date prefixes
```
Solution: Application automatically skips these files
Check the summary report for skipped items count
```

**Problem**: GUI doesn't appear in Docker
```  
Solution: Ensure X11 forwarding is configured
Linux: xhost +local:docker
macOS: Install XQuartz and allow connections
```

**Problem**: Some files not renamed in subdirectories
```
Solution: This is expected behavior
Only files in root directory are renamed
All folders (root and nested) get prefixes
```

### Performance Issues

**Large Directories (1000+ files)**:
- Processing may take several minutes
- Progress bar shows current status
- Cancel button available during processing
- Consider using CLI mode for very large directories

**Memory Usage**:
- Application uses minimal memory (<50MB typical)
- Scales linearly with directory size
- Docker containers have default memory limits

### Getting Help

**Log Files**: Check console output or Docker logs for detailed error messages
**Dry Run**: Use preview mode to test operations before applying
**Support**: Report issues with specific error messages and system details

## Developer Quick Start

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd date-prefix-renamer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run with development flags
python src/main.py --debug --dry-run
```

### Project Structure
```
src/
├── gui/              # Tkinter interface components
├── core/             # Business logic (scanning, renaming)  
├── utils/            # Validation and helper functions
└── main.py           # Application entry point

tests/
├── unit/             # Component unit tests
├── integration/      # Full workflow tests  
└── fixtures/         # Test data and mock directories

docker/
├── Dockerfile        # Container build configuration
└── entrypoint.sh     # Container startup script
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only  
pytest tests/unit/

# Integration tests with real filesystem
pytest tests/integration/

# Coverage report
pytest --cov=src --cov-report=html
```

### Building Docker Image

```bash
# Build image
docker build -t date-prefix-renamer .

# Test container
docker run --rm date-prefix-renamer --help

# Run with volume mount
docker run --rm -v $(pwd)/test-data:/data date-prefix-renamer --cli /data
```

## Next Steps

- **Production Use**: Review processing results and adjust workflow as needed
- **Integration**: Consider CLI mode for automation scripts or CI/CD pipelines  
- **Customization**: Modify date format or processing rules by editing source code
- **Scaling**: Use Docker containers for consistent deployment across environments