"""日志工具模块"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str = "evolution",
    log_dir: str = "logs",
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 文件日志 - 按日期滚动
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"evolution_{today}.log")
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    
    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # 格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 全局日志实例
_logger = None


def get_logger(name: str = "evolution") -> logging.Logger:
    """获取全局日志实例"""
    global _logger
    if _logger is None:
        _logger = setup_logger(name)
    return _logger