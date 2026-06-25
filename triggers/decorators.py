"""
Decorators for the evolution triggers.

This module provides decorator functions that can be used
to easily integrate evolution triggers into existing code.
"""

import functools
import time
from typing import Callable, Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)


def on_user_message(func: Callable) -> Callable:
    """
    Decorator that triggers evolution analysis on user message.
    
    This decorator can be applied to functions that process
    user messages to automatically trigger evolution analysis.
    
    Args:
        func: Function to decorate.
    
    Returns:
        Decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Call original function
        result = func(*args, **kwargs)
        
        # Trigger evolution analysis (non-blocking)
        try:
            message = args[0] if args else kwargs.get('message', '')
            logger.info(f"Evolution trigger (decorator): user message: {message[:50]}...")
            # In production, this would call the evolution hook
        except Exception as e:
            logger.error(f"Evolution trigger error: {e}")
        
        return result
    
    return wrapper


def on_ai_thinking(func: Callable) -> Callable:
    """
    Decorator that triggers evolution analysis before AI thinking.
    
    This decorator can be applied to functions that are called
    before AI starts thinking/processing.
    
    Args:
        func: Function to decorate.
    
    Returns:
        Decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Trigger evolution analysis (non-blocking)
        try:
            context = args[0] if args else kwargs.get('context', {})
            logger.info(f"Evolution trigger (decorator): AI thinking")
            # In production, this would call the evolution hook
        except Exception as e:
            logger.error(f"Evolution trigger error: {e}")
        
        # Call original function
        return func(*args, **kwargs)
    
    return wrapper


def on_timer(interval_minutes: float = 5.0) -> Callable:
    """
    Decorator that triggers evolution analysis on a timer.
    
    This decorator can be applied to functions that should be
    called periodically for evolution analysis.
    
    Args:
        interval_minutes: Timer interval in minutes.
    
    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Check if should trigger
            current_time = time.time()
            last_trigger = getattr(wrapper, '_last_trigger', None)
            
            if last_trigger is None or (current_time - last_trigger) >= (interval_minutes * 60):
                # Trigger evolution analysis
                try:
                    logger.info(f"Evolution trigger (decorator): timer fired")
                    # In production, this would call the evolution hook
                    wrapper._last_trigger = current_time
                except Exception as e:
                    logger.error(f"Evolution trigger error: {e}")
            
            # Call original function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def evolution_trigger(
    trigger_type: str = "user_message",
    **kwargs
) -> Callable:
    """
    General decorator for evolution triggers.
    
    This decorator provides a unified interface for all trigger types.
    
    Args:
        trigger_type: Type of trigger ('user_message', 'thinking', 'timer').
        **kwargs: Additional arguments for specific trigger types.
    
    Returns:
        Decorator function.
    
    Example:
        @evolution_trigger(trigger_type="user_message")
        def process_message(message: str) -> str:
            return f"Processed: {message}"
    """
    if trigger_type == "user_message":
        return on_user_message
    elif trigger_type == "thinking":
        return on_ai_thinking
    elif trigger_type == "timer":
        interval = kwargs.get('interval_minutes', 5.0)
        return on_timer(interval_minutes=interval)
    else:
        logger.warning(f"Unknown trigger type: {trigger_type}")
        return lambda func: func  # No-op decorator
