"""任务编排器 - 负责任务分发、依赖管理、结果汇总"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base import BaseAgent, AgentResult, AgentType, AgentStatus, Task
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionContext:
    """执行上下文"""
    task: Task
    subtasks: List[Task] = field(default_factory=list)
    results: Dict[str, AgentResult] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    status: AgentStatus = AgentStatus.IDLE


class OrchestratorAgent(BaseAgent):
    """任务编排器代理

    负责:
    1. 任务分发 - 将大任务拆分为子任务并分配给相应代理
    2. 依赖管理 - 管理任务间的依赖关系
    3. 结果汇总 - 收集并合并所有子任务结果
    """

    name: str = "orchestrator"
    description: str = "任务编排器，负责任务分发和结果汇总"
    agent_type: AgentType = AgentType.ORCHESTRATOR

    def __init__(self):
        super().__init__()
        self._agent_registry: Dict[AgentType, BaseAgent] = {}
        self._execution_contexts: Dict[str, ExecutionContext] = {}
        self._dependency_graph: Dict[str, List[str]] = {}

    def register_agent(self, agent: BaseAgent):
        """注册代理

        Args:
            agent: 代理实例
        """
        self._agent_registry[agent.agent_type] = agent
        logger.info(f"编排器注册代理: {agent.name}")

    def unregister_agent(self, agent_type: AgentType):
        """注销代理

        Args:
            agent_type: 代理类型
        """
        if agent_type in self._agent_registry:
            agent = self._agent_registry.pop(agent_type)
            logger.info(f"编排器注销代理: {agent.name}")

    async def execute(self, task: Task) -> AgentResult:
        """执行任务编排

        Args:
            task: 编排任务

        Returns:
            AgentResult: 执行结果
        """
        start_time = datetime.now()

        try:
            logger.info(f"编排器开始执行任务: {task.task_id} - {task.description}")

            # 分析任务依赖关系
            dependencies = await self.manage_dependencies(task)

            # 拆分任务为子任务
            subtasks = await self._split_task(task)

            # 调度并执行子任务
            results = await self.dispatch(subtasks, dependencies)

            # 汇总结果
            aggregated = await self.aggregate_results(results)

            # 构建返回结果
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return AgentResult(
                success=True,
                data=aggregated,
                metadata={
                    "task_id": task.task_id,
                    "subtask_count": len(subtasks),
                    "success_count": sum(1 for r in results.values() if r.success),
                    "failed_count": sum(1 for r in results.values() if not r.success)
                },
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"编排器执行失败: {e}", exc_info=True)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return AgentResult(
                success=False,
                error=str(e),
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )

    async def dispatch(self, subtasks: List[Task], dependencies: Dict[str, List[str]] = None) -> Dict[str, AgentResult]:
        """分发任务给相应代理

        Args:
            subtasks: 子任务列表
            dependencies: 依赖关系字典

        Returns:
            Dict[str, AgentResult]: 任务ID到结果的映射
        """
        results: Dict[str, AgentResult] = {}
        pending_tasks = subtasks.copy()
        completed_task_ids = set()
        dependencies = dependencies or {}

        logger.info(f"开始分发 {len(subtasks)} 个子任务")

        while pending_tasks:
            # 找出所有依赖都已完成的任务
            ready_tasks = []
            for task in pending_tasks:
                deps = dependencies.get(task.task_id, [])
                if all(dep_id in completed_task_ids for dep_id in deps):
                    ready_tasks.append(task)

            if not ready_tasks:
                # 没有可执行的任务，可能存在循环依赖
                logger.error(f"检测到循环依赖或依赖不满足: {[t.task_id for t in pending_tasks]}")
                # 强制执行剩余任务
                ready_tasks = pending_tasks[:1] if pending_tasks else []

            # 并发执行所有就绪任务
            if ready_tasks:
                task_batch = ready_tasks[:5]  # 最多同时执行5个任务
                logger.info(f"并发执行 {len(task_batch)} 个任务")

                async def execute_task(t: Task):
                    agent = self._find_agent_for_task(t)
                    if agent:
                        return await agent.execute(t)
                    else:
                        return AgentResult(
                            success=False,
                            error=f"未找到处理任务类型 {t.task_type} 的代理",
                            agent_type=t.task_type
                        )

                # 执行任务批次
                batch_results = await asyncio.gather(
                    *[execute_task(t) for t in task_batch],
                    return_exceptions=True
                )

                # 收集结果
                for task, result in zip(task_batch, batch_results):
                    if isinstance(result, Exception):
                        results[task.task_id] = AgentResult(
                            success=False,
                            error=str(result)
                        )
                    else:
                        results[task.task_id] = result

                    completed_task_ids.add(task.task_id)
                    pending_tasks.remove(task)

        logger.info(f"分发完成，成功: {sum(1 for r in results.values() if r.success)}, 失败: {sum(1 for r in results.values() if not r.success)}")
        return results

    async def manage_dependencies(self, task: Task) -> Dict[str, List[str]]:
        """管理任务依赖

        Args:
            task: 任务对象

        Returns:
            Dict[str, List[str]]: 任务ID到依赖列表的映射
        """
        dependency_graph: Dict[str, List[str]] = {}

        # 从任务负载中提取依赖信息
        if "subtasks" in task.payload:
            for subtask in task.payload["subtasks"]:
                subtask_id = subtask.get("task_id", f"subtask_{id(subtask)}")
                deps = subtask.get("dependencies", [])
                dependency_graph[subtask_id] = deps

        # 如果没有显式依赖，根据任务类型自动推断
        if not dependency_graph and len(task.payload.get("subtasks", [])) > 1:
            # 假设第一个任务没有依赖，其他任务依赖前一个任务
            subtasks = task.payload["subtasks"]
            for i, subtask in enumerate(subtasks[1:], start=1):
                prev_task_id = subtasks[i-1].get("task_id", f"subtask_{i-1}")
                task_id = subtask.get("task_id", f"subtask_{i}")
                if task_id not in dependency_graph:
                    dependency_graph[task_id] = []
                dependency_graph[task_id].append(prev_task_id)

        self._dependency_graph = dependency_graph
        logger.debug(f"依赖图: {dependency_graph}")
        return dependency_graph

    async def aggregate_results(self, results: Dict[str, AgentResult]) -> Dict[str, Any]:
        """汇总结果

        Args:
            results: 任务结果字典

        Returns:
            Dict[str, Any]: 汇总后的结果
        """
        all_success = all(r.success for r in results.values())
        total_execution_time = sum(r.execution_time_ms for r in results.values())

        # 收集所有数据
        all_data = []
        errors = []

        for task_id, result in results.items():
            if result.success and result.data:
                all_data.append({
                    "task_id": task_id,
                    "data": result.data
                })
            if result.error:
                errors.append({
                    "task_id": task_id,
                    "error": result.error
                })

        aggregated = {
            "overall_success": all_success,
            "total_tasks": len(results),
            "successful_tasks": sum(1 for r in results.values() if r.success),
            "failed_tasks": sum(1 for r in results.values() if not r.success),
            "total_execution_time_ms": total_execution_time,
            "results": all_data,
            "errors": errors
        }

        logger.info(f"结果汇总: 成功 {aggregated['successful_tasks']}/{aggregated['total_tasks']}")
        return aggregated

    def _find_agent_for_task(self, task: Task) -> Optional[BaseAgent]:
        """查找处理任务的代理

        Args:
            task: 任务对象

        Returns:
            Optional[BaseAgent]: 代理实例
        """
        for agent in self._agent_registry.values():
            if agent.can_handle(task):
                return agent

        # 如果没有找到专用代理，返回一个简单的模拟结果
        logger.warning(f"未找到处理任务类型 {task.task_type} 的代理")
        return None

    async def _split_task(self, task: Task) -> List[Task]:
        """拆分任务为子任务

        Args:
            task: 原始任务

        Returns:
            List[Task]: 子任务列表
        """
        subtasks = []

        # 如果已经有子任务定义，直接使用
        if "subtasks" in task.payload:
            for i, st in enumerate(task.payload["subtasks"]):
                subtask = Task(
                    task_id=st.get("task_id", f"{task.task_id}_subtask_{i}"),
                    task_type=st.get("task_type", st.get("type", "")),
                    description=st.get("description", st.get("desc", "")),
                    payload=st.get("payload", st.get("data", {})),
                    dependencies=st.get("dependencies", []),
                    priority=st.get("priority", 5)
                )
                subtasks.append(subtask)
        else:
            # 默认创建一个子任务
            subtasks.append(Task(
                task_id=f"{task.task_id}_subtask_0",
                task_type=task.task_type,
                description=task.description,
                payload=task.payload
            ))

        logger.debug(f"任务拆分: {task.task_id} -> {len(subtasks)} 个子任务")
        return subtasks

    def get_execution_status(self, context_id: str) -> Optional[ExecutionContext]:
        """获取执行上下文状态

        Args:
            context_id: 上下文ID

        Returns:
            Optional[ExecutionContext]: 执行上下文
        """
        return self._execution_contexts.get(context_id)

    def cancel_execution(self, context_id: str) -> bool:
        """取消执行

        Args:
            context_id: 上下文ID

        Returns:
            bool: 是否成功取消
        """
        if context_id in self._execution_contexts:
            self._execution_contexts[context_id].status = AgentStatus.FAILED
            logger.info(f"已取消执行上下文: {context_id}")
            return True
        return False