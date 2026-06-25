"""EvolutionDaemon 单元测试

测试守护进程、触发器管理器和事件队列的功能。
"""

import sys
import os
import unittest
import threading
import time
import logging
from typing import Any, Dict, List
from dataclasses import dataclass

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入被测试模块
from core.daemon import (
    EvolutionDaemon,
    get_daemon,
    start_daemon,
    stop_daemon,
    shutdown_daemon
)
from core.trigger_manager import TriggerManager, get_trigger_manager
from core.base_trigger import BaseTrigger, create_simple_trigger
from core.event_queue import Event, EventQueue, get_event_queue


class TestTrigger(BaseTrigger):
    """测试用触发器实现"""
    
    def __init__(self, name: str, should_trigger_result: bool = True):
        super().__init__(name=name, enabled=True, priority=5)
        self.should_trigger_result = should_trigger_result
        self.triggered_data: List[Dict[str, Any]] = []
        self.trigger_count = 0
    
    def should_trigger(self, data: Dict[str, Any]) -> bool:
        """判断是否应该触发"""
        return self.should_trigger_result
    
    def on_trigger(self, data: Dict[str, Any]) -> Any:
        """触发时执行的操作"""
        self.triggered_data.append(data)
        self.trigger_count += 1
        return f"Triggered: {self.name}"


class TestEventQueue(unittest.TestCase):
    """测试事件队列"""
    
    def setUp(self) -> None:
        """测试前设置"""
        self.event_queue = EventQueue(max_size=10)
    
    def tearDown(self) -> None:
        """测试后清理"""
        if self.event_queue.is_running():
            self.event_queue.stop_processing()
    
    def test_publish_and_subscribe(self) -> None:
        """测试发布和订阅事件"""
        received_events: List[Event] = []
        
        def callback(event: Event) -> None:
            received_events.append(event)
        
        # 订阅事件
        self.event_queue.subscribe("test_event", callback)
        
        # 发布事件
        event = Event(event_type="test_event", data={"message": "Hello"})
        result = self.event_queue.publish(event)
        
        # 验证
        self.assertTrue(result)
        time.sleep(0.1)  # 等待事件处理
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].data["message"], "Hello")
    
    def test_priority_queue(self) -> None:
        """测试优先级队列"""
        received_priorities: List[int] = []
        
        def callback(event: Event) -> None:
            received_priorities.append(event.priority)
        
        self.event_queue.subscribe("priority_event", callback)
        self.event_queue.start_processing()
        
        # 发布不同优先级的事件
        self.event_queue.publish_event("priority_event", {}, priority=5)
        self.event_queue.publish_event("priority_event", {}, priority=1)
        self.event_queue.publish_event("priority_event", {}, priority=3)
        
        time.sleep(0.2)  # 等待事件处理
        
        # 验证优先级（优先级数字越小越先处理）
        self.assertEqual(len(received_priorities), 3)
        self.assertEqual(received_priorities[0], 1)
        
    def test_queue_status(self) -> None:
        """测试队列状态"""
        status = self.event_queue.get_status()
        
        self.assertIn("running", status)
        self.assertIn("queue_size", status)
        self.assertIn("subscribers", status)


class TestBaseTrigger(unittest.TestCase):
    """测试触发器基类"""
    
    def test_trigger_creation(self) -> None:
        """测试触发器创建"""
        trigger = TestTrigger(name="test_trigger")
        
        self.assertEqual(trigger.name, "test_trigger")
        self.assertTrue(trigger.enabled)
        self.assertEqual(trigger.priority, 5)
    
    def test_trigger_enable_disable(self) -> None:
        """测试触发器启用/禁用"""
        trigger = TestTrigger(name="test_trigger")
        
        # 初始状态：启用
        self.assertTrue(trigger.is_enabled())
        
        # 禁用
        trigger.disable()
        self.assertFalse(trigger.is_enabled())
        
        # 启用
        trigger.enable()
        self.assertTrue(trigger.is_enabled())
    
    def test_trigger_execution(self) -> None:
        """测试触发器执行"""
        trigger = TestTrigger(name="test_trigger", should_trigger_result=True)
        data = {"message": "Test"}
        
        result = trigger.execute(data)
        
        self.assertIsNotNone(result)
        self.assertEqual(trigger.trigger_count, 1)
        self.assertEqual(len(trigger.triggered_data), 1)
        self.assertEqual(trigger.triggered_data[0]["message"], "Test")
    
    def test_trigger_should_not_trigger(self) -> None:
        """测试触发器不应该触发的情况"""
        trigger = TestTrigger(name="test_trigger", should_trigger_result=False)
        data = {"message": "Test"}
        
        result = trigger.execute(data)
        
        self.assertIsNone(result)
        self.assertEqual(trigger.trigger_count, 0)
    
    def test_trigger_disabled(self) -> None:
        """测试禁用的触发器不执行"""
        trigger = TestTrigger(name="test_trigger", should_trigger_result=True)
        trigger.disable()
        
        data = {"message": "Test"}
        result = trigger.execute(data)
        
        self.assertIsNone(result)
        self.assertEqual(trigger.trigger_count, 0)
    
    def test_simple_trigger_creation(self) -> None:
        """测试简单触发器创建"""
        def on_trigger_func(data: Dict[str, Any]) -> str:
            return f"Handled: {data.get('msg')}"
        
        trigger = create_simple_trigger(
            name="simple_trigger",
            trigger_func=on_trigger_func
        )
        
        self.assertIsInstance(trigger, BaseTrigger)
        self.assertEqual(trigger.name, "simple_trigger")


class TestTriggerManager(unittest.TestCase):
    """测试触发器管理器"""
    
    def setUp(self) -> None:
        """测试前设置"""
        self.manager = TriggerManager(auto_start=False)
        self.trigger = TestTrigger(name="test_trigger")
    
    def tearDown(self) -> None:
        """测试后清理"""
        self.manager.shutdown()
    
    def test_register_trigger(self) -> None:
        """测试注册触发器"""
        result = self.manager.register_trigger(self.trigger)
        
        self.assertTrue(result)
        self.assertIn("test_trigger", self.manager.list_triggers())
    
    def test_unregister_trigger(self) -> None:
        """测试注销触发器"""
        self.manager.register_trigger(self.trigger)
        result = self.manager.unregister_trigger("test_trigger")
        
        self.assertTrue(result)
        self.assertNotIn("test_trigger", self.manager.list_triggers())
    
    def test_register_event_trigger(self) -> None:
        """测试注册事件触发器"""
        result = self.manager.register_event_trigger("test_event", self.trigger)
        
        self.assertTrue(result)
        self.assertIn("test_trigger", self.manager.list_triggers_by_event("test_event"))
    
    def test_fire_event(self) -> None:
        """测试触发事件"""
        self.manager.register_event_trigger("test_event", self.trigger)
        
        results = self.manager.fire_event("test_event", {"data": "test"})
        
        # 异步处理，可能需要等待
        time.sleep(0.1)
        
        self.assertEqual(self.trigger.trigger_count, 1)
    
    def test_get_trigger_status(self) -> None:
        """测试获取触发器状态"""
        self.manager.register_trigger(self.trigger)
        status = self.manager.get_status()
        
        self.assertIn("total_triggers", status)
        self.assertEqual(status["total_triggers"], 1)


class TestEvolutionDaemon(unittest.TestCase):
    """测试进化守护进程"""
    
    def setUp(self) -> None:
        """测试前设置"""
        self.daemon = EvolutionDaemon(name="test_daemon", auto_start=False)
    
    def tearDown(self) -> None:
        """测试后清理"""
        if self.daemon.is_running():
            self.daemon.stop(timeout=2.0)
    
    def test_daemon_creation(self) -> None:
        """测试守护进程创建"""
        self.assertEqual(self.daemon.name, "test_daemon")
        self.assertFalse(self.daemon.is_running())
    
    def test_daemon_start_stop(self) -> None:
        """测试守护进程启动和停止"""
        # 启动
        self.daemon.start()
        time.sleep(0.5)  # 等待线程启动
        
        self.assertTrue(self.daemon.is_running())
        self.assertTrue(self.daemon.is_alive())
        
        # 停止
        result = self.daemon.stop(timeout=2.0)
        
        self.assertTrue(result)
        self.assertFalse(self.daemon.is_running())
    
    def test_daemon_register_trigger(self) -> None:
        """测试守护进程注册触发器"""
        trigger = TestTrigger(name="daemon_trigger")
        result = self.daemon.register_trigger(trigger)
        
        self.assertTrue(result)
        
        # 验证触发器已注册
        status = self.daemon.get_status()
        self.assertIn("trigger_manager_status", status)
    
    def test_daemon_pause_resume(self) -> None:
        """测试守护进程暂停和恢复"""
        self.daemon.start()
        time.sleep(0.2)
        
        # 暂停
        self.daemon.pause()
        self.assertTrue(self.daemon.is_paused())
        
        # 恢复
        self.daemon.resume()
        self.assertFalse(self.daemon.is_paused())
        
        self.daemon.stop(timeout=2.0)
    
    def test_daemon_status(self) -> None:
        """测试获取守护进程状态"""
        self.daemon.start()
        time.sleep(0.2)
        
        status = self.daemon.get_status()
        
        self.assertIn("name", status)
        self.assertIn("running", status)
        self.assertIn("uptime_seconds", status)
        self.assertIn("iteration_count", status)
        
        self.daemon.stop(timeout=2.0)
    
    def test_daemon_fire_event(self) -> None:
        """测试守护进程触发事件"""
        self.daemon.start()
        time.sleep(0.2)
        
        trigger = TestTrigger(name="event_trigger")
        self.daemon.register_event_trigger("test_event", trigger)
        
        results = self.daemon.fire_event("test_event", {"test": True})
        
        time.sleep(0.2)  # 等待事件处理
        
        self.assertEqual(trigger.trigger_count, 1)
        
        self.daemon.stop(timeout=2.0)


class TestGlobalInstances(unittest.TestCase):
    """测试全局实例管理函数"""
    
    def test_get_event_queue(self) -> None:
        """测试获取事件队列全局实例"""
        queue1 = get_event_queue()
        queue2 = get_event_queue()
        
        self.assertIs(queue1, queue2)
    
    def test_get_trigger_manager(self) -> None:
        """测试获取触发器管理器全局实例"""
        manager1 = get_trigger_manager(auto_start=False)
        manager2 = get_trigger_manager()
        
        self.assertIs(manager1, manager2)
        
        # 清理
        manager1.shutdown()
    
    def test_get_daemon(self) -> None:
        """测试获取守护进程全局实例"""
        daemon1 = get_daemon(auto_start=False)
        daemon2 = get_daemon()
        
        self.assertIs(daemon1, daemon2)


def run_tests() -> None:
    """运行所有测试"""
    # 配置日志
    logging.basicConfig(level=logging.DEBUG)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestEventQueue))
    suite.addTests(loader.loadTestsFromTestCase(TestBaseTrigger))
    suite.addTests(loader.loadTestsFromTestCase(TestTriggerManager))
    suite.addTests(loader.loadTestsFromTestCase(TestEvolutionDaemon))
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalInstances))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == "__main__":
    run_tests()
