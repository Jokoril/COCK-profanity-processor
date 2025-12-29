#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filter Loader Module
====================
Loads and optimizes filter word lists using Aho-Corasick automaton

Features:
- Fast multi-pattern matching (O(n) complexity)
- Handles large filter lists (77k+ entries)
- Automatic optimization and deduplication
- Performance validation (<500ms load time target)
"""

import time
from typing import Tuple, Dict, Set, Optional
try:
    import ahocorasick
except ImportError:
    print("WARNING: pyahocorasick not installed. Install with: pip install pyahocorasick")
    ahocorasick = None


class FilterLoader:
    """
    Filter list loader with Aho-Corasick optimization
    """
    
    def __init__(self):
        self.automaton = None
        self.stats = {}
        self.filter_words = set()
    
    def load(self, filepath: str, verbose: bool = True) -> Tuple[Optional['ahocorasick.Automaton'], Dict]:
        """
        Load filter list with aggressive optimization
        
        Args:
            filepath: Path to filter file (one word per line)
            verbose: Print loading statistics
            
        Returns:
            tuple: (automaton, stats_dict)
                - automaton: Aho-Corasick automaton (or None if pyahocorasick not installed)
                - stats_dict: Loading statistics
        
        Target Performance:
            - Load time: <500ms for 77k entries
            - Memory: <50MB
        
        File Format:
            - One word per line
            - UTF-8 encoding
            - Comments start with '#'
            - Empty lines ignored
        """
        
        if ahocorasick is None:
            return (None, {"error": "pyahocorasick not installed"})
        
        # Clean up old automaton if exists (prevents memory leak)
        if self.automaton is not None:
            del self.automaton
            self.automaton = None
            
            # Optional: Force garbage collection
            import gc
            gc.collect()
        
        stats = {
            'loaded': 0,
            'removed_non_latin': 0,
            'removed_duplicates': 0,
            'removed_empty': 0,
            'final_count': 0,
            'load_time_ms': 0,
            'file_path': filepath,
            'non_latin_examples': []
        }
        
        start_time = time.time()
        
        try:
            # Read file
            raw_words = []
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    stats['loaded'] += 1
                    word = line.strip()
                    
                    # Skip empty lines or comments
                    if not word or word.startswith('#'):
                        stats['removed_empty'] += 1
                        continue
                    
                    # Smart filtering: Support ONLY pure Latin alphabet with diacriticals
                    # Reject words with ANY non-Latin characters (CJK, Cyrillic, emoji, etc.)
                    if not self._is_pure_latin(word):
                        stats['removed_non_latin'] += 1
                        if len(stats['non_latin_examples']) < 10:
                            stats['non_latin_examples'].append(word)
                        continue
                    
                    # Store lowercase version
                    raw_words.append(word.lower())
            
            # Deduplicate
            unique_words = list(set(raw_words))
            stats['removed_duplicates'] = len(raw_words) - len(unique_words)
            stats['final_count'] = len(unique_words)
            
            # Store for later reference
            self.filter_words = set(unique_words)
            
            # Build Aho-Corasick automaton
            self.automaton = ahocorasick.Automaton()
            for idx, word in enumerate(unique_words):
                self.automaton.add_word(word, (idx, word))
            
            # Finalize automaton (required before searching)
            self.automaton.make_automaton()
            
            # Calculate load time
            stats['load_time_ms'] = (time.time() - start_time) * 1000
            
            # Store stats
            self.stats = stats
            
            # Print statistics if verbose
            if verbose:
                self._print_stats(stats)
            
            # Validate performance
            if stats['load_time_ms'] > 500:
                print(f"WARNING: Load time ({stats['load_time_ms']:.0f}ms) exceeds target (500ms)")
            
            return (self.automaton, stats)
            
        except FileNotFoundError:
            error_msg = f"Filter file not found: {filepath}"
            print(f"ERROR: {error_msg}")
            return (None, {"error": error_msg})
        
        except Exception as e:
            error_msg = f"Error loading filter file: {e}"
            print(f"ERROR: {error_msg}")
            return (None, {"error": error_msg})
    
    def search(self, text: str) -> list:
        """
        Search text for filter words using Aho-Corasick
        
        Args:
            text: Text to search
            
        Returns:
            list: List of (end_position, (index, word)) tuples
        
        Performance:
            - O(n + m) where n=text length, m=number of matches
            - Very fast for multiple pattern matching
        """
        if self.automaton is None:
            return []
        
        results = []
        for end_idx, (idx, word) in self.automaton.iter(text.lower()):
            results.append((end_idx, (idx, word)))
        
        return results
    
    def contains(self, word: str) -> bool:
        """
        Check if a word is in the filter list
        
        Args:
            word: Word to check
            
        Returns:
            bool: True if word is in filter list
        """
        return word.lower() in self.filter_words
    
    def get_stats(self) -> Dict:
        """
        Get loading statistics
        
        Returns:
            dict: Statistics dictionary
        """
        return self.stats.copy()
    
    def _is_ascii(self, text: str) -> bool:
        """
        Fast ASCII check
        
        Args:
            text: Text to check
            
        Returns:
            bool: True if text is pure ASCII
        """
        try:
            text.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False
    
    def _is_pure_latin(self, text: str) -> bool:
        """
        Check if ALL characters are Latin-based (ASCII + Latin diacriticals)
        
        Accepts:
        - Pure ASCII: "fuck", "shit", "damn"
        - Latin + diacriticals: "Coño", "café", "Scheiße"
        - Numbers with Latin: "420", "2g1c"
        
        Rejects:
        - Any CJK: "3g色站", "fuck傻逼"
        - Any Cyrillic: "хуй", "testблять"
        - Any Arabic: "كس", "testزب"
        - Any emoji: "test💩", "fuck🖕"
        
        Args:
            text: Text to check
            
        Returns:
            bool: True if ALL characters are Latin-based, False if ANY character is non-Latin
        """
        for char in text:
            code_point = ord(char)
            
            # Allow ASCII letters: a-z, A-Z
            if (ord('a') <= code_point <= ord('z')) or (ord('A') <= code_point <= ord('Z')):
                continue
            
            # Allow ASCII digits: 0-9
            if ord('0') <= code_point <= ord('9'):
                continue
            
            # Allow Latin-1 Supplement: À-ÿ (U+00C0 to U+00FF)
            # Covers: French, Spanish, German, Portuguese diacriticals
            if 0x00C0 <= code_point <= 0x00FF:
                continue
            
            # Allow Latin Extended-A: Ā-ſ (U+0100 to U+017F)
            # Covers: Polish, Czech, Turkish, Baltic diacriticals
            if 0x0100 <= code_point <= 0x017F:
                continue
            
            # Allow Latin Extended-B: ƀ-ɏ (U+0180 to U+024F)
            # Covers: Vietnamese, Croatian diacriticals
            if 0x0180 <= code_point <= 0x024F:
                continue
            
            # If we get here, character is NOT Latin-based
            # Could be: CJK, Cyrillic, Arabic, emoji, etc.
            return False
        
        # All characters passed the Latin-based check
        return True
    
    def _print_stats(self, stats: Dict) -> None:
        """
        Print loading statistics
        
        Args:
            stats: Statistics dictionary
        """
        print("\n" + "="*60)
        print("FILTER LOADING STATISTICS")
        print("="*60)
        print(f"File: {stats.get('file_path', 'Unknown')}")
        print(f"Total lines read: {stats['loaded']}")
        print(f"Removed (empty/comments): {stats['removed_empty']}")
        
        # Show non-Latin removals with examples
        if stats.get('removed_non_latin', 0) > 0:
            print(f"Removed (non-Latin/mixed): {stats['removed_non_latin']} ⚠")
            if stats.get('non_latin_examples') and stats['non_latin_examples']:
                print(f"  Examples: {', '.join(stats['non_latin_examples'][:5])}")
                if len(stats['non_latin_examples']) > 5:
                    print(f"  ... and {stats['removed_non_latin'] - 5} more")
        
        print(f"Removed (duplicates): {stats['removed_duplicates']}")
        print(f"Final filter count: {stats['final_count']}")
        print(f"  ℹ️  Pure Latin + diacriticals only (e.g., Coño, café, Scheiße)")
        print(f"  ℹ️  Rejected: Any CJK, Cyrillic, Arabic, emoji, etc.")
        print(f"Load time: {stats['load_time_ms']:.1f}ms")
        print("="*60 + "\n")


def load_whitelist(filepath: str) -> Set[str]:
    """
    Load whitelist from file
    
    Args:
        filepath: Path to whitelist file
        
    Returns:
        set: Set of whitelisted words (lowercase)
        
    File Format:
        - One word per line
        - Comments start with '#'
        - Case-insensitive
    """
    whitelist = set()
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                
                # Skip empty lines or comments
                if not word or word.startswith('#'):
                    continue
                
                whitelist.add(word.lower())
        
        print(f"Loaded {len(whitelist)} words from whitelist: {filepath}")
        
    except FileNotFoundError:
        print(f"Whitelist file not found: {filepath}")
    except Exception as e:
        print(f"Error loading whitelist: {e}")
    
    return whitelist


def load_blacklist(filepath: str) -> Set[str]:
    """
    Load blacklist from file
    
    Args:
        filepath: Path to blacklist file
        
    Returns:
        set: Set of blacklisted words (lowercase)
        
    File Format:
        - One word per line
        - Comments start with '#'
        - Case-insensitive
    """
    blacklist = set()
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                
                # Skip empty lines or comments
                if not word or word.startswith('#'):
                    continue
                
                blacklist.add(word.lower())
        
        print(f"Loaded {len(blacklist)} words from blacklist: {filepath}")
        
    except FileNotFoundError:
        print(f"Blacklist file not found: {filepath}")
    except Exception as e:
        print(f"Error loading blacklist: {e}")
    
    return blacklist


def save_whitelist(filepath: str, whitelist: Set[str]) -> bool:
    """
    Save whitelist to file
    
    Args:
        filepath: Path to whitelist file
        whitelist: Set of words to save
        
    Returns:
        bool: True if saved successfully
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Whitelist - Safe words when embedded\n")
            f.write("# Add one word per line (case-insensitive)\n\n")
            
            for word in sorted(whitelist):
                f.write(f"{word}\n")
        
        return True
        
    except Exception as e:
        print(f"Error saving whitelist: {e}")
        return False


def save_blacklist(filepath: str, blacklist: Set[str]) -> bool:
    """
    Save blacklist to file
    
    Args:
        filepath: Path to blacklist file
        blacklist: Set of words to save
        
    Returns:
        bool: True if saved successfully
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Blacklist - Always flag these words\n")
            f.write("# Add one word per line (case-insensitive)\n\n")
            
            for word in sorted(blacklist):
                f.write(f"{word}\n")
        
        return True
        
    except Exception as e:
        print(f"Error saving blacklist: {e}")
        return False


# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
