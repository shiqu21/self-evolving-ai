"""数据模型"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import json

@dataclass
class Event:
    """事件记录"""
    id: Optional[int] = None
    event_type: str = ""
    phase: str = ""
    status: str = ""
    message: str = ""
    severity: str = "info"
    metadata: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def metadata_dict(self) -> Dict[str, Any]:
        try:
            return json.loads(self.metadata) if self.metadata else {}
        except:
            return {}

@dataclass
class Memory:
    """记忆"""
    id: Optional[int] = None
    content: str = ""
    memory_type: str = "sensory"
    importance: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Skill:
    """技能"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    content: str = ""
    skill_type: str = "skill_candidate"
    risk_level: str = "micro"
    status: str = "candidate"
    validation_result: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    applied_at: Optional[datetime] = None

@dataclass
class ExecutionLog:
    """执行日志"""
    id: Optional[int] = None
    phase: str = ""
    action: str = ""
    result: str = ""
    duration_ms: int = 0
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Review:
    """复盘记录"""
    id: Optional[int] = None
    goal: str = ""
    result: str = ""
    analysis: str = ""
    learning: str = ""
    action: str = ""
    status: str = "pending"
    tools: str = ""
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class CycleResult:
    """进化周期结果"""
    cycle_id: int
    phase: str
    status: str
    improvements: int = 0
    skills_created: int = 0
    errors: int = 0
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True

    def to_dict(self):
        from dataclasses import asdict
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d
@dataclass
class AgentResult:
    """代理执行结果"""
    success: bool = False
    action: str = ""
    result: str = ""
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
