#!/usr/bin/env python3
"""
自我进化系统启动检查脚本
验证系统能否正常启动并运行一个完整周期
"""
import sys
import os
import time
from datetime import datetime

def check_imports():
    """检查依赖导入"""
    print("[检查1] 依赖导入...")
    try:
        import apscheduler
        print(f"  ✓ apscheduler {apscheduler.__version__ if hasattr(apscheduler, '__version__') else ''}")
    except ImportError as e:
        print(f"  ✗ {e}")
        return False
    
    try:
        from core.engine import EvolutionEngine
        print("  ✓ core.engine.EvolutionEngine")
    except ImportError as e:
        print(f"  ✗ {e}")
        return False
    
    try:
        from scheduler.job_scheduler import JobScheduler
        print("  ✓ scheduler.job_scheduler.JobScheduler")
    except ImportError as e:
        print(f"  ✗ {e}")
        return False
    
    return True

def check_config():
    """检查配置"""
    print("\n[检查2] 配置...")
    try:
        from config.config import Config
        config = Config.from_env()
        print(f"  ✓ 配置加载成功")
        print(f"    LLM模型: {config.llm_model}")
        print(f"    循环间隔: {config.interval_minutes}分钟")
        if not config.llm_api_key:
            print(f"  ⚠ LLM API Key未配置，将使用本地模拟模式")
        return True
    except Exception as e:
        print(f"  ✗ 配置加载失败: {e}")
        return False

def run_single_cycle():
    """运行单个进化周期"""
    print("\n[检查3] 运行单次进化周期...")
    try:
        from core.engine import EvolutionEngine
        from config.config import Config
        from storage.database import Database
        
        config = Config.from_env()
        database = Database()
        engine = EvolutionEngine(database)
        
        print("  运行周期...")
        result = engine.run_cycle()
        
        print(f"  周期完成: status={result.status}, improvements={result.improvements}")
        return result.status == "success" or result.status == "completed"
    except Exception as e:
        print(f"  ✗ 周期运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("  自我进化系统启动检查")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {
        "imports": check_imports(),
        "config": check_config(),
        "cycle": run_single_cycle() if check_imports() and check_config() else False
    }
    
    print("\n" + "=" * 60)
    print("  检查结果")
    print("=" * 60)
    for key, value in results.items():
        status = "✓ 通过" if value else "✗ 失败"
        print(f"  {key}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("  ✓ 所有检查通过，系统可以正常启动")
    else:
        print("  ✗ 部分检查失败，请查看上述错误信息")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
