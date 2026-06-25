"""多代理框架 - WorkBuddy自我进化系统的代理模块

本模块提供7种代理实现:
- orchestrator: 任务编排器 - 负责任务分发、依赖管理、结果汇总
- event_monitor: 事件监控器 - 监控所有会话中的错误和异常
- event_analyst: 事件分析师 - 分析根因、模式识别、生成改进提案
- code_reviewer: 代码评审员 - 代码质量评审、漏洞检测、改进建议
- arbiter: 质量仲裁者 - 质量决策、是否通过、升级判断
- skill_writer: 技能编写器 - 生成和优化Skills技能模块
- token_optimizer: Token优化器 - 优化提示词、减少Token使用
"""
from typing import Dict

from agents.base import (
    BaseAgent,
    AgentResult,
    AgentType,
    AgentStatus,
    Task,
    AgentRegistry
)

from agents.orchestrator import OrchestratorAgent, ExecutionContext
from agents.event_monitor import EventMonitorAgent, MonitoredEvent, SessionSummary
from agents.event_analyst import EventAnalystAgent, AnalysisResult, PatternInfo, ImprovementProposal
from agents.code_reviewer import CodeReviewerAgent, CodeIssue, ReviewReport
from agents.arbiter import ArbiterAgent, QualityDecision, EscalationRecord, DecisionType, EscalationReason
from agents.skill_writer import SkillWriterAgent, SkillSpec, GeneratedSkill
from agents.token_optimizer import TokenOptimizerAgent, OptimizationResult, CompressionStats


# 代理映射 - 按AgentType
AGENT_CLASSES = {
    AgentType.ORCHESTRATOR: OrchestratorAgent,
    AgentType.EVENT_MONITOR: EventMonitorAgent,
    AgentType.EVENT_ANALYST: EventAnalystAgent,
    AgentType.CODE_REVIEWER: CodeReviewerAgent,
    AgentType.ARBITER: ArbiterAgent,
    AgentType.SKILL_WRITER: SkillWriterAgent,
    AgentType.TOKEN_OPTIMIZER: TokenOptimizerAgent,
}


def get_agent(agent_type: AgentType) -> BaseAgent:
    """获取指定类型的代理实例
    
    Args:
        agent_type: 代理类型
        
    Returns:
        BaseAgent: 代理实例
    """
    agent_class = AGENT_CLASSES.get(agent_type)
    if agent_class:
        return agent_class()
    raise ValueError(f"未知代理类型: {agent_type}")


def create_all_agents() -> Dict[AgentType, BaseAgent]:
    """创建所有代理实例
    
    Returns:
        Dict[AgentType, BaseAgent]: 代理类型到实例的映射
    """
    return {agent_type: agent_class() for agent_type, agent_class in AGENT_CLASSES.items()}


def register_all_agents(registry: AgentRegistry):
    """将所有代理注册到注册中心
    
    Args:
        registry: 代理注册中心
    """
    for agent_type, agent_class in AGENT_CLASSES.items():
        registry.register(agent_class())


__all__ = [
    # 基类
    "BaseAgent",
    "AgentResult", 
    "AgentType",
    "AgentStatus",
    "Task",
    "AgentRegistry",
    
    # 代理类
    "OrchestratorAgent",
    "EventMonitorAgent",
    "EventAnalystAgent", 
    "CodeReviewerAgent",
    "ArbiterAgent",
    "SkillWriterAgent",
    "TokenOptimizerAgent",
    
    # 数据类型
    "ExecutionContext",
    "MonitoredEvent",
    "SessionSummary",
    "AnalysisResult",
    "PatternInfo", 
    "ImprovementProposal",
    "CodeIssue",
    "ReviewReport",
    "QualityDecision",
    "EscalationRecord",
    "DecisionType",
    "EscalationReason",
    "SkillSpec",
    "GeneratedSkill",
    "OptimizationResult",
    "CompressionStats",
    
    # 工具函数
    "AGENT_CLASSES",
    "get_agent",
    "create_all_agents", 
    "register_all_agents",
]