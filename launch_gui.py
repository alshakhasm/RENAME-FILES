#!/usr/bin/env python3
"""
Simple GUI Launcher for Date Prefix File Renamer.

This script properly handles module imports and launches the GUI application.
"""

import sys
import os
from pathlib import Path

def setup_python_path():
    """Setup Python path for module imports."""
    # Get script directory and add src to path
    script_dir = Path(__file__).parent.absolute()
    src_dir = script_dir / 'src'
    
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    return src_dir

def check_gui_dependencies():
    """Check if GUI dependencies are available."""
    try:
        import tkinter
        import tkinterdnd2
        return True
    except ImportError as e:
        print(f"Missing GUI dependencies: {e}")
        print("Please install: pip install tkinterdnd2")
        return False

def main():
    """Main entry point for GUI launcher."""
    print("Date Prefix File Renamer - GUI Application")
    print("=" * 45)
    
    # Setup paths
    src_dir = setup_python_path()
    print(f"Source directory: {src_dir}")
    
    # Check dependencies
    if not check_gui_dependencies():
        return 1
    
    print("✓ GUI dependencies available")
    
    # Import and launch GUI
    try:
        print("Launching GUI application...")
        
        # Import the GUI main function
        from gui.main_window import main as gui_main
        
        # Launch the GUI
        gui_main()
        return 0
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        return 0
        
    except Exception as e:
        print(f"Failed to launch GUI: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())