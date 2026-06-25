"""数据库连接池模块

使用SQLAlchemy连接池管理数据库连接，支持WAL模式。
提供线程安全的数据库连接获取方法。
"""

import os
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.engine.base import Connection


class ConnectionPool:
    """SQLAlchemy数据库连接池
    
    管理数据库连接池，支持WAL模式和多线程安全访问。
    
    Attributes:
        database_url: 数据库URL
        engine: SQLAlchemy引擎实例
        session_factory: 会话工厂
        scoped_session: 线程局部的会话
        _settings: 配置对象
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
        wal_mode: bool = True
    ) -> None:
        """初始化数据库连接池
        
        Args:
            database_url: 数据库URL，如果为None则使用SQLite默认路径
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
            pool_timeout: 连接超时时间（秒）
            pool_recycle: 连接回收时间（秒）
            echo: 是否打印SQL语句
            wal_mode: 是否启用WAL模式（仅SQLite有效）
        """
        # 处理数据库URL
        if database_url is None:
            db_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..',
                'db',
                'evolution.db'
            )
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            database_url = f"sqlite:///{db_path}"
        
        self.database_url = database_url
        self.wal_mode = wal_mode and database_url.startswith('sqlite:///')
        
        # 创建SQLAlchemy引擎
        self.engine: Engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            echo=echo,
            # SQLite特定配置
            connect_args=(
                {"check_same_thread": False}
                if database_url.startswith('sqlite:///')
                else {}
            )
        )
        
        # 启用WAL模式（仅SQLite）
        if self.wal_mode:
            self._enable_wal_mode()
        
        # 创建会话工厂
        self.session_factory = sessionmaker(bind=self.engine)
        self.scoped_session = scoped_session(self.session_factory)
    
    def _enable_wal_mode(self) -> None:
        """启用SQLite WAL模式
        
        通过SQLAlchemy事件监听器，在创建新连接时启用WAL模式。
        WAL模式提供更好的并发性能和事务安全性。
        """
        @event.listens_for(self.engine, "connect")
        def set_sqlite_wal_pragma(dbapi_connection: Any, connection_record: Any) -> None:
            """设置SQLite WAL模式pragma"""
            cursor = dbapi_connection.cursor()
            try:
                # 启用WAL模式
                cursor.execute("PRAGMA journal_mode=WAL")
                # 设置WAL自动检查点
                cursor.execute("PRAGMA wal_autocheckpoint=1000")
                # 设置busy timeout（毫秒）
                cursor.execute("PRAGMA busy_timeout=5000")
                # 启用外键约束
                cursor.execute("PRAGMA foreign_keys=ON")
            except Exception as e:
                print(f"Warning: Failed to set WAL mode: {e}")
            finally:
                cursor.close()
    
    def get_engine(self) -> Engine:
        """获取SQLAlchemy引擎
        
        Returns:
            SQLAlchemy引擎实例
        """
        return self.engine
    
    def get_session(self) -> Any:
        """获取数据库会话
        
        Returns:
            SQLAlchemy会话对象
        """
        return self.session_factory()
    
    def get_scoped_session(self) -> Any:
        """获取线程局部的数据库会话
        
        Returns:
            线程局部的SQLAlchemy会话对象
        """
        return self.scoped_session()
    
    def get_connection(self) -> Connection:
        """获取原始数据库连接
        
        Returns:
            原始数据库连接对象
        """
        return self.engine.connect()
    
    def dispose(self) -> None:
        """释放连接池资源
        
        关闭所有连接并释放资源。
        应在应用程序退出时调用。
        """
        if self.engine:
            self.engine.dispose()
    
    def is_healthy(self) -> bool:
        """检查数据库连接是否健康
        
        Returns:
            连接是否正常
        """
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def get_pool_status(self) -> Dict[str, Any]:
        """获取连接池状态
        
        Returns:
            连接池状态字典
        """
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalidated": pool.invalidated()
        }
    
    @classmethod
    def from_settings(cls, settings: Any) -> "ConnectionPool":
        """从配置对象创建连接池
        
        Args:
            settings: 配置对象（Settings实例或类似对象）
            
        Returns:
            ConnectionPool实例
        """
        database_url = settings.get('database.url', 'sqlite:///evolution.db')
        pool_size = settings.get('database.pool_size', 5)
        max_overflow = settings.get('database.max_overflow', 10)
        pool_timeout = settings.get('database.pool_timeout', 30)
        pool_recycle = settings.get('database.pool_recycle', 3600)
        echo = settings.get('database.echo', False)
        wal_mode = settings.get('database.wal_mode', True)
        
        return cls(
            database_url=database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            echo=echo,
            wal_mode=wal_mode
        )


# 全局连接池实例
_connection_pool_instance: Optional[ConnectionPool] = None


def get_connection_pool(settings: Optional[Any] = None) -> ConnectionPool:
    """获取全局连接池实例
    
    Args:
        settings: 配置对象（首次调用时需要）
        
    Returns:
        ConnectionPool实例
    """
    global _connection_pool_instance
    if _connection_pool_instance is None:
        if settings is None:
            from ..config.settings import get_settings
            settings = get_settings()
        _connection_pool_instance = ConnectionPool.from_settings(settings)
    return _connection_pool_instance


def dispose_connection_pool() -> None:
    """释放全局连接池资源"""
    global _connection_pool_instance
    if _connection_pool_instance:
        _connection_pool_instance.dispose()
        _connection_pool_instance = None
