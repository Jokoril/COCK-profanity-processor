#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leet Speak Module
=================
Character substitution for censorship evasion

Features:
- Common leet-speak substitutions (a→4, e→3, o→0, etc.)
- Zero byte overhead (same character count)
- Configurable substitution rules
- Reversible mappings

Usage:
    from leet_speak import LeetSpeakConverter
    
    converter = LeetSpeakConverter()
    result = converter.convert("hello")  # "h3ll0"
"""

from typing import Dict, List, Optional


class LeetSpeakConverter:
    """
    Converts text to leet-speak for censorship evasion
    
    Common substitutions:
        a/A → 4         s/S → 5 or $
        e/E → 3         t/T → 7
        i/I → 1 or !    o/O → 0
        l/L → 1         g/G → 9
        b/B → 8         z/Z → 2
    """
    
    # Default leet-speak mapping
    DEFAULT_MAPPING = {
        'a': '4', 'A': '4',
        'e': '3', 'E': '€',
        'i': '!', 'I': '!',
        'o': '0', 'O': '0',
        's': '5', 'S': '$',
        'l': '|', 'L': '|',
        'z': '2', 'Z': '2',
        'c': '¢', 'C': '¢',
    }
    
    # Alternative mappings for variety
    ALTERNATIVE_MAPPING = {
        'a': '@', 'A': '@',
        's': '$', 'S': '$',
        'i': '1', 'I': '1',
    }
    
    def __init__(self, custom_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize leet speak converter
        
        Args:
            custom_mapping: Optional custom character mapping
        """
        if custom_mapping:
            self.mapping = custom_mapping
        else:
            # Combine default and alternative mappings
            self.mapping = self.DEFAULT_MAPPING.copy()
    
    def convert(self, text: str, positions: Optional[List[int]] = None) -> str:
        """
        Convert text to leet-speak
        
        Args:
            text: Text to convert
            positions: Optional list of character positions to convert
                      If None, converts all applicable characters
        
        Returns:
            str: Leet-speak version of text
        
        Examples:
            convert("hello") → "h3ll0"
            convert("assassin") → "4ss4ss1n"
            convert("secret") → "s3cr37"
        """
        if not text:
            return text
        
        result = list(text)
        
        if positions is None:
            # Convert all applicable characters
            for i, char in enumerate(result):
                if char in self.mapping:
                    result[i] = self.mapping[char]
        else:
            # Convert only specified positions
            for pos in positions:
                if 0 <= pos < len(result) and result[pos] in self.mapping:
                    result[pos] = self.mapping[result[pos]]
        
        return ''.join(result)
    
    def convert_word(self, word: str, strategy: str = 'vowels') -> str:
        """
        Convert a specific word with a strategy
        
        Args:
            word: Word to convert
            strategy: Conversion strategy
                     'vowels' - Convert all vowels
                     'all' - Convert all applicable characters
                     'minimal' - Convert only first occurrence of each
        
        Returns:
            str: Converted word
        
        Examples:
            convert_word("assassin", "vowels") → "4ss4ss1n"
            convert_word("assassin", "minimal") → "4ssassin"
        """
        if strategy == 'vowels':
            # Convert only vowels
            vowels = set('aeiouAEIOU')
            positions = [i for i, c in enumerate(word) if c in vowels]
            return self.convert(word, positions)
        
        elif strategy == 'minimal':
            # Convert only first occurrence of each convertible character
            seen = set()
            positions = []
            for i, c in enumerate(word):
                if c in self.mapping and c.lower() not in seen:
                    positions.append(i)
                    seen.add(c.lower())
            return self.convert(word, positions)
        
        else:  # 'all'
            return self.convert(word)
    
    def get_variations(self, word: str, max_variations: int = 5) -> List[str]:
        """
        Generate multiple leet-speak variations of a word
        
        Args:
            word: Word to generate variations for
            max_variations: Maximum number of variations to generate
        
        Returns:
            list: List of leet-speak variations
        
        Examples:
            get_variations("ass") → ["4ss", "ass", "a5s", "45s"]
        """
        variations = [word]  # Include original
        
        # Get all convertible positions
        convertible = [(i, c) for i, c in enumerate(word) if c in self.mapping]
        
        if not convertible:
            return variations
        
        # Strategy 1: Convert all
        variations.append(self.convert(word))
        
        # Strategy 2: Convert vowels only
        variations.append(self.convert_word(word, 'vowels'))
        
        # Strategy 3: Convert consonants only
        vowels = set('aeiouAEIOU')
        consonant_positions = [i for i, c in enumerate(word) if c not in vowels and c in self.mapping]
        if consonant_positions:
            variations.append(self.convert(word, consonant_positions))
        
        # Strategy 4: Convert first and last convertible chars
        if len(convertible) >= 2:
            first_last = [convertible[0][0], convertible[-1][0]]
            variations.append(self.convert(word, first_last))
        
        # Remove duplicates and limit
        variations = list(dict.fromkeys(variations))  # Preserve order
        return variations[:max_variations]
    
    def is_leet_speak(self, text: str) -> bool:
        """
        Check if text contains leet-speak characters
        
        Args:
            text: Text to check
        
        Returns:
            bool: True if text appears to use leet-speak
        """
        leet_chars = set(self.mapping.values())
        return any(c in leet_chars for c in text)
    
    def reverse(self, text: str) -> str:
        """
        Attempt to reverse leet-speak back to normal text
        
        Args:
            text: Leet-speak text
        
        Returns:
            str: Normalized text (best guess)
        
        Note: This is approximate since some substitutions are ambiguous
              (e.g., '1' could be 'i' or 'l')
        """
        # Create reverse mapping (prefer lowercase)
        reverse_map = {}
        for char, leet in self.mapping.items():
            if leet not in reverse_map:
                reverse_map[leet] = char.lower()
        
        result = []
        for char in text:
            result.append(reverse_map.get(char, char))
        
        return ''.join(result)
    
    def add_mapping(self, char: str, replacement: str):
        """
        Add a custom character mapping
        
        Args:
            char: Character to replace
            replacement: Replacement character
        """
        self.mapping[char] = replacement
    
    def remove_mapping(self, char: str):
        """
        Remove a character mapping
        
        Args:
            char: Character to remove from mapping
        """
        if char in self.mapping:
            del self.mapping[char]
    
    def get_stats(self) -> Dict:
        """
        Get converter statistics
        
        Returns:
            dict: Statistics about the converter
        """
        return {
            'total_mappings': len(self.mapping),
            'unique_replacements': len(set(self.mapping.values())),
            'mapping_preview': dict(list(self.mapping.items())[:5])
        }


# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
