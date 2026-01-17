#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hotkey Recorder Widget
======================
Reusable widget for recording keyboard hotkeys

Features:
- "Click to Record" button for clear UX
- Captures actual key presses
- Supports modifiers (Ctrl, Shift, Alt)
- Supports mouse buttons (except left/right click)
- Conflict validation with warnings
- Visual feedback during recording

Usage:
    from ui.widgets.hotkey_recorder import HotkeyRecorder

    recorder = HotkeyRecorder(current_hotkey='ctrl+f12')
    # ... add to layout ...
    hotkey = recorder.get_hotkey()
"""

try:
    from PyQt5.QtWidgets import (
        QWidget, QHBoxLayout, QLabel, QPushButton, QMessageBox
    )
    from PyQt5.QtCore import Qt, QEvent
    from PyQt5.QtGui import QKeySequence
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False


if PYQT5_AVAILABLE:
    class HotkeyRecorder(QWidget):
        """
        Professional hotkey recorder widget

        Features:
        - "Click to Record" button for clear UX
        - Captures actual key presses
        - Supports modifiers (Ctrl, Shift, Alt)
        - Supports mouse buttons (except left/right click)
        - Conflict validation with warnings
        - Visual feedback during recording
        """

        def __init__(self, current_hotkey='', parent=None):
            """
            Initialize hotkey recorder

            Args:
                current_hotkey: Currently configured hotkey string
                parent: Parent widget
            """
            super().__init__(parent)
            self.recording = False
            self.hotkey = current_hotkey
            self.modifiers = set()
            self.key = None

            self.init_ui()

        def init_ui(self):
            """Initialize UI components"""
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)

            # Display label
            self.label = QLabel(self.hotkey or "Not set")
            self.label.setFrameStyle(QLabel.Panel | QLabel.Sunken)
            self.label.setMinimumWidth(150)
            self.label.setStyleSheet("padding: 4px;")
            layout.addWidget(self.label)

            # Record button
            self.record_btn = QPushButton("Record...")
            self.record_btn.clicked.connect(self.start_recording)
            layout.addWidget(self.record_btn)

            # Clear button
            clear_btn = QPushButton("Clear")
            clear_btn.clicked.connect(self.clear_hotkey)
            layout.addWidget(clear_btn)

            self.setLayout(layout)

        def start_recording(self):
            """Start recording hotkey"""
            self.recording = True
            self.modifiers = set()
            self.key = None
            self.label.setText("Press keys...")
            self.label.setStyleSheet("background-color: #ffeb3b; padding: 4px; color: #000;")
            self.record_btn.setEnabled(False)

            # Install event filter to capture keys
            self.installEventFilter(self)

            # Also install on parent window
            if self.window():
                self.window().installEventFilter(self)

        def eventFilter(self, obj, event):
            """Capture keyboard and mouse events"""
            if not self.recording:
                return False

            if event.type() == QEvent.KeyPress:
                key = event.key()

                # Track modifiers
                if key == Qt.Key_Control:
                    self.modifiers.add('ctrl')
                    return True
                elif key == Qt.Key_Shift:
                    self.modifiers.add('shift')
                    return True
                elif key == Qt.Key_Alt:
                    self.modifiers.add('alt')
                    return True
                elif key == Qt.Key_Meta or key == Qt.Key_Super_L or key == Qt.Key_Super_R:
                    # Windows/Super key - not supported
                    return True

                # Regular key pressed - finish recording
                # Get key text
                if key == Qt.Key_Escape:
                    self.key = 'esc'
                elif key == Qt.Key_Return or key == Qt.Key_Enter:
                    self.key = 'enter'
                elif key == Qt.Key_Tab:
                    self.key = 'tab'
                elif key == Qt.Key_Backspace:
                    self.key = 'backspace'
                elif key == Qt.Key_Delete:
                    self.key = 'delete'
                elif key == Qt.Key_Insert:
                    self.key = 'insert'
                elif key == Qt.Key_Home:
                    self.key = 'home'
                elif key == Qt.Key_End:
                    self.key = 'end'
                elif key == Qt.Key_PageUp:
                    self.key = 'pageup'
                elif key == Qt.Key_PageDown:
                    self.key = 'pagedown'
                elif key == Qt.Key_Up:
                    self.key = 'up'
                elif key == Qt.Key_Down:
                    self.key = 'down'
                elif key == Qt.Key_Left:
                    self.key = 'left'
                elif key == Qt.Key_Right:
                    self.key = 'right'
                elif key == Qt.Key_Space:
                    self.key = 'space'
                elif Qt.Key_F1 <= key <= Qt.Key_F35:
                    # Function keys
                    f_num = key - Qt.Key_F1 + 1
                    self.key = f'f{f_num}'
                else:
                    # Try to get text representation
                    key_text = event.text()
                    if key_text and key_text.isprintable():
                        self.key = key_text.lower()
                    else:
                        # Fallback to key sequence
                        seq = QKeySequence(key).toString().lower()
                        if seq:
                            self.key = seq

                if self.key:
                    self.finish_recording()
                return True

            elif event.type() == QEvent.MouseButtonPress:
                # Support mouse buttons (except left/right)
                button = event.button()

                if button == Qt.MiddleButton:
                    self.key = 'middle_mouse'
                    self.finish_recording()
                    return True
                elif button == Qt.XButton1:
                    self.key = 'mouse4'
                    self.finish_recording()
                    return True
                elif button == Qt.XButton2:
                    self.key = 'mouse5'
                    self.finish_recording()
                    return True

            return False

        def finish_recording(self):
            """Finish recording and display hotkey"""
            self.recording = False
            self.removeEventFilter(self)

            if self.window():
                self.window().removeEventFilter(self)

            self.record_btn.setEnabled(True)
            self.label.setStyleSheet("padding: 4px;")

            if self.key:
                # Build hotkey string
                parts = []
                if 'ctrl' in self.modifiers:
                    parts.append('ctrl')
                if 'shift' in self.modifiers:
                    parts.append('shift')
                if 'alt' in self.modifiers:
                    parts.append('alt')
                parts.append(self.key)

                self.hotkey = '+'.join(parts)

                # Check for conflicts
                self.check_conflicts()

                self.label.setText(self.hotkey)
            else:
                self.label.setText("Cancelled")
                self.hotkey = ''

        def check_conflicts(self):
            """Check for hotkey conflicts"""
            # Common system hotkeys
            system_hotkeys = [
                'ctrl+c', 'ctrl+v', 'ctrl+x', 'ctrl+a', 'ctrl+z', 'ctrl+y',
                'alt+f4', 'ctrl+alt+delete', 'alt+tab', 'ctrl+esc',
                'ctrl+shift+esc', 'alt+enter'
            ]

            if self.hotkey.lower() in system_hotkeys:
                QMessageBox.warning(
                    self,
                    "Hotkey Conflict",
                    f"Warning: '{self.hotkey}' is a system hotkey.\n\n"
                    "It may not work as expected or could interfere with system functions."
                )

        def clear_hotkey(self):
            """Clear the hotkey"""
            self.hotkey = ''
            self.label.setText("Not set")

        def get_hotkey(self):
            """
            Get the recorded hotkey

            Returns:
                str: Hotkey string (e.g., 'ctrl+f12')
            """
            return self.hotkey


# Fallback for non-PyQt5 environments
if not PYQT5_AVAILABLE:
    class HotkeyRecorder:
        """Stub class when PyQt5 is not available"""
        def __init__(self, *args, **kwargs):
            pass

        def get_hotkey(self):
            return ''


# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
