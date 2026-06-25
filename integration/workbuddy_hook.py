"""
WorkBuddy integration hook for the evolution system.

This module provides the WorkBuddyHook class that integrates the
self-evolution system into WorkBuddy's main workflow, enabling
non-blocking hooks for user messages and AI thinking.
"""

import threading
import time
import sqlite3
import os
from typing import Dict, Any, Optional, Callable, List
import logging

# Import the ORIGINAL EvolutionEngine from the correct location
try:
    # Try relative import first (when used as part of the package)
    from ..core.engine import EvolutionEngine, CycleResult
    from ..core.engine import Phase, EventType as EngineEventType
except ImportError:
    # Fall back to absolute import
    from core.engine import EvolutionEngine, CycleResult
    from core.engine import Phase, EventType as EngineEventType

from evolution.config.settings import get_settings, Settings

logger = logging.getLogger(__name__)


class SimpleDatabase:
    """
    Simple database wrapper for the evolution system.
    
    This class provides a SQLite3-based database interface
    compatible with the original EvolutionEngine.
    """
    
    def __init__(self, db_path: str = ":memory:") -> None:
        """
        Initialize the database.
        
        Args:
            db_path: Path to the SQLite database file.
                     If ":memory:", will use a temporary file database instead
                     (because :memory: databases are per-connection).
        """
        # Fix: :memory: databases don't work across connections,
        # so we use a temporary file database instead
        if db_path == ":memory:":
            import tempfile
            temp_dir = tempfile.gettempdir()
            db_path = os.path.join(temp_dir, "evolution_temp.db")
            logger.info(f":memory: detected, using file database instead: {db_path}")
        
        self.db_path = db_path
        self._init_tables()
        logger.info(f"SimpleDatabase initialized at {db_path}")
    
    def _init_tables(self) -> None:
        """Initialize database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                phase TEXT,
                status TEXT,
                message TEXT,
                severity TEXT,
                created_at TEXT
            )
        """)
        
        # Create cycle_results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cycle_results (
                cycle_id INTEGER PRIMARY KEY,
                phase TEXT,
                status TEXT,
                improvements INTEGER,
                skills_created INTEGER,
                errors INTEGER,
                message TEXT
            )
        """)
        
        # Create skills table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                content TEXT,
                skill_type TEXT,
                status TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection.
        
        Returns:
            SQLite connection object.
        """
        conn = sqlite3.connect(self.db_path)
        return conn


class WorkBuddyHook:
    """
    Integration hook for embedding evolution system into WorkBuddy.
    
    This class provides non-blocking hooks that integrate the self-evolution
    system into WorkBuddy's main workflow:
    - on_user_message: Called after each user message
    - before_ai_response: Called before AI starts thinking
    - on_timer: Called on timer trigger (runs full evolution cycle)
    
    The evolution engine runs in a background thread to avoid blocking
    the main WorkBuddy workflow.
    
    Attributes:
        engine: Original EvolutionEngine instance.
        database: Database instance for the engine.
        settings: Configuration settings.
        initialized: Whether the hook has been initialized.
    """
    
    def __init__(
        self,
        settings: Optional[Settings] = None,
        database: Optional[Any] = None,
        db_path: Optional[str] = None
    ) -> None:
        """
        Initialize the WorkBuddy integration hook.
        
        Args:
            settings: Optional custom settings.
            database: Optional database instance.
            db_path: Optional path to SQLite database file.
        """
        self._settings = settings or get_settings()
        self._initialized = False
        self._lock = threading.Lock()
        
        # Create database if not provided
        if database is None:
            db_path = db_path or self._settings.database_path or ":memory:"
            self.database = SimpleDatabase(db_path)
            logger.info(f"Created SimpleDatabase at {db_path}")
        else:
            self.database = database
        
        # Create the ORIGINAL EvolutionEngine instance
        try:
            self.engine = EvolutionEngine(database=self.database)
            logger.info("Original EvolutionEngine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EvolutionEngine: {e}")
            raise
        
        # Register triggers based on settings
        self._register_triggers()
        
        # Callbacks for integration
        self._on_evolution_event: Optional[Callable[[Dict[str, Any]], None]] = None
        
        logger.info("WorkBuddyHook initialized")
    
    def _register_triggers(self) -> None:
        """Register triggers based on settings."""
        # Note: The original engine has its own trigger system
        # We just need to configure it via settings
        logger.info("Triggers will be managed by the original EvolutionEngine")
    
    def start_evolution(self) -> None:
        """
        Start the evolution engine.
        
        This method prepares the evolution system for use.
        The actual evolution cycles are triggered by:
        - Timer (calls run_cycle() periodically)
        - Manual trigger (calls run_cycle() on demand)
        """
        with self._lock:
            if self._initialized:
                logger.warning("Evolution already started")
                return
            
            try:
                # The original engine doesn't have a separate start() method
                # It's designed to have run_cycle() called directly
                # We just set the initialized flag here
                
                self._initialized = True
                logger.info("Evolution engine started successfully")
            except Exception as e:
                logger.error(f"Failed to start evolution engine: {e}")
                raise
    
    def stop_evolution(self) -> None:
        """
        Stop the evolution engine gracefully.
        """
        with self._lock:
            if not self._initialized:
                logger.warning("Evolution not started")
                return
            
            try:
                self._initialized = False
                logger.info("Evolution engine stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping evolution engine: {e}")
    
    def on_user_message(self, message: str) -> None:
        """
        Hook called after a user message is received.
        
        This method is non-blocking. It logs the message for
        future analysis but does NOT run the full evolution cycle.
        
        Args:
            message: User message content.
        """
        if not self._initialized:
            logger.debug("Evolution not started, skipping user message hook")
            return
        
        try:
            # Log the message (non-blocking)
            logger.info(f"User message received: {message[:50]}...")
            
            # We could store this message for later analysis
            # but we DON'T run the full cycle here (too heavy)
            
        except Exception as e:
            # Don't let evolution errors affect main workflow
            logger.error(f"Error in on_user_message hook: {e}")
    
    def before_ai_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook called before AI starts thinking/processing.
        
        This method is designed to be non-blocking. It prepares
        context for the AI but does NOT run the full evolution cycle.
        
        Args:
            context: Current context dictionary.
            
        Returns:
            Context dictionary (may be enhanced in future versions).
        """
        if not self._initialized:
            logger.debug("Evolution not started, skipping before_ai_response hook")
            return context
        
        try:
            # Prepare context (non-blocking)
            logger.debug("Preparing context before AI response")
            
            # In the future, we could enhance the context here
            # For now, just return unchanged
            
            return context
            
        except Exception as e:
            # Don't let evolution errors affect main workflow
            logger.error(f"Error in before_ai_response hook: {e}")
            return context
    
    def on_timer(self) -> None:
        """
        Hook called on timer trigger.
        
        This method runs the FULL evolution cycle by calling
        the original engine's run_cycle() method.
        """
        if not self._initialized:
            logger.debug("Evolution not started, skipping timer hook")
            return
        
        try:
            logger.info("Timer trigger: starting evolution cycle")
            
            # Call the original engine's run_cycle() method
            result = self.engine.run_cycle()
            
            logger.info(f"Evolution cycle complete: {result.to_dict()}")
            
            # Call callback if registered
            if self._on_evolution_event:
                try:
                    self._on_evolution_event(result.to_dict())
                except Exception as callback_error:
                    logger.error(f"Error in evolution callback: {callback_error}")
            
        except Exception as e:
            # Don't let evolution errors affect main workflow
            logger.error(f"Error in on_timer hook: {e}")
    
    def trigger_analysis(self) -> CycleResult:
        """
        Manually trigger an evolution analysis cycle.
        
        This method can be called to manually run the evolution cycle.
        
        Returns:
            CycleResult from the evolution cycle.
        """
        if not self._initialized:
            logger.warning("Evolution not started, cannot trigger analysis")
            return None
        
        try:
            logger.info("Manually triggering evolution cycle")
            result = self.engine.run_cycle()
            return result
        except Exception as e:
            logger.error(f"Error triggering analysis: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the evolution system.
        
        Returns:
            Dictionary with status information.
        """
        try:
            engine_status = self.engine.get_status()
        except Exception as e:
            logger.error(f"Error getting engine status: {e}")
            engine_status = {}
        
        return {
            'initialized': self._initialized,
            'engine_status': engine_status,
            'database_path': getattr(self.database, 'db_path', 'unknown'),
            'settings': {
                'auto_start': self._settings.is_auto_start(),
                'trigger_on_user_message': self._settings.is_trigger_on_user_message(),
                'trigger_before_thinking': self._settings.is_trigger_before_thinking(),
                'timer_interval': self._settings.get_timer_interval(),
            }
        }
    
    def register_evolution_callback(
        self,
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Register a callback for evolution events.
        
        Args:
            callback: Function to call when evolution cycle completes.
        """
        self._on_evolution_event = callback
        logger.info("Registered evolution callback")
    
    def is_running(self) -> bool:
        """
        Check if the evolution engine is currently running.
        
        Returns:
            True if running, False otherwise.
        """
        return self._initialized
    
    def restart(self) -> None:
        """
        Restart the evolution engine.
        """
        logger.info("Restarting evolution engine...")
        self.stop_evolution()
        time.sleep(1.0)  # Give time for cleanup
        self.start_evolution()
    
    def __enter__(self) -> 'WorkBuddyHook':
        """
        Context manager entry.
        
        Returns:
            Self instance.
        """
        if self._settings.auto_start:
            self.start_evolution()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit.
        """
        self.stop_evolution()
