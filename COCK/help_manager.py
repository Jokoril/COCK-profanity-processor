"""
Help Manager Module for COCK Profanity Processor

Manages links to documentation, GitHub resources, and help pages.
Provides centralized access to all help resources.
"""

from typing import Dict, Optional

# Try to import PyQt5, fall back gracefully
try:
    from PyQt5.QtCore import QUrl
    from PyQt5.QtGui import QDesktopServices
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    print("[HELP] Warning: PyQt5 not available, help links disabled")


class HelpManager:
    """
    Manage help resources and documentation links
    
    Provides centralized access to:
    - GitHub documentation
    - README files
    - Issue tracker
    - Release notes
    - Wiki pages
    """
    
    # GitHub URLs (update with your actual repository)
    GITHUB_REPO = "https://github.com/Jokoril/COCK-profanity-processor"
    KOFI_LINK = "https://ko-fi.com/jokoril"
    
    # Documentation URLs
    URLS = {
        # Main documentation
        'readme': f"{GITHUB_REPO}#readme",
        'documentation': f"{GITHUB_REPO}/blob/main/docs/README.md",
        'getting_started': f"{GITHUB_REPO}/blob/main/docs/GETTING_STARTED.md",
        
        # Specifications
        'spec_v4': f"{GITHUB_REPO}/blob/main/Chat_Censor_Tool_PRODUCTION_SPEC_v4.md",
        'spec_v5': f"{GITHUB_REPO}/blob/main/PRODUCTION_SPEC_v5_FINAL.md",
        'quick_reference': f"{GITHUB_REPO}/blob/main/PRODUCTION_SPEC_v5_QUICK_REFERENCE.md",
        
        # GitHub resources
        'releases': f"{GITHUB_REPO}/releases",
        'latest_release': f"{GITHUB_REPO}/releases/latest",
        'issues': f"{GITHUB_REPO}/issues",
        'new_issue': f"{GITHUB_REPO}/issues/new",
        
        # Wiki (if available)
        'wiki': f"{GITHUB_REPO}/wiki",

        # Ko-fi page
        'kofi': f"{KOFI_LINK}",
        
        # Usage guides
        'whitelist_guide': f"{GITHUB_REPO}/blob/main/docs/WHITELIST_GUIDE.md",
        'optimization_guide': f"{GITHUB_REPO}/blob/main/docs/OPTIMIZATION_GUIDE.md",
        'troubleshooting': f"{GITHUB_REPO}/blob/main/docs/TROUBLESHOOTING.md",
    }
    
    def __init__(self, config: dict):
        """
        Initialize help manager
        
        Args:
            config: Application configuration dict
        """
        self.config = config
        self.available = PYQT5_AVAILABLE
        
        if not PYQT5_AVAILABLE:
            print("[HELP] Help manager disabled - PyQt5 not available")
    
    def open_url(self, url_key: str) -> bool:
        """
        Open a help URL in default browser
        
        Args:
            url_key: Key from URLS dict (e.g., 'readme', 'documentation')
            
        Returns:
            True if URL opened successfully, False otherwise
        """
        if not self.available:
            print(f"[HELP] Cannot open URL - PyQt5 not available")
            return False
        
        if url_key not in self.URLS:
            print(f"[HELP] Unknown URL key: {url_key}")
            return False
        
        url = self.URLS[url_key]
        
        try:
            print(f"[HELP] Opening URL: {url}")
            QDesktopServices.openUrl(QUrl(url))
            return True
        
        except Exception as e:
            print(f"[HELP] Failed to open URL: {e}")
            return False
    
    def open_custom_url(self, url: str) -> bool:
        """
        Open a custom URL (not in predefined URLs)
        
        Args:
            url: Full URL to open
            
        Returns:
            True if URL opened successfully, False otherwise
        """
        if not self.available:
            print(f"[HELP] Cannot open URL - PyQt5 not available")
            return False
        
        try:
            print(f"[HELP] Opening custom URL: {url}")
            QDesktopServices.openUrl(QUrl(url))
            return True
        
        except Exception as e:
            print(f"[HELP] Failed to open custom URL: {e}")
            return False
    
    def get_url(self, url_key: str) -> Optional[str]:
        """
        Get URL without opening it
        
        Args:
            url_key: Key from URLS dict
            
        Returns:
            URL string or None if key not found
        """
        return self.URLS.get(url_key)
    
    def get_all_urls(self) -> Dict[str, str]:
        """
        Get all available URLs
        
        Returns:
            Dictionary of all URLs
        """
        return self.URLS.copy()
    
    # Convenience methods for common actions
    
    def open_readme(self) -> bool:
        """Open main README"""
        return self.open_url('readme')
    
    def open_documentation(self) -> bool:
        """Open main documentation"""
        return self.open_url('documentation')
    
    def open_getting_started(self) -> bool:
        """Open getting started guide"""
        return self.open_url('getting_started')
    
    def open_latest_release(self) -> bool:
        """Open latest release page"""
        return self.open_url('latest_release')
    
    def open_issues(self) -> bool:
        """Open issues page"""
        return self.open_url('issues')
    
    def report_bug(self) -> bool:
        """Open new issue page for bug reporting"""
        return self.open_url('new_issue')
    
    def open_whitelist_guide(self) -> bool:
        """Open whitelist configuration guide"""
        return self.open_url('whitelist_guide')
    
    def open_optimization_guide(self) -> bool:
        """Open optimization techniques guide"""
        return self.open_url('optimization_guide')
    
    def open_troubleshooting(self) -> bool:
        """Open troubleshooting guide"""
        return self.open_url('troubleshooting')
    
    def open_kofi(self) -> bool:
        """Open Ko-Fi page"""
        return self.open_url('kofi')
    
    @staticmethod
    def is_available() -> bool:
        """Check if help manager is available (PyQt5 installed)"""
        return PYQT5_AVAILABLE
    
    @staticmethod
    def get_github_repo() -> str:
        """Get GitHub repository URL"""
        return HelpManager.GITHUB_REPO


# Help text for common questions (can be shown in dialogs)
HELP_TEXTS = {
    'whitelist': """
What is the Whitelist?

The whitelist contains words that are SAFE when embedded in other words.

Examples:
- "ass" in whitelist -> "assassin" and "class" are NOT flagged
- "ass" standalone -> Still flagged ("my ass")

Use this to prevent false positives for common patterns.
""",
    
    'optimization': """
Optimization Techniques:

1. Leet-speak: Replaces letters with numbers (e -> 3, a -> 4)
2. Fancy Unicode: Uses special characters (𝓯𝓾𝓬𝓴)
3. Special Char: Inserts hearts between letters (f❤uck)
4. Shorthand: Abbreviates words (you -> u)

Enable/disable in Settings -> Optimization tab.
""",
    
    'detection_modes': """
Detection Modes:

Manual Mode:
- Shows prompt with detected words
- User chooses to use optimization or cancel
- Full control over what gets sent

Auto Mode:
- Automatically optimizes and sends
- Silent operation
- Faster workflow
""",
    
    'filter_file': """
Filter File:

A text file containing filtered words (one per line).
Typically 77,000+ entries.

The tool detects these words and optimizes them before sending.

Get filter files from game communities or create your own.
""",
}


def get_help_text(topic: str) -> Optional[str]:
    """
    Get help text for a topic
    
    Args:
        topic: Topic key (e.g., 'whitelist', 'optimization')
        
    Returns:
        Help text or None if topic not found
    """
    return HELP_TEXTS.get(topic)
