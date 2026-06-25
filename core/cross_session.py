# 跨会话进化状态持久化系统
# 让进化成果跨越重启，永久保留

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 状态文件路径
STATE_DIR = Path(__file__).parent / "state"
STATE_FILE = STATE_DIR / "evolution_state.json"
KNOWLEDGE_FILE = STATE_DIR / "knowledge.json"
SKILLS_FILE = STATE_DIR / "skills.json"

class CrossSessionEvolution:
    """跨会话进化 - 持久化所有进化成果"""
    
    def __init__(self):
        self.state_dir = STATE_DIR
        self.state_file = STATE_FILE
        self.knowledge_file = KNOWLEDGE_FILE
        self.skills_file = SKILLS_FILE
        self._ensure_state_dir()
        self.state = self._load_state()
    
    def _ensure_state_dir(self):
        """确保状态目录存在"""
        self.state_dir.mkdir(exist_ok=True)
    
    def _load_state(self) -> Dict:
        """加载上次状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        # 默认状态
        return {
            "session_count": 0,
            "total_cycles": 0,
            "start_time": datetime.now().isoformat(),
            "last_session": None,
            "evolution_progress": {},
            "learned_patterns": [],
            "improvements": []
        }
    
    def _save_state(self):
        """保存状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def load_knowledge(self) -> List[Dict]:
        """加载知识库"""
        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def save_knowledge(self, knowledge: List[Dict]):
        """保存知识库"""
        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=2)
    
    def load_skills(self) -> List[Dict]:
        """加载技能库"""
        if self.skills_file.exists():
            try:
                with open(self.skills_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def save_skills(self, skills: List[Dict]):
        """保存技能库"""
        with open(self.skills_file, 'w', encoding='utf-8') as f:
            json.dump(skills, f, ensure_ascii=False, indent=2)
    
    # === 对外接口 ===
    
    def on_session_start(self):
        """会话开始时调用"""
        self.state["session_count"] += 1
        self.state["last_session"] = datetime.now().isoformat()
        self._save_state()
        
        print("="*60)
        print("【跨会话进化系统】")
        print(f"  会话次数: {self.state['session_count']}")
        print(f"  累计循环: {self.state['total_cycles']}")
        print(f"  上次会话: {self.state['last_session']}")
        
        # 显示之前学到的模式
        if self.state.get("learned_patterns"):
            print(f"  已学习模式: {len(self.state['learned_patterns'])} 个")
        
        # 显示知识库
        know = self.load_knowledge()
        if know:
            print(f"  知识库条目: {len(know)} 条")
        
        print("="*60)
    
    def on_cycle_complete(self, cycle_id: int, improvements: List[str] = None):
        """循环完成时调用"""
        self.state["total_cycles"] += 1
        if improvements:
            self.state["improvements"].extend(improvements)
            # 只保留最近50条
            self.state["improvements"] = self.state["improvements"][-50:]
        self._save_state()
    
    def add_learned_pattern(self, pattern: str):
        """添加学习到的模式"""
        if pattern not in self.state["learned_patterns"]:
            self.state["learned_patterns"].append(pattern)
            self.state["learned_patterns"] = self.state["learned_patterns"][-20:]
            self._save_state()
    
    def add_knowledge(self, knowledge: Dict):
        """添加知识"""
        know = self.load_knowledge()
        know.append({
            "content": knowledge.get("content", ""),
            "category": knowledge.get("category", "general"),
            "added_at": datetime.now().isoformat()
        })
        self.save_knowledge(know)
    
    def add_skill(self, skill: Dict):
        """添加技能"""
        skills = self.load_skills()
        skills.append({
            "name": skill.get("name", ""),
            "code": skill.get("code", ""),
            "created_at": datetime.now().isoformat()
        })
        self.save_skills(skills)
    
    def get_progress(self) -> Dict:
        """获取进化进度"""
        return {
            "session_count": self.state["session_count"],
            "total_cycles": self.state["total_cycles"],
            "learned_patterns": len(self.state.get("learned_patterns", [])),
            "improvements": len(self.state.get("improvements", [])),
            "knowledge_count": len(self.load_knowledge()),
            "skills_count": len(self.load_skills())
        }

# 全局实例
_cross_session = None

def get_cross_session() -> CrossSessionEvolution:
    """获取跨会话实例"""
    global _cross_session
    if _cross_session is None:
        _cross_session = CrossSessionEvolution()
    return _cross_session