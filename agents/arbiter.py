"""质量仲裁者 - 质量决策、是否通过、升级判断"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json
import hashlib
from difflib import SequenceMatcher

from agents.base import BaseAgent, AgentResult, AgentType, Task
from utils.llm_client import get_llm_client
from utils.logger import get_logger

logger = get_logger(__name__)


class DecisionType(Enum):
    """决策类型"""
    APPROVE = "approve"
    REJECT = "reject"
    REVISION_REQUIRED = "revision_required"
    ESCALATE = "escalate"


class EscalationReason(Enum):
    """升级原因"""
    CRITICAL_ISSUE = "critical_issue"  # 严重问题
    SECURITY_RISK = "security_risk"    # 安全风险
    RESOURCE_EXCEEDED = "resource_exceeded"  # 资源超限
    POLICY_VIOLATION = "policy_violation"    # 政策违规
    MANUAL_REVIEW_REQUIRED = "manual_review_required"  # 需要人工审查


@dataclass
class QualityDecision:
    """质量决策"""
    decision_id: str = ""
    decision_type: DecisionType = DecisionType.APPROVE
    score: float = 0.0
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict) 
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type.value,
            "score": self.score,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class EscalationRecord:
    """升级记录"""
    escalation_id: str = ""
    reason: EscalationReason = EscalationReason.MANUAL_REVIEW_REQUIRED
    description: str = ""
    original_artifact: Dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"  # low, normal, high, critical
    assigned_to: str = ""
    created_at: datetime = field(default_factory=datetime.now)


class ArbiterAgent(BaseAgent):
    """质量仲裁者代理
    
    负责:
    1. 质量决策 - 评估代码、技能或改进的质量并做出决策
    2. 是否通过 - 判断是否通过评审、测试或部署
    3. 升级判断 - 判断是否需要升级到人工审核
    """

    name: str = "arbiter"
    description: str = "质量仲裁者，负责质量决策和升级判断"
    agent_type: AgentType = AgentType.ARBITER

    def __init__(self):
        super().__init__()
        self._llm_client = get_llm_client()
        self._decision_history: List[QualityDecision] = []
        self._escalation_history: List[EscalationRecord] = []
        
        # 质量阈值配置
        self._thresholds = {
            "approve_score": 80.0,        # 批准分数阈值
            "revision_score": 50.0,       # 需要修改分数阈值
            "escalate_score": 30.0,       # 升级分数阈值
            "critical_issues": 0,         # 严重问题数量阈值
            "security_issues": 0          # 安全问题数量阈值
        }

    async def execute(self, task: Task) -> AgentResult:
        """执行质量仲裁
        
        Args:
            task: 仲裁任务
            
        Returns:
            AgentResult: 仲裁结果
        """
        start_time = datetime.now()
        
        try:
            action = task.payload.get("action", "make_decision")
            
            if action == "make_decision":
                result_data = await self.make_decision(task.payload)
            elif action == "escalate":
                result_data = await self.escalate(task.payload)
            elif action == "approve":
                result_data = await self.approve(task.payload)
            elif action == "batch_decide":
                result_data = await self.batch_decide(task.payload)
            else:
                result_data = {"message": f"未知操作: {action}"}
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "action": action,
                    "decisions_made": len(self._decision_history),
                    "escalations": len(self._escalation_history)
                },
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"质量仲裁执行失败: {e}", exc_info=True)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return AgentResult(
                success=False,
                error=str(e),
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )
    
    async def make_decision(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """做出质量决策
        
        根据质量评分、问题列表和其他指标做出决策
        
        Args:
            payload: 决策参数，包含artifact、issues、score等
            
        Returns:
            Dict[str, Any]: 决策结果
        """
        artifact = payload.get("artifact", {})
        issues = payload.get("issues", [])
        metrics = payload.get("metrics", {})
        existing_score = payload.get("score")
        
        logger.info(f"开始质量仲裁: {artifact.get('name', 'unknown')}")
        
        # 计算质量评分
        if existing_score is None:
            score = self._calculate_quality_score(issues, metrics)
        else:
            score = existing_score
        
        # 检查是否需要升级
        needs_escalation = self._check_escalation(issues, score)
        
        # 根据阈值做出决策
        decision = self._determine_decision(score, issues, needs_escalation)
        
        # 生成决策原因
        reasons = self._generate_decision_reasons(decision, score, issues)
        
        # 计算置信度
        confidence = self._calculate_confidence(issues, metrics)
        
        # 创建决策记录
        decision_id = f"decision_{len(self._decision_history) + 1}"
        decision_record = QualityDecision(
            decision_id=decision_id,
            decision_type=decision,
            score=score,
            confidence=confidence,
            reasons=reasons,
            details={
                "artifact": artifact.get("name", "unknown"),
                "issues_count": len(issues),
                "needs_escalation": needs_escalation,
                "thresholds": self._thresholds
            }
        )
        
        self._decision_history.append(decision_record)
        
        # 如果需要升级，创建升级记录
        if needs_escalation:
            escalation_record = await self.escalate({
                "artifact": artifact,
                "issues": issues,
                "reason": self._determine_escalation_reason(issues, score)
            })
        
        result = {
            "decision": decision_record.to_dict(),
            "score": score,
            "confidence": confidence,
            "reasons": reasons,
            "thresholds": self._thresholds,
            "needs_escalation": needs_escalation,
            "timestamp": decision_record.timestamp.isoformat()
        }
        
        logger.info(f"质量仲裁完成: 决策={decision.value}, 分数={score}, 置信度={confidence}")
        return result
    
    async def escalate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """执行升级
        
        当质量问题严重时，需要升级到人工审核
        
        Args:
            payload: 升级参数
            
        Returns:
            Dict[str, Any]: 升级结果
        """
        artifact = payload.get("artifact", {})
        issues = payload.get("issues", [])
        reason = payload.get("reason", EscalationReason.MANUAL_REVIEW_REQUIRED.value)
        
        logger.warning(f"执行升级: {artifact.get('name', 'unknown')}, 原因: {reason}")
        
        # 创建升级记录
        escalation_id = f"escalation_{len(self._escalation_history) + 1}"
        
        # 判断优先级
        priority = self._determine_priority(issues, reason)
        
        escalation = EscalationRecord(
            escalation_id=escalation_id,
            reason=EscalationReason(reason) if isinstance(reason, str) else reason,
            description=f"质量问题升级: {artifact.get('name', 'unknown')}",
            original_artifact=artifact,
            priority=priority,
            assigned_to=""
        )
        
        self._escalation_history.append(escalation)
        
        result = {
            "escalation_id": escalation_id,
            "reason": escalation.reason.value,
            "priority": priority,
            "artifact": artifact.get("name", "unknown"),
            "description": escalation.description,
            "created_at": escalation.created_at.isoformat(),
            "requires_manual_review": True
        }
        
        logger.warning(f"升级记录创建: {escalation_id}, 优先级: {priority}")
        return result
    
    async def approve(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """批准操作
        
        手动批准某个制品
        
        Args:
            payload: 批准参数
            
        Returns:
            Dict[str, Any]: 批准结果
        """
        artifact = payload.get("artifact", {})
        override_reason = payload.get("reason", "手动批准")
        
        logger.info(f"手动批准: {artifact.get('name', 'unknown')}")
        
        # 创建批准记录
        decision_id = f"approval_{len(self._decision_history) + 1}"
        decision_record = QualityDecision(
            decision_id=decision_id,
            decision_type=DecisionType.APPROVE,
            score=100.0,
            confidence=1.0,
            reasons=[f"手动批准: {override_reason}"],
            details={
                "artifact": artifact.get("name", "unknown"),
                "override": True
            }
        )
        
        self._decision_history.append(decision_record)
        
        return {
            "decision": decision_record.to_dict(),
            "approved": True,
            "artifact": artifact.get("name", "unknown"),
            "timestamp": decision_record.timestamp.isoformat()
        }
    
    async def batch_decide(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """批量决策
        
        对多个制品进行决策
        
        Args:
            payload: 批量决策参数，包含artifacts列表
            
        Returns:
            Dict[str, Any]: 批量决策结果
        """
        artifacts = payload.get("artifacts", [])
        
        logger.info(f"开始批量决策: {len(artifacts)} 个制品")
        
        results = []
        
        for artifact in artifacts:
            # 为每个制品做出决策
            decision_result = await self.make_decision({
                "artifact": artifact,
                "issues": artifact.get("issues", []),
                "metrics": artifact.get("metrics", {})
            })
            results.append(decision_result)
        
        # 统计结果
        approve_count = sum(1 for r in results if r.get("decision", {}).get("decision_type") == "approve")
        reject_count = sum(1 for r in results if r.get("decision", {}).get("decision_type") == "reject")
        revision_count = sum(1 for r in results if r.get("decision", {}).get("decision_type") == "revision_required")
        escalate_count = sum(1 for r in results if r.get("needs_escalation", False))
        
        return {
            "total": len(artifacts),
            "results": results,
            "summary": {
                "approved": approve_count,
                "rejected": reject_count,
                "revision_required": revision_count,
                "escalated": escalate_count
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_quality_score(self, issues: List[Dict], metrics: Dict) -> float:
        """计算质量评分
        
        Args:
            issues: 问题列表
            metrics: 指标数据
            
        Returns:
            float: 质量评分 (0-100)
        """
        base_score = 100.0
        
        # 问题扣分
        severity_weights = {
            "critical": 20,
            "error": 10,
            "warning": 5,
            "info": 1
        }
        
        for issue in issues:
            severity = issue.get("severity", "info")
            weight = severity_weights.get(severity, 1)
            base_score -= weight
        
        # 代码度量影响
        if metrics:
            complexity = metrics.get("complexity", 0)
            if complexity > 10:
                base_score -= 5
            if complexity > 20:
                base_score -= 10
                
            comment_ratio = metrics.get("comment_ratio", 0)
            if comment_ratio < 0.1:
                base_score -= 3
        
        return max(0.0, round(base_score, 1))
    
    def _check_escalation(self, issues: List[Dict], score: float) -> bool:
        """检查是否需要升级
        
        Args:
            issues: 问题列表
            score: 质量评分
            
        Returns:
            bool: 是否需要升级
        """
        # 检查严重问题数量
        critical_count = sum(1 for i in issues if i.get("severity") == "critical")
        if critical_count > self._thresholds["critical_issues"]:
            return True
        
        # 检查安全问题
        security_count = sum(1 for i in issues if i.get("category") == "security")
        if security_count > self._thresholds["security_issues"]:
            return True
        
        # 检查分数
        if score < self._thresholds["escalate_score"]:
            return True
        
        return False
    
    def _determine_decision(
        self, 
        score: float, 
        issues: List[Dict], 
        needs_escalation: bool
    ) -> DecisionType:
        """确定决策类型
        
        Args:
            score: 质量评分
            issues: 问题列表
            needs_escalation: 是否需要升级
            
        Returns:
            DecisionType: 决策类型
        """
        if needs_escalation:
            return DecisionType.ESCALATE
        
        if score >= self._thresholds["approve_score"]:
            return DecisionType.APPROVE
        elif score >= self._thresholds["revision_score"]:
            return DecisionType.REVISION_REQUIRED
        else:
            return DecisionType.REJECT
    
    def _generate_decision_reasons(
        self, 
        decision: DecisionType, 
        score: float, 
        issues: List[Dict]
    ) -> List[str]:
        """生成决策原因
        
        Args:
            decision: 决策类型
            score: 质量评分
            issues: 问题列表
            
        Returns:
            List[str]: 原因列表
        """
        reasons = []
        
        # 添加评分原因
        if decision == DecisionType.APPROVE:
            reasons.append(f"质量评分 {score} 超过阈值 {self._thresholds['approve_score']}")
        elif decision == DecisionType.REVISION_REQUIRED:
            reasons.append(f"质量评分 {score} 处于中等水平，需要修改")
        elif decision == DecisionType.REJECT:
            reasons.append(f"质量评分 {score} 低于阈值 {self._thresholds['revision_score']}")
        elif decision == DecisionType.ESCALATE:
            reasons.append("存在严重问题，需要人工审核")
        
        # 添加问题类型原因
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        if critical_issues:
            reasons.append(f"存在 {len(critical_issues)} 个严重问题")
        
        security_issues = [i for i in issues if i.get("category") == "security"]
        if security_issues:
            reasons.append(f"存在 {len(security_issues)} 个安全问题")
        
        return reasons
    
    def _calculate_confidence(self, issues: List[Dict], metrics: Dict) -> float:
        """计算决策置信度
        
        Args:
            issues: 问题列表
            metrics: 指标数据
            
        Returns:
            float: 置信度 (0-1)
        """
        confidence = 0.8
        
        # 问题越多置信度越低
        if len(issues) > 10:
            confidence -= 0.1
        if len(issues) > 20:
            confidence -= 0.2
        
        # 有详细指标置信度更高
        if metrics:
            if metrics.get("complexity", 0) > 0:
                confidence += 0.1
        
        return max(0.5, min(1.0, confidence))
    
    def _determine_escalation_reason(
        self, 
        issues: List[Dict], 
        score: float
    ) -> EscalationReason:
        """确定升级原因
        
        Args:
            issues: 问题列表
            score: 质量评分
            
        Returns:
            EscalationReason: 升级原因
        """
        # 检查严重问题
        if any(i.get("severity") == "critical" for i in issues):
            return EscalationReason.CRITICAL_ISSUE
        
        # 检查安全问题
        if any(i.get("category") == "security" for i in issues):
            return EscalationReason.SECURITY_RISK
        
        # 检查分数
        if score < self._thresholds["escalate_score"]:
            return EscalationReason.MANUAL_REVIEW_REQUIRED
        
        return EscalationReason.MANUAL_REVIEW_REQUIRED
    
    def _determine_priority(self, issues: List[Dict], reason: str) -> str:
        """确定优先级
        
        Args:
            issues: 问题列表
            reason: 升级原因
            
        Returns:
            str: 优先级
        """
        # 严重问题优先
        if any(i.get("severity") == "critical" for i in issues):
            return "critical"
        
        # 安全问题高优先
        if any(i.get("category") == "security" for i in issues):
            return "high"
        
        # 根据原因判断
        reason_to_priority = {
            EscalationReason.CRITICAL_ISSUE.value: "critical",
            EscalationReason.SECURITY_RISK.value: "high",
            EscalationReason.POLICY_VIOLATION.value: "high",
            EscalationReason.RESOURCE_EXCEEDED.value: "normal",
            EscalationReason.MANUAL_REVIEW_REQUIRED.value: "normal"
        }
        
        return reason_to_priority.get(reason, "normal")
    
    def get_history(self, limit: int = 10) -> Dict[str, Any]:
        """获取历史记录
        
        Args:
            limit: 返回数量限制
            
        Returns:
            Dict: 历史记录
        """
        return {
            "decisions": [d.to_dict() for d in self._decision_history[-limit:]],
            "escalations": [
                {"escalation_id": e.escalation_id, "reason": e.reason.value, "priority": e.priority}
                for e in self._escalation_history[-limit:]
            ],
            "total_decisions": len(self._decision_history),
            "total_escalations": len(self._escalation_history)
        }
    
    def update_thresholds(self, thresholds: Dict[str, Any]):
        """更新阈值配置
        
        Args:
            thresholds: 新阈值配置
        """
        self._thresholds.update(thresholds)
        logger.info(f"阈值配置已更新: {self._thresholds}")