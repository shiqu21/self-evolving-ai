#!/usr/bin/env python3
"""
完美自我进化系统 - 主程序入口
Self-Evolving System v3.0
参考Hermes Agent Self-Evolution/OpenClaw/EvoAgentX最佳实践

功能:
- 5阶段进化循环 (OPERATE→DETECT→ANALYZE→ENCODE→VERIFY)
- 三阶段记忆系统
- 技能自动生成
- 定时自动运行
- 质量管道

使用方法:
    python main.py                    # 启动自动运行
    python main.py --once             # 运行单次循环
    python main.py --status           # 查看状态
    python main.py --test             # 测试模式
"""
import sys
import os
import argparse
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import Config, get_config, set_config
from storage.database import Database
from core.engine import EvolutionEngine
from scheduler.job_scheduler import JobScheduler
from utils.logger import setup_logger, get_logger
from storage.models import Skill
from datetime import datetime


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="完美自我进化系统")
    
    parser.add_argument(
        "--once", "-o",
        action="store_true",
        help="仅运行一次进化循环，不启动调度器"
    )
    
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="查看当前系统状态"
    )
    
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="测试模式:运行单元测试"
    )
    
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=5,
        help="进化循环间隔(分钟)，默认5分钟"
    )
    
    parser.add_argument(
        "--no-auto-run",
        action="store_true",
        help="不自动运行，需要手动触发"
    )
    
    return parser.parse_args()


def init_system(config: Config) -> tuple:
    """初始化系统组件"""
    # 设置日志
    logger = setup_logger("evolution", config.log_path)
    
    # 初始化数据库
    db = Database(config.db_path)
    
    # 初始化进化引擎
    engine = EvolutionEngine(config, db)
    
    return logger, db, engine


def show_status(engine: EvolutionEngine):
    """显示系统状态"""
    status = engine.get_status()
    
    print("\n" + "="*50)
    print("  完美自我进化系统 v3.0 - 状态报告")
    print("="*50)
    print(f"  循环次数: {status['cycle_count']}")
    print(f"  运行状态: {'运行中' if status['running'] else '已停止'}")
    print(f"  错误计数: {status['error_count']}")
    print(f"  错误阈值: {status['error_threshold']}")
    
    if status.get('last_error_time'):
        print(f"  上次错误: {status['last_error_time']}")
    
    print(f"\n  技能统计:")
    print(f"    - 活跃技能: {status['active_skills']}")
    print(f"    - 总技能数: {status['total_skills']}")
    
    print("="*50 + "\n")


def run_tests():
    """运行测试"""
    print("运行系统测试...")
    
    # 测试数据库
    try:
        db = Database("db/test_evolution.db")
        print("✓ 数据库连接正常")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return
    
    # 测试配置
    try:
        config = Config()
        print("✓ 配置加载正常")
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return
    
    # 测试进化引擎
    try:
        engine = EvolutionEngine(config, db)
        print("✓ 进化引擎初始化正常")
    except Exception as e:
        print(f"✗ 进化引擎初始化失败: {e}")
        return
    
    # 测试单次循环
    try:
        result = engine.run_cycle()
        print(f"✓ 循环执行成功: {result.success}")
    except Exception as e:
        print(f"✗ 循环执行失败: {e}")
    
    print("\n测试完成！")


def create_default_skills(engine: EvolutionEngine):
    """创建默认技能"""
    repo = engine.repo_factory.skill_repo
    
    # 检查是否已有技能
    existing = repo.get_all()
    if existing:
        return
    
    # 创建默认技能
    default_skills = [
        Skill(
            name="self_review",
            description="自我反思技能 - 分析执行结果并生成改进建议",
            content="",
            skill_type="skill_candidate",
            risk_level="micro",
            status="applied",
        ),
        Skill(
            name="error_learner",
            description="错误学习技能 - 从错误中学习并记录教训",
            content="",
            skill_type="skill_candidate",
            risk_level="micro",
            status="applied",
        ),
        Skill(
            name="optimizer",
            description="优化器技能 - 优化系统性能和资源配置",
            content="",
            skill_type="skill_candidate",
            risk_level="micro",
            status="candidate",
        ),
    ]
    
    for skill in default_skills:
        repo.create(skill)
    
    print(f"创建了 {len(default_skills)} 个默认技能")


def main():
    """主函数"""
    args = parse_args()
    
    # 加载配置
    config = Config.from_env()
    config.interval_minutes = args.interval
    set_config(config)
    
    # 测试模式
    if args.test:
        run_tests()
        return
    
    # 初始化系统
    logger, db, engine = init_system(config)
    
    # 创建默认技能
    create_default_skills(engine)
    
    # 状态查询
    if args.status:
        show_status(engine)
        return
    
    # 单次运行
    if args.once:
        logger.info("执行单次进化循环...")
        result = engine.run_cycle()
        logger.info(f"循环执行完成: {result.to_dict()}")
        print(f"\n执行结果: {'成功' if result.success else '失败'}")
        print(f"完成阶段: {result.phases_completed}")
        print(f"耗时: {result.duration:.2f}秒")
        return
    
    # 自动运行模式
    logger.info("启动完美自我进化系统...")
    logger.info(f"循环间隔: {config.interval_minutes}分钟")
    print("\n" + "="*50)
    print("  完美自我进化系统 v3.0")
    print("  参考: Hermes Agent Self-Evolution / OpenClaw / EvoAgentX")
    print("="*50)
    print(f"  循环间隔: {config.interval_minutes}分钟")
    print(f"  错误阈值: {config.error_threshold}次")
    print(f"  自动运行: {'是' if not args.no_auto_run else '否'}")
    print("="*50 + "\n")
    
    # 初始化调度器
    scheduler = JobScheduler(config.interval_minutes)
    scheduler.set_evolution_callback(engine.run_cycle)
    
    try:
        if not args.no_auto_run:
            scheduler.start()
            
            # 显示状态信息
            show_status(engine)
            
            print("系统正在自动运行...")
            print("按 Ctrl+C 停止")
            
            # 保持运行
            while True:
                import time
                time.sleep(60)
                # 定期显示状态
                if scheduler.scheduler.get_job('evolution_cycle'):
                    next_run = scheduler.get_next_run()
                    print(f"下次运行时间: {next_run}")
        else:
            # 手动触发模式
            print("手动触发模式，输入命令控制:")
            print("  run - 执行一次循环")
            print("  status - 查看状态")
            print("  exit - 退出")
            
            while True:
                try:
                    cmd = input("\n> ").strip()
                    
                    if cmd == "run":
                        result = engine.run_cycle()
                        print(f"执行结果: {'成功' if result.success else '失败'}")
                    elif cmd == "status":
                        show_status(engine)
                    elif cmd == "exit":
                        break
                    else:
                        print("未知命令")
                        
                except KeyboardInterrupt:
                    break
                    
    except KeyboardInterrupt:
        logger.info("接收到停止信号...")
    except Exception as e:
        logger.error(f"系统运行错误: {e}", exc_=True)
    finally:
        scheduler.stop()
        logger.info("系统已停止")


if __name__ == "__main__":
    main()