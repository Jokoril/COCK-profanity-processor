#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Path Manager Module
===================
Handles file paths for both development and .exe modes

Features:
- Detects if running as .exe or Python script
- Provides consistent paths across modes
- Handles PyInstaller _MEIPASS for bundled resources
- Works correctly when in cct/ package folder
"""

import sys
import os


def get_app_dir():
    """
    Get application directory
    
    Returns:
        str: Directory path where application files should be stored
        
    Behavior:
        - Development: Project root directory (parent of cct/ folder)
        - .exe: Directory containing the .exe file
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe
        # sys.executable is the path to the .exe
        return os.path.dirname(sys.executable)
    else:
        # Running as Python script
        # __file__ is cct/path_manager.py
        # Go up TWO levels to get to project root
        module_dir = os.path.dirname(os.path.abspath(__file__))  # cct/
        project_root = os.path.dirname(module_dir)                # project root
        return project_root


def get_data_file(filename):
    """
    Get full path to a data file in the application directory
    
    Args:
        filename (str): Name of the file (NO path separators allowed)
        
    Returns:
        str: Full absolute path to the file
        
    Raises:
        ValueError: If filename is invalid or contains path traversal attempts
    """
    # Security validation
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    # No path separators
    if '/' in filename or '\\' in filename:
        raise ValueError(f"Invalid filename: '{filename}' - path separators not allowed")
    
    # No parent references
    if '..' in filename:
        raise ValueError(f"Invalid filename: '{filename}' - parent directory references not allowed")
    
    # No absolute paths
    if os.path.isabs(filename):
        raise ValueError(f"Invalid filename: '{filename}' - absolute paths not allowed")
    
    # Build path
    base_dir = get_app_dir()
    full_path = os.path.join(base_dir, filename)
    
    # Double-check: Verify final path is within base_dir (defense in depth)
    abs_base = os.path.abspath(base_dir)
    abs_full = os.path.abspath(full_path)
    
    # Ensure path starts with base_dir + separator
    if not abs_full.startswith(abs_base + os.sep):
        raise ValueError(f"Path traversal detected: '{filename}'")
    
    return full_path


def get_bundled_resource(filename):
    """
    Get path to bundled resource
    
    Args:
        filename (str): Name of the bundled resource
        
    Returns:
        str: Full path to the resource
        
    Behavior:
        - .exe mode: PyInstaller extracts bundled files to temporary _MEIPASS folder
        - Development: Uses the project root directory
        
    Use this for:
        - Default config templates
        - Icon files
        - Other files bundled into the .exe
    """
    if getattr(sys, 'frozen', False):
        # Running as .exe - use PyInstaller's temporary extraction folder
        base_path = sys._MEIPASS
    else:
        # Running as script - use project root (not cct/ folder)
        base_path = get_app_dir()
    
    return os.path.join(base_path, filename)


def ensure_data_directory():
    """
    Ensure the application data directory exists
    
    Returns:
        str: Path to the data directory
        
    Note:
        Creates the directory if it doesn't exist
    """
    data_dir = get_app_dir()
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_default_filter_path():
    """
    Get the default filter file path
    
    Returns:
        str: Path to 'censored_words.txt' in the app directory
    """
    return get_data_file('censored_words.txt')


def file_exists(filename):
    """
    Check if a data file exists
    
    Args:
        filename (str): Name of the file to check
        
    Returns:
        bool: True if file exists, False otherwise
    """
    return os.path.isfile(get_data_file(filename))


def get_resource_file(filename):
    """
    Get path to resource file (with validation)
    
    Args:
        filename (str): Relative path within resources/ folder
                       (e.g., 'icons/icon.ico' or 'splash/splash_1.png')
    """
    # Security validation: Allow / for subdirectories but no ..
    if '..' in filename:
        raise ValueError(f"Invalid resource path: '{filename}' - parent references not allowed")
    
    # Convert to OS-specific path
    filename = filename.replace('/', os.sep)
    if getattr(sys, 'frozen', False):
        # Running as .exe - use PyInstaller's temporary extraction folder
        base_path = sys._MEIPASS
        return os.path.join(base_path, 'resources', filename)
    else:
        # Running as script - try different possible locations
        app_dir = get_app_dir()  # Now returns project root
        possible_paths = [
            os.path.join(app_dir, 'resources', filename),
            os.path.join(os.getcwd(), 'resources', filename),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Return first path as fallback (will fail gracefully in calling code)
        return possible_paths[0]


def validate_user_file_path(filepath: str, allowed_extensions: list = None) -> str:
    """
    Validate a user-provided file path for security

    This is more permissive than get_data_file() - allows subdirectories
    but still prevents traversal outside the app directory.

    Args:
        filepath: User-provided file path (relative or absolute)
        allowed_extensions: Optional list of allowed file extensions (e.g., ['.txt', '.json'])

    Returns:
        str: Validated absolute path

    Raises:
        ValueError: If path is unsafe or invalid

    Example:
        >>> validate_user_file_path("filters/game1.txt", ['.txt'])
        "Z:\\App\\filters\\game1.txt"
        >>> validate_user_file_path("../../../etc/passwd")
        ValueError: Path traversal attempt detected
    """
    if not filepath:
        raise ValueError("File path cannot be empty")

    # Get app directory as base
    app_dir = get_app_dir()

    # If path is absolute, check if it's within app directory
    if os.path.isabs(filepath):
        abs_path = os.path.abspath(filepath)
    else:
        # Relative path - join with app directory
        abs_path = os.path.abspath(os.path.join(app_dir, filepath))

    # Security check: Ensure final path is within app directory
    app_dir_normalized = os.path.abspath(app_dir) + os.sep
    abs_path_normalized = os.path.abspath(abs_path)

    # Check if path is within or equal to app directory
    if not (abs_path_normalized.startswith(app_dir_normalized) or abs_path_normalized == os.path.abspath(app_dir)):
        raise ValueError(f"Path traversal attempt detected: '{filepath}' resolves outside application directory")

    # Validate file extension if specified
    if allowed_extensions:
        _, ext = os.path.splitext(abs_path)
        if ext.lower() not in [e.lower() for e in allowed_extensions]:
            raise ValueError(f"Invalid file extension: '{ext}'. Allowed: {allowed_extensions}")

    return abs_path


def is_path_safe(filepath: str, base_dir: str = None) -> bool:
    """
    Check if a file path is safe (doesn't traverse outside base directory)

    Args:
        filepath: Path to check
        base_dir: Base directory to restrict to (defaults to app directory)

    Returns:
        bool: True if path is safe, False if traversal detected
    """
    if base_dir is None:
        base_dir = get_app_dir()

    try:
        validate_user_file_path(filepath)
        return True
    except ValueError:
        return False


# Module information
__version__ = '1.0.2'  # Added user file path validation for v1.0.1 security fixes
__author__ = 'Chat Censor Tool Team'
