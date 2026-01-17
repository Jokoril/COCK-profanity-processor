#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimization Settings Tab
=========================
Leet-speak, unicode, shorthand, special char settings

Creates:
- dialog.leet_enabled
- dialog.unicode_enabled
- dialog.shorthand_enabled
- dialog.link_protection
- dialog.special_char_enabled
- dialog.special_char_input
- dialog.fancy_style_combo
- dialog.sliding_window_spin
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QCheckBox, QComboBox, QSpinBox, QLineEdit
)


def create_optimization_tab(dialog):
    """
    Create Optimization settings tab

    Args:
        dialog: SettingsDialog instance

    Returns:
        QWidget: The optimization tab widget
    """
    widget = QWidget()
    layout = QVBoxLayout()

    # Leet-speak
    leet_group = QGroupBox("Leet-Speak")
    leet_layout = QVBoxLayout()

    dialog.leet_enabled = QCheckBox("Enable leet-speak optimization")
    leet_enabled = dialog.config.get('optimization', {}).get('leet_speak', True)
    dialog.leet_enabled.setChecked(leet_enabled)
    leet_layout.addWidget(dialog.leet_enabled)

    leet_desc = QLabel("Convert characters (e.g., 'hello' → 'h3ll0')\n0 byte overhead")
    leet_desc.setWordWrap(True)
    leet_layout.addWidget(leet_desc)

    leet_group.setLayout(leet_layout)
    layout.addWidget(leet_group)

    # Fancy Unicode
    unicode_group = QGroupBox("Fancy Unicode")
    unicode_layout = QVBoxLayout()

    dialog.unicode_enabled = QCheckBox("Enable Unicode optimization")
    unicode_enabled = dialog.config.get('optimization', {}).get('fancy_unicode', True)
    dialog.unicode_enabled.setChecked(unicode_enabled)
    unicode_layout.addWidget(dialog.unicode_enabled)

    unicode_desc = QLabel("Use Fancy Text (e.g., 'hello' → '🄷🄴🄻🄻🄾')\n+3 bytes per character")
    unicode_desc.setWordWrap(True)
    unicode_layout.addWidget(unicode_desc)

    unicode_group.setLayout(unicode_layout)
    layout.addWidget(unicode_group)

    # Shorthand
    shorthand_group = QGroupBox("Shorthand")
    shorthand_layout = QVBoxLayout()

    dialog.shorthand_enabled = QCheckBox("Enable shorthand compression")
    shorthand_enabled = dialog.config.get('optimization', {}).get('shorthand', True)
    dialog.shorthand_enabled.setChecked(shorthand_enabled)
    shorthand_layout.addWidget(dialog.shorthand_enabled)

    shorthand_desc = QLabel("Abbreviate words (e.g., 'everyone' → 'every1')\nSaves bytes")
    shorthand_desc.setWordWrap(True)
    shorthand_layout.addWidget(shorthand_desc)

    shorthand_group.setLayout(shorthand_layout)
    layout.addWidget(shorthand_group)

    # Link protection
    link_group = QGroupBox("Link Protection")
    link_layout = QVBoxLayout()

    dialog.link_protection = QCheckBox("Protect URLs from modification")
    link_enabled = dialog.config.get('optimization', {}).get('link_protection', True)
    dialog.link_protection.setChecked(link_enabled)
    link_layout.addWidget(dialog.link_protection)

    link_group.setLayout(link_layout)
    layout.addWidget(link_group)

    # Special Character Interspacing
    special_char_group = QGroupBox("Special Character Interspacing")
    special_char_layout = QVBoxLayout()

    dialog.special_char_enabled = QCheckBox("Enable special character interspacing (replaces leet/fancy)")
    special_char_enabled = dialog.config.get('optimization', {}).get('special_char_interspacing', False)
    dialog.special_char_enabled.setChecked(special_char_enabled)
    special_char_layout.addWidget(dialog.special_char_enabled)

    special_char_desc = QLabel(
        "Inserts invisible/special character to break pattern detection.\n"
        "Adds an invisible character that your game recognizes and does not strip to break up word patterns\n"
        "Characters are 'invisible' when the game's font does not support them\n"
        "+1 char, +2-3 bytes per insertion"
    )
    special_char_desc.setWordWrap(True)
    special_char_layout.addWidget(special_char_desc)

    # Character input field
    char_input_layout = QHBoxLayout()
    char_input_layout.addWidget(QLabel("Character:"))

    dialog.special_char_input = QLineEdit()
    dialog.special_char_input.setMaxLength(1)
    dialog.special_char_input.setFixedWidth(50)
    current_char = dialog.config.get('special_char_interspacing', {}).get('character', '❤')
    dialog.special_char_input.setText(current_char)
    char_input_layout.addWidget(dialog.special_char_input)

    # Default button
    default_btn = QPushButton("Reset to ❤")
    default_btn.clicked.connect(lambda: dialog.special_char_input.setText('❤'))
    char_input_layout.addWidget(default_btn)

    char_input_layout.addStretch()
    special_char_layout.addLayout(char_input_layout)

    # Info label
    info_label = QLabel(
        "⚠️ Test your character in-game first!\n"
        "Some symbols may be visible or stripped by the game."
    )
    info_label.setWordWrap(True)
    info_label.setStyleSheet("color: red;")
    special_char_layout.addWidget(info_label)

    special_char_group.setLayout(special_char_layout)
    layout.addWidget(special_char_group)

    # Fancy Text Style
    style_group = QGroupBox("Fancy Text Style")
    style_layout = QVBoxLayout()

    style_layout.addWidget(QLabel("Unicode style for fancy text:"))

    dialog.fancy_style_combo = QComboBox()
    styles = ['squared', 'bold', 'italic', 'bold_italic', 'sans_serif', 'circled', 'negative_squared', 'negative_circled']
    style_names = {
        'squared': 'Squared (🄰🄱🄲)',
        'bold': 'Bold (𝐀𝐁𝐂)',
        'italic': 'Italic (𝐴𝐵𝐶)',
        'bold_italic': 'Bold Italic (𝑨𝑩𝑪)',
        'sans_serif': 'Sans Serif (𝖠𝖡𝖢)',
        'circled': 'Circled (Ⓐ Ⓑ Ⓒ)',
        'negative_squared': 'Negative Squared (🅰🅱🅲)',
        'negative_circled': 'Negative Circled (🅐🅑🅒)'
    }

    for style in styles:
        dialog.fancy_style_combo.addItem(style_names[style], style)

    current_style = dialog.config.get('optimization', {}).get('fancy_text_style', 'squared')
    index = dialog.fancy_style_combo.findData(current_style)
    if index >= 0:
        dialog.fancy_style_combo.setCurrentIndex(index)

    style_layout.addWidget(dialog.fancy_style_combo)

    # Info label
    style_info_label = QLabel(
        "⚠️ Test your chosen style!\n"
        "Some styles may be unsupported or stripped by the game."
    )
    style_info_label.setWordWrap(True)
    style_info_label.setStyleSheet("color: red;")
    style_layout.addWidget(style_info_label)

    style_group.setLayout(style_layout)
    layout.addWidget(style_group)

    # Sliding Window Detection
    window_group = QGroupBox("Sliding Window Detection")
    window_layout = QVBoxLayout()

    window_layout.addWidget(QLabel("Maximum sliding window size (2-5 words):"))

    dialog.sliding_window_spin = QSpinBox()
    dialog.sliding_window_spin.setMinimum(2)
    dialog.sliding_window_spin.setMaximum(5)
    dialog.sliding_window_spin.setValue(dialog.config.get('max_sliding_window', 3))
    window_layout.addWidget(dialog.sliding_window_spin)

    window_desc = QLabel(
        "Detects filtered words split across multiple words.\n"
        "Example: 'in fo' contains 'info' (2-word window)\n"
        "Higher values = more detection, slower performance"
    )
    window_desc.setWordWrap(True)
    window_layout.addWidget(window_desc)

    window_group.setLayout(window_layout)
    layout.addWidget(window_group)

    layout.addStretch()
    widget.setLayout(layout)
    return widget
