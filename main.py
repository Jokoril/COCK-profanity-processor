#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COCK Profanity Processor - Main Application
====================================
Compliant Online Chat Kit - Profanity Processor and Online Chat Optimization Tool

Features:
- Global hotkey detection
- Real-time message analysis
- Multi-stage optimization
- Strict & Permissive modes
- System tray integration

Usage:
    python main.py              # Run normally
    python main.py --debug      # Run with debug output
    python main.py --help       # Show help
"""

import sys
import os
import argparse
import traceback
from typing import Optional

# Fix Windows console encoding for Unicode characters (heart emoji, fancy text, etc.)
if sys.platform == 'win32':
    import io
    # Only wrap stdout/stderr if they exist (they're None when console=False in .exe)
    if sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr is not None and hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add COCK directory to path (all modules are in COCK folder)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'COCK'))

# Import Phase 1 modules
import constants
import path_manager
import permission_manager
import config_loader
import filter_loader
import clipboard_manager
import hotkey_handler

# Import Phase 2 modules
import fast_detector
import whitelist_manager

# Import Phase 3 modules
import leet_speak
import fancy_text
import shorthand_handler
import message_optimizer
import mode_router

# Import Phase 4 modules (with graceful fallback)
import overlay_manual  # Renamed from overlay_strict
# overlay_permissive removed - no longer used (replaced with auto mode)
import settings_dialog

# Import Phase 5 modules (update and help systems)
import update_checker
import help_manager

# For console window control on Windows
if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes

# Check PyQt5 availability
try:
    from PyQt5.QtWidgets import (
        QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox, 
        QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit
    )
    from PyQt5.QtGui import QIcon, QFont
    from PyQt5.QtCore import QObject, pyqtSignal, QTimer, Qt
    PYQT5_AVAILABLE = True
except ImportError:
    print("WARNING: PyQt5 not installed. Install with: pip install PyQt5")
    print("Running in console mode without GUI...")
    PYQT5_AVAILABLE = False

def check_single_instance():
    """Ensure only one instance of the app is running"""
    import sys
    import os
    import ctypes
    
    if sys.platform == 'win32':
        # Windows: Use named mutex
        from ctypes import wintypes
        
        kernel32 = ctypes.windll.kernel32
        CreateMutex = kernel32.CreateMutexW
        CreateMutex.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        CreateMutex.restype = wintypes.HANDLE
        
        ERROR_ALREADY_EXISTS = 183
        
        mutex_name = "Global\\COCK_SingleInstance_v1"
        mutex = CreateMutex(None, False, mutex_name)
        
        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            return False
        
        # Keep mutex handle in global to prevent garbage collection
        globals()['_instance_mutex'] = mutex
        return True
    else:
        # Linux/Mac: Use file lock
        import tempfile
        lock_file = os.path.join(tempfile.gettempdir(), 'COCKprofanityprocessorlock')
        
        try:
            lock_fd = open(lock_file, 'w')
            import fcntl
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            globals()['_instance_lock'] = lock_fd
            return True
        except (IOError, ImportError):
            return False

if PYQT5_AVAILABLE:
    class DebugWindow(QDialog):
        """Standalone debug console window"""
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("COCK Profanity Processor - Debug Console")
            self.setWindowFlags(Qt.Window)
            self.resize(900, 600)
            
            # Set window icon
            icon_path = path_manager.get_resource_file('icons/icon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            
            layout = QVBoxLayout()
            
            # Text display
            self.text_edit = QTextEdit()
            self.text_edit.setReadOnly(True)
            self.text_edit.setFont(QFont("Consolas", 9))
            self.text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: 1px solid #3c3c3c;
                }
            """)
            layout.addWidget(self.text_edit)
            
            # Control buttons
            button_layout = QHBoxLayout()
            
            clear_btn = QPushButton("Clear")
            clear_btn.clicked.connect(self.text_edit.clear)
            clear_btn.setStyleSheet("padding: 5px 15px;")
            button_layout.addWidget(clear_btn)
            
            button_layout.addStretch()
            
            close_btn = QPushButton("Hide Console")
            close_btn.clicked.connect(self.hide)
            close_btn.setStyleSheet("padding: 5px 15px;")
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            self.setLayout(layout)
            
            # Add welcome message
            self.append_text("="*80)
            self.append_text("COCK Profanity Processor - Debug Console")
            self.append_text("="*80)
            self.append_text("Debug messages will appear here in real-time.")
            self.append_text("Use 'Clear' to clear the console or 'Hide Console' to hide this window.")
            self.append_text("="*80)
            self.append_text("")
        
        def append_text(self, text):
            """Append text to console"""
            self.text_edit.append(text)
            # Auto-scroll to bottom
            scrollbar = self.text_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        def closeEvent(self, event):
            """Override close to hide instead of destroy"""
            event.ignore()
            self.hide()

class COCK(QObject if PYQT5_AVAILABLE else object):
    """
    Main application class
    
    Orchestrates all modules and handles the main workflow:
    1. User presses hotkey
    2. Capture clipboard
    3. Detect filtered words
    4. Route based on mode (manual/auto)
    5. Show UI overlay if needed
    6. Handle user actions
    """
    
    # Qt signal for thread-safe hotkey handling
    if PYQT5_AVAILABLE:
        hotkey_pressed = pyqtSignal()
        force_hotkey_pressed = pyqtSignal()
        toggle_hotkey_pressed = pyqtSignal()
    
    def __init__(self, config_path=None, debug=False, app=None):
        """
        Initialize the application
        
        Args:
            config_path: Optional path to config file
            debug: Enable debug output
            app: Optional QApplication instance (if already created for splash)
        """
        if PYQT5_AVAILABLE:
            super().__init__()

        # Initialize logger for this class (v1.1)
        from COCK.logger import get_logger
        self.logger = get_logger(__name__)

        self.debug = debug
        self.config_path = config_path
        self.app = app  # Store app if provided
        self._last_notification_scale = 1.0
        self._last_prompt_scale = 1.0
        self.pending_paste_part = "" # Track multi-part message remainder text

        # Create debug window
        if PYQT5_AVAILABLE:
            self.debug_window = DebugWindow()
        else:
            self.debug_window = None
        
        # Module instances
        self.config = None
        self.config_loader = None
        self.automaton = None
        self.filter_stats = None
        self.detector = None
        self.optimizer = None
        self.router = None
        self.wl_manager = None
        self.hotkey = None
        self.force_hotkey = None
        self.toggle_hotkey = None  # Hotkey to toggle optimization hotkeys on/off
        self.clipboard = None
        
        # UI components
        self.manual_overlay = None  # Renamed from strict_overlay
        # permissive_feedback removed - no longer used
        self.tray_icon = None
        
        # State
        self.running = False
        self.processing_hotkey = False  # Prevent re-entrant calls
        self.hotkeys_enabled = True  # Whether optimization hotkeys are currently enabled
        
        self.log("COCK Profanity Processor starting...")

    def log(self, message):
        """Log message using centralized logger and debug window"""
        # Use centralized logger (v1.1)
        self.logger.debug(message)

        # Also send to debug window if it exists
        if hasattr(self, 'debug_window') and self.debug_window:
            self.debug_window.append_text(f"[DEBUG] {message}")
    
    def initialize(self):
        """Initialize all modules"""
        try:
            # Phase 1: Core system
            self.log("Initializing core system...")
            
            # Load configuration
            config_path = self.config_path or path_manager.get_data_file('config.json')
            self.log(f"Loading config from: {config_path}")
            
            # Use ConfigLoader class
            self.config_loader = config_loader.ConfigLoader(config_path)
            self.config = self.config_loader.load()
            
            self.log(f"Config loaded successfully")
            
            # Check permissions
            permissions = permission_manager.check_permissions()

            # Check clipboard (tuple with (status, message))
            if not permissions.get('clipboard', (False, ""))[0]:
                self.logger.warning("Clipboard access may be restricted")

            # Check keyboard (tuple with (status, message))
            if not permissions.get('keyboard', (False, ""))[0]:
                self.logger.warning("Keyboard access may be restricted")
                self.logger.warning("  Global hotkeys may not work without keyboard module")
            
            # Admin is optional - just log status
            if permissions.get('admin', (False, ""))[0]:
                self.log("Running with administrator privileges")
            
            # Initialize clipboard manager
            try:
                self.clipboard = clipboard_manager.ClipboardManager(self.config)
                self.log("Clipboard manager initialized")
            except Exception as e:
                self.logger.warning(f"Clipboard manager initialization failed: {e}")
                self.logger.warning("  Clipboard capture may not work")
            
            # Load filter file
            self.log("Loading filter file...")
            filter_path = self.config.get('filter_file')
            
            if not filter_path or not os.path.exists(filter_path):
                self.logger.error("Filter file not found. Please configure in settings.")
                self.logger.error(f"  Expected: {filter_path}")
                return False

            # Validate filter file before loading
            try:
                file_size = os.path.getsize(filter_path)
                max_size = constants.MAX_FILTER_FILE_SIZE_MB * 1024 * 1024
                if file_size > max_size:
                    self.logger.error(f"Filter file too large ({file_size} bytes). Maximum: {max_size} bytes")
                    return False

                with open(filter_path, 'r', encoding='utf-8') as test_file:
                    for i, line in enumerate(test_file):
                        if i >= 1000:
                            break
                        if len(line.strip()) > constants.MAX_FILTER_LINE_LENGTH:
                            self.logger.warning(f"Filter file contains very long lines (line {i+1})")

            except UnicodeDecodeError as e:
                self.logger.error(f"Filter file has invalid encoding: {e}")
                return False
            except Exception as e:
                self.logger.error(f"Filter file validation failed: {e}")
                return False
            
            loader = filter_loader.FilterLoader()
            filter_path = self.config.get('filter_file')
            
            loader = filter_loader.FilterLoader()
            self.automaton, stats = loader.load(filter_path, verbose=self.debug)
            
            # Store filter loader for export functionality
            self.filter_loader = loader
            
            if self.automaton is None:
                self.logger.error("Failed to load filter file")
                return False
            
            # Store stats for settings dialog
            self.filter_stats = stats
            
            self.log(f"Loaded {stats['final_count']} filter words in {stats['load_time_ms']:.1f}ms")
            
            # Phase 2: Detection engine
            self.log("Initializing detection engine...")
            
            whitelist_path = path_manager.get_data_file('whitelist.txt')
            
            # Create default file if it doesn't exist
            if not os.path.exists(whitelist_path):
                with open(whitelist_path, 'w', encoding='utf-8') as f:
                    f.write("# Whitelist - Words safe when embedded\n")
                    f.write("# These words are NOT flagged when found embedded in larger words\n")
                    f.write("# Example: 'ass' is safe in 'assassin' but flagged when standalone\n\n")
            
            self.wl_manager = whitelist_manager.WhitelistManager(whitelist_path)
            
            self.detector = fast_detector.FastCensorDetector(
                self.automaton,
                self.wl_manager.get_whitelist(),
                self.config
            )
            
            # Phase 3: Optimization & modes
            self.log("Initializing optimization system...")
            
            self.leet = leet_speak.LeetSpeakConverter()
            self.fancy = fancy_text.FancyTextConverter()
            
            shorthand_path = 'shorthand.json'
            self.shorthand = shorthand_handler.ShorthandHandler(
                shorthand_path if os.path.exists(shorthand_path) else None
            )
            
            self.optimizer = message_optimizer.MessageOptimizer(
                self.detector, self.leet, self.fancy, self.shorthand, self.config
            )
            
            # Mode router
            self.router = mode_router.ModeRouter(
                self.config, self.detector, self.optimizer,
                self.wl_manager
            )
            
            # Phase 4: Update and help systems
            self.log("Initializing update checker and help system...")
            
            # Initialize update checker
            self.update_checker = update_checker.UpdateChecker(self.config)
            self.log("Update checker initialized")
            
            # Initialize help manager
            self.help_manager = help_manager.HelpManager(self.config)
            self.log("Help manager initialized")
            
            # Phase 5: UI will be initialized in run() after QApplication is created
            
            self.log("All modules initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            if self.debug:
                traceback.print_exc()
            return False
    
    def setup_hotkey(self):
        """Setup global hotkeys"""
        try:
            # Get normal hotkey combo from config
            hotkey_config = self.config.get('hotkey', 'ctrl+shift+v')
            
            if isinstance(hotkey_config, dict):
                # Old format
                hotkey_combo = hotkey_config.get('combo', 'ctrl+shift+v')
            else:
                # New format (string)
                hotkey_combo = hotkey_config
            
            self.log(f"Registering normal hotkey: {hotkey_combo}")
            
            # Create HotkeyHandler with hotkey and callback wrapper
            self.hotkey = hotkey_handler.HotkeyHandler(hotkey_combo, self.on_hotkey_pressed_callback)
            
            # Start listening
            if not self.hotkey.start():
                self.logger.warning(f"Could not register hotkey: {hotkey_combo}")
                self.logger.warning("  Hotkey may already be in use by another application")
                return False
            
            self.log("Normal hotkey registered successfully")
            
            # Setup force optimize hotkey
            force_hotkey_combo = self.config.get('force_optimize_hotkey', 'shift+f12')
            self.log(f"Registering force optimize hotkey: {force_hotkey_combo}")
            
            self.force_hotkey = hotkey_handler.HotkeyHandler(force_hotkey_combo, self.on_force_hotkey_pressed_callback)
            
            if not self.force_hotkey.start():
                self.logger.warning(f"Could not register force optimize hotkey: {force_hotkey_combo}")
                self.logger.warning("  Hotkey may already be in use by another application")
                # Continue anyway - normal hotkey still works
            else:
                self.log("Force optimize hotkey registered successfully")
            
            # Setup toggle hotkeys hotkey (ALWAYS active - controls enable/disable of other hotkeys)
            toggle_hotkey_combo = self.config.get('toggle_hotkeys_hotkey', 'ctrl+shift+h')
            if isinstance(toggle_hotkey_combo, dict):
                toggle_hotkey_combo = toggle_hotkey_combo.get('combo', 'ctrl+shift+h')
            
            self.log(f"Registering toggle hotkeys hotkey: {toggle_hotkey_combo}")
            
            self.toggle_hotkey = hotkey_handler.HotkeyHandler(toggle_hotkey_combo, self.on_toggle_hotkey_pressed_callback)
            
            if not self.toggle_hotkey.start():
                self.logger.warning(f"Could not register toggle hotkeys hotkey: {toggle_hotkey_combo}")
                self.logger.warning("  Hotkey may already be in use by another application")
            else:
                self.log("Toggle hotkeys hotkey registered successfully")
            
            # Load initial hotkeys_enabled state from config
            self.hotkeys_enabled = self.config.get('hotkeys_enabled', True)
            
            # If hotkeys should start disabled, stop them now
            if not self.hotkeys_enabled:
                if self.hotkey and self.hotkey.is_active():
                    self.hotkey.stop()
                if self.force_hotkey and self.force_hotkey.is_active():
                    self.force_hotkey.stop()
                self.log("Hotkeys initialized in DISABLED state")
            else:
                self.log("Hotkeys initialized in ENABLED state")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Hotkey setup failed: {e}")
            return False
    
    def show_notification(self, title: str, message: str, notification_type: str = 'info', duration: int = None):
        """
        Show a brief notification popup
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: 'clean', 'optimized', or 'info'
            duration: Optional duration in milliseconds (overrides config if provided)
        """
        if not PYQT5_AVAILABLE:
            return
        
        # Check if notifications are enabled for this type
        notifications_config = self.config.get('notifications', {})
        enabled = notifications_config.get('enabled', True)
        
        # Check specific type settings
        if notification_type == 'clean':
            enabled = notifications_config.get('show_clean_messages', True)
        elif notification_type == 'optimized':
            enabled = notifications_config.get('show_optimized_messages', True)
        
        if not enabled:
            return
        
        # Get duration from parameter or config
        if duration is None:
            duration_ms = notifications_config.get('duration_ms', 2000)  # Default 2 seconds
        else:
            duration_ms = duration
        
        try:
            from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
            from PyQt5.QtCore import QTimer, Qt
            from PyQt5.QtGui import QFont
            
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
            scale = self.config.get('ui', {}).get('notification_scale', 1.0)
            
            # Title label
            title_label = QLabel(title)
            title_font = QFont()
            title_font.setBold(True)
            title_font.setPointSize(int(10 * scale))
            title_label.setFont(title_font)
            layout.addWidget(title_label)
            
            # Message label
            message_label = QLabel(message)
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
            theme = self.config.get('ui', {}).get('theme', 'dark')
            if theme == 'dark':
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
            
            # Position in bottom-right corner
            from PyQt5.QtWidgets import QDesktopWidget
            desktop = QDesktopWidget()
            screen_rect = desktop.availableGeometry()
            
            notification.adjustSize()
            
            # Get position and offsets from config
            position = self.config.get('ui', {}).get('notification_position', 'bottom-right')
            offset_x = self.config.get('ui', {}).get('notification_offset_x', 20)
            offset_y = self.config.get('ui', {}).get('notification_offset_y', 20)
            
            # Calculate position based on config (with 9 presets)
            if position == 'top-left':
                x = offset_x
                y = offset_y
            elif position == 'top-center':
                x = (screen_rect.width() - notification.width()) // 2 + offset_x
                y = offset_y
            elif position == 'top-right':
                x = screen_rect.width() - notification.width() - offset_x
                y = offset_y
            elif position == 'center-left':
                x = offset_x
                y = (screen_rect.height() - notification.height()) // 2 + offset_y
            elif position == 'center':
                x = (screen_rect.width() - notification.width()) // 2 + offset_x
                y = (screen_rect.height() - notification.height()) // 2 + offset_y
            elif position == 'center-right':
                x = screen_rect.width() - notification.width() - offset_x
                y = (screen_rect.height() - notification.height()) // 2 + offset_y
            elif position == 'bottom-left':
                x = offset_x
                y = screen_rect.height() - notification.height() - offset_y
            elif position == 'bottom-center':
                x = (screen_rect.width() - notification.width()) // 2 + offset_x
                y = screen_rect.height() - notification.height() - offset_y
            elif position == 'bottom-right':
                x = screen_rect.width() - notification.width() - offset_x
                y = screen_rect.height() - notification.height() - offset_y
            else:  # fallback to center
                x = (screen_rect.width() - notification.width()) // 2 + offset_x
                y = (screen_rect.height() - notification.height()) // 2 + offset_y
            
            notification.move(x, y)
            
            # Store reference to prevent garbage collection
            if not hasattr(self, '_active_notifications'):
                self._active_notifications = []
            self._active_notifications.append(notification)

            # Play notification sound if enabled
            self.play_sound('notification')
            
            notification.show()
            
            # Auto-close after configured duration
            def close_and_cleanup():
                notification.close()
                if notification in self._active_notifications:
                    self._active_notifications.remove(notification)
            
            if duration_ms > 0:
                QTimer.singleShot(duration_ms, close_and_cleanup)
            
        except Exception as e:
            self.log(f"Failed to show notification: {e}")
            import traceback
            traceback.print_exc()
    
    def init_ui(self):
        """Initialize UI components (must be called after QApplication is created)"""
        if not PYQT5_AVAILABLE:
            return
        
        try:
            self.log("Initializing UI components...")
            
            # Connect hotkey signals to handlers (thread-safe)
            self.hotkey_pressed.connect(self.on_hotkey_triggered)
            self.force_hotkey_pressed.connect(self.on_force_hotkey_triggered)
            self.toggle_hotkey_pressed.connect(self.toggle_hotkeys)
            
            # Create manual overlay
            self.manual_overlay = overlay_manual.ManualModeOverlay(self.config)
            
            # Connect overlay signals
            self.log("Connecting manual overlay signals...")
            self.manual_overlay.use_suggestion.connect(self.on_use_suggestion)
            self.manual_overlay.cancelled.connect(self.on_cancelled)
            self.log("✓ Manual overlay signals connected successfully")
            
            # permissive_feedback removed - no longer used in auto mode
            
            self.log("UI components initialized")
        
        except Exception as e:
            self.logger.warning(f"UI initialization failed: {e}")
            import traceback
            traceback.print_exc()
    
    def on_hotkey_pressed_callback(self):
        """
        Callback from keyboard library (runs in keyboard thread)
        
        This just emits a signal to handle the hotkey in the main Qt thread.
        Never do GUI operations directly from this callback!
        """
        if PYQT5_AVAILABLE:
            # Emit signal to handle in main thread
            self.hotkey_pressed.emit()
        else:
            # No Qt, call directly
            self.on_hotkey_triggered()
    
    def on_force_hotkey_pressed_callback(self):
        """
        Callback from force optimize hotkey (Shift+F12)
        
        This just emits a signal to handle the force hotkey in the main Qt thread.
        """
        if PYQT5_AVAILABLE:
            # Emit signal to handle in main thread
            self.force_hotkey_pressed.emit()
        else:
            # No Qt, call directly
            self.on_force_hotkey_triggered()
    
    def on_force_hotkey_triggered(self):
        """Handle force optimize hotkey press"""
        # Call normal hotkey handler with force_mode=True
        self.on_hotkey_triggered(force_mode=True)
    
    def on_toggle_hotkey_pressed_callback(self):
        """
        Callback from toggle hotkeys hotkey (Ctrl+Shift+H)
        
        This just emits a signal to handle the toggle in the main Qt thread.
        """
        if PYQT5_AVAILABLE:
            # Emit signal to handle in main thread
            self.toggle_hotkey_pressed.emit()
        else:
            # No Qt, call directly
            self.toggle_hotkeys()
    
    def toggle_hotkeys(self):
        """Toggle optimization hotkeys on/off"""
        self.hotkeys_enabled = not self.hotkeys_enabled
        
        # Update config
        self.config['hotkeys_enabled'] = self.hotkeys_enabled
        self.config_loader.save(self.config)
        
        if self.hotkeys_enabled:
            # Enable hotkeys
            if self.hotkey and not self.hotkey.is_active():
                self.hotkey.start()
            if self.force_hotkey and not self.force_hotkey.is_active():
                self.force_hotkey.start()
            
            self.log("Hotkeys ENABLED")
            
            # Show notification
            if PYQT5_AVAILABLE and hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.showMessage(
                    "COCK Profanity Processor",
                    "Hotkeys Enabled",
                    self.tray_icon.icon(),
                    2000
                )
        else:
            # Disable hotkeys
            if self.hotkey and self.hotkey.is_active():
                self.hotkey.stop()
            if self.force_hotkey and self.force_hotkey.is_active():
                self.force_hotkey.stop()
            
            self.log("Hotkeys DISABLED")
            
            # Show notification
            if PYQT5_AVAILABLE and hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.showMessage(
                    "COCK Profanity Processor",
                    "Hotkeys Disabled",
                    self.tray_icon.icon(),
                    2000
                )
        
        # Update tray menu checkmark
        if hasattr(self, 'toggle_hotkeys_action'):
            self.toggle_hotkeys_action.setChecked(self.hotkeys_enabled)
    
    def on_hotkey_triggered(self, force_mode=False):
        """
        Handle hotkey press
        
        Args:
            force_mode: If True, apply force optimization to all words
        """
        # Prevent re-entrant calls
        if self.processing_hotkey:
            self.log("Hotkey already being processed, ignoring")
            return
        
        self.processing_hotkey = True
        self.log(f"Hotkey triggered! (force_mode={force_mode})")
        
        try:
            # Small delay to ensure modifier keys (Shift, Ctrl, Alt) are fully released
            # This prevents Shift+Ctrl+A instead of Ctrl+A
            import time
            time.sleep(0.05)  # 50ms delay
            
            # Capture text from active window using clipboard manager
            if not self.clipboard:
                self.logger.error("Clipboard manager not initialized")
                return
            
            self.log("Capturing text from active window...")
            text = self.clipboard.capture_with_backup()
            self.log(f"Capture complete: {len(text) if text else 0} chars")
            
            if not text:
                self.log("No text captured from active window")
                return
            
            # Sanity check: warn if captured text is suspiciously long
            # Normal chat messages are rarely over 500 chars
            if len(text) > constants.MAX_CLIPBOARD_CAPTURE_LENGTH:
                self.log(f"WARNING: Captured {len(text)} chars - likely captured from WRONG WINDOW!")
                self.log("Make sure the GAME CHAT WINDOW has focus, not the console!")
                self.show_notification(
                    "⚠️ Wrong Window!",
                    f"Captured {len(text)} chars from console/wrong window!\n" +
                    "Click game chat window and try again.",
                    notification_type='optimized'
                )
                return
            
            self.log(f"Captured: {text[:50]}...")
            
            # Process message through router
            self.log("Processing message...")
            if force_mode:
                result = self.router.process_force_optimize(text)
            else:
                result = self.router.process_message(text)
            
            self.log(f"Processing result: {result.action}")
            
            # Handle based on action
            if result.action == 'send':
                # Clean message - send it
                self.log("Message is clean - sending")
                
                # Paste original text
                if self.clipboard.paste_text(text):
                    # Send message (press Enter)
                    self.clipboard.send_message()
                    self.log("Clean message sent")
                    
                    # Clear clipboard
                    self.clipboard.copy_to_clipboard("")
                    
                    # Show notification
                    self.show_notification(
                        "Clean Message Sent",
                        "No filtered words detected",
                        notification_type='clean'
                    )
                
            elif result.action == 'manual':
                # Manual mode - show UI
                if PYQT5_AVAILABLE and self.manual_overlay:
                    self.log("Showing manual mode overlay")
                    try:
                        self.log(f"Overlay object exists: {self.manual_overlay is not None}")
                        self.log(f"Flagged words: {result.flagged_words}")
                        self.log(f"Suggested: {result.suggested}")
                        self.log(f"Paste part: {result.paste_part}")
                        
                        # Store paste_part for later use
                        self.pending_paste_part = result.paste_part if result.paste_part else ""
                        
                        self.manual_overlay.show_detection(
                            result.original,
                            result.flagged_words,
                            result.suggested
                        )
                        self.log("show_detection() call completed")
                    except Exception as e:
                        self.logger.error(f"Failed to show overlay: {e}")
                        if self.debug:
                            traceback.print_exc()
                else:
                    self.logger.info(f"Detected words: {', '.join(result.flagged_words)}")
                    if result.suggested:
                        self.logger.info(f"Suggested: {result.suggested}")
                
            elif result.action == 'optimize':
                # Auto mode or force mode - auto-optimized
                if result.suggested:
                    self.log(f"Optimized text: {result.suggested}")
                    
                    # Paste optimized text
                    self.log("Pasting optimized text...")
                    if self.clipboard.paste_text(result.suggested):
                        self.log("Text pasted successfully")
                        
                        # Check if multi-part message
                        if result.paste_part:
                            # Message split - send first part, paste remainder
                            self.log(f"Multi-part message: sending part, pasting remainder ({len(result.paste_part)} chars)")
                            
                            # Send first part
                            self.clipboard.send_message()
                            self.log("First part sent")
                            
                            # Brief delay
                            import time
                            delay_ms = self.config.get('multipart_paste_delay_ms', 100)
                            time.sleep(delay_ms / 1000.0)
                            
                            # Paste remainder (DON'T send)
                            self.log(f"Pasting remainder: {result.paste_part[:50]}...")
                            if self.clipboard.paste_text(result.paste_part):
                                self.log("Remainder pasted successfully")
                                
                                # Clear clipboard to prevent contamination on next capture
                                self.log("Clearing clipboard...")
                                self.clipboard.copy_to_clipboard("")
                                
                                # Show notification
                                hotkey = self.config.get('force_optimize_hotkey' if force_mode else 'hotkey', 'F12')
                                self.show_notification(
                                    "Long Message Split",
                                    f"Message went over length limit!\nPress {hotkey} to send next part",
                                    notification_type='optimized'
                                )
                            else:
                                self.log("ERROR: Failed to paste remainder")
                        else:
                            # Single-part message - send normally
                            self.clipboard.send_message()
                            self.log("Message sent automatically")
                            
                            # Clear clipboard to prevent contamination
                            self.clipboard.copy_to_clipboard("")
                            
                            # Show notification
                            mode_text = "Force optimized" if force_mode else "Optimized"
                            self.show_notification(
                                f"Message {mode_text}",
                                f"Message was modified before sending",
                                notification_type='optimized'
                            )
                    else:
                        self.log("ERROR: Failed to paste text")
            
            elif result.action == 'block':
                # Could not optimize
                if PYQT5_AVAILABLE and self.manual_overlay:
                    self.manual_overlay.show_detection(
                        result.original,
                        result.flagged_words,
                        None
                    )
                else:
                    self.logger.info(f"Could not optimize. Detected: {', '.join(result.flagged_words)}")

            self.log("Hotkey handler completed")

        except Exception as e:
            self.logger.error(f"Hotkey handler failed: {e}")
            if self.debug:
                traceback.print_exc()
        finally:
            # Always reset flag
            self.processing_hotkey = False
            self.log("Hotkey processing flag reset")

    def play_sound(self, sound_type):
        """
        Play a hardcoded sound (notification or prompt)
        
        Args:
            sound_type: 'notification' or 'prompt'
        """
        # Check if sound is enabled in config
        sound_enabled = self.config.get('ui', {}).get(f'{sound_type}_sound', True)
        if not sound_enabled:
            return
        
        try:
            import winsound
            import os
            
            # Build path to sound file
            sound_file = os.path.join(
                os.path.dirname(__file__), 
                'resources', 
                'sounds', 
                f'{sound_type}.wav'
            )
            
            # Play custom sound if file exists
            if os.path.exists(sound_file):
                self.log(f"Playing {sound_type} sound: {sound_file}")
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                # Fallback to system beep
                self.log(f"Sound file not found, using system beep: {sound_file}")
                winsound.MessageBeep(winsound.MB_OK)
                
        except Exception as e:
            self.log(f"Could not play {sound_type} sound: {e}")
    
    
    def on_use_suggestion(self):
        """Handle manual mode 'use suggestion' action"""
        self.log("=== on_use_suggestion() CALLED ===")
        
        # Debug: Check overlay state
        self.log(f"Has manual_overlay: {hasattr(self, 'manual_overlay')}")
        if hasattr(self, 'manual_overlay'):
            self.log(f"Overlay exists: {self.manual_overlay is not None}")
            if self.manual_overlay:
                self.log(f"Suggested text: '{self.manual_overlay.suggested_text}'")
        
        if not hasattr(self, 'manual_overlay') or not self.manual_overlay.suggested_text:
            self.log("ERROR: No overlay or no suggested text - ABORTING")
            return
        
        # Store values before closing overlay
        suggested_text = self.manual_overlay.suggested_text
        paste_part = self.pending_paste_part if hasattr(self, 'pending_paste_part') else ""
        
        self.log(f"Suggested text: '{suggested_text}'")
        self.log(f"Paste part: '{paste_part}'")
        
        # Close overlay FIRST
        self.log("Closing overlay...")
        self.manual_overlay.close()
        
        # Brief delay
        import time
        time.sleep(0.1)
        self.log("Overlay closed, proceeding with paste...")
        
        # Paste optimized text
        self.log(f"Pasting optimized text: '{suggested_text}'")
        
        if self.clipboard.paste_text(suggested_text):
            self.log("Text pasted successfully")
            
            if paste_part:
                # Multi-part message
                self.log(f"Multi-part message: sending part, pasting remainder ({len(paste_part)} chars)")
                
                self.clipboard.send_message()
                self.log("First part sent")
                
                delay_ms = self.config.get('multipart_paste_delay_ms', 100)
                time.sleep(delay_ms / 1000.0)
                
                self.log(f"Pasting remainder: {paste_part}...")
                if self.clipboard.paste_text(paste_part):
                    self.log("Remainder pasted successfully")
                    self.clipboard.copy_to_clipboard("")
                    self.pending_paste_part = ""
                    
                    hotkey = self.config.get('hotkey', 'F12')
                    self.show_notification(
                        "Long Message Split",
                        f"Message went over length limit!\nPress {hotkey} to send next part",
                        notification_type='optimized'
                    )
                else:
                    self.log("ERROR: Failed to paste remainder")
            else:
                # Single-part message
                self.clipboard.send_message()
                self.log("Message sent from manual mode")
                self.clipboard.copy_to_clipboard("")
                
                self.show_notification(
                    "Manual Mode - Sent",
                    "Optimized message sent",
                    notification_type='optimized'
                )
        else:
            self.log("ERROR: Failed to paste text")
        
        self.log("=== on_use_suggestion() COMPLETED ===")
    
    def on_cancelled(self):
        """Handle cancel from strict overlay"""
        self.log("User cancelled")
    
    
    def setup_tray_icon(self):
        """Setup system tray icon"""
        if not PYQT5_AVAILABLE:
            return
        
        try:
            from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
            from PyQt5.QtGui import QIcon
            
            # Load custom tray icon
            icon_path = path_manager.get_resource_file('icons/icon.ico')
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
            else:
                # Fallback to default icon
                icon = QIcon()
                self.logger.warning(f"Tray icon not found at {icon_path}")
            
            self.tray_icon = QSystemTrayIcon(icon, self.app)
            self.log("Setting up system tray...")
            
            # Icon already set in constructor above
            # Custom icon loaded from resources/icons/icon.ico
            
            # Create menu
            menu = QMenu()
            
            # Settings action
            settings_action = QAction("Settings", self.app)
            settings_action.triggered.connect(self.show_settings)
            menu.addAction(settings_action)
            
            menu.addSeparator()
            
            # Hotkeys toggle
            self.toggle_hotkeys_action = QAction("Enable Hotkeys", self.app, checkable=True)
            self.toggle_hotkeys_action.setChecked(self.hotkeys_enabled)
            self.toggle_hotkeys_action.triggered.connect(self.toggle_hotkeys)
            menu.addAction(self.toggle_hotkeys_action)
            
            menu.addSeparator()
            
            # Mode switch
            mode_menu = menu.addMenu("Mode")
            manual_action = QAction("Manual", self.app, checkable=True)
            auto_action = QAction("Auto", self.app, checkable=True)
            
            current_mode = self.router.get_mode()
            if current_mode == mode_router.DetectionMode.MANUAL:
                manual_action.setChecked(True)
            else:
                auto_action.setChecked(True)
            
            manual_action.triggered.connect(lambda: self.switch_mode('manual'))
            auto_action.triggered.connect(lambda: self.switch_mode('auto'))
            
            mode_menu.addAction(manual_action)
            mode_menu.addAction(auto_action)
            
            # Special Character Interspacing toggle
            special_char_action = QAction("Special Char Interspacing", self.app, checkable=True)
            special_char_enabled = self.config.get('optimization', {}).get('special_char_interspacing', False)
            special_char_action.setChecked(special_char_enabled)
            special_char_action.triggered.connect(lambda checked: self.toggle_special_char(checked))
            menu.addAction(special_char_action)
            
            # Fancy Text Style menu
            style_menu = menu.addMenu("Fancy Text Style")
            
            styles = ['squared', 'bold', 'italic', 'bold_italic', 'sans_serif', 'circled', 'negative_squared', 'negative_circled']
            style_names = {
                'squared': 'Squared (🄵🅄🄲🄺)',
                'bold': 'Bold (𝐟𝐮𝐜𝐤)',
                'italic': 'Italic (𝑓𝑢𝑐𝑘)',
                'bold_italic': 'Bold Italic (𝒇𝒖𝒄𝒌)',
                'sans_serif': 'Sans-Serif (𝖿𝗎𝖼𝗄)',
                'circled': 'Circled (ⓕⓤⓒⓚ)',
                'negative_squared': 'Negative Squared (🅵🆄🅲🅺)',
                'negative_circled': 'Negative Circled (🅕🅤🅒🅚)'
            }
            
            current_style = self.config.get('optimization', {}).get('fancy_text_style', 'squared')
            
            for style in styles:
                style_action = QAction(style_names[style], self.app, checkable=True)
                if style == current_style:
                    style_action.setChecked(True)
                style_action.triggered.connect(lambda checked, s=style: self.change_fancy_style(s))
                style_menu.addAction(style_action)
            
            menu.addSeparator()
            
            # Notifications menu
            notif_menu = menu.addMenu("Notifications")

            # Get current settings
            notif_config = self.config.get('notifications', {})
            enabled = notif_config.get('enabled', True)
            show_clean = notif_config.get('show_clean_messages', True)
            show_optimized = notif_config.get('show_optimized_messages', True)

            # Enable/Disable all notifications
            self.notif_enabled_action = QAction("Enable Notifications", self.app, checkable=True)
            self.notif_enabled_action.setChecked(enabled)
            self.notif_enabled_action.triggered.connect(lambda checked: self.toggle_notifications('enabled', checked))
            notif_menu.addAction(self.notif_enabled_action)

            notif_menu.addSeparator()

            # Show clean messages
            self.notif_clean_action = QAction("Show Clean Message Popups", self.app, checkable=True)
            self.notif_clean_action.setChecked(show_clean)
            self.notif_clean_action.triggered.connect(lambda checked: self.toggle_notifications('show_clean_messages', checked))
            notif_menu.addAction(self.notif_clean_action)

            # Show optimized messages
            self.notif_optimized_action = QAction("Show Optimized Message Popups", self.app, checkable=True)
            self.notif_optimized_action.setChecked(show_optimized)
            self.notif_optimized_action.triggered.connect(lambda checked: self.toggle_notifications('show_optimized_messages', checked))
            notif_menu.addAction(self.notif_optimized_action)

            menu.addSeparator()
            
            # Max Sliding Window menu
            window_menu = menu.addMenu("Max Sliding Window")
            current_max_window = self.config.get('max_sliding_window', 3)
            
            window_sizes = [
                (2, "2-word (Fast)"),
                (3, "3-word (Default)"),
                (4, "4-word"),
                (5, "5-word (Comprehensive)")
            ]
            
            for window_size, label in window_sizes:
                window_action = QAction(label, self.app, checkable=True)
                if window_size == current_max_window:
                    window_action.setChecked(True)
                window_action.triggered.connect(lambda checked, size=window_size: self.set_max_sliding_window(size))
                window_menu.addAction(window_action)
            
            menu.addSeparator()
            
            # Stats action
            stats_action = QAction("Show Stats", self.app)
            stats_action.triggered.connect(self.show_stats)
            menu.addAction(stats_action)
            
            menu.addSeparator()

            # Debug console toggle (Windows only)
            if sys.platform == 'win32':
                console_action = QAction("Toggle Debug Console", self.app)
                console_action.triggered.connect(self.toggle_console)
                menu.addAction(console_action)
            
            menu.addSeparator()
            
            # Quit action
            quit_action = QAction("Quit", self.app)
            quit_action.triggered.connect(self.quit_app)
            menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(menu)
            
            # Set tooltip
            self.tray_icon.setToolTip("COCK Profanity Processor")
            
            # Show icon
            self.tray_icon.show()
            
            # Connect click event to show settings
            self.tray_icon.activated.connect(self.on_tray_activated)
            
            # Show system tray notification with custom icon
            icon_path = path_manager.get_resource_file('icons/icon.ico')
            if os.path.exists(icon_path):
                from PyQt5.QtGui import QIcon
                custom_icon = QIcon(icon_path)
                self.tray_icon.showMessage(
                    "COCK IN OPERATION",
                    "Running in your system tray. Right click for settings.",
                    custom_icon,  # Use custom icon instead of QSystemTrayIcon.Information
                    3000  # 3 seconds
                )
            else:
                # Fallback to default blue circle
                self.tray_icon.showMessage(
                    "COCK Profanity Processor",
                    "Application is running in the system tray. Right-click the tray icon for options.",
                    QSystemTrayIcon.Information,
                    3000
                )    
            self.log("System tray icon created")
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not create system tray icon: {e}")
            return False
    
    def apply_settings_live(self):
        """Apply settings without restart"""
        
        # Store old values for comparison
        old_sliding_window = self.config.get('max_sliding_window', 3)
        old_whitelist_size = len(self.wl_manager.get_whitelist())
        
        # Update config
        self.config = self.config_loader.load()
        
        # Check what changed
        needs_detector_rebuild = False
        
        # Check 1: Sliding window changed
        new_sliding_window = self.config.get('max_sliding_window', 3)
        if new_sliding_window != old_sliding_window:
            self.log(f"Sliding window changed: {old_sliding_window} -> {new_sliding_window}")
            needs_detector_rebuild = True
        
        # Check 2: Whitelist changed (from Settings Save button or tray)
        # Reload whitelist from file
        self.wl_manager._load_whitelist()
        new_whitelist_size = len(self.wl_manager.get_whitelist())
        if new_whitelist_size != old_whitelist_size:
            self.log(f"Whitelist changed: {old_whitelist_size} -> {new_whitelist_size} entries")
            needs_detector_rebuild = True
        
        # Update optimizer settings (these don't need detector rebuild)
        self.optimizer.enable_leet = self.config.get('optimization', {}).get('leet_speak', True)
        self.optimizer.enable_unicode = self.config.get('optimization', {}).get('fancy_unicode', True)
        self.optimizer.enable_shorthand = self.config.get('optimization', {}).get('shorthand', True)
        self.optimizer.enable_link_protection = self.config.get('optimization', {}).get('link_protection', True)
        self.optimizer.enable_special_char = self.config.get('optimization', {}).get('special_char_interspacing', False)
        self.optimizer.byte_limit = self.config.get('byte_limit', 80)
        
        # Update hotkey if changed
        new_hotkey = self.config.get('hotkey', 'ctrl+shift+v')
        if isinstance(new_hotkey, dict):
            new_hotkey = new_hotkey.get('combo', 'ctrl+shift+v')
        
        if hasattr(self, 'hotkey') and self.hotkey:
            old_hotkey = self.hotkey.get_hotkey()
            if old_hotkey != new_hotkey:
                if self.hotkey.change_hotkey(new_hotkey):
                    self.log(f"Hotkey updated: {old_hotkey} -> {new_hotkey}")
        
        # Rebuild detector only if necessary
        if needs_detector_rebuild:
            self.log("Rebuilding detector due to settings change...")
            self.detector = fast_detector.FastCensorDetector(
                self.automaton,
                self.wl_manager.get_whitelist(),
                self.config
            )
            self.router.detector = self.detector
            self.optimizer.detector = self.detector
            self.log("Detector rebuilt successfully")
        else:
            self.log("Settings updated without detector rebuild")

        # Recreate overlays with new scale settings
        if PYQT5_AVAILABLE:
            # Get old scales
            old_notification_scale = getattr(self, '_last_notification_scale', 1.0)
            old_prompt_scale = getattr(self, '_last_prompt_scale', 1.0)
            
            # Get new scales
            new_notification_scale = self.config.get('ui', {}).get('notification_scale', 1.0)
            new_prompt_scale = self.config.get('ui', {}).get('prompt_scale', 1.0)
            
            # Check if scales changed
            notification_scale_changed = abs(new_notification_scale - old_notification_scale) > 0.01
            prompt_scale_changed = abs(new_prompt_scale - old_prompt_scale) > 0.01
            
            # Recreate manual overlay if prompt scale changed
            if prompt_scale_changed and hasattr(self, 'manual_overlay'):
                self.log(f"Prompt scale changed: {old_prompt_scale} → {new_prompt_scale}")
                try:
                    # Close old overlay if visible
                    if self.manual_overlay and hasattr(self.manual_overlay, 'isVisible'):
                        if self.manual_overlay.isVisible():
                            self.manual_overlay.hide()
                    
                    # Recreate with new scale
                    import overlay_manual
                    self.manual_overlay = overlay_manual.ManualModeOverlay(self.config)
                    
                    # CRITICAL: Reconnect signals after recreating overlay
                    self.manual_overlay.use_suggestion.connect(self.on_use_suggestion)
                    self.manual_overlay.cancelled.connect(self.on_cancelled)
                    
                    self.log("✓ Manual overlay recreated with new scale (signals reconnected)")
                except Exception as e:
                    print(f"Warning: Could not recreate manual overlay: {e}")
            
            # Store current scales for next comparison
            self._last_notification_scale = new_notification_scale
            self._last_prompt_scale = new_prompt_scale

        # Sync notification settings to tray menu
        self.sync_notification_settings()
        
        self.log("✓ All settings applied successfully (no restart needed)")

    def sync_notification_settings(self):
        """Sync notification settings between config and tray menu"""
        if not PYQT5_AVAILABLE or not hasattr(self, 'tray'):
            self.log("Cannot sync: PyQt5 or tray not available")
            return
        
        # Get current settings from config
        notif_enabled = self.config.get('notifications', {}).get('enabled', True)
        show_clean = self.config.get('notifications', {}).get('show_clean_messages', True)
        show_optimized = self.config.get('notifications', {}).get('show_optimized_messages', True)
        
        self.log(f"[SYNC] Reading from config: enabled={notif_enabled}, clean={show_clean}, optimized={show_optimized}")
        
        # Update action checkboxes directly using stored references
        if hasattr(self, 'notif_enabled_action'):
            self.notif_enabled_action.setChecked(notif_enabled)
            self.log(f"[SYNC] Updated notif_enabled_action to {notif_enabled}")
        else:
            self.log("[SYNC] WARNING: notif_enabled_action not found!")
            
        if hasattr(self, 'notif_clean_action'):
            self.notif_clean_action.setChecked(show_clean)
            self.log(f"[SYNC] Updated notif_clean_action to {show_clean}")
        else:
            self.log("[SYNC] WARNING: notif_clean_action not found!")
            
        if hasattr(self, 'notif_optimized_action'):
            self.notif_optimized_action.setChecked(show_optimized)
            self.log(f"[SYNC] Updated notif_optimized_action to {show_optimized}")
        else:
            self.log("[SYNC] WARNING: notif_optimized_action not found!")
        
        self.log(f"Notification settings synced: enabled={notif_enabled}, clean={show_clean}, optimized={show_optimized}")

    def on_tray_activated(self, reason):
        """Handle tray icon activation (click)"""
        from PyQt5.QtWidgets import QSystemTrayIcon
        
        # Single click or double click - open settings
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_settings()
        # Right click - context menu shows automatically
    
    def show_settings(self):
        """Show settings dialog (non-modal)"""
        self.log("show_settings() called")  # Debug
        
        if not PYQT5_AVAILABLE:
            self.log("PyQt5 not available, cannot show settings")
            return
        
        try:
            self.log("Creating settings dialog...")
            
            # If settings dialog already exists and is visible, just bring it to front
            if hasattr(self, 'settings_dialog_instance') and self.settings_dialog_instance and self.settings_dialog_instance.isVisible():
                self.log("Settings dialog already visible, bringing to front")
                self.settings_dialog_instance.raise_()
                self.settings_dialog_instance.activateWindow()
                return
            
            # Use stored filter stats or create empty dict
            filter_stats = self.filter_stats or {
                'final_count': 0,
                'load_time_ms': 0
            }
            
            self.log(f"Filter stats: {filter_stats}")
            
            # Create non-modal dialog with parent reference for update_checker and help_manager access
            self.log("Instantiating SettingsDialog...")
            # Use self.app as parent (QApplication can parent dialogs), and pass self as reference for accessing update_checker/help_manager
            self.settings_dialog_instance = settings_dialog.SettingsDialog(self.config, filter_stats, parent=None)
            # Store reference to main app so settings can access update_checker and help_manager
            self.settings_dialog_instance.main_app = self
            
            self.log("Connecting signals...")
            # Connect signals
            self.settings_dialog_instance.settings_saved.connect(self.on_settings_saved)
            self.settings_dialog_instance.finished.connect(self.on_settings_closed)
            
            self.log("Showing dialog...")
            # Show as non-modal (doesn't block other windows)
            self.settings_dialog_instance.show()
            self.settings_dialog_instance.raise_()
            self.settings_dialog_instance.activateWindow()
            
            self.log("Settings dialog shown successfully")
            
        except Exception as e:
            self.log(f"ERROR: Settings dialog failed: {e}")
            import traceback
            self.log(traceback.format_exc())  # Log full traceback to debug console
    
    def on_settings_saved(self, needs_restart):
        """
        Handle when settings are saved (called from settings dialog)
        
        Args:
            needs_restart: True if filter file changed and user wants restart
        """
        if not hasattr(self, 'settings_dialog_instance') or not self.settings_dialog_instance:
            return
        
        try:
            # Get the ACTUAL current state (not from dialog's stale copy)
            old_hotkey = self.config.get('hotkey', 'f12')
            old_force_hotkey = self.config.get('force_optimize_hotkey', 'shift+f12')
            old_mode = self.router.get_mode().value  # Get ACTUAL current mode from router
            
            self.config = self.settings_dialog_instance.get_config()
            
            # Save config using the loader
            self.config_loader.save(self.config)
            
            # Check if detection mode changed - update router and tray menu
            new_mode = self.config.get('detection_mode', 'manual')
            self.log(f"[SETTINGS] Mode check: old='{old_mode}' (from router), new='{new_mode}' (from dialog)")
            # Normalize to lowercase for comparison (Qt may capitalize display text)
            if old_mode.lower() != new_mode.lower():
                self.log(f"Detection mode changed: {old_mode} -> {new_mode}")
                new_mode_enum = mode_router.DetectionMode.MANUAL if new_mode.lower() == 'manual' else mode_router.DetectionMode.AUTO
                self.router.switch_mode(new_mode_enum)
                self.log(f"[SETTINGS] Router mode switched to {new_mode_enum}")
                # Update tray menu checkboxes
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    self.update_tray_menu_checkboxes()
                    self.log("[SETTINGS] Tray menu checkboxes updated")
            else:
                self.log(f"[SETTINGS] Mode unchanged, skipping update")
            
            # Apply settings live (without restart)
            self.apply_settings_live()
            
            # Check if restart is needed
            if needs_restart:
                # User already confirmed in dialog - just restart
                self.restart_application()
                return
            
            # Check if hotkeys changed - need to re-register
            new_hotkey = self.config.get('hotkey', 'f12')
            new_force_hotkey = self.config.get('force_optimize_hotkey', 'shift+f12')
            
            hotkeys_changed = (old_hotkey != new_hotkey) or (old_force_hotkey != new_force_hotkey)
            
            if hotkeys_changed:
                # Stop old hotkeys
                if self.hotkey:
                    self.hotkey.stop()
                if hasattr(self, 'force_hotkey') and self.force_hotkey:
                    self.force_hotkey.stop()
                
                # Re-register new hotkeys
                self.setup_hotkey()
                
                self.log("Hotkeys re-registered")
            
        except Exception as e:
            self.logger.error(f"Failed to apply settings: {e}")
    
    def on_settings_closed(self, result):
        """
        Handle settings dialog close
        
        Args:
            result: QDialog.Accepted or QDialog.Rejected
        """
        # Clean up reference
        self.settings_dialog_instance = None
    
    def switch_mode(self, mode_name):
        """Switch detection mode"""
        self.log(f"Switching to {mode_name} mode")
        
        new_mode = mode_router.DetectionMode.MANUAL if mode_name == 'manual' else mode_router.DetectionMode.AUTO
        self.router.switch_mode(new_mode)
        
        # Update config
        self.config['detection_mode'] = mode_name
        self.config_loader.save(self.config)
        
        # Update tray menu checkboxes WITHOUT rebuilding everything
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.update_tray_menu_checkboxes()
            self.log("Tray menu updated")
        
        # Update settings dialog if it's open
        if hasattr(self, 'settings_dialog_instance') and self.settings_dialog_instance and self.settings_dialog_instance.isVisible():
            self.settings_dialog_instance.update_mode_display(mode_name)
            self.log("Settings dialog mode updated")
    
    def update_tray_menu_checkboxes(self):
            """Update tray menu checkboxes to reflect current settings (without rebuilding)"""
            if not hasattr(self, 'tray_icon') or not self.tray_icon:
                return
            
            try:
                # Get the context menu
                menu = self.tray_icon.contextMenu()
                if not menu:
                    return
                
                # Get current settings
                current_mode = self.router.get_mode()
                current_style = self.config.get('optimization', {}).get('fancy_text_style', 'squared')
                current_max_window = self.config.get('max_sliding_window', 3)
                
                # Update all submenus
                for action in menu.actions():
                    if not action.menu():
                        continue
                    
                    submenu = action.menu()
                    submenu_text = action.text()
                    
                    # Update Mode submenu
                    if submenu_text == "Mode":
                        for mode_action in submenu.actions():
                            if mode_action.text() == "Manual":
                                mode_action.setChecked(current_mode == mode_router.DetectionMode.MANUAL)
                            elif mode_action.text() == "Auto":
                                mode_action.setChecked(current_mode == mode_router.DetectionMode.AUTO)
                    
                    # Update Fancy Text Style submenu
                    elif submenu_text == "Fancy Text Style":
                        for style_action in submenu.actions():
                            # Extract style name from action text (e.g., "Squared (🄵🅄🄲🄺)" -> "squared")
                            action_text = style_action.text().lower()
                            
                            # Check against all style names
                            if "squared" in action_text and "negative" not in action_text:
                                style_action.setChecked(current_style == 'squared')
                            elif "bold italic" in action_text:
                                style_action.setChecked(current_style == 'bold_italic')
                            elif "bold" in action_text and "italic" not in action_text:
                                style_action.setChecked(current_style == 'bold')
                            elif "italic" in action_text and "bold" not in action_text:
                                style_action.setChecked(current_style == 'italic')
                            elif "sans-serif" in action_text or "sans serif" in action_text:
                                style_action.setChecked(current_style == 'sans_serif')
                            elif "circled" in action_text and "negative" not in action_text:
                                style_action.setChecked(current_style == 'circled')
                            elif "negative squared" in action_text:
                                style_action.setChecked(current_style == 'negative_squared')
                            elif "negative circled" in action_text:
                                style_action.setChecked(current_style == 'negative_circled')
                    
                    # Update Max Sliding Window submenu
                    elif submenu_text == "Max Sliding Window":
                        for window_action in submenu.actions():
                            action_text = window_action.text()
                            
                            # Extract window size from text (e.g., "3-word (Default)" -> 3)
                            if "2-word" in action_text or "2 word" in action_text:
                                window_action.setChecked(current_max_window == 2)
                            elif "3-word" in action_text or "3 word" in action_text:
                                window_action.setChecked(current_max_window == 3)
                            elif "4-word" in action_text or "4 word" in action_text:
                                window_action.setChecked(current_max_window == 4)
                            elif "5-word" in action_text or "5 word" in action_text:
                                window_action.setChecked(current_max_window == 5)
                        
            except Exception as e:
                self.log(f"Failed to update tray menu checkboxes: {e}")

    def change_fancy_style(self, style):
        """Change fancy text style"""
        self.log(f"Changing fancy text style to: {style}")
        
        # Update config
        if 'optimization' not in self.config:
            self.config['optimization'] = {}
        self.config['optimization']['fancy_text_style'] = style
        self.config_loader.save(self.config)
        
        # Recreate fancy text converter with new style
        self.fancy = fancy_text.FancyTextConverter(default_style=style)
        
        # Recreate optimizer with new fancy converter
        self.optimizer = message_optimizer.MessageOptimizer(
            self.detector,
            self.leet,
            self.fancy,
            self.shorthand,
            self.config
        )

        # Update tray menu checkboxes
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.update_tray_menu_checkboxes()
        
        # Update router with new optimizer
        self.router.optimizer = self.optimizer
        
        self.log(f"Fancy text style changed to {style}")
    
    def toggle_special_char(self, enabled: bool):
        """Toggle special character interspacing"""
        self.log(f"Special character interspacing {'enabled' if enabled else 'disabled'}")
        
        # Update config
        if 'optimization' not in self.config:
            self.config['optimization'] = {}
        self.config['optimization']['special_char_interspacing'] = enabled
        self.config_loader.save(self.config)
        
        # Update optimizer setting
        self.optimizer.enable_special_char = enabled
        
        # Show notification
        if self.config.get('notifications', {}).get('enabled', True):
            char = self.optimizer.special_char.get_char()
            status = "enabled" if enabled else "disabled"
            self.show_notification(
                f"Special Char Interspacing {status}",
                f"Character: {char}\n"
                f"Normal mode: f{char}uck\n"
                f"Force mode: f{char}u{char}c{char}k",
                duration=3000
            )
    
    def toggle_notifications(self, setting: str, enabled: bool):
        """Toggle notification settings"""
        self.log(f"Notification setting '{setting}' = {enabled}")
        
        # Update config
        if 'notifications' not in self.config:
            self.config['notifications'] = {}
        self.config['notifications'][setting] = enabled
        self.config_loader.save(self.config)

        # Sync to ensure tray menu and settings dialog stay in sync
        self.sync_notification_settings()
    
    def set_notification_duration(self, duration_ms: int):
        """Set notification popup duration"""
        self.log(f"Notification duration set to {duration_ms}ms")
        
        # Update config
        if 'notifications' not in self.config:
            self.config['notifications'] = {}
        self.config['notifications']['duration_ms'] = duration_ms
        self.config_loader.save(self.config)
    
    def set_byte_limit(self, limit: Optional[int]):
        """Set message byte limit"""
        if limit is None:
            self.log("Byte limit disabled")
            limit_str = "disabled"
        else:
            self.log(f"Byte limit set to {limit} bytes")
            limit_str = f"{limit} bytes"
        
        # Update config
        self.config['byte_limit'] = limit if limit is not None else 9999
        self.config_loader.save(self.config)
        
        # Update optimizer
        self.optimizer.byte_limit = self.config['byte_limit']
        
        # Show notification
        if self.config.get('notifications', {}).get('enabled', True):
            self.show_notification(f"Byte limit set to {limit_str}")
    
    def set_character_limit(self, limit: Optional[int]):
        """Set message character limit"""
        if limit is None:
            self.log("Character limit disabled")
            limit_str = "disabled"
        else:
            self.log(f"Character limit set to {limit} characters")
            limit_str = f"{limit} characters"
        
        # Update config
        self.config['character_limit'] = limit if limit is not None else 9999
        self.config_loader.save(self.config)
        
        # Show notification
        if self.config.get('notifications', {}).get('enabled', True):
            self.show_notification(f"Character limit set to {limit_str}")
    
    def set_max_sliding_window(self, window_size: int):
        """Set maximum sliding window size for detection"""
        self.log(f"Max sliding window set to {window_size}-word")
        
        # Update config
        self.config['max_sliding_window'] = window_size
        self.config_loader.save(self.config)
        
        # Update detector (need to rebuild pattern cache if detector exists)
        if hasattr(self, 'detector') and self.detector:
            self.detector.config['max_sliding_window'] = window_size
        
        # Show notification
        if self.config.get('notifications', {}).get('enabled', True):
            self.show_notification(
                "Settings Updated",
                f"Max sliding window: {window_size}-word"
            )

        # Update tray menu checkboxes
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.update_tray_menu_checkboxes()
    
    def show_stats(self):
        """Show statistics"""
        if not PYQT5_AVAILABLE:
            stats = self.get_stats_text()
            print(stats)
            return
        
        stats = self.get_stats_text()
        
        QMessageBox.information(
            None,
            "COCK Profanity Processor - Statistics",
            stats
        )

    def toggle_console(self):
        """Toggle debug window visibility"""
        if self.debug_window:
            if self.debug_window.isVisible():
                self.debug_window.hide()
                self.log("Debug console hidden")
            else:
                self.debug_window.show()
                self.debug_window.raise_()
                self.debug_window.activateWindow()
                self.log("Debug console shown")
        else:
            print("Debug window not available (PyQt5 required)")
        
    def get_stats_text(self):
        """Get statistics as text"""
        
        stats = f"""COCK Profanity Processor Statistics

Detection:
• Mode: {self.router.get_mode().value}
• Whitelist size: {len(self.wl_manager.get_whitelist())}

Optimization:
• Leet-speak: {'✓' if self.config.get('optimization', {}).get('leet_speak', True) else '✗'}
• Fancy Unicode: {'✓' if self.config.get('optimization', {}).get('fancy_unicode', True) else '✗'}
• Shorthand: {'✓' if self.config.get('optimization', {}).get('shorthand', True) else '✗'}
"""
        return stats
    
    def export_filter_list(self):
        """Export loaded filter list to a text file"""
        if not PYQT5_AVAILABLE:
            print("Export filter list requires PyQt5")
            return
        
        try:
            # Check if filter loader exists
            if not hasattr(self, 'filter_loader') or not self.filter_loader:
                QMessageBox.warning(
                    None,
                    "Export Failed",
                    "Filter loader not initialized.\nPlease restart the application."
                )
                return
            
            # Get filter words from filter loader
            if not hasattr(self.filter_loader, 'filter_words') or not self.filter_loader.filter_words:
                QMessageBox.warning(
                    None,
                    "Export Failed",
                    "No filter words available to export.\nThe filter list may be empty."
                )
                return
            
            # Open file dialog
            from PyQt5.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                None,
                "Export Filter List",
                "exported_filter_list.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if not filename:
                # User cancelled
                return
            
            # Sort words alphabetically for easier reading
            sorted_words = sorted(self.filter_loader.filter_words)
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"# Exported Filter List\n")
                f.write(f"# Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total words: {len(sorted_words)}\n")
                f.write(f"# Original file: {self.filter_stats.get('file_path', 'Unknown')}\n")
                f.write(f"# Includes Latin + diacriticals (e.g., Coño, café, Scheiße)\n")
                f.write(f"# Excludes: Pure CJK, emoji, Cyrillic, Arabic\n")
                f.write(f"#\n")
                f.write(f"# Format: One word per line (sorted alphabetically)\n")
                f.write(f"#\n\n")
                
                # Write words
                for word in sorted_words:
                    f.write(f"{word}\n")
            
            self.log(f"Exported {len(sorted_words)} filter words to: {filename}")
            
            # Show success message
            QMessageBox.information(
                None,
                "Export Successful",
                f"Exported {len(sorted_words):,} filter words to:\n\n{filename}\n\n"
                f"You can now search this file to verify what's in the loaded filter.\n\n"
                f"Tip: Search for 'coño' (lowercase) to check if it was loaded."
            )
            
        except Exception as e:
            self.log(f"ERROR: Export failed: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                None,
                "Export Failed",
                f"Failed to export filter list:\n\n{str(e)}"
            )
    
    def quit_app(self):
        """Quit application"""
        self.log("Quitting application...")
        self.running = False
        
        # Stop hotkey listeners
        if self.hotkey:
            self.hotkey.stop()
        if hasattr(self, 'force_hotkey') and self.force_hotkey:
            self.force_hotkey.stop()
        if hasattr(self, 'toggle_hotkey') and self.toggle_hotkey:
            self.toggle_hotkey.stop()
        
        # Close debug window if open
        if hasattr(self, 'debug_window') and self.debug_window:
            self.debug_window.close()
        
        # Quit Qt application
        if PYQT5_AVAILABLE and self.app:
            self.app.quit()
        
        # Exit Python
        sys.exit(0)
    
    def restart_application(self):
        """Restart the application"""
        self.log("Restarting application...")
        
        # Stop hotkeys
        if self.hotkey:
            self.hotkey.stop()
        if hasattr(self, 'force_hotkey') and self.force_hotkey:
            self.force_hotkey.stop()
        if hasattr(self, 'toggle_hotkey') and self.toggle_hotkey:
            self.toggle_hotkey.stop()
        
        # Close Qt application if running
        if PYQT5_AVAILABLE and self.app:
            self.app.quit()
        
        # Sanitize arguments to prevent command injection
        safe_args = []
        for arg in sys.argv:
            if arg.endswith('.py') or arg in ['--debug', '--config']:
                safe_args.append(arg)
            elif arg.startswith('--config='):
                config_path = arg.split('=', 1)[1]
                if os.path.exists(config_path) and config_path.endswith('.json'):
                    safe_args.append(arg)
        
        # Restart using Python
        python = sys.executable
        os.execl(python, python, *safe_args)
    
    def run(self):
        """Run the application"""
        try:
            # Initialize modules
            if not self.initialize():
                print("Failed to initialize. Exiting.")
                return 1
            
            # Setup hotkey
            if not self.setup_hotkey():
                self.logger.warning("Running without hotkey support")
            
            # Setup GUI if available
            if PYQT5_AVAILABLE:
                # Use existing app if provided (from splash screen), otherwise create new one
                if not self.app:
                    self.app = QApplication(sys.argv)
                    
                self.app.setApplicationName("COCK Profanity Processor")
                self.app.setQuitOnLastWindowClosed(False)  # Keep running in tray

                # Set application-wide icon
                icon_path = path_manager.get_resource_file('icons/icon.ico')
                if os.path.exists(icon_path):
                    from PyQt5.QtGui import QIcon
                    self.app.setWindowIcon(QIcon(icon_path))
                
                # Initialize UI components now that QApplication exists
                self.init_ui()
                
                # Setup tray icon
                self.setup_tray_icon()
                
                self.running = True
                print("\n" + "="*50)
                print("COCK Profanity Processor is running!")
                print(f"Mode: {self.router.get_mode().value}")
                
                # Get hotkey string from config (handle both formats)
                hotkey_config = self.config.get('hotkey', 'ctrl+shift+v')
                if isinstance(hotkey_config, dict):
                    hotkey_str = hotkey_config.get('combo', 'ctrl+shift+v')
                else:
                    hotkey_str = hotkey_config
                print(f"Hotkey: {hotkey_str}")
                
                print("Right-click tray icon for options")
                print("="*50 + "\n")

                # Show settings window after splash screen fades out completely
                # Splash duration is 3000ms, so delay 3200ms to ensure fade is complete
                self.log("Scheduling auto-show settings in 3200ms...")
                QTimer.singleShot(3200, self.show_settings)
                
                # Run event loop
                return self.app.exec_()
            else:
                # Console mode
                self.running = True
                print("\n" + "="*50)
                print("COCK Profanity Processor is running (console mode)")
                
                # Get hotkey string from config (handle both formats)
                hotkey_config = self.config.get('hotkey', 'ctrl+shift+v')
                if isinstance(hotkey_config, dict):
                    hotkey_str = hotkey_config.get('combo', 'ctrl+shift+v')
                else:
                    hotkey_str = hotkey_config
                print(f"Hotkey: {hotkey_str}")
                
                print("Press Ctrl+C to quit")
                print("="*50 + "\n")
                
                # Keep running
                try:
                    while self.running:
                        import time
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    print("\nShutting down...")
                
                return 0
            
        except Exception as e:
            self.logger.error(f"Application failed: {e}")
            if self.debug:
                traceback.print_exc()
            return 1


def main():
    """Main entry point"""
    import sys
    
    # Check for single instance
    if not check_single_instance():
        if PYQT5_AVAILABLE:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            QMessageBox.warning(
                None,
                "Already Running",
                "COCK Profanity Processor is already running.\n\nCheck your system tray."
            )
        else:
            print("ERROR: COCK Profanity Processor is already running")
        return 1
    
    # Create QApplication first (required for splash)
    app = None
    splash = None
    
    if PYQT5_AVAILABLE:
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        
        # Show splash screen
        try:
            import splash_screen
            splash = splash_screen.show_splash(app, duration=3000)
            # Process events so splash actually appears
            app.processEvents()
        except ImportError:
            print("INFO: Splash screen module not found, skipping splash")
            splash = None
        except Exception as e:
            print(f"WARNING: Could not show splash screen: {e}")
            splash = None
    
    # Load configuration (allow splash to animate)
    if app:
        app.processEvents()
    
    config_loader_instance = config_loader.ConfigLoader()
    config = config_loader_instance.load()
    
    # Process events after loading config
    if app:
        app.processEvents()
    
    parser = argparse.ArgumentParser(
        description="Compliant Online Chat Kit"
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to config file'
    )
    
    args = parser.parse_args()

    # Initialize centralized logging (v1.1 feature)
    from COCK import logger
    app_logger = logger.setup_logger(
        name="COCK",
        level="DEBUG" if args.debug else "INFO",
        log_to_file=True,
        log_to_console=True,
        debug_mode=args.debug
    )
    app_logger.info("="*60)
    app_logger.info("COCK Profanity Processor - Application Starting")
    app_logger.info("="*60)
    app_logger.info(f"Debug mode: {args.debug}")
    if args.config:
        app_logger.info(f"Config file: {args.config}")

    # Process events before creating tool
    if app:
        app.processEvents()

    # Create application instance, passing the app if we created one
    tool = COCK(config_path=args.config, debug=args.debug, app=app)
    
    # Process events after tool creation
    if app:
        app.processEvents()
    
    # Run application
    return tool.run()


if __name__ == '__main__':
    sys.exit(main())