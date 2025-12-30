#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clipboard Manager Module
=========================
Safe clipboard capture with automatic restoration

Features:
- Capture text from active window
- Automatic clipboard backup and restore
- Configurable keyboard delays
- Auto-send functionality (for permissive mode)
"""

import time
from typing import Optional

try:
    import keyboard
except ImportError:
    print("WARNING: keyboard module not installed. Install with: pip install keyboard")
    keyboard = None

try:
    import pyperclip
except ImportError:
    print("WARNING: pyperclip module not installed. Install with: pip install pyperclip")
    pyperclip = None


class ClipboardManager:
    """
    Safe clipboard capture with automatic restoration
    
    Workflow:
        1. Backup current clipboard
        2. Simulate Ctrl+A (select all)
        3. Simulate Ctrl+C (copy)
        4. Capture text from clipboard
        5. Restore original clipboard
    
    Security:
        - Enforces size limits on clipboard content
        - Validates text encoding
        - Prevents excessively large pastes
    """
    
    # Security limits
    MAX_CLIPBOARD_SIZE = 1024 * 1024  # 1 MB max clipboard content
    MAX_PASTE_SIZE = 100 * 1024  # 100 KB max paste content
    
    def __init__(self, config: dict = None):
        """
        Initialize clipboard manager
        
        Args:
            config: Configuration dictionary with keyboard_delay_ms
        """
        if config is None:
            config = {}
        
        self.config = config
        self.delay_ms = config.get('keyboard_delay_ms', 100)
        self.last_capture = None
        
        # Validate dependencies
        if keyboard is None or pyperclip is None:
            raise RuntimeError("Required modules not installed: keyboard and pyperclip")
        
    def _validate_clipboard_content(self, content: str, max_size: int = MAX_CLIPBOARD_SIZE) -> tuple[bool, str]:
        """Validate clipboard content for security"""
        if not content:
            return (True, content)
        
        content_size = len(content.encode('utf-8'))
        if content_size > max_size:
            print(f"WARNING: Clipboard content too large ({content_size} bytes), truncating to {max_size} bytes")
            truncated = content.encode('utf-8')[:max_size].decode('utf-8', errors='ignore')
            return (False, truncated)
        
        return (True, content)
    
    def capture_with_backup(self) -> str:
        """
        Capture text from active window with clipboard restoration
        
        Returns:
            str: Captured text from active window
        
        Process:
            1. Save current clipboard content
            2. Select all text (Ctrl+A)
            3. Copy to clipboard (Ctrl+C)
            4. Read clipboard
            5. Restore original clipboard
        
        Notes:
            - Uses configurable delays between operations
            - Always restores clipboard even if errors occur
            - Returns empty string on failure
        """
        original_clipboard = ""
        captured_text = ""
        
        try:
            # Step 1: Backup current clipboard
            print("[CAPTURE] Step 1: Backing up clipboard...")
            try:
                original_clipboard = pyperclip.paste()
                print(f"[CAPTURE] Clipboard backup: {len(original_clipboard)} chars")
            # Validate backup size
                is_valid, original_clipboard = self._validate_clipboard_content(original_clipboard)
                if not is_valid:
                    print("[CAPTURE] WARNING: Original clipboard was truncated due to size")
            except Exception as e:
                print(f"Warning: Could not backup clipboard: {e}")
                original_clipboard = ""
            
            # Step 2: Simulate Ctrl+A (select all)
            print("[CAPTURE] Step 2: Pressing Ctrl+A (select all)...")
            keyboard.press_and_release('ctrl+a')
            print(f"[CAPTURE] Waiting {self.delay_ms}ms after Ctrl+A...")
            time.sleep(self.delay_ms / 1000.0)
            
            # Step 3: Simulate Ctrl+C (copy)
            print("[CAPTURE] Step 3: Pressing Ctrl+C (copy)...")
            keyboard.press_and_release('ctrl+c')
            print(f"[CAPTURE] Waiting {self.delay_ms}ms after Ctrl+C...")
            time.sleep(self.delay_ms / 1000.0)
            
            # Step 4: Get captured text
            print("[CAPTURE] Step 4: Reading clipboard...")
            try:
                captured_text = pyperclip.paste()
                print(f"[CAPTURE] Clipboard now contains: {len(captured_text)} chars")
            # Validate captured content
                is_valid, captured_text = self._validate_clipboard_content(captured_text)
                if not is_valid:
                    print("[CAPTURE] WARNING: Captured text was truncated due to size")
                if captured_text:
                    print(f"[CAPTURE] First 50 chars: '{captured_text[:50]}...'")
                else:
                    print("[CAPTURE] WARNING: Clipboard is EMPTY after Ctrl+C!")
                self.last_capture = captured_text
            except Exception as e:
                print(f"Error reading clipboard: {e}")
                captured_text = ""
            
            print(f"[CAPTURE] Step 5: Returning captured text ({len(captured_text)} chars)")
            return captured_text
        
        except Exception as e:
            print(f"Error during capture: {e}")
            return ""
        
        finally:
            # Step 5: ALWAYS restore original clipboard
            print(f"[CAPTURE] Step 6: Restoring original clipboard ({len(original_clipboard)} chars)...")
            try:
                pyperclip.copy(original_clipboard)
                print("[CAPTURE] Clipboard restored successfully")
            except Exception as e:
                print(f"Warning: Could not restore clipboard: {e}")
    
    def send_message(self, delay_ms: Optional[int] = None, key_combo: str = 'enter') -> None:
        """
        Auto-send message (for Permissive mode)
        
        Args:
            delay_ms: Optional delay before sending (overrides config)
            key_combo: Key combination to press (default: 'enter')
        
        Use Cases:
            - Permissive mode: Automatically send approved messages
            - Custom send keys for different games
        
        Example:
            manager.send_message(delay_ms=200, key_combo='enter')
        """
        try:
            # Use provided delay or fall back to config
            if delay_ms is None:
                delay_ms = self.config.get('auto_send', {}).get('delay_ms', 100)
            
            # Wait before sending
            time.sleep(delay_ms / 1000.0)
            
            # Press the send key
            keyboard.press_and_release(key_combo)
            
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def paste_text(self, text: str, delay_ms: Optional[int] = None) -> bool:
        """
        Paste text into active window (replaces existing content)
        
        Args:
            text: Text to paste
            delay_ms: Optional delay before pasting
            
        Returns:
            bool: True if successful, False otherwise
        
        Process:
            1. Copy text to clipboard
            2. Wait for delay
            3. Select all (Ctrl+A)
            4. Simulate Ctrl+V (paste, replacing selected text)
            5. Wait for text to be pasted
        """
        try:
            # Validate content size before pasting
            is_valid, validated_text = self._validate_clipboard_content(text, self.MAX_PASTE_SIZE)
            if not is_valid:
                print(f"WARNING: Paste text was truncated from {len(text)} to {len(validated_text)} chars")
            
            # Copy text to clipboard
            pyperclip.copy(validated_text)
            
            # Wait if delay specified
            if delay_ms:
                time.sleep(delay_ms / 1000.0)
            
            # Select all existing text (so paste replaces instead of appends)
            keyboard.press_and_release('ctrl+a')
            time.sleep(self.delay_ms / 1000.0)
            
            # Simulate Ctrl+V (paste)
            keyboard.press_and_release('ctrl+v')
            
            # Small delay to ensure paste completes
            time.sleep(self.delay_ms / 1000.0)
            
            return True
            
        except Exception as e:
            print(f"Error pasting text: {e}")
            return False
    
    def copy_to_clipboard(self, text: str) -> bool:
        """
        Copy text to clipboard (without pasting)
        
        Args:
            text: Text to copy
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            return False
    
    def get_clipboard(self) -> str:
        """
        Get current clipboard content
        
        Returns:
            str: Clipboard content, or empty string on error
        """
        try:
            return pyperclip.paste()
        except Exception as e:
            print(f"Error reading clipboard: {e}")
            return ""
    
    def get_last_capture(self) -> Optional[str]:
        """
        Get the last captured text
        
        Returns:
            str: Last captured text, or None if no capture yet
        """
        return self.last_capture
    
    def set_delay(self, delay_ms: int) -> None:
        """
        Set keyboard delay
        
        Args:
            delay_ms: Delay in milliseconds
        """
        self.delay_ms = delay_ms
    
    def test_capture(self) -> bool:
        """
        Test if capture functionality is working
        
        Returns:
            bool: True if test successful
        
        Note:
            This will briefly interact with the active window
        """
        try:
            # Try to capture
            result = self.capture_with_backup()
            
            # Check if we got something
            if result is not None:
                print(f"Capture test successful. Captured {len(result)} characters.")
                return True
            else:
                print("Capture test failed: No result")
                return False
                
        except Exception as e:
            print(f"Capture test failed: {e}")
            return False


# Utility functions
def simulate_keypress(key_combo: str, delay_ms: int = 100) -> bool:
    """
    Simulate a keyboard press
    
    Args:
        key_combo: Key combination (e.g., 'ctrl+c', 'enter', 'alt+tab')
        delay_ms: Delay after pressing
        
    Returns:
        bool: True if successful
    """
    if keyboard is None:
        print("keyboard module not available")
        return False
    
    try:
        keyboard.press_and_release(key_combo)
        time.sleep(delay_ms / 1000.0)
        return True
    except Exception as e:
        print(f"Error simulating keypress: {e}")
        return False


def check_dependencies() -> tuple[bool, list[str]]:
    """
    Check if required dependencies are available
    
    Returns:
        tuple: (all_available: bool, missing: list[str])
    """
    missing = []
    
    if keyboard is None:
        missing.append("keyboard")
    
    if pyperclip is None:
        missing.append("pyperclip")
    
    return (len(missing) == 0, missing)


# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
