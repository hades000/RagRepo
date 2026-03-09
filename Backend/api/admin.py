"""
Admin API endpoints for system management using asyncpg
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timedelta
from core.cost_tracker import CostTracker
from core.global_vector_store_manager import GlobalVectorStoreManager
from core.embedding_service import EmbeddingService
from core.bm25_service import BM25Service
from core.db import get_db
from core.document_sources import DocumentSources
from utils.response import success_response, error_response
from api.deps import get_current_user

router = APIRouter()

# Global services
cost_tracker: Optional[CostTracker] = None


def init_admin_services():
    """Initialize admin services without Prisma"""
    global cost_tracker

    cost_tracker = CostTracker()
    print("Admin services initialized")


@router.get('/stats')
async def get_stats(user: dict = Depends(get_current_user)):
    """Get system-wide statistics using asyncpg."""
    try:
        db = get_db()

        # Token usage aggregation
        token_usage = await db.fetchrow("""
            SELECT
                SUM(total_tokens) as total_tokens,
                SUM(embedding_tokens) as embedding_tokens
            FROM rag_token_usage
        """)

        # Cost summary
        cost_summary = await db.fetchrow("""
            SELECT SUM(total_cost_inr) as total_cost
            FROM rag_cost_summary
        """)

        # Recent queries (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_queries = await db.fetchval("""
            SELECT COUNT(*)
            FROM rag_token_usage
            WHERE operation_type = 'query'
            AND timestamp >= $1
        """, yesterday)

        # Vector store stats
        embedding_service = EmbeddingService()
        vs_manager = GlobalVectorStoreManager(embedding_service.embeddings)
        vs_stats = vs_manager.get_stats() if vs_manager.exists() else {
            'document_count': 0,
            'exists': False
        }

        # BM25 index stats
        bm25_service = BM25Service()
        bm25_exists = bm25_service.index_exists()

        document_count = vs_stats.get('document_count', 0)

        return success_response(
            data={
                'total_documents': document_count,
                'total_chunks': document_count,  # In this system, chunks = documents
                'total_tokens_used': int(token_usage['total_tokens'] or 0) if token_usage else 0,
                'total_cost_inr': float(cost_summary['total_cost'] or 0.0) if cost_summary else 0.0,
                'recent_queries': recent_queries or 0,

                'indices': {
                    'vector_store': vs_stats,
                    'bm25': {
                        'exists': bm25_exists,
                        'path': 'data/bm25/global/'
                    }
                },
                'usage': {
                    'total_tokens': int(token_usage['total_tokens'] or 0) if token_usage else 0,
                    'embedding_tokens': int(token_usage['embedding_tokens'] or 0) if token_usage else 0,
                    'queries_24h': recent_queries or 0
                },
                'costs': {
                    'total_cost_inr': float(cost_summary['total_cost'] or 0.0) if cost_summary else 0.0,
                    'currency': 'INR'
                },
                'timestamp': datetime.now().isoformat()
            },
            message="Statistics retrieved successfully"
        )

    except Exception as e:
        print(f"Stats error: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to get statistics: {str(e)}", 500)


@router.get('/usage/by-user')
async def get_usage_by_user(user: dict = Depends(get_current_user)):
    """Get usage breakdown by user using asyncpg."""
    try:
        db = get_db()

        query = """
            SELECT
                cs.user_id,
                u.email as user_email,
                u.name as user_name,
                cs.total_llm_cost_inr,
                cs.total_embedding_cost_inr,
                cs.total_cost_inr,
                cs.last_updated,
                COUNT(tu.id) FILTER (WHERE tu.operation_type = 'query') as query_count,
                COUNT(tu.id) FILTER (WHERE tu.operation_type = 'sync') as sync_count
            FROM rag_cost_summary cs
            LEFT JOIN "User" u ON cs.user_id = u.id
            LEFT JOIN rag_token_usage tu ON cs.user_id = tu.user_id
            GROUP BY cs.user_id, u.email, u.name, cs.total_llm_cost_inr,
                     cs.total_embedding_cost_inr, cs.total_cost_inr, cs.last_updated
            ORDER BY cs.total_cost_inr DESC
        """

        rows = await db.fetch(query)

        user_stats = []
        for row in rows:
            user_stats.append({
                'user_id': row['user_id'],
                'user_email': row['user_email'] or 'Unknown',
                'user_name': row['user_name'] or 'Unknown',
                'total_cost_inr': float(row['total_cost_inr']),
                'llm_cost_inr': float(row['total_llm_cost_inr']),
                'embedding_cost_inr': float(row['total_embedding_cost_inr']),
                'query_count': row['query_count'] or 0,
                'sync_count': row['sync_count'] or 0,
                'last_activity': row['last_updated'].isoformat() if row['last_updated'] else None
            })

        return success_response(
            data={
                'user_stats': user_stats,
                'total_users': len(user_stats)
            },
            message=f"Retrieved stats for {len(user_stats)} users"
        )

    except Exception as e:
        print(f"User usage error: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to get user usage: {str(e)}", 500)


@router.get('/usage/recent')
async def get_recent_usage(
    user: dict = Depends(get_current_user),
    limit: int = Query(default=100),
    operation_type: Optional[str] = Query(default=None),
):
    """Get recent usage activity using asyncpg."""
    try:
        db = get_db()

        query = """
            SELECT
                tu.id,
                tu.user_id,
                u.email as user_email,
                u.name as user_name,
                tu.operation_type,
                tu.model_used,
                tu.provider,
                tu.query,
                tu.input_tokens,
                tu.output_tokens,
                tu.total_tokens,
                tu.embedding_tokens,
                tu.llm_cost_inr,
                tu.embedding_cost_inr,
                tu.total_cost_inr,
                tu.timestamp
            FROM rag_token_usage tu
            LEFT JOIN "User" u ON tu.user_id = u.id
        """

        params = []
        if operation_type:
            query += " WHERE tu.operation_type = $1"
            params.append(operation_type)

        query += " ORDER BY tu.timestamp DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)

        rows = await db.fetch(query, *params)

        usage_records = []
        for row in rows:
            usage_records.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'user_email': row['user_email'] or 'Unknown',
                'user_name': row['user_name'] or 'Unknown',
                'operation_type': row['operation_type'],
                'model': row['model_used'],
                'provider': row['provider'],
                'query_preview': row['query'][:100] + '...' if row['query'] and len(row['query']) > 100 else row['query'],
                'tokens': {
                    'input': row['input_tokens'],
                    'output': row['output_tokens'],
                    'total': row['total_tokens'],
                    'embedding': row['embedding_tokens']
                },
                'costs': {
                    'llm_inr': float(row['llm_cost_inr']),
                    'embedding_inr': float(row['embedding_cost_inr']),
                    'total_inr': float(row['total_cost_inr'])
                },
                'timestamp': row['timestamp'].isoformat()
            })

        return success_response(
            data={
                'records': usage_records,
                'count': len(usage_records),
                'filter': {
                    'operation_type': operation_type,
                    'limit': limit
                }
            },
            message=f"Retrieved {len(usage_records)} usage records"
        )

    except Exception as e:
        print(f"Recent usage error: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to get recent usage: {str(e)}", 500)


@router.get('/costs/summary')
async def get_cost_summary(
    user: dict = Depends(get_current_user),
    days: int = Query(default=30),
):
    """Get cost summary with time-based breakdown using asyncpg."""
    try:
        db = get_db()

        since_date = datetime.now() - timedelta(days=days)

        daily_costs = await db.fetch("""
            SELECT
                DATE(timestamp) as date,
                SUM(total_cost_inr) as cost_inr,
                SUM(total_tokens) as tokens,
                COUNT(*) as operations
            FROM rag_token_usage
            WHERE timestamp >= $1
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp) DESC
        """, since_date)

        operation_costs = await db.fetch("""
            SELECT
                operation_type,
                SUM(total_cost_inr) as cost_inr,
                SUM(total_tokens) as tokens,
                COUNT(*) as count
            FROM rag_token_usage
            WHERE timestamp >= $1
            GROUP BY operation_type
            ORDER BY cost_inr DESC
        """, since_date)

        model_costs = await db.fetch("""
            SELECT
                provider,
                model_used,
                SUM(total_cost_inr) as cost_inr,
                SUM(total_tokens) as tokens,
                COUNT(*) as queries
            FROM rag_token_usage
            WHERE timestamp >= $1 AND operation_type = 'query'
            GROUP BY provider, model_used
            ORDER BY cost_inr DESC
        """, since_date)

        period_total = await db.fetchrow("""
            SELECT
                SUM(total_cost_inr) as total_cost,
                SUM(llm_cost_inr) as llm_cost,
                SUM(embedding_cost_inr) as embedding_cost,
                SUM(total_tokens) as total_tokens
            FROM rag_token_usage
            WHERE timestamp >= $1
        """, since_date)

        return success_response(
            data={
                'period': {
                    'days': days,
                    'start_date': since_date.date().isoformat(),
                    'end_date': datetime.now().date().isoformat()
                },
                'totals': {
                    'cost_inr': float(period_total['total_cost'] or 0.0) if period_total else 0.0,
                    'llm_cost_inr': float(period_total['llm_cost'] or 0.0) if period_total else 0.0,
                    'embedding_cost_inr': float(period_total['embedding_cost'] or 0.0) if period_total else 0.0,
                    'tokens': int(period_total['total_tokens'] or 0) if period_total else 0
                },
                'daily_costs': [
                    {
                        'date': row['date'].isoformat(),
                        'cost_inr': float(row['cost_inr'] or 0.0),
                        'tokens': int(row['tokens'] or 0),
                        'operations': row['operations']
                    }
                    for row in daily_costs
                ],
                'by_operation': [
                    {
                        'operation_type': row['operation_type'],
                        'cost_inr': float(row['cost_inr'] or 0.0),
                        'tokens': int(row['tokens'] or 0),
                        'count': row['count']
                    }
                    for row in operation_costs
                ],
                'by_model': [
                    {
                        'provider': row['provider'],
                        'model': row['model_used'],
                        'cost_inr': float(row['cost_inr'] or 0.0),
                        'tokens': int(row['tokens'] or 0),
                        'queries': row['queries']
                    }
                    for row in model_costs
                ]
            },
            message="Cost summary retrieved successfully"
        )

    except Exception as e:
        print(f"Cost summary error: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to get cost summary: {str(e)}", 500)


@router.get('/documents/summary')
async def get_document_summary(user: dict = Depends(get_current_user)):
    """Get document summary from all sources."""
    try:
        doc_sources = DocumentSources()
        documents = await doc_sources.fetch_all_documents()

        # Group by source
        by_source = {}
        for doc in documents:
            source = doc.source_table
            if source not in by_source:
                by_source[source] = 0
            by_source[source] += 1

        return success_response(
            data={
                'total_documents': len(documents),
                'by_source': by_source,
                'sources_available': list(by_source.keys())
            },
            message=f"Retrieved {len(documents)} documents from {len(by_source)} sources"
        )

    except Exception as e:
        print(f"Document summary error: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f"Failed to get document summary: {str(e)}", 500)


@router.get('/health')
def health_check():
    """Health check endpoint."""
    try:
        # Check if connection manager is initialized
        from core.db import _db_connection

        return success_response(
            data={
                'status': 'healthy',
                'database': 'connected' if _db_connection else 'not initialized',
                'cost_tracker': 'initialized' if cost_tracker else 'not initialized',
                'timestamp': datetime.now().isoformat()
            },
            message="Admin service is healthy"
        )

    except Exception as e:
        print(f"Health check error: {e}")
        return error_response(f"Health check failed: {str(e)}", 500)
