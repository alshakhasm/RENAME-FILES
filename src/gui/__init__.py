"""
GUI package initialization for Date Prefix File Renamer.

This module provides the main entry point and initialization for the
graphical user interface components.
"""

from .main_window import MainWindow, main
from .progress_dialog import ProgressDialog
from .results_dialog import ResultsDialog
from .settings_dialog import SettingsDialog

__all__ = [
    'MainWindow',
    'ProgressDialog', 
    'ResultsDialog',
    'SettingsDialog',
    'main'
]

# Version info for GUI components
__version__ = '1.0.0'
__author__ = 'Date Prefix File Renamer Team'