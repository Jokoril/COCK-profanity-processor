#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Message Optimizer Module
=========================
Multi-stage message optimization for censorship evasion

Features:
- Stage 1: Link Protection (preserve URLs)
- Stage 2: Leet-speak (0 byte overhead)
- Stage 3: Fancy Unicode (+3 bytes/char)
- Stage 4: Shorthand (saves bytes)
- Stage 5: Truncation (last resort)

Usage:
    from message_optimizer import MessageOptimizer
    
    optimizer = MessageOptimizer(detector, leet, fancy, shorthand)
    result = optimizer.optimize("bad message with ass")
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import special_char_interspacing


@dataclass
class OptimizationResult:
    """Result of message optimization"""
    original: str
    optimized: str
    stages_applied: List[str]
    byte_change: int
    success: bool
    flagged_words: List[str]
    explanation: str
    links_modified: bool = False  # Set to True if numeral words in links were modified
    paste_part: str = ""  # Remainder for multi-part messages (empty if all fits)
    partial_optimization: bool = False  # ADD THIS LINE



class MessageOptimizer:
    """
    Multi-stage message optimizer for censorship evasion
    
    Optimization stages:
        1. Link Protection - Preserve URLs from modification
        2. Leet-speak - Character substitution (0 byte overhead)
        3. Fancy Unicode - Unicode lookalikes (+3 bytes/char)
        4. Shorthand - Text compression (saves bytes)
        5. Truncation - Remove flagged words (last resort)
    """
    
    # URL pattern for link protection (with and without protocol)
    URL_PATTERN = re.compile(
        r'(?:http[s]?://|(?:www\.|[a-zA-Z0-9-]+\.(?:gg|com|net|org|io|tv|me|co)/))(?:[a-zA-Z]|[0-9]|[$-_@.&+/]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    
    def __init__(self, detector, leet_converter, fancy_converter, shorthand_handler, config: Dict):
        """
        Initialize message optimizer
        
        Args:
            detector: FastCensorDetector instance
            leet_converter: LeetSpeakConverter instance
            fancy_converter: FancyTextConverter instance
            shorthand_handler: ShorthandHandler instance
            config: Configuration dictionary
        """
        self.detector = detector
        self.leet = leet_converter
        self.fancy = fancy_converter
        self.shorthand = shorthand_handler
        self.config = config
        
        # Initialize special character interspacing
        self.special_char = special_char_interspacing.SpecialCharInterspacing(config)
        
        # Get optimization settings from config
        self.enable_leet = config.get('optimization', {}).get('leet_speak', True)
        self.enable_unicode = config.get('optimization', {}).get('fancy_unicode', True)
        self.enable_shorthand = config.get('optimization', {}).get('shorthand', True)
        self.enable_link_protection = config.get('optimization', {}).get('link_protection', True)
        self.enable_special_char = config.get('optimization', {}).get('special_char_interspacing', False)
        
        # Byte limit (default 80)
        self.byte_limit = config.get('byte_limit', 80)
        
        # Maximum message length (optional, deprecated in favor of byte_limit)
        self.max_length = config.get('max_message_length', None)
    
    def force_optimize_all(self, text: str) -> str:
        """
        Force optimization on ALL characters regardless of detection
        
        Two modes:
        1. Special Character Interspacing (if enabled):
           - Inserts special character between every character
           - Example: "fuck" → "f❤u❤c❤k"
        
        2. Standard Force Mode (default):
           - Numbers → Interspaced with Hangul araea (ᆞ)
           - Vowels → Leetspeak (if enabled)
           - Consonants → Fancy Unicode (if enabled)
        
        Used when game censors patterns we can't detect.
        Triggered by force optimize hotkey (default: Ctrl+F12)
        
        Args:
            text: Original text
            
        Returns:
            Text with all content optimized
        """
        # Protect links first
        links = []
        if self.enable_link_protection:
            text, links = self._protect_links(text)
        
        # Special Character Interspacing Mode (if enabled)
        if self.enable_special_char:
            print(f"[OPTIMIZER] Force mode with special char '{self.special_char.get_char()}': interspersing every character")
            
            # Manually intersperse while skipping link placeholders
            special_char = self.special_char.get_char()
            result = []
            i = 0
            
            while i < len(text):
                # Check if we're at the start of a link placeholder
                if text[i:i+7] == '__LINK_':
                    # Find the end of the placeholder (__LINK_N__)
                    end = text.find('__', i + 7)
                    if end != -1:
                        # Copy entire placeholder unchanged
                        result.append(text[i:end+2])
                        i = end + 2
                        continue
                
                # Add character
                result.append(text[i])
                
                # Add special char after (except for last character or before space)
                if i < len(text) - 1:
                    # Don't add special char before/after spaces
                    if text[i] != ' ' and text[i+1] != ' ':
                        result.append(special_char)
                
                i += 1
            
            optimized = ''.join(result)
            
            # Restore links
            if links:
                optimized = self._restore_links(optimized, links)
            
            print(f"[OPTIMIZER] Force optimize complete: {len(text)} → {len(optimized)} chars, {len(optimized.encode('utf-8'))} bytes")
            return optimized
        
        # Standard Force Mode (numbers=araea, vowels=leet, consonants=fancy)
        VOWELS = set('aeiouAEIOU')
        
        print(f"[OPTIMIZER] Force optimizing all words (numbers=araea, vowels=leet, consonants=fancy)")
        
        # Step 1: Intersperse all number sequences with Hangul araea (ᆞ)
        # Skip numbers inside link placeholders (__LINK_0__, etc.)
        result = []
        i = 0
        while i < len(text):
            # Check if we're at the start of a link placeholder
            if text[i:i+7] == '__LINK_':
                # Find the end of the placeholder (__LINK_N__)
                end = text.find('__', i + 7)
                if end != -1:
                    # Copy entire placeholder unchanged
                    result.append(text[i:end+2])
                    i = end + 2
                    continue
            
            char = text[i]
            
            if char.isdigit():
                # Start of a number sequence - collect all consecutive digits
                num_sequence = char
                j = i + 1
                while j < len(text) and text[j].isdigit():
                    num_sequence += text[j]
                    j += 1
                
                # Intersperse digits with ᆞ (Hangul araea)
                # Example: "420" → "4ᆞ2ᆞ0"
                interspaced = 'ᆞ'.join(num_sequence)
                result.append(interspaced)
                
                # Skip ahead past the number sequence
                i = j
            else:
                result.append(char)
                i += 1
        
        text = ''.join(result)
        
        # Step 2: Optimize letters (vowels and consonants)
        # Skip letters inside link placeholders
        result = []
        i = 0
        style = self.config.get('optimization', {}).get('fancy_text_style', 'squared')

        while i < len(text):
            # Check if we're at the start of a link placeholder
            if text[i:i+7] == '__LINK_':
                # Find the end of the placeholder (__LINK_N__)
                end = text.find('__', i + 7)
                if end != -1:
                    # Copy entire placeholder unchanged
                    result.append(text[i:end+2])
                    i = end + 2
                    continue
            
            char = text[i]
            
            if char.isalpha():
                if char in VOWELS:
                    # Vowels: Leetspeak (if enabled) OR Fancy Unicode (if leet disabled)
                    if self.enable_leet:
                        leet_char = self.leet.convert(char)
                        if leet_char != char:  # Conversion succeeded
                            result.append(leet_char)
                        else:
                            result.append(char)
                    elif self.enable_unicode:
                        # Leet disabled but fancy enabled - use fancy for vowels
                        result.append(self.fancy.convert(char, style))
                    else:
                        # Both disabled - keep vowel unchanged
                        result.append(char)
                else:
                    # Consonants: Fancy unicode (if enabled)
                    if self.enable_unicode:
                        result.append(self.fancy.convert(char, style))
                    else:
                        result.append(char)
            else:
                result.append(char)
            
            i += 1

        optimized = ''.join(result)
        
        # Restore links (which have numbers preserved)
        if links:
            optimized = self._restore_links(optimized, links)
        
        print(f"[OPTIMIZER] Force optimize complete: {len(text)} → {len(optimized)} chars, {len(optimized.encode('utf-8'))} bytes")
        
        return optimized
    
    def _convert_char(self, char: str, style: str = 'squared') -> str:
        """
        Convert a character using enabled optimization methods
        
        Priority:
        1. Leet speak (if enabled) - 0 byte overhead
        2. Fancy unicode (if enabled) - +3 bytes overhead
        3. Return unchanged if both disabled
        
        Args:
            char: Character to convert
            style: Fancy text style (if fancy enabled)
        
        Returns:
            Converted character
        """
        # Try leet speak first (lower byte overhead)
        if self.enable_leet:
            leet_char = self.leet.convert(char)
            if leet_char != char:  # Leet conversion succeeded
                return leet_char
        
        # Try fancy unicode if leet didn't work
        if self.enable_unicode:
            return self.fancy.convert(char, style)
        
        # If both disabled, return unchanged
        return char
    
    def _strip_fancy_unicode(self, text: str) -> str:
        """
        Strip fancy unicode characters back to ASCII
        
        This simulates what the game does - it strips fancy unicode,
        but KEEPS leet-speak characters like ¢, $, @, etc.
        
        Example:
            "spe🅲ialist" -> "speialist" (removes 🅲, 'c' is gone!)
            "fu¢k" -> "fu¢k" (keeps ¢, leet-speak is preserved!)
        
        Args:
            text: Text with fancy unicode characters
            
        Returns:
            Text with fancy unicode stripped but leet-speak preserved
        """
        result = []
        
        # Fancy unicode ranges (4-byte characters we want to strip)
        fancy_ranges = [
            (0x1F130, 0x1F149),  # Squared
            (0x1D400, 0x1D7FF),  # Mathematical Alphanumeric (bold, italic, etc.)
            (0x24B6, 0x24E9),    # Circled
            (0x1F150, 0x1F189),  # Negative circled/squared
        ]
        
        for char in text:
            char_code = ord(char)
            
            # Check if character is fancy unicode
            is_fancy = any(start <= char_code <= end for start, end in fancy_ranges)
            
            if not is_fancy:
                # Keep ASCII, Hangul separator, and leet-speak (¢, $, @, etc.)
                result.append(char)
            # else: skip fancy unicode
        
        return ''.join(result)
    
    def _would_create_issues_if_removed(self, text: str, position: int, target_issue: str, collapse_mapping: Optional[List[Tuple[int, int, str]]] = None) -> bool:
        """
        Check if removing a character at position would create NEW filtered words
        OR fail to fix the target issue
        
        CRITICAL CHECKS:
        1. Does preview create NEW issues? (e.g., "peia" from removing 'c')
        2. Does preview STILL have the target issue we're trying to fix?
        
        Example - "d4ffodil" trying to fix "fodi":
            Position 82 ('f'):
              Preview: "d4fodil" (stripped)
              NEW issues? No
              STILL has "fodi"? YES -> SKIP (doesn't fix it!)
            
            Position 84 ('o'):
              Preview: "d4ffdil" (stripped)
              NEW issues? No
              STILL has "fodi"? NO -> SAFE (actually fixes it!)
        
        Args:
            text: Current text
            position: Position of character to potentially replace
            target_issue: The filtered word we're trying to fix
            collapse_mapping: Optional collapse mapping for whitelist override detection
            
        Returns:
            True if removing would create issues OR not fix target, False if safe
        """
        # Get EXISTING issues in current text
        original_detection = self.detector.detect_all(text, collapse_mapping)
        original_issues = set(r.filtered_word.lower() for r in original_detection['flagged'])
        
        # Preview what text looks like with character removed (simulates fancy->stripped)
        preview = text[:position] + text[position + 1:]
        
        # Get issues in preview
        preview_detection = self.detector.detect_all(preview, collapse_mapping)
        preview_issues = set(r.filtered_word.lower() for r in preview_detection['flagged'])
        
        # Check 1: Find NEW issues (in preview but not in original)
        new_issues = preview_issues - original_issues
        
        if new_issues:
            # Would create NEW issues!
            print(f"[OPTIMIZER] Position {position} ('{text[position]}') would create NEW issues: {list(new_issues)}")
            return True
        
        # Check 2: Does preview STILL have the target issue?
        target_lower = target_issue.lower()
        if target_lower in preview_issues:
            # Doesn't fix the issue we're trying to solve!
            print(f"[OPTIMIZER] Position {position} ('{text[position]}') doesn't fix '{target_issue}' - trying next")
            return True
        
        return False
    
    def optimize_words(self, text: str, words_to_optimize: List[str]) -> OptimizationResult:
        """
        Optimize only specific words in the text
        
        Used for mixed messages where some words should be optimized
        and others left as-is (e.g., whitelisted embedded words)
        
        Args:
            text: Original message
            words_to_optimize: List of specific words to optimize
        
        Returns:
            OptimizationResult with optimization details
        """
        original = text
        current = text
        stages_applied = []
        
        # Sort by length descending to handle longer words first
        words_to_optimize = sorted(set(words_to_optimize), key=len, reverse=True)
        
        # Stage 1: Leet-speak (try first - 0 byte overhead)
        if self.enable_leet:
            leet_result = self._apply_leet_speak(current, words_to_optimize)
            if leet_result and self.detector.detect_all(leet_result)['clean']:
                current = leet_result
                stages_applied.append('leet_speak')
                
                return OptimizationResult(
                    original=original,
                    optimized=current,
                    stages_applied=stages_applied,
                    byte_change=len(current.encode('utf-8')) - len(original.encode('utf-8')),
                    success=True,
                    flagged_words=words_to_optimize,
                    explanation="Optimized using leet-speak"
                )
        
        # Stage 2: Fancy Unicode
        if self.enable_unicode:
            unicode_result = self._apply_fancy_unicode(current, words_to_optimize)
            if unicode_result and self.detector.detect_all(unicode_result)['clean']:
                current = unicode_result
                stages_applied.append('fancy_unicode')
                
                return OptimizationResult(
                    original=original,
                    optimized=current,
                    stages_applied=stages_applied,
                    byte_change=len(current.encode('utf-8')) - len(original.encode('utf-8')),
                    success=True,
                    flagged_words=words_to_optimize,
                    explanation="Optimized using fancy unicode"
                )
        
        # Failed to optimize
        return OptimizationResult(
            original=original,
            optimized=current,
            stages_applied=stages_applied,
            byte_change=0,
            success=False,
            flagged_words=words_to_optimize,
            explanation="Could not optimize specified words"
        )
    
    def _optimize_with_positions(self, text: str, detection: Dict, stages_applied: List[str], links: List, filtered_words: List[str], collapse_mapping: Optional[List[Tuple[int, int, str]]] = None, links_modified: bool = False, original_text: str = None) -> OptimizationResult:
        """
        Optimize using position information for sliding window and embedding detections
        
        Works on collapsed text (spaced patterns already collapsed) and text with
        numeral words already optimized (e.g., "420" → "4ᆞ20")
        
        Handles cases where word boundaries don't work:
        - Sliding window: 'info discord' → 'in🄵o discord'
        - Embeddings: 'assassin' → '🄰ss🄰ssin'
        - Collapsed patterns: 'motherfucking' → 'mother🄵ucking'
        
        Args:
            text: Text to optimize (collapsed, with numeral words already optimized)
            detection: Detection results with position info
            stages_applied: Stages already applied (may include 'numeral_delimiter')
            links: Extracted links
            filtered_words: List of filtered words for reference
            collapse_mapping: Optional collapse mapping for whitelist override detection
            links_modified: Whether links were modified during numeral optimization
            original_text: Original text before numeral optimization (for result)
        
        Returns:
            OptimizationResult
        """
        # Use original_text if provided, otherwise use text
        result_original = original_text if original_text is not None else text
        # Convert text to list for character-level replacement
        result = list(text)
        replaced_positions = set()  # Track what we've already replaced
        
        # Get fancy text style from config
        style = self.config.get('optimization', {}).get('fancy_text_style', 'squared')
        
        # Handle detections (sliding window, embeddings, standalone)
        for r in detection['flagged']:
            if r.detection_type.name == 'STRIPPED_WINDOW' and r.window_range:
                # Sliding window detection - find where filtered word starts in the window
                start, end = r.window_range
                filtered_word = r.filtered_word.lower()
                
                # Extract the window text and strip it (like detection does)
                window_text_raw = text[start:end]
                # Extract words from window and combine (strips punctuation)
                window_words = self.detector.extract_words(window_text_raw)
                window_text_stripped = ''.join(window_words).lower()
                
                # Find where the filtered word appears in the STRIPPED window
                # For "fodi" in "infodiscord", this gives us position 2 ('f')
                filtered_pos_in_stripped = window_text_stripped.find(filtered_word)
                
                if filtered_pos_in_stripped >= 0:
                    # Now find the corresponding position in the original text
                    # Count alphanumeric characters in raw window text until we reach filtered_pos
                    char_count = 0
                    for idx, char in enumerate(window_text_raw):
                        if char.isalnum():
                            if char_count == filtered_pos_in_stripped:
                                # Found it! This is where filtered word starts
                                target_pos = start + idx
                                
                                if target_pos < len(result) and result[target_pos].isalpha() and target_pos not in replaced_positions:
                                    # PRE-VALIDATION: Check if removing this character would create issues
                                    current_text = ''.join(result)
                                    if self._would_create_issues_if_removed(current_text, target_pos, filtered_word, collapse_mapping):
                                        print(f"[OPTIMIZER] Sliding window: SKIPPING pos {target_pos} - would create issues when stripped")
                                    else:
                                        old_char = result[target_pos]
                                        result[target_pos] = self._convert_char(result[target_pos], style)
                                        replaced_positions.add(target_pos)
                                        print(f"[OPTIMIZER] Sliding window: replaced char at pos {target_pos} ('{filtered_word}' starts here): '{old_char}' → '{result[target_pos]}'")
                                break
                            char_count += 1
                else:
                    # Fallback: replace first alphabetic character in window
                    for i in range(start, min(end, len(result))):
                        if result[i].isalpha() and i not in replaced_positions:
                            # PRE-VALIDATION: Check if removing this character would create issues
                            current_text = ''.join(result)
                            if self._would_create_issues_if_removed(current_text, i, filtered_word, collapse_mapping):
                                print(f"[OPTIMIZER] Sliding window: SKIPPING pos {i} (fallback) - would create issues when stripped")
                                continue  # Try next character in window
                            else:
                                old_char = result[i]
                                result[i] = self._convert_char(result[i], style)
                                replaced_positions.add(i)
                                print(f"[OPTIMIZER] Sliding window: replaced char at pos {i}: '{old_char}' → '{result[i]}'")
                                break
            
            elif r.detection_type.name == 'EMBEDDING':
                filtered_word = r.filtered_word
                full_word = r.full_word if r.full_word else filtered_word
                
                # CRITICAL: Use match_char_end from Aho-Corasick to find the EXACT occurrence
                # This handles multiple occurrences of the same word (e.g., "ass" twice in "assassin")
                if r.match_char_end is not None:
                    # Calculate where the filtered word starts based on end position
                    text_lower = text.lower()
                    filtered_lower = filtered_word.lower()
                    match_start = r.match_char_end - len(filtered_lower) + 1
                    
                    # Find the full word that contains this match
                    # (We know it's there from detection, just need to find word boundaries)
                    # Walk backwards to find word start
                    word_start = match_start
                    while word_start > 0 and text[word_start - 1].isalnum():
                        word_start -= 1
                    
                    # Calculate offset of filtered word within full word
                    offset_in_word = match_start - word_start
                else:
                    # Fallback: use old method (shouldn't happen with Aho-Corasick)
                    full_word_lower = full_word.lower()
                    text_lower = text.lower()
                    word_start = text_lower.find(full_word_lower)
                    offset_in_word = full_word.lower().find(filtered_word.lower())
                
                if word_start >= 0 and offset_in_word >= 0:
                    
                    if offset_in_word >= 0:
                        # Try each character in the filtered word
                        for i in range(len(filtered_word)):
                            char_pos = word_start + offset_in_word + i
                            
                            # Skip if already replaced or not alphanumeric
                            if char_pos >= len(result) or not result[char_pos].isalnum() or char_pos in replaced_positions:
                                continue
                            
                            old_char = result[char_pos]
                            
                            # TRANSFORMATION PRIORITY: Special char > Leet > Fancy
                            if self.enable_special_char:
                                # Override: Use special character interspacing
                                new_char = self.special_char.get_char()
                                transform_type = 'special'
                            elif self.enable_leet and old_char in self.leet.mapping:
                                # Leet-speak available for this character (cheap: 1 byte)
                                new_char = self.leet.mapping[old_char]
                                transform_type = 'leet'
                            else:
                                # Fallback: Fancy Unicode (expensive: 4 bytes)
                                new_char = self._convert_char(old_char, style)
                                transform_type = 'fancy'
                            
                            # Apply transformation temporarily
                            result[char_pos] = new_char
                            replaced_positions.add(char_pos)
                            
                            # VALIDATION: Test if this helps
                            test_text = ''.join(result)
                            
                            # Simulate game behavior: strip fancy unicode, keep leet
                            stripped_test = self._strip_fancy_unicode(test_text)
                            
                            # Check against filter (CRITICAL: pass collapse_mapping!)
                            test_detection = self.detector.detect_all(stripped_test, collapse_mapping)
                            
                            # Check if we're clean now
                            if test_detection['clean']:
                                # Success! Fully clean
                                print(f"[OPTIMIZER] Initial: {transform_type.upper()} at pos {char_pos} in '{full_word}': '{old_char}' -> '{new_char}' - CLEAN!")
                                break  # Done with this detection
                            
                            # Count occurrences of THIS specific filtered word (handles multi-occurrence)
                            original_word_count = sum(
                                1 for det in detection['flagged'] 
                                if det.filtered_word.lower() == filtered_word.lower()
                            )
                            new_word_count = sum(
                                1 for det in test_detection['flagged'] 
                                if det.filtered_word.lower() == filtered_word.lower()
                            )
                            
                            # Also check total issue count
                            current_issue_count = len(test_detection['flagged'])
                            original_issue_count = len(detection['flagged'])
                            
                            # RELAXED VALIDATION: Accept if word count decreased, even if total went up slightly
                            # Allow total to increase by up to 2 per word fixed (fancy unicode stripping side effects)
                            words_fixed = original_word_count - new_word_count
                            max_acceptable_increase = words_fixed * 2
                            total_increase = current_issue_count - original_issue_count
                            
                            if new_word_count < original_word_count and total_increase <= max_acceptable_increase:
                                # Made progress on THIS word, total increase is acceptable
                                print(f"[OPTIMIZER] Initial: {transform_type.upper()} at pos {char_pos} in '{full_word}': '{old_char}' -> '{new_char}' - progress ({original_word_count}->{new_word_count} '{filtered_word}', total: {original_issue_count}->{current_issue_count}), KEPT")
                                detection = test_detection
                            elif current_issue_count < original_issue_count:
                                # Didn't help THIS word but reduced total issues, keep it
                                print(f"[OPTIMIZER] Initial: {transform_type.upper()} at pos {char_pos} in '{full_word}': '{old_char}' -> '{new_char}' - progress (total: {original_issue_count}->{current_issue_count} issues), KEPT")
                                detection = test_detection
                            else:
                                # No progress OR created new issues - try fancy unicode fallback if this was leet-speak
                                if transform_type == 'leet' and self.enable_unicode and not self.enable_special_char:
                                    # Leet failed, try fancy unicode as fallback
                                    fancy_char = self._convert_char(old_char, style)
                                    result[char_pos] = fancy_char
                                    
                                    # Validate fancy unicode
                                    fancy_test_text = ''.join(result)
                                    fancy_stripped = self._strip_fancy_unicode(fancy_test_text)
                                    fancy_detection = self.detector.detect_all(fancy_stripped, collapse_mapping)
                                    
                                    if fancy_detection['clean']:
                                        # Fancy unicode succeeded!
                                        print(f"[OPTIMIZER] Initial: FANCY at pos {char_pos} in '{full_word}': '{old_char}' -> '{fancy_char}' - CLEAN (leet fallback)!")
                                        break
                                    
                                    # Check if fancy made progress
                                    fancy_word_count = sum(
                                        1 for det in fancy_detection['flagged']
                                        if det.filtered_word.lower() == filtered_word.lower()
                                    )
                                    fancy_issue_count = len(fancy_detection['flagged'])
                                    
                                    # RELAXED VALIDATION for fancy fallback too
                                    fancy_words_fixed = original_word_count - fancy_word_count
                                    max_acceptable_fancy_increase = fancy_words_fixed * 2
                                    fancy_total_increase = fancy_issue_count - original_issue_count
                                    
                                    if fancy_word_count < original_word_count and fancy_total_increase <= max_acceptable_fancy_increase:
                                        # Fancy made progress on THIS word, total increase acceptable
                                        print(f"[OPTIMIZER] Initial: FANCY at pos {char_pos} in '{full_word}': '{old_char}' -> '{fancy_char}' - progress ({original_word_count}->{fancy_word_count} '{filtered_word}', total: {original_issue_count}->{fancy_issue_count}), KEPT (leet fallback)")
                                        detection = fancy_detection
                                    elif fancy_issue_count < original_issue_count:
                                        # Fancy reduced total issues
                                        print(f"[OPTIMIZER] Initial: FANCY at pos {char_pos} in '{full_word}': '{old_char}' -> '{fancy_char}' - progress (total: {original_issue_count}->{fancy_issue_count} issues), KEPT (leet fallback)")
                                        detection = fancy_detection
                                    else:
                                        # Both leet and fancy failed - REVERT completely
                                        result[char_pos] = old_char
                                        replaced_positions.remove(char_pos)
                                        print(f"[OPTIMIZER] Initial: LEET+FANCY at pos {char_pos} in '{full_word}': '{old_char}' - no progress (both failed), REVERTED")
                                else:
                                    # No fallback available - REVERT
                                    result[char_pos] = old_char
                                    replaced_positions.remove(char_pos)
                                    print(f"[OPTIMIZER] Initial: {transform_type.upper()} at pos {char_pos} in '{full_word}': '{old_char}' -> '{new_char}' - no progress ({original_word_count}={new_word_count} '{filtered_word}', total={current_issue_count}), REVERTED")
            
            
            elif r.detection_type.name == 'STANDALONE':
                # Standalone - use word-boundary replacement
                word_to_replace = r.full_word if r.full_word else r.filtered_word
                
                # Skip pure numerals - they should have been handled in pre-stage
                if word_to_replace.isdigit():
                    print(f"[OPTIMIZER] Standalone: skipping pure numeral '{word_to_replace}' (should be handled by numeral optimizer)")
                    continue
                
                pattern = r'\b' + re.escape(word_to_replace) + r'\b'
                
                # Replace first letter only
                def replace_first_letter(match):
                    matched_word = match.group(0)
                    if len(matched_word) > 0 and matched_word[0].isalpha():
                        first_char_converted = self._convert_char(matched_word[0], style)
                        return first_char_converted + matched_word[1:]
                    return matched_word
                
                # Convert list back to string for regex replacement
                temp_text = ''.join(result)
                temp_text = re.sub(pattern, replace_first_letter, temp_text, flags=re.IGNORECASE)
                result = list(temp_text)
                print(f"[OPTIMIZER] Standalone: replaced first letter of '{word_to_replace}'")
        
        optimized = ''.join(result)
        
        # Add stages based on what's enabled
        if self.enable_leet:
            stages_applied.append('leet_speak')
        if self.enable_unicode:
            stages_applied.append('fancy_unicode')
        
        # Iteratively optimize until clean or no progress
        # This handles cases like "assassin" which contains "ass" twice
        max_iterations = 10
        iteration = 1
        
        # IMPORTANT: Preserve replaced_positions across iterations
        # This prevents replacing the same position multiple times
        # (e.g., both 'f's in "daffodils")
        
        while iteration <= max_iterations:
            # Re-detect to check if clean (CRITICAL: pass collapse_mapping!)
            check_detection = self.detector.detect_all(optimized, collapse_mapping)
            
            if check_detection['clean']:
                # Add final stripped validation
                stripped_text = self._strip_fancy_unicode(optimized)
                stripped_detection = self.detector.detect_all(stripped_text)
                
                if stripped_detection['clean']:
                    print(f"[OPTIMIZER] Iterative optimization succeeded after {iteration} iteration(s)")
                    print(f"[OPTIMIZER] Final validation: Stripped version CLEAN")
                else:
                    # This shouldn't happen with pre-validation, but warn if it does
                    print(f"[OPTIMIZER] WARNING: Stripped version has issues despite pre-validation!")
                    print(f"[OPTIMIZER] Stripped issues: {[r.filtered_word for r in stripped_detection['flagged']]}")
                break
            
            # Still has issues - try to optimize further
            print(f"[OPTIMIZER] Iteration {iteration}: Still detected {len(check_detection['flagged'])} issue(s), continuing...")
            
            # Track if we made any changes this iteration
            made_changes = False
            result = list(optimized)
            
            # Handle detections (no collapse_mapping needed - already working on collapsed text)
            for r in check_detection['flagged']:
                if r.detection_type.name == 'STRIPPED_WINDOW' and r.window_range:
                    start, end = r.window_range
                    filtered_word = r.filtered_word.lower()
                    
                    # Extract the window text and strip it
                    window_text_raw = optimized[start:end]
                    window_words = self.detector.extract_words(window_text_raw)
                    window_text_stripped = ''.join(window_words).lower()
                    
                    # Find where the filtered word appears in the STRIPPED window
                    filtered_pos_in_stripped = window_text_stripped.find(filtered_word)
                    
                    if filtered_pos_in_stripped >= 0:
                        # Find corresponding position in original text
                        char_count = 0
                        for idx, char in enumerate(window_text_raw):
                            if char.isalnum():
                                if char_count == filtered_pos_in_stripped:
                                    target_pos = start + idx
                                    
                                    # Check if already replaced
                                    if target_pos < len(result) and result[target_pos].isalpha() and target_pos not in replaced_positions:
                                        # PRE-VALIDATION: Check if removing this character would create issues
                                        current_text = ''.join(result)
                                        if self._would_create_issues_if_removed(current_text, target_pos, filtered_word, collapse_mapping):
                                            print(f"[OPTIMIZER] Iteration {iteration}: SKIPPING pos {target_pos} - would create issues when stripped")
                                        else:
                                            old_char = result[target_pos]
                                            result[target_pos] = self._convert_char(result[target_pos], style)
                                            replaced_positions.add(target_pos)
                                            made_changes = True
                                            print(f"[OPTIMIZER] Iteration {iteration}: sliding window at pos {target_pos} ('{filtered_word}' starts here): '{old_char}' → '{result[target_pos]}'")
                                    break
                                char_count += 1
                    else:
                        # Fallback: replace first alphabetic character in window
                        for i in range(start, min(end, len(result))):
                            if result[i].isalpha() and i not in replaced_positions:
                                # PRE-VALIDATION: Check if removing this character would create issues
                                current_text = ''.join(result)
                                if self._would_create_issues_if_removed(current_text, i, filtered_word, collapse_mapping):
                                    print(f"[OPTIMIZER] Iteration {iteration}: SKIPPING pos {i} (fallback) - would create issues when stripped")
                                    continue  # Try next character in window
                                else:
                                    old_char = result[i]
                                    result[i] = self._convert_char(result[i], style)
                                    replaced_positions.add(i)
                                    made_changes = True
                                    print(f"[OPTIMIZER] Iteration {iteration}: sliding window at pos {i}: '{old_char}' → '{result[i]}'")
                                    break
                
                elif r.detection_type.name == 'EMBEDDING':
                    filtered_word = r.filtered_word
                    full_word = r.full_word if r.full_word else filtered_word
                    
                    # CRITICAL: Use match_char_end from Aho-Corasick to find the EXACT occurrence
                    # in the CURRENT text state (which may be partially transformed)
                    current_text = ''.join(result)
                    current_lower = current_text.lower()
                    
                    if r.match_char_end is not None:
                        # Calculate where the filtered word starts based on end position
                        filtered_lower = filtered_word.lower()
                        match_start = r.match_char_end - len(filtered_lower) + 1
                        
                        # Find the full word that contains this match
                        # Walk backwards to find word start
                        word_start = match_start
                        while word_start > 0 and current_text[word_start - 1].isalnum():
                            word_start -= 1
                        
                        # Calculate offset of filtered word within full word
                        offset_in_word = match_start - word_start
                    else:
                        # Fallback: use old method
                        word_start = current_lower.find(full_word.lower())
                        offset_in_word = full_word.lower().find(filtered_word.lower())
                    
                    if word_start >= 0 and offset_in_word >= 0:
                        # Try each character in the filtered word
                        for i in range(len(filtered_word)):
                            char_pos = word_start + offset_in_word + i
                            
                            # Skip if already replaced or not alphanumeric
                            if char_pos >= len(result) or not result[char_pos].isalnum() or char_pos in replaced_positions:
                                continue
                            
                            old_char = result[char_pos]
                            
                            # TRANSFORMATION PRIORITY: Special char > Leet > Fancy
                            if self.enable_special_char:
                                # Override: Use special character interspacing
                                new_char = self.special_char.get_char()
                                transform_type = 'special'
                            elif self.enable_leet and old_char in self.leet.mapping:
                                # Leet-speak available for this character (cheap: 1 byte)
                                new_char = self.leet.mapping[old_char]
                                transform_type = 'leet'
                            else:
                                # Fallback: Fancy Unicode (expensive: 4 bytes)
                                new_char = self._convert_char(old_char, style)
                                transform_type = 'fancy'
                            
                            # Apply transformation temporarily
                            result[char_pos] = new_char
                            replaced_positions.add(char_pos)
                            
                            # VALIDATION: Test if this helps
                            test_text = ''.join(result)
                            
                            # Simulate game behavior: strip fancy unicode, keep leet
                            stripped_test = self._strip_fancy_unicode(test_text)
                            
                            # Check against filter (CRITICAL: pass collapse_mapping!)
                            test_detection = self.detector.detect_all(stripped_test, collapse_mapping)
                            
                            # Check if we're clean now
                            if test_detection['clean']:
                                # Success! Fully clean
                                print(f"[OPTIMIZER] Iteration {iteration}: {transform_type.upper()} at pos {char_pos} ('{old_char}'->'{new_char}') - CLEAN!")
                                made_changes = True
                                break  # Done with this detection
                            
                            # Count occurrences of THIS specific filtered word (handles multi-occurrence)
                            original_word_count = sum(
                                1 for det in detection['flagged'] 
                                if det.filtered_word.lower() == filtered_word.lower()
                            )
                            new_word_count = sum(
                                1 for det in test_detection['flagged'] 
                                if det.filtered_word.lower() == filtered_word.lower()
                            )
                            
                            # Also check total issue count
                            current_issue_count = len(test_detection['flagged'])
                            original_issue_count = len(detection['flagged'])
                            
                            # RELAXED VALIDATION in iteration loop too
                            words_fixed = original_word_count - new_word_count
                            max_acceptable_increase = words_fixed * 2
                            total_increase = current_issue_count - original_issue_count
                            
                            if new_word_count < original_word_count and total_increase <= max_acceptable_increase:
                                # Made progress on THIS word, total increase acceptable
                                made_changes = True
                                print(f"[OPTIMIZER] Iteration {iteration}: {transform_type.upper()} at pos {char_pos} ('{old_char}'->'{new_char}') - progress ({original_word_count}->{new_word_count} '{filtered_word}', total: {original_issue_count}->{current_issue_count}), KEPT")
                                detection = test_detection
                            elif current_issue_count < original_issue_count:
                                # Didn't help THIS word but reduced total issues, keep it
                                made_changes = True
                                print(f"[OPTIMIZER] Iteration {iteration}: {transform_type.upper()} at pos {char_pos} ('{old_char}'->'{new_char}') - progress (total: {original_issue_count}->{current_issue_count} issues), KEPT")
                                detection = test_detection
                            else:
                                # No progress OR created new issues - try fancy unicode fallback if this was leet-speak
                                if transform_type == 'leet' and self.enable_unicode and not self.enable_special_char:
                                    # Leet failed, try fancy unicode as fallback
                                    fancy_char = self._convert_char(old_char, style)
                                    result[char_pos] = fancy_char
                                    
                                    # Validate fancy unicode
                                    fancy_test_text = ''.join(result)
                                    fancy_stripped = self._strip_fancy_unicode(fancy_test_text)
                                    fancy_detection = self.detector.detect_all(fancy_stripped, collapse_mapping)
                                    
                                    if fancy_detection['clean']:
                                        # Fancy unicode succeeded!
                                        made_changes = True
                                        print(f"[OPTIMIZER] Iteration {iteration}: FANCY at pos {char_pos} ('{old_char}'->'{fancy_char}') - CLEAN (leet fallback)!")
                                        break
                                    
                                    # Check if fancy made progress
                                    fancy_word_count = sum(
                                        1 for det in fancy_detection['flagged']
                                        if det.filtered_word.lower() == filtered_word.lower()
                                    )
                                    fancy_issue_count = len(fancy_detection['flagged'])
                                    
                                    # RELAXED VALIDATION for fancy fallback in iteration
                                    fancy_words_fixed = original_word_count - fancy_word_count
                                    max_acceptable_fancy_increase = fancy_words_fixed * 2
                                    fancy_total_increase = fancy_issue_count - original_issue_count
                                    
                                    if fancy_word_count < original_word_count and fancy_total_increase <= max_acceptable_fancy_increase:
                                        # Fancy made progress on THIS word, total increase acceptable
                                        made_changes = True
                                        print(f"[OPTIMIZER] Iteration {iteration}: FANCY at pos {char_pos} ('{old_char}'->'{fancy_char}') - progress ({original_word_count}->{fancy_word_count} '{filtered_word}', total: {original_issue_count}->{fancy_issue_count}), KEPT (leet fallback)")
                                        detection = fancy_detection
                                    elif fancy_issue_count < original_issue_count:
                                        # Fancy reduced total issues
                                        made_changes = True
                                        print(f"[OPTIMIZER] Iteration {iteration}: FANCY at pos {char_pos} ('{old_char}'->'{fancy_char}') - progress (total: {original_issue_count}->{fancy_issue_count} issues), KEPT (leet fallback)")
                                        detection = fancy_detection
                                    else:
                                        # Both leet and fancy failed - REVERT completely
                                        result[char_pos] = old_char
                                        replaced_positions.remove(char_pos)
                                        print(f"[OPTIMIZER] Iteration {iteration}: LEET+FANCY at pos {char_pos} ('{old_char}') - no progress (both failed), REVERTED")
                                else:
                                    # No fallback available - REVERT
                                    result[char_pos] = old_char
                                    replaced_positions.remove(char_pos)
                                    print(f"[OPTIMIZER] Iteration {iteration}: {transform_type.upper()} at pos {char_pos} ('{old_char}'->'{new_char}') - no progress ({original_word_count}={new_word_count} '{filtered_word}', total={current_issue_count}), REVERTED")
                
                elif r.detection_type.name == 'STANDALONE':
                    word_to_replace = r.full_word if r.full_word else r.filtered_word
                    pattern = r'\b' + re.escape(word_to_replace) + r'\b'
                    
                    def replace_first_letter(match):
                        matched_word = match.group(0)
                        if len(matched_word) > 0:
                            first_char_converted = self._convert_char(matched_word[0], style)
                            return first_char_converted + matched_word[1:]
                        return matched_word
                    
                    temp_text = ''.join(result)
                    new_text = re.sub(pattern, replace_first_letter, temp_text, count=1, flags=re.IGNORECASE)
                    if new_text != temp_text:
                        result = list(new_text)
                        made_changes = True
                        print(f"[OPTIMIZER] Iteration {iteration}: replaced first letter of '{word_to_replace}'")
            
            if not made_changes:
                print(f"[OPTIMIZER] No more changes possible after {iteration} iteration(s)")
                break
            
            optimized = ''.join(result)
            iteration += 1
        
        # Final detection check
        final_detection = self.detector.detect_all(optimized)
        
        # Enforce limits (byte + character) - get send portion only
        # Note: paste_part handled at higher level in mode_router
        send_part, paste_part, stages_applied = self.enforce_limits(optimized, links, stages_applied)
        
        # Use send_part as the optimized result
        # If there's a paste_part, it will be handled by the calling code
        optimized = send_part
        
        # Calculate partial optimization flag
        # Show suggestion if text was optimized even if not fully clean
        original_detection = self.detector.detect_all(result_original)
        original_flagged_count = len(original_detection['flagged'])
        current_flagged_count = len(final_detection['flagged'])
        
        has_partial_optimization = (
            stages_applied and 
            optimized.lower() != result_original.lower() and
            current_flagged_count < original_flagged_count
        )
        
        # DEBUG LOGGING
        print(f"[OPTIMIZER] Partial optimization check (position-based):")
        print(f"  stages_applied: {stages_applied}")
        print(f"  text_changed: {optimized.lower() != result_original.lower()}")
        print(f"  original_flagged_count: {original_flagged_count}")
        print(f"  current_flagged_count: {current_flagged_count}")
        print(f"  flagged_reduced: {current_flagged_count < original_flagged_count}")
        print(f"  has_partial_optimization: {has_partial_optimization}")
        
        return OptimizationResult(
            original=result_original,
            optimized=optimized,
            stages_applied=stages_applied,
            byte_change=len(optimized.encode('utf-8')) - len(result_original.encode('utf-8')),
            success=final_detection['clean'],
            flagged_words=filtered_words,
            explanation=f"Optimized using position-based replacement ({iteration} iteration(s))" if final_detection['clean'] else "Could not fully optimize",
            links_modified=links_modified,
            paste_part=paste_part,
            partial_optimization=has_partial_optimization
        )
    
    def optimize_numeral_word(self, text: str, filtered_word: str, collapse_mapping: Optional[List[Tuple[int, int, str]]] = None, protect_urls: bool = True) -> Optional[str]:
        """
        Optimize filtered words that are numbers or start with numbers
        
        Respects URL protection:
        - If protect_urls=True: Only optimize numerals NOT in URLs
        - If protect_urls=False: Optimize ALL numerals (including in URLs)
        
        Strategies:
        1. Pure numerals (e.g., "420") → Insert Hangul Jungseong Araea (ᆞ) separator
           - "420" → "4ᆞ20" or "42ᆞ0"
           - This character is NOT stripped by game filters
        
        2. Starts with numeral (e.g., "2g1c", "2b") → Replace first LETTER with fancy unicode
           - "2🄶1c" → "2🄶1c" (replace 'g')
           - "2b" → "2🄱" (replace 'b')
        
        Args:
            text: Full text
            filtered_word: Numeral filtered word to optimize
            collapse_mapping: Optional collapse mapping for whitelist override detection
            protect_urls: If True, don't optimize numerals inside URLs
            
        Returns:
            Optimized text or None if no safe replacements possible
        """
        import re
        
        filtered_lower = filtered_word.lower()
        text_lower = text.lower()
        
        # Check if word exists in text
        if filtered_lower not in text_lower:
            return None
        
        word_len = len(filtered_word)
        if word_len < 2:
            return None  # Can't split single character
        
        # Find all URLs in text if protection is enabled
        url_ranges = []
        if protect_urls:
            url_pattern = r'http[s]?://[^\s]+'
            for url_match in re.finditer(url_pattern, text, re.IGNORECASE):
                url_ranges.append((url_match.start(), url_match.end()))
        
        def is_in_url(pos: int, length: int) -> bool:
            """Check if position range overlaps with any URL"""
            if not url_ranges:
                return False
            for url_start, url_end in url_ranges:
                # Check if this occurrence overlaps with URL
                if not (pos + length <= url_start or pos >= url_end):
                    return True
            return False
        
        # Strategy 1: Pure numerals - use Hangul separator
        if filtered_word.isdigit():
            # Insert Hangul Jungseong Araea (ᆞ) at middle position
            mid_pos = word_len // 2
            optimized_word = filtered_word[:mid_pos] + 'ᆞ' + filtered_word[mid_pos:]
            
            # Find all occurrences and replace only safe ones
            pattern = r'\b' + re.escape(filtered_word) + r'\b'
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            
            if not matches:
                # No word-boundary matches, try without boundaries (for URLs, etc.)
                pattern = re.escape(filtered_word)
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
            
            if not matches:
                return None
            
            # Replace occurrences from right to left (to preserve positions)
            optimized_text = text
            replaced_count = 0
            skipped_count = 0
            
            for match in reversed(matches):
                pos = match.start()
                if is_in_url(pos, word_len):
                    # This occurrence is in a URL
                    if protect_urls:
                        skipped_count += 1
                        continue  # Skip this occurrence
                    # else: protect_urls=False, so optimize it anyway
                
                # Replace this occurrence
                optimized_text = optimized_text[:pos] + optimized_word + optimized_text[pos + word_len:]
                replaced_count += 1
            
            if replaced_count == 0:
                print(f"[OPTIMIZER] Pure numeral '{filtered_word}': All {len(matches)} occurrence(s) in URLs (protected)")
                return None
            
            # Check if THIS SPECIFIC numeral word is no longer detected
            re_detection = self.detector.detect_all(optimized_text, collapse_mapping)
            numeral_still_detected = any(r.filtered_word == filtered_word for r in re_detection['flagged'])
            
            # Accept as success if:
            # 1. Not detected anymore (full success), OR
            # 2. Still detected BUT we skipped URLs (partial success - URLs still have it)
            if not numeral_still_detected:
                # Full success - word no longer detected anywhere
                if skipped_count > 0:
                    print(f"[OPTIMIZER] Pure numeral '{filtered_word}' optimized: {replaced_count} occurrence(s), {skipped_count} in URLs (protected)")
                else:
                    print(f"[OPTIMIZER] Pure numeral '{filtered_word}' optimized: {replaced_count} occurrence(s)")
                return optimized_text
            elif skipped_count > 0:
                # Partial success - optimized non-URL occurrences, URL occurrences still detected (expected)
                print(f"[OPTIMIZER] Pure numeral '{filtered_word}': Optimized {replaced_count} occurrence(s), {skipped_count} in URLs remain (partial success)")
                return optimized_text
            else:
                # Failed - no URLs were skipped, but word still detected after optimization
                print(f"[OPTIMIZER] Pure numeral '{filtered_word}' optimization failed - still detected after replacement")
                return None
        
        # Strategy 2: Starts with numeral - replace first letter
        if filtered_word[0].isdigit():
            # Find first letter in the word
            first_letter_idx = None
            for i, char in enumerate(filtered_word):
                if char.isalpha():
                    first_letter_idx = i
                    break
            
            if first_letter_idx is None:
                return None  # No letters to replace
            
            # Find all occurrences
            pattern = re.escape(filtered_word)
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            
            if not matches:
                return None
            
            # Replace occurrences from right to left
            optimized_text = text
            replaced_count = 0
            skipped_count = 0
            
            style = self.config.get('optimization', {}).get('fancy_text_style', 'squared')
            
            for match in reversed(matches):
                pos = match.start()
                matched_word = match.group(0)
                
                if is_in_url(pos, word_len):
                    if protect_urls:
                        skipped_count += 1
                        continue
                
                # Replace first letter with fancy unicode
                fancy_char = self.fancy.convert(matched_word[first_letter_idx], style)
                optimized_word = matched_word[:first_letter_idx] + fancy_char + matched_word[first_letter_idx+1:]
                
                # Replace this occurrence
                optimized_text = optimized_text[:pos] + optimized_word + optimized_text[pos + word_len:]
                replaced_count += 1
            
            if replaced_count == 0:
                print(f"[OPTIMIZER] Numeral-starting word '{filtered_word}': All {len(matches)} occurrence(s) in URLs (protected)")
                return None
            
            # Check if THIS SPECIFIC numeral word is no longer detected
            re_detection = self.detector.detect_all(optimized_text, collapse_mapping)
            numeral_still_detected = any(r.filtered_word == filtered_word for r in re_detection['flagged'])
            
            # Accept as success if:
            # 1. Not detected anymore (full success), OR
            # 2. Still detected BUT we skipped URLs (partial success - URLs still have it)
            if not numeral_still_detected:
                # Full success
                if skipped_count > 0:
                    print(f"[OPTIMIZER] Numeral-starting word '{filtered_word}' optimized: {replaced_count} occurrence(s), {skipped_count} in URLs (protected)")
                else:
                    print(f"[OPTIMIZER] Numeral-starting word '{filtered_word}' optimized: {replaced_count} occurrence(s)")
                return optimized_text
            elif skipped_count > 0:
                # Partial success - optimized non-URL occurrences, URL occurrences remain
                print(f"[OPTIMIZER] Numeral-starting word '{filtered_word}': Optimized {replaced_count} occurrence(s), {skipped_count} in URLs remain (partial success)")
                return optimized_text
            else:
                # Failed - no URLs skipped, but still detected
                print(f"[OPTIMIZER] Numeral-starting word '{filtered_word}' optimization failed - still detected after replacement")
                return None
        
        return None
    
    def optimize_numeral_words_in_text(self, text: str, numeral_words: List[str]) -> tuple[str, bool]:
        """
        Optimize numeral filtered words in text, including in links
        
        This runs BEFORE link protection to ensure numeral words in links
        (like "discord.gg/info420") are also optimized.
        
        Args:
            text: Text to optimize
            numeral_words: List of numeral filtered words
            
        Returns:
            Tuple of (optimized_text, links_modified)
        """
        optimized = text
        links_modified = False
        
        # Check if any numeral word appears in a URL
        url_pattern = r'http[s]?://\S+'
        urls_in_text = re.findall(url_pattern, optimized)
        
        for numeral_word in numeral_words:
            # Check if this numeral word is in any URL
            in_link = any(numeral_word.lower() in url.lower() for url in urls_in_text)
            
            # Try to optimize it
            result = self.optimize_numeral_word(optimized, numeral_word)
            if result:
                optimized = result
                if in_link:
                    links_modified = True
                    print(f"[OPTIMIZER] Numeral word '{numeral_word}' in link was optimized")
        
        return optimized, links_modified
    
    def enforce_limits(self, text: str, links: List = None, stages_applied: List = None) -> Tuple[str, str, List[str]]:
        """
        Enforce byte limit AND character limit through shorthand compression and splitting
        
        Returns tuple for multi-part message support:
        - If message fits: (full_message, "", stages)
        - If message too long: (send_portion, paste_portion, stages)
        
        Args:
            text: Text to enforce limits on
            links: Protected links (to restore before checking)
            stages_applied: List to append stages to
            
        Returns:
            Tuple of (send_portion, paste_portion, stages_applied)
            send_portion: Text to send (under limits)
            paste_portion: Text to paste for next iteration (empty if all fits)
            stages_applied: List of applied stages
        """
        if stages_applied is None:
            stages_applied = []
        
        # Restore links before checking (links count towards limits)
        working_text = text
        if links:
            working_text = self._restore_links(text, links)
        
        byte_size = len(working_text.encode('utf-8'))
        char_count = len(working_text)
        
        # Get limits from config
        byte_limit = self.byte_limit if self.byte_limit else float('inf')
        char_limit = self.config.get('character_limit', 80)
        
        print(f"[OPTIMIZER] Size: {char_count} chars, {byte_size} bytes (limits: {char_limit} chars, {byte_limit} bytes)")
        
        # Check if under both limits
        if byte_size <= byte_limit and char_count <= char_limit:
            return working_text, "", stages_applied
        
        # Over limit - try shorthand compression
        if self.enable_shorthand:
            if byte_size > byte_limit:
                print(f"[OPTIMIZER] Over byte limit ({byte_size}/{byte_limit}), applying shorthand compression...")
            elif char_count > char_limit:
                print(f"[OPTIMIZER] Over character limit ({char_count}/{char_limit}), applying shorthand compression...")
            
            compressed = self.shorthand.compress(working_text)
            compressed_size = len(compressed.encode('utf-8'))
            compressed_chars = len(compressed)
            
            # Check if compression fixed both limits
            if compressed_size <= byte_limit and compressed_chars <= char_limit:
                print(f"[OPTIMIZER] Shorthand compression successful: {compressed_chars} chars, {compressed_size} bytes")
                stages_applied.append('shorthand')
                return compressed, "", stages_applied
            
            print(f"[OPTIMIZER] Shorthand compression not enough: {compressed_chars} chars, {compressed_size} bytes, splitting...")
            working_text = compressed
            stages_applied.append('shorthand')
        
        # Still over limits - SPLIT at word boundary
        print(f"[OPTIMIZER] Splitting message at word boundary...")
        send_part, paste_part = self._split_at_limit(working_text, char_limit, byte_limit)
        
        if paste_part:
            stages_applied.append('multipart_split')
            send_chars = len(send_part)
            send_bytes = len(send_part.encode('utf-8'))
            paste_chars = len(paste_part)
            paste_bytes = len(paste_part.encode('utf-8'))
            print(f"[OPTIMIZER] Split → Send: {send_chars} chars, {send_bytes} bytes | Remainder: {paste_chars} chars, {paste_bytes} bytes")
        
        return send_part, paste_part, stages_applied
    
    def _split_at_limit(self, text: str, char_limit: int, byte_limit: int) -> Tuple[str, str]:
        """
        Split text at word boundary before limits
        
        Finds the longest prefix that fits within BOTH limits,
        breaking at word boundaries for readability.
        
        Args:
            text: Text to split
            char_limit: Maximum characters
            byte_limit: Maximum bytes
            
        Returns:
            Tuple of (send_part, paste_part)
            send_part: Portion that fits within limits
            paste_part: Remainder for next iteration (empty if all fits)
        """
        words = text.split()
        send_words = []
        send_text = ""
        
        for word in words:
            # Try adding next word
            test_text = ' '.join(send_words + [word]) if send_words else word
            test_chars = len(test_text)
            test_bytes = len(test_text.encode('utf-8'))
            
            # Check if still under BOTH limits
            if test_chars <= char_limit and test_bytes <= byte_limit:
                send_words.append(word)
                send_text = test_text
            else:
                # Would exceed limits, stop here
                break
        
        # Get remainder
        remaining_words = words[len(send_words):]
        paste_text = ' '.join(remaining_words) if remaining_words else ""
        
        return send_text, paste_text
    
    def optimize(self, text: str, collapse_mapping: Optional[List[Tuple[int, int, str]]] = None, max_attempts: int = 5) -> OptimizationResult:
        """
        Optimize message through multiple stages
        
        Note: Text should already be collapsed (spaced patterns pre-processed)
        
        Args:
            text: Message to optimize (collapsed text)
            collapse_mapping: Optional mapping from collapse operation (preserves whitelist override context)
            max_attempts: Maximum optimization attempts
        
        Returns:
            OptimizationResult with optimization details
        """
        original = text
        current = text
        stages_applied = []
        links_modified = False
        
        # PRE-STAGE: Detect and optimize numeral words BEFORE link protection
        # Skip if special char interspacing is enabled (will handle numerals instead)
        if not self.enable_special_char:
            pre_detection = self.detector.detect_all(current, collapse_mapping)
            filtered_words_pre = [r.filtered_word for r in pre_detection['flagged']]
            numeral_words = [w for w in filtered_words_pre if w and (w[0].isdigit() or w.isdigit())]
            
            if numeral_words:
                print(f"[OPTIMIZER] Found numeral filtered words: {numeral_words}")
                for numeral_word in numeral_words:
                    # Check if this numeral word appears in a link
                    url_pattern = r'http[s]?://\S+'
                    urls_in_text = re.findall(url_pattern, current)
                    in_link = any(numeral_word.lower() in url.lower() for url in urls_in_text)
                    
                    result = self.optimize_numeral_word(current, numeral_word, collapse_mapping=collapse_mapping, protect_urls=self.enable_link_protection)
                    if result:
                        current = result
                        stages_applied.append('numeral_delimiter')
                        if in_link:
                            links_modified = True
                            print(f"[OPTIMIZER] Numeral word '{numeral_word}' in link optimized")
                    elif in_link and self.enable_link_protection:
                        # Numeral is in a link and couldn't be optimized (protected)
                        links_modified = True
                        print(f"[OPTIMIZER] Numeral word '{numeral_word}' in link - PROTECTED (can't optimize)")
        
        # Stage 1: Link Protection (extract links AFTER numeral optimization)
        links = []
        if self.enable_link_protection:
            current, links = self._protect_links(current)
            if links:
                stages_applied.append('link_protection')
        
        # Detect issues - pass collapse_mapping to preserve whitelist override context
        detection = self.detector.detect_all(current, collapse_mapping)
        print(f"[DEBUG] Initial detection types: {[(r.filtered_word, r.detection_type.name) for r in detection['flagged']]}")

        
        if detection['clean']:
            # No optimization needed, but still enforce limits
            send_part, paste_part, stages_applied = self.enforce_limits(current, links, stages_applied)
            
            # Use send_part as the optimized result
            current = send_part
            
            return OptimizationResult(
                original=original,
                optimized=current,
                stages_applied=stages_applied,
                byte_change=len(current.encode('utf-8')) - len(original.encode('utf-8')),
                success=True,
                flagged_words=[],
                explanation="Message is clean, no optimization needed",
                links_modified=links_modified,
                paste_part=paste_part
            )
        
        # Get flagged words - USE FILTERED_WORD ONLY (not full_word)
        # We want to optimize the filtered substring, not the entire word
        flagged_words = []
        seen = set()
        for r in detection['flagged']:
            # CRITICAL: Use filtered_word, not full_word
            # "Scunthorpe" contains "cunt" -> optimize "cunt", not "Scunthorpe"
            word_to_optimize = r.filtered_word
            
            # Avoid duplicates
            if word_to_optimize.lower() not in seen:
                flagged_words.append(word_to_optimize)
                seen.add(word_to_optimize.lower())

        # Sort by length descending
        flagged_words = sorted(flagged_words, key=len, reverse=True)

        # Also store the filtered words for reference
        filtered_words = [r.filtered_word for r in detection['flagged']]
        
        # Special Character Interspacing (if enabled, used INSTEAD of leet/fancy)
        if self.enable_special_char:
            print(f"[OPTIMIZER] Applying special character interspacing (iterative)")
            
            # Iterative optimization (like position-based)
            max_iterations = 10
            iteration = 0
            optimized_text = current
            previous_text = None  # Track text changes to detect infinite loops
            
            while iteration < max_iterations:
                # Text-change detection: Stop if no progress
                if previous_text is not None and optimized_text == previous_text:
                    print(f"[OPTIMIZER] No text changes detected - stopping at iteration {iteration}")
                    break
                previous_text = optimized_text
                
                # Detect on current text
                detection_iter = self.detector.detect_all(optimized_text, collapse_mapping)
                
                if detection_iter['clean']:
                    print(f"[OPTIMIZER] Special char interspacing succeeded after {iteration} iteration(s)")
                    break
                
                print(f"[OPTIMIZER] Iteration {iteration + 1}: {len(detection_iter['flagged'])} issue(s) detected")
                
                # DEBUG: Show what detections we have
                print(f"[DEBUG] Detections: {[(r.filtered_word, r.detection_type.name, r.word_position) for r in detection_iter['flagged']]}")
                
                # CRITICAL: Deduplicate by BOTH word occurrence AND insertion position
                # This prevents:
                # 1. Same word detected multiple times (EMBEDDING + STANDALONE)
                # 2. Multiple filtered words in same word targeting same position (fuc + fuck both at pos 1)
                unique_detections = []
                seen_word_positions = set()  # Track (filtered_word, word_position)
                seen_insertion_positions = set()  # Track actual insertion positions
                
                # Check if we have ANY STANDALONE or EMBEDDING detections in THIS iteration
                # Skip STRIPPED_WINDOW in this iteration only (not persistent across iterations)
                has_direct_optimization = any(
                    r.detection_type.name in ['STANDALONE', 'EMBEDDING']
                    for r in detection_iter['flagged']
                )
                
                for result in detection_iter['flagged']:
                    # Skip STRIPPED_WINDOW if we have direct optimizations THIS iteration
                    # This prevents duplicate handling of the same word in the same iteration
                    # But allows pure sliding windows in future iterations
                    if result.detection_type.name == 'STRIPPED_WINDOW':
                        if has_direct_optimization:
                            print(f"[DEBUG] Skipping STRIPPED_WINDOW for '{result.filtered_word}' - direct optimizations in this iteration")
                            continue
                    
                    # Check 1: Skip duplicate word occurrences
                    word_key = (result.filtered_word.lower(), result.word_position)
                    if word_key in seen_word_positions:
                        print(f"[DEBUG] Skipping duplicate word occurrence: {result.filtered_word} at word_position {result.word_position}")
                        continue
                    
                    # Check 2: Calculate insertion position and skip if already used
                    insertion_pos = None
                    if result.detection_type.name == 'STANDALONE':
                        # Find first occurrence of standalone word
                        pattern = re.compile(r'\b' + re.escape(result.filtered_word) + r'\b', re.IGNORECASE)
                        matches = list(pattern.finditer(optimized_text))
                        if matches:
                            insertion_pos = matches[0].start() + 1
                    elif result.detection_type.name == 'EMBEDDING' and result.full_word:
                        # Find where filtered word appears in full word
                        pattern = re.compile(re.escape(result.full_word), re.IGNORECASE)
                        matches = list(pattern.finditer(optimized_text))
                        if matches:
                            word_start = matches[0].start()
                            full_word_lower = result.full_word.lower()
                            filtered_pos = full_word_lower.find(result.filtered_word.lower())
                            if filtered_pos >= 0:
                                insertion_pos = word_start + filtered_pos + 1
                    elif result.detection_type.name == 'STRIPPED_WINDOW' and result.window_range:
                        # Calculate position for sliding window
                        # Use window start position + 1 (matches external method behavior)
                        start, end = result.window_range
                        insertion_pos = start + 1
                    
                    # Skip if this insertion position is already used
                    if insertion_pos is not None and insertion_pos in seen_insertion_positions:
                        print(f"[DEBUG] Skipping duplicate insertion position: {result.filtered_word} at text position {insertion_pos}")
                        continue
                    
                    # Add to unique detections
                    seen_word_positions.add(word_key)
                    if insertion_pos is not None:
                        seen_insertion_positions.add(insertion_pos)
                    unique_detections.append(result)
                
                print(f"[DEBUG] After dedup: {len(unique_detections)} unique occurrences")
                
                # Apply interspacing
                optimized_text = self.special_char.apply_to_text_with_positions(optimized_text, unique_detections)
                
                iteration += 1
            
            if iteration >= max_iterations:
                print(f"[OPTIMIZER] WARNING: Max iterations ({max_iterations}) reached, may still have issues")
            
            # Restore links
            if links:
                optimized_text = self._restore_links(optimized_text, links)
            
            # Final detection check
            final_detection = self.detector.detect_all(optimized_text, collapse_mapping)
            
            # Check if remaining issues are only in protected links (only if link protection enabled)
            issues_outside_links = []
            if self.enable_link_protection and links and not final_detection['clean']:
                # Get positions of all links in text
                link_ranges = []
                for placeholder, url in links:
                    pos = optimized_text.find(url)
                    if pos >= 0:
                        link_ranges.append((pos, pos + len(url)))
                
                # Check each flagged word
                for result in final_detection['flagged']:
                    # Find where this word appears in text
                    word_lower = result.filtered_word.lower()
                    text_lower = optimized_text.lower()
                    word_pos = text_lower.find(word_lower)
                    
                    if word_pos >= 0:
                        # Check if this position is inside any link
                        in_link = any(start <= word_pos < end for start, end in link_ranges)
                        if not in_link:
                            issues_outside_links.append(result)
                
                # If all issues are in links, treat as success
                if not issues_outside_links:
                    print(f"[OPTIMIZER] All remaining issues are in protected links - treating as success")
                    final_detection = {'clean': True, 'flagged': []}
            
            stages_applied.append('special_char_interspacing')
            
            # Enforce limits
            send_part, paste_part, stages_applied = self.enforce_limits(optimized_text, links, stages_applied)
            
            print(f"[OPTIMIZER] Special char interspacing applied: '{self.special_char.get_char()}'")
            
            return OptimizationResult(
                original=original,
                optimized=send_part,
                stages_applied=stages_applied,
                byte_change=len(send_part.encode('utf-8')) - len(original.encode('utf-8')),
                success=final_detection['clean'],
                flagged_words=flagged_words,
                explanation=f"Special character '{self.special_char.get_char()}' interspacing applied ({iteration} iteration(s))",
                links_modified=links_modified,
                paste_part=paste_part
            )
        
        # Stage 2: Try leet-speak FIRST (0 byte overhead, works for all detection types)
        if self.enable_leet:
            leet_result = self._apply_leet_speak(current, flagged_words)
            if leet_result:
                print(f"[DEBUG] Leet speak applied: '{leet_result}'")
                leet_detection = self.detector.detect_all(leet_result)
                print(f"[DEBUG] Leet detection result: clean={leet_detection['clean']}, flagged={[r.filtered_word for r in leet_detection['flagged']]}")
                if leet_detection['clean']:
                    current = leet_result
                    stages_applied.append('leet_speak')
                    
                    # Restore links and enforce limits
                    if links:
                        current = self._restore_links(current, links)
                    
                    # Enforce limits (may split)
                    send_part, paste_part, stages_applied = self.enforce_limits(current, [], stages_applied)
                    
                    return OptimizationResult(
                        original=original,
                        optimized=send_part,
                        stages_applied=stages_applied,
                        byte_change=len(send_part.encode('utf-8')) - len(original.encode('utf-8')),
                        success=True,
                        flagged_words=filtered_words,
                        explanation="Optimized using leet-speak",
                        links_modified=links_modified,
                        paste_part=paste_part
                    )
                else:
                    # Leet speak didn't make it clean, but use it as current for next stage
                    current = leet_result
                    stages_applied.append('leet_speak')
                    # Re-detect to get updated flagged words
                    detection = self.detector.detect_all(current)
                    filtered_words = [r.filtered_word for r in detection['flagged']]
                    flagged_words = []
                    seen = set()
                    for r in detection['flagged']:
                        word_to_optimize = r.filtered_word  # ✓ Use filtered_word, not full_word
                        if word_to_optimize.lower() not in seen:
                            flagged_words.append(word_to_optimize)
                            seen.add(word_to_optimize.lower())
                    flagged_words = sorted(flagged_words, key=len, reverse=True)

        # Check if we have any detections that need position-based optimization
        # Use the UPDATED detection (after leet speak)
        needs_position_optimization = any(
            r.detection_type.name in ['STRIPPED_WINDOW', 'EMBEDDING'] for r in detection['flagged']
        )

        if needs_position_optimization:
            # Already re-detected above after leet speak
            if detection['clean']:
                # Leet speak fixed it!
                if links:
                    current = self._restore_links(current, links)
                send_part, paste_part, stages_applied = self.enforce_limits(current, [], stages_applied)
                return OptimizationResult(
                    original=original,
                    optimized=send_part,
                    stages_applied=stages_applied,
                    byte_change=len(send_part.encode('utf-8')) - len(original.encode('utf-8')),
                    success=True,
                    flagged_words=filtered_words,
                    explanation="Optimized using leet-speak",
                    links_modified=links_modified,
                    paste_part=paste_part
                )
            
            # Still has issues - use position-based optimization
            # Update filtered words from new detection
            filtered_words = [r.filtered_word for r in detection['flagged']]
            return self._optimize_with_positions(current, detection, stages_applied, links, filtered_words, collapse_mapping=collapse_mapping, links_modified=links_modified, original_text=original)
        
        # Stage 3: Leet-speak already tried above, skip to fancy unicode
        if self.enable_unicode:
            unicode_result = self._apply_fancy_unicode(current, flagged_words)
            if unicode_result and self.detector.detect_all(unicode_result)['clean']:
                current = unicode_result
                stages_applied.append('fancy_unicode')
                
                # Restore links and enforce limits
                if links:
                    current = self._restore_links(current, links)
                
                # Enforce limits (may split)
                send_part, paste_part, stages_applied = self.enforce_limits(current, [], stages_applied)
                
                return OptimizationResult(
                    original=original,
                    optimized=send_part,
                    stages_applied=stages_applied,
                    byte_change=len(send_part.encode('utf-8')) - len(original.encode('utf-8')),
                    success=True,
                    flagged_words=filtered_words,
                    explanation="Optimized using fancy unicode",
                    links_modified=links_modified,
                    paste_part=paste_part
                )
        
        # Stage 4: Shorthand (if message too long)
        if self.enable_shorthand and self.max_length and len(current) > self.max_length:
            shorthand_result = self.shorthand.compress(current)
            current = shorthand_result
            stages_applied.append('shorthand')
        
        # Stage 5: Truncation (last resort)
        if self.max_length and len(current) > self.max_length:
            current = self._truncate(current, flagged_words)
            stages_applied.append('truncation')
        
        # Final check
        final_detection = self.detector.detect_all(current, collapse_mapping)
        
        # Restore links
        if links:
            current = self._restore_links(current, links)
        
        # Enforce limits (may split even if optimization failed)
        send_part, paste_part, stages_applied = self.enforce_limits(current, [], stages_applied)
        
        # Determine if we should show partial optimization
        # Even if not fully clean, show optimization if:
        # 1. Some stages were applied, AND
        # 2. The optimized text is different from original, AND
        # 3. Flagged words reduced
        original_detection = self.detector.detect_all(original, collapse_mapping)
        original_flagged_count = len(original_detection['flagged'])
        current_flagged_count = len(flagged_words)
        
        has_partial_optimization = (
            stages_applied and 
            send_part.lower() != original.lower() and
            current_flagged_count < original_flagged_count
        )
        
        # DEBUG LOGGING
        print(f"[OPTIMIZER] Partial optimization check (main path):")
        print(f"  stages_applied: {stages_applied}")
        print(f"  text_changed: {send_part.lower() != original.lower()}")
        print(f"  original_flagged_count: {original_flagged_count}")
        print(f"  current_flagged_count: {current_flagged_count}")
        print(f"  flagged_reduced: {current_flagged_count < original_flagged_count}")
        print(f"  has_partial_optimization: {has_partial_optimization}")
        
        return OptimizationResult(
            original=original,
            optimized=send_part,
            stages_applied=stages_applied,
            byte_change=len(send_part.encode('utf-8')) - len(original.encode('utf-8')),
            success=final_detection['clean'],
            flagged_words=flagged_words,
            explanation="Applied multiple optimization stages" if stages_applied else "Could not optimize",
            links_modified=links_modified,
            paste_part=paste_part,
            partial_optimization=has_partial_optimization  # New flag
        )
    
    def _protect_links(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Extract and protect URLs from modification
        
        Args:
            text: Text containing URLs
        
        Returns:
            tuple: (text_with_placeholders, [(placeholder, url)])
        """
        links = []
        result = text
        
        # Find all URLs
        for i, match in enumerate(self.URL_PATTERN.finditer(text)):
            url = match.group(0)
            placeholder = f"__LINK_{i}__"
            links.append((placeholder, url))
            result = result.replace(url, placeholder, 1)
        
        return result, links
    
    def _restore_links(self, text: str, links: List[Tuple[str, str]]) -> str:
        """
        Restore protected URLs
        
        Args:
            text: Text with placeholders
            links: List of (placeholder, url) tuples
        
        Returns:
            str: Text with restored URLs
        """
        result = text
        for placeholder, url in links:
            result = result.replace(placeholder, url)
        return result
    
    def _apply_leet_speak(self, text: str, flagged_words: List[str]) -> Optional[str]:
        """
        Apply leet-speak minimally for maximum legibility
        
        Strategy: Convert only ONE letter per flagged word
        1. Try first letter - if it converts, stop there
        2. If first letter can't convert, scan forward to find next convertible letter
        
        This maintains readability while breaking filter detection.
        
        Examples:
            "anal" → "4nal" (first 'a' converts, done)
            "cunt" → "c**nt" ('c' can't convert, 'u' can, done)
            "fodi" → "f0di" ('f' can't convert, 'o' can, done)
        
        Args:
            text: Text to optimize
            flagged_words: List of flagged words (sorted by length desc)
        
        Returns:
            str: Optimized text, or None if failed
        """
        result = text
        
        for word in flagged_words:
            # Find word in text (case-insensitive)
            pattern = r'\b' + re.escape(word) + r'\b'
            
            # Replace with minimal leet-speak (one letter only)
            def replace_minimal_leet(match):
                matched_word = match.group(0)
                
                if len(matched_word) == 0:
                    return matched_word
                
                # Try first letter
                first_char_leet = self.leet.convert(matched_word[0])
                if first_char_leet != matched_word[0]:
                    # First letter can be converted - use it and stop
                    return first_char_leet + matched_word[1:]
                
                # First letter can't be converted - scan for next convertible letter
                for i in range(1, len(matched_word)):
                    char_leet = self.leet.convert(matched_word[i])
                    if char_leet != matched_word[i]:
                        # Found convertible letter - use it and stop
                        return matched_word[:i] + char_leet + matched_word[i+1:]
                
                # No letters in this word can be converted (no mappable vowels)
                return matched_word
            
            result = re.sub(pattern, replace_minimal_leet, result, flags=re.IGNORECASE)
        
        return result
    
    def _apply_fancy_unicode(self, text: str, flagged_words: List[str]) -> Optional[str]:
        """
        Apply fancy unicode to first letter of flagged words only
        
        Per spec: Minimize byte overhead by only substituting first letter
        Example: "fuck" → "🄵uck", "fucking" → "🄵ucking"
        
        Args:
            text: Text to optimize
            flagged_words: List of flagged words (sorted by length desc)
        
        Returns:
            str: Optimized text, or None if failed
        """
        result = text
        
        # Get fancy text style from config (default to 'squared')
        style = self.config.get('optimization', {}).get('fancy_text_style', 'squared')
        
        for word in flagged_words:
            # Find word in text (case-insensitive)
            pattern = r'\b' + re.escape(word) + r'\b'
            
            # Replace with fancy unicode first letter only
            def replace_first_letter(match):
                matched_word = match.group(0)
                if len(matched_word) > 0:
                    # Convert only the first letter
                    first_char_fancy = self.fancy.convert(matched_word[0], style)
                    return first_char_fancy + matched_word[1:]
                return matched_word
            
            result = re.sub(pattern, replace_first_letter, result, flags=re.IGNORECASE)
        
        return result
    
    def _truncate(self, text: str, flagged_words: List[str]) -> str:
        """
        Truncate message to fit length limit (last resort)
        
        Args:
            text: Text to truncate
            flagged_words: Words to potentially remove
        
        Returns:
            str: Truncated text
        """
        if not self.max_length:
            return text
        
        # Simple truncation for now
        if len(text) > self.max_length:
            return text[:self.max_length - 3] + "..."
        
        return text
    
    def get_optimization_preview(self, text: str) -> Dict:
        """
        Preview optimization options without applying
        
        Args:
            text: Text to preview
        
        Returns:
            dict: Preview of each optimization stage
        """
        detection = self.detector.detect_all(text)
        
        if detection['clean']:
            return {
                'status': 'clean',
                'message': 'No optimization needed',
                'options': []
            }
        
        flagged_words = [r.filtered_word for r in detection['flagged']]
        
        options = []
        
        # Preview leet-speak
        if self.enable_leet:
            leet_text = self._apply_leet_speak(text, flagged_words)
            if leet_text:
                options.append({
                    'stage': 'leet_speak',
                    'result': leet_text,
                    'byte_change': len(leet_text.encode('utf-8')) - len(text.encode('utf-8')),
                    'clean': self.detector.detect_all(leet_text)['clean']
                })
        
        # Preview fancy unicode
        if self.enable_unicode:
            unicode_text = self._apply_fancy_unicode(text, flagged_words)
            if unicode_text:
                options.append({
                    'stage': 'fancy_unicode',
                    'result': unicode_text,
                    'byte_change': len(unicode_text.encode('utf-8')) - len(text.encode('utf-8')),
                    'clean': self.detector.detect_all(unicode_text)['clean']
                })
        
        # Preview shorthand
        if self.enable_shorthand:
            shorthand_text = self.shorthand.compress(text)
            options.append({
                'stage': 'shorthand',
                'result': shorthand_text,
                'byte_change': len(shorthand_text.encode('utf-8')) - len(text.encode('utf-8')),
                'clean': self.detector.detect_all(shorthand_text)['clean']
            })
        
        return {
            'status': 'flagged',
            'flagged_words': flagged_words,
            'options': options
        }
    
    def get_stats(self) -> Dict:
        """
        Get optimizer statistics
        
        Returns:
            dict: Statistics about optimizer configuration
        """
        return {
            'leet_speak_enabled': self.enable_leet,
            'fancy_unicode_enabled': self.enable_unicode,
            'shorthand_enabled': self.enable_shorthand,
            'link_protection_enabled': self.enable_link_protection,
            'max_length': self.max_length
        }


# Module information
__version__ = '1.0.0'
__author__ = 'Chat Censor Tool Team'
