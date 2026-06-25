"""事件监控器 - 监控所有会话中的错误和异常"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from agents.base import BaseAgent, AgentResult, AgentType, Task
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MonitoredEvent:
    """监控事件"""
    event_id: str = ""
    session_id: str = ""
    event_type: str = ""
    severity: str = ""
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionSummary:
    """会话摘要"""
    session_id: str = ""
    event_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    critical_count: int = 0
    first_event_time: Optional[datetime] = None
    last_event_time: Optional[datetime] = None
    events: List[MonitoredEvent] = field(default_factory=list)


class EventMonitorAgent(BaseAgent):
    """事件监控器代理

    负责:
    1. 扫描会话 - 监控所有会话中的错误和异常
    2. 捕获事件 - 收集和记录监控数据
    3. 创建报告 - 生成监控报告
    """

    name: str = "event_monitor"
    description: str = "事件监控器，监控所有会话中的错误和异常"
    agent_type: AgentType = AgentType.EVENT_MONITOR

    def __init__(self):
        super().__init__()
        self._session_data: Dict[str, SessionSummary] = {}
        self._all_events: List[MonitoredEvent] = []
        self._monitoring_active = False
        self._scan_interval = 60  # 扫描间隔(秒)

    async def execute(self, task: Task) -> AgentResult:
        """执行事件监控

        Args:
            task: 监控任务

        Returns:
            AgentResult: 监控结果
        """
        start_time = datetime.now()

        try:
            action = task.payload.get("action", "scan")

            if action == "scan":
                result_data = await self.scan_sessions(task.payload)
            elif action == "capture":
                result_data = await self.capture_event(task.payload)
            elif action == "report":
                result_data = await self.create_report(task.payload)
            elif action == "monitor":
                result_data = await self.start_monitoring(task.payload)
            elif action == "stop":
                result_data = await self.stop_monitoring()
            else:
                result_data = {"message": f"未知操作: {action}"}

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "action": action,
                    "total_events": len(self._all_events),
                    "active_sessions": len(self._session_data)
                },
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"事件监控执行失败: {e}", exc_info=True)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return AgentResult(
                success=False,
                error=str(e),
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )

    async def scan_sessions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """扫描会话

        扫描所有活跃会话，检测错误和异常

        Args:
            payload: 负载参数

        Returns:
            Dict[str, Any]: 扫描结果
        """
        hours = payload.get("hours", 1)
        session_filter = payload.get("session_id", None)
        severity_filter = payload.get("severity", None)

        logger.info(f"开始扫描会话 (最近 {hours} 小时)")

        # 模拟扫描 - 实际应该从数据库或事件总线获取
        await asyncio.sleep(0.1)  # 模拟异步操作

        # 生成扫描结果
        sessions_scanned = session_filter or "all"
        events_found = self._get_cached_events(hours, session_filter, severity_filter)

        session_stats = self._calculate_session_stats(events_found)

        result = {
            "scanned_sessions": sessions_scanned,
            "total_sessions": len(self._session_data),
            "events_detected": len(events_found),
            "session_stats": session_stats,
            "scan_time": datetime.now().isoformat()
        }

        logger.info(f"扫描完成: 检测到 {len(events_found)} 个事件")
        return result

    async def capture_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """捕获事件

        将新事件记录到监控系统中

        Args:
            payload: 事件数据

        Returns:
            Dict[str, Any]: 捕获结果
        """
        session_id = payload.get("session_id", "unknown")
        event_type = payload.get("event_type", "info")
        severity = payload.get("severity", "info")
        description = payload.get("description", "")
        metadata = payload.get("metadata", {})

        # 创建监控事件
        event = MonitoredEvent(
            event_id=payload.get("event_id", f"evt_{len(self._all_events)}"),
            session_id=session_id,
            event_type=event_type,
            severity=severity,
            description=description,
            timestamp=datetime.now(),
            metadata=metadata
        )

        # 存储事件
        self._all_events.append(event)

        # 更新会话摘要
        if session_id not in self._session_data:
            self._session_data[session_id] = SessionSummary(session_id=session_id)

        session = self._session_data[session_id]
        session.event_count += 1
        session.events.append(event)

        if severity in ["error", "critical"]:
            session.error_count += 1
        elif severity == "warning":
            session.warning_count += 1
        if severity == "critical":
            session.critical_count += 1

        if session.first_event_time is None:
            session.first_event_time = event.timestamp
        session.last_event_time = event.timestamp

        logger.info(f"捕获事件: {event.event_id} (session={session_id}, severity={severity})")

        return {
            "event_id": event.event_id,
            "session_id": session_id,
            "captured": True,
            "timestamp": event.timestamp.isoformat()
        }

    async def create_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """创建报告

        生成监控报告，包含错误统计和趋势分析

        Args:
            payload: 报告参数

        Returns:
            Dict[str, Any]: 报告数据
        """
        report_type = payload.get("type", "summary")
        session_id = payload.get("session_id", None)

        logger.info(f"创建监控报告 (type={report_type})")

        # 获取相关事件
        events = self._all_events
        if session_id:
            events = [e for e in events if e.session_id == session_id]

        if report_type == "summary":
            # 汇总报告
            total_events = len(events)
            error_events = [e for e in events if e.severity in ["error", "critical"]]
            warning_events = [e for e in events if e.severity == "warning"]

            # 按事件类型分组
            events_by_type = defaultdict(int)
            events_by_severity = defaultdict(int)
            events_by_session = defaultdict(int)

            for event in events:
                events_by_type[event.event_type] += 1
                events_by_severity[event.severity] += 1
                events_by_session[event.session_id] += 1

            report = {
                "report_type": "summary",
                "generated_at": datetime.now().isoformat(),
                "total_events": total_events,
                "error_count": len(error_events),
                "warning_count": len(warning_events),
                "events_by_type": dict(events_by_type),
                "events_by_severity": dict(events_by_severity),
                "events_by_session": dict(events_by_session),
                "active_sessions": len(set(e.session_id for e in events))
            }

        elif report_type == "detailed":
            # 详细报告
            recent_events = sorted(events, key=lambda e: e.timestamp, reverse=True)[:100]

            report = {
                "report_type": "detailed",
                "generated_at": datetime.now().isoformat(),
                "total_events": len(events),
                "recent_events": [
                    {
                        "event_id": e.event_id,
                        "session_id": e.session_id,
                        "event_type": e.event_type,
                        "severity": e.severity,
                        "description": e.description,
                        "timestamp": e.timestamp.isoformat()
                    }
                    for e in recent_events
                ],
                "session_summaries": [
                    {
                        "session_id": s.session_id,
                        "event_count": s.event_count,
                        "error_count": s.error_count,
                        "warning_count": s.warning_count,
                        "first_event": s.first_event_time.isoformat() if s.first_event_time else None,
                        "last_event": s.last_event_time.isoformat() if s.last_event_time else None
                    }
                    for s in self._session_data.values()
                ]
            }

        elif report_type == "critical":
            # 关键问题报告
            critical_events = [
                e for e in events
                if e.severity in ["error", "critical"]
            ]

            report = {
                "report_type": "critical",
                "generated_at": datetime.now().isoformat(),
                "critical_count": len(critical_events),
                "critical_events": [
                    {
                        "event_id": e.event_id,
                        "session_id": e.session_id,
                        "event_type": e.event_type,
                        "description": e.description,
                        "timestamp": e.timestamp.isoformat()
                    }
                    for e in critical_events[:50]  # 限制数量
                ]
            }

        else:
            report = {"error": f"未知的报告类型: {report_type}"}

        logger.info(f"报告生成完成: {report.get('total_events', 0)} 个事件")
        return report

    async def start_monitoring(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """开始持续监控

        Args:
            payload: 监控配置

        Returns:
            Dict[str, Any]: 启动结果
        """
        if self._monitoring_active:
            return {"message": "监控已在运行中", "active": True}

        self._scan_interval = payload.get("interval", 60)
        self._monitoring_active = True

        logger.info(f"开始监控 (间隔: {self._scan_interval}秒)")

        # 启动监控循环
        asyncio.create_task(self._monitoring_loop())

        return {
            "message": "监控已启动",
            "active": True,
            "interval": self._scan_interval
        }

    async def stop_monitoring(self) -> Dict[str, Any]:
        """停止监控

        Returns:
            Dict[str, Any]: 停止结果
        """
        if not self._monitoring_active:
            return {"message": "监控未在运行", "active": False}

        self._monitoring_active = False
        logger.info("监控已停止")

        return {
            "message": "监控已停止",
            "active": False,
            "total_events": len(self._all_events)
        }

    async def _monitoring_loop(self):
        """监控循环"""
        while self._monitoring_active:
            try:
                # 执行扫描
                await self.scan_sessions({"hours": 1})

                # 等待下一个扫描周期
                await asyncio.sleep(self._scan_interval)

            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                await asyncio.sleep(5)  # 出错时短暂等待

    def _get_cached_events(
        self,
        hours: int,
        session_filter: Optional[str],
        severity_filter: Optional[str]
    ) -> List[MonitoredEvent]:
        """获取缓存的事件

        Args:
            hours: 最近几小时
            session_filter: 会话过滤
            severity_filter: 严重级别过滤

        Returns:
            List[MonitoredEvent]: 事件列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        events = self._all_events

        # 时间过滤
        events = [e for e in events if e.timestamp >= cutoff_time]

        # 会话过滤
        if session_filter:
            events = [e for e in events if e.session_id == session_filter]

        # 严重级别过滤
        if severity_filter:
            events = [e for e in events if e.severity == severity_filter]

        return events

    def _calculate_session_stats(self, events: List[MonitoredEvent]) -> Dict[str, Any]:
        """计算会话统计

        Args:
            events: 事件列表

        Returns:
            Dict[str, Any]: 统计信息
        """
        sessions = defaultdict(lambda: {
            "total": 0,
            "errors": 0,
            "warnings": 0
        })

        for event in events:
            sessions[event.session_id]["total"] += 1
            if event.severity in ["error", "critical"]:
                sessions[event.session_id]["errors"] += 1
            elif event.severity == "warning":
                sessions[event.session_id]["warnings"] += 1

        return {
            "session_count": len(sessions),
            "sessions": dict(sessions)
        }

    def add_test_event(self, event: MonitoredEvent):
        """添加测试事件

        Args:
            event: 监控事件
        """
        self._all_events.append(event)