"""自我进化系统 - 核心常量"""
from enum import Enum

class Phase(Enum):
    """5阶段进化循环"""
    OPERATE = "operate"     # 操作执行
    DETECT = "detect"       # 检测观察
    ANALYZE = "analyze"     # 分析诊断
    ENCODE = "encode"       # 编码学习
    VERIFY = "verify"       # 验证确认

class Status(Enum):
    """状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

class Severity(Enum):
    """严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class EventType(Enum):
    """事件类型"""
    CYCLE_START = "cycle_start"
    CYCLE_COMPLETE = "cycle_complete"
    SKILL_CREATED = "skill_created"
    SKILL_APPLIED = "skill_applied"
    ERROR_OCCURRED = "error_occurred"
    IMPROVEMENT_FOUND = "improvement_found"

class ReviewStage(Enum):
    """复盘阶段"""
    GOAL = "goal"          # 目标
    RESULT = "result"      # 结果
    ANALYSIS = "analysis"  # 分析
    LEARNING = "learning"  # 学习
    ACTION = "action"      # 行动