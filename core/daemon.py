"""守护进程模块

实现后台守护进程，管理触发器和事件处理。
使用threading.Thread实现，支持start()/stop()/get_status()。
"""

import atexit
import signal
import sys
import threading
import time
import traceback
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .trigger_manager import TriggerManager, get_trigger_manager
from .event_queue import EventQueue, get_event_queue
from .base_trigger import BaseTrigger


class EvolutionDaemon(threading.Thread):
    """进化引擎守护进程
    
    使用threading.Thread实现后台守护进程。
    管理触发器、事件队列和系统生命周期。
    
    Attributes:
        name: 守护进程名称
        _running: 是否正在运行
        _paused: 是否暂停
        _trigger_manager: 触发器管理器
        _event_queue: 事件队列
        _shutdown_event: 关闭事件
        _start_time: 启动时间
        _error_count: 错误计数
        _iteration_count: 迭代计数
        _config: 配置对象
        
    Example:
        >>> daemon = EvolutionDaemon()
        >>> daemon.register_trigger(my_trigger)
        >>> daemon.start()  # 启动守护进程
        >>> time.sleep(10)
        >>> daemon.stop()   # 停止守护进程
    """
    
    def __init__(
        self,
        name: str = "EvolutionDaemon",
        config: Optional[Any] = None,
        auto_start: bool = False
    ) -> None:
        """初始化守护进程
        
        Args:
            name: 守护进程名称
            config: 配置对象
            auto_start: 是否自动启动
        """
        super().__init__(name=name, daemon=True)
        
        self.name: str = name
        self._running: bool = False
        self._paused: bool = False
        self._trigger_manager: TriggerManager = get_trigger_manager(auto_start=False)
        self._event_queue: EventQueue = get_event_queue()
        self._shutdown_event: threading.Event = threading.Event()
        self._start_time: Optional[float] = None
        self._error_count: int = 0
        self._iteration_count: int = 0
        self._config: Optional[Any] = config
        
        # 设置日志
        self._logger: logging.Logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )
        
        # 注册清理函数
        atexit.register(self._cleanup)
        self._register_signal_handlers()
        
        self._logger.info(f"EvolutionDaemon '{name}' initialized")
        
        # 自动启动
        if auto_start:
            self.start()
    
    def _register_signal_handlers(self) -> None:
        """注册信号处理器"""
        if sys.platform!= 'win32':
            try:
                signal.signal(signal.SIGTERM, self._signal_handler)
                signal.signal(signal.SIGINT, self._signal_handler)
            except Exception as e:
                self._logger.warning(f"Failed to register signal handlers: {e}")
    
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """信号处理器
        
        Args:
            signum: 信号编号
            frame: 栈帧
        """
        self._logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def register_trigger(self, trigger: BaseTrigger) -> bool:
        """注册触发器
        
        Args:
            trigger: 触发器实例
            
        Returns:
            是否成功注册
            
        Example:
            >>> daemon = EvolutionDaemon()
            >>> trigger = MyTrigger(name='test')
            >>> daemon.register_trigger(trigger)
        """
        try:
            result = self._trigger_manager.register_trigger(trigger)
            if result:
                self._logger.info(f"Registered trigger: {trigger.name}")
            return result
        except Exception as e:
            self._logger.error(f"Failed to register trigger: {e}")
            return False
    
    def unregister_trigger(self, name: str) -> bool:
        """注销触发器
        
        Args:
            name: 触发器名称
            
        Returns:
            是否成功注销
        """
        try:
            result = self._trigger_manager.unregister_trigger(name)
            if result:
                self._logger.info(f"Unregistered trigger: {name}")
            return result
        except Exception as e:
            self._logger.error(f"Failed to unregister trigger: {e}")
            return False
    
    def register_event_trigger(self, event_type: str, trigger: BaseTrigger) -> bool:
        """注册事件触发器
        
        Args:
            event_type: 事件类型
            trigger: 触发器实例
            
        Returns:
            是否成功注册
        """
        try:
            result = self._trigger_manager.register_event_trigger(event_type, trigger)
            if result:
                self._logger.info(f"Registered event trigger: {event_type} -> {trigger.name}")
            return result
        except Exception as e:
            self._logger.error(f"Failed to register event trigger: {e}")
            return False
    
    def start(self, start_event_queue: bool = True) -> None:
        """启动守护进程
        
        Args:
            start_event_queue: 是否同时启动事件队列处理
            
        Example:
            >>> daemon = EvolutionDaemon()
            >>> daemon.register_trigger(my_trigger)
            >>> daemon.start()
        """
        if self._running:
            self._logger.warning("Daemon is already running")
            return
        
        self._running = True
        self._start_time = time.time()
        self._shutdown_event.clear()
        
        # 启动事件队列处理
        if start_event_queue and not self._event_queue.is_running():
            self._event_queue.start_processing()
            self._logger.info("Event queue processing started")
        
        # 启动线程
        super().start()
        
        self._logger.info(f"EvolutionDaemon '{self.name}' started")
    
    def stop(self, timeout: Optional[float] = None) -> bool:
        """停止守护进程
        
        Args:
            timeout: 等待超时时间（秒），None表示无限等待
            
        Returns:
            是否成功停止
            
        Example:
            >>> daemon.stop(timeout=10.0)
        """
        if not self._running:
            self._logger.warning("Daemon is not running")
            return True
        
        self._logger.info(f"Stopping EvolutionDaemon '{self.name}'...")
        
        # 设置停止标志
        self._running = False
        self._shutdown_event.set()
        
        # 停止事件队列处理
        try:
            self._event_queue.stop_processing()
        except Exception as e:
            self._logger.error(f"Error stopping event queue: {e}")
        
        # 停止触发器管理器
        try:
            self._trigger_manager.shutdown()
        except Exception as e:
            self._logger.error(f"Error shutting down trigger manager: {e}")
        
        # 等待线程结束
        if self.is_alive():
            self.join(timeout=timeout)
            if self.is_alive():
                self._logger.warning(f"Daemon did not stop within {timeout} seconds")
                return False
        
        self._logger.info(f"EvolutionDaemon '{self.name}' stopped")
        return True
    
    def pause(self) -> None:
        """暂停守护进程"""
        self._paused = True
        self._logger.info(f"EvolutionDaemon '{self.name}' paused")
    
    def resume(self) -> None:
        """恢复守护进程"""
        self._paused = False
        self._logger.info(f"EvolutionDaemon '{self.name}' resumed")
    
    def is_running(self) -> bool:
        """检查是否正在运行
        
        Returns:
            是否正在运行
        """
        return self._running and not self._shutdown_event.is_set()
    
    def is_paused(self) -> bool:
        """检查是否暂停
        
        Returns:
            是否暂停
        """
        return self._paused
    
    def run(self) -> None:
        """守护进程主循环（线程入口点）
        
        This method is called when the thread is started.
        """
        self._logger.info(f"EvolutionDaemon '{self.name}' main loop started")
        
        try:
            while self._running and not self._shutdown_event.is_set():
                try:
                    # 检查是否暂停
                    if self._paused:
                        time.sleep(1)
                        continue
                    
                    # 主循环逻辑
                    self._iteration_count += 1
                    self._main_loop_iteration()
                    
                    # 检查关闭事件
                    if self._shutdown_event.wait(timeout=1.0):
                        break
                    
                except Exception as e:
                    self._error_count += 1
                    self._logger.error(f"Error in main loop (iteration {self._iteration_count}): {e}")
                    self._logger.error(traceback.format_exc())
                    
                    # 如果错误太多，停止运行
                    if self._error_count > 100:
                        self._logger.critical("Too many errors, stopping daemon")
                        break
                    
                    time.sleep(5)  # 错误后等待
        
        except Exception as e:
            self._logger.critical(f"Fatal error in daemon main loop: {e}")
            self._logger.critical(traceback.format_exc())
        
        finally:
            self._cleanup()
            self._logger.info(f"EvolutionDaemon '{self.name}' main loop ended")
    
    def _main_loop_iteration(self) -> None:
        """主循环单次迭代（可被子类重写）
        
        默认实现：空操作，等待1秒。
        子类可以重写此方法实现具体逻辑。
        """
        time.sleep(1)
    
    def _cleanup(self) -> None:
        """清理资源（内部方法）
        
        在守护进程停止时调用，清理所有资源。
        """
        self._logger.info("Cleaning up resources...")
        
        try:
            # 停止事件队列
            if self._event_queue.is_running():
                self._event_queue.stop_processing()
            
            # 关闭触发器管理器
            self._trigger_manager.shutdown()
            
            self._logger.info("Cleanup complete")
        
        except Exception as e:
            self._logger.error(f"Error during cleanup: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取守护进程状态
            
        Returns:
            状态字典
            
        Example:
            >>> status = daemon.get_status()
            >>> print(status['uptime'])
        """
        current_time = time.time()
        uptime = (current_time - self._start_time) if self._start_time else 0
        
        return {
            "name": self.name,
            "running": self._running,
            "paused": self._paused,
            "uptime_seconds": uptime,
            "uptime_human": self._format_uptime(uptime),
            "start_time": datetime.fromtimestamp(self._start_time).isoformat() if self._start_time else None,
            "iteration_count": self._iteration_count,
            "error_count": self._error_count,
            "thread_alive": self.is_alive(),
            "trigger_manager_status": self._trigger_manager.get_status(),
            "event_queue_status": self._event_queue.get_status()
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间
            
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时间字符串
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def fire_event(self, event_type: str, data: Dict[str, Any]) -> List[Any]:
        """触发事件
            
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            触发结果列表
        """
        return self._trigger_manager.fire_event(event_type, data)
    
    def fire_event_sync(self, event_type: str, data: Dict[str, Any]) -> List[Any]:
        """同步触发事件
            
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            触发结果列表
        """
        return self._trigger_manager.fire_event_sync(event_type, data)


# 全局守护进程实例
_daemon_instance: Optional[EvolutionDaemon] = None


def get_daemon(config: Optional[Any] = None, auto_start: bool = False) -> EvolutionDaemon:
    """获取全局守护进程实例
        
    Args:
        config: 配置对象（仅首次创建时有效）
        auto_start: 是否自动启动（仅首次创建时有效）
        
    Returns:
        EvolutionDaemon实例
    """
    global _daemon_instance
    if _daemon_instance is None:
        _daemon_instance = EvolutionDaemon(config=config, auto_start=auto_start)
    return _daemon_instance


def start_daemon(config: Optional[Any] = None) -> EvolutionDaemon:
    """启动全局守护进程
        
    Args:
        config: 配置对象
        
    Returns:
        守护进程实例
    """
    daemon = get_daemon(config=config, auto_start=False)
    if not daemon.is_running():
        daemon.start()
    return daemon


def stop_daemon(timeout: Optional[float] = None) -> bool:
    """停止全局守护进程
        
    Args:
        timeout: 等待超时时间
        
    Returns:
        是否成功停止
    """
    global _daemon_instance
    if _daemon_instance:
        result = _daemon_instance.stop(timeout=timeout)
        if result:
            _daemon_instance = None
        return result
    return True


def shutdown_daemon() -> None:
    """关闭全局守护进程（atexit处理）"""
    global _daemon_instance
    if _daemon_instance:
        try:
            _daemon_instance.stop(timeout=5.0)
        except Exception as e:
            logging.error(f"Error shutting down daemon: {e}")
        finally:
            _daemon_instance = None


# 注册atexit清理函数
atexit.register(shutdown_daemon)
