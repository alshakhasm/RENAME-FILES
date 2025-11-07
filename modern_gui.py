"""
Modern Professional GUI for Date Prefix Renamer
Clean, modern design with proper styling
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
import os

# Try to import tkinterdnd2 for drag and drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
    print("✓ Drag and drop enabled")
except ImportError:
    DND_AVAILABLE = False
    print("⚠ Drag and drop not available (install tkinterdnd2 for this feature)")

class ModernDateRenamerGUI:
    def __init__(self):
        # Create root with drag and drop support if available
        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
            
        self.root.title("Date Prefix Renamer")
        self.root.geometry("650x500")
        self.root.configure(bg='#f0f0f0')
        
        # Configure modern style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure custom styles
        self._configure_styles()
        
        self.selected_paths = []  # Changed to support multiple files
        self.changes_previewed = False
        
        self._create_ui()
        
    def _configure_styles(self):
        """Configure modern styling"""
        # Main button style
        self.style.configure('Modern.TButton',
                           font=('Segoe UI', 10),
                           padding=(15, 8))
        
        # Action button style
        self.style.configure('Action.TButton',
                           font=('Segoe UI', 10, 'bold'),
                           padding=(20, 10))
        
        # Header style
        self.style.configure('Header.TLabel',
                           font=('Segoe UI', 18, 'bold'),
                           background='#f0f0f0')
        
        # Subheader style
        self.style.configure('Subheader.TLabel',
                           font=('Segoe UI', 11, 'bold'),
                           background='#f0f0f0')
        
        # Info style
        self.style.configure('Info.TLabel',
                           font=('Segoe UI', 9),
                           background='#f0f0f0',
                           foreground='#666666')
        
        # Frame style
        self.style.configure('Card.TFrame',
                           relief='solid',
                           borderwidth=1,
                           background='white')
        
    def _create_ui(self):
        # Main container
        main_container = tk.Frame(self.root, bg='#f0f0f0', padx=30, pady=25)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_container, bg='#f0f0f0')
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        title = ttk.Label(header_frame, text="Date Prefix Renamer", style='Header.TLabel')
        title.pack()
        
        subtitle = ttk.Label(header_frame, text="Add date prefixes to your files and folders", 
                           style='Info.TLabel')
        subtitle.pack(pady=(5, 0))
        
        # Selection Card
        selection_card = ttk.Frame(main_container, style='Card.TFrame', padding=20)
        selection_card.pack(fill=tk.X, pady=(0, 20))
        
        sel_label = ttk.Label(selection_card, text="Select Item", style='Subheader.TLabel')
        sel_label.pack(anchor='w', pady=(0, 10))
        
        # Selection display with drag and drop
        self.selection_frame = tk.Frame(selection_card, bg='#f8f9fa', relief='solid', 
                                      borderwidth=1, height=60)
        self.selection_frame.pack(fill=tk.X, pady=(0, 15))
        self.selection_frame.pack_propagate(False)
        
        if DND_AVAILABLE:
            drop_text = "Drag & drop multiple files/folders here or use buttons below"
        else:
            drop_text = "No items selected"
            
        self.selected_label = tk.Label(self.selection_frame, text=drop_text, 
                                     bg='#f8f9fa', fg='#6c757d', 
                                     font=('Segoe UI', 10))
        self.selected_label.pack(expand=True)
        
        # Enable drag and drop if available
        if DND_AVAILABLE:
            self.selection_frame.drop_target_register(DND_FILES)
            self.selection_frame.dnd_bind('<<Drop>>', self._on_drop)
            
            # Visual feedback for drag and drop
            self.selection_frame.bind('<Enter>', self._on_drag_enter)
            self.selection_frame.bind('<Leave>', self._on_drag_leave)
        
        # Selection buttons
        btn_frame = tk.Frame(selection_card, bg='white')
        btn_frame.pack(fill=tk.X)
        
        self.file_btn = ttk.Button(btn_frame, text="Select File", 
                                 command=self._select_file, style='Modern.TButton')
        self.file_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.folder_btn = ttk.Button(btn_frame, text="Select Folder", 
                                   command=self._select_folder, style='Modern.TButton')
        self.folder_btn.pack(side=tk.LEFT)
        
        # Preview Card
        preview_card = ttk.Frame(main_container, style='Card.TFrame', padding=20)
        preview_card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        prev_label = ttk.Label(preview_card, text="Preview Changes", style='Subheader.TLabel')
        prev_label.pack(anchor='w', pady=(0, 10))
        
        # Preview and Execute buttons side by side
        button_frame = tk.Frame(preview_card, bg='white')
        button_frame.pack(anchor='w', pady=(0, 15))
        
        self.preview_btn = ttk.Button(button_frame, text="Generate Preview", 
                                    command=self._preview_changes, 
                                    style='Modern.TButton', state='disabled')
        self.preview_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.execute_btn = ttk.Button(button_frame, text="Execute Changes", 
                                    command=self._execute_changes,
                                    style='Action.TButton', state='disabled')
        self.execute_btn.pack(side=tk.LEFT)
        
        # Preview text with modern styling
        preview_frame = tk.Frame(preview_card, bg='white')
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview_text = tk.Text(preview_frame, height=8, 
                                  font=('Consolas', 10), 
                                  bg='#f8f9fa', fg='#495057',
                                  relief='flat', padx=15, pady=15,
                                  state='disabled', wrap=tk.WORD)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, 
                                command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar.set)
        
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Reset button at bottom
        action_frame = tk.Frame(main_container, bg='#f0f0f0')
        action_frame.pack(fill=tk.X)
        
        self.reset_btn = ttk.Button(action_frame, text="Reset", 
                                  command=self._reset, style='Modern.TButton')
        self.reset_btn.pack(side=tk.RIGHT)
        
    def _select_file(self):
        """Select multiple files"""
        file_paths = filedialog.askopenfilenames(
            title="Select Files to Rename (hold Cmd for multiple)",
            filetypes=[
                ("All files", "*.*"),
                ("Documents", "*.pdf *.doc *.docx *.txt"),
                ("Images", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("Videos", "*.mp4 *.avi *.mov *.wmv")
            ]
        )
        if file_paths:
            self.selected_paths = [Path(fp) for fp in file_paths]
            self._update_selection_display()
            
    def _select_folder(self):
        """Select a folder"""
        folder_path = filedialog.askdirectory(title="Select Folder to Rename")
        if folder_path:
            self.selected_paths = [Path(folder_path)]
            self._update_selection_display()
            
    def _update_selection_display(self):
        """Update the selection display"""
        if self.selected_paths:
            count = len(self.selected_paths)
            
            if count == 1:
                path = self.selected_paths[0]
                name = path.name
                if len(name) > 50:
                    name = name[:47] + "..."
                
                icon = "📄" if path.is_file() else "📁"
                type_text = "File" if path.is_file() else "Folder"
                display_text = f"{icon} {name}\n{type_text} • {path.parent}"
            else:
                # Multiple items selected
                file_count = sum(1 for p in self.selected_paths if p.is_file())
                folder_count = count - file_count
                
                items = []
                if file_count > 0:
                    items.append(f"📄 {file_count} file{'s' if file_count != 1 else ''}")
                if folder_count > 0:
                    items.append(f"📁 {folder_count} folder{'s' if folder_count != 1 else ''}")
                
                display_text = f"Selected: {' and '.join(items)}\nTotal: {count} items"
            
            self.selected_label.config(text=display_text, fg='#212529')
            self.preview_btn.config(state='normal')
            self.changes_previewed = False
            self.execute_btn.config(state='disabled')
            
    def _preview_changes(self):
        """Show preview of changes for multiple files"""
        if not self.selected_paths:
            return
            
        self.preview_text.config(state='normal')
        self.preview_text.delete(1.0, tk.END)
        
        try:
            # Get current date
            today = datetime.now().strftime("%Y-%m-%d")
            
            preview_content = f"BATCH RENAME PREVIEW\n{'=' * 50}\n\n"
            preview_content += f"Date prefix: {today}\n"
            preview_content += f"Total items: {len(self.selected_paths)}\n\n"
            
            # Store rename plan
            self.rename_plan = []
            
            for i, path in enumerate(self.selected_paths, 1):
                old_name = path.name
                new_name = f"{today}_{old_name}"
                new_path = path.parent / new_name
                
                type_label = "📄" if path.is_file() else "📁"
                
                preview_content += f"#{i} {type_label} {path.parent.name}/\n"
                preview_content += f"  From: {old_name}\n"
                preview_content += f"  To:   {new_name}\n\n"
                
                self.rename_plan.append((path, new_path))
            
            preview_content += f"Status: Ready to execute {len(self.selected_paths)} renames"
            
            self.preview_text.insert(tk.END, preview_content)
            self.preview_text.config(state='disabled')
            
            self.changes_previewed = True
            self.execute_btn.config(state='normal')
            
        except Exception as e:
            self.preview_text.insert(tk.END, f"ERROR: {e}")
            self.preview_text.config(state='disabled')
            
    def _execute_changes(self):
        """Execute the batch rename operation"""
        if not self.changes_previewed:
            messagebox.showerror("Error", "Please generate a preview first!")
            return
            
        # Confirmation dialog
        count = len(self.rename_plan)
        result = messagebox.askyesno(
            "Confirm Batch Rename", 
            f"Are you sure you want to rename {count} item{'s' if count != 1 else ''}?\n\n"
            "This action cannot be undone!",
            icon='warning'
        )
        
        if not result:
            return
            
        try:
            success_count = 0
            errors = []
            
            for old_path, new_path in self.rename_plan:
                try:
                    if new_path.exists():
                        errors.append(f"Target already exists: {new_path.name}")
                        continue
                        
                    old_path.rename(new_path)
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Failed to rename {old_path.name}: {str(e)}")
            
            # Show results
            if success_count > 0 and not errors:
                messagebox.showinfo("Success", 
                                  f"Successfully renamed {success_count} item{'s' if success_count != 1 else ''}!")
                self._reset()
            elif success_count > 0 and errors:
                error_msg = "\n".join(errors[:5])  # Show first 5 errors
                if len(errors) > 5:
                    error_msg += f"\n... and {len(errors) - 5} more errors"
                
                messagebox.showwarning("Partial Success", 
                                     f"Renamed {success_count} of {count} items.\n\nErrors:\n{error_msg}")
                self._reset()
            else:
                error_msg = "\n".join(errors[:5])
                if len(errors) > 5:
                    error_msg += f"\n... and {len(errors) - 5} more errors"
                    
                messagebox.showerror("Failed", f"No items were renamed.\n\nErrors:\n{error_msg}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")
            
    def _on_drop(self, event):
        """Handle drag and drop of multiple files/folders"""
        if not DND_AVAILABLE:
            return
            
        # Get dropped files/folders
        files = self.root.tk.splitlist(event.data)
        if files:
            # Handle multiple files/folders
            valid_paths = []
            for file in files:
                path = Path(file)
                if path.exists():
                    valid_paths.append(path)
            
            if valid_paths:
                self.selected_paths = valid_paths
                self._update_selection_display()
                
    def _on_drag_enter(self, event):
        """Visual feedback when dragging over"""
        if DND_AVAILABLE:
            self.selection_frame.config(bg='#e3f2fd')
            self.selected_label.config(bg='#e3f2fd', fg='#1976d2')
            
    def _on_drag_leave(self, event):
        """Reset visual feedback when drag leaves"""
        if DND_AVAILABLE:
            self.selection_frame.config(bg='#f8f9fa')
            self.selected_label.config(bg='#f8f9fa', fg='#6c757d')
    
    def _reset(self):
        """Reset the interface"""
        self.selected_paths = []
        
        if DND_AVAILABLE:
            reset_text = "Drag & drop multiple files/folders here or use buttons below"
        else:
            reset_text = "No items selected"
            
        self.selected_label.config(text=reset_text, fg='#6c757d')
        self.selection_frame.config(bg='#f8f9fa')
        self.selected_label.config(bg='#f8f9fa')
        
        self.preview_btn.config(state='disabled')
        self.execute_btn.config(state='disabled')
        self.preview_text.config(state='normal')
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.config(state='disabled')
        self.changes_previewed = False
        
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    print("Modern Date Renamer GUI")
    print("======================")
    
    app = ModernDateRenamerGUI()
    app.run()