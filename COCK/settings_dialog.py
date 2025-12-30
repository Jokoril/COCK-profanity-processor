#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings Dialog
===============
Configuration interface with tabbed layout

Features:
- General settings (filter file, mode, hotkey)
- Optimization settings (leet-speak, unicode, shorthand)
- UI settings (theme, auto-dismiss)
- About tab with version info

Usage:
    from settings_dialog import SettingsDialog
    
    dialog = SettingsDialog(config)
    if dialog.exec_():
        updated_config = dialog.get_config()
"""

import sys
import os
import path_manager

try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
        QLabel, QPushButton, QFileDialog, QLineEdit,
        QComboBox, QCheckBox, QSpinBox, QGroupBox,
        QMessageBox, QApplication, QWidget, QListWidget, QListWidgetItem, QInputDialog,
        QSlider
    )
    from PyQt5.QtCore import Qt, QEvent, pyqtSignal
    from PyQt5.QtGui import QFont, QPixmap
    PYQT5_AVAILABLE = True
except ImportError:
    print("WARNING: PyQt5 not installed. Install with: pip install PyQt5")
    PYQT5_AVAILABLE = False
    class QDialog: pass


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
                from PyQt5.QtGui import QKeySequence
                
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
                    f"⚠️ Warning: '{self.hotkey}' is a system hotkey.\n\n"
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
    
    class SettingsDialog(QDialog):
        """
        Settings dialog with tabbed interface
        
        Tabs:
        - General: Filter file, mode, hotkey
        - Optimization: Leet-speak, unicode, shorthand settings
        - UI: Theme, auto-dismiss, feedback
        - About: Version and credits
        """
        
        # Signal emitted when settings are saved
        # Args: needs_restart (bool) - True if app needs restart
        settings_saved = pyqtSignal(bool)
        
        def __init__(self, config: dict, filter_stats: dict = None, parent=None):
            """
            Initialize settings dialog
            
            Args:
                config: Current configuration dictionary
                filter_stats: Statistics from filter loader (optional)
                parent: Parent widget (ChatCensorTool instance) for accessing update_checker and help_manager
            """
            super().__init__(parent)
            
            self.config = config.copy()  # Work with a copy
            self.filter_stats = filter_stats or {}
            self.filter_file_changed = False  # Track if filter file was changed
            self.original_filter_file = config.get('filter_file', '')
            
            self.init_ui()
        
        def init_ui(self):
            """Initialize the user interface"""
            # Get scaling factor
            scale = self.config.get('ui', {}).get('settings_scale', 1.0)
            
            # Make window frameless
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            
            # Window properties
            self.setWindowTitle("Compliant Online Chat Kit - Settings")
            self.setMinimumWidth(int(600 * scale))
            self.setMinimumHeight(int(500 * scale))

            # Set window icon for taskbar
            icon_path = path_manager.get_resource_file('icons/icon.ico')
            if os.path.exists(icon_path):
                from PyQt5.QtGui import QIcon
                self.setWindowIcon(QIcon(icon_path))
            
            # Apply font scaling to entire dialog
            if scale != 1.0:
                font = self.font()
                font.setPointSize(int(font.pointSize() * scale))
                self.setFont(font)
            
            # Variables for window dragging
            self.dragging = False
            self.drag_position = None
            
            # Create custom title bar
            title_bar = self.create_title_bar()
            
            # Main layout with title bar
            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            main_layout.addWidget(title_bar)
            
            # Content layout (this will hold tabs)
            layout = QVBoxLayout()
            layout.setContentsMargins(10, 10, 10, 10)
            
            # Tab widget
            self.tabs = QTabWidget()
            
            self.tabs.addTab(self.create_general_tab(), "General")
            self.tabs.addTab(self.create_optimization_tab(), "Optimization")
            self.tabs.addTab(self.create_filter_tab(), "Filter List")
            self.tabs.addTab(self.create_whitelist_tab(), "Whitelist")
            self.tabs.addTab(self.create_ui_tab(), "UI")
            self.tabs.addTab(self.create_about_tab(), "About")
            
            layout.addWidget(self.tabs)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            self.save_button = QPushButton("💾 Save Settings")
            self.save_button.clicked.connect(self.save_settings)
            button_layout.addWidget(self.save_button)
            
            button_layout.addStretch()  # Push close button to the right
            
            self.close_button = QPushButton("✕ Close")
            self.close_button.clicked.connect(self.reject)
            button_layout.addWidget(self.close_button)
            
            layout.addLayout(button_layout)
            
            # Add content layout to main layout
            content_widget = QWidget()
            content_widget.setLayout(layout)
            main_layout.addWidget(content_widget)
            
            self.setLayout(main_layout)
            
            # Apply theme
            self.apply_theme()
        
        def create_title_bar(self):
            """Create custom title bar with minimize/maximize/close buttons"""
            title_bar = QWidget()
            title_bar.setObjectName("titleBar")
            title_bar.setFixedHeight(35)
            
            layout = QHBoxLayout()
            layout.setContentsMargins(10, 0, 0, 0)
            layout.setSpacing(5)  # Space between icon and title
            
            # App icon
            icon_label = QLabel()
            icon_path = path_manager.get_resource_file('icons/icon.ico')
            if os.path.exists(icon_path):
                from PyQt5.QtGui import QIcon
                icon = QIcon(icon_path)
                pixmap = icon.pixmap(24, 24)  # Extract 24×24 from ICO
                icon_label.setPixmap(pixmap)
            
            # Title label
            self.title_label = QLabel("Compliant Online Chat Kit - Settings")
            self.title_label.setObjectName("titleLabel")
            title_font = QFont()
            title_font.setPointSize(10)
            title_font.setBold(True)
            self.title_label.setFont(title_font)
            layout.addWidget(self.title_label)
            
            layout.addStretch()
            
            # Minimize button
            min_btn = QPushButton("─")
            min_btn.setObjectName("minButton")
            min_btn.setFixedSize(45, 35)
            min_btn.clicked.connect(self.showMinimized)
            layout.addWidget(min_btn)
            
            # Maximize/Restore button
            self.max_btn = QPushButton("□")
            self.max_btn.setObjectName("maxButton")
            self.max_btn.setFixedSize(45, 35)
            self.max_btn.clicked.connect(self.toggle_maximize)
            layout.addWidget(self.max_btn)
            
            # Close button
            close_btn = QPushButton("✕")
            close_btn.setObjectName("closeButton")
            close_btn.setFixedSize(45, 35)
            close_btn.clicked.connect(self.close)
            layout.addWidget(close_btn)
            
            title_bar.setLayout(layout)
            
            # Enable dragging
            title_bar.mousePressEvent = self.title_bar_mouse_press
            title_bar.mouseMoveEvent = self.title_bar_mouse_move
            title_bar.mouseReleaseEvent = self.title_bar_mouse_release
            
            return title_bar
        
        def toggle_maximize(self):
            """Toggle between maximized and normal state"""
            if self.isMaximized():
                self.showNormal()
                self.max_btn.setText("□")
            else:
                self.showMaximized()
                self.max_btn.setText("❐")
        
        def title_bar_mouse_press(self, event):
            """Handle mouse press on title bar - start dragging"""
            if event.button() == Qt.LeftButton:
                self.dragging = True
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
        
        def title_bar_mouse_move(self, event):
            """Handle mouse move on title bar - drag window"""
            if self.dragging and event.buttons() == Qt.LeftButton:
                self.move(event.globalPos() - self.drag_position)
                event.accept()
        
        def title_bar_mouse_release(self, event):
            """Handle mouse release - stop dragging"""
            if event.button() == Qt.LeftButton:
                self.dragging = False
                event.accept()
        
        def create_general_tab(self):
            """Create General settings tab"""
            from PyQt5.QtWidgets import QWidget, QScrollArea
            
            widget = QWidget()
            layout = QVBoxLayout()
            
            # Filter file selection
            filter_group = QGroupBox("Filter Word List")
            filter_layout = QVBoxLayout()
            
            self.filter_path_label = QLabel(self.config.get('filter_file', 'Not selected'))
            self.filter_path_label.setWordWrap(True)
            filter_layout.addWidget(QLabel("Current filter file:"))
            filter_layout.addWidget(self.filter_path_label)
            
            browse_btn = QPushButton("Browse for Filter File...")
            browse_btn.clicked.connect(self.browse_filter_file)
            filter_layout.addWidget(browse_btn)
            
            # Stats display
            if self.filter_stats:
                stats_text = QLabel(
                    f"Loaded entries: {self.filter_stats.get('final_count', 0)}\n"
                    f"Load time: {self.filter_stats.get('load_time_ms', 0):.0f}ms"
                )
                filter_layout.addWidget(stats_text)
            
            filter_group.setLayout(filter_layout)
            layout.addWidget(filter_group)
            
            # Detection mode
            mode_group = QGroupBox("Detection Mode")
            mode_layout = QVBoxLayout()
            
            self.mode_combo = QComboBox()
            self.mode_combo.addItems(["manual", "auto"])
            current_mode = self.config.get('detection_mode', 'manual')
            self.mode_combo.setCurrentText(current_mode)
            mode_layout.addWidget(QLabel("Mode:"))
            mode_layout.addWidget(self.mode_combo)
            
            mode_desc = QLabel(
                "Manual: User reviews each detection and chooses action\n"
                "Auto: Automatic optimization and sending, no prompts"
            )
            mode_desc.setWordWrap(True)
            mode_layout.addWidget(mode_desc)
            
            mode_group.setLayout(mode_layout)
            layout.addWidget(mode_group)
            
            # Hotkey
            hotkey_group = QGroupBox("Hotkeys")
            hotkey_layout = QVBoxLayout()
            
            # Normal hotkey
            hotkey_layout.addWidget(QLabel("Normal Optimize Hotkey:"))
            self.hotkey_recorder = HotkeyRecorder(self.config.get('hotkey', 'F12'))
            hotkey_layout.addWidget(self.hotkey_recorder)
            
            # Force optimize hotkey
            hotkey_layout.addWidget(QLabel("Force Optimize Hotkey:"))
            self.force_hotkey_recorder = HotkeyRecorder(self.config.get('force_optimize_hotkey', 'Ctrl+F12'))
            hotkey_layout.addWidget(self.force_hotkey_recorder)
            
            # Toggle hotkeys hotkey
            hotkey_layout.addWidget(QLabel("Toggle Hotkeys On/Off:"))
            toggle_hotkey_combo = self.config.get('toggle_hotkeys_hotkey', 'Ctrl+Shift+H')
            if isinstance(toggle_hotkey_combo, dict):
                toggle_hotkey_combo = toggle_hotkey_combo.get('combo', 'Ctrl+Shift+H')
            self.toggle_hotkey_recorder = HotkeyRecorder(toggle_hotkey_combo)
            hotkey_layout.addWidget(self.toggle_hotkey_recorder)
            
            hotkey_layout.addWidget(QLabel(""))  # Spacer
            hotkey_layout.addWidget(QLabel(
                "Tip: Click 'Record...' button, then press your desired key combination.\n"
                "Supports Ctrl, Shift, Alt modifiers and most keys including function keys."
            ))
            hotkey_layout.addWidget(QLabel(
                "Note: If Force Optimize doesn't capture text, avoid using Shift\n"
                "(e.g., use ctrl+f12 instead of shift+f12)"
            ))
            
            hotkey_group.setLayout(hotkey_layout)
            layout.addWidget(hotkey_group)
            
            # Message Limits
            limits_group = QGroupBox("Message Limits")
            limits_layout = QVBoxLayout()
            
            limits_layout.addWidget(QLabel("Set to 0 for no limits"))
            
            # Byte limit
            byte_layout = QHBoxLayout()
            byte_label = QLabel("Byte limit:")
            byte_label.setFixedWidth(100)
            byte_layout.addWidget(byte_label)
            self.byte_limit_spin = QSpinBox()
            self.byte_limit_spin.setMinimum(0)
            self.byte_limit_spin.setMaximum(9999)
            self.byte_limit_spin.setValue(self.config.get('byte_limit', 92))
            byte_layout.addWidget(self.byte_limit_spin)
            byte_layout.addStretch()
            limits_layout.addLayout(byte_layout)
            
            # Character limit
            char_layout = QHBoxLayout()
            char_label = QLabel("Character limit:")
            char_label.setFixedWidth(100)
            char_layout.addWidget(char_label)
            self.char_limit_spin = QSpinBox()
            self.char_limit_spin.setMinimum(0)
            self.char_limit_spin.setMaximum(9999)
            self.char_limit_spin.setValue(self.config.get('character_limit', 80))
            char_layout.addWidget(self.char_limit_spin)
            char_layout.addStretch()
            limits_layout.addLayout(char_layout)
            
            limits_group.setLayout(limits_layout)
            layout.addWidget(limits_group)
            
            # Data folder button
            data_btn = QPushButton("Open Data Folder")
            data_btn.clicked.connect(self.open_data_folder)
            layout.addWidget(data_btn)
            
            # Update settings group
            update_group = QGroupBox("Updates")
            update_layout = QVBoxLayout()
            
            # Check for updates checkbox
            self.check_updates_cb = QCheckBox("Check for updates at startup")
            self.check_updates_cb.setChecked(
                self.config.get('updates', {}).get('check_enabled', True)
            )
            self.check_updates_cb.setToolTip(
                "Automatically check for new versions when the application starts"
            )
            
            # Last check info
            last_check = None
            if hasattr(getattr(self, "main_app", None), 'update_checker'):
                try:
                    last_check = getattr(self, "main_app", None).update_checker.get_last_check_time()
                except:
                    pass
            
            last_check_text = f"Last checked: {last_check}" if last_check else "Never checked"
            self.last_check_label = QLabel(last_check_text)
            self.last_check_label.setStyleSheet("color: gray; font-size: 9pt;")
            
            # Check now button
            check_now_btn = QPushButton("Check Now")
            check_now_btn.clicked.connect(self._check_updates_now)
            check_now_btn.setToolTip("Check for updates immediately")
            
            # View releases button
            releases_btn = QPushButton("View Releases")
            releases_btn.clicked.connect(lambda: self._open_help('releases'))
            releases_btn.setToolTip("View all releases on GitHub")
            
            # Button layout
            button_layout = QHBoxLayout()
            button_layout.addWidget(check_now_btn)
            button_layout.addWidget(releases_btn)
            button_layout.addStretch()
            
            update_layout.addWidget(self.check_updates_cb)
            update_layout.addWidget(self.last_check_label)
            update_layout.addLayout(button_layout)
            update_group.setLayout(update_layout)
            layout.addWidget(update_group)
            
            layout.addStretch()
            widget.setLayout(layout)
            return widget
        
        def _check_updates_now(self):
            """Manual update check"""
            from PyQt5.QtWidgets import QProgressDialog, QMessageBox
            from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
            
            try:
                # Get update checker from main app
                if not hasattr(getattr(self, "main_app", None), 'update_checker'):
                    QMessageBox.warning(
                        self,
                        "Update Check Unavailable",
                        "Update checker is not available."
                    )
                    return
                
                update_checker_obj = getattr(self, "main_app", None).update_checker
                
                # Create signal helper for thread-safe communication
                class ResultSignal(QObject):
                    finished = pyqtSignal(object)
                
                signal_helper = ResultSignal()
                
                # Show non-modal progress dialog
                progress = QProgressDialog("Checking for updates...", None, 0, 0, self)
                progress.setWindowTitle("Update Check")
                progress.setWindowModality(Qt.NonModal)  # Non-modal so event loop isn't blocked!
                progress.setCancelButton(None)
                progress.setMinimumDuration(0)
                progress.setValue(0)
                progress.show()
                self.update()  # Force UI update
                
                def show_result(version_info):
                    """Handle result - runs in main thread via signal"""
                    try:
                        progress.close()
                        
                        if version_info:
                            # Update available
                            try:
                                import update_checker
                                latest = version_info.get('version', 'Unknown')
                                current = update_checker.UpdateChecker.CURRENT_VERSION
                                changelog = version_info.get('changelog', [])
                                download_url = version_info.get('download_url', '')
                                
                                changelog_text = '\n'.join(f"• {item}" for item in changelog)
                                
                                msg = QMessageBox(self)
                                msg.setWindowTitle("Update Available")
                                msg.setIcon(QMessageBox.Information)
                                msg.setText(f"<h3>Version {latest} is available!</h3>")
                                msg.setInformativeText(
                                    f"<b>Current:</b> {current}<br>"
                                    f"<b>Latest:</b> {latest}<br><br>"
                                    f"<b>Changes:</b><br>{changelog_text}"
                                )
                                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                                msg.button(QMessageBox.Ok).setText("Download")
                                msg.button(QMessageBox.Cancel).setText("Later")
                                
                                result = msg.exec_()
                                
                                if result == QMessageBox.Ok:
                                    if hasattr(getattr(self, 'main_app', None), 'help_manager'):
                                        getattr(self, 'main_app', None).help_manager.open_custom_url(download_url)
                                
                                last_check = update_checker_obj.get_last_check_time()
                                if last_check and hasattr(self, 'last_check_label'):
                                    self.last_check_label.setText(f"Last checked: {last_check}")
                            except Exception as e:
                                print(f"[SETTINGS] Error showing update dialog: {e}")
                                import traceback
                                traceback.print_exc()
                        else:
                            # Up to date or error
                            try:
                                import update_checker
                                current = update_checker.UpdateChecker.CURRENT_VERSION
                                
                                QMessageBox.information(
                                    self,
                                    "Up to Date",
                                    f"You're running the latest version!\n\n"
                                    f"Current version: {current}"
                                )
                                
                                last_check = update_checker_obj.get_last_check_time()
                                if last_check and hasattr(self, 'last_check_label'):
                                    self.last_check_label.setText(f"Last checked: {last_check}")
                            except Exception as e:
                                print(f"[SETTINGS] Error showing up-to-date dialog: {e}")
                                import traceback
                                traceback.print_exc()
                    except Exception as e:
                        print(f"[SETTINGS] Error in show_result: {e}")
                        import traceback
                        traceback.print_exc()
                
                # Connect signal (auto-connection to main thread)
                signal_helper.finished.connect(show_result)
                
                def on_result(version_info):
                    """Called from background thread - emit signal"""
                    signal_helper.finished.emit(version_info)
                
                # Start async check
                update_checker_obj.check_for_updates(on_result)
            
            except Exception as e:
                print(f"[SETTINGS] Error checking updates: {e}")
                import traceback
                traceback.print_exc()
                try:
                    QMessageBox.critical(
                        self,
                        "Update Check Failed",
                        f"Failed to check for updates:\n{str(e)}"
                    )
                except:
                    pass
            
            except Exception as e:
                print(f"[SETTINGS] Error checking updates: {e}")
                QMessageBox.critical(
                    self,
                    "Update Check Failed",
                    f"Failed to check for updates:\n{str(e)}"
                )
        
        def validate_hotkeys(self):
            """Check for hotkey conflicts before saving"""
            # Get hotkeys from both recorders
            normal_hotkey = self.hotkey_recorder.get_hotkey()
            force_hotkey = self.force_hotkey_recorder.get_hotkey()
            
            # Check if both hotkeys are the same (and not empty)
            if normal_hotkey and force_hotkey and normal_hotkey.lower() == force_hotkey.lower():
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Hotkey Conflict",
                    f"Normal optimize and Force optimize cannot use the same hotkey!\n\n"
                    f"Both are set to: {normal_hotkey}\n\n"
                    f"Please choose different hotkeys.",
                    QMessageBox.Ok
                )
                return False
            
            return True

        def create_optimization_tab(self):
            """Create Optimization settings tab"""
            from PyQt5.QtWidgets import QWidget
            
            widget = QWidget()
            layout = QVBoxLayout()
            
            # Leet-speak
            leet_group = QGroupBox("Leet-Speak")
            leet_layout = QVBoxLayout()
            
            self.leet_enabled = QCheckBox("Enable leet-speak optimization")
            leet_enabled = self.config.get('optimization', {}).get('leet_speak', True)
            self.leet_enabled.setChecked(leet_enabled)
            leet_layout.addWidget(self.leet_enabled)
            
            leet_desc = QLabel("Convert characters (e.g., 'hello' → 'h3ll0')\n0 byte overhead")
            leet_desc.setWordWrap(True)
            leet_layout.addWidget(leet_desc)
            
            leet_group.setLayout(leet_layout)
            layout.addWidget(leet_group)
            
            # Fancy Unicode
            unicode_group = QGroupBox("Fancy Unicode")
            unicode_layout = QVBoxLayout()
            
            self.unicode_enabled = QCheckBox("Enable Unicode optimization")
            unicode_enabled = self.config.get('optimization', {}).get('fancy_unicode', True)
            self.unicode_enabled.setChecked(unicode_enabled)
            unicode_layout.addWidget(self.unicode_enabled)
            
            unicode_desc = QLabel("Use Fancy Text (e.g., 'hello' → '🄷🄴🄻🄻🄾')\n+3 bytes per character")
            unicode_desc.setWordWrap(True)
            unicode_layout.addWidget(unicode_desc)
            
            unicode_group.setLayout(unicode_layout)
            layout.addWidget(unicode_group)
            
            # Shorthand
            shorthand_group = QGroupBox("Shorthand")
            shorthand_layout = QVBoxLayout()
            
            self.shorthand_enabled = QCheckBox("Enable shorthand compression")
            shorthand_enabled = self.config.get('optimization', {}).get('shorthand', True)
            self.shorthand_enabled.setChecked(shorthand_enabled)
            shorthand_layout.addWidget(self.shorthand_enabled)
            
            shorthand_desc = QLabel("Abbreviate words (e.g., 'everyone' → 'every1')\nSaves bytes")
            shorthand_desc.setWordWrap(True)
            shorthand_layout.addWidget(shorthand_desc)
            
            shorthand_group.setLayout(shorthand_layout)
            layout.addWidget(shorthand_group)
            
            # Link protection
            link_group = QGroupBox("Link Protection")
            link_layout = QVBoxLayout()
            
            self.link_protection = QCheckBox("Protect URLs from modification")
            link_enabled = self.config.get('optimization', {}).get('link_protection', True)
            self.link_protection.setChecked(link_enabled)
            link_layout.addWidget(self.link_protection)
            
            link_group.setLayout(link_layout)
            layout.addWidget(link_group)
            
            # Special Character Interspacing
            special_char_group = QGroupBox("Special Character Interspacing")
            special_char_layout = QVBoxLayout()
            
            self.special_char_enabled = QCheckBox("Enable special character interspacing (replaces leet/fancy)")
            special_char_enabled = self.config.get('optimization', {}).get('special_char_interspacing', False)
            self.special_char_enabled.setChecked(special_char_enabled)
            special_char_layout.addWidget(self.special_char_enabled)
            
            special_char_desc = QLabel(
                "Inserts invisible/special character to break pattern detection.\n"
                "Adds an invisible character that your game recognizes and does not strip to break up word patterns\n"
                "Characters are 'invisible' when the game's font does not support them\n"
                "+1 char, +2-3 bytes per insertion"
            )
            special_char_desc.setWordWrap(True)
            special_char_layout.addWidget(special_char_desc)
            
            # Character input field
            char_input_layout = QHBoxLayout()
            char_input_layout.addWidget(QLabel("Character:"))
            
            self.special_char_input = QLineEdit()
            self.special_char_input.setMaxLength(1)
            self.special_char_input.setFixedWidth(50)
            current_char = self.config.get('special_char_interspacing', {}).get('character', '❤')
            self.special_char_input.setText(current_char)
            char_input_layout.addWidget(self.special_char_input)
            
            # Default button
            default_btn = QPushButton("Reset to ❤")
            default_btn.clicked.connect(lambda: self.special_char_input.setText('❤'))
            char_input_layout.addWidget(default_btn)
            
            char_input_layout.addStretch()
            special_char_layout.addLayout(char_input_layout)
            
            # Info label
            info_label = QLabel(
                "⚠️ Test your character in-game first!\n"
                "Some symbols may be visible or stripped by the game."
            )
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: red;")
            special_char_layout.addWidget(info_label)
            
            special_char_group.setLayout(special_char_layout)
            layout.addWidget(special_char_group)
            
            # Fancy Text Style
            style_group = QGroupBox("Fancy Text Style")
            style_layout = QVBoxLayout()
            
            style_layout.addWidget(QLabel("Unicode style for fancy text:"))
            
            self.fancy_style_combo = QComboBox()
            styles = ['squared', 'bold', 'italic', 'bold_italic', 'sans_serif', 'circled', 'negative_squared', 'negative_circled']
            style_names = {
                'squared': 'Squared (🄰🄱🄲)',
                'bold': 'Bold (𝐀𝐁𝐂)',
                'italic': 'Italic (𝐴𝐵𝐶)',
                'bold_italic': 'Bold Italic (𝑨𝑩𝑪)',
                'sans_serif': 'Sans Serif (𝖠𝖡𝖢)',
                'circled': 'Circled (Ⓐ Ⓑ Ⓒ)',
                'negative_squared': 'Negative Squared (🅰🅱🅲)',
                'negative_circled': 'Negative Circled (🅐🅑🅒)'
            }
            
            for style in styles:
                self.fancy_style_combo.addItem(style_names[style], style)
            
            current_style = self.config.get('optimization', {}).get('fancy_text_style', 'squared')
            index = self.fancy_style_combo.findData(current_style)
            if index >= 0:
                self.fancy_style_combo.setCurrentIndex(index)
            
            style_layout.addWidget(self.fancy_style_combo)

            # Info label
            style_info_label = QLabel(
                "⚠️ Test your chosen style!\n"
                "Some styles may be unsupported or stripped by the game."
            )
            style_info_label.setWordWrap(True)
            style_info_label.setStyleSheet("color: red;")
            style_layout.addWidget(style_info_label)
            
            style_group.setLayout(style_layout)
            layout.addWidget(style_group)
            
            # Sliding Window Detection
            window_group = QGroupBox("Sliding Window Detection")
            window_layout = QVBoxLayout()
            
            window_layout.addWidget(QLabel("Maximum sliding window size (2-5 words):"))
            
            self.sliding_window_spin = QSpinBox()
            self.sliding_window_spin.setMinimum(2)
            self.sliding_window_spin.setMaximum(5)
            self.sliding_window_spin.setValue(self.config.get('max_sliding_window', 3))
            window_layout.addWidget(self.sliding_window_spin)
            
            window_desc = QLabel(
                "Detects filtered words split across multiple words.\n"
                "Example: 'in fo' contains 'info' (2-word window)\n"
                "Higher values = more detection, slower performance"
            )
            window_desc.setWordWrap(True)
            window_layout.addWidget(window_desc)
            
            window_group.setLayout(window_layout)
            layout.addWidget(window_group)
            
            layout.addStretch()
            widget.setLayout(layout)
            return widget
        
        def create_filter_tab(self):
            """Create Filter List management tab"""
            from PyQt5.QtWidgets import QWidget, QInputDialog
            
            widget = QWidget()
            layout = QVBoxLayout()
            
            # Info label
            info_label = QLabel(
                "Manage your filter word list. Add or remove entries, search, and export.\n"
                "Note: Changes are saved to the filter file when you click Save."
            )
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            # Toggle for displaying unsupported strings
            self.filter_show_unsupported = QCheckBox("Display unsupported strings (non-Latin/CJK)")
            self.filter_show_unsupported.setChecked(False)  # Default to showing supported only
            self.filter_show_unsupported.toggled.connect(self.toggle_filter_display)
            layout.addWidget(self.filter_show_unsupported)
            
            layout.addWidget(QLabel(""))  # Spacer
            
            # Search bar
            search_layout = QHBoxLayout()
            search_layout.addWidget(QLabel("Search:"))
            
            self.filter_search = QLineEdit()
            self.filter_search.setPlaceholderText("Type to filter list...")
            self.filter_search.textChanged.connect(self.filter_search_changed)
            search_layout.addWidget(self.filter_search)
            
            layout.addLayout(search_layout)
            
            # Filter list (scrollable)
            self.filter_list = QListWidget()
            self.filter_list.setSelectionMode(QListWidget.ExtendedSelection)
            self.filter_list.setSortingEnabled(True)
            layout.addWidget(self.filter_list)
            
            # Entry count label (create BEFORE loading)
            self.filter_count_label = QLabel("Loading...")
            layout.addWidget(self.filter_count_label)
            
            # Load filter entries (after label exists)
            self.all_filter_words = []
            self.load_filter_entries()
            
            # Button panel
            btn_layout = QHBoxLayout()
            
            add_btn = QPushButton("Add Entry...")
            add_btn.clicked.connect(self.add_filter_entry)
            btn_layout.addWidget(add_btn)
            
            remove_btn = QPushButton("Remove Selected")
            remove_btn.clicked.connect(self.remove_filter_entries)
            btn_layout.addWidget(remove_btn)
            
            export_btn = QPushButton("Export List...")
            export_btn.clicked.connect(self.export_filter_list)
            btn_layout.addWidget(export_btn)
            
            layout.addLayout(btn_layout)
            
            widget.setLayout(layout)
            return widget
        
        def load_filter_entries(self):
            """Load filter entries from config - both original and filtered"""
            # Get filter file path from config
            filter_file = self.config.get('filter_file', '')
            
            if not filter_file or not os.path.exists(filter_file):
                self.filter_list.addItem("(No filter file loaded)")
                self.all_filter_words_original = []
                self.all_filter_words_supported = []
                return
            
            try:
                with open(filter_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Parse ALL filter words (pre-culled - original file)
                self.all_filter_words_original = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.all_filter_words_original.append(line)
                
                # Filter to Latin-only (post-culled - what's actually used)
                import filter_loader
                loader = filter_loader.FilterLoader()
                self.all_filter_words_supported = []
                for word in self.all_filter_words_original:
                    if loader._is_pure_latin(word):
                        self.all_filter_words_supported.append(word)
                
                # For backwards compatibility
                self.all_filter_words = self.all_filter_words_supported
                
                # Display based on toggle state
                self.update_filter_display()
                
            except Exception as e:
                self.filter_list.addItem(f"Error loading filter file: {e}")
                self.all_filter_words_original = []
                self.all_filter_words_supported = []
        
        def toggle_filter_display(self, checked):
            """Toggle between original and supported filter lists"""
            self.update_filter_display(self.filter_search.text())
        
        def update_filter_display(self, search_text=""):
            """Update filter list display based on search and toggle state"""
            self.filter_list.clear()
            
            # Choose which word list to display
            if hasattr(self, 'filter_show_unsupported') and self.filter_show_unsupported.isChecked():
                # Show unsupported (original/pre-culled list)
                source_words = self.all_filter_words_original
                list_type = "original"
            else:
                # Show supported (filtered/post-culled list) - DEFAULT
                source_words = self.all_filter_words_supported
                list_type = "supported (Latin-only)"
            
            # Filter words based on search
            if search_text:
                filtered_words = [w for w in source_words if search_text.lower() in w.lower()]
            else:
                filtered_words = source_words
            
            # Add to list
            for word in sorted(filtered_words):
                self.filter_list.addItem(word)
            
            # Update count with list type info
            unsupported_count = len(self.all_filter_words_original) - len(self.all_filter_words_supported)
            self.filter_count_label.setText(
                f"Showing {len(filtered_words)} of {len(source_words)} entries ({list_type})\n"
                f"Total: {len(self.all_filter_words_original)} entries "
                f"({len(self.all_filter_words_supported)} supported, {unsupported_count} unsupported)"
            )
        
        def filter_search_changed(self, text):
            """Handle search text change"""
            self.update_filter_display(text)
        
        def add_filter_entry(self):
            """Add new entry to filter list"""
            text, ok = QInputDialog.getText(
                self,
                "Add Filter Entry",
                "Enter word or phrase to add to filter:"
            )
            
            if ok and text:
                text = text.strip().lower()
                
                if not text:
                    return
                
                if text in self.all_filter_words_original:
                    QMessageBox.information(
                        self,
                        "Already Exists",
                        f"'{text}' is already in the filter list."
                    )
                    return
                
                # Add to original list
                self.all_filter_words_original.append(text)
                
                # If it's Latin-only, also add to supported list
                import filter_loader
                loader = filter_loader.FilterLoader()
                if loader._is_pure_latin(text):
                    self.all_filter_words_supported.append(text)
                
                # Update backwards compatibility
                self.all_filter_words = self.all_filter_words_supported
                
                # Update display
                self.update_filter_display(self.filter_search.text())
                
                QMessageBox.information(
                    self,
                    "Entry Added",
                    f"'{text}' added to filter list.\n\nClick Save to apply changes."
                )
        
        def remove_filter_entries(self):
            """Remove selected entries from filter list"""
            selected_items = self.filter_list.selectedItems()
            
            if not selected_items:
                QMessageBox.information(
                    self,
                    "No Selection",
                    "Please select one or more entries to remove."
                )
                return
            
            # Confirm removal
            count = len(selected_items)
            reply = QMessageBox.question(
                self,
                "Confirm Removal",
                f"Remove {count} selected {'entry' if count == 1 else 'entries'}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Remove from both lists
                for item in selected_items:
                    word = item.text()
                    if word in self.all_filter_words_original:
                        self.all_filter_words_original.remove(word)
                    if word in self.all_filter_words_supported:
                        self.all_filter_words_supported.remove(word)
                
                # Update backwards compatibility
                self.all_filter_words = self.all_filter_words_supported
                
                # Update display
                self.update_filter_display(self.filter_search.text())
                
                QMessageBox.information(
                    self,
                    "Entries Removed",
                    f"{count} {'entry' if count == 1 else 'entries'} removed.\n\nClick Save to apply changes."
                )
        
        def export_filter_list(self):
            """Export filter list to file (respects current display toggle)"""
            # Determine which list to export based on toggle
            if hasattr(self, 'filter_show_unsupported') and self.filter_show_unsupported.isChecked():
                export_words = self.all_filter_words_original
                list_type = "original (all strings)"
            else:
                export_words = self.all_filter_words_supported
                list_type = "supported (Latin-only)"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                f"Export Filter List ({list_type})",
                "filter_export.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"# Exported Filter List ({list_type})\n")
                        f.write(f"# Total entries: {len(export_words)}\n\n")
                        for word in sorted(export_words):
                            f.write(f"{word}\n")
                    
                    QMessageBox.information(
                        self,
                        "Export Successful",
                        f"Filter list ({list_type}) exported to:\n{file_path}\n\n{len(export_words)} entries exported."
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Export Failed",
                        f"Failed to export filter list:\n{e}"
                    )
        
        def create_whitelist_tab(self):
            """Create Whitelist management tab"""
            from PyQt5.QtWidgets import QWidget, QInputDialog
            
            widget = QWidget()
            layout = QVBoxLayout()
            
            # Info label with clear explanation
            info_label = QLabel(
                "Manage words that are SAFE when embedded in other words.\n\n"
                "• Whitelisted words are NOT flagged when embedded (e.g., 'ass' in 'assassin')\n"
                "• Standalone instances ARE STILL flagged (e.g., 'ass' by itself)\n"
                "• Use this to prevent false positives for common embedded patterns\n\n"
                "Changes are saved to whitelist.txt when you click Save."
            )
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            # Search bar
            search_layout = QHBoxLayout()
            search_layout.addWidget(QLabel("Search:"))
            
            self.whitelist_search = QLineEdit()
            self.whitelist_search.setPlaceholderText("Type to filter list...")
            self.whitelist_search.textChanged.connect(self.whitelist_search_changed)
            search_layout.addWidget(self.whitelist_search)
            
            layout.addLayout(search_layout)
            
            # Whitelist (scrollable)
            self.whitelist_list = QListWidget()
            self.whitelist_list.setSelectionMode(QListWidget.ExtendedSelection)
            self.whitelist_list.setSortingEnabled(True)
            layout.addWidget(self.whitelist_list)
            
            # Entry count label (create BEFORE loading)
            self.whitelist_count_label = QLabel("Loading...")
            layout.addWidget(self.whitelist_count_label)
            
            # Load whitelist entries (after label exists)
            self.all_whitelist_words = []
            self.load_whitelist_entries()
            
            # Button panel
            btn_layout = QHBoxLayout()
            
            add_btn = QPushButton("Add Entry...")
            add_btn.clicked.connect(self.add_whitelist_entry)
            btn_layout.addWidget(add_btn)
            
            remove_btn = QPushButton("Remove Selected")
            remove_btn.clicked.connect(self.remove_whitelist_entries)
            btn_layout.addWidget(remove_btn)
            
            layout.addLayout(btn_layout)
            
            widget.setLayout(layout)
            return widget
        
        def load_whitelist_entries(self):
            """Load whitelist entries from file"""
            # Get whitelist file path
            import path_manager
            whitelist_file = path_manager.get_data_file('whitelist.txt')
            
            if not os.path.exists(whitelist_file):
                self.whitelist_list.addItem("(No whitelist file found)")
                return
            
            try:
                with open(whitelist_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Parse whitelist words (skip comments and empty lines)
                self.all_whitelist_words = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.all_whitelist_words.append(line)
                
                # Display all words initially
                self.update_whitelist_display()
                
            except Exception as e:
                self.whitelist_list.addItem(f"Error loading whitelist: {e}")
        
        def update_whitelist_display(self, search_text=""):
            """Update whitelist display based on search"""
            self.whitelist_list.clear()
            
            # Filter words based on search
            if search_text:
                filtered_words = [w for w in self.all_whitelist_words if search_text.lower() in w.lower()]
            else:
                filtered_words = self.all_whitelist_words
            
            # Add to list
            for word in sorted(filtered_words):
                self.whitelist_list.addItem(word)
            
            # Update count
            self.whitelist_count_label.setText(
                f"Showing {len(filtered_words)} of {len(self.all_whitelist_words)} entries"
            )
        
        def whitelist_search_changed(self, text):
            """Handle whitelist search text change"""
            self.update_whitelist_display(text)
        
        def add_whitelist_entry(self):
            """Add new entry to whitelist"""
            text, ok = QInputDialog.getText(
                self,
                "Add Whitelist Entry",
                "Enter word that is safe when embedded:\n"
                "(Will NOT be flagged when embedded, but WILL be flagged standalone)"
            )
            
            if ok and text:
                text = text.strip().lower()
                
                if not text:
                    return
                
                if text in self.all_whitelist_words:
                    QMessageBox.information(
                        self,
                        "Already Exists",
                        f"'{text}' is already in the whitelist."
                    )
                    return
                
                # Add to list
                self.all_whitelist_words.append(text)
                self.update_whitelist_display(self.whitelist_search.text())
                
                QMessageBox.information(
                    self,
                    "Entry Added",
                    f"'{text}' added to whitelist.\n\n"
                    "This word will NOT be flagged when embedded in other words,\n"
                    "but WILL still be flagged when standalone.\n\n"
                    "Click Save to apply changes."
                )
        
        def remove_whitelist_entries(self):
            """Remove selected entries from whitelist"""
            selected_items = self.whitelist_list.selectedItems()
            
            if not selected_items:
                QMessageBox.information(
                    self,
                    "No Selection",
                    "Please select one or more entries to remove."
                )
                return
            
            # Confirm removal
            count = len(selected_items)
            reply = QMessageBox.question(
                self,
                "Confirm Removal",
                f"Remove {count} selected {'entry' if count == 1 else 'entries'} from whitelist?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Remove from all_whitelist_words
                for item in selected_items:
                    word = item.text()
                    if word in self.all_whitelist_words:
                        self.all_whitelist_words.remove(word)
                
                # Update display
                self.update_whitelist_display(self.whitelist_search.text())
                
                QMessageBox.information(
                    self,
                    "Entries Removed",
                    f"{count} {'entry' if count == 1 else 'entries'} removed.\n\nClick Save to apply changes."
                )
        
        def create_ui_tab(self):
            """Create UI settings tab"""
            from PyQt5.QtWidgets import QWidget
            
            widget = QWidget()
            layout = QVBoxLayout()
            
            # Theme
            theme_group = QGroupBox("Theme")
            theme_layout = QVBoxLayout()
            
            self.theme_combo = QComboBox()
            self.theme_combo.addItems(["dark", "light"])
            current_theme = self.config.get('ui', {}).get('theme', 'dark')
            self.theme_combo.setCurrentText(current_theme)
            
            # Connect to instantly apply theme changes
            self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
            
            theme_layout.addWidget(QLabel("Color theme:"))
            theme_layout.addWidget(self.theme_combo)
            
            theme_group.setLayout(theme_layout)
            layout.addWidget(theme_group)

            # Sound effects
            sound_group = QGroupBox("Sound Effects")
            sound_layout = QVBoxLayout()
            
            self.notif_sound_check = QCheckBox("Play sound on notifications")
            notif_sound_enabled = self.config.get('ui', {}).get('notification_sound', True)
            self.notif_sound_check.setChecked(notif_sound_enabled)
            sound_layout.addWidget(self.notif_sound_check)
            
            self.prompt_sound_check = QCheckBox("Play sound on prompts")
            prompt_sound_enabled = self.config.get('ui', {}).get('prompt_sound', True)
            self.prompt_sound_check.setChecked(prompt_sound_enabled)
            sound_layout.addWidget(self.prompt_sound_check)
            
            sound_desc = QLabel("Uses system sounds for audio feedback")
            sound_desc.setWordWrap(True)
            sound_layout.addWidget(sound_desc)
            
            sound_group.setLayout(sound_layout)
            layout.addWidget(sound_group)

            # Window positioning
            position_group = QGroupBox("Window Positioning")
            position_layout = QVBoxLayout()
            
            # Notification position preset
            notif_pos_layout = QHBoxLayout()
            notif_pos_label = QLabel("Notification Popups:")
            notif_pos_label.setFixedWidth(150)  # Fixed width for label
            notif_pos_layout.addWidget(notif_pos_label)
            
            self.notif_position_combo = QComboBox()
            self.notif_position_combo.addItems([
                "top-left", "top-center", "top-right",
                "center-left", "center", "center-right",
                "bottom-left", "bottom-center", "bottom-right"
            ])
            current_notif_pos = self.config.get('ui', {}).get('notification_position', 'bottom-right')
            self.notif_position_combo.setCurrentText(current_notif_pos)
            self.notif_position_combo.setFixedWidth(170) #combo fixed width
            notif_pos_layout.addWidget(self.notif_position_combo)
            notif_pos_layout.addStretch()  # Push everything left
            position_layout.addLayout(notif_pos_layout)
            
            # Notification fine-tuning (with dynamic limits based on screen size)
            notif_offset_layout = QHBoxLayout()
            fine_tune_label = QLabel("Fine-tune (X, Y):")
            fine_tune_label.setFixedWidth(150)
            notif_offset_layout.addWidget(fine_tune_label)
            
            # Get screen dimensions for dynamic limits
            from PyQt5.QtWidgets import QDesktopWidget
            desktop = QDesktopWidget()
            screen_rect = desktop.availableGeometry()
            max_x = screen_rect.width()
            max_y = screen_rect.height()
            
            self.notif_offset_x_spin = QSpinBox()
            self.notif_offset_x_spin.setRange(-max_x, max_x)
            self.notif_offset_x_spin.setValue(self.config.get('ui', {}).get('notification_offset_x', 20))
            self.notif_offset_x_spin.setSuffix(" px")
            notif_offset_layout.addWidget(self.notif_offset_x_spin)
            
            self.notif_offset_y_spin = QSpinBox()
            self.notif_offset_y_spin.setRange(-max_y, max_y)
            self.notif_offset_y_spin.setValue(self.config.get('ui', {}).get('notification_offset_y', 20))
            self.notif_offset_y_spin.setSuffix(" px")
            notif_offset_layout.addWidget(self.notif_offset_y_spin)
            notif_offset_layout.addStretch()
            
            position_layout.addLayout(notif_offset_layout)
            
            # Prompt position preset
            prompt_pos_layout = QHBoxLayout()
            prompt_pos_label = QLabel("Prompt Dialogs:")
            prompt_pos_label.setFixedWidth(150)  # Fixed width for label
            prompt_pos_layout.addWidget(prompt_pos_label)
            
            self.prompt_position_combo = QComboBox()
            self.prompt_position_combo.addItems([
                "top-left", "top-center", "top-right",
                "center-left", "center", "center-right",
                "bottom-left", "bottom-center", "bottom-right"
            ])
            current_prompt_pos = self.config.get('ui', {}).get('prompt_position', 'center')
            self.prompt_position_combo.setCurrentText(current_prompt_pos)
            self.prompt_position_combo.setFixedWidth(170) #combo fixed width
            prompt_pos_layout.addWidget(self.prompt_position_combo)
            prompt_pos_layout.addStretch()  # Push everything left
            position_layout.addLayout(prompt_pos_layout)
            
            # Prompt fine-tuning (using same screen dimensions)
            prompt_offset_layout = QHBoxLayout()
            prompt_fine_tune_label = QLabel("Fine-tune (X, Y):")
            prompt_fine_tune_label.setFixedWidth(150)  # Match label width
            prompt_offset_layout.addWidget(prompt_fine_tune_label)
            
            self.prompt_offset_x_spin = QSpinBox()
            self.prompt_offset_x_spin.setRange(-max_x, max_x)
            self.prompt_offset_x_spin.setValue(self.config.get('ui', {}).get('prompt_offset_x', 0))
            self.prompt_offset_x_spin.setSuffix(" px")
            prompt_offset_layout.addWidget(self.prompt_offset_x_spin)
            
            self.prompt_offset_y_spin = QSpinBox()
            self.prompt_offset_y_spin.setRange(-max_y, max_y)
            self.prompt_offset_y_spin.setValue(self.config.get('ui', {}).get('prompt_offset_y', 0))
            self.prompt_offset_y_spin.setSuffix(" px")
            prompt_offset_layout.addWidget(self.prompt_offset_y_spin)
            prompt_offset_layout.addStretch()  # Push everything left
            
            position_layout.addLayout(prompt_offset_layout)
            
            position_group.setLayout(position_layout)
            layout.addWidget(position_group)

            # UI Scaling
            scaling_group = QGroupBox("UI Scaling")
            scaling_layout = QVBoxLayout()
            
            scaling_desc = QLabel("Adjust window and font sizes (0.5 = 50%, 2.0 = 200%)")
            scaling_desc.setWordWrap(True)
            scaling_layout.addWidget(scaling_desc)
            
            # Notification scale
            notif_scale_layout = QHBoxLayout()
            notif_scale_left_label = QLabel("Notification Popups:")
            notif_scale_left_label.setFixedWidth(150)  # Fixed width for alignment
            notif_scale_layout.addWidget(notif_scale_left_label)
            
            self.notif_scale_slider = QSlider(Qt.Horizontal)
            self.notif_scale_slider.setRange(50, 200)  # 0.5 to 2.0 (stored as 50-200)
            current_notif_scale = int(self.config.get('ui', {}).get('notification_scale', 1.0) * 100)
            self.notif_scale_slider.setValue(current_notif_scale)
            self.notif_scale_slider.setTickPosition(QSlider.TicksBelow)
            self.notif_scale_slider.setTickInterval(25)
            self.notif_scale_slider.setFixedWidth(400)  # Fixed width for uniformity
            notif_scale_layout.addWidget(self.notif_scale_slider)
            
            self.notif_scale_label = QLabel(f"{current_notif_scale}%")
            self.notif_scale_label.setFixedWidth(50)  # Fixed width for percentage
            self.notif_scale_label.setAlignment(Qt.AlignRight)  # Right-align the percentage
            notif_scale_layout.addWidget(self.notif_scale_label)
            
            self.notif_scale_slider.valueChanged.connect(
                lambda v: self.notif_scale_label.setText(f"{v}%")
            )
            
            scaling_layout.addLayout(notif_scale_layout)
            
            # Prompt scale
            prompt_scale_layout = QHBoxLayout()
            prompt_scale_left_label = QLabel("Prompt Dialogs:")
            prompt_scale_left_label.setFixedWidth(150)  # Fixed width for alignment
            prompt_scale_layout.addWidget(prompt_scale_left_label)
            
            self.prompt_scale_slider = QSlider(Qt.Horizontal)
            self.prompt_scale_slider.setRange(50, 200)
            current_prompt_scale = int(self.config.get('ui', {}).get('prompt_scale', 1.0) * 100)
            self.prompt_scale_slider.setValue(current_prompt_scale)
            self.prompt_scale_slider.setTickPosition(QSlider.TicksBelow)
            self.prompt_scale_slider.setTickInterval(25)
            self.prompt_scale_slider.setFixedWidth(400)  # Fixed width for uniformity
            prompt_scale_layout.addWidget(self.prompt_scale_slider)
            
            self.prompt_scale_label = QLabel(f"{current_prompt_scale}%")
            self.prompt_scale_label.setFixedWidth(50)  # Fixed width for percentage
            self.prompt_scale_label.setAlignment(Qt.AlignRight)  # Right-align the percentage
            prompt_scale_layout.addWidget(self.prompt_scale_label)
            
            self.prompt_scale_slider.valueChanged.connect(
                lambda v: self.prompt_scale_label.setText(f"{v}%")
            )
            
            scaling_layout.addLayout(prompt_scale_layout)
            
            # Settings window scale
            settings_scale_layout = QHBoxLayout()
            settings_scale_left_label = QLabel("Settings Window:")
            settings_scale_left_label.setFixedWidth(150)  # Fixed width for alignment
            settings_scale_layout.addWidget(settings_scale_left_label)
            
            self.settings_scale_slider = QSlider(Qt.Horizontal)
            self.settings_scale_slider.setRange(50, 200)
            current_settings_scale = int(self.config.get('ui', {}).get('settings_scale', 1.0) * 100)
            self.settings_scale_slider.setValue(current_settings_scale)
            self.settings_scale_slider.setTickPosition(QSlider.TicksBelow)
            self.settings_scale_slider.setTickInterval(25)
            self.settings_scale_slider.setFixedWidth(400)  # Fixed width for uniformity
            settings_scale_layout.addWidget(self.settings_scale_slider)
            
            self.settings_scale_label = QLabel(f"{current_settings_scale}%")
            self.settings_scale_label.setFixedWidth(50)  # Fixed width for percentage
            self.settings_scale_label.setAlignment(Qt.AlignRight)  # Right-align the percentage
            settings_scale_layout.addWidget(self.settings_scale_label)
            
            self.settings_scale_slider.valueChanged.connect(
                lambda v: self.settings_scale_label.setText(f"{v}%")
            )
            
            scaling_layout.addLayout(settings_scale_layout)
            
            # Note about settings scale
            settings_scale_note = QLabel("Note: Settings window scale applies on next open")
            settings_scale_note.setWordWrap(True)
            settings_scale_note.setStyleSheet("font-style: italic; color: gray;")
            scaling_layout.addWidget(settings_scale_note)
            
            scaling_group.setLayout(scaling_layout)
            layout.addWidget(scaling_group)
            
            # Popup Notifications
            popup_group = QGroupBox("Popup Notifications")
            popup_layout = QVBoxLayout()
            
            # Enable/Disable all notifications
            self.notif_enabled = QCheckBox("Enable Notifications")
            notif_enabled = self.config.get('notifications', {}).get('enabled', True)
            self.notif_enabled.setChecked(notif_enabled)
            popup_layout.addWidget(self.notif_enabled)
            
            # Show clean message popups
            self.notif_show_clean = QCheckBox("Show Clean Message Popups")
            show_clean = self.config.get('notifications', {}).get('show_clean_messages', True)
            self.notif_show_clean.setChecked(show_clean)
            popup_layout.addWidget(self.notif_show_clean)
            
            # Show optimized message popups
            self.notif_show_optimized = QCheckBox("Show Optimized Message Popups")
            show_optimized = self.config.get('notifications', {}).get('show_optimized_messages', True)
            self.notif_show_optimized.setChecked(show_optimized)
            popup_layout.addWidget(self.notif_show_optimized)
            
            popup_layout.addWidget(QLabel(""))  # Spacer
            popup_layout.addWidget(QLabel("Popup duration (milliseconds):"))
            popup_layout.addWidget(QLabel("(1000 ms = 1 second, 0 = instant dismiss)"))
            
            self.popup_duration_spin = QSpinBox()
            self.popup_duration_spin.setMinimum(0)
            self.popup_duration_spin.setMaximum(10000)
            self.popup_duration_spin.setSingleStep(100)
            popup_duration = self.config.get('notifications', {}).get('duration_ms', 2000)
            self.popup_duration_spin.setValue(popup_duration)
            popup_layout.addWidget(self.popup_duration_spin)
            
            popup_group.setLayout(popup_layout)
            layout.addWidget(popup_group)
            
            layout.addStretch()
            widget.setLayout(layout)
            return widget
        
        def create_about_tab(self):
            """Create About tab"""
            from PyQt5.QtWidgets import QWidget, QTextEdit
            
            widget = QWidget()
            layout = QVBoxLayout()
            
            # Title
            title = QLabel("Compliant Online Chat Kit")
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            title.setFont(title_font)
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            
            # Version
            version = QLabel("Version 1.0")
            version.setAlignment(Qt.AlignCenter)
            layout.addWidget(version)
            
            # Description
            desc = QTextEdit()
            desc_font = QFont()
            desc_font.setPointSize(12)
            desc.setFont(desc_font)
            desc.setReadOnly(True)
            desc.setMaximumHeight(600)
            desc.setHtml(
                "<b>COCK helps you resolve over-sensitive game chat censorship by:</b><br><br>"
                "• Detecting filtered words before you send messages<br>"
                "• Suggesting & replacing filtered words with optimized alternatives<br>"
                "• Splitting long messages into parts base on in-game chat length and byte size limits<br>"
                "• Simplified one-keypress operation<br>"
                "<br>"
                "<b>FEATURES:</b><br>"
                "<br>"
                "• Efficient and fast Aho-Corasick string matching algorithm (&lt;5ms per message)<br>"
                "• Multi-stage optimization (leet-speak, fancy text, invisible character interspacing, shorthand, message splitting)<br>"
                "• Manual & Automatic modes<br>"
                "• Completely offline and external operation, safe for online games<br>"
                "<br>"
                "<b>DISCLAIMER:</b><br>"
                "<br>"
                "By using this application, you acknowledge:<br>"
                "<br>"
                "• You are resposible for the content of your own online communications <br>"
                "• The author is not liable for any consequences resulting from abuse of the tool"
            )
            layout.addWidget(desc)
            
            # Resources group
            help_group = QGroupBox("Resources")
            help_layout = QVBoxLayout()
            
            # Help text
            help_text = QLabel("Links and documentation:")
            help_text.setWordWrap(True)
            help_layout.addWidget(help_text)
            
            # Button layout (horizontal)
            button_layout = QHBoxLayout()
            
            # Documentation button
            docs_btn = QPushButton("📖 Documentation")
            docs_btn.setToolTip("Open documentation on GitHub")
            docs_btn.clicked.connect(lambda: self._open_help('documentation'))
            
            # Getting Started button
            start_btn = QPushButton("🚀 Getting Started")
            start_btn.setToolTip("Quick start guide")
            start_btn.clicked.connect(lambda: self._open_help('getting_started'))
            
            # Ko-fi button
            kofi_btn = QPushButton("☕ Buy me a coffee")
            kofi_btn.setToolTip("Fuel my caffeine addiction")
            kofi_btn.clicked.connect(lambda: self._open_help('kofi'))
            
            # Report Issue button
            issue_btn = QPushButton("🐞 Feedback")
            issue_btn.setToolTip("Report a bug or request a feature")
            issue_btn.clicked.connect(lambda: self._open_help('new_issue'))
            
            button_layout.addWidget(docs_btn)
            button_layout.addWidget(start_btn)
            button_layout.addWidget(kofi_btn)
            button_layout.addWidget(issue_btn)
            
            help_layout.addLayout(button_layout)
            help_group.setLayout(help_layout)
            layout.addWidget(help_group)
            
            # Credits
            credits = QLabel("Author: Jokoril")
            credits.setAlignment(Qt.AlignCenter)
            layout.addWidget(credits)
            
            layout.addStretch()
            widget.setLayout(layout)
            return widget
        
        def _open_help(self, help_key: str):
            """
            Open help resource
            
            Args:
                help_key: Key for help URL (e.g., 'documentation', 'faq')
            """
            try:
                # Get help manager from parent (main application)
                if hasattr(getattr(self, "main_app", None), 'help_manager'):
                    success = getattr(self, "main_app", None).help_manager.open_url(help_key)
                    if success:
                        print(f"[SETTINGS] Opened help: {help_key}")
                    else:
                        print(f"[SETTINGS] Failed to open help: {help_key}")
                else:
                    print("[SETTINGS] Help manager not available")
                    try:
                        import help_manager
                        QMessageBox.warning(
                            self,
                            "Help Unavailable",
                            "Help system is not available.\n\n"
                            f"Please visit: {help_manager.HelpManager.GITHUB_REPO}"
                        )
                    except:
                        QMessageBox.warning(
                            self,
                            "Help Unavailable",
                            "Help system is not available."
                        )
            except Exception as e:
                print(f"[SETTINGS] Error opening help: {e}")
        
        def browse_filter_file(self):
            """Browse for filter file"""
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Filter Word List",
                "",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                # Validate the path
                try:
                    if not os.path.exists(file_path):
                        QMessageBox.warning(self, "Invalid File", "Selected file does not exist")
                        return
                    if not os.path.isfile(file_path):
                        QMessageBox.warning(self, "Invalid File", "Selected path is not a file")
                        return
                    with open(file_path, 'r', encoding='utf-8') as test_file:
                        test_file.read(100)
                    file_path = os.path.abspath(file_path)
                except PermissionError:
                    QMessageBox.warning(self, "Permission Denied", "Cannot read selected file")
                    return
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Invalid file: {str(e)}")
                    return
                
                self.config['filter_file'] = file_path
                self.filter_path_label.setText(file_path)
                
                # Mark that filter file was changed (will trigger auto-restart)
                if file_path != self.original_filter_file:
                    self.filter_file_changed = True
        
        def open_data_folder(self):
            """Open data folder in file explorer"""
            import subprocess
            import os
            
            # Get app directory (would use path_manager in real app)
            if sys.platform == 'win32':
                data_dir = os.path.join(os.getenv('APPDATA'), 'CompliantOnlineChatKit')
            else:
                data_dir = os.path.expanduser('~/.CompliantOnlineChatKit')
            
            # Create if doesn't exist
            os.makedirs(data_dir, exist_ok=True)
            
            # Open in file explorer
            if sys.platform == 'win32':
                subprocess.Popen(['explorer', data_dir])
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', data_dir])
            else:
                subprocess.Popen(['xdg-open', data_dir])

        def save_settings(self):
            """
            Save settings and emit signal (non-blocking)
            """
            try:
                # Validate hotkeys
                if not self.validate_hotkeys():
                    return  # Don't save if conflict detected

                # Store old values to check what changed
                old_filter_file = self.config.get('filter_file', '')

                # Get updated config from UI
                updated_config = self.get_config()
                
                # Check if settings window scale changed
                old_scale = self.config.get('ui', {}).get('settings_scale', 1.0)
                new_scale = updated_config.get('ui', {}).get('settings_scale', 1.0)
                scale_changed = (abs(old_scale - new_scale) > 0.01)  # Use tolerance for float comparison
                
                # Check if filter file changed
                new_filter_file = updated_config.get('filter_file', '')
                filter_changed = (old_filter_file != new_filter_file)
                
                # Update internal config
                self.config = updated_config
                
                if filter_changed:
                    # Filter file changed - ask if restart needed
                    from PyQt5.QtWidgets import QMessageBox
                    reply = QMessageBox.question(
                        self,
                        "Restart Required",
                        "Filter file has been changed.\n\n"
                        "The application needs to restart to load the new filter.\n\n"
                        "Restart now?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.Yes:
                        # Emit signal with restart=True, then close dialog
                        self.filter_file_changed = True
                        self.settings_saved.emit(True)
                        self.accept()
                        return
                    else:
                        # User declined restart - emit without restart, keep dialog open
                        self.filter_file_changed = False
                        self.settings_saved.emit(False)
                        
                        # Update button to show saved
                        self.save_button.setText("💾 Saved (Restart Pending)")
                        from PyQt5.QtCore import QTimer
                        QTimer.singleShot(3000, lambda: self.save_button.setText("💾 Save Settings"))
                        return
                
                # No restart needed - emit signal and keep dialog open
                self.filter_file_changed = False
                self.settings_saved.emit(False)
                
                # Apply settings window scale immediately if changed
                if scale_changed:
                    print(f"[SETTINGS] Scale changed: {old_scale} → {new_scale}")
                    self.apply_settings_scale(new_scale)
                
                # Update button to show saved
                self.save_button.setText("💾 Saved!")
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(2000, lambda: self.save_button.setText("💾 Save Settings"))
                
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    "Error Saving Settings",
                    f"Failed to save settings:\n{str(e)}",
                    QMessageBox.Ok
                )

        def get_config(self):
            """
            Get updated configuration
            
            Returns:
                dict: Updated configuration dictionary
            """
            # Update config from UI
            self.config['detection_mode'] = self.mode_combo.currentText()
            
            # Get hotkeys from recorders
            self.config['hotkey'] = self.hotkey_recorder.get_hotkey() if self.hotkey_recorder.get_hotkey() else 'f12'
            self.config['force_optimize_hotkey'] = self.force_hotkey_recorder.get_hotkey() if self.force_hotkey_recorder.get_hotkey() else 'ctrl+f12'
            self.config['toggle_hotkeys_hotkey'] = self.toggle_hotkey_recorder.get_hotkey() if self.toggle_hotkey_recorder.get_hotkey() else 'ctrl+shift+h'
            
            # Optimization settings
            if 'optimization' not in self.config:
                self.config['optimization'] = {}
            
            self.config['optimization']['leet_speak'] = self.leet_enabled.isChecked()
            self.config['optimization']['fancy_unicode'] = self.unicode_enabled.isChecked()
            self.config['optimization']['shorthand'] = self.shorthand_enabled.isChecked()
            self.config['optimization']['link_protection'] = self.link_protection.isChecked()
            self.config['optimization']['special_char_interspacing'] = self.special_char_enabled.isChecked()
            
            # Fancy text style
            selected_style = self.fancy_style_combo.currentData()
            if selected_style:
                self.config['optimization']['fancy_text_style'] = selected_style
            
            # Sliding window
            self.config['max_sliding_window'] = self.sliding_window_spin.value()
            
            # Special char interspacing settings
            if 'special_char_interspacing' not in self.config:
                self.config['special_char_interspacing'] = {}
            
            special_char = self.special_char_input.text()
            if special_char and len(special_char) == 1:
                self.config['special_char_interspacing']['character'] = special_char
            else:
                self.config['special_char_interspacing']['character'] = '❤'  # Default
            
            # UI settings
            if 'ui' not in self.config:
                self.config['ui'] = {}
            
            self.config['ui']['theme'] = self.theme_combo.currentText()
            self.config['ui']['notification_position'] = self.notif_position_combo.currentText()
            self.config['ui']['prompt_position'] = self.prompt_position_combo.currentText()
            self.config['ui']['notification_offset_x'] = self.notif_offset_x_spin.value()
            self.config['ui']['notification_offset_y'] = self.notif_offset_y_spin.value()
            self.config['ui']['prompt_offset_x'] = self.prompt_offset_x_spin.value()
            self.config['ui']['prompt_offset_y'] = self.prompt_offset_y_spin.value()
            self.config['ui']['notification_scale'] = self.notif_scale_slider.value() / 100.0
            self.config['ui']['prompt_scale'] = self.prompt_scale_slider.value() / 100.0
            self.config['ui']['settings_scale'] = self.settings_scale_slider.value() / 100.0
            self.config['ui']['notification_sound'] = self.notif_sound_check.isChecked()
            self.config['ui']['prompt_sound'] = self.prompt_sound_check.isChecked()
            
            # Notification settings
            if 'notifications' not in self.config:
                self.config['notifications'] = {}
            
            self.config['notifications']['enabled'] = self.notif_enabled.isChecked()
            self.config['notifications']['show_clean_messages'] = self.notif_show_clean.isChecked()
            self.config['notifications']['show_optimized_messages'] = self.notif_show_optimized.isChecked()
            self.config['notifications']['duration_ms'] = self.popup_duration_spin.value()
            
            # Message limits (0 = no limit, convert to high value)
            byte_limit = self.byte_limit_spin.value()
            char_limit = self.char_limit_spin.value()
            
            self.config['byte_limit'] = byte_limit if byte_limit > 0 else 9999
            self.config['character_limit'] = char_limit if char_limit > 0 else 9999
            
            # Save filter list changes if modified (save ORIGINAL list, not filtered)
            if hasattr(self, 'all_filter_words_original') and self.all_filter_words_original:
                filter_file = self.config.get('filter_file', '')
                if filter_file and os.path.exists(filter_file):
                    try:
                        with open(filter_file, 'w', encoding='utf-8') as f:
                            f.write("# COCK Filter List\n")
                            f.write(f"# Total entries: {len(self.all_filter_words_original)}\n")
                            f.write(f"# Supported (Latin-only): {len(self.all_filter_words_supported)}\n\n")
                            for word in sorted(self.all_filter_words_original):
                                f.write(f"{word}\n")
                    except Exception as e:
                        print(f"WARNING: Failed to save filter list: {e}")
            
            # Save whitelist changes if modified
            if hasattr(self, 'all_whitelist_words') and self.all_whitelist_words is not None:
                import path_manager
                whitelist_file = path_manager.get_data_file('whitelist.txt')
                try:
                    with open(whitelist_file, 'w', encoding='utf-8') as f:
                        f.write("# Whitelist - Words safe when embedded\n")
                        f.write("# These words are NOT flagged when found embedded in larger words\n")
                        f.write("# Example: 'ass' is safe in 'assassin' but flagged when standalone\n\n")
                        for word in sorted(self.all_whitelist_words):
                            f.write(f"{word}\n")
                except Exception as e:
                    print(f"WARNING: Failed to save whitelist: {e}")
            
            # Update settings
            if 'updates' not in self.config:
                self.config['updates'] = {}
            
            self.config['updates']['check_enabled'] = self.check_updates_cb.isChecked()
            # Preserve last_check timestamp (managed by update_checker)
            if 'last_check' not in self.config['updates']:
                self.config['updates']['last_check'] = None
            
            return self.config

        def on_theme_changed(self, theme):
            """Handle theme change from combo box - apply immediately"""
            # Update internal config
            if 'ui' not in self.config:
                self.config['ui'] = {}
            self.config['ui']['theme'] = theme
            
            # Apply theme immediately
            self.apply_theme()
        
        def apply_settings_scale(self, new_scale):
            """Apply new scale to settings window immediately"""
            try:
                print(f"[SETTINGS] Applying scale: {new_scale}")
                
                # Calculate new window size
                base_width = 600  # Minimum width from init_ui
                base_height = 500  # Minimum height from init_ui
                
                new_width = int(base_width * new_scale)
                new_height = int(base_height * new_scale)
                
                print(f"[SETTINGS] Resizing window: {self.width()}x{self.height()} → {new_width}x{new_height}")
                self.resize(new_width, new_height)
                
                # Update font scaling
                if new_scale != 1.0:
                    font = self.font()
                    base_size = 9  # Default Qt font size
                    new_size = int(base_size * new_scale)
                    font.setPointSize(new_size)
                    self.setFont(font)
                    print(f"[SETTINGS] Font size: {base_size} → {new_size}")
                else:
                    # Reset to default font
                    from PyQt5.QtWidgets import QApplication
                    self.setFont(QApplication.font())
                    print(f"[SETTINGS] Font reset to default")
                
                print(f"[SETTINGS] Scale applied successfully")
                
            except Exception as e:
                print(f"[SETTINGS] ERROR applying scale: {e}")
                import traceback
                traceback.print_exc()
        
        def update_mode_display(self, mode_name):
            """Update mode combo box display (called from main.py when mode changes externally)"""
            # Block signals to prevent triggering on_settings_saved
            self.mode_combo.blockSignals(True)
            self.mode_combo.setCurrentText(mode_name)
            self.mode_combo.blockSignals(False)
        
        def apply_settings_scale(self, scale):
            """Apply new scale to settings window immediately"""
            # Update window size
            current_width = self.width()
            current_height = self.height()
            
            # Calculate new size based on scale change
            old_scale = self.config.get('ui', {}).get('settings_scale', 1.0)
            scale_ratio = scale / old_scale
            
            new_width = int(current_width * scale_ratio)
            new_height = int(current_height * scale_ratio)
            
            self.resize(new_width, new_height)
            
            # Update font scaling
            if scale != 1.0:
                font = self.font()
                base_size = 9  # Default Qt font size
                font.setPointSize(int(base_size * scale))
                self.setFont(font)
            else:
                # Reset to default font
                from PyQt5.QtWidgets import QApplication
                self.setFont(QApplication.font())
            
            print(f"[SETTINGS] Applied scale {scale} (was {old_scale})")
        
        def apply_theme(self):
            """Apply dark or light theme to settings dialog"""
            theme = self.config.get('ui', {}).get('theme', 'dark')
            
            if theme == 'dark':
                self.setStyleSheet("""
                    QDialog {
                        background-color: #2b2b2b;
                        color: #ffffff;
                        border: 1px solid #555555;
                    }
                    
                    /* Custom title bar */
                    QWidget#titleBar {
                        background-color: #FFB24D;
                        border-bottom: 1px solid #555555;
                    }
                    QLabel#titleLabel {
                        color: #000000;
                        padding-left: 5px;
                    }
                    QPushButton#minButton, QPushButton#maxButton {
                        background-color: transparent;
                        color: #000000;
                        border: none;
                        font-size: 16px;
                    }
                    QPushButton#minButton:hover, QPushButton#maxButton:hover {
                        background-color: #FFD391;
                    }
                    QPushButton#closeButton {
                        background-color: transparent;
                        color: #000000;
                        border: none;
                        font-size: 16px;
                    }
                    QPushButton#closeButton:hover {
                        background-color: #e81123;
                        color: #FFD391;
                    }
                    
                    QTabWidget::pane {
                        border: 1px solid #555555;
                        background-color: #2b2b2b;
                    }
                    QTabBar::tab {
                        background-color: #3c3c3c;
                        color: #ffffff;
                        border: 1px solid #555555;
                        padding: 8px 20px;
                        margin-right: 2px;
                    }
                    QTabBar::tab:selected {
                        background-color: #4a4a4a;
                        border-bottom-color: #FFB24D;
                    }
                    QGroupBox {
                        border: 1px solid #555555;
                        border-radius: 4px;
                        margin-top: 8px;
                        padding-top: 8px;
                        font-weight: bold;
                        color: #ffffff;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 8px;
                        padding: 0 4px;
                    }
                    QLabel {
                        color: #ffffff;
                    }
                    QLineEdit, QSpinBox, QComboBox {
                        background-color: #3c3c3c;
                        border: 1px solid #555555;
                        border-radius: 4px;
                        padding: 4px;
                        color: #ffffff;
                    }
                    QTextEdit {
                        background-color: #3c3c3c;
                        border: 1px solid #555555;
                        border-radius: 4px;
                        color: #ffffff;
                    }
                    QPushButton {
                        background-color: #4CAF50;
                        color: black;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                    QPushButton:pressed {
                        background-color: #3d8b40;
                    }
                    QCheckBox {
                        color: #ffffff;
                    }
                    QRadioButton {
                        color: #ffffff;
                    }
                    QSlider::groove:horizontal {
                        border: 1px solid #555555;
                        height: 8px;
                        background: #3c3c3c;
                        border-radius: 4px;
                    }
                    QSlider::handle:horizontal {
                        background: #4CAF50;
                        border: 1px solid #555555;
                        width: 18px;
                        margin: -5px 0;
                        border-radius: 9px;
                    }
                """)
            else:  # light theme
                self.setStyleSheet("""
                    QDialog {
                        background-color: #ffffff;
                        color: #000000;
                        border: 1px solid #cccccc;
                    }
                    
                    /* Custom title bar */
                    QWidget#titleBar {
                        background-color: #FFB24D;
                        border-bottom: 1px solid #cccccc;
                    }
                    QLabel#titleLabel {
                        color: #000000;
                        padding-left: 5px;
                    }
                    QPushButton#minButton, QPushButton#maxButton {
                        background-color: transparent;
                        color: #000000;
                        border: none;
                        font-size: 16px;
                    }
                    QPushButton#minButton:hover, QPushButton#maxButton:hover {
                        background-color: #e0e0e0;
                    }
                    QPushButton#closeButton {
                        background-color: transparent;
                        color: #000000;
                        border: none;
                        font-size: 16px;
                    }
                    QPushButton#closeButton:hover {
                        background-color: #e81123;
                        color: #ffffff;
                    }
                    
                    QTabWidget::pane {
                        border: 1px solid #cccccc;
                        background-color: #ffffff;
                    }
                    QTabBar::tab {
                        background-color: #f0f0f0;
                        color: #000000;
                        border: 1px solid #cccccc;
                        padding: 8px 16px;
                        margin-right: 2px;
                    }
                    QTabBar::tab:selected {
                        background-color: #FFD391;
                        border-bottom-color: #ffffff;
                    }
                    QGroupBox {
                        border: 1px solid #cccccc;
                        border-radius: 4px;
                        margin-top: 8px;
                        padding-top: 8px;
                        font-weight: bold;
                    }
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                    QSlider::groove:horizontal {
                        border: 1px solid #cccccc;
                        height: 8px;
                        background: #f0f0f0;
                        border-radius: 4px;
                    }
                    QSlider::handle:horizontal {
                        background: #4CAF50;
                        border: 1px solid #cccccc;
                        width: 18px;
                        margin: -5px 0;
                        border-radius: 9px;
                    }
                """)
                
else:
    # Dummy class when PyQt5 not available
    class SettingsDialog:
        """Dummy settings dialog for testing without PyQt5"""
        def __init__(self, config, filter_stats=None):
            self.config = config
        
        def exec_(self):
            print("[Settings Dialog - PyQt5 not available]")
            return False
        
        def get_config(self):
            return self.config


# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
