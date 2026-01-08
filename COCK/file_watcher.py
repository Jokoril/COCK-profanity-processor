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
    when the file changes. Includes debouncing to prevent rapid reloads.
    """

    def __init__(self, filepath: str, callback: Callable):
        """
        Initialize file handler

        Args:
            filepath: Absolute path to file to monitor
            callback: Function to call when file changes
        """
        self.filepath = Path(filepath).resolve()
        self.callback = callback
        self.last_modified = 0
        self.debounce_seconds = 0.5  # Wait 500ms after last change

    def on_modified(self, event):
        """
        File modified event handler

        Args:
            event: FileSystemEvent from watchdog
        """
        if event.is_directory:
            return

        # Check if it's our file
        changed_file = Path(event.src_path).resolve()
        if changed_file != self.filepath:
            return

        # Debounce rapid changes
        current_time = time.time()
        if current_time - self.last_modified < self.debounce_seconds:
            log.debug(f"Debounced change to {self.filepath.name}")
            return

        self.last_modified = current_time
        log.info(f"Filter file changed: {self.filepath}")

        # Call reload callback
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
