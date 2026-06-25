"""配置管理类

支持从配置文件、YAML文件和环境变量加载配置。
使用优先级：环境变量 > YAML配置文件 > 默认配置文件 > 默认值
"""

import os
import json
try:
    import yaml
except ImportError:
    yaml = None  # yaml可选依赖，未安装时跳过YAML配置加载
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Settings:
    """配置管理类
    
    支持从以下来源加载配置（按优先级排序）：
    1. 环境变量
    2. YAML配置文件
    3. JSON配置文件
    4. 默认值
    
    Attributes:
        config_file: 配置文件路径
        auto_reload: 是否自动重新加载配置
        _config: 配置字典
        _env_prefix: 环境变量前缀
    """
    
    config_file: Optional[str] = None
    auto_reload: bool = False
    _config: Dict[str, Any] = field(default_factory=dict)
    _env_prefix: str = "EVOLUTION_"
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        self._load_defaults()
        self._load_from_file()
        self._load_from_env()
    
    def _load_defaults(self) -> None:
        """加载默认配置"""
        self._config = {
            # 数据库配置
            "database": {
                "url": "sqlite:///evolution.db",
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "echo": False,
                "wal_mode": True
            },
            # 日志配置
            "logging": {
                "level": "INFO",
                "format": "json",
                "file": "logs/evolution.log",
                "max_bytes": 10485760,  # 10MB
                "backup_count": 5,
                "console_output": True
            },
            # 守护进程配置
            "daemon": {
                "enabled": True,
                "interval_seconds": 300,
                "max_retries": 3,
                "retry_delay": 5
            },
            # 触发器配置
            "trigger": {
                "event_queue_size": 1000,
                "max_workers": 5,
                "timeout_seconds": 30
            },
            # LLM配置
            "llm": {
                "api_key": "",
                "base_url": "https://api.siliconflow.cn/v1",
                "model": "deepseek-ai/DeepSeek-R1",
                "timeout": 60
            },
            # 集成配置 (Integration Settings)
            "integration": {
                "auto_start": True,
                "trigger_on_user_message": True,
                "trigger_before_thinking": True,
                "timer_interval": 300,  # 5 minutes
                "enable_thinking_trigger": True,
                "enable_timer_trigger": True,
                "enable_user_message_trigger": True,
                "database_path": ":memory:",
                "log_level": "INFO"
            }
        }
    
    def _load_from_file(self) -> None:
        """从配置文件加载配置
        
        支持JSON和YAML格式的配置文件
        """
        if not self.config_file:
            # 尝试查找默认配置文件
            default_files = [
                "config/settings.yaml",
                "config/settings.yml",
                "config/settings.json",
                "settings.yaml",
                "settings.yml",
                "settings.json"
            ]
            for file in default_files:
                if Path(file).exists():
                    self.config_file = file
                    break
        
        if not self.config_file or not Path(self.config_file).exists():
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                if self.config_file.endswith(('.yaml', '.yml')):
                    if yaml is None:
                        print("Warning: PyYAML not installed, skipping YAML config")
                        return
                    file_config = yaml.safe_load(f)
                elif self.config_file.endswith('.json'):
                    file_config = json.load(f)
                else:
                    return
                
            if file_config and isinstance(file_config, dict):
                self._deep_update(self._config, file_config)
        except Exception as e:
            print(f"Warning: Failed to load config file {self.config_file}: {e}")
    
    def _load_from_env(self) -> None:
        """从环境变量加载配置
        
        环境变量格式：EVOLUTION_SECTION_KEY
        例如：EVOLUTION_DATABASE_URL 对应 config['database']['url']
        """
        prefix = self._env_prefix
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # 移除前缀并转换为小写
                config_key = key[len(prefix):].lower()
                parts = config_key.split('_')
                
                # 构建嵌套配置
                current = self._config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # 类型转换
                current[parts[-1]] = self._parse_value(value)
    
    def _parse_value(self, value: str) -> Any:
        """解析环境变量值，进行类型转换
        
        Args:
            value: 字符串值
            
        Returns:
            转换后的类型值
        """
        # 尝试转换为布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 尝试转换为整数
        try:
            return int(value)
        except ValueError:
            pass
        
        # 尝试转换为浮点数
        try:
            return float(value)
        except ValueError:
            pass
        
        # 返回字符串
        return value
    
    def _deep_update(self, target: Dict, source: Dict) -> None:
        """深度更新字典
        
        Args:
            target: 目标字典
            source: 源字典
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键（如 'database.url'）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        current = self._config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        current = self._config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get_database_url(self) -> str:
        """获取数据库URL
        
        Returns:
            数据库URL字符串
        """
        return self.get('database.url', 'sqlite:///evolution.db')
    
    def get_log_level(self) -> str:
        """获取日志级别
        
        Returns:
            日志级别字符串
        """
        return self.get('logging.level', 'INFO')
    
    def is_wal_mode(self) -> bool:
        """检查是否启用WAL模式
        
        Returns:
            是否启用WAL模式
        """
        return self.get('database.wal_mode', True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            配置字典
        """
        return self._config.copy()
    
    def reload(self) -> None:
        """重新加载配置"""
        self._load_from_file()
        self._load_from_env()
    
    # ========= Integration Settings Helper Methods =========
    
    def is_auto_start(self) -> bool:
        """
        检查是否自动启动进化引擎。
        
        Returns:
            是否自动启动。
        """
        return self.get('integration.auto_start', True)
    
    def get_timer_interval(self) -> int:
        """
        获取定时器间隔（秒）。
        
        Returns:
            定时器间隔（秒）。
        """
        return self.get('integration.timer_interval', 300)
    
    def is_trigger_on_user_message(self) -> bool:
        """
        检查是否在用户消息时触发。
        
        Returns:
            是否触发。
        """
        return self.get('integration.trigger_on_user_message', True)
    
    def is_trigger_before_thinking(self) -> bool:
        """
        检查是否在AI思考前触发。
        
        Returns:
            是否触发。
        """
        return self.get('integration.trigger_before_thinking', True)
    
    def is_enable_thinking_trigger(self) -> bool:
        """
        检查是否启用思考触发器。
        
        Returns:
            是否启用。
        """
        return self.get('integration.enable_thinking_trigger', True)
    
    def is_enable_timer_trigger(self) -> bool:
        """
        检查是否启用定时触发器。
        
        Returns:
            是否启用。
        """
        return self.get('integration.enable_timer_trigger', True)
    
    def is_enable_user_message_trigger(self) -> bool:
        """
        检查是否启用用户消息触发器。
        
        Returns:
            是否启用。
        """
        return self.get('integration.enable_user_message_trigger', True)
    
    def get_database_path(self) -> str:
        """
        获取数据库路径。
        
        Returns:
            数据库路径。
        """
        return self.get('integration.database_path', ':memory:')
    
    def get_integration_log_level(self) -> str:
        """
        获取集成日志级别。
        
        Returns:
            日志级别字符串。
        """
        return self.get('integration.log_level', 'INFO')


_settings_instance: Optional[Settings] = None


def get_settings(config_file: Optional[str] = None) -> Settings:
    """获取全局配置实例
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        Settings实例
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings(config_file=config_file)
    return _settings_instance


def reload_settings(config_file: Optional[str] = None) -> Settings:
    """重新加载全局配置
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        重新加载后的Settings实例
    """
    global _settings_instance
    _settings_instance = Settings(config_file=config_file)
    return _settings_instance
