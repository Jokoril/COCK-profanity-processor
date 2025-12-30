#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fancy Text Module
=================
Unicode character substitution for censorship evasion

Features:
- Unicode lookalike characters (A→𝐀, a→𝚊, etc.)
- Multiple Unicode styles (bold, italic, circled, etc.)
- Larger byte overhead (+3 bytes per character typically)
- Visual similarity preservation

Warning: Some games may not support Unicode characters

Usage:
    from fancy_text import FancyTextConverter
    
    converter = FancyTextConverter()
    result = converter.convert("hello", style='bold')  # "𝐡𝐞𝐥𝐥𝐨"
"""

from typing import Dict, List, Optional


# Unicode ranges for different fancy text styles
# Used by detector to recognize fancy characters as valid word characters
STYLE_UNICODE_RANGES = {
    'bold': [
        r'\U0001D400-\U0001D419',  # Bold uppercase A-Z
        r'\U0001D41A-\U0001D433',  # Bold lowercase a-z
    ],
    'italic': [
        r'\U0001D434-\U0001D44D',  # Italic uppercase A-Z
        r'\U0001D44E-\U0001D467',  # Italic lowercase a-z
    ],
    'bold_italic': [
        r'\U0001D468-\U0001D481',  # Bold italic uppercase A-Z
        r'\U0001D482-\U0001D49B',  # Bold italic lowercase a-z
    ],
    'sans_serif': [
        r'\U0001D5A0-\U0001D5B9',  # Sans-serif uppercase A-Z
        r'\U0001D5BA-\U0001D5D3',  # Sans-serif lowercase a-z
    ],
    'circled': [
        r'\u24B6-\u24CF',  # Circled uppercase A-Z
        r'\u24D0-\u24E9',  # Circled lowercase a-z
    ],
    'squared': [
        r'\U0001F130-\U0001F149',  # Squared uppercase A-Z
        r'\U0001F130-\U0001F149',  # Squared lowercase (same as uppercase for this style)
    ],
    'negative_circled': [
        r'\U0001F150-\U0001F169',  # Negative circled uppercase A-Z
        r'\U0001F150-\U0001F169',  # Negative circled lowercase (same as uppercase for this style)
    ],
    'negative_squared': [
        r'\U0001F170-\U0001F189',  # Negative squared uppercase A-Z
        r'\U0001F170-\U0001F189',  # Negative squared lowercase (same as uppercase for this style)
    ],
}


class FancyTextConverter:
    """
    Converts text to Unicode fancy text for censorship evasion
    
    Styles available:
        - bold: 𝐀𝐁𝐂𝐚𝐛𝐜
        - italic: 𝐴𝐵𝐶𝑎𝑏𝑐
        - bold_italic: 𝑨𝑩𝑪𝒂𝒃𝒄
        - sans_serif: 𝖠𝖡𝖢𝖺𝖻𝖼
        - circled: Ⓐ Ⓑ Ⓒ ⓐ ⓑ ⓒ
        - squared: 🄰 🄱 🄲 🄰 🄱 🄲
        - negative_squared: 🅰 🅱 🅲 🅰 🅱 🅲
        - negative_circled: 🅐 🅑 🅒 🅐 🅑 🅒
    """
    
    # Unicode ranges for different styles
    # These use mathematical alphanumeric symbols (U+1D400 - U+1D7FF)
    
    BOLD_UPPER_START = 0x1D400  # 𝐀
    BOLD_LOWER_START = 0x1D41A  # 𝐚
    
    ITALIC_UPPER_START = 0x1D434  # 𝐴
    ITALIC_LOWER_START = 0x1D44E  # 𝑎
    
    BOLD_ITALIC_UPPER_START = 0x1D468  # 𝑨
    BOLD_ITALIC_LOWER_START = 0x1D482  # 𝒂
    
    SANS_SERIF_UPPER_START = 0x1D5A0  # 𝖠
    SANS_SERIF_LOWER_START = 0x1D5BA  # 𝖺
    
    # Circled characters
    CIRCLED_UPPER = {
        'A': 'Ⓐ', 'B': 'Ⓑ', 'C': 'Ⓒ', 'D': 'Ⓓ', 'E': 'Ⓔ',
        'F': 'Ⓕ', 'G': 'Ⓖ', 'H': 'Ⓗ', 'I': 'Ⓘ', 'J': 'Ⓙ',
        'K': 'Ⓚ', 'L': 'Ⓛ', 'M': 'Ⓜ', 'N': 'Ⓝ', 'O': 'Ⓞ',
        'P': 'Ⓟ', 'Q': 'Ⓠ', 'R': 'Ⓡ', 'S': 'Ⓢ', 'T': 'Ⓣ',
        'U': 'Ⓤ', 'V': 'Ⓥ', 'W': 'Ⓦ', 'X': 'Ⓧ', 'Y': 'Ⓨ', 'Z': 'Ⓩ'
    }
    
    CIRCLED_LOWER = {
        'a': 'ⓐ', 'b': 'ⓑ', 'c': 'ⓒ', 'd': 'ⓓ', 'e': 'ⓔ',
        'f': 'ⓕ', 'g': 'ⓖ', 'h': 'ⓗ', 'i': 'ⓘ', 'j': 'ⓙ',
        'k': 'ⓚ', 'l': 'ⓛ', 'm': 'ⓜ', 'n': 'ⓝ', 'o': 'ⓞ',
        'p': 'ⓟ', 'q': 'ⓠ', 'r': 'ⓡ', 's': 'ⓢ', 't': 'ⓣ',
        'u': 'ⓤ', 'v': 'ⓥ', 'w': 'ⓦ', 'x': 'ⓧ', 'y': 'ⓨ', 'z': 'ⓩ'
    }
    
    # Regional indicator symbols and squared characters
    # Squared Latin Letters (U+1F130 - U+1F149) for uppercase
    # Negative Squared Latin Letters (U+1F170 - U+1F189) for uppercase (darker)
    SQUARED_UPPER = {
        'A': '🄰', 'B': '🄱', 'C': '🄲', 'D': '🄳', 'E': '🄴',
        'F': '🄵', 'G': '🄶', 'H': '🄷', 'I': '🄸', 'J': '🄹',
        'K': '🄺', 'L': '🄻', 'M': '🄼', 'N': '🄽', 'O': '🄾',
        'P': '🄿', 'Q': '🅀', 'R': '🅁', 'S': '🅂', 'T': '🅃',
        'U': '🅄', 'V': '🅅', 'W': '🅆', 'X': '🅇', 'Y': '🅈', 'Z': '🅉'
    }
    
    SQUARED_LOWER = {
        'a': '🄰', 'b': '🄱', 'c': '🄲', 'd': '🄳', 'e': '🄴',
        'f': '🄵', 'g': '🄶', 'h': '🄷', 'i': '🄸', 'j': '🄹',
        'k': '🄺', 'l': '🄻', 'm': '🄼', 'n': '🄽', 'o': '🄾',
        'p': '🄿', 'q': '🅀', 'r': '🅁', 's': '🅂', 't': '🅃',
        'u': '🅄', 'v': '🅅', 'w': '🅆', 'x': '🅇', 'y': '🅈', 'z': '🅉'
    }
    
    # Negative Squared (dark background)
    NEGATIVE_SQUARED_UPPER = {
        'A': '🅰', 'B': '🅱', 'C': '🅲', 'D': '🅳', 'E': '🅴',
        'F': '🅵', 'G': '🅶', 'H': '🅷', 'I': '🅸', 'J': '🅹',
        'K': '🅺', 'L': '🅻', 'M': '🅼', 'N': '🅽', 'O': '🅾',
        'P': '🅿', 'Q': '🆀', 'R': '🆁', 'S': '🆂', 'T': '🆃',
        'U': '🆄', 'V': '🆅', 'W': '🆆', 'X': '🆇', 'Y': '🆈', 'Z': '🆉'
    }
    
    NEGATIVE_SQUARED_LOWER = {
        'a': '🅰', 'b': '🅱', 'c': '🅲', 'd': '🅳', 'e': '🅴',
        'f': '🅵', 'g': '🅶', 'h': '🅷', 'i': '🅸', 'j': '🅹',
        'k': '🅺', 'l': '🅻', 'm': '🅼', 'n': '🅽', 'o': '🅾',
        'p': '🅿', 'q': '🆀', 'r': '🆁', 's': '🆂', 't': '🆃',
        'u': '🆄', 'v': '🆅', 'w': '🆆', 'x': '🆇', 'y': '🆈', 'z': '🆉'
    }
    
    # Negative Circled (dark background)
    NEGATIVE_CIRCLED_UPPER = {
        'A': '🅐', 'B': '🅑', 'C': '🅒', 'D': '🅓', 'E': '🅔',
        'F': '🅕', 'G': '🅖', 'H': '🅗', 'I': '🅘', 'J': '🅙',
        'K': '🅚', 'L': '🅛', 'M': '🅜', 'N': '🅝', 'O': '🅞',
        'P': '🅟', 'Q': '🅠', 'R': '🅡', 'S': '🅢', 'T': '🅣',
        'U': '🅤', 'V': '🅥', 'W': '🅦', 'X': '🅧', 'Y': '🅨', 'Z': '🅩'
    }
    
    NEGATIVE_CIRCLED_LOWER = {
        'a': '🅐', 'b': '🅑', 'c': '🅒', 'd': '🅓', 'e': '🅔',
        'f': '🅕', 'g': '🅖', 'h': '🅗', 'i': '🅘', 'j': '🅙',
        'k': '🅚', 'l': '🅛', 'm': '🅜', 'n': '🅝', 'o': '🅞',
        'p': '🅟', 'q': '🅠', 'r': '🅡', 's': '🅢', 't': '🅣',
        'u': '🅤', 'v': '🅥', 'w': '🅦', 'x': '🅧', 'y': '🅨', 'z': '🅩'
    }
    
    def __init__(self, default_style: str = 'squared'):
        """
        Initialize fancy text converter
        
        Args:
            default_style: Default style to use (squared, bold, italic, etc.)
        """
        self.styles = [
            'squared', 'bold', 'italic', 'bold_italic', 
            'sans_serif', 'circled', 'negative_squared', 'negative_circled'
        ]
        self.default_style = default_style if default_style in self.styles else 'squared'
    
    def convert(self, text: str, style: str = None, positions: Optional[List[int]] = None) -> str:
        """
        Convert text to fancy Unicode
        
        Args:
            text: Text to convert
            style: Unicode style to use (None = use default)
            positions: Optional list of character positions to convert
        
        Returns:
            str: Fancy Unicode version of text
        
        Examples:
            convert("hello", "squared") → "🄷🄴🄻🄻🄾"
            convert("hello", "bold") → "𝐡𝐞𝐥𝐥𝐨"
            convert("assassin", "circled") → "ⓐⓢⓢⓐⓢⓢⓘⓝ"
        """
        if not text:
            return text
        
        # Use default style if none specified
        if style is None:
            style = self.default_style
        
        if style not in self.styles:
            raise ValueError(f"Unknown style: {style}. Available: {self.styles}")
        
        result = list(text)
        
        if positions is None:
            # Convert all applicable characters
            for i, char in enumerate(result):
                result[i] = self._convert_char(char, style)
        else:
            # Convert only specified positions
            for pos in positions:
                if 0 <= pos < len(result):
                    result[pos] = self._convert_char(result[pos], style)
        
        return ''.join(result)
    
    def _convert_char(self, char: str, style: str) -> str:
        """
        Convert a single character to fancy Unicode
        
        Args:
            char: Character to convert
            style: Unicode style
        
        Returns:
            str: Fancy Unicode character or original if not convertible
        """
        if style == 'squared':
            if char in self.SQUARED_UPPER:
                return self.SQUARED_UPPER[char]
            elif char in self.SQUARED_LOWER:
                return self.SQUARED_LOWER[char]
            else:
                return char
        
        if style == 'circled':
            if char in self.CIRCLED_UPPER:
                return self.CIRCLED_UPPER[char]
            elif char in self.CIRCLED_LOWER:
                return self.CIRCLED_LOWER[char]
            else:
                return char
        
        if style == 'negative_squared':
            if char in self.NEGATIVE_SQUARED_UPPER:
                return self.NEGATIVE_SQUARED_UPPER[char]
            elif char in self.NEGATIVE_SQUARED_LOWER:
                return self.NEGATIVE_SQUARED_LOWER[char]
            else:
                return char
        
        if style == 'negative_circled':
            if char in self.NEGATIVE_CIRCLED_UPPER:
                return self.NEGATIVE_CIRCLED_UPPER[char]
            elif char in self.NEGATIVE_CIRCLED_LOWER:
                return self.NEGATIVE_CIRCLED_LOWER[char]
            else:
                return char
        
        # For mathematical alphanumeric symbols
        if 'A' <= char <= 'Z':
            # Uppercase letter
            offset = ord(char) - ord('A')
            
            if style == 'bold':
                return chr(self.BOLD_UPPER_START + offset)
            elif style == 'italic':
                return chr(self.ITALIC_UPPER_START + offset)
            elif style == 'bold_italic':
                return chr(self.BOLD_ITALIC_UPPER_START + offset)
            elif style == 'sans_serif':
                return chr(self.SANS_SERIF_UPPER_START + offset)
        
        elif 'a' <= char <= 'z':
            # Lowercase letter
            offset = ord(char) - ord('a')
            
            if style == 'bold':
                return chr(self.BOLD_LOWER_START + offset)
            elif style == 'italic':
                return chr(self.ITALIC_LOWER_START + offset)
            elif style == 'bold_italic':
                return chr(self.BOLD_ITALIC_LOWER_START + offset)
            elif style == 'sans_serif':
                return chr(self.SANS_SERIF_LOWER_START + offset)
        
        # Not convertible
        return char
    
    def convert_word(self, word: str, style: str = 'bold', strategy: str = 'all') -> str:
        """
        Convert a specific word with a strategy
        
        Args:
            word: Word to convert
            style: Unicode style
            strategy: Conversion strategy
                     'all' - Convert all characters
                     'vowels' - Convert only vowels
                     'consonants' - Convert only consonants
                     'alternating' - Convert every other character
        
        Returns:
            str: Converted word
        """
        if strategy == 'vowels':
            vowels = set('aeiouAEIOU')
            positions = [i for i, c in enumerate(word) if c in vowels]
            return self.convert(word, style, positions)
        
        elif strategy == 'consonants':
            vowels = set('aeiouAEIOU')
            positions = [i for i, c in enumerate(word) if c.isalpha() and c not in vowels]
            return self.convert(word, style, positions)
        
        elif strategy == 'alternating':
            positions = [i for i in range(0, len(word), 2)]
            return self.convert(word, style, positions)
        
        else:  # 'all'
            return self.convert(word, style)
    
    def get_variations(self, word: str, max_variations: int = 5) -> List[str]:
        """
        Generate multiple fancy text variations of a word
        
        Args:
            word: Word to generate variations for
            max_variations: Maximum number of variations
        
        Returns:
            list: List of fancy text variations
        """
        variations = []
        
        # Try each style
        for style in self.styles[:max_variations]:
            try:
                variations.append(self.convert(word, style))
            except:
                pass
        
        return variations[:max_variations]
    
    def is_fancy_text(self, text: str) -> bool:
        """
        Check if text contains fancy Unicode characters
        
        Args:
            text: Text to check
        
        Returns:
            bool: True if text contains fancy Unicode
        """
        for char in text:
            code = ord(char)
            # Check if in mathematical alphanumeric range
            if 0x1D400 <= code <= 0x1D7FF:
                return True
            # Check if in circled range
            if char in self.CIRCLED_UPPER.values() or char in self.CIRCLED_LOWER.values():
                return True
        
        return False
    
    def estimate_byte_overhead(self, text: str, style: str = 'bold') -> int:
        """
        Estimate byte overhead for fancy text conversion
        
        Args:
            text: Original text
            style: Style to use
        
        Returns:
            int: Estimated additional bytes
        """
        original_bytes = len(text.encode('utf-8'))
        fancy = self.convert(text, style)
        fancy_bytes = len(fancy.encode('utf-8'))
        
        return fancy_bytes - original_bytes
    
    def get_available_styles(self) -> List[str]:
        """
        Get list of available styles
        
        Returns:
            list: Available style names
        """
        return self.styles.copy()
    
    def get_stats(self) -> Dict:
        """
        Get converter statistics
        
        Returns:
            dict: Statistics about the converter
        """
        return {
            'available_styles': len(self.styles),
            'styles': self.styles,
            'supports_uppercase': True,
            'supports_lowercase': True,
            'typical_byte_overhead': 3  # bytes per character
        }


# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
