"""
User message trigger for the evolution system.

This module provides the UserMessageTrigger class that triggers
evolution analysis based on user messages.
"""

import re
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class UserMessageTrigger:
    """
    Trigger that fires on user messages.
    
    This trigger can be configured to fire on every message
    or only on messages matching certain patterns.
    
    Attributes:
        name: Trigger name.
        trigger_on_every_message: Whether to trigger on every message.
        patterns: Optional list of regex patterns to match.
    """
    
    def __init__(
        self,
        name: str = "user_message_trigger",
        trigger_on_every_message: bool = True,
        patterns: Optional[list] = None
    ) -> None:
        """
        Initialize the user message trigger.
        
        Args:
            name: Trigger name.
            trigger_on_every_message: Whether to trigger on every message.
            patterns: Optional list of regex patterns to match.
        """
        self.name = name
        self.trigger_on_every_message = trigger_on_every_message
        self.patterns = patterns or []
        logger.info(f"UserMessageTrigger initialized: trigger_on_every_message={trigger_on_every_message}")
    
    def should_trigger(self, message: str) -> bool:
        """
        Check if the trigger should fire.
        
        Args:
            message: User message.
            
        Returns:
            True if should trigger, False otherwise.
        """
        if self.trigger_on_every_message:
            return True
        
        # Check patterns
        for pattern in self.patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        return False
    
    def create_event_data(self, message: str) -> Dict[str, Any]:
        """
        Create event data for the trigger.
        
        Args:
            message: User message.
            
        Returns:
            Event data dictionary.
        """
        return {
            'trigger_type': 'user_message',
            'message': message,
            'timestamp': time.time(),
            'trigger_name': self.name
        }
