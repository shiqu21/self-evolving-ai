"""代理模块测试 - WorkBuddy自我进化系统

测试7种代理的导入、实例化和基本功能:
- orchestrator: 任务编排器
- event_monitor: 事件监控器
- event_analyst: 事件分析师
- code_reviewer: 代码评审员
- arbiter: 质量仲裁者
- skill_writer: 技能编写器
- token_optimizer: Token优化器

作者: QA Engineer - 严过关
"""
import sys
import os
import asyncio
import pytest
from typing import Dict

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入被测试的模块
from agents import (
    BaseAgent,
    AgentResult,
    AgentType,
    AgentStatus,
    Task,
    AgentRegistry,
    OrchestratorAgent,
    EventMonitorAgent,
    EventAnalystAgent,
    CodeReviewerAgent,
    ArbiterAgent,
    SkillWriterAgent,
    TokenOptimizerAgent,
    ExecutionContext,
    MonitoredEvent,
    SessionSummary,
    AnalysisResult,
    PatternInfo,
    ImprovementProposal,
    CodeIssue,
    ReviewReport,
    QualityDecision,
    EscalationRecord,
    DecisionType,
    EscalationReason,
    SkillSpec,
    GeneratedSkill,
    OptimizationResult,
    CompressionStats,
    AGENT_CLASSES,
    get_agent,
    create_all_agents,
    register_all_agents,
)


class TestAgentImports:
    """测试代理模块导入"""

    def test_import_base_classes(self):
        """测试基础类导入"""
        assert BaseAgent is not None
        assert AgentResult is not None
        assert AgentType is not None
        assert AgentStatus is not None
        assert Task is not None
        assert AgentRegistry is not None

    def test_import_agent_classes(self):
        """测试代理类导入"""
        assert OrchestratorAgent is not None
        assert EventMonitorAgent is not None
        assert EventAnalystAgent is not None
        assert CodeReviewerAgent is not None
        assert ArbiterAgent is not None
        assert SkillWriterAgent is not None
        assert TokenOptimizerAgent is not None

    def test_import_data_types(self):
        """测试数据类型导入"""
        assert ExecutionContext is not None
        assert MonitoredEvent is not None
        assert SessionSummary is not None
        assert AnalysisResult is not None
        assert PatternInfo is not None
        assert ImprovementProposal is not None
        assert CodeIssue is not None
        assert ReviewReport is not None
        assert QualityDecision is not None
        assert EscalationRecord is not None
        assert SkillSpec is not None
        assert GeneratedSkill is not None
        assert OptimizationResult is not None
        assert CompressionStats is not None

    def test_import_utilities(self):
        """测试工具函数导入"""
        assert AGENT_CLASSES is not None
        assert get_agent is not None
        assert create_all_agents is not None
        assert register_all_agents is not None


class TestAgentType:
    """测试AgentType枚举"""

    def test_agent_type_values(self):
        """测试AgentType枚举值"""
        assert AgentType.ORCHESTRATOR.value == "orchestrator"
        assert AgentType.EVENT_MONITOR.value == "event_monitor"
        assert AgentType.EVENT_ANALYST.value == "event_analyst"
        assert AgentType.CODE_REVIEWER.value == "code_reviewer"
        assert AgentType.ARBITER.value == "arbiter"
        assert AgentType.SKILL_WRITER.value == "skill_writer"
        assert AgentType.TOKEN_OPTIMIZER.value == "token_optimizer"

    def test_agent_type_count(self):
        """测试AgentType数量"""
        assert len(AgentType) == 7


class TestAgentStatus:
    """测试AgentStatus枚举"""

    def test_agent_status_values(self):
        """测试AgentStatus枚举值"""
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.WAITING.value == "waiting"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.FAILED.value == "failed"


class TestTask:
    """测试Task类"""

    def test_task_creation(self):
        """测试Task创建"""
        task = Task(
            task_id="test_task_001",
            task_type="code_review",
            description="测试任务",
            payload={"action": "review", "code": "print('hello')"}
        )
        assert task.task_id == "test_task_001"
        assert task.task_type == "code_review"
        assert task.description == "测试任务"
        assert task.payload["action"] == "review"

    def test_task_with_context(self):
        """测试带上下文的Task"""
        task = Task(
            task_id="test_002",
            task_type="analysis",
            description="分析任务",
            context={"user": "test_user", "session": "test_session"},
            payload={"data": [1, 2, 3]}
        )
        assert task.context["user"] == "test_user"
        assert task.context["session"] == "test_session"


class TestAgentRegistry:
    """测试AgentRegistry类"""

    def test_registry_creation(self):
        """测试注册表创建"""
        registry = AgentRegistry()
        assert registry is not None
        assert len(registry._agents) == 0

    def test_register_agent(self):
        """测试注册代理"""
        registry = AgentRegistry()
        agent = OrchestratorAgent()
        registry.register(agent)
        assert len(registry._agents) == 1

    def test_get_agent(self):
        """测试获取代理"""
        registry = AgentRegistry()
        orchestrator = OrchestratorAgent()
        registry.register(orchestrator)
        retrieved = registry.get(AgentType.ORCHESTRATOR)
        assert retrieved is not None

    def test_list_agents(self):
        """测试列出代理"""
        registry = AgentRegistry()
        orchestrator = OrchestratorAgent()
        registry.register(orchestrator)
        agents = registry.list_agents()
        assert len(agents) == 1


class TestOrchestratorAgent:
    """测试OrchestratorAgent"""

    def test_orchestrator_creation(self):
        """测试OrchestratorAgent创建"""
        agent = OrchestratorAgent()
        assert agent is not None
        assert agent.agent_type == AgentType.ORCHESTRATOR

    def test_execution_context_creation(self):
        """测试ExecutionContext创建"""
        context = ExecutionContext(
            session_id="session_001",
            user_id="user_001",
            metadata={"source": "test"}
        )
        assert context.session_id == "session_001"
        assert context.user_id == "user_001"

    @pytest.mark.asyncio
    async def test_execute_task(self):
        """测试执行任务"""
        agent = OrchestratorAgent()
        task = Task(
            task_id="test_001",
            task_type="orchestrator",
            description="测试编排",
            payload={"action": "test"}
        )
        result = await agent.execute(task)
        assert result is not None


class TestEventMonitorAgent:
    """测试EventMonitorAgent"""

    def test_event_monitor_creation(self):
        """测试EventMonitorAgent创建"""
        agent = EventMonitorAgent()
        assert agent is not None
        assert agent.agent_type == AgentType.EVENT_MONITOR

    def test_monitored_event_creation(self):
        """测试MonitoredEvent创建"""
        event = MonitoredEvent(
            event_type="error",
            severity="high",
            message="测试错误",
            timestamp="2024-01-01T00:00:00"
        )
        assert event.event_type == "error"
        assert event.severity == "high"

    def test_session_summary_creation(self):
        """测试SessionSummary创建"""
        summary = SessionSummary(
            session_id="session_001",
            event_count=10,
            error_count=2,
            duration=120.5
        )
        assert summary.session_id == "session_001"
        assert summary.event_count == 10
        assert summary.error_count == 2


class TestEventAnalystAgent:
    """测试EventAnalystAgent"""

    def test_event_analyst_creation(self):
        """测试EventAnalystAgent创建"""
        agent = EventAnalystAgent()
        assert agent is not None
        assert agent.agent_type == AgentType.EVENT_ANALYST

    def test_analysis_result_creation(self):
        """测试AnalysisResult创建"""
        result = AnalysisResult(
            success=True,
            patterns=[
                PatternInfo(
                    pattern_type="error_pattern",
                    description="错误频率增加",
                    frequency=0.3
                )
            ],
            improvements=[
                ImprovementProposal(
                    title="优化建议",
                    description="添加错误处理",
                    priority=8
                )
            ]
        )
        assert result.success is True
        assert len(result.patterns) == 1
        assert len(result.improvements) == 1


class TestCodeReviewerAgent:
    """测试CodeReviewerAgent"""

    def test_code_reviewer_creation(self):
        """测试CodeReviewerAgent创建"""
        agent = CodeReviewerAgent()
        assert agent is not None
        assert agent.agent_type == AgentType.CODE_REVIEWER

    def test_code_issue_creation(self):
        """测试CodeIssue创建"""
        issue = CodeIssue(
            severity="warning",
            category="style",
            message="建议添加类型注解",
            line_number=10,
            code_snippet="def test():"
        )
        assert issue.severity == "warning"
        assert issue.line_number == 10

    def test_review_report_creation(self):
        """测试ReviewReport创建"""
        report = ReviewReport(
            file_path="test.py",
            issues=[
                CodeIssue(
                    severity="error",
                    category="syntax",
                    message="语法错误",
                    line_number=1
                )
            ],
            score=85,
            summary="代码评审完成"
        )
        assert report.score == 85
        assert len(report.issues) == 1


class TestArbiterAgent:
    """测试ArbiterAgent"""

    def test_arbiter_creation(self):
        """测试ArbiterAgent创建"""
        agent = ArbiterAgent()
        assert agent is not None
        assert agent.agent_type == AgentType.ARBITER

    def test_quality_decision_creation(self):
        """测试QualityDecision创建"""
        decision = QualityDecision(
            decision_type=DecisionType.APPROVE,
            reason="代码质量良好",
            confidence=0.9,
            details={"score": 90}
        )
        assert decision.decision_type == DecisionType.APPROVE
        assert decision.confidence == 0.9

    def test_decision_type_values(self):
        """测试DecisionType枚举值"""
        assert DecisionType.APPROVE.value == "approve"
        assert DecisionType.REJECT.value == "reject"
        assert DecisionType.REVISION_REQUIRED.value == "revision_required"
        assert DecisionType.ESCALATE.value == "escalate"

    def test_escalation_reason_values(self):
        """测试EscalationReason枚举值"""
        assert EscalationReason.CRITICAL_ISSUE.value == "critical_issue"
        assert EscalationReason.COMPLEXITY.value == "complexity"
        assert EscalationReason.SECURITY.value == "security"


class TestSkillWriterAgent:
    """测试SkillWriterAgent"""

    def test_skill_writer_creation(self):
        """测试SkillWriterAgent创建"""
        agent = SkillWriterAgent()
        assert agent is not None
        assert agent.agent_type == AgentType.SKILL_WRITER

    def test_skill_spec_creation(self):
        """测试SkillSpec创建"""
        spec = SkillSpec(
            name="test_skill",
            description="测试技能",
            triggers=["test", "测试"],
            code="def test(): pass",
            metadata={"version": "1.0"}
        )
        assert spec.name == "test_skill"
        assert "test" in spec.triggers

    def test_generated_skill_creation(self):
        """测试GeneratedSkill创建"""
        skill = GeneratedSkill(
            skill_id="skill_001",
            spec=SkillSpec(
                name="generated_skill",
                description="生成的技能",
                triggers=["generate"],
                code="pass"
            ),
            quality_score=0.85,
            validation_passed=True
        )
        assert skill.skill_id == "skill_001"
        assert skill.validation_passed is True


class TestTokenOptimizerAgent:
    """测试TokenOptimizerAgent"""

    def test_token_optimizer_creation(self):
        """测试TokenOptimizerAgent创建"""
        agent = TokenOptimizerAgent()
        assert agent is not None
        assert agent.agent_type == AgentType.TOKEN_OPTIMIZER

    def test_optimization_result_creation(self):
        """测试OptimizationResult创建"""
        result = OptimizationResult(
            original_prompt="原始提示词",
            optimized_prompt="优化后的提示词",
            original_tokens=100,
            optimized_tokens=80,
            compression_ratio=0.8,
            quality_preserved=True
        )
        assert result.original_tokens == 100
        assert result.optimized_tokens == 80
        assert result.compression_ratio == 0.8

    def test_compression_stats_creation(self):
        """测试CompressionStats创建"""
        stats = CompressionStats(
            before_tokens=1000,
            after_tokens=750,
            savings=250,
            savings_percentage=25.0
        )
        assert stats.savings_percentage == 25.0


class TestAgentUtilityFunctions:
    """测试代理工具函数"""

    def test_get_agent_orchestrator(self):
        """测试获取OrchestratorAgent"""
        agent = get_agent(AgentType.ORCHESTRATOR)
        assert isinstance(agent, OrchestratorAgent)

    def test_get_agent_all_types(self):
        """测试获取所有类型代理"""
        for agent_type in AgentType:
            agent = get_agent(agent_type)
            assert agent is not None

    def test_create_all_agents(self):
        """测试创建所有代理"""
        agents = create_all_agents()
        assert len(agents) == 7
        assert AgentType.ORCHESTRATOR in agents
        assert AgentType.EVENT_MONITOR in agents
        assert AgentType.EVENT_ANALYST in agents
        assert AgentType.CODE_REVIEWER in agents
        assert AgentType.ARBITER in agents
        assert AgentType.SKILL_WRITER in agents
        assert AgentType.TOKEN_OPTIMIZER in agents

    def test_register_all_agents(self):
        """测试注册所有代理"""
        registry = AgentRegistry()
        register_all_agents(registry)
        assert len(registry.list_agents()) == 7


class TestAgentIntegration:
    """代理集成测试"""

    @pytest.mark.asyncio
    async def test_full_agent_flow(self):
        """测试完整代理流程"""
        # 创建注册表
        registry = AgentRegistry()

        # 注册所有代理
        register_all_agents(registry)

        # 验证所有代理已注册
        assert len(registry.list_agents()) == 7

        # 获取各个代理
        orchestrator = registry.get(AgentType.ORCHESTRATOR)
        assert orchestrator is not None

        event_monitor = registry.get(AgentType.EVENT_MONITOR)
        assert event_monitor is not None

        event_analyst = registry.get(AgentType.EVENT_ANALYST)
        assert event_analyst is not None

        code_reviewer = registry.get(AgentType.CODE_REVIEWER)
        assert code_reviewer is not None

        arbiter = registry.get(AgentType.ARBITER)
        assert arbiter is not None

        skill_writer = registry.get(AgentType.SKILL_WRITER)
        assert skill_writer is not None

        token_optimizer = registry.get(AgentType.TOKEN_OPTIMIZER)
        assert token_optimizer is not None


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])