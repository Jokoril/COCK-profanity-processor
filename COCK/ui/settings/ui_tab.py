#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Settings Tab
===============
Theme, sound, positioning, and scaling settings

Creates:
- dialog.theme_combo
- dialog.notif_sound_check
- dialog.prompt_sound_check
- dialog.notif_position_combo
- dialog.notif_offset_x_spin
- dialog.notif_offset_y_spin
- dialog.prompt_position_combo
- dialog.prompt_offset_x_spin
- dialog.prompt_offset_y_spin
- dialog.notif_scale_slider
- dialog.notif_scale_label
- dialog.prompt_scale_slider
- dialog.prompt_scale_label
- dialog.settings_scale_slider
- dialog.settings_scale_label
- dialog.notif_enabled
- dialog.notif_show_clean
- dialog.notif_show_optimized
- dialog.popup_duration_spin
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QCheckBox, QSpinBox, QSlider, QDesktopWidget
)
from PyQt5.QtCore import Qt


def create_ui_tab(dialog):
    """
    Create UI settings tab

    Args:
        dialog: SettingsDialog instance

    Returns:
        QWidget: The UI tab widget
    """
    widget = QWidget()
    layout = QVBoxLayout()

    # Theme
    theme_group = QGroupBox("Theme")
    theme_layout = QVBoxLayout()

    dialog.theme_combo = QComboBox()
    dialog.theme_combo.addItems(["dark", "light"])
    current_theme = dialog.config.get('ui', {}).get('theme', 'dark')
    dialog.theme_combo.setCurrentText(current_theme)

    # Connect to instantly apply theme changes
    dialog.theme_combo.currentTextChanged.connect(dialog.on_theme_changed)

    theme_layout.addWidget(QLabel("Color theme:"))
    theme_layout.addWidget(dialog.theme_combo)

    theme_group.setLayout(theme_layout)
    layout.addWidget(theme_group)

    # Sound effects
    sound_group = QGroupBox("Sound Effects")
    sound_layout = QVBoxLayout()

    dialog.notif_sound_check = QCheckBox("Play sound on notifications")
    notif_sound_enabled = dialog.config.get('ui', {}).get('notification_sound', True)
    dialog.notif_sound_check.setChecked(notif_sound_enabled)
    sound_layout.addWidget(dialog.notif_sound_check)

    dialog.prompt_sound_check = QCheckBox("Play sound on prompts")
    prompt_sound_enabled = dialog.config.get('ui', {}).get('prompt_sound', True)
    dialog.prompt_sound_check.setChecked(prompt_sound_enabled)
    sound_layout.addWidget(dialog.prompt_sound_check)

    sound_desc = QLabel("Uses system sounds for audio feedback")
    sound_desc.setWordWrap(True)
    sound_layout.addWidget(sound_desc)

    sound_group.setLayout(sound_layout)
    layout.addWidget(sound_group)

    # Window positioning
    position_group = QGroupBox("Window Positioning")
    position_layout = QVBoxLayout()

    # Notification position preset
    notif_pos_layout = QHBoxLayout()
    notif_pos_label = QLabel("Notification Popups:")
    notif_pos_label.setFixedWidth(150)
    notif_pos_layout.addWidget(notif_pos_label)

    dialog.notif_position_combo = QComboBox()
    dialog.notif_position_combo.addItems([
        "top-left", "top-center", "top-right",
        "center-left", "center", "center-right",
        "bottom-left", "bottom-center", "bottom-right"
    ])
    current_notif_pos = dialog.config.get('ui', {}).get('notification_position', 'bottom-right')
    dialog.notif_position_combo.setCurrentText(current_notif_pos)
    dialog.notif_position_combo.setFixedWidth(170)
    notif_pos_layout.addWidget(dialog.notif_position_combo)
    notif_pos_layout.addStretch()
    position_layout.addLayout(notif_pos_layout)

    # Notification fine-tuning (with dynamic limits based on screen size)
    notif_offset_layout = QHBoxLayout()
    fine_tune_label = QLabel("Fine-tune (X, Y):")
    fine_tune_label.setFixedWidth(150)
    notif_offset_layout.addWidget(fine_tune_label)

    # Get screen dimensions for dynamic limits
    desktop = QDesktopWidget()
    screen_rect = desktop.availableGeometry()
    max_x = screen_rect.width()
    max_y = screen_rect.height()

    dialog.notif_offset_x_spin = QSpinBox()
    dialog.notif_offset_x_spin.setRange(-max_x, max_x)
    dialog.notif_offset_x_spin.setValue(dialog.config.get('ui', {}).get('notification_offset_x', 20))
    dialog.notif_offset_x_spin.setSuffix(" px")
    notif_offset_layout.addWidget(dialog.notif_offset_x_spin)

    dialog.notif_offset_y_spin = QSpinBox()
    dialog.notif_offset_y_spin.setRange(-max_y, max_y)
    dialog.notif_offset_y_spin.setValue(dialog.config.get('ui', {}).get('notification_offset_y', 20))
    dialog.notif_offset_y_spin.setSuffix(" px")
    notif_offset_layout.addWidget(dialog.notif_offset_y_spin)
    notif_offset_layout.addStretch()

    position_layout.addLayout(notif_offset_layout)

    # Prompt position preset
    prompt_pos_layout = QHBoxLayout()
    prompt_pos_label = QLabel("Prompt Dialogs:")
    prompt_pos_label.setFixedWidth(150)
    prompt_pos_layout.addWidget(prompt_pos_label)

    dialog.prompt_position_combo = QComboBox()
    dialog.prompt_position_combo.addItems([
        "top-left", "top-center", "top-right",
        "center-left", "center", "center-right",
        "bottom-left", "bottom-center", "bottom-right"
    ])
    current_prompt_pos = dialog.config.get('ui', {}).get('prompt_position', 'center')
    dialog.prompt_position_combo.setCurrentText(current_prompt_pos)
    dialog.prompt_position_combo.setFixedWidth(170)
    prompt_pos_layout.addWidget(dialog.prompt_position_combo)
    prompt_pos_layout.addStretch()
    position_layout.addLayout(prompt_pos_layout)

    # Prompt fine-tuning (using same screen dimensions)
    prompt_offset_layout = QHBoxLayout()
    prompt_fine_tune_label = QLabel("Fine-tune (X, Y):")
    prompt_fine_tune_label.setFixedWidth(150)
    prompt_offset_layout.addWidget(prompt_fine_tune_label)

    dialog.prompt_offset_x_spin = QSpinBox()
    dialog.prompt_offset_x_spin.setRange(-max_x, max_x)
    dialog.prompt_offset_x_spin.setValue(dialog.config.get('ui', {}).get('prompt_offset_x', 0))
    dialog.prompt_offset_x_spin.setSuffix(" px")
    prompt_offset_layout.addWidget(dialog.prompt_offset_x_spin)

    dialog.prompt_offset_y_spin = QSpinBox()
    dialog.prompt_offset_y_spin.setRange(-max_y, max_y)
    dialog.prompt_offset_y_spin.setValue(dialog.config.get('ui', {}).get('prompt_offset_y', 0))
    dialog.prompt_offset_y_spin.setSuffix(" px")
    prompt_offset_layout.addWidget(dialog.prompt_offset_y_spin)
    prompt_offset_layout.addStretch()

    position_layout.addLayout(prompt_offset_layout)

    position_group.setLayout(position_layout)
    layout.addWidget(position_group)

    # UI Scaling
    scaling_group = QGroupBox("UI Scaling")
    scaling_layout = QVBoxLayout()

    scaling_desc = QLabel("Adjust window and font sizes (0.5 = 50%, 2.0 = 200%)")
    scaling_desc.setWordWrap(True)
    scaling_layout.addWidget(scaling_desc)

    # Notification scale
    notif_scale_layout = QHBoxLayout()
    notif_scale_left_label = QLabel("Notification Popups:")
    notif_scale_left_label.setFixedWidth(150)
    notif_scale_layout.addWidget(notif_scale_left_label)

    dialog.notif_scale_slider = QSlider(Qt.Horizontal)
    dialog.notif_scale_slider.setRange(50, 200)
    current_notif_scale = int(dialog.config.get('ui', {}).get('notification_scale', 1.0) * 100)
    dialog.notif_scale_slider.setValue(current_notif_scale)
    dialog.notif_scale_slider.setTickPosition(QSlider.TicksBelow)
    dialog.notif_scale_slider.setTickInterval(25)
    dialog.notif_scale_slider.setFixedWidth(400)
    notif_scale_layout.addWidget(dialog.notif_scale_slider)

    dialog.notif_scale_label = QLabel(f"{current_notif_scale}%")
    dialog.notif_scale_label.setFixedWidth(50)
    dialog.notif_scale_label.setAlignment(Qt.AlignRight)
    notif_scale_layout.addWidget(dialog.notif_scale_label)

    dialog.notif_scale_slider.valueChanged.connect(
        lambda v: dialog.notif_scale_label.setText(f"{v}%")
    )

    scaling_layout.addLayout(notif_scale_layout)

    # Prompt scale
    prompt_scale_layout = QHBoxLayout()
    prompt_scale_left_label = QLabel("Prompt Dialogs:")
    prompt_scale_left_label.setFixedWidth(150)
    prompt_scale_layout.addWidget(prompt_scale_left_label)

    dialog.prompt_scale_slider = QSlider(Qt.Horizontal)
    dialog.prompt_scale_slider.setRange(50, 200)
    current_prompt_scale = int(dialog.config.get('ui', {}).get('prompt_scale', 1.0) * 100)
    dialog.prompt_scale_slider.setValue(current_prompt_scale)
    dialog.prompt_scale_slider.setTickPosition(QSlider.TicksBelow)
    dialog.prompt_scale_slider.setTickInterval(25)
    dialog.prompt_scale_slider.setFixedWidth(400)
    prompt_scale_layout.addWidget(dialog.prompt_scale_slider)

    dialog.prompt_scale_label = QLabel(f"{current_prompt_scale}%")
    dialog.prompt_scale_label.setFixedWidth(50)
    dialog.prompt_scale_label.setAlignment(Qt.AlignRight)
    prompt_scale_layout.addWidget(dialog.prompt_scale_label)

    dialog.prompt_scale_slider.valueChanged.connect(
        lambda v: dialog.prompt_scale_label.setText(f"{v}%")
    )

    scaling_layout.addLayout(prompt_scale_layout)

    # Settings window scale
    settings_scale_layout = QHBoxLayout()
    settings_scale_left_label = QLabel("Settings Window:")
    settings_scale_left_label.setFixedWidth(150)
    settings_scale_layout.addWidget(settings_scale_left_label)

    dialog.settings_scale_slider = QSlider(Qt.Horizontal)
    dialog.settings_scale_slider.setRange(50, 200)
    current_settings_scale = int(dialog.config.get('ui', {}).get('settings_scale', 1.0) * 100)
    dialog.settings_scale_slider.setValue(current_settings_scale)
    dialog.settings_scale_slider.setTickPosition(QSlider.TicksBelow)
    dialog.settings_scale_slider.setTickInterval(25)
    dialog.settings_scale_slider.setFixedWidth(400)
    settings_scale_layout.addWidget(dialog.settings_scale_slider)

    dialog.settings_scale_label = QLabel(f"{current_settings_scale}%")
    dialog.settings_scale_label.setFixedWidth(50)
    dialog.settings_scale_label.setAlignment(Qt.AlignRight)
    settings_scale_layout.addWidget(dialog.settings_scale_label)

    dialog.settings_scale_slider.valueChanged.connect(
        lambda v: dialog.settings_scale_label.setText(f"{v}%")
    )

    scaling_layout.addLayout(settings_scale_layout)

    # Note about settings scale
    settings_scale_note = QLabel("Note: Settings window scale applies on next open")
    settings_scale_note.setWordWrap(True)
    settings_scale_note.setStyleSheet("font-style: italic; color: gray;")
    scaling_layout.addWidget(settings_scale_note)

    scaling_group.setLayout(scaling_layout)
    layout.addWidget(scaling_group)

    # Popup Notifications
    popup_group = QGroupBox("Popup Notifications")
    popup_layout = QVBoxLayout()

    # Enable/Disable all notifications
    dialog.notif_enabled = QCheckBox("Enable Notifications")
    notif_enabled = dialog.config.get('notifications', {}).get('enabled', True)
    dialog.notif_enabled.setChecked(notif_enabled)
    popup_layout.addWidget(dialog.notif_enabled)

    # Show clean message popups
    dialog.notif_show_clean = QCheckBox("Show Clean Message Popups")
    show_clean = dialog.config.get('notifications', {}).get('show_clean_messages', True)
    dialog.notif_show_clean.setChecked(show_clean)
    popup_layout.addWidget(dialog.notif_show_clean)

    # Show optimized message popups
    dialog.notif_show_optimized = QCheckBox("Show Optimized Message Popups")
    show_optimized = dialog.config.get('notifications', {}).get('show_optimized_messages', True)
    dialog.notif_show_optimized.setChecked(show_optimized)
    popup_layout.addWidget(dialog.notif_show_optimized)

    popup_layout.addWidget(QLabel(""))  # Spacer
    popup_layout.addWidget(QLabel("Popup duration (milliseconds):"))
    popup_layout.addWidget(QLabel("(1000 ms = 1 second, 0 = instant dismiss)"))

    dialog.popup_duration_spin = QSpinBox()
    dialog.popup_duration_spin.setMinimum(0)
    dialog.popup_duration_spin.setMaximum(10000)
    dialog.popup_duration_spin.setSingleStep(100)
    popup_duration = dialog.config.get('notifications', {}).get('duration_ms', 2000)
    dialog.popup_duration_spin.setValue(popup_duration)
    popup_layout.addWidget(dialog.popup_duration_spin)

    popup_group.setLayout(popup_layout)
    layout.addWidget(popup_group)

    layout.addStretch()
    widget.setLayout(layout)
    return widget
