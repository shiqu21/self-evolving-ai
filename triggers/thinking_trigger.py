"""
Thinking trigger for the evolution system.

This module provides the ThinkingTrigger class that triggers
evolution analysis when AI starts thinking/processing.
"""

import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ThinkingTrigger:
    """
    Trigger that fires when AI starts thinking.
    
    This trigger can be used to analyze the context before
    the AI starts processing, enabling proactive evolution.
    
    Attributes:
        name: Trigger name.
        min_confidence: Minimum confidence threshold to trigger.
    """
    
    def __init__(
        self,
        name: str = "thinking_trigger",
        min_confidence: float = 0.5
    ) -> None:
        """
        Initialize the thinking trigger.
        
        Args:
            name: Trigger name.
            min_confidence: Minimum confidence threshold to trigger.
        """
        self.name = name
        self.min_confidence = min_confidence
        logger.info(f"ThinkingTrigger initialized: min_confidence={min_confidence}")
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """
        Check if the trigger should fire.
        
        Args:
            context: AI thinking context.
            
        Returns:
            True if should trigger, False otherwise.
        """
        # Always trigger when AI starts thinking
        # In the future, we could add confidence-based triggering
        return True
    
    def create_event_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create event data for the trigger.
        
        Args:
            context: AI thinking context.
            
        Returns:
            Event data dictionary.
        """
        return {
            'trigger_type': 'thinking',
            'context': context,
            'timestamp': time.time(),
            'trigger_name': self.name
        }
