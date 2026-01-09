#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Input Validation Layer
======================
Centralized validation functions for all user inputs

Features:
- File path validation with security checks
- Configuration value validation with range checking
- Text input sanitization
- Special character whitelisting
- Hotkey format validation

All validators follow the pattern:
    validate_x(value, ...) -> (is_valid: bool, sanitized_value: Any, error_msg: str)

This allows callers to:
1. Check if input is valid
2. Get sanitized/default value if invalid
3. Get user-friendly error message for logging/display

Version: 1.0.0
Author: Chat Censor Tool Team
"""

import os
import re
from pathlib import Path
from typing import Tuple, Any, Optional, List, Set
from logger import get_logger

# Module logger
log = get_logger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

# Allowed special characters for interspacing
ALLOWED_SPECIAL_CHARS = {
    '❤', '★', '☆', '♥', '♡', '✓', '✔', '✗', '✘',
    '•', '●', '○', '◆', '◇', '■', '□', '▪', '▫',
    '~', '`', '|', '¦', '†', '‡', '°', '∙', '∘',
    '·', '※', '⁕', '⁜', '⁂', '⁎', '⁕', '◉', '◎'
}

# Dangerous characters (potential injection/control)
DANGEROUS_CHARS = {
    '`', ';', '|', '&', '$', '(', ')', '{', '}',
    '<', '>', '\n', '\r', '\t', '\0', '\\', '"', "'"
}

# ============================================================================
# EXCEPTION CLASSES
# ============================================================================

class ValidationError(Exception):
    """Raised when validation fails critically"""
    pass


# ============================================================================
# FILE PATH VALIDATORS
# ============================================================================

def validate_file_path(
    filepath: str,
    base_dir: Optional[str] = None,
    allowed_extensions: Optional[List[str]] = None,
    must_exist: bool = False,
    must_be_readable: bool = False
) -> Tuple[bool, str, str]:
    """
    Validate file path for security and existence

    Security checks:
    - No path traversal (../)
    - Must be within base_dir if specified
    - Validates extension if specified

    Args:
        filepath: Path to validate (relative or absolute)
        base_dir: Optional base directory to restrict to (default: app directory)
        allowed_extensions: Optional list of allowed extensions ['.txt', '.json']
        must_exist: If True, file must exist
        must_be_readable: If True, file must be readable

    Returns:
        (is_valid, sanitized_path, error_message)

    Example:
        >>> validate_file_path("filter.txt", must_exist=True, allowed_extensions=['.txt'])
        (True, "Z:\\App\\filter.txt", "")

        >>> validate_file_path("../../../etc/passwd")
        (False, "", "Path traversal detected")
    """
    if not filepath:
        return (False, "", "File path cannot be empty")

    try:
        # Get base directory
        if base_dir is None:
            import path_manager
            base_dir = path_manager.get_app_dir()

        # Convert to absolute path
        if os.path.isabs(filepath):
            abs_path = os.path.abspath(filepath)
        else:
            abs_path = os.path.abspath(os.path.join(base_dir, filepath))

        # Security: Check for path traversal
        base_dir_normalized = os.path.abspath(base_dir) + os.sep
        abs_path_normalized = os.path.abspath(abs_path)

        if not (abs_path_normalized.startswith(base_dir_normalized) or
                abs_path_normalized == os.path.abspath(base_dir)):
            return (False, "", f"Path traversal detected: '{filepath}' resolves outside application directory")

        # Validate extension if specified
        if allowed_extensions:
            _, ext = os.path.splitext(abs_path)
            if ext.lower() not in [e.lower() for e in allowed_extensions]:
                return (False, abs_path, f"Invalid file extension: '{ext}'. Allowed: {allowed_extensions}")

        # Check existence if required
        if must_exist and not os.path.exists(abs_path):
            return (False, abs_path, f"File does not exist: '{filepath}'")

        # Check readability if required
        if must_be_readable:
            if not os.path.exists(abs_path):
                return (False, abs_path, f"File does not exist: '{filepath}'")
            if not os.access(abs_path, os.R_OK):
                return (False, abs_path, f"File is not readable: '{filepath}'")

        return (True, abs_path, "")

    except Exception as e:
        log.debug(f"File path validation error: {e}")
        return (False, filepath, f"Invalid file path: {str(e)}")


def validate_filter_file(filepath: str, base_dir: Optional[str] = None) -> Tuple[bool, str, str]:
    """
    Validate filter file (must exist, readable, .txt extension, reasonable size)

    Args:
        filepath: Path to filter file
        base_dir: Optional base directory to restrict to (default: app directory)

    Returns:
        (is_valid, sanitized_path, error_message)

    Example:
        >>> validate_filter_file("filter.txt")
        (True, "Z:\\App\\filter.txt", "")
    """
    # First check path, existence, and extension
    is_valid, path, error = validate_file_path(
        filepath,
        base_dir=base_dir,
        allowed_extensions=['.txt'],
        must_exist=True,
        must_be_readable=True
    )

    if not is_valid:
        return (False, path, error)

    # Check file size (max 100MB)
    try:
        size = os.path.getsize(path)
        max_size = 100 * 1024 * 1024  # 100MB

        if size > max_size:
            return (False, path, f"Filter file too large: {size/1024/1024:.1f}MB (max 100MB)")

        if size == 0:
            return (False, path, "Filter file is empty")

        return (True, path, "")

    except Exception as e:
        return (False, path, f"Error checking filter file: {str(e)}")


# ============================================================================
# TEXT VALIDATORS
# ============================================================================

def validate_text_input(
    text: str,
    max_length: int = 10000,
    allow_empty: bool = False
) -> Tuple[bool, str, str]:
    """
    Validate user text input

    Checks:
    - Length within bounds
    - No null bytes
    - No other dangerous control characters

    Args:
        text: Text to validate
        max_length: Maximum allowed length
        allow_empty: Whether empty strings are valid

    Returns:
        (is_valid, sanitized_text, error_message)

    Example:
        >>> validate_text_input("Hello world")
        (True, "Hello world", "")

        >>> validate_text_input("x" * 20000, max_length=10000)
        (False, "x" * 10000, "Text too long: 20000 chars (max 10000)")
    """
    if not text:
        if allow_empty:
            return (True, "", "")
        else:
            return (False, "", "Text cannot be empty")

    # Check length
    if len(text) > max_length:
        truncated = text[:max_length]
        return (False, truncated, f"Text too long: {len(text)} chars (max {max_length})")

    # Check for null bytes
    if '\x00' in text:
        sanitized = text.replace('\x00', '')
        return (False, sanitized, "Text contains null bytes")

    # Check for dangerous control characters
    dangerous_found = []
    for char in ['\r', '\t']:
        if char in text:
            dangerous_found.append(repr(char))

    if dangerous_found:
        # Allow but warn
        log.warning(f"Text contains control characters: {', '.join(dangerous_found)}")

    return (True, text, "")


def validate_special_char(char: str) -> Tuple[bool, str, str]:
    """
    Validate special character for interspacing

    Rules:
    - Must be exactly 1 character
    - Must not be alphanumeric
    - Must not be control character
    - Must not be dangerous character
    - Preferably in ALLOWED_SPECIAL_CHARS whitelist

    Args:
        char: Character to validate

    Returns:
        (is_valid, sanitized_char, error_message)
        Default fallback: '❤'

    Example:
        >>> validate_special_char('❤')
        (True, '❤', "")

        >>> validate_special_char(';')
        (False, '❤', "Character ';' not allowed (potentially dangerous)")
    """
    default_char = '❤'

    if not char:
        return (False, default_char, "Special character cannot be empty")

    if len(char) != 1:
        return (False, default_char, f"Special character must be exactly 1 character (got {len(char)})")

    # Check if alphanumeric (not allowed)
    if char.isalnum():
        return (False, default_char, f"Special character '{char}' cannot be alphanumeric")

    # Check if control character (not allowed)
    code_point = ord(char)
    if code_point < 32 or code_point == 127:
        return (False, default_char, f"Special character cannot be control character (code {code_point})")

    # Check for dangerous characters
    if char in DANGEROUS_CHARS:
        return (False, default_char, f"Character '{char}' not allowed (potentially dangerous)")

    # Warn if not in whitelist (but still allow)
    if char not in ALLOWED_SPECIAL_CHARS:
        log.warning(f"Special character '{char}' not in whitelist, using anyway")

    return (True, char, "")


# ============================================================================
# CONFIG VALUE VALIDATORS
# ============================================================================

def validate_integer_range(
    value: Any,
    min_val: int,
    max_val: int,
    default: int,
    name: str
) -> Tuple[bool, int, str]:
    """
    Validate integer is within range

    Args:
        value: Value to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        default: Default value if invalid
        name: Name of parameter (for error messages)

    Returns:
        (is_valid, validated_value, error_message)

    Example:
        >>> validate_integer_range(3, 2, 5, 3, "window_size")
        (True, 3, "")

        >>> validate_integer_range(10, 2, 5, 3, "window_size")
        (False, 3, "window_size must be between 2 and 5")
    """
    try:
        val = int(value)

        if val < min_val:
            return (False, default, f"{name} must be at least {min_val} (got {val})")

        if val > max_val:
            return (False, default, f"{name} must be at most {max_val} (got {val})")

        return (True, val, "")

    except (ValueError, TypeError):
        return (False, default, f"{name} must be an integer (got {type(value).__name__})")


def validate_float_range(
    value: Any,
    min_val: float,
    max_val: float,
    default: float,
    name: str
) -> Tuple[bool, float, str]:
    """
    Validate float is within range

    Args:
        value: Value to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        default: Default value if invalid
        name: Name of parameter (for error messages)

    Returns:
        (is_valid, validated_value, error_message)

    Example:
        >>> validate_float_range(1.0, 0.5, 2.0, 1.0, "ui_scale")
        (True, 1.0, "")

        >>> validate_float_range(3.0, 0.5, 2.0, 1.0, "ui_scale")
        (False, 1.0, "ui_scale must be at most 2.0 (got 3.0)")
    """
    try:
        val = float(value)

        if val < min_val:
            return (False, default, f"{name} must be at least {min_val} (got {val})")

        if val > max_val:
            return (False, default, f"{name} must be at most {max_val} (got {val})")

        return (True, val, "")

    except (ValueError, TypeError):
        return (False, default, f"{name} must be a number (got {type(value).__name__})")


def validate_choice(
    value: Any,
    choices: List[Any],
    default: Any,
    name: str,
    case_sensitive: bool = True
) -> Tuple[bool, Any, str]:
    """
    Validate value is in allowed choices

    Args:
        value: Value to validate
        choices: List of allowed values
        default: Default value if invalid
        name: Name of parameter (for error messages)
        case_sensitive: Whether string comparison is case-sensitive

    Returns:
        (is_valid, validated_value, error_message)

    Example:
        >>> validate_choice("auto", ["auto", "manual"], "manual", "detection_mode")
        (True, "auto", "")

        >>> validate_choice("INVALID", ["auto", "manual"], "manual", "detection_mode")
        (False, "manual", "detection_mode must be one of ['auto', 'manual']")
    """
    # Case-insensitive comparison for strings
    if not case_sensitive and isinstance(value, str):
        value_lower = value.lower()
        choices_lower = [c.lower() if isinstance(c, str) else c for c in choices]

        if value_lower in choices_lower:
            # Find original case version
            idx = choices_lower.index(value_lower)
            return (True, choices[idx], "")
    else:
        if value in choices:
            return (True, value, "")

    return (False, default, f"{name} must be one of {choices} (got '{value}')")


# ============================================================================
# HOTKEY VALIDATORS
# ============================================================================

def validate_hotkey(hotkey: str) -> Tuple[bool, str, str]:
    """
    Validate hotkey string format

    Valid formats:
    - Single key: "f12", "a", "space"
    - With modifiers: "ctrl+f12", "shift+a", "ctrl+shift+s"

    Args:
        hotkey: Hotkey string to validate

    Returns:
        (is_valid, normalized_hotkey, error_message)
        Default fallback: 'f12'

    Example:
        >>> validate_hotkey("ctrl+f12")
        (True, "ctrl+f12", "")

        >>> validate_hotkey("invalid!@#")
        (False, "f12", "Invalid hotkey format")
    """
    default_hotkey = 'f12'

    if not hotkey:
        return (False, default_hotkey, "Hotkey cannot be empty")

    # Check length
    if len(hotkey) > 50:
        return (False, default_hotkey, "Hotkey string too long (max 50 chars)")

    # Normalize case
    hotkey_lower = hotkey.lower().strip()

    # Valid pattern: optional modifiers + key
    # Modifiers: ctrl, shift, alt, win
    # Key: a-z, 0-9, f1-f12, special names
    valid_modifiers = {'ctrl', 'shift', 'alt', 'win'}
    valid_special_keys = {
        'space', 'enter', 'tab', 'escape', 'esc',
        'backspace', 'delete', 'del', 'insert', 'ins',
        'home', 'end', 'pageup', 'pagedown', 'pgup', 'pgdn',
        'up', 'down', 'left', 'right',
        'f1', 'f2', 'f3', 'f4', 'f5', 'f6',
        'f7', 'f8', 'f9', 'f10', 'f11', 'f12'
    }

    # Split by +
    parts = hotkey_lower.split('+')

    if len(parts) == 0 or len(parts) > 4:
        return (False, default_hotkey, "Invalid hotkey format (too many parts)")

    # Check each part
    modifiers = []
    key = None

    for i, part in enumerate(parts):
        part = part.strip()

        if not part:
            return (False, default_hotkey, "Invalid hotkey format (empty part)")

        if i < len(parts) - 1:
            # Should be modifier
            if part not in valid_modifiers:
                return (False, default_hotkey, f"Invalid modifier: '{part}'")
            modifiers.append(part)
        else:
            # Last part is the key
            if part in valid_modifiers:
                # Modifier without key
                return (False, default_hotkey, "Hotkey must end with a key, not a modifier")

            # Check if valid key
            if len(part) == 1 and part.isalnum():
                # Single alphanumeric key
                key = part
            elif part in valid_special_keys:
                # Special key name
                key = part
            else:
                return (False, default_hotkey, f"Invalid key: '{part}'")

    # Reconstruct normalized hotkey
    if modifiers:
        normalized = '+'.join(modifiers) + '+' + key
    else:
        normalized = key

    return (True, normalized, "")


# ============================================================================
# MODULE INFORMATION
# ============================================================================

__version__ = '1.0.0'
__author__ = 'Chat Censor Tool Team'
