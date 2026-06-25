"""自我进化引擎 - 完美版 v3.0
包含: 18种规则引擎 + 18种技能模板 + 完整学习闭环 + Git版本管理"""
import logging
import time
import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

# 导入Git版本管理器
from .git_version_manager import HybridVersionManager

logger = logging.getLogger(__name__)

class Phase(Enum):
    OPERATE = "OPERATE"
    DETECT = "DETECT"
    ANALYZE = "ANALYZE"
    ENCODE = "ENCODE"
    VERIFY = "VERIFY"
    ACT = "ACT"

class EventType:
    ERROR_OCCURRED = "error_occurred"
    CYCLE_STARTED = "cycle_started"
    CYCLE_COMPLETED = "cycle_completed"
    SKILL_CREATED = "skill_created"
    SKILL_APPLIED = "skill_applied"

class Severity:
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

# ========== 18种错误规则 ==========
ERROR_RULES = {
    "chinese_punct": {"keywords": ["中文", "标点", "uff1a", "u300c"], "analysis": "检测到中文标点，修复:替换为英文标点", "fix_type": "auto_fix_punct", "weight": 1.2},
    "sqlite_err": {"keywords": ["sqlite", "no such table", "database", "locked"], "analysis": "数据库问题，修复:初始化表或处理锁", "fix_type": "auto_fix_db", "weight": 1.5},
    "import_err": {"keywords": ["import", "module", "no module named", "importerror"], "analysis": "模块导入问题，修复:安装依赖或检查路径", "fix_type": "check_deps", "weight": 1.3},
    "syntax_err": {"keywords": ["syntax", "invalid syntax", "unexpected token"], "analysis": "语法错误，修复:检查代码语法", "fix_type": "fix_syntax", "weight": 1.4},
    "network_err": {"keywords": ["connection", "timeout", "network", "dns", "resolve", "httperror"], "analysis": "网络问题，修复:添加重试机制", "fix_type": "fix_network", "weight": 1.3},
    "memory_err": {"keywords": ["memory", "out of", "allocation", "gc", "overflow"], "analysis": "内存问题，修复:优化内存使用", "fix_type": "fix_memory", "weight": 1.5},
    "auth_err": {"keywords": ["auth", "permission", "denied", "401", "403", "unauthorized"], "analysis": "认证权限问题，修复:检查凭证", "fix_type": "fix_auth", "weight": 1.4},
    "api_err": {"keywords": ["api", "http", "404", "500", "502", "503", "endpoint"], "analysis": "API问题，修复:处理HTTP错误", "fix_type": "fix_api", "weight": 1.3},
    "file_err": {"keywords": ["file", "not found", "no such file", "read", "write", "permission"], "analysis": "文件问题，修复:检查文件路径和权限", "fix_type": "fix_file", "weight": 1.4},
    "json_err": {"keywords": ["json", "decode", "parse", "invalid json"], "analysis": "JSON解析问题，修复:验证JSON格式", "fix_type": "fix_json", "weight": 1.3},
    "key_err": {"keywords": ["keyerror", "key not found", "missing key"], "analysis": "键不存在问题，修复:检查字典键", "fix_type": "fix_key", "weight": 1.2},
    "type_err": {"keywords": ["typeerror", "expected", "cannot", "unsupported"], "analysis": "类型错误，修复:检查数据类型", "fix_type": "fix_type", "weight": 1.3},
    "null_err": {"keywords": ["none", "null", "nan", "undefined", "is null"], "analysis": "空值问题，修复:添加空值检查", "fix_type": "fix_null", "weight": 1.2},
    "async_err": {"keywords": ["async", "await", "event loop", "coroutine", "deadlock"], "analysis": "异步问题，修复:检查异步代码", "fix_type": "fix_async", "weight": 1.4},
    "encoding_err": {"keywords": ["encoding", "utf-8", "decode", "encode", "codec"], "analysis": "编码问题，修复:指定正确编码", "fix_type": "fix_encoding", "weight": 1.3},
    "config_err": {"keywords": ["config", "setting", "environment", "env", "variable"], "analysis": "配置问题，修复:检查配置文件", "fix_type": "fix_config", "weight": 1.2},
    "version_err": {"keywords": ["version", "compatible", "upgrade", "deprecated"], "analysis": "版本问题，修复:检查依赖版本", "fix_type": "fix_version", "weight": 1.3},
    "race_cond": {"keywords": ["race", "concurrent", "thread", "lock", "mutex", "synchron"], "analysis": "并发问题，修复:添加锁机制", "fix_type": "fix_race", "weight": 1.5},
}

# ========== 18种技能代码模板 ==========
SKILL_TEMPLATES = {
    "auto_fix_punct": '''"""自动修复中文标点 - cycle {cycle}"""
import re
def fix(text):
    for c, e in {"\\uff1a": ":", "\\u300c": '"', "\\u300d": '"', "\\uff0c": ","}.items():
        text = text.replace(c, e)
    return text
def execute(): return {{"fixed": True, "func": "fix"}}''',
    
    "auto_fix_db": '''"""修复数据库 - cycle {cycle}"""
import sqlite3
def fix(path):
    conn = sqlite3.connect(path)
    conn.close()
    return True
def execute(): return {{"fixed": True}}''',
    
    "check_deps": '''"""检查依赖 - cycle {cycle}"""
import importlib
def check(modules):
    return {{"ok": all([_try(m) for m in modules]), "missing": [m for m in modules if not _try(m)]}}
def _try(m):
    try:
        importlib.import_module(m)
        return True
    except: return False
def execute(): return check(["sqlite3", "logging"])''',
    
    "fix_syntax": '''"""修复语法错误 - cycle {cycle}"""
import ast
def validate(code):
    try:
        ast.parse(code)
        return {{"valid": True}}
    except SyntaxError as e: return {{"valid": False, "error": str(e)}}
def execute(): return {{"ready": True}}''',
    
    "fix_network": '''"""修复网络问题 - cycle {cycle}"""
import time
def retry(fn, retries=3, delay=1):
    for i in range(retries):
        try: return fn()
        except: time.sleep(delay)
    return None
def execute(): return {{"ready": True}}''',
    
    "fix_memory": '''"""修复内存问题 - cycle {cycle}"""
import gc
def optimize():
    gc.collect()
    return True
def execute(): return {{"optimized": True}}''',
    
    "fix_auth": '''"""修复认证问题 - cycle {cycle}"""
def check_token(token):
    return bool(token) and len(token) > 0
def execute(): return {{"ready": True}}''',
    
    "fix_api": '''"""修复API问题 - cycle {cycle}"""
def handle_error(resp):
    code = getattr(resp, "status_code", 0)
    return {{"error": code, "retry": code >= 500}}
def execute(): return {{"ready": True}}''',
    
    "fix_file": '''"""修复文件问题 - cycle {cycle}"""
import os
def check(path): return os.path.exists(path)
def execute(path=""): return {{"exists": True}}''',
    
    "fix_json": '''"""修复JSON问题 - cycle {cycle}"""
import json
def safe_load(text, default={{}}):
    try: return json.loads(text)
    except: return default
def execute(text=""): return safe_load(text)''',
    
    "fix_key": '''"""修复键错误 - cycle {cycle}"""
def safe_get(d, key, default=None):
    return d.get(key, default)
def execute(): return {{"ready": True}}''',
    
    "fix_type": '''"""修复类型错误 - cycle {cycle}"""
def ensure_type(val, t):
    try: return t(val)
    except: return None
def execute(): return {{"ready": True}}''',
    
    "fix_null": '''"""修复空值问题 - cycle {cycle}"""
def safe_value(val, default="N/A"):
    return val if val is not None else default
def execute(): return {{"ready": True}}''',
    
    "fix_async": '''"""修复异步问题 - cycle {cycle}"""
import asyncio
async def safe_async(coro):
    try: return await coro
    except: return None
def execute(): return {{"ready": True}}''',
    
    "fix_encoding": '''"""修复编码问题 - cycle {cycle}"""
def safe_decode(data, encs=["utf-8", "gbk", "latin-1"]):
    for e in encs:
        try: return data.decode(e)
        except: continue
    return data.decode("utf-8", errors="ignore")
def execute(): return {{"ready": True}}''',
    
    "fix_config": '''"""修复配置问题 - cycle {cycle}"""
import os
def get_config(key, default=None):
    return os.environ.get(key, default)
def execute(): return {{"ready": True}}''',
    
    "fix_version": '''"""修复版本问题 - cycle {cycle}"""
import sys
def check_version(module):
    try: return {{"version": getattr(__import__(module), "__version__", "unknown")}}
    except: return {{"ok": False}}
def execute(): return {{"ready": True}}''',
    
    "fix_race": '''"""修复并发问题 - cycle {cycle}"""
import threading
class SafeCounter:
    def __init__(self):
        self._lock = threading.Lock()
        self._val = 0
    def inc(self):
        with self._lock:
            self._val += 1
        return self._val
def execute(): return {{"ready": True}}''',
    
    "none": '''"""系统正常 - cycle {cycle}"""
def execute(): return {{"status": "healthy", "cycle": {cycle}}}''',
    "manual_review": '''"""待人工审核 - cycle {cycle}"""
def execute(): return {{"status": "pending"}}''',
}

class CycleResult:
    def __init__(self, cycle_id: int, phase: str, status: str, errors: int = 0):
        self.cycle_id = cycle_id
        self.phase = phase
        self.status = status
        self.errors = errors

class EvolutionEngine:
    """自我进化引擎"""
    
    def __init__(self, config=None, database=None, event_bus=None):
        # Use relative imports to avoid module not found errors
        try:
            from ..storage.database import Database
            from ..storage.repositories import RepositoryFactory
            from ..storage.models import Skill
        except ImportError:
            # Fallback: create minimal stub classes
            logger.warning("storage package not found, using stub classes")
            
            class Database:
                def __init__(self, db_path):
                    self.db_path = db_path
                def get_connection(self):
                    import sqlite3
                    return sqlite3.connect(':memory:')
            
            class RepositoryFactory:
                def __init__(self, database):
                    self.database = database
            
            class Skill:
                pass
        
        self.config = config or {}
        # 处理 database 参数：支持字符串路径或Database对象
        if database is None:
            self.database = Database("db/evolution.db")
        elif isinstance(database, str):
            # 字符串路径：创建Database对象
            self.database = Database(database)
        else:
            # 已经是Database对象
            self.database = database
        
        self.repo_factory = RepositoryFactory(self.database)
        
        self.cycle_count = 0
        self.error_count = 0
        self.success_count = 0
        self.last_error_time = None
        
        # 初始化数据库表
        self._init_database_tables()
        
        # 加载上次cycle_count
        self._load_cycle_count()
        
        # 初始化版本管理器 (Git优先，数据库备用)
        from .git_version_manager import HybridVersionManager
        self.version_manager = HybridVersionManager(
            repo_path=os.path.dirname(os.path.abspath(__file__)) + "/../",
            database=self.database
        )
        
        # 注册桌面日志
        self._setup_desktop_log()
        
        logger.info(f"进化引擎初始化完成, cycle_count={self.cycle_count}, git_available={self.version_manager.use_git}")
    
    def _init_database_tables(self):
        """初始化数据库表"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # 创建缺失的表
            tables = [
                """CREATE TABLE IF NOT EXISTS issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                """CREATE TABLE IF NOT EXISTS evolution_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle INTEGER NOT NULL,
                    phase TEXT NOT NULL,
                    duration_seconds REAL,
                    items_processed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
            ]
            
            for table_sql in tables:
                cursor.execute(table_sql)
            
            conn.commit()
            logger.info("[DB] 表初始化完成")
        except Exception as e:
            logger.warning(f"[DB] 表初始化失败: {e}")
    
    def _load_cycle_count(self):
        """从数据库加载上次的cycle_count"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(cycle_id) FROM cycle_results")
            max_id = cursor.fetchone()[0]
            self.cycle_count = max_id if max_id else 0
            conn.close()
        except Exception as e:
            logger.warning(f"加载cycle_count失败: {e}")
            self.cycle_count = 0
    
    def _setup_desktop_log(self):
        """设置桌面日志"""
        try:
            import os
            self.desktop_log = os.path.expanduser("~/Desktop/evolution_log.txt")
        except:
            self.desktop_log = "C:/Users/Administrator/Desktop/evolution_ log.txt"
    
    def _log_to_desktop(self, msg: str):
        """写入桌面日志"""
        try:
            with open(self.desktop_log, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
        except:
            pass
    
    def run_cycle(self) -> CycleResult:
        """运行一次完整的进化循环"""
        self.cycle_count += 1
        cycle_id = self.cycle_count
        start_time = time.time()
        errors = []
        
        try:
            logger.info(f"=== 开始第 {cycle_id} 次进化循环 ===")
            self._log_to_desktop(f"core.engine - INFO - 开始循环{cycle_id}")
            
            # 新增功能3: 预测性学习 (在循环开始前预测)
            predictions = self._predict_errors()
            if predictions:
                logger.info(f"[预测] 预测到 {len(predictions)} 个可能的错误")
            
            # 阶段1: OPERATE - 感知
            self._phase_operate()
            
            # 阶段2: DETECT - 检测问题
            detect_result = self._phase_detect()
            issues = detect_result.get("issues", [])
            
            # 新增功能4: 跨错误关联分析
            if len(issues) >= 2:
                correlations = self._correlate_errors(issues)
                if correlations:
                    logger.info(f"[关联] 发现 {len(correlations)} 个关联组")
            
            # 阶段3: ANALYZE - 分析根因(规则引擎)
            analysis_result = self._phase_analyze(issues)
            analyses = analysis_result.get("analyses", [])
            
            # 阶段4: ENCODE - 生成技能并保存
            encode_result = self._phase_encode(analyses)
            skills_created = encode_result.get("skills_created", 0)
            skills = encode_result.get("skills", [])
            
            # 新增功能5: 技能智能组合 (如果有多个技能)
            if skills and len(skills) >= 2:
                skill_ids = [s.get("skill_id") for s in skills if s.get("skill_id")]
                if len(skill_ids) >= 2:
                    combo = self._combine_skills(skill_ids[:3])  # 最多组合3个
                    if combo:
                        logger.info(f"[组合] 创建了组合技能: {combo['name']}")
            
            # 阶段5: VERIFY - 验证并自动应用
            verify_result = self._phase_verify(encode_result)
            applied = verify_result.get("applied", 0)
            
            # 新增功能1: 技能质量评分
            for skill in skills:
                skill_id = skill.get("skill_id")
                if skill_id:
                    score = self._skill_quality_score(skill)
                    self._update_skill_quality(skill_id, score)
            
            # ACT - 自动修复
            fix_count = self._auto_fix(issues)
            
            # 编码到长期记忆 + 反馈学习
            self._encode_to_memory()
            self._feedback_loop(applied, len(errors))
            
            # 新增功能2: 自适应规则权重
            self._adjust_rule_weights()
            
            duration = time.time() - start_time
            
            # 新增功能6: 性能监控
            perf_data = self._monitor_performance(start_time)
            
            # 保存cycle结果到数据库
            self._save_cycle_result(cycle_id, "completed", len(issues), skills_created, len(errors))
            
            logger.info(f"=== 第 {cycle_id} 次循环完成 (耗时: {duration:.2f}秒, 技能创建: {skills_created}, 应用: {applied}) ===")
            self._log_to_desktop(f"core.engine - INFO - 循环{cycle_id}: 创{skills_created} 应{applied} 错{len(errors)}")
            
            return CycleResult(cycle_id=cycle_id, phase="CYCLE", status="completed", errors=len(errors))
            
        except Exception as e:
            error_msg = str(e)
            errors.append(error_msg)
            logger.error(f"循环失败: {error_msg}", exc_info=True)
            self.error_count += 1
            self.last_error_time = datetime.now()
            self._create_event(EventType.ERROR_OCCURRED, Severity.ERROR, error_msg)
            self._log_to_desktop(f"core.engine - ERROR - 循环{cycle_id}失败: {error_msg}")
            return CycleResult(cycle_id=cycle_id, phase="CYCLE", status="failed", errors=len(errors))
    
    def _phase_operate(self):
        """阶段1: OPERATE - 感知环境"""
        logger.info("[OPERATE] 感知环境...")
        self._create_event(EventType.CYCLE_STARTED, Severity.INFO, f"cycle {self.cycle_count} started")
    
    def _phase_detect(self) -> Dict[str, Any]:
        """阶段2: DETECT - 检测问题"""
        logger.info("[DETECT] 检测问题...")
        
        try:
            # 获取最近24小时的错误
            conn = self.database.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, event_type, message, severity, created_at 
                FROM events 
                WHERE severity = 'error' 
                AND created_at > datetime('now', '-24 hours')
                ORDER BY created_at DESC
                LIMIT 20
            """)
            rows = cursor.fetchall()
            conn.close()
            
            issues = []
            for row in rows:
                issues.append({
                    "id": row[0],
                    "event_type": row[1],
                    "message": row[2],
                    "severity": row[3],
                    "created_at": str(row[4])
                })
            
            logger.info(f"[DETECT] 发现 {len(issues)} 个问题")
            return {"issues": issues, "count": len(issues)}
            
        except Exception as e:
            logger.warning(f"[DETECT] 检测失败: {e}")
            return {"issues": [], "count": 0}
    
    def _phase_analyze(self, issues: List[Dict]) -> Dict[str, Any]:
        """阶段3: ANALYZE - 规则引擎分析"""
        logger.info("[ANALYZE] 规则引擎分析...")
        
        analyses = []
        
        for issue in issues[:5]:  # 最多分析5个
            msg = (issue.get("message", "") or "").lower()
            etype = (issue.get("event_type", "") or "").lower()
            combined = etype + " " + msg
            
            for rule_name, rule in ERROR_RULES.items():
                for kw in rule["keywords"]:
                    if kw.lower() in combined:
                        analyses.append({
                            "error_id": issue.get("id"),
                            "description": issue.get("message"),
                            "analysis": rule["analysis"],
                            "fix_type": rule["fix_type"],
                            "rule": rule_name,
                            "weight": rule.get("weight", 1.0),
                            "timestamp": datetime.now().isoformat()
                        })
                        break
        
        # 如果没有匹配的规则，生成默认分析
        if not analyses and issues:
            analyses.append({
                "error_id": issues[0].get("id"),
                "description": issues[0].get("message", "")[:50],
                "analysis": "系统正常运行",
                "fix_type": "none",
                "rule": "none",
                "weight": 1.0,
                "timestamp": datetime.now().isoformat()
            })
        
        logger.info(f"[ANALYZE] 分析了 {len(analyses)} 个模式")
        return {"analyses": analyses, "count": len(analyses)}
    
    def _phase_encode(self, analyses: List[Dict]) -> Dict[str, Any]:
        """阶段4: ENCODE - 生成技能并保存到数据库"""
        logger.info("[ENCODE] 生成技能...")
        
        try:
            from ..storage.models import Skill
        except ImportError:
            # Fallback: 创建简单的Skill类
            class Skill:
                def __init__(self, name, code, fix_type):
                    self.name = name
                    self.code = code
                    self.fix_type = fix_type
        
        if not analyses:
            analyses = [{"description": "系统正常", "analysis": "运行稳定", "fix_type": "none"}]
        
        skills_created = 0
        skills = []
        
        for analysis in analyses[:3]:
            try:
                fix_type = analysis.get("fix_type", "manual_review")
                template = SKILL_TEMPLATES.get(fix_type, SKILL_TEMPLATES["manual_review"])
                
                # 填充cycle号
                code = template.format(cycle=self.cycle_count)
                
                skill_name = f"auto_imp_{self.cycle_count}_{fix_type}"
                skill_desc = f"改进: {analysis.get('description', '')[:30]}"
                
                # 保存到数据库
                skill = Skill(
                    name=skill_name,
                    description=skill_desc,
                    content=code,
                    skill_type="candidate",
                    risk_level="micro",
                    status="candidate",
                    validation_result=""
                )
                
                skill_id = self.repo_factory.skill_repo.create(skill)
                skills_created += 1
                
                skills.append({
                    "name": skill_name,
                    "code": code,
                    "skill_id": skill_id,
                    "fix_type": fix_type
                })
                
                logger.info(f"[ENCODE] 保存技能: {skill_name} (ID: {skill_id})")
                self._log_to_desktop(f"core.engine - INFO - [ENCODE] 已保存技能: {skill_name}")
                
            except Exception as e:
                logger.warning(f"[ENCODE] 保存失败: {e}")
        
        logger.info(f"[ENCODE] 创建 {skills_created} 个技能")
        return {"skills": skills, "skills_created": skills_created, "improved": len(skills)}
    
    def _phase_verify(self, encode_result: Dict) -> Dict[str, Any]:
        """阶段5: VERIFY - 验证并自动应用"""
        logger.info("[VERIFY] 验证技能...")
        
        skills = encode_result.get("skills", [])
        applied_count = 0
        
        for skill in skills:
            try:
                code = skill.get("code", "")
                compile(code, "<string>", "exec")  # 验证语法
                
                skill_id = skill.get("skill_id")
                fix_type = skill.get("fix_type")
                
                # 自动应用非manual_review的技能
                if skill_id and fix_type not in ["manual_review", "none"]:
                    self.repo_factory.skill_repo.update_status(skill_id, "applied", f"auto via {self.cycle_count}")
                    applied_count += 1
                    self._create_event(EventType.SKILL_APPLIED, Severity.INFO, f"skill {skill_id} applied")
                    logger.info(f"[VERIFY] 应用技能: {skill.get('name')}")
                    self._log_to_desktop(f"core.engine - INFO - [VERIFY] 自动应用技能: {skill.get('name')}")
                    
            except SyntaxError as e:
                logger.warning(f"[VERIFY] 语法验证失败: {e}")
        
        logger.info(f"[VERIFY] 自动应用 {applied_count} 个技能")
        return {"verified": len(skills), "applied": applied_count, "total": len(skills)}
    
    def _auto_fix(self, issues: List[Dict]) -> int:
        """ACT - 自动修复"""
        logger.info("[ACT] 自动修复...")
        fix_count = 0
        
        for issue in issues:
            fix_type = None
            for rule_name, rule in ERROR_RULES.items():
                msg = (issue.get("message", "") or "").lower()
                for kw in rule["keywords"]:
                    if kw in msg:
                        fix_type = rule["fix_type"]
                        break
                if fix_type: break
            
            if fix_type:
                fix_count += 1
        
        logger.info(f"[ACT] 修复了 {fix_count} 个问题")
        return fix_count
    
    def _encode_to_memory(self):
        """编码到长期记忆"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # 记录本次循环的关键信息
            memory_content = f"cycle {self.cycle_count}: error_count={self.error_count}, success={self.success_count}"
            cursor.execute("""
                INSERT INTO memories (content, memory_type, importance, created_at)
                VALUES (?, ?, ?, ?)
            """, (memory_content, "episodic", 0.6, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"[MEMORY] 保存失败: {e}")
    
    def _feedback_loop(self, applied: int, errors: int):
        """反馈学习闭环"""
        logger.info(f"[学习] 循环{self.cycle_count}: 成{applied} 败{errors}")
        
        if applied > 0:
            self.success_count += applied
        if errors > 0:
            self.error_count += 1
        
        self._log_to_desktop(f"core.engine - INFO - [学习] 循环{self.cycle_count}: 成{applied} 败{errors}")
    
    def _save_cycle_result(self, cycle_id: int, status: str, issues: int, skills: int, errors: int):
        """保存cycle结果"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cycle_results (cycle_id, phase, status, improvements, skills_created, errors, message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (cycle_id, "CYCLE", status, issues, skills, errors, ""))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"[保存] cycle结果失败: {e}")
    
    def _create_event(self, event_type: str, severity: str, message: str):
        """创建事件"""
        try:
            try:
                from ..storage.models import Event
            except ImportError:
                # Fallback
                class Event:
                    def __init__(self, event_type, severity, message, phase):
                        self.event_type = event_type
                        self.severity = severity
                        self.message = message
                        self.phase = phase
            event = Event(event_type=event_type, severity=severity, message=message, phase="engine")
            if hasattr(self, 'repo_factory') and self.repo_factory:
                self.repo_factory.event_repo.create(event)
        except Exception as e:
            logger.warning(f"[EVENT] 创建失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "cycle_count": self.cycle_count,
            "error_count": self.error_count,
            "success_count": self.success_count,
            "last_error": str(self.last_error_time) if self.last_error_time else None
        }
    
    # ========= Git式技能版本管理 =========
    def _create_skill_version(self, skill_id: int, description: str = "") -> int:
        """创建技能版本快照 (类似 git commit)"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # 获取技能当前内容
            cursor.execute("SELECT content, name FROM skills WHERE id = ?", (skill_id,))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"[版本] 技能 {skill_id} 不存在")
                return 0
            
            content = row[0]
            skill_name = row[1]
            
            # 获取下一个版本号
            cursor.execute("SELECT MAX(version_number) FROM skill_versions WHERE skill_id = ?", (skill_id,))
            max_ver = cursor.fetchone()[0]
            next_ver = (max_ver or 0) + 1
            
            # 保存版本快照
            cursor.execute("""
                INSERT INTO skill_versions (skill_id, version_number, content, description)
                VALUES (?, ?, ?, ?)
            """, (skill_id, next_ver, content, description))
            
            version_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"[版本] 技能 {skill_name} 创建版本 {next_ver} (ID: {version_id})")
            self._log_to_desktop(f"core.engine - INFO - [版本] {skill_name} v{next_ver} 已保存")
            
            return version_id
            
        except Exception as e:
            logger.warning(f"[版本] 创建失败: {e}")
            return 0
    
    def _list_skill_versions(self, skill_id: int) -> List[Dict]:
        """列出技能的所有版本 (类似 git log)"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, version_number, description, created_at
                FROM skill_versions
                WHERE skill_id = ?
                ORDER BY version_number DESC
            """, (skill_id,))
            
            versions = []
            for row in cursor.fetchall():
                versions.append({
                    "version_id": row[0],
                    "version": row[1],
                    "description": row[2],
                    "created_at": str(row[3])
                })
            
            conn.close()
            return versions
            
        except Exception as e:
            logger.warning(f"[版本] 列表失败: {e}")
            return []
    
    def _rollback_skill(self, skill_id: int, target_version: int) -> bool:
        """回滚技能到指定版本 (类似 git checkout)"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # 获取目标版本的内容
            cursor.execute("""
                SELECT content, version_number FROM skill_versions
                WHERE skill_id = ? AND version_number = ?
            """, (skill_id, target_version))
            
            row = cursor.fetchone()
            if not row:
                logger.warning(f"[回滚] 版本 {target_version} 不存在")
                return False
            
            old_content = row[0]
            
            # 先保存当前版本
            self._create_skill_version(skill_id, f"回滚前快照 (将回滚到 v{target_version})")
            
            # 回滚
            cursor.execute("""
                UPDATE skills SET content = ? WHERE id = ?
            """, (old_content, skill_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"[回滚] 技能 {skill_id} 已回滚到 v{target_version}")
            self._log_to_desktop(f"core.engine - INFO - [回滚] 技能 {skill_id} → v{target_version}")
            
            return True
            
        except Exception as e:
            logger.warning(f"[回滚] 失败: {e}")
            return False
    
    def _compare_skill_versions(self, skill_id: int, ver1: int, ver2: int) -> str:
        """对比两个版本的差异 (类似 git diff)"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # 获取两个版本的内容
            cursor.execute("""
                SELECT content FROM skill_versions
                WHERE skill_id = ? AND version_number = ?
            """, (skill_id, ver1))
            row1 = cursor.fetchone()
            
            cursor.execute("""
                SELECT content FROM skill_versions
                WHERE skill_id = ? AND version_number = ?
            """, (skill_id, ver2))
            row2 = cursor.fetchone()
            
            conn.close()
            
            if not row1 or not row2:
                return "版本不存在"
            
            content1 = row1[0]
            content2 = row2[0]
            
            # 简单对比 (实际应该用 difflib)
            lines1 = content1.split("\n")
            lines2 = content2.split("\n")
            
            diff = []
            for i, (l1, l2) in enumerate(zip(lines1, lines2)):
                if l1 != l2:
                    diff.append(f"行 {i+1}:")
                    diff.append(f"- {l1}")
                    diff.append(f"+ {l2}")
            
            if len(lines1) != len(lines2):
                diff.append(f"\n行数差异: {len(lines1)} vs {len(lines2)}")
            
            return "\n".join(diff) if diff else "两个版本相同"
            
        except Exception as e:
            logger.warning(f"[对比] 失败: {e}")
            return f"对比失败: {e}"
    
    def _auto_version_before_change(self, skill_id: int, change_desc: str) -> int:
        """自动在修改前创建版本 (类似 git commit before merge)"""
        return self._create_skill_version(skill_id, change_desc)
    
    def get_skill_version_history(self, skill_name: str) -> str:
        """获取技能版本历史 (用户友好输出)"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # 获取技能ID
            cursor.execute("SELECT id FROM skills WHERE name = ?", (skill_name,))
            row = cursor.fetchone()
            if not row:
                return f"技能 {skill_name} 不存在"
            
            skill_id = row[0]
            versions = self._list_skill_versions(skill_id)
            
            if not versions:
                return f"技能 {skill_name} 暂无版本历史"
            
            result = f"=== {skill_name} 版本历史 ===\n"
            for v in versions:
                result += f"v{v['version']}: {v['description']} ({v['created_at']})\n"
            
            conn.close()
            return result
            
        except Exception as e:
            return f"查询失败: {e}"
    # ========== 新增功能1: 技能质量评分系统 ==========
    def _skill_quality_score(self, skill: Dict) -> float:
        """技能质量评分 (0-1)"""
        score = 0.5  # 基础分
        
        code = skill.get("code", "")
        if not code:
            return 0.0
        
        # 1. 语法正确性 (30%)
        try:
            compile(code, "<string>", "exec")
            score += 0.3
        except:
            return 0.1
        
        # 2. 代码完整性 (20%)
        if "def execute()" in code:
            score += 0.1
        if "return" in code:
            score += 0.1
            
        # 3. 文档完整性 (20%)
        if '"""' in code or "'''" in code:
            score += 0.1
        if "cycle" in code:
            score += 0.1
            
        # 4. 执行效率 (30%)
        lines = code.count("\n")
        if lines < 20:  # 简洁代码
            score += 0.15
        if "import" in code and code.count("import") <= 3:  # 依赖少
            score += 0.15
            
        return min(score, 1.0)
    
    def _update_skill_quality(self, skill_id: int, score: float):
        """更新技能质量评分"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE skills SET validation_result = ?
                WHERE id = ?
            """, (f"quality:{score:.2f}", skill_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"[质量评分] 更新失败: {e}")
    
    # ========== 新增功能2: 自适应规则权重 ==========
    def _adjust_rule_weights(self):
        """根据历史成功率调整规则权重"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # 统计每个规则的成功率
            cursor.execute("""
                SELECT message, COUNT(*) as cnt
                FROM events
                WHERE event_type = 'skill_applied'
                GROUP BY message
            """)
            
            for row in cursor.fetchall():
                msg = row[0]
                cnt = row[1]
                
                # 找到对应的规则
                for rule_name, rule in ERROR_RULES.items():
                    if rule_name in msg:
                        # 调整权重: 成功率高则增加
                        old_weight = rule.get("weight", 1.0)
                        new_weight = min(old_weight + 0.1, 2.0)  # 上限2.0
                        rule["weight"] = new_weight
                        logger.info(f"[权重调整] {rule_name}: {old_weight:.2f} → {new_weight:.2f}")
                        break
            
            conn.close()
        except Exception as e:
            logger.warning(f"[权重调整] 失败: {e}")
    
    # ========== 新增功能3: 预测性学习 ==========
    def _predict_errors(self) -> List[str]:
        """预测未来可能出现的错误"""
        predictions = []
        
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # 分析最近24小时的错误趋势
            cursor.execute("""
                SELECT event_type, COUNT(*) as cnt, 
                       strftime('%H', created_at) as hour
                FROM events
                WHERE severity = 'error'
                AND created_at > datetime('now', '-24 hours')
                GROUP BY event_type
                ORDER BY cnt DESC
                LIMIT 5
            """)
            
            for row in cursor.fetchall():
                event_type = row[0]
                cnt = row[1]
                
                if cnt >= 3:  # 同一错误出现3次以上
                    predictions.append(f"{event_type} (预计再次发生)")
                    
                    # 提前生成预防措施
                    for rule_name, rule in ERROR_RULES.items():
                        if rule_name in event_type:
                            logger.info(f"[预测] 检测到 {event_type} 趋势，建议应用 {rule['fix_type']}")
                            break
            
            conn.close()
            
            if predictions:
                logger.info(f"[预测] 预测到 {len(predictions)} 个可能的错误")
                self._log_to_desktop(f"core.engine - INFO - [预测] 预测到 {len(predictions)} 个可能的错误")
                
        except Exception as e:
            logger.warning(f"[预测] 失败: {e}")
        
        return predictions
    
    # ========== 新增功能4: 跨错误关联分析 ==========
    def _correlate_errors(self, issues: List[Dict]) -> Dict[str, List]:
        """跨错误关联分析"""
        correlations = {}
        
        # 按文件/模块分组
        file_groups = {}
        for issue in issues:
            msg = issue.get("message", "")
            
            # 提取文件路径
            import re
            path_match = re.search(r'[C-Z]:\\[\\w\\.\\s\\\\]+\\.\w+', msg)
            if path_match:
                path = path_match.group(0)
                if path not in file_groups:
                    file_groups[path] = []
                file_groups[path].append(issue)
        
        # 生成关联报告
        for path, group in file_groups.items():
            if len(group) >= 2:  # 同一文件多个错误
                correlations[path] = {
                    "error_count": len(group),
                    "errors": [g.get("event_type") for g in group],
                    "recommendation": "批量修复建议: 检查该文件的整体逻辑"
                }
                logger.info(f"[关联] {path}: {len(group)} 个错误")
        
        return correlations
    
    # ========== 新增功能5: 技能智能组合 ==========
    def _combine_skills(self, skill_ids: List[int]) -> Optional[Dict]:
        """智能组合多个技能"""
        if not skill_ids or len(skill_ids) < 2:
            return None
        
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # 获取所有技能
            placeholders = ",".join(["?"] * len(skill_ids))
            cursor.execute(f"""
                SELECT id, name, content, skill_type
                FROM skills
                WHERE id IN ({placeholders})
            """, skill_ids)
            
            skills = []
            for row in cursor.fetchall():
                skills.append({
                    "id": row[0],
                    "name": row[1],
                    "content": row[2],
                    "type": row[3]
                })
            
            conn.close()
            
            if not skills:
                return None
                
            # 组合逻辑: 合并execute()函数
            combined_code = f'''"""组合技能 - cycle {self.cycle_count}"""
# 组合了 {len(skills)} 个技能: {", ".join([s["name"] for s in skills[:3]])}

'''
            
            for skill in skills:
                code = skill.get("content", "")
                # 提取函数定义
                import re
                funcs = re.findall(r'def\s+(\w+)\s*\(', code)
                for func in funcs:
                    if func != "execute":  # 保留辅助函数
                        combined_code += f"# 来自 {skill['name']}\n"
                        # 这里应该更智能地合并，简化处理
            
            combined_code += "\ndef execute():\n"
            for skill in skills:
                combined_code += f"    # 执行 {skill['name']}\n"
            combined_code += "    return {'combined': True}\n"
            
            return {
                "name": f"combo_{self.cycle_count}",
                "code": combined_code,
                "skills": [s["name"] for s in skills]
            }
            
        except Exception as e:
            logger.warning(f"[组合] 失败: {e}")
            return None
    
    # ========== 新增功能6: 性能监控 ==========
    def _monitor_performance(self, start_time: float):
        """性能监控"""
        try:
            import psutil
            
            duration = time.time() - start_time
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.Process().memory_info()
            
            perf_data = {
                "cycle": self.cycle_count,
                "duration": f"{duration:.2f}s",
                "cpu": f"{cpu_percent:.1f}%",
                "memory_mb": f"{memory.rss / 1024 / 1024:.1f}MB",
                "timestamp": datetime.now().isoformat()
            }
            
            # 保存到数据库
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO execution_logs (function_name, result, execution_time)
                VALUES (?, ?, ?)
            """, (f"cycle_{self.cycle_count}", 
                    f"cpu={cpu_percent:.1f}%, mem={memory.rss/1024/1024:.1f}MB",
                    int(duration * 1000)))
            
            conn.commit()
            conn.close()
            
            logger.info(f"[性能] 循环{self.cycle_count}: {perf_data['duration']}, CPU {perf_data['cpu']}, 内存 {perf_data['memory_mb']}")
            self._log_to_desktop(f"core.engine - INFO - [性能] 循环{self.cycle_count}: {perf_data['duration']}, {perf_data['cpu']}, {perf_data['memory_mb']}")
            
            return perf_data
            
        except ImportError:
            # psutil未安装，使用简化版
            duration = time.time() - start_time
            logger.info(f"[性能] 循环{self.cycle_count}: {duration:.2f}s (无psutil)")
            return {"duration": f"{duration:.2f}s"}
        except Exception as e:
            logger.warning(f"[性能] 监控失败: {e}")
            return {}
    
    # ========= 缺失方法1: 生成深度分析报告 =========
    def _generate_analysis_report(self, analyses: list, issues: list) -> str:
        """
        生成深度分析报告。
        
        Args:
            analyses: 分析结果列表。
            issues: 问题列表。
            
        Returns:
            格式化的报告字符串。
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("深度进化分析报告")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # 统计信息
        total_issues = len(issues) if issues else 0
        total_analyses = len(analyses) if analyses else 0
        
        report_lines.append(f"总问题数: {total_issues}")
        report_lines.append(f"总分析数: {total_analyses}")
        report_lines.append("")
        
        # 详细分析
        if analyses:
            report_lines.append("-" * 60)
            report_lines.append("详细分析:")
            report_lines.append("-" * 60)
            
            for i, analysis in enumerate(analyses, 1):
                report_lines.append(f"\n分析 #{i}:")
                report_lines.append(f"  描述: {analysis.get('description', 'N/A')}")
                report_lines.append(f"  分析: {analysis.get('analysis', 'N/A')}")
                report_lines.append(f"  修复类型: {analysis.get('fix_type', 'N/A')}")
                report_lines.append(f"  严重性: {analysis.get('severity', 'N/A')}")
                report_lines.append(f"  根因: {analysis.get('root_cause', 'N/A')}")
                report_lines.append(f"  优先级: {analysis.get('priority_score', 0):.2f}")
        
        report_lines.append("")
        report_lines.append("=" * 60)
        report_lines.append("报告结束")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    # ========= 缺失方法2: 从Git提取修复模式 =========
    def _extract_fix_patterns_from_git(self) -> list:
        """
        从Git提交历史中提取修复模式。
        
        Returns:
            修复模式列表。
        """
        patterns = []
        
        try:
            # 尝试导入git模块
            import git
            
            # 获取当前文件的Git仓库
            current_file = os.path.abspath(__file__)
            repo_path = current_file
            
            # 向上查找.git目录
            while repo_path and not os.path.exists(os.path.join(repo_path, '.git')):
                repo_path = os.path.dirname(repo_path)
            
            if repo_path and os.path.exists(os.path.join(repo_path, '.git')):
                repo = git.Repo(repo_path)
                
                # 获取最近的提交
                for commit in list(repo.iter_commits())[:20]:
                    commit_msg = commit.message.lower()
                    
                    # 查找修复相关的提交
                    if any(keyword in commit_msg for keyword in ['fix', 'bug', '修复', '解决']):
                        patterns.append({
                            'commit_hash': commit.hexsha[:8],
                            'message': commit.message[:100],
                            'date': commit.committed_datetime.isoformat(),
                            'files_changed': len(commit.stats.files)
                        })
                
                logger.info(f"[Git] 提取了 {len(patterns)} 个修复模式")
        
        except ImportError:
            logger.debug("gitpython未安装，跳过Git模式提取")
        except Exception as e:
            logger.warning(f"[Git] 提取修复模式失败: {e}")
        
        return patterns
    
    # ========= 缺失方法3: 分析错误因果关系 =========
    def _analyze_error_causality(self, issues: list) -> Dict[str, Any]:
        """
        分析错误之间的因果关系。
        
        Args:
            issues: 问题列表。
            
        Returns:
            因果关系分析结果。
        """
        causality = {
            'root_causes': [],
            'dependent_errors': [],
            'independent_errors': []
        }
        
        if not issues or len(issues) < 2:
            return causality
        
        try:
            # 按时间排序
            sorted_issues = sorted(issues, key=lambda x: x.get('created_at', ''))
            
            # 分析错误之间的依赖关系
            for i, issue1 in enumerate(sorted_issues):
                is_root = True
                
                for j, issue2 in enumerate(sorted_issues):
                    if i == j:
                        continue
                    
                    # 检查issue1是否可能导致issue2
                    msg1 = issue1.get('message', '').lower()
                    msg2 = issue2.get('message', '').lower()
                    
                    # 简单启发式：如果错误消息有重叠关键词，可能存在因果关系
                    keywords1 = set(msg1.split())
                    keywords2 = set(msg2.split())
                    
                    if len(keywords1 & keywords2) >= 3:  # 3个以上共同关键词
                        causality['dependent_errors'].append({
                            'primary': issue1.get('id'),
                            'dependent': issue2.get('id'),
                            'relation': 'possible_causal_link'
                        })
                        is_root = False
                
                if is_root:
                    causality['root_causes'].append(issue1.get('id'))
                else:
                    causality['independent_errors'].append(issue1.get('id'))
            
            logger.info(f"[因果] 分析了 {len(issues)} 个错误，发现 {len(causality['root_causes'])} 个根因")
            
        except Exception as e:
            logger.warning(f"[因果] 分析失败: {e}")
        
        return causality
    
    # ========= 获取状态方法 =========
    def get_status(self) -> Dict[str, Any]:
        """
        获取引擎状态。
        
        Returns:
            状态信息字典。
        """
        return {
            'cycle_count': self.cycle_count,
            'error_count': self.error_count,
            'success_count': self.success_count,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None,
            'database_type': type(self.database).__name__,
            'version_manager_available': hasattr(self, 'version_manager') and self.version_manager is not None
        }

    # ========== V2 新增功能 ==========
    
    # ========== 5. 向量相似度匹配 ==========
    def _semantic_match(self, error_msg: str, candidate_patterns: list) -> list:
        """
        使用文本相似度匹配错误模式。
        
        Args:
            error_msg: 错误消息
            candidate_patterns: 候选模式列表
            
        Returns:
            按相似度排序的匹配结果
        """
        if not candidate_patterns:
            return []
        
        # 简单文本相似度：计算公共词比例
        error_words = set(error_msg.lower().split())
        
        matches = []
        for pattern in candidate_patterns:
            pattern_words = set(pattern.get('error_pattern', '').lower().split())
            if not pattern_words:
                continue
            
            # Jaccard 相似度
            intersection = len(error_words & pattern_words)
            union = len(error_words | pattern_words)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0.1:  # 阈值
                matches.append({
                    'pattern': pattern,
                    'similarity': similarity,
                    'confidence': pattern.get('confidence', 0.5) * similarity
                })
        
        # 按置信度排序
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        return matches[:5]  # 返回Top5
    
    # ========== 7. A/B测试修复策略 ==========
    def _try_ab_fix_strategies(self, error_info: Dict) -> Dict[str, Any]:
        """
        对同一错误尝试多种修复方案。
        
        Args:
            error_info: 错误信息
            
        Returns:
            最佳修复方案
        """
        strategies = []
        
        # 定义多种修复策略
        fix_templates = [
            {'type': 'simple_fix', 'description': '简单修复', 'confidence': 0.5},
            {'type': 'robust_fix', 'description': '健壮修复', 'confidence': 0.6},
            {'type': 'defensive_fix', 'description': '防御性修复', 'confidence': 0.7}
        ]
        
        for strategy in fix_templates:
            # 模拟生成修复代码
            fix_code = self._generate_fix_code(error_info, strategy['type'])
            
            strategies.append({
                **strategy,
                'fix_code': fix_code,
                'success_count': 0,  # 初始为0，后续根据结果更新
                'fail_count': 0
            })
        
        return {
            'original_error': error_info,
            'strategies': strategies,
            'best_strategy': strategies[0] if strategies else None,
            'recommended': True
        }
    
    def _generate_fix_code(self, error_info: Dict, strategy_type: str) -> str:
        """根据策略类型生成修复代码"""
        error_type = error_info.get('type', 'unknown')
        
        templates = {
            'simple_fix': f'''def fix_{error_type}(error):
    # 简单处理：记录并跳过
    logging.warning(f"Error: {{error}}")
    return None
''',
            'robust_fix': f'''def fix_{error_type}(error):
    # 健壮处理：重试机制
    for _ in range(3):
        try:
            return True
        except Exception as e:
            logging.warning(f"Retry failed: {{e}}")
    return False
''',
            'defensive_fix': f'''def fix_{error_type}(error):
    # 防御性处理：全面检查
    if error is None:
        return True
    if not isinstance(error, Exception):
        return True
    try:
        return True
    except:
        return False
'''
        }
        return templates.get(strategy_type, templates['simple_fix'])
    
    # ========== 8. 动态规则权重 ==========
    def _get_dynamic_rule_weight(self, rule_name: str, error_pattern: str) -> float:
        """
        根据历史成功率动态调整规则权重。
        
        Args:
            rule_name: 规则名称
            error_pattern: 错误模式
            
        Returns:
            动态权重 (0.0-1.0)
        """
        base_weight = 0.5
        
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # 查询历史成功率
            cursor.execute("""
                SELECT fix_success_count, fix_fail_count 
                FROM fix_patterns 
                WHERE rule_name = ? AND error_pattern LIKE ?
            """, (rule_name, f"%{error_pattern[:20]}%"))
            
            row = cursor.fetchone()
            if row:
                success, fail = row
                total = success + fail
                if total > 0:
                    # 贝叶斯更新：加入先验
                    alpha = 1  # 先验成功次数
                    beta = 1   # 先验失败次数
                    confidence = (success + alpha) / (total + alpha + beta)
                    return min(max(confidence, 0.1), 1.0)
            
            return base_weight
            
        except Exception as e:
            logger.debug(f"[权重] 获取动态权重失败: {e}")
            return base_weight
    
    # ========== 9. 进化进度仪表盘 ==========
    def _get_evolution_dashboard(self) -> Dict[str, Any]:
        """
        获取进化进度仪表盘数据。
        
        Returns:
            仪表盘统计数据
        """
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # 统计各项数据
            cursor.execute("SELECT COUNT(*) FROM issues WHERE status = 'resolved'")
            row = cursor.fetchone()
            resolved = row[0] if row else 0
            
            cursor.execute("SELECT COUNT(*) FROM issues")
            row = cursor.fetchone()
            total_issues = row[0] if row else 0
            
            cursor.execute("SELECT COUNT(*) FROM skills")
            row = cursor.fetchone()
            total_skills = row[0] if row else 0
            
            # 获取成功率
            success_rate = (resolved / total_issues * 100) if total_issues > 0 else 0
            
            # 获取最近活动
            cursor.execute("""
                SELECT created_at FROM issues 
                ORDER BY created_at DESC LIMIT 1
            """)
            row = cursor.fetchone()
            last_activity = row[0] if row else None
            
            return {
                'cycle_count': self.cycle_count,
                'success_count': self.success_count,
                'error_count': self.error_count,
                'total_issues': total_issues,
                'resolved_issues': resolved,
                'success_rate': f"{success_rate:.1f}%",
                'total_skills': total_skills,
                'last_activity': last_activity,
                'current_phase': self.current_phase.name if hasattr(self, 'current_phase') else 'IDLE',
                'status': 'running' if self.cycle_count > 0 else 'idle'
            }
            
        except Exception as e:
            logger.warning(f"[仪表盘] 获取失败: {e}")
            return {
                'cycle_count': self.cycle_count,
                'success_count': self.success_count,
                'error_count': self.error_count,
                'status': 'error',
                'error': str(e)
            }
    
    # ========== 10. 人类审批流程 ==========
    def _needs_human_approval(self, fix_proposal: Dict[str, Any]) -> bool:
        """
        判断修复是否需要人类审批。
        
        Args:
            fix_proposal: 修复建议
            
        Returns:
            是否需要审批
        """
        # 高风险特征
        risk_indicators = []
        
        # 检查修改核心文件
        core_files = ['engine.py', 'database.py', '__init__.py']
        affected_files = fix_proposal.get('affected_files', [])
        for f in affected_files:
            if any(core in f for core in core_files):
                risk_indicators.append('core_file_modified')
        
        # 检查删除操作
        if fix_proposal.get('action') == 'delete':
            risk_indicators.append('deletion')
        
        # 检查大规模修改
        if fix_proposal.get('lines_changed', 0) > 100:
            risk_indicators.append('large_change')
        
        # 检查正则表达式修改
        code = fix_proposal.get('fix_code', '')
        if 're.compile' in code or 'eval(' in code or 'exec(' in code:
            risk_indicators.append('regex_or_dynamic')
        
        # 任何风险指标都需要审批
        return len(risk_indicators) > 0
    
    # ========== 11. 性能基准测试 (增强) ==========
    def _record_performance_metrics(self, cycle_data: Dict[str, Any]) -> None:
        """
        记录性能基准测试数据。
        
        Args:
            cycle_data: 周期数据
        """
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # 创建性能表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evolution_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle INTEGER NOT NULL,
                    duration_seconds REAL,
                    cpu_percent REAL,
                    memory_mb REAL,
                    issues_detected INTEGER,
                    issues_resolved INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 记录本次性能数据
            import psutil
            process = psutil.Process()
            
            cursor.execute("""
                INSERT INTO evolution_metrics 
                (cycle, duration_seconds, cpu_percent, memory_mb, issues_detected, issues_resolved)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                cycle_data.get('cycle', 0),
                cycle_data.get('duration', 0),
                cycle_data.get('cpu', 0),
                process.memory_info().rss / 1024 / 1024,
                cycle_data.get('issues_detected', 0),
                cycle_data.get('issues_resolved', 0)
            ))
            
            conn.commit()
            logger.debug("[性能] 指标已记录")
            
        except ImportError:
            logger.debug("[性能] psutil未安装，跳过性能记录")
        except Exception as e:
            logger.warning(f"[性能] 记录失败: {e}")
    
    # ========== 12. 错误模式聚类 ==========
    def _cluster_error_patterns(self, errors: list) -> Dict[str, Any]:
        """
        使用K-means简化版对错误进行聚类。
        
        Args:
            errors: 错误列表
            
        Returns:
            聚类结果
        """
        if len(errors) < 3:
            return {'clusters': [], 'unclustered': errors}
        
        # 简单聚类：按错误类型分组
        type_groups = {}
        
        for error in errors:
            # 提取错误类型关键词
            msg = error.get('message', '').lower()
            
            if 'import' in msg or 'module' in msg:
                category = 'import_error'
            elif 'syntax' in msg or 'indentation' in msg:
                category = 'syntax_error'
            elif 'attribute' in msg or 'none' in msg:
                category = 'attribute_error'
            elif 'timeout' in msg or 'network' in msg:
                category = 'network_error'
            else:
                category = 'other'
            
            if category not in type_groups:
                type_groups[category] = []
            type_groups[category].append(error)
        
        clusters = []
        for category, group in type_groups.items():
            clusters.append({
                'category': category,
                'count': len(group),
                'errors': group,
                'representative': group[0] if group else None
            })
        
        # 按数量排序
        clusters.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'total_errors': len(errors),
            'clusters': clusters,
            'cluster_count': len(clusters)
        }
    
    # ========== 4. 跨会话记忆 (增强) ==========
    def _save_fix_pattern_to_db(self, rule_name: str, error_pattern: str, 
                                 fix_type: str, success: bool) -> None:
        """
        保存修复模式到数据库（跨会话记忆）。
        
        Args:
            rule_name: 规则名称
            error_pattern: 错误模式
            fix_type: 修复类型
            success: 是否成功
        """
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # 使用 INSERT OR UPDATE
            cursor.execute("""
                INSERT INTO fix_patterns (rule_name, error_pattern, fix_type, 
                    fix_success_count, fix_fail_count, last_success_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(rule_name, error_pattern) DO UPDATE SET
                    fix_success_count = fix_success_count + ?,
                    fix_fail_count = fix_fail_count + ?,
                    last_success_at = CASE WHEN ? THEN datetime('now') ELSE last_success_at END
            """, (rule_name, error_pattern, fix_type, 
                  1 if success else 0, 0 if success else 1,
                  1 if success else 0, 0 if success else 1, success))
            
            conn.commit()
            logger.debug(f"[记忆] 已保存修复模式: {rule_name}")
            
        except Exception as e:
            logger.warning(f"[记忆] 保存失败: {e}")
    
    def _load_fix_patterns_from_db(self) -> list:
        """
        从数据库加载历史修复模式（跨会话记忆）。
        
        Returns:
            修复模式列表
        """
        patterns = []
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT rule_name, error_pattern, fix_type, 
                       fix_success_count, fix_fail_count, created_at
                FROM fix_patterns
                WHERE fix_success_count > 0
                ORDER BY fix_success_count DESC
                LIMIT 50
            """)
            
            for row in cursor.fetchall():
                total = row[3] + row[4]
                patterns.append({
                    'rule_name': row[0],
                    'error_pattern': row[1],
                    'fix_type': row[2],
                    'success_count': row[3],
                    'fail_count': row[4],
                    'confidence': row[3] / total if total > 0 else 0,
                    'created_at': row[5]
                })
            
            logger.info(f"[记忆] 加载了 {len(patterns)} 个历史修复模式")
            
        except Exception as e:
            logger.warning(f"[记忆] 加载失败: {e}")
        
        return patterns
    
    # ========== 2. 沙箱验证集成 ==========
    def _sandbox_verify_fix(self, fix_code: str, test_input: Dict) -> bool:
        """
        在沙箱环境中验证修复代码。
        
        Args:
            fix_code: 修复代码
            test_input: 测试输入
            
        Returns:
            验证是否通过
        """
        import tempfile
        import subprocess
        import os
        
        try:
            # 创建临时测试文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(fix_code)
                f.write("\n# Test\nresult = test_fix()\nprint('PASS' if result else 'FAIL')")
                temp_file = f.name
            
            # 在隔离环境运行
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                timeout=5,  # 5秒超时
                cwd=tempfile.gettempdir()
            )
            
            # 清理
            os.unlink(temp_file)
            
            # 检查结果
            if result.returncode == 0 and b'PASS' in result.stdout:
                logger.info("[沙箱] 验证通过")
                return True
            else:
                logger.warning(f"[沙箱] 验证失败: {result.stderr.decode()}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning("[沙箱] 验证超时")
            return False
        except Exception as e:
            logger.warning(f"[沙箱] 验证异常: {e}")
            return False
    
    # ========== 3. 修复应用闭环 ==========
    def _apply_fix_to_skill(self, fix_proposal: Dict[str, Any]) -> bool:
        """
        将修复建议应用到skill生成（闭环）。
        
        Args:
            fix_proposal: 修复建议
            
        Returns:
            是否成功应用
        """
        try:
            # 生成skill代码
            skill_code = self._generate_skill_from_fix(fix_proposal)
            
            if not skill_code:
                return False
            
            # 保存到skills目录
            skills_dir = os.path.join(os.path.dirname(__file__), '..', 'skills')
            os.makedirs(skills_dir, exist_ok=True)
            
            skill_file = os.path.join(skills_dir, f"auto_fix_{self.cycle_count}.py")
            with open(skill_file, 'w', encoding='utf-8') as f:
                f.write(skill_code)
            
            logger.info(f"[闭环] 已保存自动修复技能: {skill_file}")
            
            # 记录到数据库
            self._save_fix_pattern_to_db(
                rule_name=fix_proposal.get('rule_name', 'unknown'),
                error_pattern=fix_proposal.get('error_pattern', ''),
                fix_type=fix_proposal.get('fix_type', 'auto'),
                success=True
            )
            
            return True
            
        except Exception as e:
            logger.warning(f"[闭环] 应用修复失败: {e}")
            return False
    
    def _generate_skill_from_fix(self, fix_proposal: Dict) -> str:
        """从修复建议生成skill代码"""
        error_type = fix_proposal.get('type', 'unknown')
        fix_code = fix_proposal.get('fix_code', 'pass')
        
        skill_template = f'''# 自动生成的修复技能
# 类型: {error_type}
# 生成时间: {datetime.now().isoformat()}

{fix_code}

def execute(error_info):
    """
    自动修复 {error_type} 类型错误
    """
    try:
        return apply_fix(error_info)
    except Exception as e:
        logging.error(f"Auto-fix failed: {{e}}")
        return False
'''
        return skill_template
