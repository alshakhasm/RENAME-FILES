"""
Main GUI window for the Date Prefix File Renamer application.

This module provides the primary tkinter-based graphical user interface with
drag-and-drop functionality, progress tracking, and results display.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
from pathlib import Path
from typing import Optional, List, Callable
import webbrowser
from datetime import datetime

try:
    from ..core.session import SessionManager, SessionFactory
    from ..models.enums import ValidationLevel, DateFormatStyle, SessionStatus
    from ..utils.logging import setup_logging, get_operation_logger
except ImportError:
    # Handle direct execution - add parent to path
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    
    from core.session import SessionManager, SessionFactory
    from models.enums import ValidationLevel, DateFormatStyle, SessionStatus
    from utils.logging import setup_logging, get_operation_logger
from .progress_dialog import ProgressDialog
from .results_dialog import ResultsDialog
from .settings_dialog import SettingsDialog


class MainWindow:
    """
    Main application window with drag-and-drop interface.
    
    This class provides the primary user interface for the Date Prefix File Renamer,
    including drag-and-drop zone, settings, progress tracking, and results display.
    
    Attributes:
        root: Main tkinter window
        session_manager: SessionManager for file operations
        current_settings: Application settings dictionary
        progress_dialog: Progress dialog window
        results_dialog: Results dialog window
        logger: Logger instance for GUI operations
    """
    
    def __init__(self):
        """Initialize the main GUI window."""
        # Initialize tkinter with drag-and-drop support
        self.root = TkinterDnD.Tk()
        self.root.title("Date Prefix File Renamer")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Initialize session manager
        self.session_manager = SessionFactory.create_default_session_manager()
        
        # Application state
        self.current_settings = self._get_default_settings()
        self.is_processing = False
        self.progress_dialog = None
        self.results_dialog = None
        
        # Setup logging for GUI
        setup_logging(console_output=False)  # GUI will handle log display
        self.logger = get_operation_logger(__name__)
        
        # Setup GUI components
        self._setup_styles()
        self._create_menu()
        self._create_main_interface()
        self._setup_drag_drop()
        
        # Center window on screen
        self._center_window()
        
        self.logger.info("GUI application initialized")
    
    def _get_default_settings(self) -> dict:
        """Get default application settings."""
        return {
            'date_format': DateFormatStyle.ISO_DATE,
            'validation_level': ValidationLevel.NORMAL,
            'recursive_processing': True,
            'include_hidden_files': False,
            'follow_symlinks': False,
            'create_backups': False,
            'dry_run_mode': True,  # Start in safe mode
            'auto_close_results': False,
            'show_skipped_items': True,
            'theme': 'default'
        }
    
    def _setup_styles(self):
        """Setup custom styles for the interface."""
        style = ttk.Style()
        
        # Configure custom styles
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Helvetica', 10))
        style.configure('DropZone.TFrame', relief='solid', borderwidth=2)
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
    
    def _create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Directory...", command=self._select_directory, accelerator="Cmd+O")
        file_menu.add_separator()
        file_menu.add_command(label="Clear History", command=self._clear_history)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self._quit_application, accelerator="Cmd+Q")
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences...", command=self._show_settings)
        settings_menu.add_separator()
        settings_menu.add_checkbutton(label="Dry Run Mode", variable=tk.BooleanVar(value=self.current_settings['dry_run_mode']))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self._show_help)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)
        
        # Keyboard bindings
        self.root.bind('<Command-o>', lambda e: self._select_directory())
        self.root.bind('<Command-q>', lambda e: self._quit_application())
        self.root.bind('<F1>', lambda e: self._show_help())
    
    def _create_main_interface(self):
        """Create the main user interface elements."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Header section
        self._create_header(main_frame)
        
        # Settings preview section
        self._create_settings_preview(main_frame)
        
        # Drag and drop zone
        self._create_drop_zone(main_frame)
        
        # Control buttons section
        self._create_controls(main_frame)
        
        # Status bar
        self._create_status_bar(main_frame)
    
    def _create_header(self, parent):
        """Create the header section with title and subtitle."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        header_frame.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="Date Prefix File Renamer",
            style='Title.TLabel'
        )
        title_label.grid(row=0, column=0)
        
        # Subtitle
        subtitle_label = ttk.Label(
            header_frame,
            text="Automatically add creation date prefixes to your files and folders",
            style='Subtitle.TLabel'
        )
        subtitle_label.grid(row=1, column=0, pady=(5, 0))
    
    def _create_settings_preview(self, parent):
        """Create a preview of current settings."""
        settings_frame = ttk.LabelFrame(parent, text="Current Settings", padding="10")
        settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        settings_frame.columnconfigure(1, weight=1)
        
        # Date format
        ttk.Label(settings_frame, text="Date Format:").grid(row=0, column=0, sticky=tk.W)
        self.format_var = tk.StringVar(value=self.current_settings['date_format'].example)
        ttk.Label(settings_frame, textvariable=self.format_var).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Processing mode
        ttk.Label(settings_frame, text="Mode:").grid(row=1, column=0, sticky=tk.W)
        self.mode_var = tk.StringVar(value="Dry Run (Safe Preview)" if self.current_settings['dry_run_mode'] else "Live Mode")
        mode_label = ttk.Label(settings_frame, textvariable=self.mode_var)
        mode_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Recursive processing
        ttk.Label(settings_frame, text="Recursive:").grid(row=2, column=0, sticky=tk.W)
        self.recursive_var = tk.StringVar(value="Yes" if self.current_settings['recursive_processing'] else "No")
        ttk.Label(settings_frame, textvariable=self.recursive_var).grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Settings button
        settings_button = ttk.Button(
            settings_frame,
            text="Change Settings...",
            command=self._show_settings
        )
        settings_button.grid(row=0, column=2, rowspan=3, padx=(20, 0))
    
    def _create_drop_zone(self, parent):
        """Create the drag-and-drop zone."""
        # Drop zone container
        drop_container = ttk.LabelFrame(parent, text="Drop Directory Here", padding="20")
        drop_container.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        drop_container.columnconfigure(0, weight=1)
        drop_container.rowconfigure(0, weight=1)
        
        # Drop zone frame
        self.drop_zone = ttk.Frame(drop_container, style='DropZone.TFrame', padding="40")
        self.drop_zone.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.drop_zone.columnconfigure(0, weight=1)
        self.drop_zone.rowconfigure(1, weight=1)
        
        # Drop zone icon (using text for now)
        icon_label = ttk.Label(
            self.drop_zone,
            text="📁",
            font=('Helvetica', 48)
        )
        icon_label.grid(row=0, column=0, pady=(0, 10))
        
        # Drop zone text
        self.drop_text_var = tk.StringVar(value="Drag a folder here to add date prefixes\n\nor click 'Select Directory' below")
        drop_text = ttk.Label(
            self.drop_zone,
            textvariable=self.drop_text_var,
            justify=tk.CENTER,
            font=('Helvetica', 12)
        )
        drop_text.grid(row=1, column=0)
        
        # Selected directory display
        self.selected_dir_var = tk.StringVar()
        self.selected_dir_label = ttk.Label(
            self.drop_zone,
            textvariable=self.selected_dir_var,
            font=('Helvetica', 10, 'italic'),
            foreground='gray'
        )
        self.selected_dir_label.grid(row=2, column=0, pady=(10, 0))
    
    def _create_controls(self, parent):
        """Create the control buttons section."""
        controls_frame = ttk.Frame(parent)
        controls_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Center the buttons
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(4, weight=1)
        
        # Select Directory button
        self.select_button = ttk.Button(
            controls_frame,
            text="Select Directory...",
            command=self._select_directory
        )
        self.select_button.grid(row=0, column=1, padx=(0, 10))
        
        # Process button
        self.process_button = ttk.Button(
            controls_frame,
            text="Preview Changes",
            command=self._start_processing,
            state='disabled'
        )
        self.process_button.grid(row=0, column=2, padx=(0, 10))
        
        # Clear button
        self.clear_button = ttk.Button(
            controls_frame,
            text="Clear",
            command=self._clear_selection,
            state='disabled'
        )
        self.clear_button.grid(row=0, column=3)
        
        # Update button text based on mode
        self._update_process_button_text()
    
    def _create_status_bar(self, parent):
        """Create the status bar at the bottom."""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)
        
        # Status text
        self.status_var = tk.StringVar(value="Ready - Select a directory to begin")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Progress bar (hidden by default)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame,
            variable=self.progress_var,
            mode='determinate'
        )
        # Don't grid the progress bar initially
    
    def _setup_drag_drop(self):
        """Setup drag-and-drop functionality."""
        # Register drop zone for file drops
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind('<<Drop>>', self._handle_drop)
        
        # Visual feedback for drag operations
        self.drop_zone.dnd_bind('<<DragEnter>>', self._on_drag_enter)
        self.drop_zone.dnd_bind('<<DragLeave>>', self._on_drag_leave)
    
    def _handle_drop(self, event):
        """Handle files dropped onto the drop zone."""
        try:
            # Get dropped files
            files = self.root.tk.splitlist(event.data)
            
            if not files:
                return
            
            # Take the first file/directory
            dropped_path = Path(files[0])
            
            # Validate that it's a directory
            if not dropped_path.exists():
                messagebox.showerror("Error", f"Path does not exist: {dropped_path}")
                return
            
            if not dropped_path.is_dir():
                messagebox.showwarning("Invalid Selection", "Please drop a directory, not a file.")
                return
            
            # Set the selected directory
            self._set_selected_directory(dropped_path)
            
        except Exception as e:
            self.logger.error(f"Error handling dropped files: {e}")
            messagebox.showerror("Error", f"Failed to process dropped item: {e}")
    
    def _on_drag_enter(self, event):
        """Visual feedback when drag enters the drop zone."""
        self.drop_zone.configure(style='DropZone.TFrame')
        self.drop_text_var.set("Release to select this directory")
    
    def _on_drag_leave(self, event):
        """Reset visual feedback when drag leaves the drop zone."""
        if not hasattr(self, 'selected_directory') or not self.selected_directory:
            self.drop_text_var.set("Drag a folder here to add date prefixes\n\nor click 'Select Directory' below")
    
    def _select_directory(self):
        """Open directory selection dialog."""
        directory = filedialog.askdirectory(
            title="Select Directory to Process",
            mustexist=True
        )
        
        if directory:
            self._set_selected_directory(Path(directory))
    
    def _set_selected_directory(self, directory_path: Path):
        """Set the selected directory and update UI."""
        self.selected_directory = directory_path
        
        # Update UI
        self.selected_dir_var.set(f"Selected: {directory_path}")
        self.drop_text_var.set("Directory selected!\n\nClick 'Preview Changes' to see what will be renamed")
        
        # Enable buttons
        self.process_button.configure(state='normal')
        self.clear_button.configure(state='normal')
        
        # Update status
        self.status_var.set(f"Directory selected: {directory_path.name}")
        
        self.logger.info(f"Directory selected: {directory_path}")
    
    def _clear_selection(self):
        """Clear the selected directory."""
        self.selected_directory = None
        
        # Reset UI
        self.selected_dir_var.set("")
        self.drop_text_var.set("Drag a folder here to add date prefixes\n\nor click 'Select Directory' below")
        
        # Disable buttons
        self.process_button.configure(state='disabled')
        self.clear_button.configure(state='disabled')
        
        # Update status
        self.status_var.set("Ready - Select a directory to begin")
        
        self.logger.info("Directory selection cleared")
    
    def _start_processing(self):
        """Start the file processing operation."""
        if not hasattr(self, 'selected_directory') or not self.selected_directory:
            messagebox.showwarning("No Directory", "Please select a directory first.")
            return
        
        if self.is_processing:
            messagebox.showwarning("Processing", "A processing operation is already in progress.")
            return
        
        # Show progress dialog
        self.progress_dialog = ProgressDialog(self.root, self._cancel_processing)
        
        # Start processing in background thread
        self.is_processing = True
        processing_thread = threading.Thread(
            target=self._process_directory_async,
            daemon=True
        )
        processing_thread.start()
    
    def _process_directory_async(self):
        """Process directory in background thread."""
        try:
            # Update session manager with current settings
            self._apply_settings_to_session_manager()
            
            # Create progress callback
            def progress_callback(phase: str, current: int, total: int, message: str):
                if self.progress_dialog:
                    self.root.after(0, lambda: self.progress_dialog.update_progress(
                        phase, current, total, message
                    ))
            
            # Run processing workflow
            result = self.session_manager.run_complete_workflow(
                target_directory=self.selected_directory,
                is_dry_run=self.current_settings['dry_run_mode'],
                recursive=self.current_settings['recursive_processing'],
                progress_callback=progress_callback
            )
            
            # Show results on main thread
            self.root.after(0, lambda: self._show_results(result))
            
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            self.root.after(0, lambda: self._show_error(str(e)))
        
        finally:
            self.is_processing = False
            if self.progress_dialog:
                self.root.after(0, lambda: self.progress_dialog.close())
    
    def _cancel_processing(self):
        """Cancel the current processing operation."""
        if self.session_manager.current_session:
            self.session_manager.cancel_current_session()
        
        self.is_processing = False
        self.status_var.set("Processing cancelled")
        self.logger.info("Processing cancelled by user")
    
    def _show_results(self, result):
        """Show processing results in a dialog."""
        self.results_dialog = ResultsDialog(self.root, result, self.current_settings)
        self.results_dialog.show()
        
        # Update status
        success_rate = result.success_rate
        if success_rate == 100:
            status_text = f"Completed successfully - {len(result.successful_renames)} items processed"
        else:
            status_text = f"Completed with {len(result.failed_operations)} errors - {success_rate:.1f}% success rate"
        
        self.status_var.set(status_text)
    
    def _show_error(self, error_message: str):
        """Show error dialog."""
        messagebox.showerror("Processing Error", f"An error occurred during processing:\n\n{error_message}")
        self.status_var.set("Processing failed")
    
    def _apply_settings_to_session_manager(self):
        """Apply current settings to the session manager."""
        # Update date extractor
        self.session_manager.date_extractor.default_style = self.current_settings['date_format']
        
        # Update file scanner
        self.session_manager.file_scanner.include_hidden = self.current_settings['include_hidden_files']
        self.session_manager.file_scanner.follow_symlinks = self.current_settings['follow_symlinks']
        
        # Update file renamer
        self.session_manager.file_renamer.create_backups = self.current_settings['create_backups']
        self.session_manager.file_renamer.dry_run_mode = self.current_settings['dry_run_mode']
        self.session_manager.file_renamer.validation_level = self.current_settings['validation_level']
    
    def _update_process_button_text(self):
        """Update the process button text based on current mode."""
        if hasattr(self, 'process_button'):
            if self.current_settings['dry_run_mode']:
                self.process_button.configure(text="Preview Changes")
            else:
                self.process_button.configure(text="Rename Files")
    
    def _show_settings(self):
        """Show the settings dialog."""
        settings_dialog = SettingsDialog(self.root, self.current_settings)
        new_settings = settings_dialog.show()
        
        if new_settings:
            self.current_settings.update(new_settings)
            self._update_settings_display()
            self._update_process_button_text()
            self.logger.info("Settings updated")
    
    def _update_settings_display(self):
        """Update the settings display in the main window."""
        self.format_var.set(self.current_settings['date_format'].example)
        self.mode_var.set("Dry Run (Safe Preview)" if self.current_settings['dry_run_mode'] else "Live Mode")
        self.recursive_var.set("Yes" if self.current_settings['recursive_processing'] else "No")
    
    def _clear_history(self):
        """Clear the session history."""
        self.session_manager.session_history.clear()
        messagebox.showinfo("History Cleared", "Session history has been cleared.")
    
    def _show_help(self):
        """Show help documentation."""
        help_text = """
Date Prefix File Renamer - User Guide

DRAG AND DROP:
• Drag any folder onto the drop zone
• The app will scan all files and folders inside
• Preview mode shows what will be renamed

SETTINGS:
• Date Format: Choose how dates appear (YYYY-MM-DD, MM-DD-YYYY, etc.)
• Mode: Dry Run (safe preview) vs Live Mode (actual renaming)
• Recursive: Process subfolders or just the main folder
• Backups: Create backup copies before renaming

KEYBOARD SHORTCUTS:
• Cmd+O: Select directory
• Cmd+Q: Quit application
• F1: Show this help

SAFETY FEATURES:
• Always start in Preview mode
• Skips files that already have date prefixes
• Comprehensive validation and error checking
• Optional backup creation
        """
        
        messagebox.showinfo("User Guide", help_text)
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts."""
        shortcuts_text = """
Keyboard Shortcuts:

Cmd+O    Select Directory
Cmd+Q    Quit Application
F1       Show Help
        """
        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text)
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """
Date Prefix File Renamer v1.0

A cross-platform application for automatically adding 
creation date prefixes to files and folders.

Features:
• Drag-and-drop interface
• Multiple date formats
• Safe preview mode
• Comprehensive validation
• Docker support

Built with Python and tkinter.
        """
        messagebox.showinfo("About", about_text)
    
    def _center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _quit_application(self):
        """Quit the application safely."""
        if self.is_processing:
            response = messagebox.askyesno(
                "Quit", 
                "A processing operation is in progress. Do you want to cancel it and quit?"
            )
            if response:
                self._cancel_processing()
            else:
                return
        
        self.logger.info("Application shutting down")
        self.session_manager.cleanup()
        self.root.quit()
    
    def run(self):
        """Start the GUI application."""
        try:
            self.logger.info("Starting GUI application")
            self.root.protocol("WM_DELETE_WINDOW", self._quit_application)
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"GUI application error: {e}")
            messagebox.showerror("Application Error", f"An unexpected error occurred: {e}")
        finally:
            if hasattr(self, 'session_manager'):
                self.session_manager.cleanup()


def main():
    """Main entry point for GUI application."""
    app = MainWindow()
    app.run()


if __name__ == '__main__':
    main()