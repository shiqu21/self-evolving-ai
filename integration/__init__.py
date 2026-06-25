"""
Evolution system integration package.

This package provides integration components for embedding the
self-evolution system into WorkBuddy's main workflow.
"""

from .workbuddy_hook import WorkBuddyHook
from .startup import (
    initialize_evolution_integration,
    start_evolution,
    stop_evolution,
    get_evolution_status,
    check_daemon_running
)

__all__ = [
    'WorkBuddyHook',
    'initialize_evolution_integration',
    'start_evolution',
    'stop_evolution',
    'get_evolution_status',
    'check_daemon_running',
]
