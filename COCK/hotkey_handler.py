#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hotkey Handler Module
======================
Global hotkey registration and management

Features:
- Register global hotkeys
- Background thread monitoring
- Callback on hotkey press
- Safe start/stop
"""

import logging
from typing import Callable, Optional

try:
    import keyboard
except ImportError:
    print("WARNING: keyboard module not installed. Install with: pip install keyboard")
    keyboard = None


class HotkeyHandler:
    """
    Global hotkey registration and management
    
    Usage:
        handler = HotkeyHandler('ctrl+shift+c', on_hotkey_pressed)
        handler.start()
        # ... application runs ...
        handler.stop()
    """
    
    def __init__(self, hotkey: str, callback: Callable[[], None]):
        """
        Initialize hotkey handler
        
        Args:
            hotkey: Hotkey combination (e.g., 'ctrl+shift+c')
            callback: Function to call when hotkey is pressed
        
        Examples:
            HotkeyHandler('ctrl+shift+c', my_function)
            HotkeyHandler('f1', on_help)
            HotkeyHandler('ctrl+alt+d', toggle_debug)
        """
        if keyboard is None:
            raise RuntimeError("keyboard module not installed")
        
        self.hotkey = hotkey
        self.callback = callback
        self.is_running = False
        self._hotkey_id = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def start(self) -> bool:
        """
        Register hotkey and start listening
        
        Returns:
            bool: True if started successfully, False otherwise
        
        Note:
            - Runs in background thread automatically
            - Can be called multiple times safely (idempotent)
            - Returns False if already running
        """
        if self.is_running:
            self.logger.warning("Hotkey handler already running")
            return False
        
        try:
            # Register hotkey with keyboard module
            keyboard.add_hotkey(self.hotkey, self._on_hotkey)
            
            self.is_running = True
            self.logger.info(f"Hotkey registered: {self.hotkey}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering hotkey '{self.hotkey}': {e}")
            return False
    
    def stop(self) -> bool:
        """
        Unregister hotkey and stop listening
        
        Returns:
            bool: True if stopped successfully, False otherwise
        
        Note:
            - Safe to call even if not running
            - Cleans up background thread
        """
        if not self.is_running:
            self.logger.warning("Hotkey handler not running")
            return False
        
        try:
            # Unregister hotkey
            keyboard.remove_hotkey(self.hotkey)
            
            self.is_running = False
            self.logger.info(f"Hotkey unregistered: {self.hotkey}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error unregistering hotkey '{self.hotkey}': {e}")
            return False
    
    def _on_hotkey(self) -> None:
        """
        Internal callback wrapper
        
        Wraps user callback with error handling
        """
        try:
            self.callback()
        except Exception as e:
            self.logger.error(f"Hotkey callback error: {e}", exc_info=True)
    
    def is_active(self) -> bool:
        """
        Check if hotkey handler is active
        
        Returns:
            bool: True if listening for hotkey
        """
        return self.is_running
    
    def change_hotkey(self, new_hotkey: str) -> bool:
        """
        Change the hotkey combination
        
        Args:
            new_hotkey: New hotkey combination
            
        Returns:
            bool: True if changed successfully
        
        Note:
            - Automatically stops and restarts if running
            - Returns False if new hotkey is invalid
        """
        was_running = self.is_running
        
        # Stop current hotkey if running
        if was_running:
            self.stop()
        
        # Update hotkey
        old_hotkey = self.hotkey
        self.hotkey = new_hotkey
        
        # Restart if it was running
        if was_running:
            success = self.start()
            if success:
                self.logger.info(f"Hotkey changed: {old_hotkey} -> {new_hotkey}")
                return True
            else:
                # Failed to start with new hotkey, revert
                self.hotkey = old_hotkey
                self.start()  # Try to restore old hotkey
                self.logger.error(f"Failed to change hotkey to '{new_hotkey}', reverted to '{old_hotkey}'")
                return False
        else:
            self.logger.info(f"Hotkey updated (not running): {old_hotkey} -> {new_hotkey}")
            return True
    
    def get_hotkey(self) -> str:
        """
        Get current hotkey combination
        
        Returns:
            str: Current hotkey
        """
        return self.hotkey
    
    def __del__(self):
        """
        Cleanup on deletion
        """
        if self.is_running:
            self.stop()


class MultiHotkeyHandler:
    """
    Manage multiple hotkeys
    
    Usage:
        manager = MultiHotkeyHandler()
        manager.add_hotkey('ctrl+shift+c', on_capture)
        manager.add_hotkey('ctrl+shift+s', on_settings)
        manager.start_all()
    """
    
    def __init__(self):
        """Initialize multi-hotkey manager"""
        self.handlers = {}
        self.logger = logging.getLogger(__name__)
    
    def add_hotkey(self, name: str, hotkey: str, callback: Callable[[], None]) -> bool:
        """
        Add a hotkey
        
        Args:
            name: Unique name for this hotkey
            hotkey: Hotkey combination
            callback: Function to call
            
        Returns:
            bool: True if added successfully
        """
        if name in self.handlers:
            self.logger.warning(f"Hotkey '{name}' already exists")
            return False
        
        try:
            handler = HotkeyHandler(hotkey, callback)
            self.handlers[name] = handler
            return True
        except Exception as e:
            self.logger.error(f"Error adding hotkey '{name}': {e}")
            return False
    
    def remove_hotkey(self, name: str) -> bool:
        """
        Remove a hotkey
        
        Args:
            name: Name of hotkey to remove
            
        Returns:
            bool: True if removed successfully
        """
        if name not in self.handlers:
            self.logger.warning(f"Hotkey '{name}' not found")
            return False
        
        # Stop if running
        handler = self.handlers[name]
        if handler.is_active():
            handler.stop()
        
        del self.handlers[name]
        return True
    
    def start_all(self) -> None:
        """Start all hotkey handlers"""
        for name, handler in self.handlers.items():
            if not handler.is_active():
                handler.start()
    
    def stop_all(self) -> None:
        """Stop all hotkey handlers"""
        for handler in self.handlers.values():
            if handler.is_active():
                handler.stop()
    
    def start_hotkey(self, name: str) -> bool:
        """
        Start a specific hotkey
        
        Args:
            name: Name of hotkey to start
            
        Returns:
            bool: True if started successfully
        """
        if name not in self.handlers:
            return False
        return self.handlers[name].start()
    
    def stop_hotkey(self, name: str) -> bool:
        """
        Stop a specific hotkey
        
        Args:
            name: Name of hotkey to stop
            
        Returns:
            bool: True if stopped successfully
        """
        if name not in self.handlers:
            return False
        return self.handlers[name].stop()
    
    def get_status(self) -> dict:
        """
        Get status of all hotkeys
        
        Returns:
            dict: {name: is_active}
        """
        return {
            name: handler.is_active()
            for name, handler in self.handlers.items()
        }


def validate_hotkey(hotkey: str) -> bool:
    """
    Validate hotkey string format
    
    Args:
        hotkey: Hotkey combination to validate
        
    Returns:
        bool: True if valid format
    
    Examples:
        validate_hotkey('ctrl+c') -> True
        validate_hotkey('ctrl+shift+c') -> True
        validate_hotkey('f1') -> True
        validate_hotkey('invalid') -> False
    """
    if keyboard is None:
        return False
    
    try:
        # Try to parse the hotkey
        # keyboard library will raise exception if invalid
        keyboard.parse_hotkey(hotkey)
        return True
    except Exception:
        return False


def test_hotkey(hotkey: str, timeout_seconds: int = 5) -> bool:
    """
    Test a hotkey by waiting for it to be pressed
    
    Args:
        hotkey: Hotkey to test
        timeout_seconds: How long to wait for press
        
    Returns:
        bool: True if hotkey was pressed during timeout
    
    Note:
        This is a blocking function for testing purposes
    """
    if keyboard is None:
        print("keyboard module not available")
        return False
    
    print(f"Press '{hotkey}' within {timeout_seconds} seconds...")
    
    try:
        # Wait for the hotkey with timeout
        keyboard.wait(hotkey, timeout_seconds)
        print(f"Hotkey '{hotkey}' detected!")
        return True
    except Exception:
        print(f"Timeout: '{hotkey}' not pressed")
        return False


# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
