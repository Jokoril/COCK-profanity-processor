"""
Update Checker Module for Chat Censor Tool

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
    CURRENT_VERSION = "1.0.0"  # Updated to match production version
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
    
    def _check_thread(self, callback: Optional[Callable]):
        """Background thread for checking updates"""
        try:
            print(f"[UPDATE] Checking for updates from {self.VERSION_URL}")
            
            # Fetch version info
            response = requests.get(self.VERSION_URL, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()
            
            version_info = response.json()
            
            # Update last check time
            self.last_check = datetime.now().isoformat()
            if 'updates' not in self.config:
                self.config['updates'] = {}
            self.config['updates']['last_check'] = self.last_check
            
            # Compare versions
            remote_version = version_info.get('version', '0.0.0')
            
            if self._is_newer_version(remote_version, self.CURRENT_VERSION):
                print(f"[UPDATE] New version available: {remote_version} (current: {self.CURRENT_VERSION})")
                if callback:
                    callback(version_info)
            else:
                print(f"[UPDATE] Already on latest version: {self.CURRENT_VERSION}")
                if callback:
                    callback(None)
        
        except requests.RequestException as e:
            print(f"[UPDATE] Network error checking for updates: {e}")
            if callback:
                callback(None)
        
        except Exception as e:
            print(f"[UPDATE] Error checking for updates: {e}")
            if callback:
                callback(None)
    
    def _is_newer_version(self, remote: str, current: str) -> bool:
        """
        Compare version strings
        
        Args:
            remote: Remote version string (e.g., "1.1.0")
            current: Current version string (e.g., "1.0.0")
            
        Returns:
            bool: True if remote is newer than current
        """
        if PACKAGING_AVAILABLE:
            try:
                return version.parse(remote) > version.parse(current)
            except Exception as e:
                print(f"[UPDATE] Error parsing versions: {e}")
                return False
        else:
            # Simple string comparison fallback
            try:
                remote_parts = [int(x) for x in remote.split('.')]
                current_parts = [int(x) for x in current.split('.')]
                
                # Pad with zeros if needed
                while len(remote_parts) < len(current_parts):
                    remote_parts.append(0)
                while len(current_parts) < len(remote_parts):
                    current_parts.append(0)
                
                # Compare
                for r, c in zip(remote_parts, current_parts):
                    if r > c:
                        return True
                    elif r < c:
                        return False
                
                return False  # Equal versions
            
            except Exception as e:
                print(f"[UPDATE] Error comparing versions: {e}")
                return False
    
    def check_now_sync(self) -> Optional[Dict[str, Any]]:
        """
        Check for updates synchronously (blocking)
        
        Returns:
            dict: Version info if update available, None otherwise
        """
        if not self.available:
            print("[UPDATE] Update check skipped (disabled or dependencies missing)")
            return None
        
        try:
            print(f"[UPDATE] Checking for updates from {self.VERSION_URL}")
            
            response = requests.get(self.VERSION_URL, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()
            
            version_info = response.json()
            remote_version = version_info.get('version', '0.0.0')
            
            if self._is_newer_version(remote_version, self.CURRENT_VERSION):
                print(f"[UPDATE] New version available: {remote_version}")
                return version_info
            else:
                print(f"[UPDATE] Already on latest version: {self.CURRENT_VERSION}")
                return None
        
        except requests.RequestException as e:
            print(f"[UPDATE] Network error: {e}")
            return None
        
        except Exception as e:
            print(f"[UPDATE] Error: {e}")
            return None
    
    def get_release_notes(self, version_info: Dict[str, Any]) -> str:
        """
        Extract release notes from version info
        
        Args:
            version_info: Version info dict from server
            
        Returns:
            str: Release notes text
        """
        notes = version_info.get('release_notes', '')
        if not notes:
            notes = version_info.get('changelog', 'No release notes available.')
        
        return notes
    
    def get_download_url(self, version_info: Dict[str, Any]) -> str:
        """
        Extract download URL from version info
        
        Args:
            version_info: Version info dict from server
            
        Returns:
            str: Download URL
        """
        return version_info.get('download_url', 'https://github.com/Jokoril/COCK-profanity-processor/releases/latest')
    
    def disable_checks(self):
        """Disable automatic update checks"""
        self.check_enabled = False
        if 'updates' not in self.config:
            self.config['updates'] = {}
        self.config['updates']['check_enabled'] = False
        print("[UPDATE] Update checks disabled")
    
    def enable_checks(self):
        """Enable automatic update checks"""
        if REQUESTS_AVAILABLE:
            self.check_enabled = True
            self.available = True
            if 'updates' not in self.config:
                self.config['updates'] = {}
            self.config['updates']['check_enabled'] = True
            print("[UPDATE] Update checks enabled")
        else:
            print("[UPDATE] Cannot enable - 'requests' module not installed")
