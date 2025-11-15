#!/usr/bin/env python3.11
"""
Folder Renamer GUI - Native macOS app with drag-and-drop support
Uses tkinterdnd2 for proper drag-and-drop handling
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from pathlib import Path
from datetime import datetime
import sys

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    TkinterDnD = tk

class FolderRenamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📁 Folder Renamer")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('aqua')
        
        # Main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(main_frame, text="📁 Folder Renamer", font=("Helvetica", 24, "bold"))
        title.pack(pady=20)
        
        # Subtitle
        subtitle = ttk.Label(main_frame, text="Rename folders/files with date prefix (DDMMYYYY_name)", 
                            font=("Helvetica", 12), foreground="gray")
        subtitle.pack(pady=(0, 20))
        
        # Drop zone
        drop_frame = tk.Frame(main_frame, relief=tk.GROOVE, borderwidth=2, bg="#f0f0f0", height=150)
        drop_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        if HAS_DND:
            drop_frame.drop_target_register(DND_FILES)
            drop_frame.dnd_bind('<<Drop>>', self.drop_handler)
            drop_text = "Drag & Drop folders or files here"
        else:
            drop_text = "Use 'Select' button below (drag-drop unavailable)"
        
        drop_label = ttk.Label(drop_frame, text=drop_text, 
                              font=("Helvetica", 14), background="#f0f0f0")
        drop_label.pack(pady=50, expand=True)
        
        # Button section
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        select_btn = ttk.Button(button_frame, text="📂 Select Folder/File", command=self.select_item)
        select_btn.pack(pady=10, padx=10, fill=tk.X)
        
        # Status area
        self.status_text = tk.Text(main_frame, height=8, width=60, state=tk.DISABLED, font=("Monaco", 10))
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scroll bar for status
        scrollbar = ttk.Scrollbar(self.status_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.status_text.yview)
    
    def drop_handler(self, event):
        """Handle drag-and-drop"""
        files = self.root.tk.splitlist(event.data)
        for file_path in files:
            # Remove curly braces if present (macOS adds them)
            file_path = file_path.strip('{}')
            self.process_item(file_path)
    
    def select_item(self):
        """Open file/folder selector"""
        item_path = filedialog.askdirectory(title="Select Folder")
        if item_path:
            self.process_item(item_path)
    
    def get_item_date(self, item_path: str) -> datetime:
        """Get file/folder creation or modification date"""
        try:
            stat_info = Path(item_path).stat()
            if hasattr(stat_info, 'st_birthtime'):
                return datetime.fromtimestamp(stat_info.st_birthtime)
            else:
                return datetime.fromtimestamp(stat_info.st_mtime)
        except Exception:
            return datetime.now()
    
    def process_item(self, item_path: str):
        """Rename an item in-place"""
        if not os.path.exists(item_path):
            self.append_status(f"❌ Item not found: {item_path}\n")
            return
        
        item_name = os.path.basename(item_path)
        parent_dir = os.path.dirname(item_path)
        
        # Check if already renamed
        if len(item_name) > 9 and item_name[:8].isdigit() and item_name[8] == '_':
            self.append_status(f"⏭️  Already renamed: {item_name}\n")
            return
        
        # Get date and create new name
        item_date = self.get_item_date(item_path)
        date_prefix = item_date.strftime("%d%m%Y")
        new_name = f"{date_prefix}_{item_name}"
        new_path = os.path.join(parent_dir, new_name)
        
        # Check if target exists
        if os.path.exists(new_path):
            self.append_status(f"⚠️  Target already exists: {new_name}\n")
            return
        
        # Rename in-place
        try:
            os.rename(item_path, new_path)
            item_type = "📁 Folder" if os.path.isdir(new_path) else "📄 File"
            self.append_status(f"✅ {item_type} renamed:\n   {item_name}\n   ↓\n   {new_name}\n\n")
        except Exception as e:
            self.append_status(f"❌ Error renaming {item_name}: {e}\n")
    
    def append_status(self, message: str):
        """Add message to status text"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message)
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)

def main():
    if HAS_DND:
        root = TkinterDnD.Tk()
        print("✅ Using tkinterdnd2 for drag-and-drop support")
    else:
        root = tk.Tk()
        print("⚠️  tkinterdnd2 not available - using basic mode")
        print("� Install with: pip install tkinterdnd2")
    
    app = FolderRenamerGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
