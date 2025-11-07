"""
Results dialog for displaying file processing results.

This module provides a dialog that shows the results of file processing
operations, including successful renames, errors, and statistics.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, Any
import webbrowser
from pathlib import Path

try:
    from ..models.result_models import ProcessingResult
except ImportError:
    # Handle direct execution - add parent to path
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    
    from models.result_models import ProcessingResult


class ResultsDialog:
    """
    Dialog for displaying processing results with detailed statistics and logs.
    
    This dialog shows comprehensive results of file processing operations,
    including success/failure counts, detailed logs, and options for
    further actions.
    
    Attributes:
        parent: Parent window
        result: Processing result data
        settings: Application settings used during processing
        dialog: The modal dialog window
    """
    
    def __init__(self, parent: tk.Tk, result: ProcessingResult, settings: Dict[str, Any]):
        """
        Initialize the results dialog.
        
        Args:
            parent: Parent window
            result: Processing result containing operation details
            settings: Settings used during processing
        """
        self.parent = parent
        self.result = result
        self.settings = settings
        self.dialog = None
    
    def show(self):
        """Show the results dialog."""
        # Create modal dialog
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Processing Results")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center on parent
        self._center_on_parent()
        
        # Create UI elements
        self._create_widgets()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_widgets(self):
        """Create the dialog widgets."""
        # Main container with notebook for tabs
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Summary tab
        self._create_summary_tab(notebook)
        
        # Successful operations tab
        if self.result.successful_renames:
            self._create_success_tab(notebook)
        
        # Failed operations tab
        if self.result.failed_operations:
            self._create_errors_tab(notebook)
        
        # Skipped items tab
        if hasattr(self.result, 'skipped_items') and self.result.skipped_items:
            self._create_skipped_tab(notebook)
        
        # Session log tab
        self._create_log_tab(notebook)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Action buttons
        if not self.settings['dry_run_mode'] and self.result.successful_renames:
            # Undo button (if not dry run and there were changes)
            undo_button = ttk.Button(
                button_frame,
                text="Undo Changes",
                command=self._undo_changes
            )
            undo_button.pack(side=tk.LEFT)
        
        # Export results button
        export_button = ttk.Button(
            button_frame,
            text="Export Results...",
            command=self._export_results
        )
        export_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # Process again button (if in dry run mode)
        if self.settings['dry_run_mode']:
            process_button = ttk.Button(
                button_frame,
                text="Apply Changes",
                command=self._apply_changes
            )
            process_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # Close button
        close_button = ttk.Button(
            button_frame,
            text="Close",
            command=self._on_close
        )
        close_button.pack(side=tk.RIGHT)
    
    def _create_summary_tab(self, notebook):
        """Create the summary tab with statistics."""
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Summary")
        
        # Main container with padding
        container = ttk.Frame(summary_frame, padding="20")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Header with status icon and title
        header_frame = ttk.Frame(container)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Status icon
        if self.result.success_rate == 100 and not self.result.failed_operations:
            status_icon = "✅"
            status_text = "Success"
            status_color = "green"
        elif self.result.failed_operations:
            status_icon = "⚠️"
            status_text = "Completed with Errors"
            status_color = "orange"
        else:
            status_icon = "ℹ️"
            status_text = "Completed"
            status_color = "blue"
        
        icon_label = ttk.Label(header_frame, text=status_icon, font=('Helvetica', 32))
        icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        title_label = ttk.Label(
            title_frame,
            text=status_text,
            font=('Helvetica', 18, 'bold')
        )
        title_label.pack(anchor=tk.W)
        
        mode_text = "Preview Mode (No Changes Made)" if self.settings['dry_run_mode'] else "Live Mode (Changes Applied)"
        mode_label = ttk.Label(
            title_frame,
            text=mode_text,
            font=('Helvetica', 12, 'italic')
        )
        mode_label.pack(anchor=tk.W)
        
        # Statistics grid
        stats_frame = ttk.LabelFrame(container, text="Statistics", padding="15")
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Configure grid
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)
        
        # Statistics data
        stats = [
            ("Total Items Processed", str(len(self.result.processed_items))),
            ("Successful Operations", str(len(self.result.successful_renames))),
            ("Failed Operations", str(len(self.result.failed_operations))),
            ("Success Rate", f"{self.result.success_rate:.1f}%")
        ]
        
        for i, (label, value) in enumerate(stats):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(stats_frame, text=f"{label}:", font=('Helvetica', 10, 'bold')).grid(
                row=row, column=col, sticky=tk.W, padx=(0, 5), pady=2
            )
            ttk.Label(stats_frame, text=value).grid(
                row=row, column=col+1, sticky=tk.W, pady=2
            )
        
        # Processing details
        details_frame = ttk.LabelFrame(container, text="Processing Details", padding="15")
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Session information
        session = self.result.session
        details_text = f"""Session ID: {session.session_id}
Target Directory: {session.target_directory}
Processing Mode: {'Dry Run' if session.is_dry_run else 'Live Processing'}
Recursive Processing: {'Yes' if session.recursive else 'No'}
Date Format: {session.date_format.name if session.date_format else 'Default'}

Started: {session.start_time.strftime('%Y-%m-%d %H:%M:%S') if session.start_time else 'N/A'}
Completed: {session.end_time.strftime('%Y-%m-%d %H:%M:%S') if session.end_time else 'N/A'}
Duration: {self._format_duration(session.duration) if session.duration else 'N/A'}
"""
        
        details_display = scrolledtext.ScrolledText(
            details_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.NORMAL
        )
        details_display.pack(fill=tk.BOTH, expand=True)
        details_display.insert(tk.END, details_text)
        details_display.configure(state=tk.DISABLED)
    
    def _create_success_tab(self, notebook):
        """Create the successful operations tab."""
        success_frame = ttk.Frame(notebook)
        notebook.add(success_frame, text=f"Successful ({len(self.result.successful_renames)})")
        
        container = ttk.Frame(success_frame, padding="10")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_label = ttk.Label(
            container,
            text="Successfully Processed Items",
            font=('Helvetica', 12, 'bold')
        )
        header_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Create treeview for successful operations
        columns = ('Original', 'New Name', 'Type')
        tree = ttk.Treeview(container, columns=columns, show='headings', height=15)
        
        # Configure columns
        tree.heading('Original', text='Original Name')
        tree.heading('New Name', text='New Name')
        tree.heading('Type', text='Type')
        
        tree.column('Original', width=300, anchor=tk.W)
        tree.column('New Name', width=300, anchor=tk.W)
        tree.column('Type', width=80, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate with data
        for operation in self.result.successful_renames:
            file_type = 'Folder' if operation.target_path.is_dir() else 'File'
            tree.insert('', tk.END, values=(
                operation.original_name,
                operation.new_name,
                file_type
            ))
    
    def _create_errors_tab(self, notebook):
        """Create the failed operations tab."""
        errors_frame = ttk.Frame(notebook)
        notebook.add(errors_frame, text=f"Errors ({len(self.result.failed_operations)})")
        
        container = ttk.Frame(errors_frame, padding="10")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_label = ttk.Label(
            container,
            text="Failed Operations",
            font=('Helvetica', 12, 'bold')
        )
        header_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Create treeview for failed operations
        columns = ('Item', 'Error', 'Type')
        tree = ttk.Treeview(container, columns=columns, show='headings', height=15)
        
        # Configure columns
        tree.heading('Item', text='Item Name')
        tree.heading('Error', text='Error Message')
        tree.heading('Type', text='Type')
        
        tree.column('Item', width=250, anchor=tk.W)
        tree.column('Error', width=400, anchor=tk.W)
        tree.column('Type', width=80, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate with data
        for operation in self.result.failed_operations:
            file_type = 'Folder' if operation.target_path.is_dir() else 'File'
            tree.insert('', tk.END, values=(
                operation.original_name,
                operation.error_message or 'Unknown error',
                file_type
            ))
    
    def _create_skipped_tab(self, notebook):
        """Create the skipped items tab."""
        skipped_frame = ttk.Frame(notebook)
        notebook.add(skipped_frame, text=f"Skipped ({len(self.result.skipped_items)})")
        
        container = ttk.Frame(skipped_frame, padding="10")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_label = ttk.Label(
            container,
            text="Skipped Items",
            font=('Helvetica', 12, 'bold')
        )
        header_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Explanation
        explanation_text = """Items were skipped for the following reasons:
• Already has date prefix
• Invalid characters in filename
• System or hidden files (if configured)
• Symbolic links (if not following symlinks)"""
        
        explanation_label = ttk.Label(container, text=explanation_text, justify=tk.LEFT)
        explanation_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Create treeview for skipped items
        columns = ('Item', 'Reason', 'Type')
        tree = ttk.Treeview(container, columns=columns, show='headings', height=12)
        
        # Configure columns
        tree.heading('Item', text='Item Name')
        tree.heading('Reason', text='Skip Reason')
        tree.heading('Type', text='Type')
        
        tree.column('Item', width=300, anchor=tk.W)
        tree.column('Reason', width=300, anchor=tk.W)
        tree.column('Type', width=80, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate with data
        for item in self.result.skipped_items:
            file_type = 'Folder' if item.is_directory else 'File'
            tree.insert('', tk.END, values=(
                item.name,
                item.skip_reason or 'Not specified',
                file_type
            ))
    
    def _create_log_tab(self, notebook):
        """Create the session log tab."""
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Log")
        
        container = ttk.Frame(log_frame, padding="10")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_label = ttk.Label(
            container,
            text="Session Log",
            font=('Helvetica', 12, 'bold')
        )
        header_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Log display
        log_display = scrolledtext.ScrolledText(
            container,
            wrap=tk.WORD,
            state=tk.NORMAL,
            font=('Consolas', 10)
        )
        log_display.pack(fill=tk.BOTH, expand=True)
        
        # Get session log entries
        session_log = self._get_session_log()
        log_display.insert(tk.END, session_log)
        log_display.configure(state=tk.DISABLED)
    
    def _get_session_log(self) -> str:
        """Get formatted session log entries."""
        if hasattr(self.result.session, 'log_entries') and self.result.session.log_entries:
            log_lines = []
            for entry in self.result.session.log_entries:
                timestamp = entry.timestamp.strftime('%H:%M:%S')
                log_lines.append(f"[{timestamp}] {entry.level}: {entry.message}")
            return '\n'.join(log_lines)
        else:
            return "No detailed log entries available for this session."
    
    def _format_duration(self, duration) -> str:
        """Format duration for display."""
        if hasattr(duration, 'total_seconds'):
            seconds = duration.total_seconds()
        else:
            seconds = float(duration)
        
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
    
    def _undo_changes(self):
        """Undo the changes made in this session."""
        # This would require implementing an undo mechanism
        # For now, show a placeholder dialog
        tk.messagebox.showinfo(
            "Undo Changes",
            "Undo functionality will be implemented in a future version.\n\n"
            "For now, you can manually revert changes by restoring from backups "
            "if backup creation was enabled.",
            parent=self.dialog
        )
    
    def _apply_changes(self):
        """Apply changes (convert from dry run to live mode)."""
        # Close this dialog and signal parent to run in live mode
        self._on_close()
        
        # This would need to be implemented in the main window
        # For now, show instruction dialog
        tk.messagebox.showinfo(
            "Apply Changes",
            "To apply these changes:\n\n"
            "1. Close this dialog\n"
            "2. Change settings to 'Live Mode'\n"
            "3. Process the directory again",
            parent=self.dialog
        )
    
    def _export_results(self):
        """Export results to a file."""
        from tkinter import filedialog
        
        # Ask for export file location
        file_path = filedialog.asksaveasfilename(
            parent=self.dialog,
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
                self._write_export_file(file_path)
                tk.messagebox.showinfo(
                    "Export Complete",
                    f"Results exported successfully to:\n{file_path}",
                    parent=self.dialog
                )
            except Exception as e:
                tk.messagebox.showerror(
                    "Export Failed",
                    f"Failed to export results:\n{e}",
                    parent=self.dialog
                )
    
    def _write_export_file(self, file_path: str):
        """Write results to export file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("Date Prefix File Renamer - Processing Results\n")
            f.write("=" * 50 + "\n\n")
            
            # Summary
            f.write("SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Items Processed: {len(self.result.processed_items)}\n")
            f.write(f"Successful Operations: {len(self.result.successful_renames)}\n")
            f.write(f"Failed Operations: {len(self.result.failed_operations)}\n")
            f.write(f"Success Rate: {self.result.success_rate:.1f}%\n")
            f.write(f"Processing Mode: {'Dry Run' if self.settings['dry_run_mode'] else 'Live Mode'}\n\n")
            
            # Successful operations
            if self.result.successful_renames:
                f.write("SUCCESSFUL OPERATIONS\n")
                f.write("-" * 30 + "\n")
                for op in self.result.successful_renames:
                    f.write(f"✓ {op.original_name} → {op.new_name}\n")
                f.write("\n")
            
            # Failed operations
            if self.result.failed_operations:
                f.write("FAILED OPERATIONS\n")
                f.write("-" * 25 + "\n")
                for op in self.result.failed_operations:
                    f.write(f"✗ {op.original_name}: {op.error_message}\n")
                f.write("\n")
            
            # Session log
            f.write("SESSION LOG\n")
            f.write("-" * 15 + "\n")
            f.write(self._get_session_log())
    
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
    
    def _on_close(self):
        """Handle dialog close."""
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.grab_release()
            self.dialog.destroy()


# Example usage and testing
if __name__ == '__main__':
    # This would normally be tested with actual ProcessingResult data
    pass