"""SQLite数据库管理"""
import sqlite3
from pathlib import Path
from datetime import datetime
import os
 
class Database:
    _instance = None
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = None):
        if self._initialized:
            return
            
        if db_path is None:
            # 默认使用项目目录下的db文件夹
            base_dir = Path(__file__).parent.parent
            db_dir = base_dir / "db"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "evolution.db")
        
        self.db_path = db_path
        self._initialized = True
        self.init_tables()
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def init_tables(self):
        """初始化表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 事件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                phase TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                severity TEXT DEFAULT 'info',
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 记忆表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                memory_type TEXT DEFAULT 'sensory',
                importance REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 技能表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                content TEXT,
                skill_type TEXT DEFAULT 'skill_candidate',
                risk_level TEXT DEFAULT 'micro',
                status TEXT DEFAULT 'candidate',
                validation_result TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                applied_at TIMESTAMP
            )
        """)
        
        # 执行日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phase TEXT NOT NULL,
                action TEXT NOT NULL,
                result TEXT,
                duration_ms INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 复盘表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                result TEXT DEFAULT '',
                analysis TEXT DEFAULT '',
                learning TEXT DEFAULT '',
                action TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                tools TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 周期结果表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cycle_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id INTEGER NOT NULL,
                phase TEXT NOT NULL,
                status TEXT NOT NULL,
                improvements INTEGER DEFAULT 0,
                skills_created INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ========== 新增: 技能版本表 (Git式版本管理) ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skill_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id INTEGER NOT NULL,
                version_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
                UNIQUE(skill_id, version_number)
            )
        """)
        
        # ========== 新增: 修复模式历史表 (用于学习和置信度计算) ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fix_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                error_pattern TEXT NOT NULL,
                fix_type TEXT NOT NULL,
                fix_success_count INTEGER DEFAULT 0,
                fix_fail_count INTEGER DEFAULT 0,
                last_success_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(rule_name, error_pattern)
            )
        """)
        
        # ========== 新增: 技能应用历史表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skill_apply_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id INTEGER NOT NULL,
                skill_name TEXT NOT NULL,
                cycle_id INTEGER NOT NULL,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def close(self):
        """关闭连接"""
        self._instance = None
        self._initialized = False