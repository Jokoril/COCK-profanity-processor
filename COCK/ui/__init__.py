#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COCK UI Module
==============
User interface components for COCK Profanity Processor

Submodules:
- settings: Settings dialog and tab components
- widgets: Reusable UI widgets
- interface: Abstract UI provider interface
- pyqt5_provider: PyQt5 implementation
- null_provider: No-op implementation for headless/testing

Features (v1.1.0):
- UIProvider abstraction for framework-agnostic UI code
- PyQt5Provider for desktop GUI
- NullProvider for headless operation and testing
"""

from .widgets.hotkey_recorder import HotkeyRecorder

# UI Provider interface and data classes
from .interface import (
    UIProvider,
    NotificationConfig,
    MessageBoxConfig,
    TrayMenuItem,
    TrayMenuConfig,
    SettingsDialogConfig,
    DetectionOverlayConfig,
)

# Provider implementations
from .pyqt5_provider import PyQt5Provider
from .null_provider import NullProvider


def get_provider() -> UIProvider:
    """Get the appropriate UI provider based on availability

    Returns PyQt5Provider if PyQt5 is available, otherwise NullProvider.

    Returns:
        UIProvider instance
    """
    provider = PyQt5Provider()
    if provider.is_available():
        return provider
    return NullProvider()


__all__ = [
    # Widgets
    'HotkeyRecorder',
    # Interface
    'UIProvider',
    'NotificationConfig',
    'MessageBoxConfig',
    'TrayMenuItem',
    'TrayMenuConfig',
    'SettingsDialogConfig',
    'DetectionOverlayConfig',
    # Providers
    'PyQt5Provider',
    'NullProvider',
    'get_provider',
]

__version__ = '1.1.0'
