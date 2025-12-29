#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Overlay - Manual Mode UI
=========================
Always-on-top overlay window for Manual mode detection results

Features:
- Shows detected filtered words
- Displays optimization suggestions
- [Use Suggestion] and [Cancel] buttons
- Auto-dismiss option
- Dark/Light theme support

Usage:
    from overlay_manual import ManualModeOverlay
    
    overlay = ManualModeOverlay(config)
    overlay.show_detection(original, flagged_words, suggested)
"""

try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QListWidget, QListWidgetItem, QGroupBox
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QFont, QIcon
    PYQT5_AVAILABLE = True
except ImportError:
    print("WARNING: PyQt5 not installed. Install with: pip install PyQt5")
    PYQT5_AVAILABLE = False
    # Create dummy classes for testing without PyQt5
    class QDialog: pass
    class pyqtSignal: 
        def __init__(self, *args): pass
        def emit(self, *args): pass
try:
    from PyQt5.QtMultimedia import QSound
    QSOUND_AVAILABLE = True
except ImportError:
    QSOUND_AVAILABLE = False
    print("WARNING: QSound not available (install PyQt5.QtMultimedia)")


if PYQT5_AVAILABLE:
    class ManualModeOverlay(QDialog):
        """
        Manual Mode overlay window
        
        Shows detection results and awaits user action:
        - Add individual words to whitelist
        - Use the suggested optimization
        - Cancel and edit message manually
        """
        
        # Signals
        use_suggestion = pyqtSignal()       # Emitted when user accepts suggestion
        cancelled = pyqtSignal()            # Emitted when user cancels
        
        def __init__(self, config: dict):
            """
            Initialize strict mode overlay
            
            Args:
                config: Configuration dictionary
            """
            super().__init__()
            
            self.config = config
            self.original_text = ""
            self.suggested_text = ""
            self.flagged_words = []
            
            # Get theme from config
            self.theme = config.get('ui', {}).get('theme', 'dark')
            
            self.init_ui()
        
        def init_ui(self):
            """Initialize the user interface"""
            # Get scaling factor
            scale = self.config.get('ui', {}).get('prompt_scale', 1.0)
            
            # Calculate scaled font sizes
            base_font_size = 9  # Qt default
            scaled_font_size = int(base_font_size * scale)
            title_font_size = int(12 * scale)
            
            # Window properties
            self.setWindowTitle("COCK Profanity Processor - Detection")
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            
            # Apply scaling to all elements
            self.setMinimumWidth(int(450 * scale))
            self.setMaximumWidth(int(600 * scale))
            
            # Main layout
            layout = QVBoxLayout()
            layout.setSpacing(int(12 * scale))
            layout.setContentsMargins(
                int(16 * scale), 
                int(16 * scale), 
                int(16 * scale), 
                int(16 * scale)
            )
            
            # Create scaled font for all text elements
            text_font = QFont()
            text_font.setPointSize(scaled_font_size)
            
            # Title
            title = QLabel("⚠ Filtered Words Detected")
            title_font = QFont()
            title_font.setPointSize(title_font_size)
            title_font.setBold(True)
            title.setFont(title_font)
            layout.addWidget(title)
            
            # Detected words section
            words_group = QGroupBox("Detected Words")
            words_group.setFont(text_font)  # Scale group box title
            words_layout = QVBoxLayout()
            
            self.words_list = QListWidget()
            self.words_list.setFont(text_font)  # Scale list items
            self.words_list.setMaximumHeight(int(150 * scale))
            words_layout.addWidget(self.words_list)
            
            words_group.setLayout(words_layout)
            layout.addWidget(words_group)
            
            # Original message section
            original_group = QGroupBox("Original Message")
            original_group.setFont(text_font)  # Scale group box title
            original_layout = QVBoxLayout()
            
            self.original_label = QLabel()
            self.original_label.setFont(text_font)  # Scale message text
            self.original_label.setWordWrap(True)
            self.original_label.setMaximumHeight(int(80 * scale))
            original_layout.addWidget(self.original_label)
            
            original_group.setLayout(original_layout)
            layout.addWidget(original_group)
            
            # Suggestion section
            suggestion_group = QGroupBox("Suggested Optimization")
            suggestion_group.setFont(text_font)  # Scale group box title
            suggestion_layout = QVBoxLayout()
            
            self.suggestion_label = QLabel()
            self.suggestion_label.setFont(text_font)  # Scale suggestion text
            self.suggestion_label.setWordWrap(True)
            self.suggestion_label.setMaximumHeight(int(80 * scale))
            suggestion_layout.addWidget(self.suggestion_label)
            
            self.copy_btn = QPushButton("📋 Copy to Clipboard")
            self.copy_btn.setFont(text_font)  # Scale button text
            self.copy_btn.setMinimumHeight(int(32 * scale))  # Scale button height
            self.copy_btn.clicked.connect(self.copy_suggestion)
            self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2196F3;
                color: white;
                padding: {int(8 * scale)}px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1976D2;
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD;
                color: #757575;
            }}
            """)
            suggestion_layout.addWidget(self.copy_btn)
            
            suggestion_group.setLayout(suggestion_layout)
            layout.addWidget(suggestion_group)
            
            # Action buttons
            button_layout = QHBoxLayout()
            
            self.use_btn = QPushButton("✓ Use Suggestion")
            self.use_btn.setFont(text_font)  # Scale button text
            self.use_btn.setMinimumHeight(int(40 * scale))  # Scale button height
            self.use_btn.clicked.connect(self.on_use_suggestion)
            self.use_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #4CAF50;
                color: white;
                padding: {int(8 * scale)}px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #45a049;
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD;
                color: #757575;
            }}
            """)
            button_layout.addWidget(self.use_btn)
            
            self.cancel_btn = QPushButton("✗ Cancel")
            self.cancel_btn.setFont(text_font)  # Scale button text
            self.cancel_btn.setMinimumHeight(int(40 * scale))  # Scale button height
            self.cancel_btn.clicked.connect(self.on_cancel)
            self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f44336;
                color: white;
                padding: {int(8 * scale)}px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #C6372D;
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD;
                color: #757575;
            }}
            """)
            button_layout.addWidget(self.cancel_btn)
            
            layout.addLayout(button_layout)
            
            self.setLayout(layout)
            
            # Apply theme
            self.apply_theme()

        def on_copy_clicked(self):
            """Handle copy button click"""
            print("[OVERLAY] Copy button clicked!")
            import pyperclip
            pyperclip.copy(self.suggested_text)
        
        def apply_theme(self):
            """Apply dark or light theme"""
            if self.theme == 'dark':
                self.setStyleSheet("""
                    QDialog {
                        background-color: #2b2b2b;
                        color: #ffffff;
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
                        color: #ffffff;
                    }
                    QListWidget {
                        background-color: #3c3c3c;
                        border: 1px solid #555555;
                        border-radius: 4px;
                        padding: 4px;
                        color: #ffffff;
                    }
                    QListWidgetItem {
                        color: #ffffff;
                    }
                    QLabel {
                        background-color: #3c3c3c;
                        border: 1px solid #555555;
                        border-radius: 4px;
                        padding: 8px;
                        color: #ffffff;
                    }
                    QPushButton {
                        border-radius: 4px;
                        padding: 6px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        opacity: 0.8;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QDialog {
                        background-color: #ffffff;
                        color: #000000;
                    }
                    QGroupBox {
                        border: 1px solid #cccccc;
                        border-radius: 4px;
                        margin-top: 8px;
                        padding-top: 8px;
                        font-weight: bold;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 8px;
                        padding: 0 4px;
                    }
                    QListWidget {
                        background-color: #f5f5f5;
                        border: 1px solid #cccccc;
                        border-radius: 4px;
                        padding: 4px;
                    }
                    QLabel {
                        background-color: #f5f5f5;
                        border: 1px solid #cccccc;
                        border-radius: 4px;
                        padding: 8px;
                    }
                    QPushButton {
                        border-radius: 4px;
                        padding: 6px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        opacity: 0.8;
                    }
                """)
        
        def show_detection(self, original: str, flagged_words: list, suggested: str = None):
            """
            Show detection results
            
            Args:
                original: Original message text
                flagged_words: List of detected words
                suggested: Suggested optimized version (optional)
            """
            print(f"[OVERLAY DEBUG] show_detection called with {len(flagged_words)} words")
            
            self.original_text = original
            self.flagged_words = flagged_words
            
            # Update UI
            self.original_label.setText(original)
            
            # Check if suggestion is provided and different from original
            if suggested and suggested.strip() and suggested.lower() != original.lower():
                self.suggested_text = suggested
                self.suggestion_label.setText(suggested)
                self.use_btn.setEnabled(True)
                self.copy_btn.setEnabled(True)
            else:
                # No suggestion available
                self.suggested_text = ""
                self.suggestion_label.setText("(No optimization available)")
                self.use_btn.setEnabled(False)
                self.copy_btn.setEnabled(False)
            
            # Populate words list
            self.words_list.clear()
            for word in flagged_words:
                item = QListWidgetItem(f"• {word}")
                self.words_list.addItem(item)
            
            print(f"[OVERLAY DEBUG] UI updated, about to show window")
            
            # Make absolutely sure window is visible
            self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
            
            # Position based on config with fine-tuning
            try:
                from PyQt5.QtWidgets import QApplication
                screen = QApplication.primaryScreen().geometry()
                position = self.config.get('ui', {}).get('prompt_position', 'center')
                offset_x = self.config.get('ui', {}).get('prompt_offset_x', 0)
                offset_y = self.config.get('ui', {}).get('prompt_offset_y', 0)
                
                # Calculate position (with 9 presets)
                if position == 'top-left':
                    x = 20 + offset_x
                    y = 20 + offset_y
                elif position == 'top-center':
                    x = (screen.width() - self.width()) // 2 + offset_x
                    y = 20 + offset_y
                elif position == 'top-right':
                    x = screen.width() - self.width() - 20 + offset_x
                    y = 20 + offset_y
                elif position == 'center-left':
                    x = 20 + offset_x
                    y = (screen.height() - self.height()) // 2 + offset_y
                elif position == 'center':
                    x = (screen.width() - self.width()) // 2 + offset_x
                    y = (screen.height() - self.height()) // 2 + offset_y
                elif position == 'center-right':
                    x = screen.width() - self.width() - 20 + offset_x
                    y = (screen.height() - self.height()) // 2 + offset_y
                elif position == 'bottom-left':
                    x = 20 + offset_x
                    y = screen.height() - self.height() - 60 + offset_y
                elif position == 'bottom-center':
                    x = (screen.width() - self.width()) // 2 + offset_x
                    y = screen.height() - self.height() - 60 + offset_y
                elif position == 'bottom-right':
                    x = screen.width() - self.width() - 20 + offset_x
                    y = screen.height() - self.height() - 60 + offset_y
                else:  # fallback to center
                    x = (screen.width() - self.width()) // 2 + offset_x
                    y = (screen.height() - self.height()) // 2 + offset_y
                
                self.move(x, y)
                print(f"[OVERLAY DEBUG] Window positioned at {x}, {y}")
            except Exception as e:
                print(f"[OVERLAY DEBUG] Failed to center: {e}")

            # Play prompt sound if enabled
            if self.config.get('ui', {}).get('prompt_sound', True):
                try:
                    import winsound
                    import os
                    import path_manager
                    
                    # Build path to prompt sound file (works in both dev and .exe)
                    sound_file = path_manager.get_resource_file('sounds/prompt.wav')
                    
                    # Play custom sound if file exists, otherwise system beep
                    if os.path.exists(sound_file):
                        winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    else:
                        winsound.MessageBeep(winsound.MB_OK)
                        
                except Exception as e:
                    print(f"[OVERLAY] Could not play sound: {e}")
            
            # FORCE window to be visible with multiple methods
            self.setVisible(True)
            self.show()
            self.raise_()
            self.activateWindow()
            self.setFocus()
            
            # Force window to front on Windows
            try:
                self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
                self.show()  # Need to show again after changing flags
                self.raise_()
                self.activateWindow()
            except Exception as e:
                print(f"[OVERLAY DEBUG] Failed to set always on top: {e}")
            
            # Force repaint
            self.repaint()
            
            print(f"[OVERLAY DEBUG] Window shown - isVisible={self.isVisible()}, isActiveWindow={self.isActiveWindow()}")
            
            # Try Windows-specific method to force to foreground
            try:
                import ctypes
                hwnd = int(self.winId())
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                print(f"[OVERLAY DEBUG] SetForegroundWindow called")
            except Exception as e:
                print(f"[OVERLAY DEBUG] SetForegroundWindow failed: {e}")
        
        def copy_suggestion(self):
            """Copy suggested text to clipboard"""
            try:
                from PyQt5.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setText(self.suggested_text)
            except:
                pass
        
        def on_use_suggestion(self):
            """User clicked Use Suggestion"""
            print("[OVERLAY] Use Suggestion button clicked!")
            print(f"[OVERLAY] Emitting signal with suggested text: '{self.suggested_text}'")
            self.use_suggestion.emit()
            self.accept()

        def on_cancel(self):
            """User clicked Cancel"""
            print("[OVERLAY] Cancel button clicked!")
            self.cancelled.emit()
            self.reject()
else:
    # Dummy class when PyQt5 not available
    class ManualModeOverlay:
        """Dummy overlay for testing without PyQt5"""
        def __init__(self, config):
            self.config = config
        
        def show_detection(self, original, flagged_words, suggested=None):
            print(f"[Manual Mode Overlay - PyQt5 not available]")
            print(f"Original: {original}")
            print(f"Flagged: {flagged_words}")
            print(f"Suggested: {suggested}")


# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
