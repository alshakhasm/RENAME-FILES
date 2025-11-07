"""
Progress dialog for displaying file processing progress.

This module provides a modal dialog that shows the progress of file processing
operations with cancellation support and detailed status updates.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
import threading


class ProgressDialog:
    """
    Modal progress dialog with cancellation support.
    
    This dialog displays the progress of file processing operations,
    including current phase, progress bar, item count, and status messages.
    
    Attributes:
        parent: Parent window
        on_cancel: Callback function for cancellation
        dialog: The modal dialog window
        is_cancelled: Whether the operation was cancelled
        progress_var: Variable for progress bar value
        status_vars: Variables for status text display
    """
    
    def __init__(self, parent: tk.Tk, on_cancel: Optional[Callable] = None):
        """
        Initialize the progress dialog.
        
        Args:
            parent: Parent window
            on_cancel: Optional callback function when cancelled
        """
        self.parent = parent
        self.on_cancel = on_cancel
        self.is_cancelled = False
        
        # Create modal dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Processing Files...")
        self.dialog.geometry("500x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center on parent
        self._center_on_parent()
        
        # Variables for progress tracking
        self.progress_var = tk.DoubleVar()
        self.phase_var = tk.StringVar(value="Initializing...")
        self.status_var = tk.StringVar(value="Starting file processing...")
        self.count_var = tk.StringVar(value="")
        self.current_file_var = tk.StringVar(value="")
        
        # Create UI elements
        self._create_widgets()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_widgets(self):
        """Create the dialog widgets."""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with icon and phase
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Processing icon
        icon_label = ttk.Label(header_frame, text="⚙️", font=('Helvetica', 24))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Phase text
        phase_label = ttk.Label(
            header_frame,
            textvariable=self.phase_var,
            font=('Helvetica', 14, 'bold')
        )
        phase_label.pack(side=tk.LEFT)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="15")
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Count display
        count_label = ttk.Label(progress_frame, textvariable=self.count_var)
        count_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Status message
        status_label = ttk.Label(
            progress_frame,
            textvariable=self.status_var,
            wraplength=450
        )
        status_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Current file being processed
        self.current_file_label = ttk.Label(
            progress_frame,
            textvariable=self.current_file_var,
            font=('Helvetica', 9, 'italic'),
            foreground='gray',
            wraplength=450
        )
        self.current_file_label.pack(anchor=tk.W)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Cancel button
        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        )
        self.cancel_button.pack(side=tk.RIGHT)
        
        # Close button (initially hidden)
        self.close_button = ttk.Button(
            button_frame,
            text="Close",
            command=self._on_close
        )
        # Don't pack initially - will be shown when processing completes
    
    def update_progress(self, phase: str, current: int, total: int, message: str = ""):
        """
        Update the progress display.
        
        Args:
            phase: Current processing phase
            current: Current item number
            total: Total number of items
            message: Optional status message
        """
        if self.is_cancelled or not self.dialog.winfo_exists():
            return
        
        try:
            # Update phase
            self.phase_var.set(phase)
            
            # Update progress bar
            if total > 0:
                progress_percent = (current / total) * 100
                self.progress_var.set(progress_percent)
            else:
                self.progress_var.set(0)
            
            # Update count
            if total > 0:
                self.count_var.set(f"Processing item {current} of {total}")
            else:
                self.count_var.set("")
            
            # Update status message
            if message:
                self.status_var.set(message)
                
                # If message looks like a file path, show it in current file
                if len(message) > 50 and ('/' in message or '\\' in message):
                    # Truncate long file paths for display
                    if len(message) > 60:
                        display_message = "..." + message[-57:]
                    else:
                        display_message = message
                    self.current_file_var.set(f"Current: {display_message}")
                else:
                    self.current_file_var.set("")
            
            # Force update
            self.dialog.update_idletasks()
            
        except tk.TclError:
            # Dialog may have been destroyed
            pass
    
    def set_indeterminate(self):
        """Set progress bar to indeterminate mode."""
        if not self.is_cancelled and self.dialog.winfo_exists():
            self.progress_bar.configure(mode='indeterminate')
            self.progress_bar.start()
    
    def set_determinate(self):
        """Set progress bar to determinate mode."""
        if not self.is_cancelled and self.dialog.winfo_exists():
            self.progress_bar.stop()
            self.progress_bar.configure(mode='determinate')
    
    def set_completed(self):
        """Mark the operation as completed."""
        if not self.is_cancelled and self.dialog.winfo_exists():
            self.phase_var.set("Completed")
            self.progress_var.set(100)
            self.status_var.set("Processing completed successfully")
            self.current_file_var.set("")
            
            # Show close button instead of cancel
            self.cancel_button.pack_forget()
            self.close_button.pack(side=tk.RIGHT)
    
    def set_error(self, error_message: str):
        """Mark the operation as failed with error."""
        if not self.is_cancelled and self.dialog.winfo_exists():
            self.phase_var.set("Error")
            self.status_var.set(f"Processing failed: {error_message}")
            self.current_file_var.set("")
            
            # Show close button instead of cancel
            self.cancel_button.pack_forget()
            self.close_button.pack(side=tk.RIGHT)
    
    def _on_cancel(self):
        """Handle cancel button click."""
        if not self.is_cancelled:
            self.is_cancelled = True
            self.phase_var.set("Cancelling...")
            self.status_var.set("Cancelling operation, please wait...")
            self.cancel_button.configure(state='disabled')
            
            # Call the cancel callback if provided
            if self.on_cancel:
                # Run callback in separate thread to avoid blocking UI
                cancel_thread = threading.Thread(target=self.on_cancel, daemon=True)
                cancel_thread.start()
    
    def _on_close(self):
        """Handle dialog close."""
        if not self.is_cancelled:
            # Ask for confirmation if operation is still running
            if self.phase_var.get() not in ["Completed", "Error", "Cancelled"]:
                import tkinter.messagebox as messagebox
                response = messagebox.askyesno(
                    "Cancel Processing",
                    "Processing is still in progress. Do you want to cancel?",
                    parent=self.dialog
                )
                if response:
                    self._on_cancel()
                return
        
        self.close()
    
    def close(self):
        """Close the dialog."""
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.grab_release()
            self.dialog.destroy()
    
    def _center_on_parent(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Calculate centered position
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        self.dialog.geometry(f'+{x}+{y}')


# Example usage and testing
if __name__ == '__main__':
    import time
    
    def test_progress_dialog():
        """Test the progress dialog with simulated processing."""
        root = tk.Tk()
        root.title("Progress Dialog Test")
        root.geometry("400x200")
        
        def simulate_processing():
            """Simulate a long-running process."""
            dialog = ProgressDialog(root)
            
            phases = [
                ("Scanning files", 20),
                ("Analyzing dates", 30),
                ("Validating names", 25),
                ("Renaming files", 25)
            ]
            
            current_item = 0
            for phase_name, phase_items in phases:
                for i in range(phase_items):
                    current_item += 1
                    dialog.update_progress(
                        phase_name,
                        current_item,
                        100,
                        f"Processing item {current_item}"
                    )
                    time.sleep(0.1)  # Simulate work
                    
                    if dialog.is_cancelled:
                        dialog.close()
                        return
            
            dialog.set_completed()
            root.after(2000, dialog.close)  # Auto-close after 2 seconds
        
        # Start button
        start_button = ttk.Button(
            root,
            text="Start Processing",
            command=lambda: threading.Thread(target=simulate_processing, daemon=True).start()
        )
        start_button.pack(expand=True)
        
        root.mainloop()
    
    test_progress_dialog()