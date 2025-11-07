#!/usr/bin/env python3
"""
GUI Launcher for Date Prefix File Renamer.

This script provides a simple way to launch the GUI application
with proper error handling and dependency checking.
"""

import sys
import os
from pathlib import Path

# Add src directory to path for imports
script_dir = Path(__file__).parent
src_dir = script_dir / 'src'
sys.path.insert(0, str(src_dir))

def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    # Check for tkinter (should be built-in)
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter (Python GUI library)")
    
    # Check for tkinterdnd2
    try:
        import tkinterdnd2
    except ImportError:
        missing_deps.append("tkinterdnd2 (drag and drop support)")
    
    return missing_deps

def install_dependencies():
    """Attempt to install missing dependencies."""
    import subprocess
    
    print("Installing missing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tkinterdnd2"])
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def main():
    """Main entry point for GUI launcher."""
    print("Date Prefix File Renamer - GUI Mode")
    print("=" * 40)
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print("Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        
        print("\nAttempting to install dependencies...")
        if not install_dependencies():
            print("\nPlease install the missing dependencies manually:")
            print("  pip install tkinterdnd2")
            return 1
        
        # Re-check after installation
        missing_deps = check_dependencies()
        if missing_deps:
            print("Some dependencies are still missing. Please install manually.")
            return 1
    
    # Launch GUI
    try:
        print("Starting GUI application...")
        from gui.main_window import main as gui_main
        gui_main()
        return 0
        
    except ImportError as e:
        print(f"Failed to import GUI modules: {e}")
        print("Make sure you're running this from the project root directory.")
        return 1
    
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        return 0
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())