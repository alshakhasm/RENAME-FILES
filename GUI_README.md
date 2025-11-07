# Date Prefix File Renamer - GUI Usage Guide

## Quick Start

1. **Launch the GUI application:**
   ```bash
   python basic_gui.py
   ```

2. **Select a directory:**
   - Click "Select Directory..." button
   - Choose a folder containing files you want to rename
   - For testing, use the `test_files` directory

3. **Configure options:**
   - **Date Format**: Choose from YYYY-MM-DD, YYYY_MM_DD, MM-DD-YYYY, or DD-MM-YYYY
   - **Recursive**: Process subdirectories (recommended)
   - **Dry Run**: Preview changes without actually renaming (recommended for first run)

4. **Process files:**
   - Click "Preview Changes" (dry run mode) or "Rename Files" (live mode)
   - Confirm the operation in the dialog
   - View results in the detailed results window

## GUI Features

### Main Window
- **Directory Selection**: Visual feedback for selected directory
- **Options Panel**: Configure date format and processing options
- **Control Buttons**: Select, process, and clear operations
- **Status Bar**: Real-time status updates and progress indication

### Results Window
- **Tabbed Interface**: Separate tabs for processed, skipped, and error files
- **Detailed Information**: See original names, new names, and file paths
- **Export Function**: Save results to text or CSV files
- **Summary Statistics**: Quick overview of processing results

### Safety Features
- **Dry Run Mode**: Preview changes before applying them
- **Confirmation Dialogs**: Confirm operations before execution
- **Skip Existing Prefixes**: Won't re-prefix already prefixed files
- **Error Handling**: Graceful handling of locked files, permissions, etc.

## Testing the Application

### Using Test Files
The `test_files` directory contains sample files for testing:
- `document1.txt` - Sample text document
- `meeting_notes.md` - Markdown file
- `employee_data.csv` - CSV data file
- `sample_script.py` - Python script
- `images/photo1.jpg` - Sample image file
- `images/screenshot.png` - Another image file

### Recommended Test Workflow
1. **First Test - Dry Run:**
   - Select the `test_files` directory
   - Keep "Dry run" enabled
   - Click "Preview Changes"
   - Review what would be renamed

2. **Second Test - Live Run:**
   - If satisfied with preview, disable "Dry run"
   - Click "Rename Files"
   - Confirm the operation
   - Files will actually be renamed

3. **View Results:**
   - Check the results tabs to see what was processed
   - Export results if needed
   - Note that already-prefixed files will be skipped

## Date Format Examples

| Format | Example | Description |
|--------|---------|-------------|
| YYYY-MM-DD | 2025-01-21_document1.txt | ISO format (recommended) |
| YYYY_MM_DD | 2025_01_21_document1.txt | Underscore separated |
| MM-DD-YYYY | 01-21-2025_document1.txt | US format |
| DD-MM-YYYY | 21-01-2025_document1.txt | European format |

## Common Use Cases

### Photo Organization
- Process photo directories to add date prefixes
- Use recursive mode for nested folder structures
- Helps organize photos chronologically

### Document Management  
- Add creation dates to documents and files
- Maintain chronological order in file listings
- Useful for backup organization

### Project Files
- Date-prefix project deliverables
- Track file creation timelines
- Organize version history

## Tips and Best Practice

1. **Always test with dry run first** - See what will happen before committing
2. **Use descriptive date formats** - YYYY-MM-DD is usually best for sorting
3. **Check the results window** - Review what was processed, skipped, or failed
4. **Export results for records** - Keep a log of what was renamed
5. **Handle errors gracefully** - Files may be locked or have permission issues

## Troubleshooting

### Common Issues
- **Permission denied**: Run as administrator or check file permissions
- **File in use**: Close applications that might have files open
- **Already prefixed**: Files with existing date prefixes are skipped automatically

### GUI Not Starting
- Ensure Python 3.11+ is installed with tkinter support
- Check that all dependencies are installed
- Try running from the terminal to see error messages

## Technical Notes

### Architecture
- Built with Python tkinter for cross-platform compatibility
- Threaded processing prevents GUI freezing
- Modular design for maintainability

### File Safety
- Uses Python's pathlib for robust file operations
- Validates target paths before renaming
- Handles edge cases like duplicate names

### Performance
- Processes files in background threads
- Progress indication for large directories
- Efficient file system operations