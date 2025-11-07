"""
Settings dialog for configuring application preferences.

This module provides a dialog for configuring all application settings
including date formats, processing options, and validation levels.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional

try:
    from ..models.enums import ValidationLevel, DateFormatStyle
except ImportError:
    # Handle direct execution - add parent to path
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    
    from models.enums import ValidationLevel, DateFormatStyle


class SettingsDialog:
    """
    Modal settings dialog for configuring application preferences.
    
    This dialog provides a comprehensive interface for configuring all
    application settings including date formats, processing modes,
    validation levels, and other preferences.
    
    Attributes:
        parent: Parent window
        current_settings: Current application settings
        dialog: The modal dialog window
        settings_vars: Tkinter variables for settings
        result_settings: Settings to return (None if cancelled)
    """
    
    def __init__(self, parent: tk.Tk, current_settings: Dict[str, Any]):
        """
        Initialize the settings dialog.
        
        Args:
            parent: Parent window
            current_settings: Current application settings dictionary
        """
        self.parent = parent
        self.current_settings = current_settings.copy()
        self.dialog = None
        self.settings_vars = {}
        self.result_settings = None
    
    def show(self) -> Optional[Dict[str, Any]]:
        """
        Show the settings dialog and return updated settings.
        
        Returns:
            Updated settings dictionary if OK was clicked, None if cancelled
        """
        # Create modal dialog
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Settings")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center on parent
        self._center_on_parent()
        
        # Create UI elements
        self._create_widgets()
        
        # Initialize values
        self._initialize_values()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Wait for dialog to close
        self.dialog.wait_window()
        
        return self.result_settings
    
    def _create_widgets(self):
        """Create the dialog widgets."""
        # Main container with notebook for categories
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for settings categories
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # General settings tab
        self._create_general_tab(notebook)
        
        # Processing settings tab
        self._create_processing_tab(notebook)
        
        # Advanced settings tab
        self._create_advanced_tab(notebook)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Reset to defaults button
        reset_button = ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults
        )
        reset_button.pack(side=tk.LEFT)
        
        # OK and Cancel buttons
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        )
        cancel_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        ok_button = ttk.Button(
            button_frame,
            text="OK",
            command=self._on_ok
        )
        ok_button.pack(side=tk.RIGHT)
    
    def _create_general_tab(self, notebook):
        """Create the general settings tab."""
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        
        container = ttk.Frame(general_frame, padding="20")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Date format settings
        date_frame = ttk.LabelFrame(container, text="Date Format", padding="15")
        date_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Date format selection
        ttk.Label(date_frame, text="Date format for file prefixes:").pack(anchor=tk.W, pady=(0, 5))
        
        self.settings_vars['date_format'] = tk.StringVar()
        
        # Create radio buttons for each date format
        for format_style in DateFormatStyle:
            radio = ttk.Radiobutton(
                date_frame,
                text=f"{format_style.example} ({format_style.description})",
                variable=self.settings_vars['date_format'],
                value=format_style.name
            )
            radio.pack(anchor=tk.W, pady=2)
        
        # Processing mode settings
        mode_frame = ttk.LabelFrame(container, text="Processing Mode", padding="15")
        mode_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.settings_vars['dry_run_mode'] = tk.BooleanVar()
        dry_run_check = ttk.Checkbutton(
            mode_frame,
            text="Dry Run Mode (Preview only, no actual changes)",
            variable=self.settings_vars['dry_run_mode']
        )
        dry_run_check.pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Label(
            mode_frame,
            text="When enabled, shows what would be renamed without making changes",
            font=('Helvetica', 9, 'italic'),
            foreground='gray'
        ).pack(anchor=tk.W)
        
        # Backup settings
        backup_frame = ttk.LabelFrame(container, text="Backup Options", padding="15")
        backup_frame.pack(fill=tk.X)
        
        self.settings_vars['create_backups'] = tk.BooleanVar()
        backup_check = ttk.Checkbutton(
            backup_frame,
            text="Create backup copies before renaming",
            variable=self.settings_vars['create_backups']
        )
        backup_check.pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Label(
            backup_frame,
            text="Creates .backup copies of files before renaming (recommended)",
            font=('Helvetica', 9, 'italic'),
            foreground='gray'
        ).pack(anchor=tk.W)
    
    def _create_processing_tab(self, notebook):
        """Create the processing settings tab."""
        processing_frame = ttk.Frame(notebook)
        notebook.add(processing_frame, text="Processing")
        
        container = ttk.Frame(processing_frame, padding="20")
        container.pack(fill=tk.BOTH, expand=True)
        
        # File scanning settings
        scanning_frame = ttk.LabelFrame(container, text="File Scanning", padding="15")
        scanning_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.settings_vars['recursive_processing'] = tk.BooleanVar()
        recursive_check = ttk.Checkbutton(
            scanning_frame,
            text="Process subdirectories recursively",
            variable=self.settings_vars['recursive_processing']
        )
        recursive_check.pack(anchor=tk.W, pady=(0, 10))
        
        self.settings_vars['include_hidden_files'] = tk.BooleanVar()
        hidden_check = ttk.Checkbutton(
            scanning_frame,
            text="Include hidden files and folders",
            variable=self.settings_vars['include_hidden_files']
        )
        hidden_check.pack(anchor=tk.W, pady=(0, 10))
        
        self.settings_vars['follow_symlinks'] = tk.BooleanVar()
        symlinks_check = ttk.Checkbutton(
            scanning_frame,
            text="Follow symbolic links",
            variable=self.settings_vars['follow_symlinks']
        )
        symlinks_check.pack(anchor=tk.W)
        
        ttk.Label(
            scanning_frame,
            text="⚠️ Following symlinks may cause infinite loops in recursive mode",
            font=('Helvetica', 9, 'italic'),
            foreground='orange'
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # Validation settings
        validation_frame = ttk.LabelFrame(container, text="Validation", padding="15")
        validation_frame.pack(fill=tk.X)
        
        ttk.Label(validation_frame, text="Validation level:").pack(anchor=tk.W, pady=(0, 5))
        
        self.settings_vars['validation_level'] = tk.StringVar()
        
        # Create radio buttons for validation levels
        validation_descriptions = {
            ValidationLevel.STRICT: "Strict - Maximum safety checks",
            ValidationLevel.NORMAL: "Normal - Standard validation",
            ValidationLevel.PERMISSIVE: "Permissive - Minimal checks"
        }
        
        for level in ValidationLevel:
            radio = ttk.Radiobutton(
                validation_frame,
                text=validation_descriptions[level],
                variable=self.settings_vars['validation_level'],
                value=level.name
            )
            radio.pack(anchor=tk.W, pady=2)
    
    def _create_advanced_tab(self, notebook):
        """Create the advanced settings tab."""
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced")
        
        container = ttk.Frame(advanced_frame, padding="20")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Interface settings
        interface_frame = ttk.LabelFrame(container, text="Interface", padding="15")
        interface_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.settings_vars['auto_close_results'] = tk.BooleanVar()
        auto_close_check = ttk.Checkbutton(
            interface_frame,
            text="Automatically close results dialog after successful processing",
            variable=self.settings_vars['auto_close_results']
        )
        auto_close_check.pack(anchor=tk.W, pady=(0, 10))
        
        self.settings_vars['show_skipped_items'] = tk.BooleanVar()
        show_skipped_check = ttk.Checkbutton(
            interface_frame,
            text="Show skipped items in results",
            variable=self.settings_vars['show_skipped_items']
        )
        show_skipped_check.pack(anchor=tk.W)
        
        # Theme settings (placeholder for future implementation)
        theme_frame = ttk.LabelFrame(container, text="Appearance", padding="15")
        theme_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(theme_frame, text="Theme:").pack(anchor=tk.W, pady=(0, 5))
        
        self.settings_vars['theme'] = tk.StringVar()
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.settings_vars['theme'],
            values=['Default', 'Dark', 'Light'],
            state='readonly',
            width=20
        )
        theme_combo.pack(anchor=tk.W)
        
        ttk.Label(
            theme_frame,
            text="Theme changes will take effect after restarting the application",
            font=('Helvetica', 9, 'italic'),
            foreground='gray'
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # Performance settings
        performance_frame = ttk.LabelFrame(container, text="Performance", padding="15")
        performance_frame.pack(fill=tk.X)
        
        ttk.Label(performance_frame, text="Max concurrent operations:").pack(anchor=tk.W, pady=(0, 5))
        
        self.settings_vars['max_concurrent'] = tk.IntVar()
        concurrent_spin = ttk.Spinbox(
            performance_frame,
            from_=1,
            to=10,
            textvariable=self.settings_vars['max_concurrent'],
            width=10
        )
        concurrent_spin.pack(anchor=tk.W)
        
        ttk.Label(
            performance_frame,
            text="Higher values may improve performance but use more system resources",
            font=('Helvetica', 9, 'italic'),
            foreground='gray'
        ).pack(anchor=tk.W, pady=(5, 0))
    
    def _initialize_values(self):
        """Initialize dialog values from current settings."""
        # Date format
        if 'date_format' in self.current_settings:
            format_style = self.current_settings['date_format']
            if hasattr(format_style, 'name'):
                self.settings_vars['date_format'].set(format_style.name)
            else:
                self.settings_vars['date_format'].set(DateFormatStyle.ISO_DATE.name)
        else:
            self.settings_vars['date_format'].set(DateFormatStyle.ISO_DATE.name)
        
        # Validation level
        if 'validation_level' in self.current_settings:
            level = self.current_settings['validation_level']
            if hasattr(level, 'name'):
                self.settings_vars['validation_level'].set(level.name)
            else:
                self.settings_vars['validation_level'].set(ValidationLevel.NORMAL.name)
        else:
            self.settings_vars['validation_level'].set(ValidationLevel.NORMAL.name)
        
        # Boolean settings
        boolean_settings = [
            'dry_run_mode', 'recursive_processing', 'include_hidden_files',
            'follow_symlinks', 'create_backups', 'auto_close_results', 'show_skipped_items'
        ]
        
        for setting in boolean_settings:
            if setting in self.settings_vars:
                value = self.current_settings.get(setting, False)
                self.settings_vars[setting].set(value)
        
        # String settings
        theme = self.current_settings.get('theme', 'default')
        if 'theme' in self.settings_vars:
            self.settings_vars['theme'].set(theme.title())
        
        # Integer settings
        max_concurrent = self.current_settings.get('max_concurrent', 4)
        if 'max_concurrent' in self.settings_vars:
            self.settings_vars['max_concurrent'].set(max_concurrent)
    
    def _reset_to_defaults(self):
        """Reset all settings to default values."""
        import tkinter.messagebox as messagebox
        
        response = messagebox.askyesno(
            "Reset Settings",
            "This will reset all settings to their default values. Continue?",
            parent=self.dialog
        )
        
        if response:
            # Default settings
            defaults = {
                'date_format': DateFormatStyle.ISO_DATE,
                'validation_level': ValidationLevel.NORMAL,
                'recursive_processing': True,
                'include_hidden_files': False,
                'follow_symlinks': False,
                'create_backups': False,
                'dry_run_mode': True,
                'auto_close_results': False,
                'show_skipped_items': True,
                'theme': 'default',
                'max_concurrent': 4
            }
            
            self.current_settings.update(defaults)
            self._initialize_values()
    
    def _on_ok(self):
        """Handle OK button click."""
        # Collect settings from dialog
        updated_settings = {}
        
        # Date format
        format_name = self.settings_vars['date_format'].get()
        updated_settings['date_format'] = getattr(DateFormatStyle, format_name)
        
        # Validation level
        level_name = self.settings_vars['validation_level'].get()
        updated_settings['validation_level'] = getattr(ValidationLevel, level_name)
        
        # Boolean settings
        boolean_settings = [
            'dry_run_mode', 'recursive_processing', 'include_hidden_files',
            'follow_symlinks', 'create_backups', 'auto_close_results', 'show_skipped_items'
        ]
        
        for setting in boolean_settings:
            if setting in self.settings_vars:
                updated_settings[setting] = self.settings_vars[setting].get()
        
        # String settings
        if 'theme' in self.settings_vars:
            updated_settings['theme'] = self.settings_vars['theme'].get().lower()
        
        # Integer settings
        if 'max_concurrent' in self.settings_vars:
            updated_settings['max_concurrent'] = self.settings_vars['max_concurrent'].get()
        
        # Validate settings
        validation_errors = self._validate_settings(updated_settings)
        if validation_errors:
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "Invalid Settings",
                "Please correct the following errors:\n\n" + "\n".join(validation_errors),
                parent=self.dialog
            )
            return
        
        self.result_settings = updated_settings
        self._close_dialog()
    
    def _on_cancel(self):
        """Handle Cancel button click."""
        self.result_settings = None
        self._close_dialog()
    
    def _validate_settings(self, settings: Dict[str, Any]) -> list:
        """
        Validate settings values.
        
        Args:
            settings: Settings dictionary to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate max concurrent operations
        if 'max_concurrent' in settings:
            max_concurrent = settings['max_concurrent']
            if not isinstance(max_concurrent, int) or max_concurrent < 1 or max_concurrent > 10:
                errors.append("Max concurrent operations must be between 1 and 10")
        
        # Validate symlinks + recursive combination
        if (settings.get('follow_symlinks', False) and 
            settings.get('recursive_processing', False)):
            import tkinter.messagebox as messagebox
            response = messagebox.askyesno(
                "Warning",
                "Following symbolic links in recursive mode may cause infinite loops. "
                "Are you sure you want to enable this combination?",
                parent=self.dialog
            )
            if not response:
                errors.append("Please disable either 'Follow symbolic links' or 'Recursive processing'")
        
        return errors
    
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
    
    def _close_dialog(self):
        """Close the dialog."""
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.grab_release()
            self.dialog.destroy()


# Example usage and testing
if __name__ == '__main__':
    def test_settings_dialog():
        """Test the settings dialog."""
        root = tk.Tk()
        root.title("Settings Dialog Test")
        root.geometry("400x200")
        
        # Sample settings
        current_settings = {
            'date_format': DateFormatStyle.ISO_DATE,
            'validation_level': ValidationLevel.NORMAL,
            'recursive_processing': True,
            'include_hidden_files': False,
            'follow_symlinks': False,
            'create_backups': True,
            'dry_run_mode': True,
            'auto_close_results': False,
            'show_skipped_items': True,
            'theme': 'default',
            'max_concurrent': 4
        }
        
        def show_settings():
            """Show the settings dialog."""
            dialog = SettingsDialog(root, current_settings)
            new_settings = dialog.show()
            
            if new_settings:
                print("New settings:", new_settings)
            else:
                print("Settings dialog was cancelled")
        
        # Test button
        test_button = ttk.Button(
            root,
            text="Open Settings Dialog",
            command=show_settings
        )
        test_button.pack(expand=True)
        
        root.mainloop()
    
    test_settings_dialog()