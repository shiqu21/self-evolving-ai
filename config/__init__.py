"""配置模块初始化文件

此模块提供配置管理功能，支持从多种来源加载配置。
"""

from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
