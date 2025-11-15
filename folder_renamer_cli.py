#!/usr/bin/env python3.11
"""
Folder Renamer CLI - Watch a folder for drag-and-drop and rename items in-place
Supports both files and folders with date prefix (DDMMYYYY_itemname)
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import time
import argparse
from typing import Optional

def get_item_date(item_path: str) -> datetime:
    """Get file/folder creation or modification date"""
    try:
        stat_info = Path(item_path).stat()
        if hasattr(stat_info, 'st_birthtime'):
            return datetime.fromtimestamp(stat_info.st_birthtime)
        else:
            return datetime.fromtimestamp(stat_info.st_mtime)
    except Exception:
        return datetime.now()

def rename_item_in_place(item_path: str) -> Optional[str]:
    """
    Rename a file or folder in-place with date prefix.
    Returns the new path if successful, None if already renamed or error.
    """
    item_path = os.path.expanduser(item_path)
    
    if not os.path.exists(item_path):
        print(f"❌ Item not found: {item_path}")
        return None
    
    # Get item name and directory
    parent_dir = os.path.dirname(item_path)
    item_name = os.path.basename(item_path)
    
    # Check if already has date prefix (DDMMYYYY_)
    if len(item_name) > 9 and item_name[:8].isdigit() and item_name[8] == '_':
        print(f"⏭️  Already renamed: {item_name}")
        return item_path
    
    # Get date and create new name
    item_date = get_item_date(item_path)
    date_prefix = item_date.strftime("%d%m%Y")
    new_name = f"{date_prefix}_{item_name}"
    new_path = os.path.join(parent_dir, new_name)
    
    # Check if target already exists
    if os.path.exists(new_path):
        print(f"⚠️  Target already exists: {new_name}")
        return None
    
    # Rename in-place
    try:
        os.rename(item_path, new_path)
        item_type = "📁 Folder" if os.path.isdir(new_path) else "📄 File"
        print(f"✅ {item_type} renamed: {item_name} → {new_name}")
        return new_path
    except Exception as e:
        print(f"❌ Error renaming {item_name}: {e}")
        return None

def watch_folder(watch_path: str, recursive: bool = False) -> None:
    """
    Watch a folder for new items and rename them automatically.
    Press Ctrl+C to stop.
    """
    watch_path = os.path.expanduser(watch_path)
    os.makedirs(watch_path, exist_ok=True)
    
    print(f"📂 Watching: {watch_path}")
    print(f"🔄 Recursive: {recursive}")
    print("💡 Drag and drop items here. Press Ctrl+C to stop.\n")
    
    # Try to use watchdog if available, otherwise fall back to polling
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class DropHandler(FileSystemEventHandler):
            def on_created(self, event):
                # Wait for file/folder to be fully written
                time.sleep(1)
                if os.path.exists(event.src_path):
                    if not os.path.basename(event.src_path).startswith('.'):
                        rename_item_in_place(event.src_path)
            
            def on_moved(self, event):
                # Handle drag-drop which may generate move events
                time.sleep(1)
                if os.path.exists(event.dest_path):
                    if not os.path.basename(event.dest_path).startswith('.'):
                        rename_item_in_place(event.dest_path)
        
        observer = Observer()
        observer.schedule(DropHandler(), watch_path, recursive=recursive)
        observer.start()
        
        print("✨ Using watchdog for instant detection\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Stopped watching.")
            observer.stop()
            observer.join()
            sys.exit(0)
    
    except ImportError:
        # Fallback to polling if watchdog not available
        print("⚠️  watchdog not installed, using polling (slower)\n")
        print("💡 To install: pip install watchdog\n")
        
        seen_items = set()
        
        try:
            while True:
                # Get current items in watch folder
                try:
                    if recursive:
                        current_items = set()
                        for root, dirs, files in os.walk(watch_path):
                            for d in dirs:
                                item_path = os.path.join(root, d)
                                if not os.path.basename(item_path).startswith('.'):
                                    current_items.add(item_path)
                            for f in files:
                                item_path = os.path.join(root, f)
                                if not os.path.basename(item_path).startswith('.'):
                                    current_items.add(item_path)
                    else:
                        current_items = set()
                        for item in os.listdir(watch_path):
                            if not item.startswith('.'):
                                item_path = os.path.join(watch_path, item)
                                current_items.add(item_path)
                except OSError:
                    current_items = set()
                
                # Find new items
                new_items = current_items - seen_items
                
                for item_path in sorted(new_items):
                    # Give the file system time to finish writing
                    time.sleep(0.5)
                    
                    if os.path.exists(item_path):
                        rename_item_in_place(item_path)
                    
                    seen_items.add(item_path)
                
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            print("\n\n👋 Stopped watching.")
            sys.exit(0)

def process_single_item(item_path: str) -> None:
    """Process a single file or folder"""
    result = rename_item_in_place(item_path)
    if result:
        print(f"📍 New path: {result}")
    sys.exit(0 if result else 1)

def main():
    parser = argparse.ArgumentParser(
        description="Rename files and folders with date prefix (DDMMYYYY_name)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Watch ~/Downloads for new items and rename them
  python3.11 folder_renamer_cli.py --watch ~/Downloads
  
  # Watch recursively (include subfolders)
  python3.11 folder_renamer_cli.py --watch ~/Downloads --recursive
  
  # Rename a single item
  python3.11 folder_renamer_cli.py --rename ~/Downloads/MyFolder
        """
    )
    
    parser.add_argument(
        '--watch',
        type=str,
        help='Watch folder path for new items (drag-and-drop)'
    )
    parser.add_argument(
        '--rename',
        type=str,
        help='Rename a single file or folder in-place'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Watch subfolders recursively (with --watch)'
    )
    
    args = parser.parse_args()
    
    if args.watch:
        watch_folder(args.watch, recursive=args.recursive)
    elif args.rename:
        process_single_item(args.rename)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
