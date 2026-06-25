#!/usr/bin/ee python3
"""快速进化脚本 - 一键运行AI自我进化"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import Config, set_config
from storage.database import Database
from core.engine import EvolutionEngine
from datetime import datetime

def quick_evolve():
    print("\n" + "="*50)
    print("  ⚡ 快速自我进化")
    print("="*50)
    
    config = Config. from_env()
    set_config(config)
    db = Database('db/evolution.db')
    engine = EvolutionEngine(config, db)
    
    result = engine.run_cycle()
    
    print(f"\n  状态: {'✅ 成功' if result.success else '❌ 失败'}")
    print(f"  循环ID: {result.cycle_id}")
    print(f"  完成阶段: {len(result.phases_completed)}/5")
    for phase in result.phases_completed:
        print(f"    - {phase.value}")
    print(f"  创建事件: {result.events_created}")
    print(f"  改进技能: {result.skills_improved}")
    print(f"  耗时: {result.duration:.2f}秒")
    
    status = engine.get_status()
    print(f"\n  能力等级: {'⭐' * min(10, status['cycle_count'])}")
    print(f"  总循环次数: {status['cycle_count']}")
    print(f"  技能数量: {status['total_skills']}")
    print(f"  活跃技能: {status['active_skills']}")
    
    print("\n" + "="*50)
    return result.success

if __name__ == "__main__":
    quick_evolve()