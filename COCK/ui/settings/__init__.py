#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COCK Settings UI
================
Settings dialog and tab components

Components:
- SettingsDialog: Main settings dialog coordinator
- Tab creation functions: Individual tab implementations
"""

from .general_tab import create_general_tab, validate_hotkeys
from .optimization_tab import create_optimization_tab
from .filter_tab import (
    create_filter_tab, load_filter_entries, update_filter_display,
    add_filter_entry, remove_filter_entries, export_filter_list
)
from .whitelist_tab import (
    create_whitelist_tab, load_whitelist_entries, update_whitelist_display,
    add_whitelist_entry, remove_whitelist_entries
)
from .ui_tab import create_ui_tab
from .about_tab import (
    create_about_tab, open_help, browse_filter_file, open_data_folder
)

__all__ = [
    # General tab
    'create_general_tab',
    'validate_hotkeys',
    # Optimization tab
    'create_optimization_tab',
    # Filter tab
    'create_filter_tab',
    'load_filter_entries',
    'update_filter_display',
    'add_filter_entry',
    'remove_filter_entries',
    'export_filter_list',
    # Whitelist tab
    'create_whitelist_tab',
    'load_whitelist_entries',
    'update_whitelist_display',
    'add_whitelist_entry',
    'remove_whitelist_entries',
    # UI tab
    'create_ui_tab',
    # About tab
    'create_about_tab',
    'open_help',
    'browse_filter_file',
    'open_data_folder',
]
__version__ = '1.0.0'
