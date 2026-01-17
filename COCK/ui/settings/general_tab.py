#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
General Settings Tab
====================
Filter file, mode, hotkey, and update settings

Creates:
- dialog.filter_path_label
- dialog.mode_combo
- dialog.hotkey_recorder
- dialog.force_hotkey_recorder
- dialog.toggle_hotkey_recorder
- dialog.byte_limit_spin
- dialog.char_limit_spin
- dialog.check_updates_cb
- dialog.last_check_label
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QComboBox, QSpinBox, QCheckBox
)

from ..widgets.hotkey_recorder import HotkeyRecorder


def create_general_tab(dialog):
    """
    Create General settings tab

    Args:
        dialog: SettingsDialog instance

    Returns:
        QWidget: The general tab widget
    """
    widget = QWidget()
    layout = QVBoxLayout()

    # Filter file selection
    filter_group = QGroupBox("Filter Word List")
    filter_layout = QVBoxLayout()

    dialog.filter_path_label = QLabel(dialog.config.get('filter_file', 'Not selected'))
    dialog.filter_path_label.setWordWrap(True)
    filter_layout.addWidget(QLabel("Current filter file:"))
    filter_layout.addWidget(dialog.filter_path_label)

    browse_btn = QPushButton("Browse for Filter File...")
    browse_btn.clicked.connect(dialog.browse_filter_file)
    filter_layout.addWidget(browse_btn)

    # Stats display
    if dialog.filter_stats:
        stats_text = QLabel(
            f"Loaded entries: {dialog.filter_stats.get('final_count', 0)}\n"
            f"Load time: {dialog.filter_stats.get('load_time_ms', 0):.0f}ms"
        )
        filter_layout.addWidget(stats_text)

    filter_group.setLayout(filter_layout)
    layout.addWidget(filter_group)

    # Detection mode
    mode_group = QGroupBox("Detection Mode")
    mode_layout = QVBoxLayout()

    dialog.mode_combo = QComboBox()
    dialog.mode_combo.addItems(["manual", "auto"])
    current_mode = dialog.config.get('detection_mode', 'manual')
    dialog.mode_combo.setCurrentText(current_mode)
    mode_layout.addWidget(QLabel("Mode:"))
    mode_layout.addWidget(dialog.mode_combo)

    mode_desc = QLabel(
        "Manual: User reviews each detection and chooses action\n"
        "Auto: Automatic optimization and sending, no prompts"
    )
    mode_desc.setWordWrap(True)
    mode_layout.addWidget(mode_desc)

    mode_group.setLayout(mode_layout)
    layout.addWidget(mode_group)

    # Hotkey
    hotkey_group = QGroupBox("Hotkeys")
    hotkey_layout = QVBoxLayout()

    # Normal hotkey
    hotkey_layout.addWidget(QLabel("Normal Optimize Hotkey:"))
    dialog.hotkey_recorder = HotkeyRecorder(dialog.config.get('hotkey', 'F12'))
    hotkey_layout.addWidget(dialog.hotkey_recorder)

    # Force optimize hotkey
    hotkey_layout.addWidget(QLabel("Force Optimize Hotkey:"))
    dialog.force_hotkey_recorder = HotkeyRecorder(dialog.config.get('force_optimize_hotkey', 'Ctrl+F12'))
    hotkey_layout.addWidget(dialog.force_hotkey_recorder)

    # Toggle hotkeys hotkey
    hotkey_layout.addWidget(QLabel("Toggle Hotkeys On/Off:"))
    toggle_hotkey_combo = dialog.config.get('toggle_hotkeys_hotkey', 'Ctrl+Shift+H')
    if isinstance(toggle_hotkey_combo, dict):
        toggle_hotkey_combo = toggle_hotkey_combo.get('combo', 'Ctrl+Shift+H')
    dialog.toggle_hotkey_recorder = HotkeyRecorder(toggle_hotkey_combo)
    hotkey_layout.addWidget(dialog.toggle_hotkey_recorder)

    hotkey_layout.addWidget(QLabel(""))  # Spacer
    hotkey_layout.addWidget(QLabel(
        "Tip: Click 'Record...' button, then press your desired key combination.\n"
        "Supports Ctrl, Shift, Alt modifiers and most keys including function keys."
    ))
    hotkey_layout.addWidget(QLabel(
        "Note: If Force Optimize doesn't capture text, avoid using Shift\n"
        "(e.g., use ctrl+f12 instead of shift+f12)"
    ))

    hotkey_group.setLayout(hotkey_layout)
    layout.addWidget(hotkey_group)

    # Message Limits
    limits_group = QGroupBox("Message Limits")
    limits_layout = QVBoxLayout()

    limits_layout.addWidget(QLabel("Set to 0 for no limits"))

    # Byte limit
    byte_layout = QHBoxLayout()
    byte_label = QLabel("Byte limit:")
    byte_label.setFixedWidth(100)
    byte_layout.addWidget(byte_label)
    dialog.byte_limit_spin = QSpinBox()
    dialog.byte_limit_spin.setMinimum(0)
    dialog.byte_limit_spin.setMaximum(9999)
    dialog.byte_limit_spin.setValue(dialog.config.get('byte_limit', 92))
    byte_layout.addWidget(dialog.byte_limit_spin)
    byte_layout.addStretch()
    limits_layout.addLayout(byte_layout)

    # Character limit
    char_layout = QHBoxLayout()
    char_label = QLabel("Character limit:")
    char_label.setFixedWidth(100)
    char_layout.addWidget(char_label)
    dialog.char_limit_spin = QSpinBox()
    dialog.char_limit_spin.setMinimum(0)
    dialog.char_limit_spin.setMaximum(9999)
    dialog.char_limit_spin.setValue(dialog.config.get('character_limit', 80))
    char_layout.addWidget(dialog.char_limit_spin)
    char_layout.addStretch()
    limits_layout.addLayout(char_layout)

    limits_group.setLayout(limits_layout)
    layout.addWidget(limits_group)

    # Data folder button
    data_btn = QPushButton("Open Data Folder")
    data_btn.clicked.connect(dialog.open_data_folder)
    layout.addWidget(data_btn)

    # Update settings group
    update_group = QGroupBox("Updates")
    update_layout = QVBoxLayout()

    # Check for updates checkbox
    dialog.check_updates_cb = QCheckBox("Check for updates at startup")
    dialog.check_updates_cb.setChecked(
        dialog.config.get('updates', {}).get('check_enabled', True)
    )
    dialog.check_updates_cb.setToolTip(
        "Automatically check for new versions when the application starts"
    )

    # Last check info
    last_check = None
    if hasattr(getattr(dialog, "main_app", None), 'update_checker'):
        try:
            last_check = getattr(dialog, "main_app", None).update_checker.get_last_check_time()
        except:
            pass

    last_check_text = f"Last checked: {last_check}" if last_check else "Never checked"
    dialog.last_check_label = QLabel(last_check_text)
    dialog.last_check_label.setStyleSheet("color: gray; font-size: 9pt;")

    # Check now button
    check_now_btn = QPushButton("Check Now")
    check_now_btn.clicked.connect(dialog._check_updates_now)
    check_now_btn.setToolTip("Check for updates immediately")

    # View releases button
    releases_btn = QPushButton("View Releases")
    releases_btn.clicked.connect(lambda: dialog._open_help('releases'))
    releases_btn.setToolTip("View all releases on GitHub")

    # Button layout
    button_layout = QHBoxLayout()
    button_layout.addWidget(check_now_btn)
    button_layout.addWidget(releases_btn)
    button_layout.addStretch()

    update_layout.addWidget(dialog.check_updates_cb)
    update_layout.addWidget(dialog.last_check_label)
    update_layout.addLayout(button_layout)
    update_group.setLayout(update_layout)
    layout.addWidget(update_group)

    layout.addStretch()
    widget.setLayout(layout)
    return widget


def validate_hotkeys(dialog):
    """
    Check for hotkey conflicts before saving

    Args:
        dialog: SettingsDialog instance

    Returns:
        bool: True if valid, False if conflicts exist
    """
    from PyQt5.QtWidgets import QMessageBox

    # Get hotkeys from both recorders
    normal_hotkey = dialog.hotkey_recorder.get_hotkey()
    force_hotkey = dialog.force_hotkey_recorder.get_hotkey()

    # Check if both hotkeys are the same (and not empty)
    if normal_hotkey and force_hotkey and normal_hotkey.lower() == force_hotkey.lower():
        QMessageBox.warning(
            dialog,
            "Hotkey Conflict",
            f"Normal optimize and Force optimize cannot use the same hotkey!\n\n"
            f"Both are set to: {normal_hotkey}\n\n"
            f"Please choose different hotkeys.",
            QMessageBox.Ok
        )
        return False

    return True
