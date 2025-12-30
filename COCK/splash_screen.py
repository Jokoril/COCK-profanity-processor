#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Splash Screen Module
====================
Animated splash screen with fade effects and random rotation
"""

import random
import os
from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import QGraphicsOpacityEffect
import path_manager


class AnimatedSplashScreen(QSplashScreen):
    """
    Custom splash screen with fade in/out animations
    Randomly selects from multiple splash designs
    """
    
    def __init__(self, splash_duration=3000):
        """
        Initialize animated splash screen
        
        Args:
            splash_duration: Total display time in milliseconds (default: 3000ms = 3 seconds)
        """
        # Select random splash image
        splash_images = [
            'splash/splash_1.png',
            'splash/splash_2.png',
            'splash/splash_3.png',
            'splash/splash_4.png'
        ]
        
        # Find first existing splash image
        selected_splash = None
        random.shuffle(splash_images)  # Randomize order
        
        for splash_file in splash_images:
            splash_path = path_manager.get_resource_file(splash_file)
            if os.path.exists(splash_path):
                selected_splash = splash_path
                print(f"[SPLASH] Selected: {splash_file}")
                break
        
        if not selected_splash:
            print("[SPLASH] WARNING: No splash images found, using blank splash")
            pixmap = QPixmap(800, 600)
            pixmap.fill(Qt.black)
        else:
            pixmap = QPixmap(selected_splash)
        
        super().__init__(pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        self.splash_duration = splash_duration
        self.fade_duration = 500  # 500ms for fade in/out
        
        # Set up opacity effect for fading
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)  # Start invisible
        
        # Center splash screen
        self.center_on_screen()
        
    def center_on_screen(self):
        """Center the splash screen on the primary monitor"""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().availableGeometry()
        splash_size = self.size()
        x = (screen.width() - splash_size.width()) // 2
        y = (screen.height() - splash_size.height()) // 2
        self.move(x, y)
    
    def show_with_fade(self):
        """Show splash screen with fade in effect"""
        self.show()
        self.raise_()  # Bring to front
        self.activateWindow()  # Activate window
        
        # Force immediate update
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Fade in animation
        self.fade_in_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_anim.setDuration(self.fade_duration)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in_anim.start()
        
        # Schedule fade out
        display_time = self.splash_duration - self.fade_duration
        QTimer.singleShot(display_time, self.fade_out)
    
    def fade_out(self):
        """Fade out splash screen"""
        self.fade_out_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_anim.setDuration(self.fade_duration)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out_anim.finished.connect(self.close)
        self.fade_out_anim.start()


def show_splash(app, duration=3000):
    """
    Show splash screen with fade effects
    
    Args:
        app: QApplication instance
        duration: Display duration in milliseconds
        
    Returns:
        AnimatedSplashScreen instance
    """
    splash = AnimatedSplashScreen(duration)
    splash.show_with_fade()
    return splash


# Module information
__version__ = '1.0.0'
__author__ = 'Jokoril'
