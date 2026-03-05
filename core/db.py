"""
AsyncPG database connection for Flask async routes
"""
import asyncpg
import os
from typing import Optional
from contextlib import asynccontextmanager


class DatabaseConnection:
    """
    Manages asyncpg connections for Flask async routes.
    Creates connections on-demand per request instead of using a pool.
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._initialized = False
    
    async def initialize(self, database_url: Optional[str] = None):
        """
        Initialize the connection manager.
        For compatibility with scripts - no-op since connections are per-request.
        
        Args:
            database_url: Optional database URL (uses constructor URL if not provided)
        """
        if database_url:
            self.database_url = database_url
        self._initialized = True
        print(f"✅ DatabaseConnection initialized for {self.database_url[:30]}...")
    
    async def close(self):
        """
        Close the connection manager.
        For compatibility with scripts - no-op since connections are per-request.
        """
        self._initialized = False
        print("✅ DatabaseConnection closed (per-request connections automatically managed)")
    
    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a database connection.
        Creates a new connection for each request.
        
        Usage:
            async with db_connection.acquire() as conn:
                await conn.execute("SELECT 1")
        """
        conn = await asyncpg.connect(self.database_url)
        try:
            yield conn
        finally:
            await conn.close()
    
    async def fetch(self, query: str, *args):
        """Fetch multiple rows."""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """Fetch single row."""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """Fetch single value."""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute(self, query: str, *args):
        """Execute query without returning results."""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def executemany(self, query: str, args_list):
        """Execute query multiple times with different parameters."""
        async with self.acquire() as conn:
            return await conn.executemany(query, args_list)


# Internal state — never import these directly
_db_connection: Optional[DatabaseConnection] = None
_reference_db_connection: Optional[DatabaseConnection] = None


def init_db():
    """Initialize database connection managers"""
    global _db_connection, _reference_db_connection
    
    from config import Config
    
    _db_connection = DatabaseConnection(Config.DATABASE_URL)
    _reference_db_connection = DatabaseConnection(Config.REFERENCE_DATABASE_URL)
    
    print("✅ Database connection managers initialized")


def close_db():
    """Cleanup (no-op for per-request connections)"""
    print("✅ Database connections will be closed per-request")


def get_db() -> DatabaseConnection:
    """
    Get the main database connection manager.
    
    Call this at runtime (inside request handlers), never at import time.
    
    Returns:
        DatabaseConnection instance
        
    Raises:
        RuntimeError: If init_db() has not been called
    """
    if _db_connection is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db_connection


def get_reference_db() -> DatabaseConnection:
    """
    Get the reference database connection manager.
    
    Returns:
        DatabaseConnection instance
        
    Raises:
        RuntimeError: If init_db() has not been called
    """
    if _reference_db_connection is None:
        raise RuntimeError("Reference database not initialized. Call init_db() first.")
    return _reference_db_connection