"""
Startup script for initializing the evolution system integration with WorkBuddy.

This module provides functions for starting the evolution system
and integrating it with WorkBuddy's startup process.
"""

import os
import sys
import threading
import time
import atexit
from typing import Optional, Dict, Any
import logging

from evolution.integration.workbuddy_hook import WorkBuddyHook
from evolution.config.settings import get_settings, Settings

logger = logging.getLogger(__name__)


# Global hook instance
_hook_instance: Optional[WorkBuddyHook] = None
_hook_lock = threading.Lock()


def get_hook() -> Optional[WorkBuddyHook]:
    """
    Get the global WorkBuddyHook instance.
    
    Returns:
        Global WorkBuddyHook instance, or None if not initialized.
    """
    global _hook_instance
    return _hook_instance


def check_daemon_running() -> bool:
    """
    Check if the evolution system is already initialized.
    
    Returns:
        True if initialized, False otherwise.
    """
    global _hook_instance
    if _hook_instance and _hook_instance.is_running():
        logger.info("Evolution system is already running (global instance)")
        return True
    
    return False


def start_evolution(
    settings: Optional[Settings] = None,
    database: Optional[Any] = None,
    db_path: Optional[str] = None,
    auto_start: bool = True
) -> Optional[WorkBuddyHook]:
    """
    Start the evolution system.
    
    This function:
    1. Checks if already running
    2. Creates a WorkBuddyHook instance
    3. Starts the evolution engine (if auto_start is True)
    
    Args:
        settings: Optional custom settings.
        database: Optional database instance.
        db_path: Optional path to SQLite database file.
        auto_start: Whether to automatically start the evolution engine.
        
    Returns:
        WorkBuddyHook instance, or None if already running.
        
    Raises:
        RuntimeError: If failed to start the evolution system.
    """
    global _hook_instance
    
    with _hook_lock:
        # Check if already running
        if check_daemon_running():
            logger.warning("Evolution system is already running")
            return _hook_instance
        
        try:
            # Create settings if not provided
            if settings is None:
                settings = get_settings()
            
            # Override auto_start if provided
            if not auto_start:
                settings.auto_start = False
            
            # Create hook instance
            _hook_instance = WorkBuddyHook(
                settings=settings,
                database=database,
                db_path=db_path
            )
            
            # Start evolution if auto_start is enabled
            if settings.auto_start:
                _hook_instance.start_evolution()
            
            logger.info("Evolution system started successfully")
            return _hook_instance
            
        except Exception as e:
            logger.error(f"Failed to start evolution system: {e}")
            raise RuntimeError(f"Failed to start evolution system: {e}") from e


def stop_evolution() -> None:
    """
    Stop the evolution system gracefully.
    
    This function stops the evolution engine and cleans up resources.
    """
    global _hook_instance
    
    with _hook_lock:
        if _hook_instance is None:
            logger.warning("Evolution system is not running")
            return
        
        try:
            _hook_instance.stop_evolution()
            _hook_instance = None
            
            logger.info("Evolution system stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping evolution system: {e}")


def restart_evolution() -> Optional[WorkBuddyHook]:
    """
    Restart the evolution system.
    
    Returns:
        New WorkBuddyHook instance.
    """
    logger.info("Restarting evolution system...")
    stop_evolution()
    time.sleep(1.0)  # Give time for cleanup
    return start_evolution()


def get_evolution_status() -> Dict[str, Any]:
    """
    Get the current status of the evolution system.
    
    Returns:
        Dictionary with status information.
    """
    global _hook_instance
    
    if _hook_instance is None:
        return {
            'running': False,
            'message': 'Evolution system is not initialized'
        }
    
    return _hook_instance.get_status()


def initialize_evolution_integration(
    settings: Optional[Settings] = None,
    database: Optional[Any] = None,
    db_path: Optional[str] = None
) -> WorkBuddyHook:
    """
    Initialize the evolution system for integration with WorkBuddy.
    
    This is the main entry point for integrating the evolution system
    into WorkBuddy. It creates and starts the evolution system.
    
    Args:
        settings: Optional custom settings.
        database: Optional database instance.
        db_path: Optional path to SQLite database file.
        
    Returns:
        WorkBuddyHook instance.
        
    Example:
        >>> hook = initialize_evolution_integration()
        >>> hook.on_user_message("Hello, world!")
    """
    hook = start_evolution(
        settings=settings,
        database=database,
        db_path=db_path
    )
    if hook is None:
        # Already running, get existing instance
        hook = get_hook()
        if hook is None:
            raise RuntimeError("Failed to initialize evolution integration")
    
    return hook


# Register cleanup function
atexit.register(stop_evolution)


if __name__ == "__main__":
    """
    Test the startup script.
    """
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Testing evolution startup...")
    
    try:
        # Initialize
        hook = initialize_evolution_integration()
        
        logger.info(f"Status: {hook.get_status()}")
        
        # Test hooks
        hook.on_user_message("Test message")
        
        # Cleanup
        stop_evolution()
        
        logger.info("Startup test completed successfully!")
        
    except Exception as e:
        logger.error(f"Startup test failed: {e}", exc_info=True)
