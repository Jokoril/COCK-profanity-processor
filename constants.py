#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application Constants
=====================
Centralized constants for maintainability
"""

# ============================================================
# VALIDATION LIMITS
# ============================================================
MAX_FILTER_FILE_SIZE_MB = 100
MAX_FILTER_LINE_LENGTH = 1000
MAX_REASONABLE_MESSAGE_LENGTH = 500
MAX_CLIPBOARD_CAPTURE_LENGTH = 500

# ============================================================
# PERFORMANCE TARGETS
# ============================================================
TARGET_DETECTION_TIME_MS = 5
TARGET_FILTER_LOAD_TIME_MS = 500

# ============================================================
# UI DEFAULTS
# ============================================================
DEFAULT_NOTIFICATION_DURATION_MS = 3000
DEFAULT_OVERLAY_TIMEOUT_MS = 5000

# UI Scaling Factors
DEFAULT_FONT_SIZE = 9
TITLE_FONT_SIZE = 12
MIN_OVERLAY_WIDTH = 450
MAX_OVERLAY_WIDTH = 600
LAYOUT_SPACING = 12
LAYOUT_MARGIN = 16
LIST_MAX_HEIGHT = 150
LABEL_MAX_HEIGHT = 80
COPY_BUTTON_HEIGHT = 32
ACTION_BUTTON_HEIGHT = 40

# ============================================================
# FILE PATHS
# ============================================================
DEFAULT_CONFIG_FILENAME = 'config.json'
DEFAULT_WHITELIST_FILENAME = 'whitelist.txt'
DEFAULT_FILTER_FILENAME = 'filter_default.txt'

# ============================================================
# MESSAGE LIMITS
# ============================================================
DEFAULT_BYTE_LIMIT = 920
DEFAULT_CHARACTER_LIMIT = 800

# ============================================================
# OPTIMIZATION CHARACTERS
# ============================================================
HANGUL_ARAEA_CHAR = '\u119E'
DEFAULT_SPECIAL_CHAR = '\u2764'  # Heart emoji

# ============================================================
# DETECTION
# ============================================================
DEFAULT_SLIDING_WINDOW_MIN = 2
DEFAULT_SLIDING_WINDOW_MAX = 5
DEFAULT_SLIDING_WINDOW_DEFAULT = 3

# ============================================================
# CLIPBOARD SECURITY
# ============================================================
MAX_CLIPBOARD_SIZE = 1024 * 1024  # 1 MB
MAX_PASTE_SIZE = 100 * 1024  # 100 KB

# ============================================================
# TIMING (milliseconds)
# ============================================================
HOTKEY_DEBOUNCE_MS = 50
CLIPBOARD_CAPTURE_DELAY_MS = 50
MULTIPART_PASTE_DELAY_MS = 100
WINDOW_FOCUS_DELAY_MS = 100
OVERLAY_DELAY_MS = 100