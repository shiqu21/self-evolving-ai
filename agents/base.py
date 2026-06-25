"""代理基类 - 所有代理的抽象基类"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from utils.logger import get_logger

logger = get_logger(__name__)


class AgentType(Enum):
    """代理类型枚举"""
    ORCHESTRATOR = "orchestrator"
    EVENT_MONITOR = "event_monitor"
    EVENT_ANALYST = "event_analyst"
    CODE_REVIEWER = "code_reviewer"
    ARBITER = "arbiter"
    SKILL_WRITER = "skill_writer"
    TOKEN_OPTIMIZER = "token_optimizer"


class AgentStatus(Enum):
    """代理状态"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentResult:
    """代理执行结果"""
    success: bool
    data: Any = None
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    agent_type: str = ""
    execution_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "agent_type": self.agent_type,
            "execution_time_ms": self.execution_time_ms
        }


@dataclass
class Task:
    """任务定义"""
    task_id: str = ""
    task_type: str = ""
    description: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 5
    timeout_seconds: int = 300
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "description": self.description,
            "payload": self.payload,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at.isoformat()
        }


class BaseAgent(ABC):
    """代理基类

    所有代理必须继承此类并实现execute方法。
    代理负责处理特定类型的任务，通过can_handle方法判断是否能处理给定任务。
    """

    name: str = "base_agent"
    description: str = "基础代理"
    agent_type: AgentType = AgentType.ORCHESTRATOR
    max_retries: int = 3

    def __init__(self):
        self.status = AgentStatus.IDLE
        self.execution_count = 0
        self.success_count = 0
        self.error_count = 0
        self._logger = logger
        self._logger.info(f"初始化代理: {self.name}")

    @abstractmethod
    async def execute(self, task: Task) -> AgentResult:
        """执行任务

        Args:
            task: 任务对象

        Returns:
            AgentResult: 执行结果
        """
        pass

    def can_handle(self, task: Task) -> bool:
        """判断是否能处理该任务

        Args:
            task: 任务对象

        Returns:
            bool: 是否可以处理
        """
        return task.task_type == self.agent_type.value

    async def execute_with_retry(self, task: Task) -> AgentResult:
        """带重试的执行

        Args:
            task: 任务对象

        Returns:
            AgentResult: 执行结果
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                self.status = AgentStatus.RUNNING
                result = await self.execute(task)

                self.execution_count += 1
                if result.success:
                    self.success_count += 1
                    self.status = AgentStatus.COMPLETED
                    return result
                else:
                    last_error = result.error
                    self._logger.warning(
                        f"代理 {self.name} 执行失败 (尝试 {attempt + 1}/{self.max_retries}): {last_error}"
                    )

            except Exception as e:
                last_error = str(e)
                self.error_count += 1
                self._logger.error(
                    f"代理 {self.name} 执行异常 (尝试 {attempt + 1}/{self.max_retries}): {e}"
                )

        self.status = AgentStatus.FAILED
        return AgentResult(
            success=False,
            error=f"重试{self.max_retries}次后仍失败: {last_error}",
            agent_type=self.agent_type.value
        )

    def get_stats(self) -> Dict[str, Any]:
        """获取代理统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            "name": self.name,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_count / max(self.execution_count, 1)
        }

    async def health_check(self) -> bool:
        """健康检查

        Returns:
            bool: 是否健康
        """
        return True


class AgentRegistry:
    """代理注册中心

    管理所有可用代理的注册和查找
    """

    def __init__(self):
        self._agents: Dict[AgentType, BaseAgent] = {}
        self._logger = logger

    def register(self, agent: BaseAgent):
        """注册代理

        Args:
            agent: 代理实例
        """
        self._agents[agent.agent_type] = agent
        self._logger.info(f"注册代理: {agent.name} ({agent.agent_type.value})")

    def unregister(self, agent_type: AgentType):
        """注销代理

        Args:
            agent_type: 代理类型
        """
        if agent_type in self._agents:
            agent = self._agents.pop(agent_type)
            self._logger.info(f"注销代理: {agent.name}")

    def get(self, agent_type: AgentType) -> Optional[BaseAgent]:
        """获取代理

        Args:
            agent_type: 代理类型

        Returns:
            Optional[BaseAgent]: 代理实例
        """
        return self._agents.get(agent_type)

    def get_all(self) -> List[BaseAgent]:
        """获取所有代理

        Returns:
            List[BaseAgent]: 代理列表
        """
        return list(self._agents.values())

    def find_can_handle(self, task: Task) -> Optional[BaseAgent]:
        """查找可以处理任务的代理

        Args:
            task: 任务对象

        Returns:
            Optional[BaseAgent]: 可处理任务的代理
        """
        for agent in self._agents.values():
            if agent.can_handle(task):
                return agent
        return None

    def clear(self):
        """清空所有代理"""
        self._agents.clear()
        self._logger.info("清空所有代理注册")