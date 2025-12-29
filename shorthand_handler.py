#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shorthand Handler Module
=========================
Text compression using common abbreviations

Features:
- Common shorthand substitutions (everyone→every1, please→pls)
- Saves bytes (reduces message length)
- Configurable abbreviation dictionary
- JSON-based custom shorthand support

Usage:
    from shorthand_handler import ShorthandHandler
    
    handler = ShorthandHandler()
    result = handler.compress("everyone please wait")  # "every1 pls wait"
"""

import json
import os
from typing import Dict, List, Optional, Tuple


class ShorthandHandler:
    """
    Handles text compression using shorthand abbreviations
    
    Common abbreviations:
        everyone → every1       please → pls
        someone → some1         because → bc/cuz
        before → b4             later → l8r
        something → smth        without → w/o
        with → w/               people → ppl
        probably → prob         actually → actual/actly
        really → rly            something → sth
    """
    
    # Default shorthand dictionary
    DEFAULT_SHORTHAND = {
    # Numbers in words
    'everyone': 'every1',
    'someone': 'some1',
    'anyone': 'any1',
    'no one': 'no1',
    'noone': 'no1',
    
    # Letter/number substitutions
    'before': 'b4',
    'for': '4',
    'to': '2',
    'too': '2',
    'ate': '8',
    'late': 'l8',
    'later': 'l8r',
    'great': 'gr8',
    'mate': 'm8',
    'wait': 'w8',
    'straight': 'str8',
    'date': 'd8',
    'rate': 'r8',
    'appreciate': 'apprec8',
    'activate': 'activ8',
    
    # Common abbreviations
    'please': 'pls',
    'because': 'bc',
    'be cause': 'bc',
    'with': 'w/',
    'without': 'w/o',
    'you': 'u',
    'your': 'ur',
    'are': 'r',
    'why': 'y',
    'see': 'c',
    'and': 'n',
    'at': '@',
    'be': 'b',
    
    # Pronouns and possessives
    'them': 'em',
    
    # Word shortening
    'probably': 'prob',
    'actually': 'actly',
    'really': 'rly',
    'definitely': 'def',
    'people': 'ppl',
    'person': 'prsn',
    'something': 'smth',
    'anything': 'anyth',
    'nothing': 'noth',
    'everything': 'everyth',
    'okay': 'ok',
    'alright': 'aite',
    'about': 'abt',
    'though': 'tho',
    'through': 'thru',
    'thanks': 'thx',
    'thank you': 'ty',
    'tomorrow': 'tmr',
    'tonight': '2nite',
    'today': '2day',
    'message': 'msg',
    'messages': 'msgs',
    'minutes': 'mins',
    'minute': 'min',
    'seconds': 'secs',
    'second': 'sec',
    'picture': 'pic',
    'pictures': 'pics',
    'photo': 'pic',
    'photos': 'pics',
    'video': 'vid',
    'videos': 'vids',
    
    # Greetings and farewells
    'hello': 'hey',
    'goodbye': 'bye',
    'good night': 'gn',
    'goodnight': 'gn',
    'good morning': 'gm',
    'goodmorning': 'gm',
    'see you': 'cu',
    'see you later': 'cya',
    'talk to you later': 'ttyl',
    'be right back': 'brb',
    'got to go': 'g2g',
    'gotta go': 'g2g',
    
    # Common phrases and acronyms
    'i do not know': 'idk',
    'i don\'t know': 'idk',
    'to be honest': 'tbh',
    'in my opinion': 'imo',
    'in my humble opinion': 'imho',
    'by the way': 'btw',
    'for your information': 'fyi',
    'as far as i know': 'afaik',
    'i know right': 'ikr',
    'laughing out loud': 'lol',
    'laugh out loud': 'lol',
    'be back later': 'bbl',
    'on my way': 'omw',
    'let me know': 'lmk',
    'never mind': 'nvm',
    'nevermind': 'nvm',
    'oh my god': 'omg',
    'oh my gosh': 'omg',
    'what the': 'wt',
    'what the hell': 'wth',
    'what the heck': 'wth',
    'as soon as possible': 'asap',
    'for what it\'s worth': 'fwiw',
    'not gonna lie': 'ngl',
    'not going to lie': 'ngl',
    'not safe for work': 'nsfw',
    'too long didn\'t read': 'tldr',
    'too long didnt read': 'tldr',
    'just kidding': 'jk',
    'just saying': 'js',
    'i love you': 'ily',
    'love you': 'ly',
    'hugs and kisses': 'xoxo',
    
    # Question words
    'what': 'wut',
    'where': 'whr',
    
    # Common verbs
    'going': 'goin',
    'doing': 'doin',
    'coming': 'comin',
    'know': 'kno',
    'think': 'thnk',
    'should': 'shld',
    'would': 'wld',
    'could': 'cld',
    'have': 'hv',
    'talk': 'tlk',
    'text': 'txt',
    
    # Social/reactions
    'yeah': 'ye',
    'yep': 'ye',
    'yes': 'ye',
    'nope': 'nop',
    'sorry': 'sry',
    'excuse me': 'scuse me',
    'whatever': 'whatev',
    'double': 'dbl',
    
    # Time references
    'monday': 'mon',
    'tuesday': 'tue',
    'wednesday': 'wed',
    'thursday': 'thu',
    'friday': 'fri',
    'saturday': 'sat',
    'sunday': 'sun',
    'morning': 'morn',
    'afternoon': 'aft',
    'evening': 'eve',
    'night': 'nite',
    
    # Internet/tech
    'address': 'addr',
    'website': 'site',
    'internet': 'net',
    'computer': 'PC',
    'information': 'info',
    'favorite': 'fav',
    'application': 'app',
    'profile': 'prof',
    'username': 'user',
    'password': 'pass',
    
    # Misc common words
    'between': 'btwn',
    'around': 'arnd',
    'some': 'sum',
    'very': 'v',
    'from': 'frm',
    'of course': 'ofc',
    'off course': 'ofc',
    'kind of': 'kinda',
    'sort of': 'sorta',
    'got': 'gt',
    'just': 'jst',
    'each': 'ea',
    'maybe': 'mayb',
    'serious': 'srs',
    'seriously': 'srsly',
    'super': 'spr',
    'pretty': 'prtty',
    'little': 'lil',
    'especially': 'esp',
    'important': 'impt',
    'question': 'q',
    'answer': 'ans',
    'number': 'no.',
    'different': 'diff',
    'boyfriend': 'bf',
    'girlfriend': 'gf',
    'best friend': 'bff',
    'family': 'fam',
    'brother': 'bro',
    'sister': 'sis',
}
    
    def __init__(self, shorthand_file: Optional[str] = None):
        """
        Initialize shorthand handler
        
        Args:
            shorthand_file: Optional path to JSON file with custom shorthand
        """
        self.shorthand = self.DEFAULT_SHORTHAND.copy()
        
        # Load custom shorthand if provided
        if shorthand_file and os.path.exists(shorthand_file):
            self.load_from_file(shorthand_file)
    
    def compress(self, text: str, aggressive: bool = False) -> str:
        """
        Compress text using shorthand
        
        Args:
            text: Text to compress
            aggressive: If True, apply more aggressive abbreviations
        
        Returns:
            str: Compressed text
        
        Examples:
            compress("everyone please wait") → "every1 pls w8"
            compress("see you later") → "c u l8r"
        """
        if not text:
            return text
        
        result = text
        
        # Sort by length (longest first) to avoid partial replacements
        sorted_shortcuts = sorted(self.shorthand.items(), key=lambda x: len(x[0]), reverse=True)
        
        for full, short in sorted_shortcuts:
            # Case-insensitive replacement
            # Replace whole words only (with word boundaries)
            import re
            
            # Pattern to match whole words
            pattern = r'\b' + re.escape(full) + r'\b'
            
            # Replace preserving case where possible
            def replace_func(match):
                matched = match.group(0)
                if matched.isupper():
                    return short.upper()
                elif matched[0].isupper():
                    return short.capitalize()
                else:
                    return short
            
            result = re.sub(pattern, replace_func, result, flags=re.IGNORECASE)
        
        return result
    
    def expand(self, text: str) -> str:
        """
        Expand shorthand back to full text
        
        Args:
            text: Compressed text
        
        Returns:
            str: Expanded text
        
        Note: This is approximate - some abbreviations are ambiguous
        """
        result = text
        
        # Create reverse mapping
        reverse = {v: k for k, v in self.shorthand.items()}
        
        # Sort by length (longest first)
        sorted_expansions = sorted(reverse.items(), key=lambda x: len(x[0]), reverse=True)
        
        import re
        for short, full in sorted_expansions:
            pattern = r'\b' + re.escape(short) + r'\b'
            result = re.sub(pattern, full, result, flags=re.IGNORECASE)
        
        return result
    
    def get_compression_ratio(self, text: str) -> float:
        """
        Calculate compression ratio for text
        
        Args:
            text: Text to analyze
        
        Returns:
            float: Compression ratio (0.0 to 1.0)
                  0.5 means compressed to 50% of original size
        """
        if not text:
            return 1.0
        
        compressed = self.compress(text)
        
        original_len = len(text)
        compressed_len = len(compressed)
        
        return compressed_len / original_len
    
    def estimate_savings(self, text: str) -> int:
        """
        Estimate byte savings from compression
        
        Args:
            text: Text to analyze
        
        Returns:
            int: Estimated bytes saved (negative if expanded)
        """
        original_bytes = len(text.encode('utf-8'))
        compressed = self.compress(text)
        compressed_bytes = len(compressed.encode('utf-8'))
        
        return original_bytes - compressed_bytes
    
    def add_shorthand(self, full: str, short: str):
        """
        Add a custom shorthand mapping
        
        Args:
            full: Full text
            short: Abbreviated form
        """
        self.shorthand[full.lower()] = short.lower()
    
    def remove_shorthand(self, full: str):
        """
        Remove a shorthand mapping
        
        Args:
            full: Full text to remove
        """
        full_lower = full.lower()
        if full_lower in self.shorthand:
            del self.shorthand[full_lower]
    
    def load_from_file(self, filepath: str) -> bool:
        """
        Load custom shorthand from JSON file
        
        Args:
            filepath: Path to JSON file
        
        Returns:
            bool: True if loaded successfully
        
        File format:
            {
                "everyone": "every1",
                "please": "pls",
                ...
            }
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                custom = json.load(f)
                
                # Merge with existing
                self.shorthand.update(custom)
                
                return True
        except Exception as e:
            print(f"Error loading shorthand file: {e}")
            return False
    
    def save_to_file(self, filepath: str) -> bool:
        """
        Save shorthand dictionary to JSON file
        
        Args:
            filepath: Path to save file
        
        Returns:
            bool: True if saved successfully
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.shorthand, f, indent=2, sort_keys=True)
                
                return True
        except Exception as e:
            print(f"Error saving shorthand file: {e}")
            return False
    
    def get_suggestions(self, text: str) -> List[Tuple[str, str, int]]:
        """
        Get compression suggestions for text
        
        Args:
            text: Text to analyze
        
        Returns:
            list: List of (full_word, short_form, bytes_saved) tuples
        """
        suggestions = []
        
        import re
        for full, short in self.shorthand.items():
            # Check if full word appears in text
            pattern = r'\b' + re.escape(full) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                bytes_saved = len(full.encode('utf-8')) - len(short.encode('utf-8'))
                suggestions.append((full, short, bytes_saved))
        
        # Sort by bytes saved (descending)
        suggestions.sort(key=lambda x: x[2], reverse=True)
        
        return suggestions
    
    def get_stats(self) -> Dict:
        """
        Get handler statistics
        
        Returns:
            dict: Statistics about shorthand dictionary
        """
        return {
            'total_shortcuts': len(self.shorthand),
            'average_compression': sum(
                1 - len(v) / len(k) for k, v in self.shorthand.items()
            ) / len(self.shorthand) if self.shorthand else 0
        }
    
    def get_all_shorthand(self) -> Dict[str, str]:
        """
        Get all shorthand mappings
        
        Returns:
            dict: Copy of shorthand dictionary
        """
        return self.shorthand.copy()


# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
