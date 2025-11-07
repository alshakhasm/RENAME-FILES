"""
Simplified GUI Application for Date Prefix File Renamer.

This is a standalone GUI application that can be launched directly
without complex relative import issues.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os
from pathlib import Path
import threading
from datetime import datetime

# Add src directory to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent if current_dir.name == 'gui' else current_dir / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DRAG_DROP_AVAILABLE = True
except ImportError:
    print("Warning: tkinterdnd2 not available. Drag-and-drop will be disabled.")
    DRAG_DROP_AVAILABLE = False


class SimpleDateRenamerGUI:
    """
    Simplified GUI for date prefix file renaming.
    
    This is a self-contained GUI that doesn't depend on the complex
    session management system, making it easier to test and run.
    """
    
    def __init__(self):
        """Initialize the GUI application."""
        # Create main window
        if DRAG_DROP_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
            
        self.root.title("Date Prefix File Renamer")
        self.root.geometry("700x500")
        self.root.minsize(600, 400)
        
        # Application state
        self.selected_directory = None
        self.is_processing = False
        
        # Create UI
        self._create_interface()
        self._center_window()
        
        print("Simple GUI initialized successfully!")
    
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
        
        # Drop zone or selection area
        self.drop_frame = ttk.Frame(dir_frame, relief='solid', borderwidth=2, padding="30")
        self.drop_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Icon and text
        icon_label = ttk.Label(self.drop_frame, text="📁", font=('Helvetica', 36))
        icon_label.pack()
        
        self.drop_text_var = tk.StringVar(value="Select a directory to process")
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
        
        # Setup drag and drop if available
        if DRAG_DROP_AVAILABLE:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self._handle_drop)
            self.drop_text_var.set("Drag a folder here or click 'Select Directory' below")
    
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
            variable=self.recursive_var
        )
        recursive_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        self.dry_run_var = tk.BooleanVar(value=True)
        dry_run_check = ttk.Checkbutton(
            options_frame,
            text="Dry run (preview only, no actual changes)",
            variable=self.dry_run_var
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
        
        # Select directory button
        self.select_button = ttk.Button(
            button_container,
            text="Select Directory...",
            command=self._select_directory
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
    
    def _handle_drop(self, event):
        """Handle files dropped onto the drop zone."""
        if not DRAG_DROP_AVAILABLE:
            return
            
        try:
            files = self.root.tk.splitlist(event.data)
            if files:
                dropped_path = Path(files[0])
                if dropped_path.exists() and dropped_path.is_dir():
                    self._set_selected_directory(dropped_path)
                else:
                    messagebox.showwarning("Invalid Selection", "Please drop a directory, not a file.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process dropped item: {e}")
    
    def _select_directory(self):
        """Open directory selection dialog."""
        directory = filedialog.askdirectory(
            title="Select Directory to Process",
            mustexist=True
        )
        
        if directory:
            self._set_selected_directory(Path(directory))
    
    def _set_selected_directory(self, directory_path: Path):
        """Set the selected directory."""
        self.selected_directory = directory_path
        
        # Update UI
        self.selected_dir_var.set(f"Selected: {directory_path}")
        self.drop_text_var.set("Directory selected! Click 'Preview Changes' to continue.")
        
        # Enable buttons
        self.process_button.configure(state='normal')
        self.clear_button.configure(state='normal')
        
        # Update button text based on dry run mode
        self._update_process_button()
        
        # Update status
        self.status_var.set(f"Directory selected: {directory_path.name}")
        
        print(f"Directory selected: {directory_path}")
    
    def _clear_selection(self):
        """Clear the selected directory."""
        self.selected_directory = None
        
        # Reset UI
        self.selected_dir_var.set("")
        if DRAG_DROP_AVAILABLE:
            self.drop_text_var.set("Drag a folder here or click 'Select Directory' below")
        else:
            self.drop_text_var.set("Click 'Select Directory' to choose a folder")
        
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
    
    def _start_processing(self):
        """Start file processing."""
        if not self.selected_directory:
            messagebox.showwarning("No Directory", "Please select a directory first.")
            return
        
        if self.is_processing:
            messagebox.showwarning("Processing", "Processing is already in progress.")
            return
        
        # Update button state
        self.dry_run_var.trace_add('write', lambda *args: self._update_process_button())
        
        # Show confirmation dialog
        is_dry_run = self.dry_run_var.get()
        mode_text = "preview (no changes will be made)" if is_dry_run else "rename files"
        
        response = messagebox.askyesno(
            "Confirm Processing",
            f"This will {mode_text} in:\n{self.selected_directory}\n\n"
            f"Recursive: {'Yes' if self.recursive_var.get() else 'No'}\n"
            f"Date format: {self.date_format_var.get()}\n\n"
            "Continue?"
        )
        
        if not response:
            return
        
        # Start processing in background thread
        self.is_processing = True
        self.status_var.set("Processing files...")
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
        self.progress_bar.start()
        
        processing_thread = threading.Thread(
            target=self._process_files_async,
            daemon=True
        )
        processing_thread.start()
    
    def _process_files_async(self):
        """Process files in background thread."""
        try:
            # Simulate processing for now
            import time
            
            # Get files to process
            files = list(self.selected_directory.rglob("*") if self.recursive_var.get() 
                        else self.selected_directory.iterdir())
            
            results = []
            processed = 0
            
            for file_path in files:
                if not file_path.is_file():
                    continue
                
                # Simulate processing time
                time.sleep(0.1)
                
                # Simple date prefix logic (placeholder)
                current_name = file_path.name
                
                # Skip if already has date prefix
                if current_name[:10].replace('-', '').replace('_', '').isdigit():
                    continue
                
                # Get file creation date
                try:
                    creation_time = datetime.fromtimestamp(file_path.stat().st_ctime)
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
                    
                    # In dry run mode, just collect results
                    if self.dry_run_var.get():
                        results.append({
                            'original': current_name,
                            'new': new_name,
                            'path': file_path,
                            'action': 'preview'
                        })
                    else:
                        # Actually rename the file
                        new_path = file_path.parent / new_name
                        if not new_path.exists():
                            file_path.rename(new_path)
                            results.append({
                                'original': current_name,
                                'new': new_name,
                                'path': new_path,
                                'action': 'renamed'
                            })
                
                except Exception as e:
                    results.append({
                        'original': current_name,
                        'error': str(e),
                        'path': file_path,
                        'action': 'error'
                    })
                
                processed += 1
                # Update progress (rough approximation)
                progress = min(90, (processed / len(files)) * 100)
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
            
            # Show results on main thread
            self.root.after(0, lambda: self._show_results(results))
            
        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))
        
        finally:
            self.is_processing = False
            self.root.after(0, self._processing_complete)
    
    def _processing_complete(self):
        """Called when processing is complete."""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_var.set("Processing complete")
    
    def _show_results(self, results):
        """Show processing results."""
        # Create results window
        results_window = tk.Toplevel(self.root)
        results_window.title("Processing Results")
        results_window.geometry("600x400")
        results_window.transient(self.root)
        
        # Results display
        main_frame = ttk.Frame(results_window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Summary
        successful = len([r for r in results if r.get('action') in ['preview', 'renamed']])
        errors = len([r for r in results if r.get('action') == 'error'])
        
        summary_text = f"Processing Summary:\n"
        summary_text += f"• Total files processed: {len(results)}\n"
        summary_text += f"• Successful operations: {successful}\n"
        summary_text += f"• Errors: {errors}\n"
        
        if self.dry_run_var.get():
            summary_text += "\n(Preview mode - no actual changes were made)"
        
        summary_label = ttk.Label(main_frame, text=summary_text, font=('Helvetica', 10))
        summary_label.pack(pady=(0, 15))
        
        # Results list
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for results
        columns = ('Original', 'New Name', 'Status')
        tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        tree.heading('Original', text='Original Name')
        tree.heading('New Name', text='New Name')
        tree.heading('Status', text='Status')
        
        tree.column('Original', width=200)
        tree.column('New Name', width=200)
        tree.column('Status', width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate results
        for result in results:
            if result.get('action') == 'error':
                tree.insert('', tk.END, values=(
                    result['original'],
                    result.get('error', 'Unknown error'),
                    'Error'
                ))
            else:
                tree.insert('', tk.END, values=(
                    result['original'],
                    result.get('new', 'N/A'),
                    'Preview' if self.dry_run_var.get() else 'Renamed'
                ))
        
        # Close button
        ttk.Button(
            main_frame,
            text="Close",
            command=results_window.destroy
        ).pack(pady=(15, 0))
        
        # Update status
        self.status_var.set(f"Processed {successful} files successfully")
    
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
    
    def run(self):
        """Start the GUI application."""
        try:
            print("Starting GUI application...")
            self.root.mainloop()
        except Exception as e:
            print(f"GUI error: {e}")
            messagebox.showerror("Application Error", f"Unexpected error: {e}")


def main():
    """Main entry point."""
    print("Date Prefix File Renamer - Simple GUI")
    print("=" * 40)
    
    # Check tkinter
    try:
        import tkinter
        print("✓ tkinter available")
    except ImportError:
        print("❌ tkinter not available")
        return 1
    
    # Check drag-drop (optional)
    if DRAG_DROP_AVAILABLE:
        print("✓ Drag-and-drop enabled")
    else:
        print("⚠️  Drag-and-drop disabled (tkinterdnd2 not available)")
    
    # Launch GUI
    app = SimpleDateRenamerGUI()
    app.run()
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())