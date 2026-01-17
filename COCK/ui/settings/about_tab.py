#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
About Settings Tab
==================
Version info, documentation links, and credits

Creates:
- (no dialog attributes - purely informational tab)
"""

import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QTextEdit, QMessageBox, QFileDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from logger import get_logger

log = get_logger(__name__)


def create_about_tab(dialog):
    """
    Create About tab

    Args:
        dialog: SettingsDialog instance

    Returns:
        QWidget: The about tab widget
    """
    widget = QWidget()
    layout = QVBoxLayout()

    # Title
    title = QLabel("Compliant Online Chat Kit")
    title_font = QFont()
    title_font.setPointSize(16)
    title_font.setBold(True)
    title.setFont(title_font)
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    # Version
    version = QLabel("Version 1.0")
    version.setAlignment(Qt.AlignCenter)
    layout.addWidget(version)

    # Description
    desc = QTextEdit()
    desc_font = QFont()
    desc_font.setPointSize(12)
    desc.setFont(desc_font)
    desc.setReadOnly(True)
    desc.setMaximumHeight(600)
    desc.setHtml(
        "<b>COCK helps you resolve over-sensitive game chat censorship by:</b><br><br>"
        "• Detecting filtered words before you send messages<br>"
        "• Suggesting & replacing filtered words with optimized alternatives<br>"
        "• Splitting long messages into parts base on in-game chat length and byte size limits<br>"
        "• Simplified one-keypress operation<br>"
        "<br>"
        "<b>FEATURES:</b><br>"
        "<br>"
        "• Efficient and fast Aho-Corasick string matching algorithm (&lt;5ms per message)<br>"
        "• Multi-stage optimization (leet-speak, fancy text, invisible character interspacing, shorthand, message splitting)<br>"
        "• Manual & Automatic modes<br>"
        "• Completely offline and external operation, safe for online games<br>"
        "<br>"
        "<b>DISCLAIMER:</b><br>"
        "<br>"
        "By using this application, you acknowledge:<br>"
        "<br>"
        "• You are resposible for the content of your own online communications <br>"
        "• The author is not liable for any consequences resulting from abuse of the tool"
    )
    layout.addWidget(desc)

    # Resources group
    help_group = QGroupBox("Resources")
    help_layout = QVBoxLayout()

    # Help text
    help_text = QLabel("Links and documentation:")
    help_text.setWordWrap(True)
    help_layout.addWidget(help_text)

    # Button layout (horizontal)
    button_layout = QHBoxLayout()

    # Documentation button
    docs_btn = QPushButton("Documentation")
    docs_btn.setToolTip("Open documentation on GitHub")
    docs_btn.clicked.connect(lambda: open_help(dialog, 'documentation'))

    # Getting Started button
    start_btn = QPushButton("Getting Started")
    start_btn.setToolTip("Quick start guide")
    start_btn.clicked.connect(lambda: open_help(dialog, 'getting_started'))

    # Ko-fi button
    kofi_btn = QPushButton("Buy me a coffee")
    kofi_btn.setToolTip("Fuel my caffeine addiction")
    kofi_btn.clicked.connect(lambda: open_help(dialog, 'kofi'))

    # Report Issue button
    issue_btn = QPushButton("Feedback")
    issue_btn.setToolTip("Report a bug or request a feature")
    issue_btn.clicked.connect(lambda: open_help(dialog, 'new_issue'))

    button_layout.addWidget(docs_btn)
    button_layout.addWidget(start_btn)
    button_layout.addWidget(kofi_btn)
    button_layout.addWidget(issue_btn)

    help_layout.addLayout(button_layout)
    help_group.setLayout(help_layout)
    layout.addWidget(help_group)

    # Credits
    credits = QLabel("Author: Jokoril")
    credits.setAlignment(Qt.AlignCenter)
    layout.addWidget(credits)

    layout.addStretch()
    widget.setLayout(layout)
    return widget


def open_help(dialog, help_key: str):
    """
    Open help resource

    Args:
        dialog: SettingsDialog instance
        help_key: Key for help URL (e.g., 'documentation', 'faq')
    """
    try:
        # Get help manager from parent (main application)
        if hasattr(getattr(dialog, "main_app", None), 'help_manager'):
            success = getattr(dialog, "main_app", None).help_manager.open_url(help_key)
            if success:
                log.debug(f"Opened help: {help_key}")
            else:
                log.warning(f"Failed to open help: {help_key}")
        else:
            log.warning("Help manager not available")
            try:
                import help_manager
                QMessageBox.warning(
                    dialog,
                    "Help Unavailable",
                    "Help system is not available.\n\n"
                    f"Please visit: {help_manager.HelpManager.GITHUB_REPO}"
                )
            except:
                QMessageBox.warning(
                    dialog,
                    "Help Unavailable",
                    "Help system is not available."
                )
    except Exception as e:
        log.error(f"Error opening help: {e}")


def browse_filter_file(dialog):
    """
    Browse for filter file

    Args:
        dialog: SettingsDialog instance
    """
    file_path, _ = QFileDialog.getOpenFileName(
        dialog,
        "Select Filter Word List",
        "",
        "Text Files (*.txt);;All Files (*)"
    )

    if file_path:
        # Validate the path
        try:
            if not os.path.exists(file_path):
                QMessageBox.warning(dialog, "Invalid File", "Selected file does not exist")
                return
            if not os.path.isfile(file_path):
                QMessageBox.warning(dialog, "Invalid File", "Selected path is not a file")
                return
            with open(file_path, 'r', encoding='utf-8') as test_file:
                test_file.read(100)
            file_path = os.path.abspath(file_path)
        except PermissionError:
            QMessageBox.warning(dialog, "Permission Denied", "Cannot read selected file")
            return
        except Exception as e:
            QMessageBox.warning(dialog, "Error", f"Invalid file: {str(e)}")
            return

        dialog.config['filter_file'] = file_path
        dialog.filter_path_label.setText(file_path)

        # Mark that filter file was changed (will trigger auto-restart)
        if file_path != dialog.original_filter_file:
            dialog.filter_file_changed = True


def open_data_folder(dialog):
    """
    Open data folder in file explorer

    Args:
        dialog: SettingsDialog instance (unused but kept for consistency)
    """
    # Get app directory
    if sys.platform == 'win32':
        data_dir = os.path.join(os.getenv('APPDATA'), 'CompliantOnlineChatKit')
    else:
        data_dir = os.path.expanduser('~/.CompliantOnlineChatKit')

    # Create if doesn't exist
    os.makedirs(data_dir, exist_ok=True)

    # Open in file explorer
    if sys.platform == 'win32':
        subprocess.Popen(['explorer', data_dir])
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', data_dir])
    else:
        subprocess.Popen(['xdg-open', data_dir])
