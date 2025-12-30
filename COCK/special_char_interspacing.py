"""
Special Character Interspacing Module
======================================

Inserts special Unicode characters into text to break filter pattern detection
while minimizing visual impact.

Strategy:
- Normal mode: Insert between 1st and 2nd character of flagged words
- Force mode: Insert between every character

Example (normal mode):
    "fuck" → "f❤uck" (insert ❤ after 1st char)
    "420" → "4❤20" (insert ❤ after 1st char)

Example (force mode):
    "fuck" → "f❤u❤c❤k" (insert ❤ between every char)
    "test message" → "t❤e❤s❤t❤ ❤m❤e❤s❤s❤a❤g❤e"
"""


class SpecialCharInterspacing:
    """
    Special character interspacing for filter evasion
    
    Inserts user-configurable special characters that:
    - Break filter pattern detection
    - Minimize overhead (+1 char, +2-3 bytes per insertion)
    - Preserve or enhance legibility (depending on game font)
    """
    
    DEFAULT_CHAR = '❤'  # Heart symbol (U+2764, 3 bytes)
    
    def __init__(self, config: dict):
        """
        Initialize special character interspacing
        
        Args:
            config: Configuration dictionary with 'special_char_interspacing' section
        """
        self.config = config
        interspacing_config = config.get('special_char_interspacing', {})
        
        # Get user's custom character or use default
        self.char = interspacing_config.get('character', self.DEFAULT_CHAR)
        
        # Validate character (must be exactly 1 character)
        if not self.char or len(self.char) != 1:
            print(f"[INTERSPACING] Warning: Invalid character '{self.char}', using default ❤")
            self.char = self.DEFAULT_CHAR
    
    def apply_to_word(self, word: str) -> str:
        """
        Apply interspacing to a single word (normal mode)
        
        Inserts special character between 1st and 2nd character.
        Similar to numerical araea handling.
        
        Args:
            word: Word to process
            
        Returns:
            str: Word with special character inserted
            
        Examples:
            "fuck" → "f❤uck"
            "ass" → "a❤ss"
            "420" → "4❤20"
            "a" → "a" (unchanged, only 1 char)
        """
        if len(word) < 2:
            # Single character word, nothing to insert
            return word
        
        # Insert between 1st and 2nd character
        return word[0] + self.char + word[1:]
    
    def apply_to_text(self, text: str, flagged_words: list = None) -> str:
        """
        Apply interspacing to flagged words in text (normal mode)
        
        Args:
            text: Original text
            flagged_words: List of flagged words to process (lowercase)
                          If None, applies to all words
            
        Returns:
            str: Text with special character inserted in flagged words
            
        Examples:
            text="fuck you", flagged=["fuck"]
            → "f❤uck you"
            
            text="test 420", flagged=["420"]
            → "test 4❤20"
        """
        if not flagged_words:
            print(f"[INTERSPACING] No flagged words provided")
            return text
        
        result = text
        
        # Process each flagged word
        # Sort by length (longest first) to avoid partial replacements
        sorted_words = sorted(flagged_words, key=len, reverse=True)
        
        print(f"[INTERSPACING] Processing {len(sorted_words)} flagged words with char '{self.char}'")
        
        for word in sorted_words:
            if len(word) < 2:
                print(f"[INTERSPACING] Skipping '{word}' (too short)")
                continue
            
            # Create interspaced version
            interspaced = self.apply_to_word(word)
            
            print(f"[INTERSPACING] Looking for '{word}' to replace with '{interspaced}'")
            
            # Replace in text (case-insensitive)
            import re
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            
            # Check if pattern found
            matches = pattern.findall(result)
            if matches:
                print(f"[INTERSPACING] Found {len(matches)} occurrence(s) of '{word}'")
                result = pattern.sub(interspaced, result, count=1)
                print(f"[INTERSPACING] Replaced '{word}' with '{interspaced}'")
            else:
                print(f"[INTERSPACING] WARNING: '{word}' not found in text!")
                print(f"[INTERSPACING] Text: {result[:50]}...")
        
        return result
    
    def apply_to_text_with_positions(self, text: str, detection_results: list) -> str:
        """
        Apply interspacing using position information from detection results
        
        This method handles embeddings correctly by using the position where
        the filtered word appears within the larger word.
        
        Args:
            text: Original text
            detection_results: List of DetectionResult objects with position info
            
        Returns:
            str: Text with special character inserted at correct positions
            
        Examples:
            Detection: "urin" embedded in "During" at position 1
            Result: "Du❤ring" (insert after position 1)
        """
        if not detection_results:
            print(f"[INTERSPACING] No detection results provided")
            return text
        
        # Sort detection results by position (process from end to start to avoid offset issues)
        # For embedding results, we need to insert at the position of the filtered word
        insertions = []  # List of (position, char) tuples
        
        for result in detection_results:
            # Get the full word and filtered word
            filtered_word = result.filtered_word.lower()
            
            if result.detection_type.name == 'EMBEDDING' and result.full_word:
                # Embedding: filtered word is within a larger word
                full_word = result.full_word
                
                # Find the full word in the text (case-insensitive)
                import re
                pattern = re.compile(re.escape(full_word), re.IGNORECASE)
                matches = list(pattern.finditer(text))
                
                if matches:
                    match = matches[0]  # Use first match
                    word_start = match.start()
                    
                    # Find where the filtered word appears in the full word
                    full_word_lower = full_word.lower()
                    filtered_pos_in_word = full_word_lower.find(filtered_word)
                    
                    if filtered_pos_in_word >= 0:
                        # Calculate absolute position in text where we need to insert
                        # Insert after the first character of the filtered word
                        insert_pos = word_start + filtered_pos_in_word + 1
                        
                        insertions.append((insert_pos, self.char))
                        print(f"[INTERSPACING] Embedding: '{filtered_word}' in '{full_word}' at word pos {filtered_pos_in_word}")
                        print(f"[INTERSPACING]   Inserting '{self.char}' at text position {insert_pos}")
                else:
                    print(f"[INTERSPACING] WARNING: Full word '{full_word}' not found in text")
            
            elif result.detection_type.name == 'STANDALONE':
                # Standalone word: use the standard approach
                # Find the word and insert after first character
                import re
                pattern = re.compile(r'\b' + re.escape(filtered_word) + r'\b', re.IGNORECASE)
                matches = list(pattern.finditer(text))
                
                if matches:
                    match = matches[0]
                    insert_pos = match.start() + 1  # After first character
                    insertions.append((insert_pos, self.char))
                    print(f"[INTERSPACING] Standalone: '{filtered_word}' at position {insert_pos}")
                else:
                    print(f"[INTERSPACING] WARNING: Standalone word '{filtered_word}' not found")
            
            elif result.detection_type.name == 'STRIPPED_WINDOW' and result.window_range:
                # Sliding window: find where filtered word appears in the window
                start, end = result.window_range
                filtered_word = result.filtered_word.lower()
                
                # Extract the window text
                window_text = text[start:end]
                
                # Strip it like the detector does (remove non-alphanumeric)
                import re as re_module
                stripped_window = re_module.sub(r'[^a-zA-Z0-9]', '', window_text).lower()
                
                # Find where filtered word appears in stripped window
                filtered_pos_in_stripped = stripped_window.find(filtered_word)
                
                if filtered_pos_in_stripped >= 0:
                    # Map back to original text position
                    # Count alphanumeric characters in window until we reach filtered_pos
                    char_count = 0
                    for i, char in enumerate(window_text):
                        if char.isalnum():
                            if char_count == filtered_pos_in_stripped:
                                # Found it - insert after this character
                                insert_pos = start + i + 1
                                insertions.append((insert_pos, self.char))
                                print(f"[INTERSPACING] Sliding window: '{filtered_word}' starts at position {insert_pos}")
                                break
                            char_count += 1
                else:
                    # Fallback: insert at window start
                    insert_pos = start + 1
                    insertions.append((insert_pos, self.char))
                    print(f"[INTERSPACING] Sliding window (fallback): inserting at position {insert_pos}")
        
        # Sort insertions by position (descending) to avoid offset issues
        insertions.sort(key=lambda x: x[0], reverse=True)
        
        # Apply insertions from end to start
        result_text = text
        for pos, char in insertions:
            if 0 <= pos <= len(result_text):
                result_text = result_text[:pos] + char + result_text[pos:]
                print(f"[INTERSPACING] Inserted '{char}' at position {pos}")
        
        return result_text
    
    def apply_force_mode(self, text: str) -> str:
        """
        Apply interspacing to ALL characters (force mode)
        
        Inserts special character between every character in the text.
        Maximum obfuscation for when normal mode fails.
        
        Args:
            text: Original text
            
        Returns:
            str: Text with special character between every character
            
        Examples:
            "fuck" → "f❤u❤c❤k"
            "test 420" → "t❤e❤s❤t❤ ❤4❤2❤0"
        """
        if len(text) < 2:
            return text
        
        # Insert special char between every character
        result = []
        for i, char in enumerate(text):
            result.append(char)
            if i < len(text) - 1:  # Don't add after last char
                result.append(self.char)
        
        return ''.join(result)
    
    def get_char(self) -> str:
        """Get current special character"""
        return self.char
    
    def set_char(self, char: str) -> bool:
        """
        Set special character
        
        Args:
            char: New character (must be exactly 1 character)
            
        Returns:
            bool: True if set successfully, False if invalid
        """
        if not char or len(char) != 1:
            return False
        
        self.char = char
        return True
    
    def reset_to_default(self):
        """Reset to default character (❤)"""
        self.char = self.DEFAULT_CHAR
    
    def get_overhead_info(self) -> dict:
        """
        Get overhead information for current character
        
        Returns:
            dict: {
                'char': character,
                'bytes': byte count,
                'per_word': overhead per word (normal mode),
                'per_char': overhead per char (force mode)
            }
        """
        char_bytes = len(self.char.encode('utf-8'))
        
        return {
            'char': self.char,
            'bytes': char_bytes,
            'per_word': f"+1 char, +{char_bytes} bytes",
            'per_char': f"+1 char, +{char_bytes} bytes per insertion"
        }
