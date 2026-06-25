"""触发器基类模块

定义所有触发器的抽象基类。
触发器用于监听事件并根据条件触发相应动作。
"""

import abc
import threading
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class TriggerContext:
    """触发器执行上下文
    
    Attributes:
        event: 触发事件
        data: 事件数据
        metadata: 额外元数据
        should_stop: 是否应该停止执行
    """
    
    event: Any
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    should_stop: bool = False


class BaseTrigger(abc.ABC):
    """触发器抽象基类
    
    所有触发器必须继承此类并实现抽象方法。
    触发器用于监听特定事件并在满足条件时执行动作。
    
    Attributes:
        name: 触发器名称（唯一标识）
        enabled: 是否启用
        priority: 优先级（数字越小优先级越高）
        _lock: 线程锁（用于线程安全）
        
    Example:
        >>> class MyTrigger(BaseTrigger):
        ...     def should_trigger(self, data):
        ...         return True
        ...     def on_trigger(self, data):
        ...         print("Triggered!")
    """
    
    def __init__(self, name: str, enabled: bool = True, priority: int = 5) -> None:
        """初始化触发器
        
        Args:
            name: 触发器名称（必须唯一）
            enabled: 是否启用
            priority: 优先级（0-10，数字越小优先级越高）
        """
        self.name: str = name
        self.enabled: bool = enabled
        self.priority: int = max(0, min(10, priority))
        self._lock: threading.RLock = threading.RLock()
        self._execution_count: int = 0
        self._last_execution_time: Optional[float] = None
    
    @abc.abstractmethod
    def should_trigger(self, data: Dict[str, Any]) -> bool:
        """判断是否应该触发（抽象方法）
        
        子类必须实现此方法，根据输入数据判断是否应该触发。
        
        Args:
            data: 触发数据，通常包含事件相关信息
            
        Returns:
            True表示应该触发，False表示不应该触发
            
        Example:
            >>> def should_trigger(self, data):
            ...     return data.get('error_count', 0) > 3
        """
        pass
    
    @abc.abstractmethod
    def on_trigger(self, data: Dict[str, Any]) -> Any:
        """触发时执行的操作（抽象方法）
        
        子类必须实现此方法，定义触发时要执行的具体操作。
        
        Args:
            data: 触发数据
            
        Returns:
            执行结果（可以是任意类型）
            
        Raises:
            Exception: 子类可以抛出异常
            
        Example:
            >>> def on_trigger(self, data):
            ...     send_alert(data.get('message'))
            ...     return True
        """
        pass
    
    def enable(self) -> None:
        """启用触发器"""
        with self._lock:
            self.enabled = True
    
    def disable(self) -> None:
        """禁用触发器"""
        with self._lock:
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """检查触发器是否启用
        
        Returns:
            是否启用
        """
        with self._lock:
            return self.enabled
    
    def execute(self, data: Dict[str, Any]) -> Any:
        """执行触发器
        
        此方法会检查是否应该触发，如果应该则执行on_trigger。
        
        Args:
            data: 触发数据
            
        Returns:
            如果触发了返回on_trigger的结果，否则返回None
            
        Raises:
            Exception: 如果on_trigger抛出异常
        """
        with self._lock:
            if not self.enabled:
                return None
            
            if not self.should_trigger(data):
                return None
            
            # 更新执行统计
            self._execution_count += 1
            import time
            self._last_execution_time = time.time()
            
            # 执行触发动作
            return self.on_trigger(data)
    
    def get_status(self) -> Dict[str, Any]:
        """获取触发器状态
        
        Returns:
            状态字典
        """
        with self._lock:
            return {
                "name": self.name,
                "enabled": self.enabled,
                "priority": self.priority,
                "execution_count": self._execution_count,
                "last_execution_time": self._last_execution_time
            }
    
    def __lt__(self, other: "BaseTrigger") -> bool:
        """比较优先级（用于排序）
        
        Args:
            other: 另一个触发器
            
        Returns:
            当前触发器优先级是否更高
        """
        return self.priority < other.priority
    
    def __repr__(self) -> str:
        """字符串表示
        
        Returns:
            触发器的字符串表示
        """
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled}, priority={self.priority})"


class TriggerDecorator:
    """触发器装饰器
    
    用于快速创建简单的触发器。
    
    Example:
        >>> @TriggerDecorator.create(name='my_trigger')
        ... def handle_event(data):
        ...     print(f"Received: {data}")
    """
    
    @staticmethod
    def create(
        name: str,
        enabled: bool = True,
        priority: int = 5,
        condition: Optional[callable] = None
    ) -> callable:
        """创建触发器装饰器
        
        Args:
            name: 触发器名称
            enabled: 是否启用
            priority: 优先级
            condition: 条件函数，用于判断should_trigger
            
        Returns:
            装饰器函数
        """
        def decorator(func: callable) -> BaseTrigger:
            """装饰器
            
            Args:
                func: 被装饰的函数
                
            Returns:
                触发器实例
            """
            class DecoratedTrigger(BaseTrigger):
                def should_trigger(self, data):
                    if condition:
                        return condition(data)
                    return True
                
                def on_trigger(self, data):
                    return func(data)
            
            return DecoratedTrigger(name=name, enabled=enabled, priority=priority)
        
        return decorator


# 便捷函数：创建简单触发器
def create_simple_trigger(
    name: str,
    trigger_func: callable,
    condition_func: Optional[callable] = None,
    enabled: bool = True,
    priority: int = 5
) -> BaseTrigger:
    """创建简单触发器
    
    Args:
        name: 触发器名称
        trigger_func: 触发时执行的函数
        condition_func: 条件函数（可选）
        enabled: 是否启用
        priority: 优先级
        
    Returns:
        触发器实例
        
    Example:
        >>> def on_error(data):
        ...     print(f"Error: {data.get('message')}")
        >>> trigger = create_simple_trigger('error_handler', on_error)
    """
    class SimpleTrigger(BaseTrigger):
        def should_trigger(self, data):
            if condition_func:
                return condition_func(data)
            return True
        
        def on_trigger(self, data):
            return trigger_func(data)
    
    return SimpleTrigger(name=name, enabled=enabled, priority=priority)
