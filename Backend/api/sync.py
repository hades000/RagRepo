"""
Document synchronization API endpoints using asyncpg
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from typing import Optional
from core.document_sync_service import DocumentSyncService
from core.minio_fetcher import MinIOFetcher
from core.embedding_service import EmbeddingService
from core.bm25_service import BM25Service
from core.cost_tracker import CostTracker
from core.db import get_db
from utils.response import success_response, error_response
from utils.auth import require_auth, get_current_user
from api.search import init_search_services as reload_search

import traceback

sync_bp = Blueprint('sync', __name__)

# Global service
sync_service: Optional[DocumentSyncService] = None


# ❌ REMOVED: require_admin decorator - Next.js handles authorization


def init_sync_services():
    """Initialize sync services without Prisma"""
    global sync_service
    
    try:
        minio_fetcher = MinIOFetcher()
        embedding_service = EmbeddingService()
        bm25_service = BM25Service()
        cost_tracker = CostTracker()
        
        sync_service = DocumentSyncService(
            minio_fetcher=minio_fetcher,
            embedding_service=embedding_service,
            bm25_service=bm25_service,
            cost_tracker=cost_tracker
        )
        
        print("✅ Sync services initialized")
        
    except Exception as e:
        print(f"❌ Error initializing sync services: {e}")
        import traceback
        traceback.print_exc()


@sync_bp.route('/sync', methods=['POST'])
@require_auth  # ✅ Just check JWT is valid
async def trigger_sync():
    """Trigger full document synchronization."""
    try:
        if not sync_service:
            return error_response("Sync service not initialized", 500)
        
        # Get user ID from auth context
        user = get_current_user()
        user_id = str(user.get('id', 'system')) if user and user.get('id') else 'system'
        
        print(f"🔄 Triggering full sync for user: {user_id}")
        
        # Run synchronization
        result = await sync_service.sync_all_documents(user_id)

        if result.get('success'):
            print("🔄 Reloading search services with new indices...")
            reload_search()
        
        return success_response(
            data=result,
            message="Document synchronization completed"
        )
            
    except Exception as e:
        print(f"❌ Sync error: {e}")
        traceback.print_exc()
        return error_response(f"Sync failed: {str(e)}", 500)


@sync_bp.route('/sync/status', methods=['GET'])
async def get_sync_status():
    """Get current synchronization status."""
    try:
        if not sync_service:
            return error_response("Sync service not initialized", 500)
        
        status = await sync_service.get_sync_status()
        
        return success_response(
            data=status,
            message="Sync status retrieved"
        )
        
    except Exception as e:
        print(f"❌ Sync status error: {e}")
        traceback.print_exc()
        return error_response(f"Failed to get sync status: {str(e)}", 500)


@sync_bp.route('/sync/incremental', methods=['POST'])
@require_auth  # ✅ Just check JWT is valid
async def trigger_incremental_sync():
    """Trigger incremental sync for specific documents."""
    try:
        if not sync_service:
            return error_response("Sync service not initialized", 500)
        
        data = request.get_json()
        doc_ids = data.get('document_ids', [])
        
        if not doc_ids:
            return error_response("No document IDs provided", 400)
        
        # Get user ID from auth context
        user = get_current_user()
        user_id = str(user.get('id', 'system')) if user and user.get('id') else 'system'
        
        print(f"🔄 Triggering incremental sync for {len(doc_ids)} documents")
        
        result = await sync_service.sync_incremental(doc_ids, user_id)
        
        return success_response(
            data=result,
            message=f"Incremental sync completed for {len(doc_ids)} documents"
        )
            
    except Exception as e:
        print(f"❌ Incremental sync error: {e}")
        traceback.print_exc()
        return error_response(f"Incremental sync failed: {str(e)}", 500)


@sync_bp.route('/sync/rebuild', methods=['POST'])
# @require_auth  # ✅ Just check JWT is valid
async def rebuild_indices():
    """Rebuild all indices from scratch."""
    try:
        if not sync_service:
            return error_response("Sync service not initialized", 500)
        
        # Get user ID from auth context
        user = get_current_user()
        user_id = str(user.get('id', 'system')) if user and user.get('id') else 'system'
        
        print(f"🔨 Rebuilding indices for user: {user_id}")
        
        result = await sync_service.rebuild_indices(user_id)

        if result.get('success'):
            print("🔄 Reloading search services with new indices...")
            reload_search()
        
        return success_response(
            data=result,
            message="Index rebuild completed"
        )
            
    except Exception as e:
        print(f"❌ Rebuild error: {e}")
        traceback.print_exc()
        return error_response(f"Index rebuild failed: {str(e)}", 500)


@sync_bp.route('/sync/documents/count', methods=['GET'])
@require_auth  # ✅ Just check JWT is valid
async def get_document_counts():
    """Get document counts from all source tables."""
    try:
        from core.document_sources import DocumentSources
        doc_sources = DocumentSources()
        documents = await doc_sources.fetch_all_documents()
        
        return success_response(
            data={'count': len(documents)},
            message=f"Found {len(documents)} documents"
        )
        
    except Exception as e:
        print(f"❌ Document count error: {e}")
        traceback.print_exc()
        return error_response(f"Failed to count documents: {str(e)}", 500)


@sync_bp.route('/sync/health', methods=['GET'])
def sync_health_check():
    """Health check for sync service."""
    try:
        return success_response(
            data={
                'status': 'healthy',
                'sync_service': 'initialized' if sync_service else 'not initialized',
                'timestamp': datetime.now().isoformat()
            },
            message="Sync service is healthy"
        )
        
    except Exception as e:
        print(f"❌ Sync health check error: {e}")
        return error_response(f"Health check failed: {str(e)}", 500)