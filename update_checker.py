"""
Update Checker Module for COCK Profanity Processor

Checks for application updates from GitHub-hosted version.json file.
Non-blocking, privacy-friendly, opt-out available.
"""

import json
import threading
from typing import Optional, Callable, Dict, Any
from datetime import datetime

# Try to import requests, fall back gracefully
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("[UPDATE] Warning: 'requests' module not available, update checks disabled")

# Try to import packaging for version comparison
try:
    from packaging import version
    PACKAGING_AVAILABLE = True
except ImportError:
    PACKAGING_AVAILABLE = False
    print("[UPDATE] Warning: 'packaging' module not available, using simple string comparison")


class UpdateChecker:
    """
    Check for application updates from GitHub
    
    Features:
    - Asynchronous checking (non-blocking)
    - Version comparison
    - Changelog retrieval
    - Privacy-friendly (no user data sent)
    - Graceful failure (network errors don't affect app)
    """
    
    # Configuration
    VERSION_URL = "https://raw.githubusercontent.com/Jokoril/COCK-profanity-processor/main/version.json"
    CURRENT_VERSION = "1.0.0"
    TIMEOUT_SECONDS = 5
    
    def __init__(self, config: dict):
        """
        Initialize update checker
        
        Args:
            config: Application configuration dict
        """
        self.config = config
        self.check_enabled = config.get('updates', {}).get('check_enabled', True)
        self.last_check = config.get('updates', {}).get('last_check', None)
        
        # Check if dependencies available
        self.available = REQUESTS_AVAILABLE and self.check_enabled
        
        if not REQUESTS_AVAILABLE:
            print("[UPDATE] Update checker disabled - 'requests' module not installed")
    
    def check_for_updates(self, callback: Optional[Callable[[Optional[Dict[str, Any]]], None]] = None):
        """
        Check for updates asynchronously (non-blocking)
        
        Args:
            callback: Function to call with results
                     - Called with version_info dict if update available
                     - Called with None if no update or error
        """
        if not self.available:
            print("[UPDATE] Update check skipped (disabled or dependencies missing)")
            if callback:
                callback(None)
            return
        
        # Run in background thread
        thread = threading.Thread(target=self._check_thread, args=(callback,))
        thread.daemon = True
        thread.start()
    
    def _check_thread(self, callback: Optional[Callable[[Optional[Dict[str, Any]]], None]]):
        """
        Background thread for update check
        
        Args:
            callback: Function to call with results
        """
        try:
            print(f"[UPDATE] Checking for updates from {self.VERSION_URL}")
            
            # HTTP GET with timeout
            response = requests.get(self.VERSION_URL, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()
            
            # Parse JSON
            version_info = response.json()
            
            # Validate required fields
            if 'version' not in version_info:
                print("[UPDATE] Error: version.json missing 'version' field")
                if callback:
                    callback(None)
                return
            
            latest = version_info.get('version', '0.0.0')
            
            print(f"[UPDATE] Current: {self.CURRENT_VERSION}, Latest: {latest}")
            
            # Compare versions
            if self._is_newer_version(latest, self.CURRENT_VERSION):
                print(f"[UPDATE] Update available: {latest}")
                
                # Update last check timestamp
                self._update_last_check()
                
                # Call callback with version info
                if callback:
                    callback(version_info)
            else:
                print("[UPDATE] Already up to date")
                
                # Update last check timestamp
                self._update_last_check()
                
                if callback:
                    callback(None)
        
        except requests.exceptions.Timeout:
            print(f"[UPDATE] Check timed out after {self.TIMEOUT_SECONDS}s")
            if callback:
                callback(None)
        
        except requests.exceptions.RequestException as e:
            print(f"[UPDATE] Network error: {e}")
            if callback:
                callback(None)
        
        except json.JSONDecodeError as e:
            print(f"[UPDATE] Invalid JSON in version.json: {e}")
            if callback:
                callback(None)
        
        except Exception as e:
            print(f"[UPDATE] Unexpected error: {e}")
            if callback:
                callback(None)
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """
        Compare version strings
        
        Args:
            latest: Latest version string (e.g., "5.1.0")
            current: Current version string (e.g., "5.0.0")
            
        Returns:
            True if latest > current
        """
        if PACKAGING_AVAILABLE:
            # Use packaging library for proper semantic versioning
            try:
                return version.parse(latest) > version.parse(current)
            except Exception as e:
                print(f"[UPDATE] Version parsing error: {e}")
                return False
        else:
            # Fall back to simple string comparison
            # Works for X.Y.Z format if all numbers
            try:
                latest_parts = [int(x) for x in latest.split('.')]
                current_parts = [int(x) for x in current.split('.')]
                return latest_parts > current_parts
            except Exception as e:
                print(f"[UPDATE] Version comparison error: {e}")
                return False
    
    def _update_last_check(self):
        """Update last check timestamp in config"""
        try:
            if 'updates' not in self.config:
                self.config['updates'] = {}
            
            self.config['updates']['last_check'] = datetime.now().isoformat()
            self.last_check = self.config['updates']['last_check']
            
            # Note: Config saving handled by main application
            print(f"[UPDATE] Last check timestamp updated")
        
        except Exception as e:
            print(f"[UPDATE] Failed to update last check timestamp: {e}")
    
    def get_last_check_time(self) -> Optional[str]:
        """
        Get human-readable last check time
        
        Returns:
            Formatted string like "2 hours ago" or None
        """
        if not self.last_check:
            return None
        
        try:
            last = datetime.fromisoformat(self.last_check)
            now = datetime.now()
            delta = now - last
            
            # Format time delta
            if delta.days > 0:
                return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
            elif delta.seconds >= 3600:
                hours = delta.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif delta.seconds >= 60:
                minutes = delta.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "just now"
        
        except Exception as e:
            print(f"[UPDATE] Error formatting last check time: {e}")
            return None
    
    @staticmethod
    def get_current_version() -> str:
        """Get current application version"""
        return UpdateChecker.CURRENT_VERSION
    
    @staticmethod
    def is_available() -> bool:
        """Check if update checker is available (dependencies installed)"""
        return REQUESTS_AVAILABLE


# Example version.json structure for reference:
"""
{
  "version": "1.1.0",
  "release_date": "2024-12-31",
  "download_url": "https://github.com/Jokoril/COCK-profanity-processor/releases/latest",
  "release_notes": "https://github.com/Jokoril/COCK-profanity-processor/releases/tag/v1.1.0",
  "minimum_version": "1.0.0",
  "changelog": [
    "Security improvements",
    "Performance optimizations",
    "Bug fixes"
  ],
  "critical": false
}
"""
