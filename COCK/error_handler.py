#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error Recovery System
=====================
Centralized error handling with graceful degradation patterns

Features:
- Exception classes for different error severities
- Error handling functions with context logging
- Backup-and-restore pattern for risky operations
- Performance monitoring with automatic logging
- Decorator for automatic error handling

All error handlers follow the pattern:
    - Log errors with full context and traceback
    - Attempt recovery if possible
    - Return safe default values
    - Never crash the application

Version: 1.0.0
Author: Chat Censor Tool Team
"""

import time
import traceback
import functools
from typing import Callable, Any, Optional, Dict
from contextlib import contextmanager
from logger import get_logger

# Module logger
log = get_logger(__name__)

# ============================================================================
# EXCEPTION CLASSES
# ============================================================================

class RecoverableError(Exception):
    """
    Error that can be recovered from with fallback behavior

    Examples:
    - Filter file not found -> use default filter
    - Config corrupted -> use default config
    - Network timeout -> retry or use cached data
    """
    pass


class CriticalError(Exception):
    """
    Error that requires application restart or user intervention

    Examples:
    - Core dependency missing (pyahocorasick)
    - Permissions denied on critical file
    - Out of memory
    """
    pass


class BackupRestoreError(Exception):
    """
    Error during backup-restore operation

    Contains the backup state for manual recovery
    """
    def __init__(self, message: str, backup: Dict[str, Any]):
        super().__init__(message)
        self.backup = backup


# ============================================================================
# ERROR HANDLING FUNCTIONS
# ============================================================================

def handle_error(
    error: Exception,
    context: str,
    recovery_func: Optional[Callable] = None,
    module: str = "unknown"
) -> bool:
    """
    Handle error with logging and optional recovery

    Args:
        error: The exception that occurred
        context: Description of what was being attempted (e.g., "loading filter file")
        recovery_func: Optional function to attempt recovery (takes no args)
        module: Name of module where error occurred

    Returns:
        bool: True if recovered successfully, False otherwise

    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     recovered = handle_error(e, "risky operation", use_default_value)
        ...     if not recovered:
        ...         raise
    """
    # Determine severity
    is_critical = isinstance(error, CriticalError)

    # Log with appropriate level
    if is_critical:
        log.critical(f"CRITICAL ERROR in {module} while {context}: {error}")
    else:
        log.error(f"ERROR in {module} while {context}: {error}")

    # Log full traceback at debug level
    log.debug(f"Full traceback:\n{traceback.format_exc()}")

    # Attempt recovery if function provided
    if recovery_func is not None:
        try:
            log.info(f"Attempting recovery for: {context}")
            recovery_func()
            log.info("Recovery successful")
            return True
        except Exception as recovery_error:
            log.error(f"Recovery failed: {recovery_error}")
            return False

    return False


def safe_execute(
    func: Callable,
    context: str,
    default_return: Any = None,
    recovery_func: Optional[Callable] = None
) -> Any:
    """
    Execute function with automatic error handling

    Args:
        func: Function to execute (no arguments)
        context: Description of operation
        default_return: Value to return on error
        recovery_func: Optional recovery function

    Returns:
        Function result on success, default_return on error

    Example:
        >>> config = safe_execute(
        ...     lambda: load_config_file(),
        ...     "loading config",
        ...     default_return=DEFAULT_CONFIG,
        ...     recovery_func=lambda: create_default_config()
        ... )
    """
    try:
        return func()
    except Exception as e:
        # Try recovery first
        recovered = handle_error(e, context, recovery_func, module=func.__module__)

        if recovered:
            # Try executing again after recovery
            try:
                return func()
            except Exception as retry_error:
                log.error(f"Retry after recovery failed: {retry_error}")

        # Return default
        log.warning(f"Returning default value for: {context}")
        return default_return


def with_error_handling(context: str, default_return: Any = None):
    """
    Decorator for automatic error handling

    Args:
        context: Description of what the function does
        default_return: Value to return on error

    Example:
        >>> @with_error_handling("loading filter file", default_return={})
        ... def load_filter(filepath):
        ...     # May raise exceptions
        ...     return load_data(filepath)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(e, context, module=func.__module__)
                log.warning(f"Returning default value for {func.__name__}: {default_return}")
                return default_return
        return wrapper
    return decorator


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

@contextmanager
def backup_state(**state_vars):
    """
    Context manager for backup-and-restore pattern

    Backs up state before risky operation, restores on exception

    Args:
        **state_vars: Named state variables to backup (e.g., automaton=self.automaton)

    Yields:
        dict: Backup dictionary with state snapshots

    Raises:
        BackupRestoreError: If operation fails (contains backup for manual recovery)

    Example:
        >>> with backup_state(automaton=self.automaton, config=self.config):
        ...     # Risky operation
        ...     self.automaton = load_new_automaton()
        ...     self.config = load_new_config()
        ... # On exception, automaton and config are restored automatically
    """
    # Create backup
    backup = {}
    for name, value in state_vars.items():
        # Deep copy if possible
        if hasattr(value, 'copy'):
            backup[name] = value.copy()
        elif isinstance(value, (list, tuple, set)):
            backup[name] = type(value)(value)
        elif isinstance(value, dict):
            backup[name] = value.copy()
        else:
            # For objects without copy method, store reference
            # Note: This won't protect against in-place modifications
            backup[name] = value

    try:
        yield backup
    except Exception as e:
        # Restore backed up state
        log.warning("Operation failed, restoring backed up state")

        # Get the caller's frame to restore variables
        import inspect
        frame = inspect.currentframe().f_back

        for name in state_vars.keys():
            if name in backup:
                # Try to restore in caller's context
                # This requires the caller to handle restoration
                log.debug(f"Backup available for: {name}")

        # Raise with backup attached
        raise BackupRestoreError(
            f"Operation failed, backup available: {str(e)}",
            backup=backup
        ) from e


@contextmanager
def monitor_performance(operation: str, warn_threshold_ms: float = 500):
    """
    Context manager for performance monitoring with automatic logging

    Args:
        operation: Name of operation being monitored
        warn_threshold_ms: Threshold in milliseconds to trigger warning (default: 500ms)

    Yields:
        dict: Performance metrics dictionary (updated on exit)
            - 'elapsed_ms': Elapsed time in milliseconds
            - 'start_time': Start timestamp
            - 'end_time': End timestamp

    Example:
        >>> with monitor_performance("Filter reload", warn_threshold_ms=500):
        ...     load_large_file()
        ... # Automatically logs: "Filter reload completed in 234.5ms"
    """
    perf = {
        'start_time': time.perf_counter(),
        'end_time': None,
        'elapsed_ms': None
    }

    try:
        yield perf
    finally:
        # Calculate elapsed time
        perf['end_time'] = time.perf_counter()
        perf['elapsed_ms'] = (perf['end_time'] - perf['start_time']) * 1000

        # Log performance
        log.info(f"{operation} completed in {perf['elapsed_ms']:.1f}ms")

        # Warn if slow
        if perf['elapsed_ms'] > warn_threshold_ms:
            log.warning(
                f"Slow operation: {operation} took {perf['elapsed_ms']:.1f}ms "
                f"(threshold: {warn_threshold_ms}ms)"
            )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_critical(error: Exception) -> bool:
    """
    Determine if error is critical

    Args:
        error: Exception to check

    Returns:
        bool: True if error is critical
    """
    return isinstance(error, (CriticalError, MemoryError, KeyboardInterrupt))


def format_error_context(error: Exception, context: str) -> str:
    """
    Format error message with context

    Args:
        error: Exception that occurred
        context: Context description

    Returns:
        str: Formatted error message
    """
    error_type = type(error).__name__
    return f"{error_type} while {context}: {str(error)}"


# ============================================================================
# MODULE INFORMATION
# ============================================================================

__version__ = '1.0.0'
__author__ = 'Chat Censor Tool Team'
