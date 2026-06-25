"""事件总线 - 系统内部事件通信"""
import logging
from typing import Dict, List, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class SystemEvents:
    """系统事件类型"""
    CYCLE_START = "cycle_start"
    CYCLE_END = "cycle_end"
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    ERROR_DETECTED = "error_detected"
    SKILL_CREATED = "skill_created"
    SKILL_UPDATED = "skill_updated"
    MEMORY_CREATED = "memory_created"


@dataclass
class Event:
    """事件对象"""
    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "system"


class EventBus:
    """事件总线 - 发布/订阅模式"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_history: List[Event] = []
        self._max_history = 1000
    
    def subscribe(self, event_type: str, callback: Callable[[Event], None]):
        """订阅事件"""
        self._subscribers[event_type].append(callback)
        logger.debug(f"订阅事件: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅"""
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
    
    def publish(self, event: Event):
        """发布事件"""
        # 记录到历史
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # 通知订阅者
        callbacks = self._subscribers.get(event.event_type, [])
        callbacks.extend(self._subscribers.get("*", []))  # 广播到所有
        
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"事件处理失败: {e}")
    
    def publish_simple(self, event_type: str, data: Dict[str, Any] = None, source: str = "system"):
        """简化发布"""
        event = Event(event_type=event_type, data=data or {}, source=source)
        self.publish(event)
    
    def get_history(self, event_type: str = None, limit: int = 100) -> List[Event]:
        """获取事件历史"""
        if event_type:
            events = [e for e in self._event_history if e.event_type == event_type]
        else:
            events = self._event_history
        
        return events[-limit:]