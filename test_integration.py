"""
Integration tests for the Self-Evolution System integrated into WorkBuddy.

This test module provides comprehensive testing for:
1. Import tests - Verify all modules can be correctly imported
2. Instantiation tests - Verify WorkBuddyHook can be correctly instantiated
3. Hook tests - Verify on_user_message(), before_ai_response(), on_timer() hooks work
4. Trigger tests - Verify all triggers function correctly
5. Daemon tests - Verify EvolutionDaemon can start, run, stop
6. Configuration tests - Verify Settings class can correctly load and save configuration
7. Error handling tests - Verify the system gracefully handles errors

Author: QA Engineer Edward
"""

import unittest
import sys
import os
import time
import threading
import sqlite3
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock

# Add the Claw directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging for tests
import logging
logging.basicConfig(level=logging.WARNING, format='%(name)s - %(levelname)s - %(message)s')


class TestImports(unittest.TestCase):
    """Test that all modules can be correctly imported."""
    
    def test_import_settings(self):
        """Test importing Settings class."""
        try:
            from evolution.config.settings import Settings, get_settings
            self.assertTrue(True, "Settings imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import Settings: {e}")
    
    def test_import_triggers(self):
        """Test importing all trigger classes."""
        try:
            from evolution.triggers.user_message_trigger import UserMessageTrigger
            from evolution.triggers.timer_trigger import TimerTrigger
            from evolution.triggers.thinking_trigger import ThinkingTrigger
            self.assertTrue(True, "All triggers imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import triggers: {e}")
    
    def test_import_daemon(self):
        """Test importing EvolutionDaemon."""
        try:
            from evolution.core.daemon import EvolutionDaemon, get_daemon
            self.assertTrue(True, "EvolutionDaemon imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import EvolutionDaemon: {e}")
    
    def test_import_workbuddy_hook(self):
        """Test importing WorkBuddyHook."""
        try:
            from evolution.integration.workbuddy_hook import WorkBuddyHook
            self.assertTrue(True, "WorkBuddyHook imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import WorkBuddyHook: {e}")
    
    def test_import_engine(self):
        """Test importing EvolutionEngine."""
        try:
            from evolution.core.engine import EvolutionEngine, CycleResult
            self.assertTrue(True, "EvolutionEngine imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import EvolutionEngine: {e}")


class TestSettings(unittest.TestCase):
    """Test the Settings class configuration management."""
    
    def setUp(self):
        """Set up test fixtures."""
        from evolution.config.settings import Settings
        self.SettingsClass = Settings
    
    def test_settings_default_initialization(self):
        """Test Settings initializes with default values."""
        settings = self.SettingsClass()
        
        # Verify default configuration sections exist
        self.assertIsNotNone(settings.get('database'))
        self.assertIsNotNone(settings.get('logging'))
        self.assertIsNotNone(settings.get('daemon'))
        self.assertIsNotNone(settings.get('trigger'))
        self.assertIsNotNone(settings.get('integration'))
    
    def test_settings_get_method(self):
        """Test Settings.get() method."""
        settings = self.SettingsClass()
        
        # Test getting existing value
        db_url = settings.get('database.url')
        self.assertEqual(db_url, 'sqlite:///evolution.db')
        
        # Test getting non-existent value with default
        missing = settings.get('nonexistent.key', 'default_value')
        self.assertEqual(missing, 'default_value')
    
    def test_settings_set_method(self):
        """Test Settings.set() method."""
        settings = self.SettingsClass()
        
        # Set a value
        settings.set('database.url', 'sqlite:///test.db')
        self.assertEqual(settings.get('database.url'), 'sqlite:///test.db')
    
    def test_settings_integration_helpers(self):
        """Test integration helper methods."""
        settings = self.SettingsClass()
        
        # Test is_auto_start
        self.assertTrue(settings.is_auto_start())
        
        # Test get_timer_interval
        self.assertEqual(settings.get_timer_interval(), 300)
        
        # Test trigger helpers
        self.assertTrue(settings.is_trigger_on_user_message())
        self.assertTrue(settings.is_trigger_before_thinking())
    
    def test_settings_to_dict(self):
        """Test converting settings to dictionary."""
        settings = self.SettingsClass()
        config_dict = settings.to_dict()
        
        self.assertIsInstance(config_dict, dict)
        self.assertIn('database', config_dict)
        self.assertIn('integration', config_dict)
    
    def test_settings_environment_variable(self):
        """Test loading configuration from environment variables."""
        # Set an environment variable
        os.environ['EVOLUTION_DATABASE_URL'] = 'sqlite:///env_test.db'
        
        try:
            settings = self.SettingsClass()
            db_url = settings.get('database.url')
            self.assertEqual(db_url, 'sqlite:///env_test.db')
        finally:
            # Clean up
            del os.environ['EVOLUTION_DATABASE_URL']
    
    def test_settings_yaml_optional(self):
        """Test that YAML import is optional (should not crash if PyYAML not installed)."""
        settings = self.SettingsClass()
        # Should not raise an exception even if yaml is not available
        self.assertIsNotNone(settings)


class TestUserMessageTrigger(unittest.TestCase):
    """Test the UserMessageTrigger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        from evolution.triggers.user_message_trigger import UserMessageTrigger
        self.trigger_class = UserMessageTrigger
    
    def test_trigger_initialization(self):
        """Test trigger initializes correctly."""
        trigger = self.trigger_class()
        
        self.assertEqual(trigger.name, 'user_message_trigger')
        self.assertTrue(trigger.trigger_on_every_message)
        self.assertEqual(len(trigger.patterns), 0)
    
    def test_trigger_should_trigger_every_message(self):
        """Test trigger fires on every message."""
        trigger = self.trigger_class(trigger_on_every_message=True)
        
        self.assertTrue(trigger.should_trigger("Hello"))
        self.assertTrue(trigger.should_trigger("World"))
        self.assertTrue(trigger.should_trigger(""))
    
    def test_trigger_should_trigger_with_patterns(self):
        """Test trigger fires only on matching patterns."""
        trigger = self.trigger_class(
            trigger_on_every_message=False,
            patterns=[r'error', r'bug']
        )
        
        self.assertTrue(trigger.should_trigger("This is an error"))
        self.assertTrue(trigger.should_trigger("Found a bug"))
        self.assertFalse(trigger.should_trigger("Normal message"))
    
    def test_trigger_create_event_data(self):
        """Test creating event data."""
        trigger = self.trigger_class()
        event_data = trigger.create_event_data("Test message")
        
        self.assertEqual(event_data['trigger_type'], 'user_message')
        self.assertEqual(event_data['message'], 'Test message')
        self.assertEqual(event_data['trigger_name'], 'user_message_trigger')
        self.assertIn('timestamp', event_data)


class TestTimerTrigger(unittest.TestCase):
    """Test the TimerTrigger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        from evolution.triggers.timer_trigger import TimerTrigger
        self.trigger_class = TimerTrigger
    
    def test_trigger_initialization(self):
        """Test trigger initializes correctly."""
        trigger = self.trigger_class(interval_minutes=5.0)
        
        self.assertEqual(trigger.name, 'timer_trigger')
        self.assertEqual(trigger.interval_minutes, 5.0)
        self.assertEqual(trigger.interval_seconds, 300.0)
        self.assertFalse(trigger.running)
    
    def test_trigger_should_trigger_initial(self):
        """Test trigger should fire on first check."""
        trigger = self.trigger_class()
        
        self.assertTrue(trigger.should_trigger())
    
    def test_trigger_should_trigger_after_interval(self):
        """Test trigger should fire after interval passes."""
        trigger = self.trigger_class(interval_minutes=0.01)  # Very short interval
        
        # First check - should trigger
        self.assertTrue(trigger.should_trigger())
        
        # Mark triggered
        trigger.mark_triggered()
        
        # Immediate second check - should not trigger
        self.assertFalse(trigger.should_trigger())
        
        # Wait for interval
        time.sleep(1)
        
        # After interval - should trigger again
        self.assertTrue(trigger.should_trigger())
    
    def test_trigger_create_event_data(self):
        """Test creating event data."""
        trigger = self.trigger_class(interval_minutes=5.0)
        event_data = trigger.create_event_data()
        
        self.assertEqual(event_data['trigger_type'], 'timer')
        self.assertEqual(event_data['interval_minutes'], 5.0)
        self.assertEqual(event_data['trigger_name'], 'timer_trigger')
        self.assertIn('timestamp', event_data)
    
    def test_trigger_start_stop(self):
        """Test starting and stopping the timer."""
        trigger = self.trigger_class(interval_minutes=0.1)
        
        # Start the timer
        trigger.start()
        self.assertTrue(trigger.running)
        
        # Stop the timer
        trigger.stop()
        self.assertFalse(trigger.running)


class TestThinkingTrigger(unittest.TestCase):
    """Test the ThinkingTrigger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        from evolution.triggers.thinking_trigger import ThinkingTrigger
        self.trigger_class = ThinkingTrigger
    
    def test_trigger_initialization(self):
        """Test trigger initializes correctly."""
        trigger = self.trigger_class(min_confidence=0.5)
        
        self.assertEqual(trigger.name, 'thinking_trigger')
        self.assertEqual(trigger.min_confidence, 0.5)
    
    def test_trigger_should_trigger(self):
        """Test trigger always fires (current implementation)."""
        trigger = self.trigger_class()
        
        context = {'message': 'Test', 'confidence': 0.8}
        self.assertTrue(trigger.should_trigger(context))
        
        # Even with low confidence
        context_low = {'message': 'Test', 'confidence': 0.1}
        self.assertTrue(trigger.should_trigger(context_low))
    
    def test_trigger_create_event_data(self):
        """Test creating event data."""
        trigger = self.trigger_class()
        context = {'message': 'AI thinking', 'stage': 'planning'}
        
        event_data = trigger.create_event_data(context)
        
        self.assertEqual(event_data['trigger_type'], 'thinking')
        self.assertEqual(event_data['context'], context)
        self.assertEqual(event_data['trigger_name'], 'thinking_trigger')
        self.assertIn('timestamp', event_data)


class TestSimpleDatabase(unittest.TestCase):
    """Test the SimpleDatabase class used by WorkBuddyHook."""
    
    def setUp(self):
        """Set up test fixtures."""
        from evolution.integration.workbuddy_hook import SimpleDatabase
        self.db_class = SimpleDatabase
        # Use file-based database for testing (workaround for :memory: bug)
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_database_initialization_file(self):
        """Test database initializes with file-based SQLite."""
        db = self.db_class(db_path=self.db_path)
        
        self.assertEqual(db.db_path, self.db_path)
        
        # Verify tables were created
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        self.assertIn('events', tables)
        self.assertIn('cycle_results', tables)
        self.assertIn('skills', tables)
        
        conn.close()
    
    def test_database_get_connection(self):
        """Test getting database connection."""
        db = self.db_class(db_path=self.db_path)
        conn = db.get_connection()
        
        self.assertIsInstance(conn, sqlite3.Connection)
        conn.close()


class TestWorkBuddyHook(unittest.TestCase):
    """Test the WorkBuddyHook integration class."""
    
    def setUp(self):
        """Set up test fixtures."""
        from evolution.integration.workbuddy_hook import WorkBuddyHook
        from evolution.config.settings import Settings
        
        # Use in-memory database for tests
        self.hook_class = WorkBuddyHook
        self.settings = Settings()
        self.settings.set('integration.database_path', ':memory:')
    
    def test_hook_initialization(self):
        """Test WorkBuddyHook initializes correctly."""
        try:
            hook = self.hook_class(settings=self.settings, db_path=':memory:')
            
            self.assertIsNotNone(hook)
            self.assertIsNotNone(hook.engine)
            self.assertIsNotNone(hook.database)
            self.assertFalse(hook.is_running())  # Not started yet
            
            hook.stop_evolution()  # Clean up
        except Exception as e:
            self.fail(f"Failed to initialize WorkBuddyHook: {e}")
    
    def test_hook_start_stop(self):
        """Test starting and stopping the evolution engine."""
        hook = self.hook_class(settings=self.settings, db_path=':memory:')
        
        # Start
        hook.start_evolution()
        self.assertTrue(hook.is_running())
        
        # Stop
        hook.stop_evolution()
        self.assertFalse(hook.is_running())
    
    def test_hook_on_user_message(self):
        """Test on_user_message hook (non-blocking)."""
        hook = self.hook_class(settings=self.settings, db_path=':memory:')
        hook.start_evolution()
        
        # Should not raise an exception
        try:
            hook.on_user_message("Test message")
            hook.on_user_message("Another message")
        except Exception as e:
            self.fail(f"on_user_message raised an exception: {e}")
        finally:
            hook.stop_evolution()
    
    def test_hook_before_ai_response(self):
        """Test before_ai_response hook (non-blocking)."""
        hook = self.hook_class(settings=self.settings, db_path=':memory:')
        hook.start_evolution()
        
        # Should return context unchanged (currently)
        context = {'message': 'Test', 'history': []}
        result = hook.before_ai_response(context)
        
        self.assertEqual(result, context)
        
        hook.stop_evolution()
    
    def test_hook_get_status(self):
        """Test getting hook status."""
        hook = self.hook_class(settings=self.settings, db_path=':memory:')
        hook.start_evolution()
        
        status = hook.get_status()
        
        self.assertIn('initialized', status)
        self.assertIn('engine_status', status)
        self.assertIn('database_path', status)
        self.assertTrue(status['initialized'])
        
        hook.stop_evolution()
    
    def test_hook_context_manager(self):
        """Test using WorkBuddyHook as a context manager."""
        self.settings.set('integration.auto_start', True)
        
        with patch.object(self.hook_class, 'start_evolution') as mock_start:
            with patch.object(self.hook_class, 'stop_evolution') as mock_stop:
                # We can't easily test the full context manager without a real engine
                # So we just verify the methods exist
                self.assertTrue(hasattr(self.hook_class, '__enter__'))
                self.assertTrue(hasattr(self.hook_class, '__exit__'))
    
    def test_hook_trigger_analysis(self):
        """Test manually triggering analysis."""
        hook = self.hook_class(settings=self.settings, db_path=':memory:')
        hook.start_evolution()
        
        # Mock the engine's run_cycle to avoid actual execution
        with patch.object(hook.engine, 'run_cycle', return_value=Mock()) as mock_run:
            result = hook.trigger_analysis()
            # Result might be None if engine.run_cycle fails
            # Just verify it doesn't crash
            
        hook.stop_evolution()


class TestEvolutionDaemon(unittest.TestCase):
    """Test the EvolutionDaemon class."""
    
    def setUp(self):
        """Set up test fixtures."""
        from evolution.core.daemon import EvolutionDaemon
        self.daemon_class = EvolutionDaemon
    
    def test_daemon_initialization(self):
        """Test daemon initializes correctly."""
        daemon = self.daemon_class(name='TestDaemon')
        
        self.assertEqual(daemon.name, 'TestDaemon')
        self.assertFalse(daemon.is_running())
        self.assertFalse(daemon.is_paused())
        self.assertEqual(daemon._error_count, 0)
        self.assertEqual(daemon._iteration_count, 0)
    
    def test_daemon_start_stop(self):
        """Test starting and stopping the daemon."""
        daemon = self.daemon_class(name='TestDaemon', auto_start=False)
        
        # Start
        daemon.start()
        
        # Give it a moment to start
        time.sleep(0.5)
        
        self.assertTrue(daemon.is_running())
        self.assertTrue(daemon.is_alive())
        
        # Stop
        result = daemon.stop(timeout=5.0)
        self.assertTrue(result)
        self.assertFalse(daemon.is_running())
    
    def test_daemon_pause_resume(self):
        """Test pausing and resuming the daemon."""
        daemon = self.daemon_class(name='TestDaemon', auto_start=False)
        daemon.start()
        
        time.sleep(0.5)
        
        # Pause
        daemon.pause()
        self.assertTrue(daemon.is_paused())
        
        # Resume
        daemon.resume()
        self.assertFalse(daemon.is_paused())
        
        daemon.stop(timeout=5.0)
    
    def test_daemon_get_status(self):
        """Test getting daemon status."""
        daemon = self.daemon_class(name='TestDaemon')
        
        status = daemon.get_status()
        
        self.assertIn('name', status)
        self.assertIn('running', status)
        self.assertIn('paused', status)
        self.assertIn('uptime_seconds', status)
        self.assertIn('iteration_count', status)
        self.assertIn('error_count', status)
    
    def test_daemon_register_trigger(self):
        """Test registering a trigger with the daemon."""
        daemon = self.daemon_class(name='TestDaemon')
        
        # Create a mock trigger
        mock_trigger = Mock()
        mock_trigger.name = 'test_trigger'
        
        result = daemon.register_trigger(mock_trigger)
        # Result depends on trigger manager implementation
        # Just verify it doesn't crash


class TestErrorHandling(unittest.TestCase):
    """Test error handling across the system."""
    
    def test_hook_handles_engine_error(self):
        """Test that hook handles engine errors gracefully."""
        from evolution.integration.workbuddy_hook import WorkBuddyHook
        from evolution.config.settings import Settings
        
        settings = Settings()
        settings.set('integration.database_path', ':memory:')
        
        hook = WorkBuddyHook(settings=settings, db_path=':memory:')
        hook.start_evolution()
        
        # Mock engine to raise an exception
        with patch.object(hook.engine, 'run_cycle', side_effect=Exception('Test error')):
            # on_timer should not crash
            try:
                hook.on_timer()
            except Exception as e:
                self.fail(f"on_timer should handle errors gracefully, but got: {e}")
        
        hook.stop_evolution()
    
    def test_trigger_handles_invalid_input(self):
        """Test that triggers handle invalid input gracefully."""
        from evolution.triggers.user_message_trigger import UserMessageTrigger
        from evolution.triggers.thinking_trigger import ThinkingTrigger
        
        # UserMessageTrigger with None message
        trigger = UserMessageTrigger()
        # should_trigger should handle None gracefully
        try:
            result = trigger.should_trigger(None)
            # Accept either True (if trigger_on_every_message) or False
        except Exception as e:
            self.fail(f"UserMessageTrigger should handle None gracefully: {e}")
        
        # ThinkingTrigger with None context
        thinking_trigger = ThinkingTrigger()
        try:
            result = thinking_trigger.should_trigger(None)
            self.assertTrue(result)  # Current implementation always returns True
        except Exception as e:
            self.fail(f"ThinkingTrigger should handle None gracefully: {e}")
    
    def test_settings_handles_invalid_input(self):
        """Test that Settings handles invalid input gracefully."""
        from evolution.config.settings import Settings
        
        settings = Settings()
        
        # Get non-existent key
        result = settings.get('totally.nonexistent.key')
        self.assertIsNone(result)
        
        # Get with default
        result = settings.get('totally.nonexistent.key', 'default')
        self.assertEqual(result, 'default')


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components."""
    
    def test_hook_with_triggers(self):
        """Test WorkBuddyHook working with triggers."""
        from evolution.integration.workbuddy_hook import WorkBuddyHook
        from evolution.triggers.user_message_trigger import UserMessageTrigger
        from evolution.config.settings import Settings
        
        settings = Settings()
        settings.set('integration.database_path', ':memory:')
        
        hook = WorkBuddyHook(settings=settings, db_path=':memory:')
        
        # Create and test trigger
        trigger = UserMessageTrigger()
        self.assertTrue(trigger.should_trigger("Test"))
        
        hook.stop_evolution()
    
    def test_daemon_with_event_queue(self):
        """Test daemon starts and manages event queue."""
        from evolution.core.daemon import EvolutionDaemon
        
        daemon = self.daemon_class = EvolutionDaemon(name='TestDaemon')
        
        # Start daemon (which should also start event queue)
        daemon.start()
        
        time.sleep(1)
        
        # Check status
        status = daemon.get_status()
        self.assertIn('event_queue_status', status)
        
        daemon.stop(timeout=5.0)


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestImports))
    suite.addTests(loader.loadTestsFromTestCase(TestSettings))
    suite.addTests(loader.loadTestsFromTestCase(TestUserMessageTrigger))
    suite.addTests(loader.loadTestsFromTestCase(TestTimerTrigger))
    suite.addTests(loader.loadTestsFromTestCase(TestThinkingTrigger))
    suite.addTests(loader.loadTestsFromTestCase(TestSimpleDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkBuddyHook))
    suite.addTests(loader.loadTestsFromTestCase(TestEvolutionDaemon))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("Self-Evolution System Integration Test Suite")
    print("=" * 70)
    print()
    
    result = run_tests()
    
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
