"""Git版本管理后端 - 支持Git和数据库双后端"""
import os
import json
import logging
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class GitVersionManager:
    """Git版本管理器 - 当Git可用时使用"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.git_available = self._check_git()
    
    def _check_git(self) -> bool:
        """检查Git是否可用"""
        try:
            result = subprocess.run(
                ["git", "--version"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"[Git] Git可用: {result.stdout.strip()}")
                return True
        except Exception as e:
            logger.warning(f"[Git] Git不可用: {e}")
            return False
        return False
    
    def init_repo(self) -> bool:
        """初始化Git仓库"""
        if not self.git_available:
            return False
        try:
            # 检查是否已经初始化
            result = subprocess.run(
                ["git", "status"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("[Git] 仓库已初始化")
                return True
            
            # 初始化
            subprocess.run(
                ["git", "init"],
                cwd=self.repo_path,
                capture_output=True,
                timeout=5,
                check=True
            )
            
            # 配置用户信息
            subprocess.run(
                ["git", "config", "user.email", "evolution@workbuddy.ai"],
                cwd=self.repo_path,
                timeout=5,
                check=True
            )
            subprocess.run(
                ["git", "config", "user.name", "Evolution System"],
                cwd=self.repo_path,
                timeout=5,
                check=True
            )
            
            logger.info("[Git] 仓库初始化完成")
            return True
        except Exception as e:
            logger.error(f"[Git] 初始化失败: {e}")
            return False
    
    def create_version(self, file_path: str, content: str, 
                      message: str = "Auto version") -> Optional[str]:
        """创建版本 (git commit)"""
        if not self.git_available:
            return None
        
        try:
            # 写入文件
            full_path = os.path.join(self.repo_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Git add
            subprocess.run(
                ["git", "add", file_path],
                cwd=self.repo_path,
                timeout=5,
                check=True
            )
            
            # Git commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # 获取commit hash
                hash_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                commit_hash = hash_result.stdout.strip()[:8]
                logger.info(f"[Git] 版本已创建: {commit_hash} - {message}")
                return commit_hash
            else:
                logger.warning(f"[Git] Commit失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"[Git] 创建版本失败: {e}")
            return None
    
    def list_versions(self, file_path: str = None) -> List[Dict]:
        """列出版本历史 (git log)"""
        if not self.git_available:
            return []
        
        try:
            cmd = ["git", "log", "--oneline", "--pretty=format:%H|%an|%ae|%s|%ci"]
            if file_path:
                cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                versions = []
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    parts = line.split("|")
                    if len(parts) >= 5:
                        versions.append({
                            "commit_hash": parts[0][:8],
                            "author": parts[1],
                            "email": parts[2],
                            "message": parts[3],
                            "date": parts[4]
                        })
                return versions
            return []
        except Exception as e:
            logger.error(f"[Git] 列出版本失败: {e}")
            return []
    
    def rollback(self, commit_hash: str) -> bool:
        """回滚到指定版本"""
        if not self.git_available:
            return False
        
        try:
            subprocess.run(
                ["git", "checkout", commit_hash],
                cwd=self.repo_path,
                timeout=10,
                check=True
            )
            logger.info(f"[Git] 已回滚到: {commit_hash[:8]}")
            return True
        except Exception as e:
            logger.error(f"[Git] 回滚失败: {e}")
            return False
    
    def get_diff(self, commit1: str, commit2: str, 
                file_path: str = None) -> str:
        """获取版本差异"""
        if not self.git_available:
            return "Git不可用"
        
        try:
            cmd = ["git", "diff", f"{commit1}..{commit2}"]
            if file_path:
                cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.stdout if result.stdout else "无差异"
        except Exception as e:
            return f"获取差异失败: {e}"


class HybridVersionManager:
    """混合版本管理 - Git优先，数据库备用"""
    
    def __init__(self, repo_path: str = ".", database=None):
        self.git_manager = GitVersionManager(repo_path)
        self.db = database
        self.use_git = self.git_manager.git_available
        
        if self.use_git:
            self.git_manager.init_repo()
            logger.info("[版本管理] 使用Git后端")
        else:
            logger.info("[版本管理] Git不可用，使用数据库后端")
    
    def create_version(self, skill_id: int, content: str, 
                     description: str = "") -> Optional[int]:
        """创建版本"""
        if self.use_git:
            # Git后端：commit
            commit_hash = self.git_manager.create_version(
                f"skills/skill_{skill_id}.py",
                content,
                f"[Skill {skill_id}] {description}"
            )
            if commit_hash:
                # 同时保存到数据库（记录映射）
                return self._save_to_db(skill_id, content, description, commit_hash)
        else:
            # 数据库后端
            return self._save_to_db(skill_id, content, description)
    
    def _save_to_db(self, skill_id: int, content: str, 
                    description: str, git_hash: str = None) -> int:
        """保存到数据库"""
        try:
            import sqlite3
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # 获取当前版本号
            cursor.execute("""
                SELECT COALESCE(MAX(version_number), 0) + 1 
                FROM skill_versions 
                WHERE skill_id = ?
            """, (skill_id,))
            version_number = cursor.fetchone()[0]
            
            # 插入版本
            cursor.execute("""
                INSERT INTO skill_versions 
                (skill_id, version_number, content, description, git_commit_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (skill_id, version_number, content, description, git_hash))
            
            version_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"[版本] 已创建: skill_id={skill_id}, v{version_number}, id={version_id}")
            return version_id
            
        except Exception as e:
            logger.error(f"[版本] 保存失败: {e}")
            return 0
    
    def list_versions(self, skill_id: int) -> List[Dict]:
        """列出版本"""
        if self.use_git:
            # Git后端
            return self.git_manager.list_versions(f"skills/skill_{skill_id}.py")
        else:
            # 数据库后端
            try:
                import sqlite3
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, version_number, description, git_commit_hash, created_at
                    FROM skill_versions
                    WHERE skill_id = ?
                    ORDER BY version_number DESC
                """, (skill_id,))
                
                versions = []
                for row in cursor.fetchall():
                    versions.append({
                        "id": row[0],
                        "version": row[1],
                        "description": row[2],
                        "git_hash": row[3],
                        "created_at": row[4]
                    })
                
                conn.close()
                return versions
            except Exception as e:
                logger.error(f"[版本] 查询失败: {e}")
                return []
    
    def sync_to_git(self) -> int:
        """同步数据库版本到Git (当Git变为可用时)"""
        if not self.git_manager.git_available:
            logger.warning("[同步] Git不可用，无法同步")
            return 0
        
        try:
            # 获取所有未同步的版本
            import sqlite3
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sv.id, sv.skill_id, sv.version_number, 
                       sv.content, sv.description, s.name
                FROM skill_versions sv
                JOIN skills s ON sv.skill_id = s.id
                WHERE sv.git_commit_hash IS NULL
                ORDER BY sv.id
            """)
            
            synced = 0
            for row in cursor.fetchall():
                version_id, skill_id, version_number = row[0], row[1], row[2]
                content, description, skill_name = row[3], row[4], row[5]
                
                # 创建Git版本
                commit_hash = self.git_manager.create_version(
                    f"skills/skill_{skill_id}.py",
                    content,
                    f"[Sync] {skill_name} v{version_number}: {description}"
                )
                
                if commit_hash:
                    # 更新数据库记录
                    cursor.execute("""
                        UPDATE skill_versions 
                        SET git_commit_hash = ?
                        WHERE id = ?
                    """, (commit_hash, version_id))
                    synced += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"[同步] 已同步 {synced} 个版本到Git")
            return synced
            
        except Exception as e:
            logger.error(f"[同步] 失败: {e}")
            return 0
