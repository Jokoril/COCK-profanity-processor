#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whitelist Settings Tab
======================
Whitelist management for embedding protection

Creates:
- dialog.whitelist_search
- dialog.whitelist_list
- dialog.whitelist_count_label
- dialog.all_whitelist_words
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit,
    QListWidget, QInputDialog, QMessageBox
)


def create_whitelist_tab(dialog):
    """
    Create Whitelist management tab

    Args:
        dialog: SettingsDialog instance

    Returns:
        QWidget: The whitelist tab widget
    """
    widget = QWidget()
    layout = QVBoxLayout()

    # Info label with clear explanation
    info_label = QLabel(
        "Manage words that are SAFE when embedded in other words.\n\n"
        "• Whitelisted words are NOT flagged when embedded (e.g., 'ass' in 'assassin')\n"
        "• Standalone instances ARE STILL flagged (e.g., 'ass' by itself)\n"
        "• Use this to prevent false positives for common embedded patterns\n\n"
        "Changes are saved to whitelist.txt when you click Save."
    )
    info_label.setWordWrap(True)
    layout.addWidget(info_label)

    # Search bar
    search_layout = QHBoxLayout()
    search_layout.addWidget(QLabel("Search:"))

    dialog.whitelist_search = QLineEdit()
    dialog.whitelist_search.setPlaceholderText("Type to filter list...")
    dialog.whitelist_search.textChanged.connect(lambda text: whitelist_search_changed(dialog, text))
    search_layout.addWidget(dialog.whitelist_search)

    layout.addLayout(search_layout)

    # Whitelist (scrollable)
    dialog.whitelist_list = QListWidget()
    dialog.whitelist_list.setSelectionMode(QListWidget.ExtendedSelection)
    dialog.whitelist_list.setSortingEnabled(True)
    layout.addWidget(dialog.whitelist_list)

    # Entry count label (create BEFORE loading)
    dialog.whitelist_count_label = QLabel("Loading...")
    layout.addWidget(dialog.whitelist_count_label)

    # Load whitelist entries (after label exists)
    dialog.all_whitelist_words = []
    load_whitelist_entries(dialog)

    # Button panel
    btn_layout = QHBoxLayout()

    add_btn = QPushButton("Add Entry...")
    add_btn.clicked.connect(lambda: add_whitelist_entry(dialog))
    btn_layout.addWidget(add_btn)

    remove_btn = QPushButton("Remove Selected")
    remove_btn.clicked.connect(lambda: remove_whitelist_entries(dialog))
    btn_layout.addWidget(remove_btn)

    layout.addLayout(btn_layout)

    widget.setLayout(layout)
    return widget


def load_whitelist_entries(dialog):
    """Load whitelist entries from file"""
    # Get whitelist file path
    import path_manager
    whitelist_file = path_manager.get_data_file('whitelist.txt')

    if not os.path.exists(whitelist_file):
        dialog.whitelist_list.addItem("(No whitelist file found)")
        return

    try:
        with open(whitelist_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Parse whitelist words (skip comments and empty lines)
        dialog.all_whitelist_words = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                dialog.all_whitelist_words.append(line)

        # Display all words initially
        update_whitelist_display(dialog)

    except Exception as e:
        dialog.whitelist_list.addItem(f"Error loading whitelist: {e}")


def update_whitelist_display(dialog, search_text=""):
    """Update whitelist display based on search"""
    dialog.whitelist_list.clear()

    # Filter words based on search
    if search_text:
        filtered_words = [w for w in dialog.all_whitelist_words if search_text.lower() in w.lower()]
    else:
        filtered_words = dialog.all_whitelist_words

    # Add to list
    for word in sorted(filtered_words):
        dialog.whitelist_list.addItem(word)

    # Update count
    dialog.whitelist_count_label.setText(
        f"Showing {len(filtered_words)} of {len(dialog.all_whitelist_words)} entries"
    )


def whitelist_search_changed(dialog, text):
    """Handle whitelist search text change"""
    update_whitelist_display(dialog, text)


def add_whitelist_entry(dialog):
    """Add new entry to whitelist"""
    text, ok = QInputDialog.getText(
        dialog,
        "Add Whitelist Entry",
        "Enter word that is safe when embedded:\n"
        "(Will NOT be flagged when embedded, but WILL be flagged standalone)"
    )

    if ok and text:
        text = text.strip().lower()

        if not text:
            return

        if text in dialog.all_whitelist_words:
            QMessageBox.information(
                dialog,
                "Already Exists",
                f"'{text}' is already in the whitelist."
            )
            return

        # Add to list
        dialog.all_whitelist_words.append(text)
        update_whitelist_display(dialog, dialog.whitelist_search.text())

        QMessageBox.information(
            dialog,
            "Entry Added",
            f"'{text}' added to whitelist.\n\n"
            "This word will NOT be flagged when embedded in other words,\n"
            "but WILL still be flagged when standalone.\n\n"
            "Click Save to apply changes."
        )


def remove_whitelist_entries(dialog):
    """Remove selected entries from whitelist"""
    selected_items = dialog.whitelist_list.selectedItems()

    if not selected_items:
        QMessageBox.information(
            dialog,
            "No Selection",
            "Please select one or more entries to remove."
        )
        return

    # Confirm removal
    count = len(selected_items)
    reply = QMessageBox.question(
        dialog,
        "Confirm Removal",
        f"Remove {count} selected {'entry' if count == 1 else 'entries'} from whitelist?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )

    if reply == QMessageBox.Yes:
        # Remove from all_whitelist_words
        for item in selected_items:
            word = item.text()
            if word in dialog.all_whitelist_words:
                dialog.all_whitelist_words.remove(word)

        # Update display
        update_whitelist_display(dialog, dialog.whitelist_search.text())

        QMessageBox.information(
            dialog,
            "Entries Removed",
            f"{count} {'entry' if count == 1 else 'entries'} removed.\n\nClick Save to apply changes."
        )
