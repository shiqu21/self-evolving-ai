"""
Timer trigger for the evolution system.

This module provides the TimerTrigger class that triggers
evolution analysis on a timer interval.
"""

import time
import threading
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TimerTrigger:
    """
    Trigger that fires on a timer interval.
    
    This trigger fires periodically based on a configurable
    interval (in minutes).
    
    Attributes:
        name: Trigger name.
        interval_minutes: Timer interval in minutes.
        last_trigger_time: Timestamp of last trigger.
        timer_thread: Background timer thread.
        running: Whether the timer is running.
    """
    
    def __init__(
        self,
        name: str = "timer_trigger",
        interval_minutes: float = 5.0
    ) -> None:
        """
        Initialize the timer trigger.
        
        Args:
            name: Trigger name.
            interval_minutes: Timer interval in minutes.
        """
        self.name = name
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60.0
        self.last_trigger_time = None
        self.timer_thread = None
        self.running = False
        logger.info(f"TimerTrigger initialized: interval={interval_minutes} minutes")
    
    def should_trigger(self) -> bool:
        """
        Check if the trigger should fire.
        
        Returns:
            True if should trigger, False otherwise.
        """
        if self.last_trigger_time is None:
            return True
        
        elapsed = time.time() - self.last_trigger_time
        return elapsed >= self.interval_seconds
    
    def mark_triggered(self) -> None:
        """
        Mark the trigger as having fired.
        """
        self.last_trigger_time = time.time()
    
    def create_event_data(self) -> Dict[str, Any]:
        """
        Create event data for the trigger.
        
        Returns:
            Event data dictionary.
        """
        return {
            'trigger_type': 'timer',
            'timestamp': time.time(),
            'trigger_name': self.name,
            'interval_minutes': self.interval_minutes
        }
    
    def start(self, callback=None) -> None:
        """
        Start the timer trigger.
        
        Args:
            callback: Optional callback function to call on trigger.
        """
        if self.running:
            logger.warning("Timer already running")
            return
        
        self.running = True
        
        def timer_loop():
            while self.running:
                if self.should_trigger():
                    logger.info("Timer trigger fired")
                    self.mark_triggered()
                    if callback:
                        try:
                            callback(self.create_event_data())
                        except Exception as e:
                            logger.error(f"Timer callback error: {e}")
                
                # Sleep for a short interval to check again
                time.sleep(min(60.0, self.interval_seconds / 10.0))
        
        self.timer_thread = threading.Thread(target=timer_loop, daemon=True)
        self.timer_thread.start()
        logger.info("Timer trigger started")
    
    def stop(self) -> None:
        """
        Stop the timer trigger.
        """
        self.running = False
        if self.timer_thread:
            self.timer_thread.join(timeout=5.0)
            self.timer_thread = None
        logger.info("Timer trigger stopped")
