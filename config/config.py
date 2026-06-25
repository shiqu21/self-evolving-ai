"""配置管理模块"""
import os
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """系统配置"""
    # LLM配置
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1"))
    llm_model: str = "deepseek-ai/DeepSeek-R1"
    llm_timeout: int = 60
    
    # 运行配置
    interval_minutes: int = 5
    error_threshold: int = 3
    max_iterations: int = 100
    auto_run: bool = True
    
    # 存储配置
    db_path: str = "db/evolution.db"
    log_path: str = "logs"
    skill_path: str = "skills"
    
    # 安全配置
    require_human_review: bool = True
    max_skill_size: int = 15 * 1024
    
    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置"""
        return cls(
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_base_url=os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1"),
            llm_model=os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-R1"),
            interval_minutes=int(os.getenv("EVOLUTION_INTERVAL", "5")),
            error_threshold=int(os.getenv("ERROR_THRESHOLD", "3")),
            auto_run=os.getenv("AUTO_RUN", "true").lower() == "true"
        )
    
    def validate(self) -> bool:
        """验证配置"""
        if not self.llm_api_key:
            return False
        return True


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置"""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def set_config(config: Config):
    """设置全局配置"""
    global _config
    _config = config