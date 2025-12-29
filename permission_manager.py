#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Permission Manager Module
=========================
Handles platform-specific permission checks and admin rights

Features:
- Windows admin privilege detection
- Permission requirement validation
- Platform-specific UAC handling
"""

import sys
import os
import ctypes
from typing import Dict, Tuple


def is_admin():
    """
    Check if running with administrator privileges
    
    Returns:
        bool: True if running as admin, False otherwise
        
    Platform Support:
        - Windows: Uses ctypes to check admin status
        - Linux/macOS: Checks if effective UID is 0 (root)
    """
    try:
        if sys.platform == 'win32':
            # Windows: Check if user is admin
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # Unix-like: Check if running as root
            return os.geteuid() == 0
    except Exception:
        # If check fails, assume not admin
        return False


def request_admin_privileges():
    """
    Request administrator privileges (Windows only)
    
    Returns:
        bool: True if successfully elevated, False otherwise
        
    Behavior:
        - Windows: Attempts to restart the application with UAC prompt
        - Other platforms: Returns False (not implemented)
        
    Note:
        On Windows, this will restart the application if elevation is granted.
        The current process will exit.
    """
    if sys.platform != 'win32':
        return False
    
    if is_admin():
        # Already running as admin
        return True
    
    try:
        # Get the path to the current executable or script
        if getattr(sys, 'frozen', False):
            # Running as .exe
            exe_path = sys.executable
        else:
            # Running as script
            exe_path = sys.executable
            script_path = os.path.abspath(sys.argv[0])
        
        # Prepare parameters
        if getattr(sys, 'frozen', False):
            params = ' '.join(sys.argv[1:])
        else:
            params = f'"{script_path}" {" ".join(sys.argv[1:])}'
        
        # Request elevation via ShellExecute with 'runas'
        result = ctypes.windll.shell32.ShellExecuteW(
            None,           # hwnd
            "runas",        # operation (triggers UAC)
            exe_path,       # file
            params,         # parameters
            None,           # directory
            1               # show command (SW_SHOWNORMAL)
        )
        
        # If result > 32, elevation was granted and new process started
        if result > 32:
            # Exit current process (elevated version is now running)
            sys.exit(0)
        
        return False
        
    except Exception as e:
        print(f"Failed to request admin privileges: {e}")
        return False


def check_permissions() -> Dict[str, Tuple[bool, str]]:
    """
    Check all required permissions for the application
    
    Returns:
        dict: Dictionary of permission checks
            {
                'keyboard': (bool, str),  # (has_permission, message)
                'clipboard': (bool, str),
                'admin': (bool, str)
            }
    """
    results = {}
    
    # Keyboard access check
    try:
        import keyboard
        results['keyboard'] = (True, "Keyboard access available")
    except ImportError:
        results['keyboard'] = (False, "keyboard module not installed")
    except Exception as e:
        results['keyboard'] = (False, f"Keyboard access error: {e}")
    
    # Clipboard access check
    try:
        import pyperclip
        # Try to access clipboard
        pyperclip.paste()
        results['clipboard'] = (True, "Clipboard access available")
    except ImportError:
        results['clipboard'] = (False, "pyperclip module not installed")
    except Exception as e:
        results['clipboard'] = (False, f"Clipboard access error: {e}")
    
    # Admin privileges check (optional)
    admin_status = is_admin()
    if admin_status:
        results['admin'] = (True, "Running with administrator privileges")
    else:
        results['admin'] = (False, "Not running as administrator (optional)")
    
    return results


def get_permission_summary() -> str:
    """
    Get a formatted summary of all permission checks
    
    Returns:
        str: Multi-line string with permission status
    """
    checks = check_permissions()
    lines = ["Permission Status:"]
    lines.append("-" * 50)
    
    for permission, (status, message) in checks.items():
        symbol = "✓" if status else "✗"
        lines.append(f"{symbol} {permission.capitalize()}: {message}")
    
    return "\n".join(lines)


def requires_admin() -> bool:
    """
    Determine if the application requires admin privileges
    
    Returns:
        bool: True if admin is required, False otherwise
        
    Note:
        Currently returns False because admin is optional.
        Can be configured based on application needs.
    """
    # Admin is optional for this application
    # Keyboard library might need admin for global hotkeys in some cases
    return False


def can_run() -> Tuple[bool, str]:
    """
    Check if application can run with current permissions
    
    Returns:
        tuple: (can_run: bool, reason: str)
    """
    checks = check_permissions()
    
    # Required permissions
    required = ['keyboard', 'clipboard']
    
    for perm in required:
        if not checks.get(perm, (False, ""))[0]:
            return (False, f"Missing required permission: {perm}")
    
    return (True, "All required permissions available")


# Platform detection helpers
def is_windows():
    """Check if running on Windows"""
    return sys.platform == 'win32'


def is_macos():
    """Check if running on macOS"""
    return sys.platform == 'darwin'


def is_linux():
    """Check if running on Linux"""
    return sys.platform.startswith('linux')


def get_platform_name():
    """Get human-readable platform name"""
    if is_windows():
        return "Windows"
    elif is_macos():
        return "macOS"
    elif is_linux():
        return "Linux"
    else:
        return sys.platform


# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
