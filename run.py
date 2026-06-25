#!/usr/bin/env python3
"""
WorkBuddy 自我进化系统 - 运行入口（简化版）
"""
import sys
import os
import argparse
import logging
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 简化导入 - 只依赖核心引擎
from core.engine import EvolutionEngine
from storage.database import Database

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()), "WorkBuddy", "evolution.db")

def get_engine():
    """获取或创建引擎实例"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return EvolutionEngine(database=DB_PATH)

def run_once():
    """运行单次进化循环"""
    logger.info("开始执行进化循环...")
    engine = get_engine()
    result = engine.run_cycle()
    logger.info(f"进化完成: phase={result.phase}, status={result.status}, errors={result.errors}")
    return result

def show_status():
    """显示系统状态"""
    engine = get_engine()
    status = engine.get_status()
    dashboard = engine._get_evolution_dashboard()
    print("=== 状态 ===")
    for k, v in status.items(): print(f"  {k}: {v}")
    print("=== 仪表盘 ===")
    for k, v in dashboard.items(): print(f"  {k}: {v}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="自我进化系统")
    parser.add_argument("--once", "-o", action="store_true", help="运行单次进化")
    parser.add_argument("--status", "-s", action="store_true", help="查看状态")
    args = parser.parse_args()
    
    if args.status:
        show_status()
    elif args.once:
        run_once()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
