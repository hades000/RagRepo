"""
Database connection using psycopg2 (no Prisma needed)
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    """PostgreSQL connection manager"""
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._pool is None:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL not found in environment")
            
            # Create connection pool
            self._pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=database_url
            )
            print("✅ Database connection pool created")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool"""
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """Get a cursor (returns rows as dictionaries)"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    def close(self):
        """Close all connections"""
        if self._pool:
            self._pool.closeall()
            print("❌ Database connections closed")


# Global instance
db_manager = DatabaseManager()


# Helper functions for RAG operations
def create_rag_document(user_id: str, filename: str, file_size: int, embedding_tokens: int = 0):
    """Create a document record"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO rag_documents (id, filename, user_id, file_size, embedding_tokens, upload_timestamp)
            VALUES (gen_random_uuid()::text, %s, %s, %s, %s, NOW())
            RETURNING id, filename, upload_timestamp, file_size, processing_status
        """, (filename, user_id, file_size, embedding_tokens))
        return cursor.fetchone()


def get_user_documents(user_id: str):
    """Get all documents for a user"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, filename, upload_timestamp, file_size, processing_status, embedding_tokens
            FROM rag_documents
            WHERE user_id = %s
            ORDER BY upload_timestamp DESC
        """, (user_id,))
        return cursor.fetchall()


def delete_rag_document(doc_id: str, user_id: str):
    """Delete a document"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            DELETE FROM rag_documents
            WHERE id = %s AND user_id = %s
            RETURNING id
        """, (doc_id, user_id))
        return cursor.fetchone() is not None


def get_user_stats(user_id: str):
    """Get document statistics for a user"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                COUNT(*) as doc_count,
                COALESCE(SUM(file_size), 0) as total_size
            FROM rag_documents
            WHERE user_id = %s
        """, (user_id,))
        return cursor.fetchone()


def log_token_usage(user_id: str, query: str, input_tokens: int, output_tokens: int, 
                     model: str, llm_cost: float, embedding_tokens: int = 0, embedding_cost: float = 0):
    """Log token usage for cost tracking"""
    total_cost = llm_cost + embedding_cost
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO rag_token_usage 
            (id, user_id, query, input_tokens, output_tokens, total_tokens, model_used, 
             llm_cost_inr, embedding_tokens, embedding_cost_inr, total_cost_inr, operation_type)
            VALUES (gen_random_uuid()::text, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'query')
        """, (user_id, query, input_tokens, output_tokens, input_tokens + output_tokens, 
              model, llm_cost, embedding_tokens, embedding_cost, total_cost))


async def init_db():
    """Initialize database (compatibility with async)"""
    print("✅ Database ready (psycopg2 pool)")


async def close_db():
    """Close database (compatibility with async)"""
    db_manager.close()