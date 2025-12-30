#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whitelist Manager Module
=========================
Manages whitelist for detection system

Features:
- Load/save whitelist file
- Add/remove words dynamically
- Thread-safe operations
"""

import os
from typing import Set, Optional
import threading


class WhitelistManager:
    """
    Manages whitelist file
    
    Whitelist: Words that are safe when embedded (e.g., "ass" in "assassin")
    These words are NOT flagged for optimization when found embedded in larger words.
    Standalone instances are still flagged.
    """
    
    def __init__(self, whitelist_path: str):
        """
        Initialize whitelist manager
        
        Args:
            whitelist_path: Path to whitelist file
        """
        self.whitelist_path = whitelist_path
        self.whitelist: Set[str] = set()
        
        # Thread lock for safe concurrent access
        self._lock = threading.Lock()
        
        # Load existing file
        self._load_whitelist()
    
    def _load_whitelist(self) -> None:
        """Load whitelist from file"""
        self.whitelist = self._load_word_file(self.whitelist_path)
    
    def _load_word_file(self, filepath: str) -> Set[str]:
        """
        Load words from file
        
        Args:
            filepath: Path to word file
            
        Returns:
            set: Set of words (lowercase)
        """
        words = set()
        
        if not os.path.exists(filepath):
            return words
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    # Strip whitespace and convert to lowercase
                    word = line.strip().lower()
                    
                    # Skip empty lines and comments
                    if word and not word.startswith('#'):
                        words.add(word)
        except Exception as e:
            print(f"WARNING: Failed to load {filepath}: {e}")
        
        return words
    
    def get_whitelist(self) -> Set[str]:
        """
        Get current whitelist
        
        Returns:
            set: Set of whitelisted words
        """
        with self._lock:
            return self.whitelist.copy()
    
    def add_to_whitelist(self, word: str) -> bool:
        """
        Add word to whitelist
        
        Args:
            word: Word to add
            
        Returns:
            bool: True if successful
        """
        if not word:
            return False
        
        word_lower = word.strip().lower()
        
        if not word_lower:
            return False
        
        with self._lock:
            # Add to whitelist
            self.whitelist.add(word_lower)
            
            # Save to file
            return self._save_whitelist()
    
    def remove_from_whitelist(self, word: str) -> bool:
        """
        Remove word from whitelist
        
        Args:
            word: Word to remove
            
        Returns:
            bool: True if successful
        """
        if not word:
            return False
        
        word_lower = word.strip().lower()
        
        with self._lock:
            if word_lower in self.whitelist:
                self.whitelist.remove(word_lower)
                return self._save_whitelist()
            else:
                return False
    
    def is_whitelisted(self, word: str) -> bool:
        """
        Check if word is whitelisted
        
        Args:
            word: Word to check
            
        Returns:
            bool: True if whitelisted
        """
        if not word:
            return False
        
        word_lower = word.strip().lower()
        
        with self._lock:
            return word_lower in self.whitelist
    
    def _save_whitelist(self) -> bool:
        """
        Save whitelist to file
        
        Returns:
            bool: True if successful
        """
        try:
            with open(self.whitelist_path, 'w', encoding='utf-8') as f:
                f.write("# Whitelist - Words safe when embedded\n")
                f.write("# These words are NOT flagged when found embedded in larger words\n")
                f.write("# Example: 'ass' is safe in 'assassin' but flagged when standalone\n\n")
                
                for word in sorted(self.whitelist):
                    f.write(f"{word}\n")
            
            return True
        except Exception as e:
            print(f"ERROR: Failed to save whitelist: {e}")
            return False
    
    def export_words(self) -> Set[str]:
        """
        Export whitelist as a set
        
        Returns:
            set: Set of whitelisted words
        """
        with self._lock:
            return self.whitelist.copy()


# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
