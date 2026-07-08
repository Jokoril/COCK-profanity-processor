#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Null UI Provider
================

No-op implementation of UIProvider for headless operation or testing.

This module provides:
- Complete UIProvider implementation with no actual UI
- Safe defaults for all methods
- Useful for unit testing, CI environments, or server mode

Usage:
    from ui.null_provider import NullProvider

    provider = NullProvider()
    provider.show_notification(config)  # Does nothing

Version: 1.0.0
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

from logger import get_logger

from .interface import (
    UIProvider,
    NotificationConfig,
    MessageBoxConfig,
    TrayMenuConfig,
    SettingsDialogConfig,
    DetectionOverlayConfig,
)

log = get_logger(__name__)


class NullProvider(UIProvider):
    """No-op implementation of UIProvider

    All methods are safe to call but perform no actual UI operations.
    Useful for headless mode, testing, or when PyQt5 is not available.
    """

    def __init__(self):
        """Initialize the null provider"""
        log.debug("NullProvider initialized - UI operations will be no-ops")

    # =========================================================================
    # Application Lifecycle
    # =========================================================================

    def is_available(self) -> bool:
        """Always returns False - no UI available"""
        return False

    def create_app(self, argv: List[str]) -> Any:
        """No-op - returns None"""
        return None

    def run_event_loop(self) -> int:
        """No-op - returns success immediately"""
        return 0

    def quit(self) -> None:
        """No-op"""
        pass

    def schedule_callback(self, delay_ms: int, callback: Callable) -> None:
        """Execute callback immediately (no scheduling)

        For testing, callbacks are executed synchronously.

        Args:
            delay_ms: Ignored
            callback: Function to call immediately
        """
        # In null provider, we can optionally execute the callback
        # immediately for testing purposes, or skip entirely
        pass

    # =========================================================================
    # Notifications
    # =========================================================================

    def show_notification(self, config: NotificationConfig) -> None:
        """Log notification instead of showing

        Args:
            config: Notification configuration
        """
        log.debug(f"[NullProvider] Notification: {config.title} - {config.message}")

    def play_sound(self, sound_type: str) -> None:
        """No-op

        Args:
            sound_type: Ignored
        """
        pass

    # =========================================================================
    # Message Boxes
    # =========================================================================

    def show_message_box(self, config: MessageBoxConfig) -> str:
        """Return first button without showing dialog

        Args:
            config: Message box configuration

        Returns:
            First button label or 'OK'
        """
        log.debug(f"[NullProvider] MessageBox: {config.title} - {config.message}")
        return config.buttons[0] if config.buttons else 'OK'

    # =========================================================================
    # System Tray
    # =========================================================================

    def create_tray_icon(self, icon_path: str, tooltip: str) -> bool:
        """No-op - returns False

        Args:
            icon_path: Ignored
            tooltip: Ignored

        Returns:
            False (no tray icon created)
        """
        log.debug(f"[NullProvider] Tray icon request: {tooltip}")
        return False

    def update_tray_menu(self, config: TrayMenuConfig) -> None:
        """No-op

        Args:
            config: Ignored
        """
        pass

    def show_tray_message(
        self,
        title: str,
        message: str,
        icon_path: Optional[str] = None,
        duration_ms: int = 3000
    ) -> None:
        """Log message instead of showing

        Args:
            title: Message title
            message: Message content
            icon_path: Ignored
            duration_ms: Ignored
        """
        log.debug(f"[NullProvider] Tray message: {title} - {message}")

    def set_tray_activated_callback(self, callback: Callable) -> None:
        """No-op

        Args:
            callback: Ignored
        """
        pass

    # =========================================================================
    # Settings Dialog
    # =========================================================================

    def show_settings_dialog(self, config: SettingsDialogConfig) -> Any:
        """No-op - returns None

        Args:
            config: Ignored

        Returns:
            None
        """
        log.debug("[NullProvider] Settings dialog request")
        return None

    # =========================================================================
    # Detection Overlay
    # =========================================================================

    def show_detection_overlay(self, config: DetectionOverlayConfig) -> Any:
        """No-op - returns None

        Args:
            config: Ignored

        Returns:
            None
        """
        log.debug("[NullProvider] Detection overlay request")
        return None

    # =========================================================================
    # Utilities
    # =========================================================================

    def get_screen_size(self) -> Tuple[int, int]:
        """Return default screen size

        Returns:
            Default 1920x1080
        """
        return (1920, 1080)

    def set_app_icon(self, icon_path: str) -> None:
        """No-op

        Args:
            icon_path: Ignored
        """
        pass

    def set_app_name(self, name: str) -> None:
        """No-op

        Args:
            name: Ignored
        """
        pass


# =============================================================================
# Module Info
# =============================================================================
__version__ = '1.0.0'
__author__ = 'COCK Development Team'
