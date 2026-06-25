"""事件分析师 - 分析根因、模式识别、生成改进提案"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import json

from agents.base import BaseAgent, AgentResult, AgentType, Task
from utils.llm_client import get_llm_client
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AnalysisResult:
    """分析结果"""
    error_id: str = ""
    root_cause: str = ""
    affected_components: List[str] = field(default_factory=list)
    impact_assessment: str = ""
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PatternInfo:
    """模式信息"""
    pattern_id: str = ""
    pattern_name: str = ""
    description: str = ""
    frequency: int = 0
    severity: str = ""
    related_errors: List[str] = field(default_factory=list)


@dataclass
class ImprovementProposal:
    """改进提案"""
    proposal_id: str = ""
    title: str = ""
    description: str = ""
    priority: str = ""  # high, medium, low
    affected_modules: List[str] = field(default_factory=list)
    expected_improvement: str = ""
    implementation_effort: str = ""  # small, medium, large
    risks: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class EventAnalystAgent(BaseAgent):
    """事件分析师代理

    负责:
    1. 分析 - 分析根因并提供诊断见解
    2. 模式识别 - 识别错误模式和趋势
    3. 生成改进提案 - 生成系统改进建议
    """

    name: str = "event_analyst"
    description: str = "事件分析师，分析根因、识别模式、生成改进提案"
    agent_type: AgentType = AgentType.EVENT_ANALYST

    def __init__(self):
        super().__init__()
        self._llm_client = get_llm_client()
        self._cached_analyses: Dict[str, AnalysisResult] = {}
        self._detected_patterns: List[PatternInfo] = []
        self._proposals: List[ImprovementProposal] = []

    async def execute(self, task: Task) -> AgentResult:
        """执行事件分析

        Args:
            task: 分析任务

        Returns:
            AgentResult: 分析结果
        """
        start_time = datetime.now()

        try:
            action = task.payload.get("action", "analyze")

            if action == "analyze":
                result_data = await self.analyze(task.payload)
            elif action == "identify_pattern":
                result_data = await self.identify_pattern(task.payload)
            elif action == "generate_proposal":
                result_data = await self.generate_proposal(task.payload)
            elif action == "full_analysis":
                result_data = await self.full_analysis(task.payload)
            else:
                result_data = {"message": f"未知操作: {action}"}

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "action": action,
                    "analysis_count": len(self._cached_analyses),
                    "pattern_count": len(self._detected_patterns),
                    "proposal_count": len(self._proposals)
                },
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"事件分析执行失败: {e}", exc_info=True)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return AgentResult(
                success=False,
                error=str(e),
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )

    async def analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """分析根因

        分析错误事件的根因并提供诊断见解

        Args:
            payload: 分析参数，包含error_events或event_ids

        Returns:
            Dict[str, Any]: 分析结果
        """
        error_events = payload.get("error_events", [])
        event_ids = payload.get("event_ids", [])
        use_llm = payload.get("use_llm", True)

        logger.info(f"开始分析 {len(error_events) + len(event_ids)} 个错误事件")

        if not error_events and event_ids:
            # 如果只有ID，加载事件详情(这里简化处理)
            error_events = self._load_error_events(event_ids)

        analyses = []

        for error in error_events[:10]:  # 最多分析10个
            analysis = await self._analyze_single_error(error, use_llm)
            analyses.append({
                "error_id": error.get("id", error.get("event_id", "")),
                "error_type": error.get("event_type", ""),
                "description": error.get("description", ""),
                "root_cause": analysis.root_cause,
                "affected_components": analysis.affected_components,
                "impact_assessment": analysis.impact_assessment,
                "confidence": analysis.confidence,
                "timestamp": analysis.timestamp.isoformat()
            })

            # 缓存分析结果
            self._cached_analyses[analysis.error_id] = analysis

        # 生成改进建议摘要
        summary = self._generate_analysis_summary(analyses)

        result = {
            "analyses": analyses,
            "summary": summary,
            "total_analyzed": len(analyses)
        }

        logger.info(f"分析完成: {len(analyses)} 个错误已分析")
        return result

    async def identify_pattern(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """识别模式

        从错误事件中识别重复出现的模式

        Args:
            payload: 模式识别参数

        Returns:
            Dict[str, Any]: 模式识别结果
        """
        min_frequency = payload.get("min_frequency", 2)
        error_events = payload.get("error_events", [])

        logger.info("开始识别错误模式")

        if not error_events:
            # 使用缓存的分析结果
            error_events = self._get_cached_error_events()

        # 基于事件类型分组识别模式
        patterns_by_type: Dict[str, List[Dict]] = defaultdict(list)
        for error in error_events:
            event_type = error.get("event_type", "unknown")
            patterns_by_type[event_type].append(error)

        # 生成模式信息
        patterns = []
        pattern_id = 1

        for event_type, events in patterns_by_type.items():
            if len(events) >= min_frequency:
                # 计算严重程度
                severities = [e.get("severity", "info") for e in events]
                severity = "critical" if "critical" in severities else "error" if "error" in severities else "warning"

                pattern = PatternInfo(
                    pattern_id=f"pattern_{pattern_id}",
                    pattern_name=f"重复错误: {event_type}",
                    description=f"检测到 {len(events)} 次 {event_type} 类型错误",
                    frequency=len(events),
                    severity=severity,
                    related_errors=[e.get("id", e.get("event_id", f"err_{i}")) for i, e in enumerate(events)]
                )

                patterns.append(pattern)
                self._detected_patterns.append(pattern)
                pattern_id += 1

        # 计算模式统计
        stats = {
            "total_patterns": len(patterns),
            "critical_patterns": sum(1 for p in patterns if p.severity == "critical"),
            "error_patterns": sum(1 for p in patterns if p.severity == "error"),
            "warning_patterns": sum(1 for p in patterns if p.severity == "warning"),
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "name": p.pattern_name,
                    "frequency": p.frequency,
                    "severity": p.severity
                }
                for p in patterns
            ]
        }

        logger.info(f"模式识别完成: 发现 {len(patterns)} 个模式")
        return stats

    async def generate_proposal(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """生成改进提案

        根据分析结果生成系统改进提案

        Args:
            payload: 提案生成参数

        Returns:
            Dict[str, Any]: 改进提案
        """
        focus_areas = payload.get("focus_areas", ["error_prevention", "performance"])
        max_proposals = payload.get("max_proposals", 3)

        logger.info(f"开始生成改进提案 (关注领域: {focus_areas})")

        proposals = []

        # 基于检测到的模式生成提案
        for pattern in self._detected_patterns[:5]:
            if pattern.severity in ["critical", "error"] and pattern.frequency >= 2:
                proposal = await self._create_proposal_from_pattern(pattern, focus_areas)
                if proposal:
                    proposals.append(proposal)
                    self._proposals.append(proposal)

        # 如果没有足够提案，生成通用提案
        while len(proposals) < max_proposals:
            proposal = await self._create_generic_proposal(focus_areas)
            proposals.append(proposal)
            self._proposals.append(proposal)

        result = {
            "proposals": [
                {
                    "proposal_id": p.proposal_id,
                    "title": p.title,
                    "description": p.description,
                    "priority": p.priority,
                    "affected_modules": p.affected_modules,
                    "expected_improvement": p.expected_improvement,
                    "implementation_effort": p.implementation_effort,
                    "risks": p.risks,
                    "created_at": p.created_at.isoformat()
                }
                for p in proposals[:max_proposals]
            ],
            "total_proposals": len(proposals)
        }

        logger.info(f"改进提案生成完成: {len(proposals)} 个提案")
        return result

    async def full_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """完整分析

        执行完整的分析流程:分析+模式识别+提案生成

        Args:
            payload: 分析参数

        Returns:
            Dict[str, Any]: 完整分析结果
        """
        logger.info("开始完整分析流程")

        # 1. 分析错误
        analysis_result = await self.analyze(payload)

        # 2. 识别模式
        pattern_result = await self.identify_pattern(payload)

        # 3. 生成改进提案
        proposal_result = await self.generate_proposal(payload)

        return {
            "analysis": analysis_result,
            "patterns": pattern_result,
            "proposals": proposal_result,
            "full_analysis_completed": True,
            "timestamp": datetime.now().isoformat()
        }

    async def _analyze_single_error(self, error: Dict[str, Any], use_llm: bool) -> AnalysisResult:
        """分析单个错误

        Args:
            error: 错误事件
            use_llm: 是否使用LLM分析

        Returns:
            AnalysisResult: 分析结果
        """
        error_id = error.get("id", error.get("event_id", f"err_{len(self._cached_analyses)}"))
        error_type = error.get("event_type", "")
        description = error.get("description", "")
        severity = error.get("severity", "info")

        # 基础分析 - 基于规则
        root_cause = self._rule_based_analysis(error_type, description)
        affected_components = self._extract_components(error_type, description)
        impact = self._assess_impact(severity, error_type)

        # 如果启用LLM，增强分析
        if use_llm and self._llm_client:
            try:
                llm_analysis = await self._llm_analysis(error)
                if llm_analysis:
                    root_cause = llm_analysis.get("root_cause", root_cause)
                    affected_components = llm_analysis.get("components", affected_components)
            except Exception as e:
                logger.warning(f"LLM分析失败: {e}")

        return AnalysisResult(
            error_id=error_id,
            root_cause=root_cause,
            affected_components=affected_components,
            impact_assessment=impact,
            confidence=0.8 if use_llm else 0.6
        )

    def _rule_based_analysis(self, event_type: str, description: str) -> str:
        """基于规则的分析

        Args:
            event_type: 事件类型
            description: 描述

        Returns:
            str: 根因分析
        """
        event_lower = event_type.lower()
        desc_lower = description.lower()

        # 简单规则映射
        rules = [
            (["timeout", "超时"], "可能是网络延迟或服务响应慢"),
            (["null", "none", "空"], "存在空指针或未初始化的数据"),
            (["auth", "认证", "permission"], "权限或认证问题"),
            (["database", "db", "sql"], "数据库相关错误"),
            (["memory", "oom", "内存"], "内存管理问题"),
            (["file", "io", "读取"], "文件IO操作问题")
        ]

        for keywords, cause in rules:
            if any(kw in event_lower or kw in desc_lower for kw in keywords):
                return cause

        return "需要进一步分析"

    def _extract_components(self, event_type: str, description: str) -> List[str]:
        """提取受影响的组件

        Args:
            event_type: 事件类型
            description: 描述

        Returns:
            List[str]: 组件列表
        """
        components = set()

        component_keywords = {
            "database": ["database", "db", "sql"],
            "api": ["api", "http", "request"],
            "auth": ["auth", "login", "token"],
            "memory": ["memory", "heap", "gc"],
            "storage": ["storage", "disk", "file"],
            "network": ["network", "connection", "socket"]
        }

        text = f"{event_type} {description}".lower()
        for component, keywords in component_keywords.items():
            if any(kw in text for kw in keywords):
                components.add(component)

        return list(components) if components else ["unknown"]

    def _assess_impact(self, severity: str, event_type: str) -> str:
        """评估影响

        Args:
            severity: 严重程度
            event_type: 事件类型

        Returns:
            str: 影响评估
        """
        impact_map = {
            "critical": "系统可能崩溃或不可用，需要立即处理",
            "error": "功能受损，影响部分用户体验",
            "warning": "潜在问题，可能在未来导致错误",
            "info": "信息性通知，影响较小"
        }

        return impact_map.get(severity, "影响未知")

    async def _llm_analysis(self, error: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用LLM进行深入分析

        Args:
            error: 错误事件

        Returns:
            Optional[Dict]: LLM分析结果
        """
        try:
            prompt = f"""分析以下错误的根因:

错误类型: {error.get("event_type", "")}
严重程度: {error.get("severity", "")}
描述: {error.get("description", "")}

请简洁回答:
1. 根因是什么？
2. 受影响的组件有哪些？
3. 如何修复？"""

            result = self._llm_client.chat(prompt)

            return {
                "root_cause": result[:200],
                "components": ["unknown"],  # 简化处理
                "llm_analysis": result
            }

        except Exception as e:
            logger.warning(f"LLM分析失败: {e}")
            return None

    async def _create_proposal_from_pattern(
        self,
        pattern: PatternInfo,
        focus_areas: List[str]
    ) -> Optional[ImprovementProposal]:
        """从模式创建提案

        Args:
            pattern: 模式信息
            focus_areas: 关注领域

        Returns:
            Optional[ImprovementProposal]: 改进提案
        """
        proposal_id = f"prop_{len(self._proposals) + 1}"

        priority = "high" if pattern.severity == "critical" else "medium"

        # 基于模式生成提案
        title = f"修复重复错误: {pattern.pattern_name}"
        description = f"检测到 {pattern.frequency} 次重复的 {pattern.pattern_name}，需要进行修复"

        affected = list(set(pattern.related_errors[:2]))  # 简化

        return ImprovementProposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            priority=priority,
            affected_modules=affected,
            expected_improvement=f"减少 {pattern.frequency} 次同类错误",
            implementation_effort="medium",
            risks=["可能引入新的问题", "需要充分测试"]
        )

    async def _create_generic_proposal(self, focus_areas: List[str]) -> ImprovementProposal:
        """创建通用提案

        Args:
            focus_areas: 关注领域

        Returns:
            ImprovementProposal: 改进提案
        """
        proposal_id = f"prop_{len(self._proposals) + 1}"

        proposals = [
            ImprovementProposal(
                proposal_id=proposal_id,
                title="增加输入验证",
                description="在所有API端点增加输入参数验证，防止无效数据进入系统",
                priority="medium",
                affected_modules=["api", "validation"],
                expected_improvement="减少20%的参数错误",
                implementation_effort="small",
                risks=["可能影响现有功能"]
            ),
            ImprovementProposal(
                proposal_id=proposal_id,
                title="优化错误处理",
                description="统一错误处理机制，提供更友好的错误信息",
                priority="medium",
                affected_modules=["error_handling"],
                expected_improvement="提高错误可追溯性",
                implementation_effort="medium",
                risks=[]
            ),
            ImprovementProposal(
                proposal_id=proposal_id,
                title="增加超时重试机制",
                description="对网络请求增加超时检测和自动重试",
                priority="high",
                affected_modules=["network", "api_client"],
                expected_improvement="减少30%的超时错误",
                implementation_effort="small",
                risks=["可能增加系统负载"]
            )
        ]

        return proposals[len(self._proposals) % len(proposals)]

    def _load_error_events(self, event_ids: List[str]) -> List[Dict]:
        """加载错误事件(简化实现)

        Args:
            event_ids: 事件ID列表

        Returns:
            List[Dict]: 事件列表
        """
        # 这里应该从数据库加载，实际简化处理
        return [{"id": eid, "event_type": "unknown", "description": ""} for eid in event_ids]

    def _get_cached_error_events(self) -> List[Dict]:
        """获取缓存的错误事件

        Returns:
            List[Dict]: 错误事件列表
        """
        return [
            {
                "id": a.error_id,
                "event_type": "error",
                "description": a.root_cause,
                "severity": "error"
            }
            for a in self._cached_analyses.values()
        ]

    def _generate_analysis_summary(self, analyses: List[Dict]) -> Dict[str, Any]:
        """生成分析摘要

        Args:
            analyses: 分析列表

        Returns:
            Dict: 摘要信息
        """
        if not analyses:
            return {"message": "无分析数据"}

        severities = defaultdict(int)
        root_causes = defaultdict(int)

        for a in analyses:
            severity = a.get("severity", "info")
            root_cause = a.get("root_cause", "unknown")[:30]
            severities[severity] += 1
            root_causes[root_cause] += 1

        return {
            "total_analyzed": len(analyses),
            "by_severity": dict(severities),
            "top_root_causes": dict(sorted(root_causes.items(), key=lambda x: x[1], reverse=True)[:3]),
            "high_confidence_count": sum(1 for a in analyses if a.get("confidence", 0) >= 0.7)
        }