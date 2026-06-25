"""数据仓库 - CRUD操作"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import Event, Memory, Skill, ExecutionLog, Review, CycleResult
from .database import Database
import json
 
class BaseRepository:
    """基础仓库类"""
    def __init__(self, db: Database):
        self.db = db
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """行转字典"""
        if row is None:
            return {}
        return dict(row)
 
class EventRepository(BaseRepository):
    """事件仓库"""
    def create(self, event: Event) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO events 
            (event_type, phase, status, message, severity, metadata) 
            VALUES (?, ?, ?, ?, ?, ?)""",
            (event.event_type, event.phase, event.status, 
             event.message, event.severity, event.metadata))
        conn.commit()
        event_id = cursor.lastrowid
        conn.close()
        return event_id
    
    def get_by_id(self, event_id: int) -> Optional[Event]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Event(**self._row_to_dict(row))
        return None
    
    def search(self, event_type: str = None, phase: str = None, 
               limit: int = 50) -> List[Event]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if phase:
            query += " AND phase = ?"
            params.append(phase)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [Event(**self._row_to_dict(row)) for row in rows]
    
    def get_all(self) -> List[Event]:
        """获取所有事件"""
        return self.search(limit=1000)
    
    def get_errors(self, hours: int = 1, limit: int = 100) -> List[Event]:
        """获取最近的错误事件"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM events 
            WHERE severity = 'error' 
            ORDER BY created_at DESC LIMIT ?""", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [Event(**self._row_to_dict(row)) for row in rows]

class MemoryRepository(BaseRepository):
    """记忆仓库"""
    def create(self, memory: Memory) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO memories 
            (content, memory_type, importance, access_count, last_accessed) 
            VALUES (?, ?, ?, ?, ?)""",
            (memory.content, memory.memory_type, memory.importance,
             memory.access_count, memory.last_accessed))
        conn.commit()
        memory_id = cursor.lastrowid
        conn.close()
        return memory_id
    
    def get_by_type(self, memory_type: str, limit: int = 50) -> List[Memory]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM memories 
            WHERE memory_type = ? ORDER BY importance DESC, created_at DESC LIMIT ?""",
            (memory_type, limit))
        rows = cursor.fetchall()
        conn.close()
        return [Memory(**self._row_to_dict(row)) for row in rows]
    
    def get_important(self, min_importance: float = 0.7, limit: int = 20) -> List[Memory]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM memories 
            WHERE importance >= ? ORDER BY importance DESC, access_count DESC LIMIT ?""",
            (min_importance, limit))
        rows = cursor.fetchall()
        conn.close()
        return [Memory(**self._row_to_dict(row)) for row in rows]
    
    def increment_access(self, memory_id: int):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""UPDATE memories 
            SET access_count = access_count + 1, last_accessed = ? 
            WHERE id = ?""", (datetime.now(), memory_id))
        conn.commit()
        conn.close()
    
    def get_all(self) -> List[Memory]:
        """获取所有记忆"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories ORDER BY importance DESC, created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [Memory(**self._row_to_dict(row)) for row in rows]
 
class SkillRepository(BaseRepository):
    """技能仓库"""
    def create(self, skill: Skill) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO skills 
            (name, description, content, skill_type, risk_level, status, validation_result) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (skill.name, skill.description, skill.content, 
             skill.skill_type, skill.risk_level, skill.status, skill.validation_result))
        conn.commit()
        skill_id = cursor.lastrowid
        conn.close()
        return skill_id
    
    def get_by_id(self, skill_id: int) -> Optional[Skill]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills WHERE id = ?", (skill_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Skill(**self._row_to_dict(row))
        return None
    
    def get_all(self) -> List[Skill]:
        """获取所有技能"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [Skill(**self._row_to_dict(row)) for row in rows]
    
    def get_by_status(self, status: str) -> List[Skill]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills WHERE status = ? ORDER BY created_at DESC", (status,))
        rows = cursor.fetchall()
        conn.close()
        return [Skill(**self._row_to_dict(row)) for row in rows]
    
    def get_active(self) -> List[Skill]:
        """获取已应用的活跃技能"""
        return self.get_by_status("applied")
    
    def update_status(self, skill_id: int, status: str, validation_result: str = ""):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if status == "applied":
            cursor.execute("""UPDATE skills 
                SET status = ?, applied_at = ?, validation_result = ? 
                WHERE id = ?""", 
                (status, datetime.now(), validation_result, skill_id))
        else:
            cursor.execute("""UPDATE skills 
                SET status = ?, validation_result = ? 
                WHERE id = ?""", 
                (status, validation_result, skill_id))
        
        conn.commit()
        conn.close()
 
class ExecutionLogRepository(BaseRepository):
    """执行日志仓库"""
    def create(self, log: ExecutionLog) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO execution_logs 
            (phase, action, result, duration_ms) VALUES (?, ?, ?, ?)""",
            (log.phase, log.action, log.result, log.duration_ms))
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        return log_id
    
    def get_by_phase(self, phase: str, limit: int = 20) -> List[ExecutionLog]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM execution_logs 
            WHERE phase = ? ORDER BY created_at DESC LIMIT ?""", (phase, limit))
        rows = cursor.fetchall()
        conn.close()
        return [ExecutionLog(**self._row_to_dict(row)) for row in rows]
    
    def get_recent(self, limit: int = 50) -> List[ExecutionLog]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM execution_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [ExecutionLog(**self._row_to_dict(row)) for row in rows]
    
    def update(self, log_id: int, result: str = None, phase: str = None) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        updates = []
        params = []
        if result is not None:
            updates.append("result = ?")
            params.append(result)
        if phase is not None:
            updates.append("phase = ?")
            params.append(phase)
        if updates:
            params.append(log_id)
            cursor.execute(f"UPDATE execution_logs SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()
        conn.close()
        return True

class ReviewRepository(BaseRepository):
    """复盘仓库"""
    def create(self, review: Review) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO reviews 
            (goal, result, analysis, learning, action, status, tools) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (review.goal, review.result, review.analysis, 
             review.learning, review.action, review.status, review.tools))
        conn.commit()
        review_id = cursor.lastrowid
        conn.close()
        return review_id
    
    def get_all(self) -> List[Review]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reviews ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [Review(**self._row_to_dict(row)) for row in rows]
    
    def update(self, review_id: int, **kwargs):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [review_id]
        
        cursor.execute(f"UPDATE reviews SET {set_clause} WHERE id = ?", values)
        conn.commit()
        conn.close()
 
class CycleResultRepository(BaseRepository):
    """周期结果仓库"""
    def create(self, result: CycleResult) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO cycle_results 
            (cycle_id, phase, status, improvements, skills_created, errors, message) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (result.cycle_id, result.phase, result.status, 
             result.improvements, result.skills_created, result.errors, result.message))
        conn.commit()
        result_id = cursor.lastrowid
        conn.close()
        return result_id
    
    def get_by_cycle(self, cycle_id: int) -> List[CycleResult]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cycle_results WHERE cycle_id = ? ORDER BY timestamp", (cycle_id,))
        rows = cursor.fetchall()
        conn.close()
        return [CycleResult(**self._row_to_dict(row)) for row in rows]
    
    def get_latest_cycle_id(self) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(cycle_id) as max_id FROM cycle_results")
        row = cursor.fetchone()
        conn.close()
        return row["max_id"] if row and row["max_id"] else 0


class RepositoryFactory:
    """数据仓库工厂 - 创建所有仓库实例"""
    def __init__(self, db: Database):
        self.db = db
        self._event_repo = None
        self._memory_repo = None
        self._skill_repo = None
        self._execution_log_repo = None
        self._review_repo = None
        self._cycle_result_repo = None
    
    @property
    def event_repo(self) -> EventRepository:
        if self._event_repo is None:
            self._event_repo = EventRepository(self.db)
        return self._event_repo
    
    @property
    def memory_repo(self) -> MemoryRepository:
        if self._memory_repo is None:
            self._memory_repo = MemoryRepository(self.db)
        return self._memory_repo
    
    @property
    def skill_repo(self) -> SkillRepository:
        if self._skill_repo is None:
            self._skill_repo = SkillRepository(self.db)
        return self._skill_repo
    
    @property
    def execution_log_repo(self) -> ExecutionLogRepository:
        if self._execution_log_repo is None:
            self._execution_log_repo = ExecutionLogRepository(self.db)
        return self._execution_log_repo
    
    @property
    def review_repo(self) -> ReviewRepository:
        if self._review_repo is None:
            self._review_repo = ReviewRepository(self.db)
        return self._review_repo
    
    @property
    def cycle_result_repo(self) -> CycleResultRepository:
        if self._cycle_result_repo is None:
            self._cycle_result_repo = CycleResultRepository(self.db)
        return self._cycle_result_repo