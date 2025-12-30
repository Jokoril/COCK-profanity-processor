#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mode Router Module
==================
Routes processing based on Strict vs Permissive mode

Features:
- Strict Mode: Manual whitelist management, user confirms sends
- Permissive Mode: Auto-optimization, auto-learning from game behavior
- Mode-specific workflows and UI behavior

Usage:
    from mode_router import ModeRouter
    
    router = ModeRouter(config, detector, optimizer, whitelist_manager)
    result = router.process_message("test message")
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
import fast_detector


class DetectionMode(Enum):
    """Detection modes"""
    MANUAL = "manual"  # Renamed from STRICT - user reviews and chooses
    AUTO = "auto"      # Renamed from PERMISSIVE - automatic optimization


@dataclass
class ProcessingResult:
    """Result of message processing"""
    mode: DetectionMode
    original: str
    suggested: Optional[str]
    should_show_ui: bool
    flagged_words: List[str]
    action: str  # 'send', 'optimize', 'block', 'manual'
    explanation: str
    paste_part: str = ""  # Remainder for multi-part messages (empty if all fits)


class ModeRouter:
    """
    Routes message processing based on detection mode
    
    Modes:
        Strict Mode:
            - Show UI when filtered word detected
            - User manually whitelists or optimizes
            - User confirms message before send
            - Learning: Manual whitelist additions only
        
        Permissive Mode:
            - Auto-optimize filtered messages
            - Auto-send optimized version
            - Learning: Auto-update whitelist/blacklist from game feedback
            - UI only shown for failures
    """
    
    def __init__(self, config: Dict, detector, optimizer, whitelist_manager):
        """
        Initialize mode router
        
        Args:
            config: Configuration dictionary
            detector: FastCensorDetector instance
            optimizer: MessageOptimizer instance
            whitelist_manager: WhitelistManager instance
        """
        self.config = config
        self.detector = detector
        self.optimizer = optimizer
        self.whitelist = whitelist_manager
        
        # Get mode from config
        mode_str = config.get('detection_mode', 'manual').lower()
        self.mode = DetectionMode.MANUAL if mode_str == 'manual' else DetectionMode.AUTO
        
        # Get auto-send settings for auto mode
        auto_send_config = config.get('auto_send', {})
        self.auto_send_enabled = auto_send_config.get('enabled', False)
        self.auto_send_delay = auto_send_config.get('delay_ms', 100)
        self.auto_send_key = auto_send_config.get('key_combo', 'enter')
    
    def process_message(self, text: str) -> ProcessingResult:
        """
        Process message based on current mode
        
        Args:
            text: Message to process
        
        Returns:
            ProcessingResult with processing details and recommended action
        """
        # Detect issues
        detection = self.detector.detect_all(text)
        
        if detection['clean']:
            # Message is clean - but check if it needs shorthand for length
            original_text = detection.get('original_text', text)
            collapsed_text = detection.get('collapsed_text', text)
            
            # Check if message exceeds limits
            byte_limit = self.config.get('byte_limit', 92)
            char_limit = self.config.get('character_limit', 80)
            
            exceeds_byte_limit = byte_limit > 0 and len(collapsed_text.encode('utf-8')) > byte_limit
            exceeds_char_limit = char_limit > 0 and len(collapsed_text) > char_limit
            
            if exceeds_byte_limit or exceeds_char_limit:
                # Message too long - apply shorthand compression
                print(f"[ROUTER] Clean message exceeds limits: {len(collapsed_text.encode('utf-8'))} bytes, {len(collapsed_text)} chars")
                
                # Use optimizer to apply shorthand and enforce limits
                # Pass collapse_mapping so optimizer knows which words were from collapse
                collapse_mapping = detection.get('collapse_mapping')
                optimization = self.optimizer.optimize(collapsed_text, collapse_mapping=collapse_mapping)
                
                if optimization.paste_part:
                    # Message was split
                    return ProcessingResult(
                        mode=self.mode,
                        original=original_text,
                        suggested=optimization.optimized,
                        should_show_ui=(self.mode == DetectionMode.MANUAL),
                        flagged_words=[],
                        action='manual' if self.mode == DetectionMode.MANUAL else 'optimize',
                        explanation=f"Message shortened with shorthand (was {len(collapsed_text)} chars)",
                        paste_part=optimization.paste_part
                    )
                else:
                    # Shorthand applied successfully
                    return ProcessingResult(
                        mode=self.mode,
                        original=original_text,
                        suggested=optimization.optimized if optimization.optimized != collapsed_text else None,
                        should_show_ui=False,
                        flagged_words=[],
                        action='send',
                        explanation=f"Message shortened with shorthand" if optimization.optimized != collapsed_text else "Message is clean",
                        paste_part=""
                    )
            
            # Message is clean and within limits
            return ProcessingResult(
                mode=self.mode,
                original=text,
                suggested=None,
                should_show_ui=False,
                flagged_words=[],
                action='send',
                explanation="Message is clean",
                paste_part=""
            )
        
        # Message has filtered words - route to mode-specific handler
        flagged_words = [r.filtered_word for r in detection['flagged']]
        
        if self.mode == DetectionMode.MANUAL:
            return self._process_manual(text, flagged_words, detection)
        else:  # AUTO mode
            return self._process_auto(text, flagged_words, detection)
    
    def _process_manual(self, text: str, flagged_words: List[str], detection: Dict) -> ProcessingResult:
        """
        Process in Manual mode (renamed from Strict mode)
        
        Manual Mode Workflow:
            1. Detect filtered words
            2. Show UI overlay with:
               - Detected words
               - Optimization suggestions (even if partial)
               - [Add to Whitelist] button
               - [Use Suggestion] button
               - [Cancel] button
            3. User makes decision
            4. Manual send (user presses hotkey again)
        
        Note: Works on COLLAPSED text (spaced patterns are collapsed)
        
        Args:
            text: Original message
            flagged_words: List of flagged words
            detection: Detection results
        
        Returns:
            ProcessingResult for manual mode
        """
        # Get collapsed text from detection
        original_text = detection.get('original_text', text)
        collapsed_text = detection.get('collapsed_text', text)
        collapse_mapping = detection.get('collapse_mapping')
        
        # Generate optimization suggestions using collapsed text
        # Pass collapse_mapping so optimizer knows which words were from collapse (whitelist override)
        optimization = self.optimizer.optimize(collapsed_text, collapse_mapping=collapse_mapping)
        
        # Show suggestion if:
        # 1. Optimization succeeded (clean), OR
        # 2. Partial optimization available (some words optimized)
        show_suggestion = optimization.success or optimization.partial_optimization
        
        # Build explanation
        if optimization.success:
            explanation = f"Optimization successful. {len(flagged_words)} word(s) detected."
        elif optimization.partial_optimization:
            if optimization.links_modified:
                explanation = f"Partial optimization (URLs protected). {len(flagged_words)} word(s) remain in URLs."
            else:
                explanation = f"Partial optimization available. {len(flagged_words)} word(s) detected."
        else:
            explanation = f"Detected {len(flagged_words)} filtered word(s). User action required."
        
        return ProcessingResult(
            mode=DetectionMode.MANUAL,
            original=original_text,
            suggested=optimization.optimized if show_suggestion else None,
            should_show_ui=True,
            flagged_words=flagged_words,
            action='manual',
            explanation=explanation,
            paste_part=optimization.paste_part if show_suggestion else ""
        )
    
    def _process_auto(self, text: str, flagged_words: List[str], detection: Dict) -> ProcessingResult:
        """
        Process in Auto mode (replaces Permissive mode)
        
        Auto Mode: Simple and predictable
        - Detect all filtered words (standalone, embedded, sliding window)
        - Optimize everything automatically
        - Send immediately
        - No prompts, no learning
        
        Note: Works on COLLAPSED text (spaced patterns like "m o t h e r f u c k"
        become "motherfuck" in output - spacing NOT preserved for collapsed patterns)
        
        Args:
            text: Original message
            flagged_words: List of flagged words
            detection: Detection results
        
        Returns:
            ProcessingResult for auto mode
        """
        # Get collapsed text from detection (this is what we'll optimize)
        original_text = detection.get('original_text', text)
        collapsed_text = detection.get('collapsed_text', text)
        
        print(f"\n[AUTO] ========== Processing: '{original_text}' ==========")
        
        if not flagged_words:
            # Clean message - send collapsed version
            print(f"[AUTO] → Action: SEND (clean)")
            return ProcessingResult(
                mode=DetectionMode.AUTO,
                original=original_text,
                suggested=collapsed_text,  # Send collapsed version
                should_show_ui=False,
                flagged_words=[],
                action='send',
                explanation="Message is clean",
                paste_part=""
            )
        
        # Optimize using COLLAPSED text (simpler, no position mapping needed)
        print(f"[AUTO] Detected: {flagged_words}")
        print(f"[AUTO] Calling optimizer on collapsed text...")
        
        # Pass collapse_mapping so optimizer knows which words were from collapse (whitelist override)
        collapse_mapping = detection.get('collapse_mapping')
        optimization = self.optimizer.optimize(collapsed_text, collapse_mapping=collapse_mapping)
        print(f"[AUTO] Optimization result: success={optimization.success}, optimized='{optimization.optimized}'")
        
        if optimization.success:
            print(f"[AUTO] → Action: OPTIMIZE (auto-send, NO prompt)")
            
            # Build explanation
            explanation = f"Auto-optimized all detected words"
            if optimization.links_modified:
                explanation += " (⚠️ Link modified)"
                print(f"[AUTO] WARNING: Numeral words in links were modified!")
            
            if optimization.paste_part:
                print(f"[AUTO] Multi-part message: paste_part has {len(optimization.paste_part)} chars")
            
            return ProcessingResult(
                mode=DetectionMode.AUTO,
                original=original_text,
                suggested=optimization.optimized,  # Send portion
                should_show_ui=False,  # No prompts in auto mode
                flagged_words=flagged_words,
                action='optimize',
                explanation=explanation,
                paste_part=optimization.paste_part  # Remainder for multi-part
            )
        
        # Optimization not fully successful - check if partial optimization or split available
        elif optimization.paste_part:
            # Message was split - send the split portion
            print(f"[AUTO] → Action: SEND_SPLIT (message split due to length)")
            print(f"[AUTO] Sending {len(optimization.optimized)} chars, pasting {len(optimization.paste_part)} chars")
            
            explanation = "Message split due to length limits"
            if optimization.partial_optimization:
                explanation += " (partial optimization applied)"
            
            return ProcessingResult(
                mode=DetectionMode.AUTO,
                original=original_text,
                suggested=optimization.optimized,  # Use split portion
                should_show_ui=False,
                flagged_words=flagged_words,
                action='optimize',
                explanation=explanation,
                paste_part=optimization.paste_part
            )
        
        elif optimization.partial_optimization:
            # Partial optimization succeeded - send it
            print(f"[AUTO] → Action: PARTIAL_OPTIMIZE (some words optimized)")
            print(f"[AUTO] Reduced flagged words, sending partial optimization")
            
            explanation = "Partial optimization applied"
            if optimization.links_modified:
                explanation += " (URLs protected)"
                print(f"[AUTO] Some filtered words remain in protected URLs")
            
            return ProcessingResult(
                mode=DetectionMode.AUTO,
                original=original_text,
                suggested=optimization.optimized,
                should_show_ui=False,
                flagged_words=flagged_words,
                action='optimize',  # Send the partial optimization
                explanation=explanation,
                paste_part=""
            )
        
        else:
            # No optimization, no split, no partial - block
            print(f"[AUTO] → Action: BLOCK (optimization failed completely)")
            return ProcessingResult(
                mode=DetectionMode.AUTO,
                original=original_text,
                suggested=optimization.optimized,
                should_show_ui=False,
                flagged_words=flagged_words,
                action='block',
                explanation="Could not optimize message",
                paste_part=""
            )
    
    def process_force_optimize(self, text: str) -> ProcessingResult:
        """
        Process message with force optimization
        
        Force optimization applies optimization to ALL words regardless of detection:
        - Vowels → Leetspeak (if enabled)
        - Consonants → Fancy Unicode (if enabled)
        
        Used when game censors patterns we can't detect.
        Triggered by force optimize hotkey (default: Shift+F12)
        
        Args:
            text: Message to force optimize
            
        Returns:
            ProcessingResult with force-optimized text
        """
        print(f"[FORCE] ========== Force Optimizing: '{text}' ==========")
        
        # Collapse spaced patterns
        collapsed_text = self.detector.collapse_spaced_patterns(text)
        
        # Force optimize ALL words
        optimized = self.optimizer.force_optimize_all(collapsed_text)
        
        # Enforce limits (may split into parts)
        send_part, paste_part, stages = self.optimizer.enforce_limits(optimized, links=[], stages_applied=['force_optimize'], )
        
        print(f"[FORCE] Optimization complete: '{send_part}'")
        if paste_part:
            print(f"[FORCE] Multi-part: remainder '{paste_part}' will be pasted")
        
        return ProcessingResult(
            mode=self.mode,
            original=text,
            suggested=send_part,
            should_show_ui=False,
            flagged_words=[],
            action='optimize',
            explanation="Force optimized all words",
            paste_part=paste_part
        )
    
    def switch_mode(self, new_mode: DetectionMode):
        """
        Switch detection mode
        
        Args:
            new_mode: New detection mode
        """
        self.mode = new_mode
        
        # Update config
        self.config['detection_mode'] = new_mode.value
    
    def get_mode(self) -> DetectionMode:
        """
        Get current detection mode
        
        Returns:
            DetectionMode: Current mode
        """
        return self.mode
    
    def is_strict(self) -> bool:
        """Check if in strict mode"""
        return self.mode == DetectionMode.STRICT
    
    def is_permissive(self) -> bool:
        """Check if in permissive mode"""
        return self.mode == DetectionMode.PERMISSIVE
    
    def get_stats(self) -> Dict:
        """
        Get router statistics
        
        Returns:
            dict: Statistics about router configuration
        """
        return {
            'mode': self.mode.value,
            'auto_send_enabled': self.auto_send_enabled,
            'auto_send_delay_ms': self.auto_send_delay
        }


# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
