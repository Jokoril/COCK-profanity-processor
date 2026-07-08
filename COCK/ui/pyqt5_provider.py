#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt5 UI Provider
=================

Implementation of UIProvider using PyQt5 for desktop GUI.

This module provides:
- Full implementation of UIProvider interface
- Notification popups with theming and positioning
- System tray icon with context menus
- Integration with existing settings dialog and overlay modules

Usage:
    from ui.pyqt5_provider import PyQt5Provider

    provider = PyQt5Provider()
    if provider.is_available():
        provider.create_app(sys.argv)
        provider.show_notification(NotificationConfig(...))

Version: 1.0.0
"""

import os
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

from logger import get_logger

from .interface import (
    UIProvider,
    NotificationConfig,
    MessageBoxConfig,
    TrayMenuConfig,
    TrayMenuItem,
    SettingsDialogConfig,
    DetectionOverlayConfig,
)

log = get_logger(__name__)

# Try to import PyQt5
try:
    from PyQt5.QtWidgets import (
        QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox,
        QWidget, QLabel, QVBoxLayout, QDesktopWidget
    )
    from PyQt5.QtGui import QIcon, QFont
    from PyQt5.QtCore import QTimer, Qt
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    log.warning("PyQt5 not available - PyQt5Provider will be non-functional")


class PyQt5Provider(UIProvider):
    """PyQt5 implementation of UIProvider

    Provides full desktop GUI functionality using PyQt5 framework.
    """

    def __init__(self):
        """Initialize the PyQt5 provider"""
        self.app: Optional[QApplication] = None
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self._active_notifications: List[QWidget] = []
        self._tray_actions: Dict[str, QAction] = {}
        self._tray_activated_callback: Optional[Callable] = None
        self._config: Dict[str, Any] = {}

    def set_config(self, config: Dict[str, Any]) -> None:
        """Set configuration reference for notification styling

        Args:
            config: Application configuration dict
        """
        self._config = config

    # =========================================================================
    # Application Lifecycle
    # =========================================================================

    def is_available(self) -> bool:
        """Check if PyQt5 is available"""
        return PYQT5_AVAILABLE

    def create_app(self, argv: List[str]) -> Any:
        """Create QApplication instance

        Args:
            argv: Command line arguments

        Returns:
            QApplication instance
        """
        if not PYQT5_AVAILABLE:
            log.warning("Cannot create app - PyQt5 not available")
            return None

        # Check if app already exists
        existing = QApplication.instance()
        if existing:
            self.app = existing
            log.debug("Using existing QApplication instance")
        else:
            self.app = QApplication(argv)
            log.debug("Created new QApplication instance")

        self.app.setQuitOnLastWindowClosed(False)
        return self.app

    def run_event_loop(self) -> int:
        """Run Qt event loop

        Returns:
            Exit code
        """
        if not self.app:
            log.warning("Cannot run event loop - no app created")
            return 1
        return self.app.exec_()

    def quit(self) -> None:
        """Quit the Qt application"""
        if self.app:
            self.app.quit()

    def schedule_callback(self, delay_ms: int, callback: Callable) -> None:
        """Schedule callback using QTimer

        Args:
            delay_ms: Delay in milliseconds
            callback: Function to call
        """
        if not PYQT5_AVAILABLE:
            return
        QTimer.singleShot(delay_ms, callback)

    # =========================================================================
    # Notifications
    # =========================================================================

    def show_notification(self, config: NotificationConfig) -> None:
        """Show a notification popup

        Creates a custom frameless widget positioned on screen.

        Args:
            config: Notification configuration
        """
        if not PYQT5_AVAILABLE:
            return

        try:
            # Create custom notification widget
            notification = QWidget()
            notification.setWindowFlags(
                Qt.WindowStaysOnTopHint |
                Qt.FramelessWindowHint |
                Qt.Tool
            )
            notification.setAttribute(Qt.WA_TranslucentBackground)
            notification.setAttribute(Qt.WA_ShowWithoutActivating)

            layout = QVBoxLayout()

            # Get scaling factor
            scale = config.scale

            # Title label
            title_label = QLabel(config.title)
            title_font = QFont()
            title_font.setBold(True)
            title_font.setPointSize(int(10 * scale))
            title_label.setFont(title_font)
            layout.addWidget(title_label)

            # Message label
            message_label = QLabel(config.message)
            message_label.setWordWrap(True)
            message_font = QFont()
            message_font.setPointSize(int(9 * scale))
            message_label.setFont(message_font)
            layout.addWidget(message_label)

            # Apply padding scale
            padding = int(12 * scale)
            layout.setContentsMargins(padding, padding, padding, padding)
            layout.setSpacing(int(8 * scale))

            notification.setLayout(layout)

            # Style based on theme
            if config.theme == 'dark':
                notification.setStyleSheet("""
                    QWidget {
                        background-color: #2b2b2b;
                        color: white;
                        border: 2px solid #555;
                        border-radius: 8px;
                        padding: 10px;
                    }
                """)
            else:
                notification.setStyleSheet("""
                    QWidget {
                        background-color: #f0f0f0;
                        color: black;
                        border: 2px solid #ccc;
                        border-radius: 8px;
                        padding: 10px;
                    }
                """)

            # Position on screen
            desktop = QDesktopWidget()
            screen_rect = desktop.availableGeometry()

            notification.adjustSize()

            # Calculate position based on config
            x, y = self._calculate_notification_position(
                screen_rect.width(),
                screen_rect.height(),
                notification.width(),
                notification.height(),
                config.position,
                config.offset_x,
                config.offset_y
            )

            notification.move(x, y)

            # Store reference to prevent garbage collection
            self._active_notifications.append(notification)

            notification.show()

            # Auto-close after duration
            if config.duration_ms > 0:
                def close_and_cleanup():
                    notification.close()
                    if notification in self._active_notifications:
                        self._active_notifications.remove(notification)

                QTimer.singleShot(config.duration_ms, close_and_cleanup)

        except Exception as e:
            log.error(f"Failed to show notification: {e}")

    def _calculate_notification_position(
        self,
        screen_width: int,
        screen_height: int,
        notif_width: int,
        notif_height: int,
        position: str,
        offset_x: int,
        offset_y: int
    ) -> Tuple[int, int]:
        """Calculate notification position on screen

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            notif_width: Notification width
            notif_height: Notification height
            position: Position preset name
            offset_x: X offset from edge
            offset_y: Y offset from edge

        Returns:
            Tuple of (x, y) position
        """
        positions = {
            'top-left': (offset_x, offset_y),
            'top-center': ((screen_width - notif_width) // 2 + offset_x, offset_y),
            'top-right': (screen_width - notif_width - offset_x, offset_y),
            'center-left': (offset_x, (screen_height - notif_height) // 2 + offset_y),
            'center': ((screen_width - notif_width) // 2 + offset_x,
                       (screen_height - notif_height) // 2 + offset_y),
            'center-right': (screen_width - notif_width - offset_x,
                             (screen_height - notif_height) // 2 + offset_y),
            'bottom-left': (offset_x, screen_height - notif_height - offset_y),
            'bottom-center': ((screen_width - notif_width) // 2 + offset_x,
                              screen_height - notif_height - offset_y),
            'bottom-right': (screen_width - notif_width - offset_x,
                             screen_height - notif_height - offset_y),
        }

        return positions.get(position, positions['center'])

    def play_sound(self, sound_type: str) -> None:
        """Play notification sound

        Note: Sound playback delegated to main app for now.

        Args:
            sound_type: Type of sound
        """
        # Sound playback stays in main.py for now
        pass

    # =========================================================================
    # Message Boxes
    # =========================================================================

    def show_message_box(self, config: MessageBoxConfig) -> str:
        """Show a message box dialog

        Args:
            config: Message box configuration

        Returns:
            Label of clicked button
        """
        if not PYQT5_AVAILABLE:
            return config.buttons[0] if config.buttons else 'OK'

        box_types = {
            'info': QMessageBox.information,
            'warning': QMessageBox.warning,
            'error': QMessageBox.critical,
            'question': QMessageBox.question,
        }

        func = box_types.get(config.box_type, QMessageBox.information)

        # Build button flags
        button_map = {
            'OK': QMessageBox.Ok,
            'Cancel': QMessageBox.Cancel,
            'Yes': QMessageBox.Yes,
            'No': QMessageBox.No,
            'Abort': QMessageBox.Abort,
            'Retry': QMessageBox.Retry,
            'Ignore': QMessageBox.Ignore,
        }

        buttons = QMessageBox.NoButton
        for btn_label in config.buttons:
            if btn_label in button_map:
                buttons |= button_map[btn_label]

        if buttons == QMessageBox.NoButton:
            buttons = QMessageBox.Ok

        result = func(None, config.title, config.message, buttons)

        # Convert result back to label
        result_map = {v: k for k, v in button_map.items()}
        return result_map.get(result, 'OK')

    # =========================================================================
    # System Tray
    # =========================================================================

    def create_tray_icon(self, icon_path: str, tooltip: str) -> bool:
        """Create system tray icon

        Args:
            icon_path: Path to icon file
            tooltip: Hover tooltip text

        Returns:
            True if successful
        """
        if not PYQT5_AVAILABLE:
            return False

        try:
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
            else:
                icon = QIcon()
                log.warning(f"Tray icon not found at {icon_path}")

            self.tray_icon = QSystemTrayIcon(icon, self.app)
            self.tray_icon.setToolTip(tooltip)

            # Connect activation signal
            self.tray_icon.activated.connect(self._on_tray_activated)

            self.tray_icon.show()
            log.debug("System tray icon created")
            return True

        except Exception as e:
            log.warning(f"Could not create system tray icon: {e}")
            return False

    def _on_tray_activated(self, reason) -> None:
        """Handle tray icon activation"""
        if self._tray_activated_callback:
            self._tray_activated_callback(reason)

    def update_tray_menu(self, config: TrayMenuConfig) -> None:
        """Update tray icon context menu

        Args:
            config: Menu configuration
        """
        if not self.tray_icon:
            return

        menu = QMenu()
        self._tray_actions.clear()

        self._build_menu(menu, config.items)

        self.tray_icon.setContextMenu(menu)

    def _build_menu(self, menu: QMenu, items: List[TrayMenuItem]) -> None:
        """Recursively build menu structure

        Args:
            menu: Parent menu
            items: List of menu items
        """
        for item in items:
            if item.separator:
                menu.addSeparator()
                continue

            if item.submenu:
                # Create submenu
                submenu = menu.addMenu(item.label)
                self._build_menu(submenu, item.submenu)
            else:
                # Create action
                action = QAction(item.label, self.app)

                if item.checkable:
                    action.setCheckable(True)
                    action.setChecked(item.checked)

                if item.callback:
                    if item.checkable:
                        action.triggered.connect(item.callback)
                    else:
                        action.triggered.connect(item.callback)

                menu.addAction(action)

                # Store reference for later updates
                self._tray_actions[item.label] = action

    def show_tray_message(
        self,
        title: str,
        message: str,
        icon_path: Optional[str] = None,
        duration_ms: int = 3000
    ) -> None:
        """Show tray balloon notification

        Args:
            title: Notification title
            message: Notification message
            icon_path: Optional custom icon
            duration_ms: Display duration
        """
        if not self.tray_icon:
            return

        if icon_path and os.path.exists(icon_path):
            custom_icon = QIcon(icon_path)
            self.tray_icon.showMessage(title, message, custom_icon, duration_ms)
        else:
            self.tray_icon.showMessage(
                title, message, QSystemTrayIcon.Information, duration_ms
            )

    def set_tray_activated_callback(self, callback: Callable) -> None:
        """Set callback for tray icon activation

        Args:
            callback: Function to call on tray activation
        """
        self._tray_activated_callback = callback

    def get_tray_action(self, label: str) -> Optional[QAction]:
        """Get a tray menu action by label

        Args:
            label: Action label

        Returns:
            QAction or None
        """
        return self._tray_actions.get(label)

    # =========================================================================
    # Settings Dialog
    # =========================================================================

    def show_settings_dialog(self, config: SettingsDialogConfig) -> Any:
        """Show settings dialog

        Delegates to existing settings_dialog module.

        Args:
            config: Settings dialog configuration

        Returns:
            Dialog instance
        """
        if not PYQT5_AVAILABLE:
            return None

        try:
            import settings_dialog
            dialog = settings_dialog.SettingsDialog(
                config.config,
                config.filter_stats,
                parent=None
            )

            # Connect callbacks
            if 'settings_saved' in config.callbacks:
                dialog.settings_saved.connect(config.callbacks['settings_saved'])
            if 'finished' in config.callbacks:
                dialog.finished.connect(config.callbacks['finished'])

            return dialog

        except Exception as e:
            log.error(f"Failed to create settings dialog: {e}")
            return None

    # =========================================================================
    # Detection Overlay
    # =========================================================================

    def show_detection_overlay(self, config: DetectionOverlayConfig) -> Any:
        """Show detection result overlay

        Delegates to existing overlay_manual module.

        Args:
            config: Overlay configuration

        Returns:
            Overlay instance
        """
        if not PYQT5_AVAILABLE:
            return None

        try:
            import overlay_manual
            overlay = overlay_manual.ManualModeOverlay(config.detection_result)

            # Connect callbacks
            if 'use_suggestion' in config.callbacks:
                overlay.use_suggestion.connect(config.callbacks['use_suggestion'])
            if 'cancelled' in config.callbacks:
                overlay.cancelled.connect(config.callbacks['cancelled'])

            return overlay

        except Exception as e:
            log.error(f"Failed to create detection overlay: {e}")
            return None

    # =========================================================================
    # Utilities
    # =========================================================================

    def get_screen_size(self) -> Tuple[int, int]:
        """Get primary screen dimensions

        Returns:
            Tuple of (width, height)
        """
        if not PYQT5_AVAILABLE:
            return (1920, 1080)  # Fallback

        desktop = QDesktopWidget()
        screen_rect = desktop.availableGeometry()
        return (screen_rect.width(), screen_rect.height())

    def set_app_icon(self, icon_path: str) -> None:
        """Set application-wide icon

        Args:
            icon_path: Path to icon file
        """
        if not self.app or not os.path.exists(icon_path):
            return
        self.app.setWindowIcon(QIcon(icon_path))

    def set_app_name(self, name: str) -> None:
        """Set application name

        Args:
            name: Application name
        """
        if self.app:
            self.app.setApplicationName(name)


# =============================================================================
# Module Info
# =============================================================================
__version__ = '1.0.0'
__author__ = 'COCK Development Team'
