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

Note:
    Tab components are extracted to COCK/ui/settings/ for maintainability.
    This file coordinates the tabs and handles dialog-level logic.
"""

import sys
import os
import path_manager

try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
        QLabel, QPushButton, QFileDialog,
        QMessageBox, QApplication, QWidget
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QFont
    PYQT5_AVAILABLE = True
except ImportError:
    print("WARNING: PyQt5 not installed. Install with: pip install PyQt5")
    PYQT5_AVAILABLE = False
    class QDialog: pass

# Import HotkeyRecorder widget (for backwards compatibility - used by main.py)
if PYQT5_AVAILABLE:
    from ui.widgets.hotkey_recorder import HotkeyRecorder

# Import tab creation functions
from ui.settings import (
    create_general_tab,
    create_optimization_tab,
    create_filter_tab,
    create_whitelist_tab,
    create_ui_tab,
    create_about_tab,
    validate_hotkeys as _validate_hotkeys,
    browse_filter_file as _browse_filter_file,
    open_data_folder as _open_data_folder,
    open_help as _open_help,
    load_filter_entries as _load_filter_entries,
)


if PYQT5_AVAILABLE:
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

            # Setup file watcher for filter file (v1.2)
            self._setup_filter_file_watcher()

        def _setup_filter_file_watcher(self):
            """Setup QFileSystemWatcher for filter file auto-refresh (v1.2)"""
            from PyQt5.QtCore import QFileSystemWatcher
            self._filter_watcher = QFileSystemWatcher(self)
            filter_file = self.config.get('filter_file', '')
            if filter_file and os.path.exists(filter_file):
                self._filter_watcher.addPath(filter_file)
                self._filter_watcher.fileChanged.connect(self._on_filter_file_changed)

        def _on_filter_file_changed(self, path):
            """Handle filter file external change (v1.2)"""
            # Re-add path (QFileSystemWatcher removes it after change on some platforms)
            if os.path.exists(path) and path not in self._filter_watcher.files():
                self._filter_watcher.addPath(path)

            # Reload filter entries if we have the method
            if hasattr(self, 'load_filter_entries'):
                self.load_filter_entries()

        def showEvent(self, event):
            """Refresh filter list when dialog is shown (v1.2)"""
            super().showEvent(event)
            # Reload filter entries to pick up external changes
            if hasattr(self, 'load_filter_entries'):
                self.load_filter_entries()
        
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
            
            # Create tabs using extracted tab functions
            self.tabs.addTab(create_general_tab(self), "General")
            self.tabs.addTab(create_optimization_tab(self), "Optimization")
            self.tabs.addTab(create_filter_tab(self), "Filter List")
            self.tabs.addTab(create_whitelist_tab(self), "Whitelist")
            self.tabs.addTab(create_ui_tab(self), "UI")
            self.tabs.addTab(create_about_tab(self), "About")
            
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
            """Check for hotkey conflicts - delegates to extracted function"""
            return _validate_hotkeys(self)

        def load_filter_entries(self):
            """Load filter entries - delegates to extracted function"""
            _load_filter_entries(self)

        def _open_help(self, help_key: str):
            """Open help resource - delegates to extracted function"""
            _open_help(self, help_key)
        
        def browse_filter_file(self):
            """Browse for filter file - delegates to extracted function"""
            _browse_filter_file(self)

        def open_data_folder(self):
            """Open data folder in file explorer - delegates to extracted function"""
            _open_data_folder(self)

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

                # Refresh filter list to show current state (v1.2)
                if hasattr(self, 'load_filter_entries'):
                    self.load_filter_entries()

                # Reset filter modified flag after save (v1.2)
                self._filter_modified = False

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
            
            # Save filter list changes ONLY if user modified via UI (v1.2 fix)
            # This prevents overwriting external changes to the filter file
            if getattr(self, '_filter_modified', False) and hasattr(self, 'all_filter_words_original'):
                filter_file = self.config.get('filter_file', '')
                if filter_file and os.path.exists(filter_file):
                    try:
                        with open(filter_file, 'w', encoding='utf-8') as f:
                            f.write("# COCK Filter List\n")
                            f.write(f"# Total entries: {len(self.all_filter_words_original)}\n")
                            f.write(f"# Supported (Latin-only): {len(self.all_filter_words_supported)}\n\n")
                            for word in sorted(self.all_filter_words_original):
                                f.write(f"{word}\n")
                        print(f"Filter list saved ({len(self.all_filter_words_original)} entries)")
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
