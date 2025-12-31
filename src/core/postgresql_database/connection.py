"""
Database Connection Management

Handles PostgreSQL database connections with connection pooling.
"""

import os
from typing import Optional
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database configuration."""
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="ai_app")
    user: str = Field(default="postgres")
    password: str = Field(default="")
    min_connections: int = Field(default=1)
    max_connections: int = Field(default=10)
    connection_timeout: int = Field(default=30)
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create config from environment variables."""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "ai_app"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            min_connections=int(os.getenv("DB_MIN_CONNECTIONS", "1")),
            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "10")),
        )


class DatabaseConnection:
    """
    PostgreSQL database connection manager with connection pooling.
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize database connection.
        
        Args:
            config: Database configuration
        """
        self.config = config
        self.connection_pool: Optional[pool.ThreadedConnectionPool] = None
    
    def connect(self) -> None:
        """Create connection pool."""
        try:
            self.connection_pool = pool.ThreadedConnectionPool(
                minconn=self.config.min_connections,
                maxconn=self.config.max_connections,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to create connection pool: {e}")
    
    def close(self) -> None:
        """Close all connections in pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            self.connection_pool = None
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Yields:
            Database connection
        """
        if not self.connection_pool:
            self.connect()
        
        conn = self.connection_pool.getconn()
        try:
            yield conn
        finally:
            self.connection_pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, cursor_factory=None):
        """
        Get a cursor from the connection pool.
        
        Args:
            cursor_factory: Optional cursor factory (e.g., RealDictCursor)
        
        Yields:
            Database cursor
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = True
    ):
        """
        Execute a query.
        
        Args:
            query: SQL query
            params: Query parameters
            fetch_one: Return single row
            fetch_all: Return all rows
        
        Returns:
            Query results
        """
        with self.get_cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.rowcount
    
    def execute_transaction(self, queries: list[tuple[str, Optional[tuple]]]) -> None:
        """
        Execute multiple queries in a transaction.
        
        Args:
            queries: List of (query, params) tuples
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                for query, params in queries:
                    cursor.execute(query, params)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def check_connection(self) -> bool:
        """
        Check if database connection is working.
        
        Returns:
            True if connection is valid
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False

