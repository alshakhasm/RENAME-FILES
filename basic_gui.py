"""
Basic GUI Application for Date Prefix File Renamer.

This version works without tkinterdnd2 to avoid architecture issues.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os
from pathlib import Path
from datetime import datetime
import threading
from datetime import datetime


class BasicDateRenamerGUI:
    """
    Basic GUI for date prefix file renaming without drag-and-drop.
    """
    
    def __init__(self):
        """Initialize the GUI application."""
        # Create main window
        self.root = tk.Tk()
        self.root.title("Date Prefix File Renamer")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        
        # Application state
        self.selected_directory = None
        self.is_processing = False
        self.file_items = {}  # Store file/folder items with selection state
        self.selected_items = set()  # Track selected items
        self.single_file_mode = False  # Whether we're processing a single file
        self.selected_single_file = None  # The single selected file
        
        # Create UI
        self._create_interface()
        self._center_window()
        
        print("Basic GUI initialized successfully!")
    
    def _create_interface(self):
        """Create the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Date Prefix File Renamer",
            font=('Helvetica', 18, 'bold')
        )
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_label = ttk.Label(
            main_frame,
            text="Add creation date prefixes to your files and folders automatically",
            font=('Helvetica', 10)
        )
        desc_label.pack(pady=(0, 30))
        
        # Directory selection area
        self._create_directory_section(main_frame)
        
        # File/folder selection tree (initially hidden)
        self._create_file_tree_section(main_frame)
        
        # Options
        self._create_options_section(main_frame)
        
        # Control buttons
        self._create_controls_section(main_frame)
        
        # Status bar
        self._create_status_section(main_frame)
    
    def _create_directory_section(self, parent):
        """Create directory selection section."""
        # Directory frame
        dir_frame = ttk.LabelFrame(parent, text="Directory Selection", padding="15")
        dir_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Selection area
        self.drop_frame = ttk.Frame(dir_frame, relief='solid', borderwidth=2, padding="30")
        self.drop_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Icon and text
        icon_label = ttk.Label(self.drop_frame, text="📁", font=('Helvetica', 36))
        icon_label.pack()
        
        self.drop_text_var = tk.StringVar(value="Click 'Select Directory' to choose a folder")
        drop_text = ttk.Label(
            self.drop_frame,
            textvariable=self.drop_text_var,
            font=('Helvetica', 12),
            justify=tk.CENTER
        )
        drop_text.pack(pady=(10, 0))
        
        # Selected directory display
        self.selected_dir_var = tk.StringVar()
        self.dir_display = ttk.Label(
            dir_frame,
            textvariable=self.selected_dir_var,
            font=('Helvetica', 10, 'italic'),
            foreground='blue'
        )
        self.dir_display.pack(pady=(10, 0))
    
    def _create_file_tree_section(self, parent):
        """Create file/folder selection tree section."""
        # Tree frame (initially hidden)
        self.tree_container = ttk.LabelFrame(parent, text="Select Files/Folders to Process", padding="15")
        # Don't pack yet - will be shown after directory selection
        
        # Toolbar
        toolbar = ttk.Frame(self.tree_container)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="Select All", command=self._select_all_items).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Deselect All", command=self._deselect_all_items).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Invert Selection", command=self._invert_selection).pack(side=tk.LEFT, padx=(0, 5))
        
        # Selection count label
        self.selection_count_var = tk.StringVar(value="0 items selected")
        ttk.Label(toolbar, textvariable=self.selection_count_var).pack(side=tk.RIGHT)
        
        # Help text
        help_text = ttk.Label(toolbar, text="💡 To select: Click item → Press ENTER or T", foreground='green')
        help_text.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Debug label (shows what was last clicked)
        self.debug_var = tk.StringVar(value="")
        self.debug_label = ttk.Label(toolbar, textvariable=self.debug_var, foreground='blue')
        self.debug_label.pack(side=tk.RIGHT, padx=(10, 10))
        
        # Tree frame with scrollbar
        tree_frame = ttk.Frame(self.tree_container)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        columns = ('Type', 'Size', 'Modified')
        self.file_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=12)
        
        # Configure columns
        self.file_tree.heading('#0', text='Name')
        self.file_tree.heading('Type', text='Type')
        self.file_tree.heading('Size', text='Size')
        self.file_tree.heading('Modified', text='Modified')
        
        self.file_tree.column('#0', width=300, minwidth=200)
        self.file_tree.column('Type', width=80, minwidth=60)
        self.file_tree.column('Size', width=100, minwidth=80)
        self.file_tree.column('Modified', width=150, minwidth=120)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.file_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Pack tree and scrollbars
        self.file_tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        
                # Bind click event for checkbox toggle
        self.file_tree.bind('<Button-1>', self._on_tree_click)
        self.file_tree.bind('<Double-Button-1>', self._on_tree_double_click)
        self.file_tree.bind('<KeyPress-space>', self._on_tree_space)
        
        # Add keyboard shortcuts that definitely work
        self.file_tree.bind('<Return>', self._on_tree_enter)  # Enter key to toggle
        self.file_tree.bind('<KeyPress-t>', self._on_tree_toggle_key)  # T key to toggle
        self.file_tree.bind('<Return>', self._on_tree_space)
        
        # Add right-click context menu
        # Right-click bindings removed for now
        
        # Create context menu
        self.context_menu = tk.Menu(self.file_tree, tearoff=0)
        self.context_menu.add_command(label="Toggle Selection", command=self._toggle_selected)
        self.context_menu.add_command(label="Select", command=self._select_item)
        self.context_menu.add_command(label="Deselect", command=self._deselect_item)
        
        print("Tree bindings configured")
    
    def _populate_file_tree(self):
        """Populate the file tree with files and folders from selected directory or single file."""
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        self.file_items.clear()
        self.selected_items.clear()
        
        if not self.selected_directory or not self.selected_directory.exists():
            return
        
        # Handle single file mode
        if self.single_file_mode and self.selected_single_file:
            self._populate_single_file()
            return
        
        # Get all files and folders
        try:
            items = []
            
            if self.recursive_var.get():
                # Recursive: get all items
                for item_path in sorted(self.selected_directory.rglob("*")):
                    if item_path != self.selected_directory:
                        items.append(item_path)
            else:
                # Non-recursive: only immediate children
                for item_path in sorted(self.selected_directory.iterdir()):
                    items.append(item_path)
            
            # Build tree structure
            parent_map = {}
            
            for item_path in items:
                # Get relative path
                try:
                    rel_path = item_path.relative_to(self.selected_directory)
                except ValueError:
                    continue
                
                # Determine parent
                parent_id = ''
                if len(rel_path.parts) > 1:
                    parent_rel = Path(*rel_path.parts[:-1])
                    parent_id = parent_map.get(str(parent_rel), '')
                
                # Get item info
                item_type = 'Folder' if item_path.is_dir() else 'File'
                
                try:
                    if item_path.is_file():
                        size = item_path.stat().st_size
                        size_str = self._format_size(size)
                    else:
                        size_str = ''
                    
                    modified = datetime.fromtimestamp(item_path.stat().st_mtime)
                    modified_str = modified.strftime('%Y-%m-%d %H:%M')
                except:
                    size_str = ''
                    modified_str = ''
                
                # Insert into tree with checkbox
                # Add icon to distinguish files from folders
                if item_type == 'Folder':
                    item_name = f"☐ 📁 {item_path.name}"
                else:
                    item_name = f"☐ 📄 {item_path.name}"
                    
                tree_id = self.file_tree.insert(
                    parent_id,
                    'end',
                    text=item_name,
                    values=(item_type, size_str, modified_str),
                    open=len(rel_path.parts) <= 2  # Open first two levels
                )
                
                # Store mapping
                self.file_items[tree_id] = {
                    'path': item_path,
                    'selected': False,
                    'type': item_type
                }
                
                parent_map[str(rel_path)] = tree_id
            
            # Update selection count
            self._update_selection_count()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load directory contents:\n{e}")
    
    def _populate_single_file(self):
        """Populate tree with just the selected single file."""
        file_path = self.selected_single_file
        
        # Get file info
        try:
            if file_path.is_file():
                size = file_path.stat().st_size
                size_str = self._format_size(size)
                item_type = 'File'
                icon = '📄'
            else:
                size_str = ''
                item_type = 'Folder' 
                icon = '📁'
            
            modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            modified_str = modified.strftime('%Y-%m-%d %H:%M')
        except:
            size_str = ''
            modified_str = ''
            item_type = 'File' if file_path.suffix else 'Folder'
            icon = '📄' if item_type == 'File' else '📁'
        
        # Insert single item into tree with checkbox (selected by default)
        display_text = f"☑ {icon} {file_path.name}"
        
        tree_id = self.file_tree.insert('', 'end', 
                                      text=display_text,
                                      values=(item_type, size_str, modified_str))
        
        # Store item data
        self.file_items[tree_id] = {
            'path': file_path,
            'type': item_type,
            'selected': True  # Auto-select the single file
        }
        
        # Update selection count
        self._update_selection_count()
    
    def _format_size(self, size):
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def _on_tree_click(self, event):
        """Handle tree item click for checkbox toggle."""
        # Get the item that was clicked
        item = self.file_tree.identify_row(event.y)
        
        # Enhanced debug output
        print(f"CLICK DEBUG: item='{item}', file_items keys: {list(self.file_items.keys())[:3]}...")
        self.debug_var.set(f"Click: item={item[:20] if item else 'None'}, in_items={item in self.file_items if item else 'N/A'}")
        
        if item:
            if item in self.file_items:
                # Toggle the item
                self._toggle_item(item)
                self.debug_var.set(f"SUCCESS: Toggled {item[:20]}...")
                return "break"  # Prevent default selection behavior
            else:
                self.debug_var.set(f"ERROR: Item '{item}' not found in file_items dict")
                print(f"ERROR: Item '{item}' not in file_items. Available keys: {list(self.file_items.keys())}")
        else:
            self.debug_var.set(f"ERROR: No item identified at click position")
    
    def _on_tree_double_click(self, event):
        """Handle double-click as an alternative toggle method."""
        item = self.file_tree.identify_row(event.y)
        if item:
            print(f"Double-click on item: {item}")
            self._toggle_item(item)
            return "break"
    
    def _on_tree_space(self, event):
        """Handle space key press to toggle selection."""
        selection = self.file_tree.selection()
        if selection:
            for item in selection:
                self._toggle_item(item)
    
    def _on_tree_enter(self, event):
        """Handle Enter key press to toggle selection."""
        selection = self.file_tree.selection()
        if selection:
            item = selection[0]
            self._toggle_item(item)
            self.debug_var.set(f"ENTER: Toggled {item[:20]}...")
            return "break"
    
    def _on_tree_toggle_key(self, event):
        """Handle T key press to toggle selection."""
        selection = self.file_tree.selection()
        if selection:
            item = selection[0]
            self._toggle_item(item)
            self.debug_var.set(f"T KEY: Toggled {item[:20]}...")
            return "break"
    
    def _toggle_selected(self):
        """Toggle selection for the currently selected tree item."""
        selection = self.file_tree.selection()
        if selection:
            for item in selection:
                self._toggle_item(item)
    
    def _select_item(self):
        """Select the currently selected tree item."""
        selection = self.file_tree.selection()
        if selection:
            for item in selection:
                if item in self.file_items:
                    self.file_items[item]['selected'] = True
                    # Update display
                    current_text = self.file_tree.item(item, 'text')
                    if current_text.startswith("☐"):
                        new_text = current_text.replace("☐", "☑", 1)
                        self.file_tree.item(item, text=new_text)
    
    def _deselect_item(self):
        """Deselect the currently selected tree item."""
        selection = self.file_tree.selection()
        if selection:
            for item in selection:
                if item in self.file_items:
                    self.file_items[item]['selected'] = False
                    # Update display
                    current_text = self.file_tree.item(item, 'text')
                    if current_text.startswith("☑"):
                        new_text = current_text.replace("☑", "☐", 1)
                        self.file_tree.item(item, text=new_text)
    
    def _toggle_item(self, item_id):
        """Toggle the selection state of an item."""
        if item_id not in self.file_items:
            self.debug_var.set(f"ERROR: Item {item_id[:20]}... not in file_items!")
            return
        
        item_data = self.file_items[item_id]
        item_data['selected'] = not item_data['selected']
        
        # Debug output
        item_type = item_data['type']
        item_path = item_data['path']
        self.debug_var.set(f"Toggled: {item_path.name} ({item_type}) → {'✓' if item_data['selected'] else '✗'}")
        
        # Update checkbox display
        current_text = self.file_tree.item(item_id, 'text')
        
        # Extract item name (remove checkbox and icon)
        # Format is either "☐ 📁 name" or "☐ 📄 name"
        parts = current_text.split(' ', 2)  # Split into at most 3 parts
        if len(parts) >= 3:
            icon = parts[1]  # 📁 or 📄
            item_name = parts[2]
        else:
            # Fallback if format is different
            icon = '📄' if item_type == 'File' else '📁'
            item_name = current_text[2:].strip()
        
        if item_data['selected']:
            new_text = f"☑ {icon} {item_name}"
            self.selected_items.add(item_id)
        else:
            new_text = f"☐ {icon} {item_name}"
            self.selected_items.discard(item_id)
        
        self.file_tree.item(item_id, text=new_text)
        self._update_selection_count()
    
    def _update_button_states(self):
        """Update the state of control buttons based on current selection."""
        if hasattr(self, 'process_button') and hasattr(self, 'clear_button'):
            # Enable process button if we have a directory/file selected and items to process
            has_selection = bool(self.selected_directory)
            has_items = len(self.file_items) > 0
            has_selected_items = len([item for item in self.file_items.values() if item.get('selected', False)]) > 0
            
            if has_selection and (has_selected_items or self.single_file_mode):
                self.process_button.configure(state='normal')
                self.clear_button.configure(state='normal')
            else:
                self.process_button.configure(state='disabled')
                self.clear_button.configure(state='disabled')
    
    def _select_all_items(self):
        """Select all items in the tree."""
        for item_id, item_data in self.file_items.items():
            if not item_data['selected']:
                item_data['selected'] = True
                current_text = self.file_tree.item(item_id, 'text')
                # Extract icon and name
                parts = current_text.split(' ', 2)
                if len(parts) >= 3:
                    icon = parts[1]
                    item_name = parts[2]
                else:
                    icon = '📄' if item_data['type'] == 'File' else '📁'
                    item_name = current_text[2:].strip()
                self.file_tree.item(item_id, text=f"☑ {icon} {item_name}")
                self.selected_items.add(item_id)
        
        self._update_selection_count()
    
    def _deselect_all_items(self):
        """Deselect all items in the tree."""
        for item_id, item_data in self.file_items.items():
            if item_data['selected']:
                item_data['selected'] = False
                current_text = self.file_tree.item(item_id, 'text')
                # Extract icon and name
                parts = current_text.split(' ', 2)
                if len(parts) >= 3:
                    icon = parts[1]
                    item_name = parts[2]
                else:
                    icon = '📄' if item_data['type'] == 'File' else '📁'
                    item_name = current_text[2:].strip()
                self.file_tree.item(item_id, text=f"☐ {icon} {item_name}")
                self.selected_items.discard(item_id)
        
        self._update_selection_count()
    
    def _invert_selection(self):
        """Invert the current selection."""
        for item_id, item_data in self.file_items.items():
            item_data['selected'] = not item_data['selected']
            current_text = self.file_tree.item(item_id, 'text')
            # Extract icon and name
            parts = current_text.split(' ', 2)
            if len(parts) >= 3:
                icon = parts[1]
                item_name = parts[2]
            else:
                icon = '📄' if item_data['type'] == 'File' else '📁'
                item_name = current_text[2:].strip()
            
            if item_data['selected']:
                self.file_tree.item(item_id, text=f"☑ {icon} {item_name}")
                self.selected_items.add(item_id)
            else:
                self.file_tree.item(item_id, text=f"☐ {icon} {item_name}")
                self.selected_items.discard(item_id)
        
        self._update_selection_count()
    
    def _update_selection_count(self):
        """Update the selection count label."""
        count = len(self.selected_items)
        self.selection_count_var.set(f"{count} item{'s' if count != 1 else ''} selected")
        
        # Enable/disable process button based on selection
        if hasattr(self, 'process_button'):
            if count > 0 and self.selected_directory:
                self.process_button.configure(state='normal')
            else:
                self.process_button.configure(state='disabled')
    
    def _create_options_section(self, parent):
        """Create options section."""
        options_frame = ttk.LabelFrame(parent, text="Options", padding="15")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Date format
        ttk.Label(options_frame, text="Date Format:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.date_format_var = tk.StringVar(value="YYYY-MM-DD")
        format_combo = ttk.Combobox(
            options_frame,
            textvariable=self.date_format_var,
            values=["YYYY-MM-DD", "YYYY_MM_DD", "MM-DD-YYYY", "DD-MM-YYYY"],
            state="readonly",
            width=15
        )
        format_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Processing options
        self.recursive_var = tk.BooleanVar(value=True)
        recursive_check = ttk.Checkbutton(
            options_frame,
            text="Process subdirectories recursively",
            variable=self.recursive_var,
            command=self._on_recursive_changed
        )
        recursive_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        self.dry_run_var = tk.BooleanVar(value=True)
        dry_run_check = ttk.Checkbutton(
            options_frame,
            text="Dry run (preview only, no actual changes)",
            variable=self.dry_run_var,
            command=self._update_process_button
        )
        dry_run_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Configure grid weights
        options_frame.columnconfigure(1, weight=1)
    
    def _create_controls_section(self, parent):
        """Create control buttons section."""
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Center buttons
        button_container = ttk.Frame(controls_frame)
        button_container.pack()
        
        # Select directory or file button
        self.select_button = ttk.Button(
            button_container,
            text="Select File/Folder...",
            command=self._select_file_or_folder
        )
        self.select_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Process button
        self.process_button = ttk.Button(
            button_container,
            text="Preview Changes",
            command=self._start_processing,
            state='disabled'
        )
        self.process_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        self.clear_button = ttk.Button(
            button_container,
            text="Clear",
            command=self._clear_selection,
            state='disabled'
        )
        self.clear_button.pack(side=tk.LEFT)
    
    def _create_status_section(self, parent):
        """Create status section."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready - Select a directory to begin")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        # Progress bar (hidden initially)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame,
            variable=self.progress_var,
            mode='determinate',
            length=200
        )
        # Don't pack initially
    
    def _select_file_or_folder(self):
        """Give user choice to select directory, single file, or multiple files."""
        # Create a simple dialog to ask what they want to select
        choice = messagebox.askyesnocancel(
            "Selection Type",
            "What would you like to select?\n\n"
            "• Yes: Select a folder (directory)\n"
            "• No: Select a single file\n"
            "• Cancel: Go back"
        )
        
        if choice is True:
            # Select directory
            directory = filedialog.askdirectory(
                title="Select Folder to Process",
                mustexist=True
            )
            if directory:
                self._set_selected_directory(Path(directory))
                
        elif choice is False:
            # Select single file
            file_path = filedialog.askopenfilename(
                title="Select Single File to Process",
                filetypes=[
                    ("All files", "*.*"),
                    ("Text files", "*.txt"),
                    ("Documents", "*.pdf *.doc *.docx"),
                    ("Images", "*.jpg *.jpeg *.png *.gif"),
                    ("Videos", "*.mp4 *.avi *.mov"),
                ]
            )
            if file_path:
                # Treat single file as if it's in its own directory
                file_path = Path(file_path)
                self._set_selected_file(file_path)
    
    def _select_directory(self):
        """Open directory selection dialog."""
        directory = filedialog.askdirectory(
            title="Select Directory to Process",
            mustexist=True
        )
        
        if directory:
            self._set_selected_directory(Path(directory))
    
    def _set_selected_file(self, file_path: Path):
        """Set a selected single file."""
        self.selected_directory = file_path.parent  # Set parent as directory
        self.single_file_mode = True
        self.selected_single_file = file_path
        
        # Update UI
        self._populate_file_tree()
        self._update_button_states()
    
    def _set_selected_directory(self, directory_path: Path):
        """Set the selected directory."""
        self.selected_directory = directory_path
        self.single_file_mode = False
        self.selected_single_file = None
        
        # Update UI
        self.selected_dir_var.set(f"Selected: {directory_path}")
        self.drop_text_var.set("Directory selected! Select individual files/folders below.")
        
        # Show and populate file tree
        self.tree_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        self._populate_file_tree()
        
        # Update button states
        self._update_button_states()
        
        # Process button will be enabled when items are selected
        
        # Update status
        self.status_var.set(f"Directory loaded: {directory_path.name} - Select items to process")
        
        print(f"Directory selected: {directory_path}")
    
    def _clear_selection(self):
        """Clear the selected directory."""
        self.selected_directory = None
        
        # Reset UI
        self.selected_dir_var.set("")
        self.drop_text_var.set("Click 'Select Directory' to choose a folder")
        
        # Hide tree
        if hasattr(self, 'tree_container'):
            self.tree_container.pack_forget()
        
        # Clear tree data
        self.file_items.clear()
        self.selected_items.clear()
        
        # Disable buttons
        self.process_button.configure(state='disabled')
        self.clear_button.configure(state='disabled')
        
        # Update status
        self.status_var.set("Ready - Select a directory to begin")
    
    def _update_process_button(self):
        """Update process button text based on dry run mode."""
        if hasattr(self, 'process_button'):
            if self.dry_run_var.get():
                self.process_button.configure(text="Preview Changes")
            else:
                self.process_button.configure(text="Rename Files")
    
    def _on_recursive_changed(self):
        """Handle recursive option change - refresh tree if directory is loaded."""
        if self.selected_directory and hasattr(self, 'file_tree'):
            self._populate_file_tree()
            self.status_var.set(f"Tree refreshed - {'Recursive' if self.recursive_var.get() else 'Non-recursive'} mode")
    
    def _start_processing(self):
        """Start file processing."""
        if not self.selected_directory:
            messagebox.showwarning("No Directory", "Please select a directory first.")
            return
        
        if len(self.selected_items) == 0:
            messagebox.showwarning("No Items Selected", "Please select at least one file or folder to process.")
            return
        
        if self.is_processing:
            messagebox.showwarning("Processing", "Processing is already in progress.")
            return
        
        # Show confirmation dialog
        is_dry_run = self.dry_run_var.get()
        mode_text = "preview (no changes will be made)" if is_dry_run else "rename"
        
        response = messagebox.askyesno(
            "Confirm Processing",
            f"This will {mode_text} {len(self.selected_items)} selected item(s) in:\n{self.selected_directory}\n\n"
            f"Date format: {self.date_format_var.get()}\n\n"
            "Continue?"
        )
        
        if not response:
            return
        
        # Start processing in background thread
        self.is_processing = True
        self.status_var.set("Processing selected items...")
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
        self.progress_bar.start()
        
        # Disable process button during processing
        self.process_button.configure(state='disabled')
        
        processing_thread = threading.Thread(
            target=self._process_files_async,
            daemon=True
        )
        processing_thread.start()
    
    def _process_files_async(self):
        """Process files in background thread."""
        try:
            # Get selected items from the tree (both files AND folders)
            items_to_process = []
            for item_id in self.selected_items:
                if item_id in self.file_items:
                    item_path = self.file_items[item_id]['path']
                    # Include both files and folders
                    if item_path.exists():
                        items_to_process.append(item_path)
            
            results = []
            total_items = len(items_to_process)
            processed = 0
            
            for item_path in items_to_process:
                try:
                    # Update progress
                    progress = (processed / total_items) * 100 if total_items > 0 else 0
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    
                    current_name = item_path.name
                    
                    # Skip if already has date prefix (basic check)
                    if self._has_date_prefix(current_name):
                        results.append({
                            'original': current_name,
                            'new': current_name,
                            'path': item_path,
                            'action': 'skipped',
                            'reason': 'Already has date prefix'
                        })
                        processed += 1
                        continue
                    
                    # Get item creation date
                    creation_time = datetime.fromtimestamp(item_path.stat().st_ctime)
                    date_format = self.date_format_var.get()
                    
                    if date_format == "YYYY-MM-DD":
                        date_prefix = creation_time.strftime("%Y-%m-%d")
                    elif date_format == "YYYY_MM_DD":
                        date_prefix = creation_time.strftime("%Y_%m_%d")
                    elif date_format == "MM-DD-YYYY":
                        date_prefix = creation_time.strftime("%m-%d-%Y")
                    else:  # DD-MM-YYYY
                        date_prefix = creation_time.strftime("%d-%m-%Y")
                    
                    new_name = f"{date_prefix}_{current_name}"
                    new_path = item_path.parent / new_name
                    
                    # Check if target already exists
                    if new_path.exists():
                        results.append({
                            'original': current_name,
                            'error': 'Target file already exists',
                            'path': item_path,
                            'action': 'error'
                        })
                    else:
                        # In dry run mode, just collect results
                        if self.dry_run_var.get():
                            results.append({
                                'original': current_name,
                                'new': new_name,
                                'path': item_path,
                                'action': 'preview'
                            })
                        else:
                            # Actually rename the item (file or folder)
                            item_path.rename(new_path)
                            results.append({
                                'original': current_name,
                                'new': new_name,
                                'path': new_path,
                                'action': 'renamed'
                            })
                
                except Exception as e:
                    results.append({
                        'original': item_path.name if item_path else 'Unknown',
                        'error': str(e),
                        'path': item_path,
                        'action': 'error'
                    })
                
                processed += 1
            
            # Final progress update
            self.root.after(0, lambda: self.progress_var.set(100))
            
            # Show results on main thread
            self.root.after(0, lambda: self._show_results(results))
            
        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))
        
        finally:
            self.is_processing = False
            self.root.after(0, self._processing_complete)
    
    def _has_date_prefix(self, filename):
        """Check if filename already has a date prefix."""
        if len(filename) < 8:
            return False
        
        # Check for common date patterns at the start
        prefix = filename[:10]
        
        # YYYY-MM-DD or YYYY_MM_DD
        if len(prefix) >= 10:
            date_part = prefix.replace('-', '').replace('_', '')
            if len(date_part) >= 8 and date_part[:8].isdigit():
                return True
        
        return False
    
    def _processing_complete(self):
        """Called when processing is complete."""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.process_button.configure(state='normal')
        self.status_var.set("Processing complete")
    
    def _show_results(self, results):
        """Show processing results."""
        # Create results window
        results_window = tk.Toplevel(self.root)
        results_window.title("Processing Results")
        results_window.geometry("800x500")
        results_window.transient(self.root)
        results_window.grab_set()
        
        # Center on parent
        self._center_dialog(results_window)
        
        # Results display
        main_frame = ttk.Frame(results_window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Summary
        successful = len([r for r in results if r.get('action') in ['preview', 'renamed']])
        errors = len([r for r in results if r.get('action') == 'error'])
        skipped = len([r for r in results if r.get('action') == 'skipped'])
        
        summary_text = f"Processing Summary:\n"
        summary_text += f"• Total files found: {len(results)}\n"
        summary_text += f"• Successfully processed: {successful}\n"
        summary_text += f"• Skipped (already prefixed): {skipped}\n"
        summary_text += f"• Errors: {errors}\n"
        
        if self.dry_run_var.get():
            summary_text += "\n(Preview mode - no actual changes were made)"
        
        summary_label = ttk.Label(main_frame, text=summary_text, font=('Helvetica', 11))
        summary_label.pack(pady=(0, 15))
        
        # Results list with notebook for different categories
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Successful operations tab
        if successful > 0:
            success_frame = ttk.Frame(notebook)
            notebook.add(success_frame, text=f"Processed ({successful})")
            self._create_results_tree(success_frame, 
                [r for r in results if r.get('action') in ['preview', 'renamed']])
        
        # Skipped items tab
        if skipped > 0:
            skipped_frame = ttk.Frame(notebook)
            notebook.add(skipped_frame, text=f"Skipped ({skipped})")
            self._create_results_tree(skipped_frame, 
                [r for r in results if r.get('action') == 'skipped'], show_reason=True)
        
        # Errors tab
        if errors > 0:
            error_frame = ttk.Frame(notebook)
            notebook.add(error_frame, text=f"Errors ({errors})")
            self._create_results_tree(error_frame, 
                [r for r in results if r.get('action') == 'error'], show_error=True)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Export button
        ttk.Button(
            button_frame,
            text="Export Results...",
            command=lambda: self._export_results(results)
        ).pack(side=tk.LEFT)
        
        # Close button
        ttk.Button(
            button_frame,
            text="Close",
            command=results_window.destroy
        ).pack(side=tk.RIGHT)
        
        # Update status
        if errors == 0:
            self.status_var.set(f"Successfully processed {successful} files")
        else:
            self.status_var.set(f"Processed {successful} files with {errors} errors")
    
    def _create_results_tree(self, parent, results, show_error=False, show_reason=False):
        """Create a treeview for results."""
        tree_frame = ttk.Frame(parent, padding="10")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        if show_error:
            columns = ('Original', 'Error', 'Path')
            headings = ('Original Name', 'Error Message', 'File Path')
        elif show_reason:
            columns = ('Original', 'Reason', 'Path')  
            headings = ('Original Name', 'Skip Reason', 'File Path')
        else:
            columns = ('Original', 'New Name', 'Path')
            headings = ('Original Name', 'New Name', 'File Path')
        
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
        
        # Configure columns and headings
        for col, heading in zip(columns, headings):
            tree.heading(col, text=heading)
            tree.column(col, width=200)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate results
        for result in results:
            if show_error:
                values = (
                    result.get('original', 'N/A'),
                    result.get('error', 'Unknown error'),
                    str(result.get('path', 'N/A'))
                )
            elif show_reason:
                values = (
                    result.get('original', 'N/A'),
                    result.get('reason', 'Unknown reason'),
                    str(result.get('path', 'N/A'))
                )
            else:
                values = (
                    result.get('original', 'N/A'),
                    result.get('new', 'N/A'),
                    str(result.get('path', 'N/A'))
                )
            
            tree.insert('', tk.END, values=values)
    
    def _export_results(self, results):
        """Export results to a file."""
        file_path = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("Date Prefix File Renamer - Processing Results\n")
                    f.write("=" * 50 + "\n\n")
                    
                    # Summary
                    successful = len([r for r in results if r.get('action') in ['preview', 'renamed']])
                    errors = len([r for r in results if r.get('action') == 'error'])
                    skipped = len([r for r in results if r.get('action') == 'skipped'])
                    
                    f.write("SUMMARY\n")
                    f.write("-" * 20 + "\n")
                    f.write(f"Total files found: {len(results)}\n")
                    f.write(f"Successfully processed: {successful}\n")
                    f.write(f"Skipped: {skipped}\n")
                    f.write(f"Errors: {errors}\n")
                    f.write(f"Processing mode: {'Dry Run' if self.dry_run_var.get() else 'Live Mode'}\n\n")
                    
                    # Detailed results
                    for result in results:
                        action = result.get('action', 'unknown')
                        original = result.get('original', 'N/A')
                        
                        if action in ['preview', 'renamed']:
                            new_name = result.get('new', 'N/A')
                            f.write(f"✓ {original} → {new_name}\n")
                        elif action == 'skipped':
                            reason = result.get('reason', 'No reason')
                            f.write(f"- {original} (Skipped: {reason})\n")
                        elif action == 'error':
                            error = result.get('error', 'Unknown error')
                            f.write(f"✗ {original} (Error: {error})\n")
                
                messagebox.showinfo(
                    "Export Complete",
                    f"Results exported successfully to:\n{file_path}"
                )
            
            except Exception as e:
                messagebox.showerror(
                    "Export Failed",
                    f"Failed to export results:\n{e}"
                )
    
    def _show_error(self, error_message):
        """Show error dialog."""
        messagebox.showerror("Processing Error", f"An error occurred:\n\n{error_message}")
        self.status_var.set("Processing failed")
    
    def _center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _center_dialog(self, dialog):
        """Center a dialog on the main window."""
        dialog.update_idletasks()
        
        # Get main window position and size
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        
        # Get dialog size
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()
        
        # Calculate centered position
        x = main_x + (main_width // 2) - (dialog_width // 2)
        y = main_y + (main_height // 2) - (dialog_height // 2)
        
        dialog.geometry(f'+{x}+{y}')
    
    def run(self):
        """Start the GUI application."""
        try:
            print("Starting GUI application...")
            self.root.protocol("WM_DELETE_WINDOW", self.root.quit)
            self.root.mainloop()
        except Exception as e:
            print(f"GUI error: {e}")
            messagebox.showerror("Application Error", f"Unexpected error: {e}")


def main():
    """Main entry point."""
    print("Date Prefix File Renamer - Basic GUI")
    print("=" * 40)
    
    # Check tkinter
    try:
        import tkinter
        print("✓ tkinter available")
    except ImportError:
        print("❌ tkinter not available")
        return 1
    
    print("✓ Basic GUI mode (no drag-and-drop)")
    
    # Launch GUI
    app = BasicDateRenamerGUI()
    app.run()
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())