"""
Evolution triggers package.

This package provides trigger classes for the evolution system.
"""

from evolution.triggers.user_message_trigger import UserMessageTrigger
from evolution.triggers.timer_trigger import TimerTrigger
from evolution.triggers.thinking_trigger import ThinkingTrigger
from evolution.triggers.decorators import (
    on_user_message,
    on_ai_thinking,
    on_timer,
    evolution_trigger
)

__all__ = [
    'UserMessageTrigger',
    'TimerTrigger',
    'ThinkingTrigger',
    'on_user_message',
    'on_ai_thinking',
    'on_timer',
    'evolution_trigger',
]
