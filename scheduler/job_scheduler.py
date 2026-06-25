"""调度器 - 多层级自动运行主循环

支持:
- 每小时的快速自检
- 每天的知识沉淀
- 每周的技能优化
- 每月的深度进化
"""
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import Callable, Optional, Dict, Any

logger = logging.getLogger("evolution.scheduler")


class JobScheduler:
    """定时任务调度器 - 自动执行进化循环

    支持多种运行频率:
    - evolution_cycle: 基础进化循环 (默认5分钟)
    - hourly_check: 每小时自检
    - daily_consolidation: 每天知识沉淀
    - weekly_optimization: 每周技能优化
    - monthly_evolution: 每月深度进化
    """

    def __init__(self, interval_minutes: int = 5):
        """初始化调度器

        Args:
            interval_minutes: 进化循环间隔(分钟)
        """
        self.interval = interval_minutes
        self.scheduler = BlockingScheduler()
        self.running = False
        self.cycle_callback: Optional[Callable] = None
        self.hourly_callback: Optional[Callable] = None
        self.daily_callback: Optional[Callable] = None
        self.weekly_callback: Optional[Callable] = None
        self.monthly_callback: Optional[Callable] = None
        self._job_results: Dict[str, Any] = {}

    def set_evolution_callback(self, callback: Callable):
        """设置进化循环回调"""
        self.cycle_callback = callback

    def set_hourly_callback(self, callback: Callable):
        """设置每小时自检回调"""
        self.hourly_callback = callback

    def set_daily_callback(self, callback: Callable):
        """设置每天知识沉淀回调"""
        self.daily_callback = callback

    def set_weekly_callback(self, callback: Callable):
        """设置每周技能优化回调"""
        self.weekly_callback = callback

    def set_monthly_callback(self, callback: Callable):
        """设置每月深度进化回调"""
        self.monthly_callback = callback

    def set_all_callbacks(self, callbacks: Dict[str, Callable]):
        """批量设置回调

        Args:
            callbacks: 回调字典，支持键: evolution, hourly, daily, weekly, monthly
        """
        if "evolution" in callbacks:
            self.set_evolution_callback(callbacks["evolution"])
        if "hourly" in callbacks:
            self.set_hourly_callback(callbacks["hourly"])
        if "daily" in callbacks:
            self.set_daily_callback(callbacks["daily"])
        if "weekly" in callbacks:
            self.set_weekly_callback(callbacks["weekly"])
        if "monthly" in callbacks:
            self.set_monthly_callback(callbacks["monthly"])

    def start(self, enable_all: bool = True):
        """启动调度器

        Args:
            enable_all: 是否启用所有定时任务
        """
        if self.running:
            logger.warning("调度器已在运行")
            return

        # 1. 基础进化循环 - 默认间隔
        if self.cycle_callback:
            self.scheduler.add_job(
                self._run_evolution_cycle,
                trigger=IntervalTrigger(minutes=self.interval),
                id='evolution_cycle',
                name='进化循环',
                replace_existing=True
            )
            logger.info(f"添加进化循环任务，间隔: {self.interval}分钟")

        if enable_all:
            # 2. 每小时自检
            if self.hourly_callback:
                self.scheduler.add_job(
                    self._run_hourly_check,
                    trigger=CronTrigger(minute=0),  # 每小时整点
                    id='hourly_check',
                    name='每小时自检',
                    replace_existing=True
                )
                logger.info("添加每小时自检任务")

            # 3. 每天知识沉淀 (凌晨2点)
            if self.daily_callback:
                self.scheduler.add_job(
                    self._run_daily_consolidation,
                    trigger=CronTrigger(hour=2, minute=0),
                    id='daily_consolidation',
                    name='每日知识沉淀',
                    replace_existing=True
                )
                logger.info("添加每日知识沉淀任务")

            # 4. 每周技能优化 (周日凌晨3点)
            if self.weekly_callback:
                self.scheduler.add_job(
                    self._run_weekly_optimization,
                    trigger=CronTrigger(day_of_week=6, hour=3, minute=0),
                    id='weekly_optimization',
                    name='每周技能优化',
                    replace_existing=True
                )
                logger.info("添加每周技能优化任务")

            # 5. 每月深度进化 (每月1日凌晨4点)
            if self.monthly_callback:
                self.scheduler.add_job(
                    self._run_monthly_evolution,
                    trigger=CronTrigger(day=1, hour=4, minute=0),
                    id='monthly_evolution',
                    name='每月深度进化',
                    replace_existing=True
                )
                logger.info("添加每月深度进化任务")

        try:
            self.scheduler.start()
            self.running = True
            logger.info("调度器启动成功")
        except Exception as e:
            logger.error(f"调度器启动失败: {e}")
            raise

    def stop(self):
        """停止调度器"""
        if not self.running:
            return

        try:
            self.scheduler.shutdown(wait=False)
            self.running = False
            logger.info("调度器已停止")
        except Exception as e:
            logger.error(f"调度器停止失败: {e}")

    def _run_evolution_cycle(self):
        """运行进化循环"""
        if self.cycle_callback:
            try:
                logger.info("触发进化循环...")
                result = self.cycle_callback()
                self._job_results['evolution_cycle'] = {
                    'success': result.status == "success" if result else False,
                    'timestamp': datetime.now().isoformat()
                }
                if result:
                    logger.info(f"进化循环完成: status={result.status}")
            except Exception as e:
                logger.error(f"进化循环失败: {e}", exc_info=True)
                self._job_results['evolution_cycle'] = {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }

    def _run_hourly_check(self):
        """运行每小时自检"""
        if self.hourly_callback:
            try:
                logger.info("触发每小时自检...")
                result = self.hourly_callback()
                self._job_results['hourly_check'] = {
                    'success': result.get('success', False) if isinstance(result, dict) else bool(result),
                    'timestamp': datetime.now().isoformat()
                }
                if result:
                    logger.info(f"每小时自检完成: {result}")
            except Exception as e:
                logger.error(f"每小时自检失败: {e}", exc_info=True)
                self._job_results['hourly_check'] = {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }

    def _run_daily_consolidation(self):
        """运行每日知识沉淀"""
        if self.daily_callback:
            try:
                logger.info("触发每日知识沉淀...")
                result = self.daily_callback()
                self._job_results['daily_consolidation'] = {
                    'success': result.get('success', False) if isinstance(result, dict) else bool(result),
                    'timestamp': datetime.now().isoformat()
                }
                if result:
                    logger.info(f"每日知识沉淀完成: {result}")
            except Exception as e:
                logger.error(f"每日知识沉淀失败: {e}", exc_info=True)
                self._job_results['daily_consolidation'] = {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }

    def _run_weekly_optimization(self):
        """运行每周技能优化"""
        if self.weekly_callback:
            try:
                logger.info("触发每周技能优化...")
                result = self.weekly_callback()
                self._job_results['weekly_optimization'] = {
                    'success': result.get('success', False) if isinstance(result, dict) else bool(result),
                    'timestamp': datetime.now().isoformat()
                }
                if result:
                    logger.info(f"每周技能优化完成: {result}")
            except Exception as e:
                logger.error(f"每周技能优化失败: {e}", exc_info=True)
                self._job_results['weekly_optimization'] = {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }

    def _run_monthly_evolution(self):
        """运行每月深度进化"""
        if self.monthly_callback:
            try:
                logger.info("触发每月深度进化...")
                result = self.monthly_callback()
                self._job_results['monthly_evolution'] = {
                    'success': result.get('success', False) if isinstance(result, dict) else bool(result),
                    'timestamp': datetime.now().isoformat()
                }
                if result:
                    logger.info(f"每月深度进化完成: {result}")
            except Exception as e:
                logger.error(f"每月深度进化失败: {e}", exc_info=True)
                self._job_results['monthly_evolution'] = {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }

    def trigger_now(self, job_id: str = 'evolution_cycle'):
        """立即触发指定任务

        Args:
            job_id: 任务ID
        """
        handlers = {
            'evolution_cycle': self._run_evolution_cycle,
            'hourly_check': self._run_hourly_check,
            'daily_consolidation': self._run_daily_consolidation,
            'weekly_optimization': self._run_weekly_optimization,
            'monthly_evolution': self._run_monthly_evolution
        }

        if job_id in handlers:
            handlers[job_id]()
        else:
            logger.warning(f"未知任务ID: {job_id}")

    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.running and self.scheduler.running

    def get_next_run(self, job_id: str = 'evolution_cycle') -> Optional[datetime]:
        """获取任务下次运行时间"""
        job = self.scheduler.get_job(job_id)
        return job.next_run_time if job else None

    def get_job_status(self) -> Dict[str, Any]:
        """获取所有任务状态"""
        jobs = self.scheduler.get_jobs()
        status = {}
        for job in jobs:
            status[job.id] = {
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'pending': job.pending
            }
        return status

    def get_results(self) -> Dict[str, Any]:
        """获取任务执行结果"""
        return self._job_results.copy()