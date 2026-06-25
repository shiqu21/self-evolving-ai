"""事件队列模块

使用queue.Queue实现线程安全事件队列。
支持事件的发布、订阅和处理。
"""

import queue
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Event:
    """事件数据类
    
    Attributes:
        event_type: 事件类型
        data: 事件数据
        timestamp: 事件时间戳
        source: 事件来源
        priority: 优先级（数字越小优先级越高）
    """
    
    event_type: str
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "unknown"
    priority: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            事件字典表示
        """
        return {
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "source": self.source,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """从字典创建事件
        
        Args:
            data: 事件字典
            
        Returns:
            事件对象
        """
        return cls(
            event_type=data.get("event_type", "unknown"),
            data=data.get("data", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            source=data.get("source", "unknown"),
            priority=data.get("priority", 5)
        )


class EventQueue:
    """线程安全事件队列
    
    使用queue.Queue实现线程安全的事件队列。
    支持优先级队列和事件过滤。
    
    Attributes:
        _queue: 内部队列对象
        _subscribers: 事件订阅者字典
        _running: 是否正在运行
        _processor_thread: 事件处理线程
        _max_size: 队列最大大小
        _logger: 日志记录器
    """
    
    def __init__(self, max_size: int = 1000) -> None:
        """初始化事件队列
        
        Args:
            max_size: 队列最大大小，超过此大小会阻塞发布者
        """
        self._queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=max_size)
        self._subscribers: Dict[str, List[Callable]] = {}
        self._running: bool = False
        self._processor_thread: Optional[threading.Thread] = None
        self._max_size: int = max_size
        self._lock: threading.RLock = threading.RLock()
        
        # 设置日志
        import logging
        self._logger = logging.getLogger(f"{__name__}.EventQueue")
    
    def publish(self, event: Event) -> bool:
        """发布事件到队列
        
        Args:
            event: 事件对象
            
        Returns:
            是否成功发布
        """
        try:
            # 使用优先级作为第一个元素，确保优先级队列工作
            priority_event = (event.priority, time.time(), event)
            self._queue.put(priority_event, block=True, timeout=5)
            self._logger.debug(f"Published event: {event.event_type}")
            return True
        except queue.Full:
            self._logger.error(f"Event queue is full, cannot publish event: {event.event_type}")
            return False
        except Exception as e:
            self._logger.error(f"Failed to publish event: {e}")
            return False
    
    def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "unknown",
        priority: int = 5
    ) -> bool:
        """便捷方法：直接发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件来源
            priority: 优先级
            
        Returns:
            是否成功发布
        """
        event = Event(
            event_type=event_type,
            data=data,
            source=source,
            priority=priority
        )
        return self.publish(event)
    
    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数，接收Event对象作为参数
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
            self._logger.debug(f"Subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """取消订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        with self._lock:
            if event_type in self._subscribers:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)
                    self._logger.debug(f"Unsubscribed from event: {event_type}")
    
    def start_processing(self) -> None:
        """启动事件处理线程"""
        if self._running:
            self._logger.warning("Event processing is already running")
            return
        
        self._running = True
        self._processor_thread = threading.Thread(
            target=self._process_events_loop,
            name="EventQueue-Processor",
            daemon=True
        )
        self._processor_thread.start()
        self._logger.info("Event processing started")
    
    def stop_processing(self) -> None:
        """停止事件处理线程"""
        self._running = False
        if self._processor_thread and self._processor_thread.is_alive():
            # 发送一个空事件来唤醒线程
            try:
                dummy_event = Event(event_type="_shutdown", data={}, priority=0)
                self._queue.put((0, time.time(), dummy_event), block=False)
            except Exception:
                pass
            self._processor_thread.join(timeout=5)
            self._logger.info("Event processing stopped")
    
    def _process_events_loop(self) -> None:
        """事件处理循环（内部方法）"""
        while self._running:
            try:
                # 从队列获取事件（阻塞，超时1秒）
                try:
                    priority, timestamp, event = self._queue.get(block=True, timeout=1)
                except queue.Empty:
                    continue
                
                # 处理关闭事件
                if event.event_type == "_shutdown":
                    self._queue.task_done()
                    break
                
                # 处理事件
                self._process_event(event)
                self._queue.task_done()
                
            except Exception as e:
                self._logger.error(f"Error in event processing loop: {e}")
    
    def _process_event(self, event: Event) -> None:
        """处理单个事件（内部方法）
        
        Args:
            event: 事件对象
        """
        with self._lock:
            subscribers = self._subscribers.get(event.event_type, [])
        
        if not subscribers:
            self._logger.debug(f"No subscribers for event: {event.event_type}")
            return
        
        self._logger.debug(f"Processing event: {event.event_type} with {len(subscribers)} subscribers")
        
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                self._logger.error(f"Error in event subscriber for {event.event_type}: {e}")
    
    def get_queue_size(self) -> int:
        """获取队列当前大小
        
        Returns:
            队列中的事件数量
        """
        return self._queue.qsize()
    
    def clear(self) -> None:
        """清空队列"""
        while not self._queue.empty():
            try:
                self._queue.get(block=False)
                self._queue.task_done()
            except queue.Empty:
                break
        self._logger.info("Event queue cleared")
    
    def is_running(self) -> bool:
        """检查是否正在处理事件
        
        Returns:
            是否正在运行
        """
        return self._running
    
    def get_status(self) -> Dict[str, Any]:
        """获取队列状态
        
        Returns:
            状态字典
        """
        with self._lock:
            subscriber_count = {
                event_type: len(callbacks)
                for event_type, callbacks in self._subscribers.items()
            }
        
        return {
            "running": self._running,
            "queue_size": self.get_queue_size(),
            "max_size": self._max_size,
            "subscribers": subscriber_count,
            "total_subscriber_count": sum(subscriber_count.values())
        }


# 全局事件队列实例
_event_queue_instance: Optional[EventQueue] = None


def get_event_queue(max_size: int = 1000) -> EventQueue:
    """获取全局事件队列实例
    
    Args:
        max_size: 队列最大大小（仅首次创建时有效）
        
    Returns:
        事件队列实例
    """
    global _event_queue_instance
    if _event_queue_instance is None:
        _event_queue_instance = EventQueue(max_size=max_size)
    return _event_queue_instance


def shutdown_event_queue() -> None:
    """关闭全局事件队列"""
    global _event_queue_instance
    if _event_queue_instance:
        _event_queue_instance.stop_processing()
        _event_queue_instance = None
