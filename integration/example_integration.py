"""
Example integration of the evolution system with WorkBuddy.

This module provides example code demonstrating how to integrate
the self-evolution system into WorkBuddy's main workflow.
"""

import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Example 1: Basic Integration
# =============================================================================

def example_basic_integration():
    """
    Example 1: Basic integration with WorkBuddy.
    
    This example shows the simplest way to integrate the evolution
    system with WorkBuddy.
    """
    logger.info("=" * 60)
    logger.info("Example 1: Basic Integration")
    logger.info("=" * 60)
    
    # Import the hook
    from evolution.integration.workbuddy_hook import WorkBuddyHook
    
    # Create hook instance
    hook = WorkBuddyHook()
    
    # Start evolution (starts background daemon)
    hook.start_evolution()
    
    logger.info("Evolution system started!")
    logger.info(f"Status: {hook.get_status()}")
    
    # Simulate user messages
    logger.info("\n--- Simulating user messages ---")
    hook.on_user_message("Hello, can you help me with Python?")
    hook.on_user_message("I'm getting a TypeError in my code")
    
    # Get status
    logger.info("\n--- Getting status ---")
    status = hook.get_status()
    logger.info(f"Status: {status}")
    
    # Stop evolution
    logger.info("\n--- Stopping evolution ---")
    hook.stop_evolution()
    
    logger.info("Example 1 completed!")


# =============================================================================
# Example 2: Integration with Startup Script
# =============================================================================

def example_startup_integration():
    """
    Example 2: Integration using the startup script.
    
    This example shows how to use the startup script to initialize
    the evolution system during WorkBuddy's startup.
    """
    logger.info("=" * 60)
    logger.info("Example 2: Startup Integration")
    logger.info("=" * 60)
    
    # Import startup function
    from evolution.integration.startup import initialize_evolution_integration
    
    # Initialize evolution system (starts automatically)
    hook = initialize_evolution_integration()
    
    logger.info("Evolution system initialized via startup script!")
    logger.info(f"Status: {hook.get_status()}")
    
    # Use the hook
    logger.info("\n--- Using the hook ---")
    hook.on_user_message("How do I optimize this code?")
    
    # Stop when done
    from evolution.integration.startup import stop_evolution
    stop_evolution()
    
    logger.info("Example 2 completed!")


# =============================================================================
# Example 3: Manual Evolution Trigger
# =============================================================================

def example_manual_trigger():
    """
    Example 3: Manually triggering evolution analysis.
    
    This example shows how to manually trigger an evolution
    cycle (e.g., on timer or user request).
    """
    logger.info("=" * 60)
    logger.info("Example 3: Manual Evolution Trigger")
    logger.info("=" * 60)
    
    from evolution.integration.startup import initialize_evolution_integration
    
    # Initialize
    hook = initialize_evolution_integration()
    
    # Manually trigger evolution cycle
    logger.info("\n--- Manually triggering evolution cycle ---")
    result = hook.trigger_analysis()
    
    if result:
        logger.info(f"Cycle result: {result.to_dict()}")
    else:
        logger.info("Cycle failed or not completed")
    
    # Cleanup
    from evolution.integration.startup import stop_evolution
    stop_evolution()
    
    logger.info("Example 3 completed!")


# =============================================================================
# Example 4: Custom Database Path
# =============================================================================

def example_custom_database():
    """
    Example 4: Integration with custom database path.
    
    This example shows how to specify a custom database path
    for persisting evolution data.
    """
    logger.info("=" * 60)
    logger.info("Example 4: Custom Database Path")
    logger.info("=" * 60)
    
    from evolution.integration.workbuddy_hook import WorkBuddyHook
    
    # Specify custom database path
    db_path = "C:/temp/evolution.db"
    
    # Create hook with custom db_path
    hook = WorkBuddyHook(db_path=db_path)
    hook.start_evolution()
    
    logger.info(f"Evolution system started with database: {db_path}")
    
    # Use the hook
    hook.on_user_message("Test message with custom database")
    
    # Stop
    hook.stop_evolution()
    
    logger.info("Example 4 completed!")


# =============================================================================
# Example 5: Callback Integration
# =============================================================================

def example_callback_integration():
    """
    Example 5: Integration with callbacks.
    
    This example shows how to register callbacks to receive
    notifications about evolution events.
    """
    logger.info("=" * 60)
    logger.info("Example 5: Callback Integration")
    logger.info("=" * 60)
    
    from evolution.integration.workbuddy_hook import WorkBuddyHook
    
    # Define callback function
    def on_evolution_event(event_data: Dict[str, Any]) -> None:
        logger.info(f"Evolution event received: {event_data}")
        # Process event (e.g., update UI, notify user, etc.)
    
    # Create hook and register callback
    hook = WorkBuddyHook()
    hook.register_evolution_callback(on_evolution_event)
    
    # Start evolution
    hook.start_evolution()
    
    logger.info("Evolution system started with callback!")
    
    # Use the hook
    hook.on_user_message("Test message with callback")
    
    # Wait a bit for async processing
    import time
    time.sleep(2.0)
    
    # Stop
    hook.stop_evolution()
    
    logger.info("Example 5 completed!")


# =============================================================================
# Example 6: Full WorkBuddy Integration Simulation
# =============================================================================

def simulate_workbuddy_workflow():
    """
    Example 6: Full WorkBuddy workflow simulation.
    
    This example simulates how the evolution system would be
    integrated into WorkBuddy's actual workflow.
    """
    logger.info("=" * 60)
    logger.info("Example 6: Full WorkBuddy Workflow Simulation")
    logger.info("=" * 60)
    
    from evolution.integration.startup import initialize_evolution_integration
    
    # Step 1: Initialize during WorkBuddy startup
    logger.info("\n[Step 1] WorkBuddy starting up...")
    hook = initialize_evolution_integration()
    logger.info("Evolution system initialized!")
    
    # Step 2: Simulate user interaction
    logger.info("\n[Step 2] User sends message...")
    user_message = "Can you help me fix this bug in my Python code?"
    hook.on_user_message(user_message)
    
    # Step 3: AI prepares to respond
    logger.info("\n[Step 3] AI preparing response...")
    context = {
        'user_message': user_message,
        'conversation_id': '12345',
        'user_id': 'user_001',
        'timestamp': time.time()
    }
    enhanced_context = hook.before_ai_response(context)
    logger.info(f"Context prepared")
    
    # Step 4: Timer trigger fires (simulated)
    logger.info("\n[Step 4] Timer trigger fires (simulated)...")
    # In production, this would be called by a timer
    # hook.on_timer()
    
    # Step 5: Get status and reports
    logger.info("\n[Step 5] Checking evolution status...")
    status = hook.get_status()
    logger.info(f"Status: {status}")
    
    # Step 6: WorkBuddy shutting down
    logger.info("\n[Step 6] WorkBuddy shutting down...")
    from evolution.integration.startup import stop_evolution
    stop_evolution()
    
    logger.info("\nExample 6 completed!")
    logger.info("=" * 60)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    """
    Run examples.
    
    To run a specific example, uncomment the desired function call.
    """
    logger.info("Evolution System Integration Examples")
    logger.info("=" * 60)
    
    # Uncomment the example you want to run:
    
    # Example 1: Basic integration
    # example_basic_integration()
    
    # Example 2: Startup integration
    # example_startup_integration()
    
    # Example 3: Manual trigger
    # example_manual_trigger()
    
    # Example 4: Custom database
    # example_custom_database()
    
    # Example 5: Callback integration
    # example_callback_integration()
    
    # Example 6: Full workflow simulation
    # simulate_workbuddy_workflow()
    
    logger.info("\nAll examples completed!")
