#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Provider Interface
=====================

Abstract interface for UI operations, enabling framework-agnostic UI code.

This module provides:
- Data classes for UI configuration (notifications, menus, dialogs)
- Abstract UIProvider base class defining the UI contract
- Enables testability via mock/null providers
- Supports future framework migrations

Usage:
    from ui.interface import UIProvider, NotificationConfig

    # Get provider (PyQt5 or Null)
    provider = get_provider()

    # Show notification
    provider.show_notification(NotificationConfig(
        title="Success",
        message="Operation completed",
        notification_type='info'
    ))

Version: 1.0.0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class NotificationConfig:
    """Configuration for notification popups

    Attributes:
        title: Notification title text
        message: Notification body message
        notification_type: Type of notification ('clean', 'optimized', 'info', 'error')
        duration_ms: Auto-dismiss duration in milliseconds (0 = persistent)
        position: Screen position preset (e.g., 'bottom-right', 'center')
        scale: UI scale factor for notification size
        offset_x: Horizontal offset from edge
        offset_y: Vertical offset from edge
        theme: Visual theme ('dark' or 'light')
    """
    title: str
    message: str
    notification_type: str = 'info'
    duration_ms: int = 3000
    position: str = 'bottom-right'
    scale: float = 1.0
    offset_x: int = 20
    offset_y: int = 20
    theme: str = 'dark'


@dataclass
class MessageBoxConfig:
    """Configuration for message box dialogs

    Attributes:
        title: Dialog title
        message: Dialog message content
        box_type: Type of dialog ('info', 'warning', 'error', 'question')
        buttons: List of button labels (e.g., ['OK'], ['Yes', 'No', 'Cancel'])
    """
    title: str
    message: str
    box_type: str = 'info'
    buttons: List[str] = field(default_factory=lambda: ['OK'])


@dataclass
class TrayMenuItem:
    """Single tray menu item

    Attributes:
        label: Display text for menu item
        callback: Function to call when item is clicked
        checkable: Whether item shows a checkbox
        checked: Initial checked state (if checkable)
        separator: If True, this is a separator (label/callback ignored)
        submenu: Optional list of child menu items
    """
    label: str = ''
    callback: Optional[Callable] = None
    checkable: bool = False
    checked: bool = False
    separator: bool = False
    submenu: List['TrayMenuItem'] = field(default_factory=list)


@dataclass
class TrayMenuConfig:
    """Configuration for system tray menu

    Attributes:
        items: List of menu items
    """
    items: List[TrayMenuItem] = field(default_factory=list)


@dataclass
class SettingsDialogConfig:
    """Configuration for settings dialog

    Attributes:
        config: Current application configuration dict
        filter_stats: Filter loading statistics dict
        callbacks: Dict of callback functions for dialog events
    """
    config: Dict[str, Any] = field(default_factory=dict)
    filter_stats: Dict[str, Any] = field(default_factory=dict)
    callbacks: Dict[str, Callable] = field(default_factory=dict)


@dataclass
class DetectionOverlayConfig:
    """Configuration for detection result overlay

    Attributes:
        detection_result: Dict containing detected words and suggestions
        callbacks: Dict of callback functions (use_suggestion, cancelled)
    """
    detection_result: Dict[str, Any] = field(default_factory=dict)
    callbacks: Dict[str, Callable] = field(default_factory=dict)


class UIProvider(ABC):
    """Abstract base class for UI providers

    Defines the contract for all UI operations. Implementations can use
    PyQt5, Tkinter, curses, or provide no-op behavior for headless mode.

    All methods that interact with the UI should be called from the main thread.
    """

    # =========================================================================
    # Application Lifecycle
    # =========================================================================

    @abstractmethod
    def is_available(self) -> bool:
        """Check if UI framework is available

        Returns:
            True if UI framework is loaded and functional
        """
        pass

    @abstractmethod
    def create_app(self, argv: List[str]) -> Any:
        """Create the application instance

        Args:
            argv: Command line arguments

        Returns:
            Application instance (framework-specific)
        """
        pass

    @abstractmethod
    def run_event_loop(self) -> int:
        """Run the main event loop

        Returns:
            Exit code (0 for success)
        """
        pass

    @abstractmethod
    def quit(self) -> None:
        """Quit the application gracefully"""
        pass

    @abstractmethod
    def schedule_callback(self, delay_ms: int, callback: Callable) -> None:
        """Schedule a callback to run after delay

        Args:
            delay_ms: Delay in milliseconds
            callback: Function to call
        """
        pass

    # =========================================================================
    # Notifications
    # =========================================================================

    @abstractmethod
    def show_notification(self, config: NotificationConfig) -> None:
        """Show a notification popup

        Args:
            config: Notification configuration
        """
        pass

    @abstractmethod
    def play_sound(self, sound_type: str) -> None:
        """Play a notification sound

        Args:
            sound_type: Type of sound to play (e.g., 'notification')
        """
        pass

    # =========================================================================
    # Message Boxes
    # =========================================================================

    @abstractmethod
    def show_message_box(self, config: MessageBoxConfig) -> str:
        """Show a message box dialog

        Args:
            config: Message box configuration

        Returns:
            Label of clicked button
        """
        pass

    # =========================================================================
    # System Tray
    # =========================================================================

    @abstractmethod
    def create_tray_icon(self, icon_path: str, tooltip: str) -> bool:
        """Create system tray icon

        Args:
            icon_path: Path to icon file
            tooltip: Hover tooltip text

        Returns:
            True if tray icon created successfully
        """
        pass

    @abstractmethod
    def update_tray_menu(self, config: TrayMenuConfig) -> None:
        """Update tray icon context menu

        Args:
            config: Menu configuration
        """
        pass

    @abstractmethod
    def show_tray_message(self, title: str, message: str,
                          icon_path: Optional[str] = None,
                          duration_ms: int = 3000) -> None:
        """Show tray balloon notification

        Args:
            title: Notification title
            message: Notification message
            icon_path: Optional custom icon path
            duration_ms: Display duration
        """
        pass

    @abstractmethod
    def set_tray_activated_callback(self, callback: Callable) -> None:
        """Set callback for tray icon activation (click)

        Args:
            callback: Function to call on tray activation
        """
        pass

    # =========================================================================
    # Settings Dialog
    # =========================================================================

    @abstractmethod
    def show_settings_dialog(self, config: SettingsDialogConfig) -> Any:
        """Show settings dialog

        Args:
            config: Settings dialog configuration

        Returns:
            Dialog instance (framework-specific)
        """
        pass

    # =========================================================================
    # Detection Overlay
    # =========================================================================

    @abstractmethod
    def show_detection_overlay(self, config: DetectionOverlayConfig) -> Any:
        """Show detection result overlay

        Args:
            config: Overlay configuration

        Returns:
            Overlay instance (framework-specific)
        """
        pass

    # =========================================================================
    # Utilities
    # =========================================================================

    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        """Get primary screen dimensions

        Returns:
            Tuple of (width, height) in pixels
        """
        pass

    @abstractmethod
    def set_app_icon(self, icon_path: str) -> None:
        """Set application-wide icon

        Args:
            icon_path: Path to icon file
        """
        pass

    @abstractmethod
    def set_app_name(self, name: str) -> None:
        """Set application name

        Args:
            name: Application name
        """
        pass


# =============================================================================
# Module Info
# =============================================================================
__version__ = '1.0.0'
__author__ = 'COCK Development Team'
