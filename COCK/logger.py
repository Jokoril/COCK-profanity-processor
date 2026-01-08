#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centralized Logging Module
===========================
v1.1 feature - replaces scattered print() statements

Features:
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File logging with rotation
- Console logging with optional colors
- Module-specific loggers
- Thread-safe logging

Usage:
    # In any module:
    from logger import get_logger

    log = get_logger(__name__)
    log.info("Operation started")
    log.debug("Debug details: %s", data)
    log.warning("Potential issue detected")
    log.error("Operation failed: %s", error)
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
import path_manager


# Global flag to track if root logger is configured
_LOGGER_CONFIGURED = False


def setup_logger(
    name: str = "COCK",
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    debug_mode: bool = False
) -> logging.Logger:
    """
    Set up centralized logger (call once during app initialization)

    This should be called ONCE at application startup, typically in main.py.
    All other modules should use get_logger(__name__) instead.

    Args:
        name: Logger name (usually "COCK" for main app)
        level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Enable file logging with rotation
        log_to_console: Enable console logging
        debug_mode: If True, sets level to DEBUG and adds verbose formatting

    Returns:
        Configured logger instance

    Example:
        # In main.py during startup:
        from logger import setup_logger
        logger = setup_logger("COCK", level="INFO", debug_mode=args.debug)
        logger.info("Application starting...")
    """
    global _LOGGER_CONFIGURED

    # Override level if debug mode
    if debug_mode:
        level = "DEBUG"

    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Prevent duplicate handlers if already configured
    if _LOGGER_CONFIGURED:
        return logger

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

        if debug_mode:
            # Verbose format for debugging
            console_format = logging.Formatter(
                '[%(asctime)s] [%(name)s] %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
        else:
            # Compact format for normal use
            console_format = logging.Formatter(
                '[%(name)s] %(levelname)s: %(message)s'
            )

        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

    # File handler with rotation
    if log_to_file:
        try:
            # Create logs directory
            log_dir = os.path.join(path_manager.get_app_dir(), 'logs')
            os.makedirs(log_dir, exist_ok=True)

            log_file = os.path.join(log_dir, f'{name}.log')

            # Rotating file handler: 5MB max size, keep 3 backup files
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)  # Log everything to file

            # Detailed format for file logs
            file_format = logging.Formatter(
                '%(asctime)s - [%(name)s] %(levelname)s - %(funcName)s() - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)

            # Log startup message
            logger.info(f"Logging initialized - File: {log_file}")

        except Exception as e:
            # If file logging fails, at least log to console
            logger.warning(f"Failed to initialize file logging: {e}")

    _LOGGER_CONFIGURED = True
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger for a specific module

    Call this in each module to get a module-specific logger.
    The logger will inherit configuration from the root logger
    set up by setup_logger().

    Args:
        name: Module name (use __name__ to get current module)

    Returns:
        Logger instance for the module

    Example:
        # In fast_detector.py:
        from logger import get_logger

        log = get_logger(__name__)  # Creates logger named 'fast_detector'

        def detect_all(self, text):
            log.debug(f"Detecting in text: {text[:50]}")
            log.info(f"Found {count} matches")
    """
    return logging.getLogger(name)


def set_level(level: str):
    """
    Change logging level at runtime

    Args:
        level: New level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Example:
        # Enable debug logging for troubleshooting
        from logger import set_level
        set_level("DEBUG")
    """
    logging.getLogger().setLevel(getattr(logging, level.upper()))


def disable_logging():
    """
    Disable all logging (for performance-critical sections)

    Example:
        from logger import disable_logging, enable_logging

        disable_logging()
        # ... performance-critical code ...
        enable_logging()
    """
    logging.disable(logging.CRITICAL)


def enable_logging():
    """
    Re-enable logging after disable_logging()
    """
    logging.disable(logging.NOTSET)


# Module information
__version__ = '1.1.0'
__author__ = 'Chat Censor Tool Team'
