#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Watcher Module
===================
Monitors filter and config files for external changes

Features:
- Auto-reload filter list when file changes externally
- Debouncing to prevent rapid reload spam
- Thread-safe observer pattern
- Error-tolerant callback execution

Usage:
    from COCK.file_watcher import FileWatcher

    watcher = FileWatcher()
    watcher.watch_file('/path/to/filter.txt', lambda: reload_filter())
    watcher.start()
    # ... later ...
    watcher.stop()

Version: 1.0.3
"""

import time
from pathlib import Path
from typing import Callable, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from logger import get_logger

# Module logger
log = get_logger(__name__)


class FilterFileHandler(FileSystemEventHandler):
    """
    Handle filter file change events

    Monitors a specific file for modifications and triggers a callback
    when the file changes. Uses trailing-edge debounce to wait for
    file writes to complete before triggering.
    """

    def __init__(self, filepath: str, callback: Callable):
        """
        Initialize file handler

        Args:
            filepath: Absolute path to file to monitor
            callback: Function to call when file changes
        """
        import threading
        self.filepath = Path(filepath).resolve()
        self.callback = callback
        self.debounce_seconds = 0.3  # Wait 300ms after LAST change (trailing edge)
        self._timer = None
        self._lock = threading.Lock()

    def on_modified(self, event):
        """
        File modified event handler

        Uses trailing-edge debounce: waits for events to stop,
        then triggers callback after debounce period.

        Args:
            event: FileSystemEvent from watchdog
        """
        if event.is_directory:
            return

        # Check if it's our file
        changed_file = Path(event.src_path).resolve()
        if changed_file != self.filepath:
            return

        # Trailing-edge debounce: cancel existing timer, start new one
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                log.debug(f"Reset debounce timer for {self.filepath.name}")

            # Start new timer - callback fires after debounce_seconds of no events
            import threading
            self._timer = threading.Timer(self.debounce_seconds, self._trigger_callback)
            self._timer.start()

    def _trigger_callback(self):
        """Execute callback after debounce period"""
        log.info(f"File change detected (after debounce): {self.filepath}")
        try:
            self.callback()
        except Exception as e:
            log.error(f"Reload callback failed: {e}")


class FileWatcher:
    """
    Watch files for changes and trigger callbacks

    Uses watchdog library to monitor files and directories for changes.
    Supports multiple files with different callbacks.

    Example:
        watcher = FileWatcher()
        watcher.watch_file('/path/to/filter.txt', reload_filter)
        watcher.watch_file('/path/to/config.json', reload_config)
        watcher.start()
    """

    def __init__(self):
        """Initialize file watcher"""
        self.observer = Observer()
        self.handlers: Dict[str, FileSystemEventHandler] = {}

    def watch_file(self, filepath: str, callback: Callable):
        """
        Watch file for changes

        Args:
            filepath: Absolute path to file
            callback: Function to call when file changes (no arguments)

        Example:
            watcher.watch_file('/path/to/filter.txt', lambda: self.reload_filter())
        """
        filepath = Path(filepath).resolve()
        watch_dir = filepath.parent

        # Create handler
        handler = FilterFileHandler(str(filepath), callback)
        self.handlers[str(filepath)] = handler

        # Schedule observer
        self.observer.schedule(handler, str(watch_dir), recursive=False)
        log.info(f"Watching file: {filepath}")

    def start(self):
        """Start watching files"""
        if not self.observer.is_alive():
            self.observer.start()
            log.info("File watcher started")

    def stop(self):
        """Stop watching files"""
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=1.0)
            log.info("File watcher stopped")

    def is_running(self) -> bool:
        """
        Check if watcher is running

        Returns:
            bool: True if observer is alive
        """
        return self.observer.is_alive()


# Module information
__version__ = '1.0.3'
__author__ = 'Jokoril'
