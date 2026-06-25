"""触发器管理器模块

管理触发器的注册、触发和事件处理。
提供线程安全的触发器操作。
"""

import threading
import logging
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict

from .base_trigger import BaseTrigger, TriggerContext
from .event_queue import Event, get_event_queue


class TriggerManager:
    """触发器管理器
    
    管理触发器的生命周期，包括注册、注销、触发等操作。
    所有操作都是线程安全的。
    
    Attributes:
        _triggers: 触发器字典（按名称索引）
        _event_triggers: 事件类型到触发器列表的映射
        _lock: 线程锁
        _event_queue: 事件队列
        _logger: 日志记录器
    """
    
    def __init__(self, auto_start: bool = True) -> None:
        """初始化触发器管理器
        
        Args:
            auto_start: 是否自动启动事件处理
        """
        self._triggers: Dict[str, BaseTrigger] = {}
        self._event_triggers: Dict[str, List[BaseTrigger]] = defaultdict(list)
        self._lock: threading.RLock = threading.RLock()
        self._event_queue = get_event_queue()
        self._logger = logging.getLogger(f"{__name__}.TriggerManager")
        
        # 注册为事件订阅者
        self._event_queue.subscribe("_trigger", self._on_trigger_event)
        self._event_queue.subscribe("trigger.fire", self._on_trigger_event)
        
        if auto_start:
            self._event_queue.start_processing()
            self._logger.info("TriggerManager initialized with auto-start")
        else:
            self._logger.info("TriggerManager initialized (manual start required)")
    
    def register_trigger(self, trigger: BaseTrigger) -> bool:
        """注册触发器
        
        Args:
            trigger: 触发器实例
            
        Returns:
            是否成功注册
            
        Example:
            >>> manager = TriggerManager()
            >>> trigger = MyTrigger(name='test')
            >>> manager.register_trigger(trigger)
            True
        """
        with self._lock:
            if trigger.name in self._triggers:
                self._logger.warning(f"Trigger '{trigger.name}' already registered, overwriting")
            
            self._triggers[trigger.name] = trigger
            self._logger.info(f"Registered trigger: {trigger.name}")
            return True
    
    def unregister_trigger(self, name: str) -> bool:
        """注销触发器
        
        Args:
            name: 触发器名称
            
        Returns:
            是否成功注销
        """
        with self._lock:
            if name not in self._triggers:
                self._logger.warning(f"Trigger '{name}' not found")
                return False
            
            # 从事件映射中移除
            trigger = self._triggers[name]
            for event_type in list(self._event_triggers.keys()):
                if trigger in self._event_triggers[event_type]:
                    self._event_triggers[event_type].remove(trigger)
                # 如果列表为空，删除键
                if not self._event_triggers[event_type]:
                    del self._event_triggers[event_type]
            
            # 从触发器字典中删除
            del self._triggers[name]
            self._logger.info(f"Unregistered trigger: {name}")
            return True
    
    def register_event_trigger(self, event_type: str, trigger: BaseTrigger) -> bool:
        """注册事件触发器（触发器会监听指定事件）
        
        Args:
            event_type: 事件类型
            trigger: 触发器实例
            
        Returns:
            是否成功注册
        """
        with self._lock:
            # 先确保触发器已注册
            if trigger.name not in self._triggers:
                self.register_trigger(trigger)
            
            # 添加到事件触发器映射
            if trigger not in self._event_triggers[event_type]:
                self._event_triggers[event_type].append(trigger)
                # 按优先级排序
                self._event_triggers[event_type].sort(key=lambda t: t.priority)
            
            self._logger.debug(f"Registered event trigger: {event_type} -> {trigger.name}")
            return True
    
    def unregister_event_trigger(self, event_type: str, trigger_name: str) -> bool:
        """注销事件触发器
        
        Args:
            event_type: 事件类型
            trigger_name: 触发器名称
            
        Returns:
            是否成功注销
        """
        with self._lock:
            if event_type not in self._event_triggers:
                return False
            
            trigger = self._triggers.get(trigger_name)
            if not trigger:
                return False
            
            if trigger in self._event_triggers[event_type]:
                self._event_triggers[event_type].remove(trigger)
                self._logger.debug(f"Unregistered event trigger: {event_type} -> {trigger_name}")
                return True
            
            return False
    
    def fire_event(self, event_type: str, data: Dict[str, Any]) -> List[Any]:
        """触发事件（线程安全）
        
        发布事件到事件队列，由事件处理器异步处理。
        
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            触发结果列表（异步情况下可能为空）
            
        Example:
            >>> results = manager.fire_event('error', {'message': 'Something wrong'})
        """
        try:
            # 发布事件到队列
            success = self._event_queue.publish_event(
                event_type="_trigger",
                data={
                    "trigger_event_type": event_type,
                    "trigger_data": data
                },
                source="TriggerManager",
                priority=5
            )
            
            if success:
                self._logger.debug(f"Fired event: {event_type}")
                return []  # 异步处理，返回空列表
            else:
                self._logger.error(f"Failed to fire event: {event_type}")
                return []
                
        except Exception as e:
            self._logger.error(f"Error firing event {event_type}: {e}")
            return []
    
    def fire_event_sync(self, event_type: str, data: Dict[str, Any]) -> List[Any]:
        """同步触发事件
        
        立即处理事件，不通过事件队列。
        
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            触发结果列表
        """
        return self._process_trigger_event(event_type, data)
    
    def _on_trigger_event(self, event: Event) -> None:
        """事件队列回调函数（内部方法）
        
        Args:
            event: 事件对象
        """
        event_type = event.data.get("trigger_event_type")
        data = event.data.get("trigger_data", {})
        
        if event_type:
            self._process_trigger_event(event_type, data)
    
    def _process_trigger_event(self, event_type: str, data: Dict[str, Any]) -> List[Any]:
        """处理触发事件（内部方法）
        
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            处理结果列表
        """
        results = []
        
        with self._lock:
            triggers = self._event_triggers.get(event_type, [])
        
        if not triggers:
            self._logger.debug(f"No triggers for event: {event_type}")
            return results
        
        self._logger.debug(f"Processing {len(triggers)} triggers for event: {event_type}")
        
        for trigger in triggers:
            try:
                result = trigger.execute(data)
                if result is not None:
                    results.append(result)
            except Exception as e:
                self._logger.error(f"Error executing trigger '{trigger.name}': {e}")
        
        return results
    
    def get_trigger(self, name: str) -> Optional[BaseTrigger]:
        """获取触发器
        
        Args:
            name: 触发器名称
            
        Returns:
            触发器实例或None
        """
        with self._lock:
            return self._triggers.get(name)
    
    def list_triggers(self) -> List[str]:
        """列出所有触发器名称
        
        Returns:
            触发器名称列表
        """
        with self._lock:
            return list(self._triggers.keys())
    
    def list_triggers_by_event(self, event_type: str) -> List[str]:
        """列出指定事件类型的触发器名称
        
        Args:
            event_type: 事件类型
            
        Returns:
            触发器名称列表
        """
        with self._lock:
            triggers = self._event_triggers.get(event_type, [])
            return [t.name for t in triggers]
    
    def enable_trigger(self, name: str) -> bool:
        """启用触发器
        
        Args:
            name: 触发器名称
            
        Returns:
            是否成功
        """
        trigger = self.get_trigger(name)
        if trigger:
            trigger.enable()
            self._logger.info(f"Enabled trigger: {name}")
            return True
        return False
    
    def disable_trigger(self, name: str) -> bool:
        """禁用触发器
        
        Args:
            name: 触发器名称
            
        Returns:
            是否成功
        """
        trigger = self.get_trigger(name)
        if trigger:
            trigger.disable()
            self._logger.info(f"Disabled trigger: {name}")
            return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取触发器管理器状态
        
        Returns:
            状态字典
        """
        with self._lock:
            trigger_statuses = {
                name: trigger.get_status()
                for name, trigger in self._triggers.items()
            }
            
            event_trigger_count = {
                event_type: len(triggers)
                for event_type, triggers in self._event_triggers.items()
            }
        
        return {
            "total_triggers": len(self._triggers),
            "triggers": trigger_statuses,
            "event_triggers": event_trigger_count,
            "event_queue_status": self._event_queue.get_status()
        }
    
    def shutdown(self) -> None:
        """关闭触发器管理器
        
        停止事件处理并清理资源。
        """
        self._logger.info("Shutting down TriggerManager...")
        
        # 注销所有触发器
        with self._lock:
            trigger_names = list(self._triggers.keys())
        
        for name in trigger_names:
            self.unregister_trigger(name)
        
        # 停止事件队列处理
        self._event_queue.stop_processing()
        
        self._logger.info("TriggerManager shutdown complete")


# 全局触发器管理器实例
_trigger_manager_instance: Optional[TriggerManager] = None


def get_trigger_manager(auto_start: bool = True) -> TriggerManager:
    """获取全局触发器管理器实例
    
    Args:
        auto_start: 是否自动启动（仅首次创建时有效）
        
    Returns:
        TriggerManager实例
    """
    global _trigger_manager_instance
    if _trigger_manager_instance is None:
        _trigger_manager_instance = TriggerManager(auto_start=auto_start)
    return _trigger_manager_instance


def shutdown_trigger_manager() -> None:
    """关闭全局触发器管理器"""
    global _trigger_manager_instance
    if _trigger_manager_instance:
        _trigger_manager_instance.shutdown()
        _trigger_manager_instance = None
