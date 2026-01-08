#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fast Detector Module
====================
v4.0 Detection algorithm with Aho-Corasick optimization

Features:
- Validated v4.0 algorithm (19/19 tests passed)
- Multi-pattern matching using Aho-Corasick
- Three-tier detection: Blacklist -> Embedding -> Stripped Window
- Whitelist embedding rule for window combinations

Algorithm Version: 4.0 (Production)
"""

import re
import time
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from logger import get_logger

# Module logger
log = get_logger(__name__)

# Import fancy text unicode ranges for dynamic pattern building
try:
    from fancy_text import STYLE_UNICODE_RANGES
except ImportError:
    # Fallback if fancy_text not available
    STYLE_UNICODE_RANGES = {
        'squared': [r'\U0001F130-\U0001F169'],
    }

# Extended Latin character ranges for detection
# Includes ASCII + Latin-1 Supplement + Latin Extended A/B
LATIN_CHAR_CLASS = r'a-zA-Z\u00C0-\u00FF\u0100-\u017F\u0180-\u024F'
LATIN_ALNUM_CLASS = r'a-zA-Z0-9\u00C0-\u00FF\u0100-\u017F\u0180-\u024F'


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class DetectionType(Enum):
    """Types of detection results"""
    EMBEDDING = "EMBEDDING"              # Found embedded in word
    STRIPPED_WINDOW = "STRIPPED_WINDOW"  # Found in sliding window
    STANDALONE = "STANDALONE"            # Standalone occurrence
    NO_MATCH = "NO_MATCH"               # Not found


@dataclass
class DetectionResult:
    """Result of censorship detection"""
    detection_type: DetectionType
    filtered_word: str
    can_whitelist: bool
    explanation: str
    
    # Embedding-specific fields
    full_word: Optional[str] = None
    word_position: Optional[int] = None
    match_char_end: Optional[int] = None  # Character position where match ends (from Aho-Corasick)
    
    # Stripped-specific fields
    matched_text: Optional[str] = None
    window_words: Optional[List[str]] = None
    window_range: Optional[Tuple[int, int]] = None
    
    # Debug info
    debug_info: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'detection_type': self.detection_type.value,
            'filtered_word': self.filtered_word,
            'can_whitelist': self.can_whitelist,
            'explanation': self.explanation,
            'full_word': self.full_word,
            'word_position': self.word_position,
            'matched_text': self.matched_text,
            'window_words': self.window_words,
            'window_range': self.window_range,
            'debug_info': self.debug_info
        }


# ============================================================================
# FAST DETECTOR CLASS
# ============================================================================

class FastCensorDetector:
    """
    v4.0 Detection algorithm with Aho-Corasick optimization
    
    Implements the validated prototype logic with multi-pattern matching
    
    Detection Priority:
        1. Blacklist check (always flag, no embedding protection)
        2. Embedding detection (check if in alphanumeric words)
        3. Sliding window stripped detection (with whitelist embedding rule)
    """
    
    def __init__(self, automaton, whitelist: Set[str], config: Dict):
        """
        Initialize fast detector

        Args:
            automaton: Aho-Corasick automaton from filter_loader
            whitelist: Set of whitelisted words (safe when embedded)
            config: Configuration dictionary
        """
        self.automaton = automaton
        self.whitelist = set(w.lower() for w in whitelist)
        self.config = config
        
        # Sliding window size for stripped detection
        # Note: detect_all uses dynamic sizes (2 to max_window)
        # This is used by detect_single's _check_stripped_window
        self.window_size = 3  # Standard 3-word window
        
        # Build and cache word extraction regex based on fancy text style and special char
        self._cached_pattern_key = None
        self._cached_word_pattern = None
        self._build_word_pattern()
    
    def _build_word_pattern(self):
        """Build regex pattern for word extraction"""
        # Get current fancy text style
        style = self.config.get('optimization', {}).get('fancy_text_style', 'squared')
        
        # Get special character for interspacing (default heart)
        special_char = self.config.get('special_char_interspacing', {}).get('character', '\u2764')
        
        # Check if we need to rebuild (style or special char changed)
        current_cache_key = (style, special_char)
        if hasattr(self, '_cached_pattern_key') and current_cache_key == self._cached_pattern_key and self._cached_word_pattern:
            return  # Use cached pattern
        
        # Build base pattern - include special char so it's not treated as word boundary
        # ASCII + Extended Latin + Hangul
        pattern_parts = [
            r'a-zA-Z0-9',           # ASCII letters and numbers
            r'\u00C0-\u00FF',       # Latin-1 Supplement (À-ÿ) - includes ß, ó, ń
            r'\u0100-\u017F',       # Latin Extended-A (Ā-ſ)
            r'\u0180-\u024F',       # Latin Extended-B (Ȁ-ɏ)
            r'\u119E',              # Hangul Jungseong Araea (numeral separator)
        ]
        
        # Add escaped special character
        if special_char:
            escaped_special = re.escape(special_char)
            pattern_parts.append(escaped_special)
        
        # Add fancy unicode ranges for current style
        if style in STYLE_UNICODE_RANGES:
            pattern_parts.extend(STYLE_UNICODE_RANGES[style])
        
        # Combine into full pattern
        pattern = r'[' + ''.join(pattern_parts) + r']+'
        
        # Compile and cache
        self._cached_word_pattern = re.compile(pattern)
        self._cached_pattern_key = current_cache_key

        log.debug(f"Word pattern rebuilt: style='{style}', special='{special_char}'")
    
    def extract_words(self, text: str) -> List[str]:
        """
        Extract alphanumeric words from text
        
        Includes:
        - ASCII letters and numbers
        - Hangul Jungseong Araea (ᆞ) for numeral filtering evasion
        - Fancy unicode characters (based on selected style)
        
        This ensures fancy characters are treated as valid word characters,
        preventing sliding window from rejoining broken words.
        
        Args:
            text: Input text
            
        Returns:
            list: List of words including fancy characters
            
        Examples:
            "I'm an assassin" -> ["I", "m", "an", "assassin"]
            "test_123" -> ["test", "123"]
            "hello-world" -> ["hello", "world"]
            "4ᆞ20" -> ["4ᆞ20"]
            "🄰ssault" → ["🄰ssault"] (fancy char preserved)
        """
        # Rebuild pattern if style changed
        self._build_word_pattern()
        
        # Extract words using cached pattern
        return self._cached_word_pattern.findall(text)
    
    def _strip_fancy_for_detection(self, text: str) -> str:
        """
        Strip fancy unicode characters for sliding window detection
        
        Simulates game behavior: strips fancy unicode but keeps leet-speak AND special char.
        Special char is NOT stripped by games - that's why it works!
        
        Example:
            "daff0🅳il" -> "daff0il" (strips 🅳)
            "fu¢k" -> "fu¢k" (keeps ¢)
            "a❤ssassin" -> "a❤ssassin" (keeps ❤ - games don't strip it!)
        
        Args:
            text: Text with potential fancy unicode
            
        Returns:
            Text with fancy unicode stripped but leet-speak and special char preserved
        """
        # Fancy unicode ranges (4-byte characters to strip)
        # All 8 supported fancy text styles
        fancy_ranges = [
            (0x1F130, 0x1F149),  # Squared
            (0x1D400, 0x1D433),  # Bold
            (0x1D434, 0x1D467),  # Italic
            (0x1D468, 0x1D49B),  # Bold Italic
            (0x1D5A0, 0x1D5D3),  # Sans Serif
            (0x24B6, 0x24E9),    # Circled
            (0x1F150, 0x1F169),  # Negative Circled
            (0x1F170, 0x1F189),  # Negative Squared
        ]
        
        result = []
        for char in text:
            char_code = ord(char)
            is_fancy = any(start <= char_code <= end for start, end in fancy_ranges)
            if not is_fancy:
                result.append(char)
        
        return ''.join(result)
    
    def collapse_spaced_patterns(self, text: str) -> str:
        """
        Collapse spaced single-letter patterns into words
        
        Handles evasion attempts like:
        - "a_s_s" -> "ass"
        - "f u c k" -> "fuck"
        - "m o t h e r f u c k e r" -> "motherfucker"
        - "a - b - c" -> "abc"
        
        Pattern: 3+ single letters separated by non-alphanumeric characters
        
        Args:
            text: Input text with potential spaced patterns
            
        Returns:
            Text with collapsed patterns
            
        Examples:
            "hello a_s_s world" -> "hello ass world"
            "info discord" -> "info discord" (no change)
            "I am a student" -> "I am a student" (no change - no consistent pattern)
        """
        # Pattern matches: single letter + (separator + single letter){2,}
        # {2,} means "2 or more" additional letters (so minimum 3 total letters)
        # \b ensures word boundaries (won't match inside words)
        # Supports extended Latin (À-ÿ, etc.)
        pattern = rf'\b([{LATIN_CHAR_CLASS}])(?:[\W_]+([{LATIN_CHAR_CLASS}])){{2,}}\b'
        
        def collapse_match(match):
            """Extract only letters from matched pattern"""
            matched_text = match.group(0)
            # Extract all letters (including extended Latin), collapse into single word
            letters = re.findall(rf'[{LATIN_CHAR_CLASS}]', matched_text)
            collapsed = ''.join(letters)
            print(f"[DETECTOR] Pattern collapse: '{matched_text}' -> '{collapsed}'")
            return collapsed
        
        collapsed_text = re.sub(pattern, collapse_match, text)
        
        # Only log if something changed
        if collapsed_text != text:
            print(f"[DETECTOR] Pre-processing: '{text}' -> '{collapsed_text}'")
        
        return collapsed_text
    
    def collapse_spaced_patterns_with_mapping(self, text: str) -> Tuple[str, Optional[List[Tuple[int, int, str]]]]:
        """
        Collapse spaced patterns and return mapping information
        
        Returns:
            Tuple of (collapsed_text, collapse_mapping)
            collapse_mapping: List of (original_start, original_end, collapsed_word)
                             or None if no patterns collapsed
        
        Examples:
            "hello a_s_s world" -> ("hello ass world", [(6, 11, "ass")])
            "m o t h e r f u c k" -> ("motherfuck", [(0, 19, "motherfuck")])
        """
        # Supports extended Latin (À-ÿ, etc.)
        pattern = rf'\b([{LATIN_CHAR_CLASS}])(?:[\W_]+([{LATIN_CHAR_CLASS}])){{2,}}\b'
        
        collapse_info = []
        
        def collapse_match(match):
            """Extract letters and track position"""
            matched_text = match.group(0)
            start_pos = match.start()
            end_pos = match.end()
            
            # Extract all letters (including extended Latin), collapse into single word
            letters = re.findall(rf'[{LATIN_CHAR_CLASS}]', matched_text)
            collapsed = ''.join(letters)
            
            # Store mapping info
            collapse_info.append((start_pos, end_pos, collapsed))
            
            print(f"[DETECTOR] Pattern collapse: '{matched_text}' -> '{collapsed}' (pos {start_pos}-{end_pos})")
            return collapsed
        
        collapsed_text = re.sub(pattern, collapse_match, text)
        
        # Only log if something changed
        if collapsed_text != text:
            print(f"[DETECTOR] Pre-processing: '{text}' -> '{collapsed_text}'")
        
        return collapsed_text, collapse_info if collapse_info else None
    
    def detect_all(self, text: str, provided_collapse_mapping: Optional[List[Tuple[int, int, str]]] = None) -> Dict:
        """
        Detect all filtered words in text using Aho-Corasick
        
        Args:
            text: Text to analyze (may already be collapsed)
            provided_collapse_mapping: Optional pre-computed collapse mapping (if text already collapsed)
            
        Returns:
            dict: {
                'flagged': List[DetectionResult],
                'clean': bool,
                'message': str,
                'collapse_mapping': mapping info
            }
        """
        if not self.automaton:
            return {
                'flagged': [],
                'clean': True,
                'message': 'No filter loaded',
                'original_text': text,
                'collapsed_text': text,
                'collapse_mapping': None
            }
        
        # PRE-PROCESSING: Collapse spaced patterns
        # If collapse_mapping provided, text is already collapsed - use provided mapping
        # Otherwise, perform collapse operation
        original_text = text
        
        if provided_collapse_mapping is not None:
            # Text is already collapsed, use provided mapping
            collapsed_text = text
            collapse_mapping = provided_collapse_mapping
        else:
            # Perform collapse operation
            collapsed_text, collapse_mapping = self.collapse_spaced_patterns_with_mapping(text)
        
        text = collapsed_text
        
        flagged_results = []
        # REMOVED: processed_words tracking
        # We need to detect ALL occurrences, not skip duplicates
        # Example: "daffodil...DAFFODIL" should detect "fodi" TWICE
        
        # STEP 1: Direct matches via Aho-Corasick (fast)
        # Track (word, position) pairs we've processed to avoid exact duplicates
        processed_pairs = set()
        
        # Track which filtered words were found in direct scan
        # (used to avoid duplicating in sliding window scan)
        found_words = set()
        
        for end_idx, (idx, word) in self.automaton.iter(text.lower()):
            # Create position-aware key (word at specific position)
            word_key = (word, end_idx)
            
            # Skip only if we've processed this exact word at this exact position
            if word_key in processed_pairs:
                continue
            
            processed_pairs.add(word_key)
            found_words.add(word)  # Track for sliding window deduplication
            
            # Run through v4.0 priority detection (returns list now)
            # Pass character position so detect_single can identify which specific occurrence
            results = self.detect_single(text, word, collapse_mapping, char_position=end_idx)
            
            # Add all results that should be flagged
            for result in results:
                if result.detection_type != DetectionType.NO_MATCH:
                    flagged_results.append(result)
        
        # STEP 2: Multi-word sliding window matches via Aho-Corasick
        # This catches patterns like:
        # - 2-word: "fodi" in "info discord"
        # - 3-word: "dago" in "find a good"
        words = self.extract_words(text)
        max_window = self.config.get('max_sliding_window', 3)
        
        if len(words) >= 2:
            # Track detections with their window sizes for deduplication
            window_detections = []
            
            # Check all window sizes from 2 to min(word_count, max_window)
            for window_size in range(2, min(len(words), max_window) + 1):
                text_lower = text.lower()
                current_pos = 0
                
                # Build N-word sliding windows
                for i in range(len(words) - window_size + 1):
                    # Find positions of all words in this window
                    word_positions = []
                    search_pos = current_pos
                    
                    for j in range(window_size):
                        word_idx = i + j
                        word_start = text_lower.find(words[word_idx].lower(), search_pos)
                        if word_start == -1:
                            break
                        word_positions.append((word_start, words[word_idx]))
                        search_pos = word_start + len(words[word_idx])
                    
                    # Skip if couldn't find all words
                    if len(word_positions) != window_size:
                        continue
                    
                    # Update position for next iteration
                    current_pos = word_positions[0][0] + 1
                    
                    # Calculate window range
                    window_start = word_positions[0][0]
                    window_end = word_positions[-1][0] + len(word_positions[-1][1])
                    
                    # Combine words and scan
                    window_words = [pos[1] for pos in word_positions]
                    window_combined = ''.join(window_words).lower()
                    
                    # Scan this window combination with Aho-Corasick
                    for end_idx, (idx, filtered_word) in self.automaton.iter(window_combined):
                        # DON'T skip based on word alone - we need to detect ALL occurrences
                        # Example: "fodi" EMBEDDING in "daffodil" AND "fodi" STRIPPED_WINDOW at junction
                        # Both are separate issues that need separate fixes
                        
                        # Store detection with window size for later deduplication
                        window_detections.append({
                            'filtered_word': filtered_word,
                            'window_size': window_size,
                            'window_words': window_words,
                            'window_start': window_start,
                            'window_end': window_end
                        })
            
            # Deduplicate: Prefer longer windows (more specific)
            # Group by filtered_word and position range
            unique_detections = {}
            for det in window_detections:
                key = det['filtered_word']
                range_key = (det['window_start'], det['window_end'])
                
                # If new or longer window, use it
                if key not in unique_detections or det['window_size'] > unique_detections[key]['window_size']:
                    unique_detections[key] = det
            
            # Create detection results from unique detections
            for filtered_word, det in unique_detections.items():
                # CRITICAL: Apply whitelist check to Aho-Corasick sliding window detections
                # Same logic as in _check_stripped_window()
                filtered_lower = filtered_word.lower()
                if filtered_lower in self.whitelist:
                    # Get combined window text and strip fancy unicode
                    window_words = det['window_words']
                    combined = ''.join(window_words)
                    combined_stripped = self._strip_fancy_for_detection(combined)
                    combined_lower = combined_stripped.lower()
                    
                    # Check if embedded
                    is_standalone = (filtered_lower == combined_lower)
                    
                    print(f"[DETECTOR DEBUG] Aho-Corasick whitelist check: '{filtered_lower}' in whitelist")
                    print(f"[DETECTOR DEBUG]   combined_lower: '{combined_lower}'")
                    print(f"[DETECTOR DEBUG]   is_standalone: {is_standalone}")
                    
                    if not is_standalone:
                        # Embedded and whitelisted - skip this detection
                        print(f"[DETECTOR DEBUG]   -> SKIPPING Aho-Corasick detection (embedded)")
                        continue
                    
                    print(f"[DETECTOR DEBUG]   -> KEEPING Aho-Corasick detection (standalone)")
                
                found_words.add(filtered_word)  # Track that we found this word
                
                result = DetectionResult(
                    detection_type=DetectionType.STRIPPED_WINDOW,
                    filtered_word=filtered_word,
                    full_word=None,
                    can_whitelist=False,
                    window_range=(det['window_start'], det['window_end']),
                    explanation=f"'{filtered_word}' found in {det['window_size']}-word window: {' + '.join(det['window_words'])} (positions {det['window_start']}-{det['window_end']})"
                )
                
                flagged_results.append(result)
                window_desc = ' + '.join([f"'{w}'" for w in det['window_words']])
                print(f"[DETECTOR] Sliding window found via Aho-Corasick: '{filtered_word}' in {det['window_size']}-word window {window_desc} (positions {det['window_start']}-{det['window_end']})")
        
        return {
            'flagged': flagged_results,
            'clean': len(flagged_results) == 0,
            'message': f"Found {len(flagged_results)} issue(s)" if flagged_results else "Clean",
            'original_text': original_text,
            'collapsed_text': collapsed_text,
            'collapse_mapping': collapse_mapping
        }
    
    def detect_single(self, text: str, filtered_word: str, collapse_mapping: Optional[List[Tuple[int, int, str]]] = None, char_position: Optional[int] = None) -> List[DetectionResult]:
        """
        Detect single filtered word using v4.0 algorithm
        
        Args:
            text: Text to analyze (already collapsed)
            filtered_word: Word to detect
            collapse_mapping: Optional list of (start, end, collapsed_word) tuples from collapse operation
            char_position: Optional character position from Aho-Corasick (end position of match)
            
        Returns:
            List of DetectionResults (may contain multiple for same word in different contexts)
            
        Priority:
            1. Embedding check (in alphanumeric words) - may return both EMBEDDING and STANDALONE
            2. Stripped sliding window check (with v4 whitelist embedding rule)
        """
        filtered_lower = filtered_word.lower()
        results = []
        
        # Extract collapsed words for whitelist override check
        collapsed_words = set()
        if collapse_mapping:
            for _, _, word in collapse_mapping:
                collapsed_words.add(word.lower())
        
        # Priority 1: Embedding check (returns list now)
        embedding_results = self._check_embedding(text, filtered_word, collapsed_words, char_position)
        
        if embedding_results:
            # Check whitelist rules for each result
            for result in embedding_results:
                if result.detection_type == DetectionType.EMBEDDING:
                    # CRITICAL: Don't apply whitelist if word was created by collapse
                    # Example: "a.s.s.a.s.s.i.n" -> "assassin" should NOT get whitelist protection
                    word_from_collapse = result.full_word and result.full_word.lower() in collapsed_words
                    
                    if not word_from_collapse and filtered_lower in self.whitelist:
                        # Natural embedding + whitelisted = skip
                        continue
                    # Otherwise: collapsed word OR not whitelisted = flag it
                # Add non-whitelisted results (STANDALONE always added, non-whitelisted EMBEDDING added)
                results.append(result)
            
            # If we found valid results, return them
            if results:
                return results
        
        # Priority 2: Stripped sliding window (only if no embedding results)
        stripped_result = self._check_stripped_window(text, filtered_word)
        if stripped_result:
            return [stripped_result]
        
        # No match found
        return [DetectionResult(
            detection_type=DetectionType.NO_MATCH,
            filtered_word=filtered_word,
            can_whitelist=False,
            explanation=f"'{filtered_word}' not found in message"
        )]
    
    
    def _check_embedding(self, text: str, filtered_word: str, collapsed_words: Optional[Set[str]] = None, char_position: Optional[int] = None) -> List[DetectionResult]:
        """
        Check if filtered word appears embedded in alphanumeric words
        
        CRITICAL: Checks ALL occurrences and returns ALL distinct detection types
        - Returns BOTH EMBEDDING and STANDALONE when word appears in both contexts
        - This allows optimizer to see full context (e.g., "assassin ass" shows both)
        - If char_position provided (from Aho-Corasick), finds the SPECIFIC occurrence at that position
        
        Args:
            text: Text to check
            filtered_word: Word to find
            collapsed_words: Optional set of words that were created by collapse (lowercase)
            char_position: Optional character position (end index) from Aho-Corasick match
            
        Returns:
            List of DetectionResults (may contain both EMBEDDING and STANDALONE)
        """
        words = self.extract_words(text)
        filtered_lower = filtered_word.lower()
        text_lower = text.lower()
        
        results = []
        has_standalone = False
        has_embedding = False
        
        # If char_position provided, find which word contains this specific match
        target_word_idx = None
        if char_position is not None:
            # Find which word contains the character at char_position
            char_count = 0
            for idx, word in enumerate(words):
                word_start = text_lower.find(word.lower(), char_count)
                word_end = word_start + len(word)
                
                # Check if the filtered word match ending at char_position is in this word
                match_start = char_position - len(filtered_lower) + 1
                if word_start <= match_start and char_position <= word_end:
                    target_word_idx = idx
                    break
                
                char_count = word_end
        
        for idx, word in enumerate(words):
            word_lower = word.lower()
            
            # If we have a target word index from char_position, only process that word
            if target_word_idx is not None and idx != target_word_idx:
                continue
            
            # Check if filtered word appears in this word
            if filtered_lower in word_lower:
                # Check if it's the entire word (standalone) or embedded
                is_standalone = (word_lower == filtered_lower)
                
                if is_standalone and not has_standalone:
                    # Found standalone occurrence
                    results.append(DetectionResult(
                        detection_type=DetectionType.STANDALONE,
                        filtered_word=filtered_word,
                        can_whitelist=False,
                        explanation=f"Standalone occurrence of '{filtered_word}'",
                        full_word=word,
                        word_position=idx,
                        match_char_end=char_position  # Store Aho-Corasick position
                    ))
                    has_standalone = True
                elif not is_standalone and not has_embedding:
                    # Embedded in larger word - save first occurrence
                    # Note: Whitelist check happens in detect_single, not here
                    results.append(DetectionResult(
                        detection_type=DetectionType.EMBEDDING,
                        filtered_word=filtered_word,
                        can_whitelist=filtered_lower not in self.whitelist,
                        explanation=f"'{filtered_word}' embedded in '{word}'",
                        full_word=word,
                        word_position=idx,
                        match_char_end=char_position  # Store Aho-Corasick position
                    ))
                    has_embedding = True
                
                # If we have both types, we can stop early
                if has_standalone and has_embedding:
                    break
        
        return results
    
    def _build_stripped_pattern(self, filtered_word: str) -> str:
        """
        Build regex pattern for stripped detection
        
        Args:
            filtered_word: Word to create pattern for
            
        Returns:
            str: Regex pattern
            
        Example:
            "ass" -> "a[^a-zA-Z0-9...]*s[^a-zA-Z0-9...]*s"
            Matches "a s s", "a_s_s", "a!!!s???s", etc.
            Supports extended Latin characters (À-ÿ, etc.)
        """
        pattern = ''
        for i, char in enumerate(filtered_word):
            pattern += re.escape(char)
            if i < len(filtered_word) - 1:
                # Allow zero or more non-alphanumeric characters between
                # Excludes all letters including extended Latin
                pattern += rf'[^{LATIN_ALNUM_CLASS}]*'
        return pattern
    
    def _check_stripped_window(self, text: str, filtered_word: str) -> Optional[DetectionResult]:
        """
        Check filtered word in sliding windows of adjacent words
        
        v4.0 Algorithm - Validates with whitelist embedding rule
        
        Logic:
        1. Combine adjacent words in window
        2. Check if filtered word appears in combined window
        3. Verify with regex pattern to ensure it's stripped (has non-alphanumeric separators)
        4. Apply whitelist embedding rule:
           - If whitelisted AND embedded in combined window -> Don't flag
           - Otherwise -> Flag
        
        Example v4.0 behavior:
            "As secret as" + "ass" (NOT whitelisted) -> STRIPPED_WINDOW (flagged)
            "As secret as" + "ass" (IS whitelisted) -> NO_MATCH (protected by whitelist)
            "a s s" -> STRIPPED_WINDOW (flagged regardless)
        
        Args:
            text: Text to check
            filtered_word: Word to find
            
        Returns:
            DetectionResult if found and should be flagged, None otherwise
        """
        words = self.extract_words(text)
        
        if len(words) < 2:
            # Single word or empty - no sliding window needed
            return None
        
        pattern = self._build_stripped_pattern(filtered_word)
        filtered_lower = filtered_word.lower()
        
        # Slide window across words
        for i in range(len(words) - self.window_size + 1):
            # Get window of adjacent words
            window_words = words[i:i + self.window_size]
            combined = ''.join(window_words)
            
            # CRITICAL: Strip fancy unicode for detection (game strips these)
            # Otherwise "daff0🅳il" prevents detection of "fodi"
            combined_stripped = self._strip_fancy_for_detection(combined)
            combined_lower = combined_stripped.lower()
            
            # Check if filtered word appears in this window
            if filtered_lower not in combined_lower:
                continue
            
            # Find this window in original text
            window_start = text.lower().find(window_words[0].lower())
            window_end_word = window_words[-1]
            window_end_pos = text.lower().rfind(window_end_word.lower())
            window_end = window_end_pos + len(window_end_word)
            window_text = text[window_start:window_end]
            
            # Check if pattern matches in this window
            match = re.search(pattern, window_text, re.IGNORECASE)
            
            if not match:
                continue
            
            matched_text = match.group()
            
            # v4.0: Apply whitelist embedding rule FIRST
            # CRITICAL: Check whitelist BEFORE skipping pure alphanumeric
            # because modified words like "a❤ssassin" won't trigger embedding detection
            if filtered_lower in self.whitelist:
                # Whitelisted = has embedding protection
                # Check if embedded in combined window string
                
                # Is it the entire combined string (standalone)?
                is_standalone = (filtered_lower == combined_lower)
                
                print(f"[DETECTOR DEBUG] Whitelist check: '{filtered_lower}' in whitelist")
                print(f"[DETECTOR DEBUG]   combined_lower: '{combined_lower}'")
                print(f"[DETECTOR DEBUG]   is_standalone: {is_standalone}")
                
                if not is_standalone:
                    # Embedded in combined window string
                    # Apply embedding rule -> Don't flag
                    print(f"[DETECTOR DEBUG]   -> SKIPPING (embedded)")
                    continue
                
                # If standalone in combined string, still flag
                print(f"[DETECTOR DEBUG]   -> FLAGGING (standalone)")
            
            # Skip if matched text is pure alphanumeric (including extended Latin)
            # (optimization: pure alphanumeric is less likely to be problematic)
            if re.match(rf'^[{LATIN_ALNUM_CLASS}]+$', matched_text):
                continue
            
            # Not whitelisted OR standalone -> Flag it
            return DetectionResult(
                detection_type=DetectionType.STRIPPED_WINDOW,
                filtered_word=filtered_word,
                can_whitelist=filtered_lower not in self.whitelist,
                explanation=f"'{filtered_word}' found in window: {window_words}",
                matched_text=matched_text,
                window_words=window_words,
                window_range=(window_start, window_end),
                debug_info={
                    'combined': combined,
                    'window_text': window_text,
                    'window_index': i,
                    'whitelisted': filtered_lower in self.whitelist,
                    'embedded_in_combined': filtered_lower in combined_lower and filtered_lower != combined_lower
                }
            )
        
        return None

    def update_automaton(self, new_automaton):
        """
        Update the Aho-Corasick automaton for live filter reload

        Enables filter list updates without restarting the application (v1.0.2 feature).
        v1.0.3: Added performance monitoring.

        Args:
            new_automaton: New Aho-Corasick automaton from FilterLoader.reload()

        Example:
            # After UI adds a filter entry
            loader.reload()
            detector.update_automaton(loader.automaton)
        """
        # Performance monitoring (v1.0.3)
        start_time = time.perf_counter()

        self.automaton = new_automaton

        # Log performance (v1.0.3)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        log.debug(f"Automaton updated in {elapsed_ms:.3f}ms")
        log.info("Filter automaton updated - new entries now active")

    def get_stats(self) -> Dict:
        """
        Get detector statistics
        
        Returns:
            dict: Statistics about loaded filters
        """
        return {
            'whitelist_size': len(self.whitelist),
            'window_size': self.window_size
        }


# Module information
__version__ = '4.0.0'
__author__ = 'Jokoril'
__status__ = 'Production'
