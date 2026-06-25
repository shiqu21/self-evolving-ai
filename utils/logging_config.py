"""日志配置模块

提供JSON格式的日志输出，包含timestamp、module、level、message等字段。
支持同时输出到文件和控制台。
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器
    
    将日志记录格式化为JSON格式，包含以下字段：
    - timestamp: 日志时间戳（ISO 8601格式）
    - module: 模块名称
    - level: 日志级别
    - message: 日志消息
    - logger: 日志记录器名称
    - thread: 线程名称（可选）
    - extra: 额外字段（可选）
    """
    
    def __init__(self, include_extra: bool = True) -> None:
        """初始化JSON格式化器
        
        Args:
            include_extra: 是否包含额外字段
        """
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON字符串
        
        Args:
            record: 日志记录
            
        Returns:
            JSON格式的日志字符串
        """
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "module": record.module,
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        
        # 添加线程信息
        if hasattr(record, 'threadName') and record.threadName:
            log_entry["thread"] = record.threadName
        
        # 添加额外字段
        if self.include_extra:
            extra_fields = [
                'stack_info', 'exc_info', 'lineno', 'funcName', 'pathname'
            ]
            for field in extra_fields:
                if hasattr(record, field):
                    value = getattr(record, field)
                    if value and field not in ['stack_info', 'exc_info']:
                        log_entry[field] = value
            
            # 处理异常信息
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(
    logger_name: str = "evolution",
    level: str = "INFO",
    log_format: str = "json",
    log_file: str = "logs/evolution.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    """设置日志配置
    
    Args:
        logger_name: 日志记录器名称
        level: 日志级别
        log_format: 日志格式（'json' 或 'text'）
        log_file: 日志文件路径
        max_bytes: 日志文件最大字节数
        backup_count: 备份文件数量
        console_output: 是否输出到控制台
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 清除现有handlers
    logger.handlers.clear()
    
    # 创建格式化器
    if log_format.lower() == "json":
        formatter = JSONFormatter(include_extra=True)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # 文件handler - 按大小滚动
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 控制台handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)
        logger.addHandler(console_handler)
    
    return logger


def setup_logging_from_settings(settings: Any) -> logging.Logger:
    """从配置对象设置日志
    
    Args:
        settings: 配置对象（Settings实例或类似对象）
        
    Returns:
        配置好的日志记录器
    """
    log_config = {
        "logger_name": "evolution",
        "level": "INFO",
        "log_format": "json",
        "log_file": "logs/evolution.log",
        "max_bytes": 10 * 1024 * 1024,
        "backup_count": 5,
        "console_output": True
    }
    
    # 从配置对象读取配置
    if hasattr(settings, 'get'):
        log_config["level"] = settings.get('logging.level', 'INFO')
        log_config["log_format"] = settings.get('logging.format', 'json')
        log_config["log_file"] = settings.get('logging.file', 'logs/evolution.log')
        log_config["max_bytes"] = settings.get('logging.max_bytes', 10 * 1024 * 1024)
        log_config["backup_count"] = settings.get('logging.backup_count', 5)
        log_config["console_output"] = settings.get('logging.console_output', True)
    
    return setup_logging(**log_config)


class LoggingMixin:
    """日志混合类
    
    为其他类提供日志记录功能。
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """初始化日志混合类"""
        super().__init__(*args, **kwargs)
        self._logger: Optional[logging.Logger] = None
    
    @property
    def logger(self) -> logging.Logger:
        """获取日志记录器
        
        Returns:
            日志记录器
        """
        if self._logger is None:
            self._logger = logging.getLogger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger
    
    def set_logger(self, logger: logging.Logger) -> None:
        """设置日志记录器
        
        Args:
            logger: 日志记录器
        """
        self._logger = logger


# 全局日志实例
_logger_instance: Optional[logging.Logger] = None


def get_logger(name: str = "evolution") -> logging.Logger:
    """获取全局日志实例
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = setup_logging(logger_name=name)
    return _logger_instance


def reset_logger() -> None:
    """重置全局日志实例"""
    global _logger_instance
    _logger_instance = None
