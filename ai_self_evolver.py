#!/usr/bin/env python3
"""
完美AI自我进化系统 - 服务于AI的进化引擎
让AI越用越聪明，自动进化！

核心功能:
- 记录AI的工作表现和错误
- 自动分析不足并生成改进方案  
- 积累技能和经验
- 每次使用都让AI变得更强
"""
import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# 配置
EVOLUTION_DIR = Path("C:/Users/Administrator/WorkBuddy/Claw/evolution")
sys.path.insert(0, str(EVOLUTION_DIR))

from config.config import Config, get_config, set_config
from storage.database import Database
from core.engine import EvolutionEngine
from memory.three_stage import SensoryBuffer, Hippocampus, Cortex
from storage.repositories import RepositoryFactory
from storage.models import Memory, Event
from utils.llm_client import get_llm_client
from utils.logger import setup_logger, get_logger


class AISelfEvolver:
    """AI自我进化器 - 让AI越用越聪明"""
    
    def __init__(self):
        setup_logger("evolution", "logs")
        self.logger = get_logger("AISelfEvolver")
        
        # 初始化组件
        config = Config.from_env()
        set_config(config)
        self.db = Database("db/evolution.db")
        self.repo_factory = RepositoryFactory(self.db)
        
        # 记忆系统
        self.hippocampus = Hippocampus(self.repo_factory.memory_repo)
        self.cortex = Cortex(self.repo_factory.memory_repo)
        self.sensory_buffer = SensoryBuffer()
        
        # LLM客户端
        self.llm = get_llm_client()
        
        # 统计
        self.total_reflections = 0
        self.total_improvements = 0
        
        self.logger.info("AI自我进化器初始化完成")
    
    def record_task(self, task_name: str, task_result: str, 
                   errors: list = None, learnings: list = None):
        """记录任务执行情况"""
        self.logger.info(f"记录任务: {task_name}")
        
        # 记录事件
        event = Event(
            timestamp=datetime.now(),
            event_type="task_execution",
            severity="info" if not errors else "error",
            description=f"任务: {task_name}, 结果: {task_result}",
            context=json.dumps({
                "task": task_name,
                "result": task_result,
                "errors": errors or [],
                "learnings": learnings or []
            })
        )
        self.repo_factory.event_repo.create(event)
        
        # 记录到感觉缓冲区
        self.sensory_buffer.capture({
            "type": "task_execution",
            "task_name": task_name,
            "result": task_result,
            "errors": errors or [],
            "learnings": learnings or [],
            "timestamp": datetime.now().isoformat()
        })
        
        self.total_reflections += 1
    
    def analyze_and_improve(self) -> dict:
        """分析并生成改进"""
        self.logger.info("开始自我分析和改进...")
        
        # 获取最近的错误
        recent_events = self.repo_factory.event_repo.get_recent(hours=24)
        errors = [e for e in recent_events if e.severity in ['error', 'critical']]
        
        if not errors:
            return {"status": "no_errors", "message": "近期无错误"}
        
        # 分析错误根源
        error_summary = "\n".join([
            f"- {e.event_type}: {e.description[:100]}" 
            for e in errors[:10]
        ])
        
        # 使用LLM分析并生成改进方案
        prompt = f"""作为AI，请分析你最近犯的错误，并生成改进方案:

错误列表:
{error_summary}

请回答:
1. 这些错误的共同根因是什么？
2. 你应该如何改进？
3. 生成1-3个具体的技能改进建议(如果需要新技能，列出技能名称和功能)
"""
        
        analysis = self.llm.chat(prompt)
        
        # 保存分析结果
        memory = Memory(
            topic="self_improvement",
            content=analysis,
            created_at=datetime.now(),
            importance=9
        )
        self.repo_factory.memory_repo.create(memory)
        
        # 编码到长期记忆
        facts = self.hippocampus.encode(self.sensory_buffer.get_all())
        self.cortex.integrate(facts)
        self.sensory_buffer.clear()
        
        self.total_improvements += 1
        
        return {
            "status": "improved",
            "errors_analyzed": len(errors),
            "analysis": analysis,
            "improvements_count": self.total_improvements
        }
    
    def get_learned_skills(self) -> list:
        """获取已学习的技能/经验"""
        memories = self.repo_factory.memory_repo.get_by_topic("self_improvement")
        return [
            {
                "content": m.content[:200],
                "importance": m.importance,
                "created_at": m.created_at.isoformat()
            }
            for m in memories
        ]
    
    def get_capability_summary(self) -> dict:
        """获取能力摘要"""
        total_events = len(self.repo_factory.event_repo.get_recent(hours=168))  # 一周
        total_memories = len(self.repo_factory.memory_repo.get_all())
        total_skills = len(self.repo_factory.skill_repo.get_all())
        
        return {
            "total_reflections": self.total_reflections,
            "total_improvements": self.total_improvements,
            "weekly_events": total_events,
            "total_memories": total_memories,
            "total_skills": total_skills,
            "capability_level": min(10, self.total_improvements + 1)
        }
    
    def auto_evolve(self):
        """自动进化一次"""
        # 1. 记录当前状态
        self.record_task(
            task_name="auto_evolve",
            task_result="running",
            errors=[],
            learnings=[f"第{self.total_reflections + 1}次自我反思"]
        )
        
        # 2. 分析并改进
        result = self.analyze_and_improve()
        
        return result


def main():
    evolver = AISelfEvolver()
    
    print("\n" + "="*60)
    print("  🧠 AI自我进化系统 - 让AI越用越聪明")
    print("="*60)
    
    # 显示能力摘要
    summary = evolver.get_capability_summary()
    print(f"\n📊 能力状态:")
    print(f"   自我反思次数: {summary['total_reflections']}")
    print(f"   改进次数: {summary['total_improvements']}")
    print(f"   一周事件数: {summary['weekly_events']}")
    print(f"   记忆数量: {summary['total_memories']}")
    print(f"   技能数量: {summary['total_skills']}")
    print(f"   能力等级: {'⭐' * summary['capability_level']}")
    
    # 自动进化
    print(f"\n🔄 开始自动进化...")
    result = evolver.auto_evolve()
    print(f"   状态: {result.get('status', 'unknown')}")
    print(f"   改进数: {result.get('improvements_count', 0)}")
    
    # 显示已学到的技能
    skills = evolver.get_learned_skills()[:3]
    if skills:
        print(f"\n📝 最近学习:")
        for i, s in enumerate(skills, 1):
            print(f"   {i}. {s['content'][:80]}...")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()