#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filter List Settings Tab
========================
Filter word list management

Creates:
- dialog.filter_show_unsupported
- dialog.filter_search
- dialog.filter_list
- dialog.filter_count_label
- dialog.all_filter_words
- dialog.all_filter_words_original
- dialog.all_filter_words_supported
- dialog._filter_modified
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QLineEdit,
    QListWidget, QInputDialog, QMessageBox, QFileDialog
)


def create_filter_tab(dialog):
    """
    Create Filter List management tab

    Args:
        dialog: SettingsDialog instance

    Returns:
        QWidget: The filter tab widget
    """
    widget = QWidget()
    layout = QVBoxLayout()

    # Info label
    info_label = QLabel(
        "Manage your filter word list. Add or remove entries, search, and export.\n"
        "Note: Changes are saved to the filter file when you click Save."
    )
    info_label.setWordWrap(True)
    layout.addWidget(info_label)

    # Toggle for displaying unsupported strings
    dialog.filter_show_unsupported = QCheckBox("Display unsupported strings (non-Latin/CJK)")
    dialog.filter_show_unsupported.setChecked(False)  # Default to showing supported only
    dialog.filter_show_unsupported.toggled.connect(lambda checked: toggle_filter_display(dialog, checked))
    layout.addWidget(dialog.filter_show_unsupported)

    layout.addWidget(QLabel(""))  # Spacer

    # Search bar
    search_layout = QHBoxLayout()
    search_layout.addWidget(QLabel("Search:"))

    dialog.filter_search = QLineEdit()
    dialog.filter_search.setPlaceholderText("Type to filter list...")
    dialog.filter_search.textChanged.connect(lambda text: filter_search_changed(dialog, text))
    search_layout.addWidget(dialog.filter_search)

    layout.addLayout(search_layout)

    # Filter list (scrollable)
    dialog.filter_list = QListWidget()
    dialog.filter_list.setSelectionMode(QListWidget.ExtendedSelection)
    dialog.filter_list.setSortingEnabled(True)
    layout.addWidget(dialog.filter_list)

    # Entry count label (create BEFORE loading)
    dialog.filter_count_label = QLabel("Loading...")
    layout.addWidget(dialog.filter_count_label)

    # Load filter entries (after label exists)
    dialog.all_filter_words = []
    load_filter_entries(dialog)

    # Button panel
    btn_layout = QHBoxLayout()

    add_btn = QPushButton("Add Entry...")
    add_btn.clicked.connect(lambda: add_filter_entry(dialog))
    btn_layout.addWidget(add_btn)

    remove_btn = QPushButton("Remove Selected")
    remove_btn.clicked.connect(lambda: remove_filter_entries(dialog))
    btn_layout.addWidget(remove_btn)

    export_btn = QPushButton("Export List...")
    export_btn.clicked.connect(lambda: export_filter_list(dialog))
    btn_layout.addWidget(export_btn)

    layout.addLayout(btn_layout)

    widget.setLayout(layout)
    return widget


def load_filter_entries(dialog):
    """Load filter entries from config - both original and filtered"""
    # Get filter file path from config
    filter_file = dialog.config.get('filter_file', '')

    if not filter_file or not os.path.exists(filter_file):
        dialog.filter_list.addItem("(No filter file loaded)")
        dialog.all_filter_words_original = []
        dialog.all_filter_words_supported = []
        return

    try:
        with open(filter_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Track if user modifies filter list via UI (v1.2)
        dialog._filter_modified = False

        # Parse ALL filter words (pre-culled - original file)
        dialog.all_filter_words_original = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                dialog.all_filter_words_original.append(line)

        # Filter to Latin-only (post-culled - what's actually used)
        import filter_loader
        loader = filter_loader.FilterLoader()
        dialog.all_filter_words_supported = []
        for word in dialog.all_filter_words_original:
            if loader._is_pure_latin(word):
                dialog.all_filter_words_supported.append(word)

        # For backwards compatibility
        dialog.all_filter_words = dialog.all_filter_words_supported

        # Display based on toggle state
        update_filter_display(dialog)

    except Exception as e:
        dialog.filter_list.addItem(f"Error loading filter file: {e}")
        dialog.all_filter_words_original = []
        dialog.all_filter_words_supported = []


def toggle_filter_display(dialog, checked):
    """Toggle between original and supported filter lists"""
    update_filter_display(dialog, dialog.filter_search.text())


def update_filter_display(dialog, search_text=""):
    """Update filter list display based on search and toggle state"""
    dialog.filter_list.clear()

    # Choose which word list to display
    if hasattr(dialog, 'filter_show_unsupported') and dialog.filter_show_unsupported.isChecked():
        # Show unsupported (original/pre-culled list)
        source_words = dialog.all_filter_words_original
        list_type = "original"
    else:
        # Show supported (filtered/post-culled list) - DEFAULT
        source_words = dialog.all_filter_words_supported
        list_type = "supported (Latin-only)"

    # Filter words based on search
    if search_text:
        filtered_words = [w for w in source_words if search_text.lower() in w.lower()]
    else:
        filtered_words = source_words

    # Add to list
    for word in sorted(filtered_words):
        dialog.filter_list.addItem(word)

    # Update count with list type info
    unsupported_count = len(dialog.all_filter_words_original) - len(dialog.all_filter_words_supported)
    dialog.filter_count_label.setText(
        f"Showing {len(filtered_words)} of {len(source_words)} entries ({list_type})\n"
        f"Total: {len(dialog.all_filter_words_original)} entries "
        f"({len(dialog.all_filter_words_supported)} supported, {unsupported_count} unsupported)"
    )


def filter_search_changed(dialog, text):
    """Handle search text change"""
    update_filter_display(dialog, text)


def add_filter_entry(dialog):
    """Add new entry to filter list"""
    text, ok = QInputDialog.getText(
        dialog,
        "Add Filter Entry",
        "Enter word or phrase to add to filter:"
    )

    if ok and text:
        text = text.strip().lower()

        if not text:
            return

        if text in dialog.all_filter_words_original:
            QMessageBox.information(
                dialog,
                "Already Exists",
                f"'{text}' is already in the filter list."
            )
            return

        # Add to original list
        dialog.all_filter_words_original.append(text)
        dialog._filter_modified = True  # Mark as modified (v1.2)

        # If it's Latin-only, also add to supported list
        import filter_loader
        loader = filter_loader.FilterLoader()
        if loader._is_pure_latin(text):
            dialog.all_filter_words_supported.append(text)

        # Update backwards compatibility
        dialog.all_filter_words = dialog.all_filter_words_supported

        # Update display
        update_filter_display(dialog, dialog.filter_search.text())

        QMessageBox.information(
            dialog,
            "Entry Added",
            f"'{text}' added to filter list.\n\nClick Save to apply changes."
        )


def remove_filter_entries(dialog):
    """Remove selected entries from filter list"""
    selected_items = dialog.filter_list.selectedItems()

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
        f"Remove {count} selected {'entry' if count == 1 else 'entries'}?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )

    if reply == QMessageBox.Yes:
        # Remove from both lists
        for item in selected_items:
            word = item.text()
            if word in dialog.all_filter_words_original:
                dialog.all_filter_words_original.remove(word)
            if word in dialog.all_filter_words_supported:
                dialog.all_filter_words_supported.remove(word)

        dialog._filter_modified = True  # Mark as modified (v1.2)

        # Update backwards compatibility
        dialog.all_filter_words = dialog.all_filter_words_supported

        # Update display
        update_filter_display(dialog, dialog.filter_search.text())

        QMessageBox.information(
            dialog,
            "Entries Removed",
            f"{count} {'entry' if count == 1 else 'entries'} removed.\n\nClick Save to apply changes."
        )


def export_filter_list(dialog):
    """Export filter list to file (respects current display toggle)"""
    # Determine which list to export based on toggle
    if hasattr(dialog, 'filter_show_unsupported') and dialog.filter_show_unsupported.isChecked():
        export_words = dialog.all_filter_words_original
        list_type = "original (all strings)"
    else:
        export_words = dialog.all_filter_words_supported
        list_type = "supported (Latin-only)"

    file_path, _ = QFileDialog.getSaveFileName(
        dialog,
        f"Export Filter List ({list_type})",
        "filter_export.txt",
        "Text Files (*.txt);;All Files (*)"
    )

    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Exported Filter List ({list_type})\n")
                f.write(f"# Total entries: {len(export_words)}\n\n")
                for word in sorted(export_words):
                    f.write(f"{word}\n")

            QMessageBox.information(
                dialog,
                "Export Successful",
                f"Filter list ({list_type}) exported to:\n{file_path}\n\n{len(export_words)} entries exported."
            )
        except Exception as e:
            QMessageBox.critical(
                dialog,
                "Export Failed",
                f"Failed to export filter list:\n{e}"
            )
