#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Loader Module
============================
Manages application configuration using JSON

Features:
- Load/save configuration from JSON
- Default configuration template
- Configuration validation
- Auto-creation of missing files
"""

import json
import os
from typing import Dict, Any, Optional
import path_manager
import tempfile
import shutil

# Filepath sanitization
def sanitize_path(file_path: str, base_dir: Optional[str] = None) -> str:
    """Sanitize file path to prevent path traversal attacks"""
    abs_path = os.path.abspath(file_path)
    if base_dir:
        base_abs = os.path.abspath(base_dir)
        if not abs_path.startswith(base_abs + os.sep) and abs_path != base_abs:
            raise ValueError(f"Path traversal detected: {file_path} outside {base_dir}")
    return abs_path

# Default configuration template
DEFAULT_CONFIG = {
    "version": "1.0",
    "filter_file": "filter_default.txt",  # Default bundled filter
    "detection_mode": "auto",  # "auto" or "manual"
    
    "hotkey": "f12",  # Global hotkey combination
    "force_optimize_hotkey": "ctrl+f12",  # Force optimize hotkey
    "toggle_hotkeys_hotkey": "ctrl+alt+c",  # Toggle hotkeys on/off
    "hotkeys_enabled": True,  # Whether hotkeys are currently enabled
    
    "keyboard_delay_ms": 100,
    
    "sliding_window_size": 3,
    
    "auto_send": {
        "enabled": False,  # Only for auto mode
        "delay_ms": 100,
        "key_combo": "enter"
    },
    
"ui": {
        "theme": "dark",
        "show_debug_info": False,
        "notification_position": "bottom-right",
        "prompt_position": "center",
        "notification_sound": True,
        "prompt_sound": True,
        # Fine-tuning offsets (pixels from edge)
        "notification_offset_x": 20,
        "notification_offset_y": 20,
        "prompt_offset_x": 0,
        "prompt_offset_y": 0,
        # UI scaling (0.5 to 2.0, default 1.0)
        "notification_scale": 1.0,
        "prompt_scale": 1.0,
        "settings_scale": 1.0
    },
    
    "optimization": {
        "leet_speak": True,
        "fancy_unicode": True,
        "shorthand": True,
        "link_protection": True
    },
    
    "performance": {
        "max_filter_load_time_ms": 500,
        "max_detection_time_ms": 50
    },
    
    "paths": {
        "whitelist_file": "whitelist.txt",
    },
    
    "updates": {
        "check_enabled": True,           # Check for updates at startup
        "check_frequency": "startup",    # "startup" or "daily" (future)
        "last_check": None               # ISO timestamp of last check
    },
    
    "help": {
        "show_tooltips": True,           # Show help tooltips
        "show_first_run_guide": True     # Show guide on first run (future)
    }
}


class ConfigLoader:
    """
    Configuration management class
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader
        
        Args:
            config_path: Optional custom config file path.
                        If None, uses default 'config.json' in app directory.
        """
        if config_path is None:
            config_path = path_manager.get_data_file('config.json')
        
        self.config_path = config_path
        self.config = None
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file
        
        Returns:
            dict: Configuration dictionary
            
        Behavior:
            - If file doesn't exist, creates it with defaults
            - If file is corrupted, backs it up and creates new one
            - Merges with defaults to ensure all keys exist
        """
        if not os.path.exists(self.config_path):
            # Config doesn't exist - create default
            print(f"Config file not found. Creating default: {self.config_path}")
            self.config = DEFAULT_CONFIG.copy()
            
            # Copy bundled filter file to exe directory on first run
            self._ensure_filter_file_exists()
            
            self.save()
            return self.config
        
        try:
            # Load existing config
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            self.config = self._merge_with_defaults(loaded_config)

            # Sanitize file paths in config
            self._sanitize_config_paths()
            
            return self.config
            
        except json.JSONDecodeError as e:
            # Config file is corrupted
            print(f"Error reading config file: {e}")
            
            # Secure backup using temp file
            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.backup') as tmp:
                    backup_path = tmp.name
                shutil.copy2(self.config_path, backup_path)
                print(f"Corrupted config backed up to: {backup_path}")
            except Exception as backup_error:
                print(f"Warning: Could not backup corrupted config: {backup_error}")
            
            # Create new default config
            self.config = DEFAULT_CONFIG.copy()
            self.save()
            return self.config
        
        except Exception as e:
            print(f"Unexpected error loading config: {e}")
            self.config = DEFAULT_CONFIG.copy()
            return self.config
        
    def _ensure_filter_file_exists(self) -> None:
        """
        Ensure filter file exists, copy from bundle if needed
        """
        import sys
        
        filter_file = self.config.get('filter_file', 'filter_default.txt')
        
        # If filter_file is just a filename, make it relative to exe directory
        if not os.path.isabs(filter_file):
            filter_file = path_manager.get_data_file(filter_file)
            self.config['filter_file'] = filter_file
        
        # If filter file doesn't exist, try to copy from bundle
        if not os.path.exists(filter_file):
            print(f"Filter file not found at: {filter_file}")
            
            # Check if running as .exe with bundled resources
            if getattr(sys, 'frozen', False):
                bundled_filter = path_manager.get_bundled_resource('filter_default.txt')
                
                if os.path.exists(bundled_filter):
                    try:
                        print(f"Copying bundled filter file...")
                        print(f"  From: {bundled_filter}")
                        print(f"  To: {filter_file}")
                        shutil.copy2(bundled_filter, filter_file)
                        print(f"Filter file created successfully")
                    except Exception as e:
                        print(f"Warning: Could not copy filter file: {e}")
                else:
                    print(f"Warning: Bundled filter not found at: {bundled_filter}")
            else:
                # Running as script - create empty filter file with instructions
                print(f"Creating empty filter file at: {filter_file}")
                try:
                    with open(filter_file, 'w', encoding='utf-8') as f:
                        f.write("# COCK Profanity Processor - Filter Word List\n")
                        f.write("# Add filtered words here, one per line\n")
                        f.write("# Example:\n")
                        f.write("# badword\n")
                        f.write("# anotherbadword\n")
                    print("Empty filter file created - please add your filtered words")
                except Exception as e:
                    print(f"Error creating filter file: {e}")
    
    def save(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save configuration to file
        
        Args:
            config: Optional config dict to save. If None, saves current config.
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if config is not None:
            self.config = config
        
        if self.config is None:
            print("No configuration to save")
            return False
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Write config
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (supports dot notation: "ui.theme")
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        if self.config is None:
            self.load()
        
        # Support dot notation for nested keys
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value
        
        Args:
            key: Configuration key (supports dot notation: "ui.theme")
            value: Value to set
        """
        if self.config is None:
            self.load()
        
        # Support dot notation for nested keys
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate configuration
        
        Returns:
            tuple: (is_valid: bool, errors: list[str])
        """
        if self.config is None:
            return (False, ["Configuration not loaded"])
        
        errors = []
        
        # Check required fields
        if not self.config.get('filter_file'):
            errors.append("filter_file is not set (required)")
        
        # Check detection mode
        mode = self.config.get('detection_mode')
        if mode not in ['strict', 'permissive']:
            errors.append(f"Invalid detection_mode: {mode}")
        
        # Check hotkey combo
        if not self.config.get('hotkey', {}).get('combo'):
            errors.append("hotkey.combo is not set")
        
        # Check theme
        theme = self.config.get('ui', {}).get('theme')
        if theme not in ['dark', 'light']:
            errors.append(f"Invalid ui.theme: {theme}")
        
        return (len(errors) == 0, errors)
    
    def _sanitize_config_paths(self) -> None:
        """Sanitize all file paths in configuration"""
        if not self.config:
            return
        
        if self.config.get('filter_file'):
            try:
                self.config['filter_file'] = sanitize_path(self.config['filter_file'])
            except ValueError as e:
                print(f"Warning: Invalid filter_file path: {e}")
                self.config['filter_file'] = ""
        
        if 'paths' in self.config:
            for key in ['whitelist_file', 'shorthand_file']:
                if key in self.config['paths'] and self.config['paths'][key]:
                    try:
                        path = self.config['paths'][key]
                        if not os.path.isabs(path):
                            path = path_manager.get_data_file(path)
                        self.config['paths'][key] = sanitize_path(path)
                    except ValueError as e:
                        print(f"Warning: Invalid {key} path: {e}")
                        self.config['paths'][key] = ""
    
    def _merge_with_defaults(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge loaded config with defaults to ensure all keys exist
        
        Args:
            loaded_config: Configuration loaded from file
            
        Returns:
            dict: Merged configuration
        """
        def merge_dicts(default: dict, loaded: dict) -> dict:
            """Recursively merge dictionaries"""
            result = default.copy()
            
            for key, value in loaded.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
            
            return result
        
        return merge_dicts(DEFAULT_CONFIG, loaded_config)
    
    def reset_to_defaults(self) -> None:
        """
        Reset configuration to defaults
        """
        self.config = DEFAULT_CONFIG.copy()
        self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get entire configuration dictionary
        
        Returns:
            dict: Complete configuration
        """
        if self.config is None:
            self.load()
        return self.config.copy()


def create_default_files():
    """
    Create default data files if they don't exist
    
    Creates:
        - config.json (with defaults)
        - whitelist.txt (empty)
        - blacklist.txt (empty)
        - shorthand.json (with common abbreviations)
    """
    # Create config.json
    config_loader = ConfigLoader()
    if not os.path.exists(config_loader.config_path):
        config_loader.load()  # This will create it
        print(f"Created: {config_loader.config_path}")
    
    # Create whitelist.txt
    whitelist_path = path_manager.get_data_file('whitelist.txt')
    if not os.path.exists(whitelist_path):
        with open(whitelist_path, 'w', encoding='utf-8') as f:
            f.write("# Whitelist - Safe words when embedded\n")
            f.write("# Add one word per line (case-insensitive)\n")
            f.write("# Example: ass (makes 'assassin' safe)\n")
        print(f"Created: {whitelist_path}")
    
# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
