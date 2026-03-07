"""
Rebuild Vector Store Indices
Rebuilds FAISS and BM25 indices from existing documents in the database
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

from core.db import get_db
from core.document_sync_service import DocumentSyncService
from core.minio_fetcher import MinIOFetcher
from core.embedding_service import EmbeddingService
from core.bm25_service import BM25Service
from core.cost_tracker import CostTracker
from core.global_vector_store_manager import GlobalVectorStoreManager
from config import Config # pyright: ignore[reportAttributeAccessIssue]


class IndexRebuilder:
    """Rebuild FAISS and BM25 indices"""
    
    def __init__(self):
        self.minio_fetcher = None
        self.embedding_service = None
        self.bm25_service = None
        self.cost_tracker = None
        self.sync_service = None
    
    async def initialize_services(self):
        """Initialize all required services"""
        print("\n" + "="*70)
        print("🔨 REBUILD VECTOR STORE INDICES")
        print("="*70)
        
        # Initialize database pool
        print("\n1️⃣  Initializing database connection...")
        await get_db().initialize(Config.DATABASE_URL)
        
        # Initialize MinIO fetcher
        print("2️⃣  Initializing MinIO fetcher...")
        self.minio_fetcher = MinIOFetcher(
            endpoint=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
            access_key=os.getenv('MINIO_ACCESS_KEY', ''),
            secret_key=os.getenv('MINIO_SECRET_KEY', ''),
            bucket_name=os.getenv('MINIO_BUCKET', 'coreiq-documents'),
            secure=os.getenv('MINIO_SECURE', 'false').lower() == 'true'
        )
        
        # Initialize embedding service
        print("3️⃣  Initializing embedding service...")
        self.embedding_service = EmbeddingService()
        
        # Initialize BM25 service
        print("4️⃣  Initializing BM25 service...")
        self.bm25_service = BM25Service()
        
        # Initialize cost tracker
        print("5️⃣  Initializing cost tracker...")
        self.cost_tracker = CostTracker()
        
        # Initialize sync service
        print("6️⃣  Initializing document sync service...")
        self.sync_service = DocumentSyncService(
            minio_fetcher=self.minio_fetcher,
            embedding_service=self.embedding_service,
            bm25_service=self.bm25_service,
            cost_tracker=self.cost_tracker
        )
        
        print("\n✅ All services initialized successfully")
    
    async def backup_existing_indices(self) -> dict:
        """Backup existing indices before rebuilding"""
        print("\n💾 Backing up existing indices...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_info = {
            'timestamp': timestamp,
            'vector_store': None,
            'bm25': None
        }
        
        # Backup FAISS vector store
        vs_path = Path(Config.VECTOR_STORE_PATH) / 'global'
        if vs_path.exists():
            backup_vs_path = Path(Config.VECTOR_STORE_PATH) / f'global_backup_{timestamp}'
            
            try:
                import shutil
                shutil.copytree(vs_path, backup_vs_path)
                backup_info['vector_store'] = str(backup_vs_path)
                print(f"   ✅ Vector store backed up to: {backup_vs_path}")
            except Exception as e:
                print(f"   ⚠️  Vector store backup failed: {e}")
        else:
            print("   ℹ️  No existing vector store to backup")
        
        # Backup BM25 index
        bm25_path = Path(Config.BASE_DIR) / 'data' / 'bm25' / 'global'
        if bm25_path.exists():
            backup_bm25_path = Path(Config.BASE_DIR) / 'data' / 'bm25' / f'global_backup_{timestamp}'
            
            try:
                import shutil
                shutil.copytree(bm25_path, backup_bm25_path)
                backup_info['bm25'] = str(backup_bm25_path)
                print(f"   ✅ BM25 index backed up to: {backup_bm25_path}")
            except Exception as e:
                print(f"   ⚠️  BM25 backup failed: {e}")
        else:
            print("   ℹ️  No existing BM25 index to backup")
        
        return backup_info
    
    async def delete_existing_indices(self):
        """Delete existing indices"""
        print("\n🗑️  Deleting existing indices...")
        
        # Delete FAISS vector store
        if not self.embedding_service:
            print("   ⚠️  Embedding service not initialized")
            return
        
        vs_manager = GlobalVectorStoreManager(embeddings=self.embedding_service.embeddings)
        if vs_manager.exists():
            vs_manager.delete()
            print("   ✅ Vector store deleted")
        else:
            print("   ℹ️  No vector store to delete")
        
        # Delete BM25 index
        bm25_path = Path(Config.BASE_DIR) / 'data' / 'bm25' / 'global'
        if bm25_path.exists():
            import shutil
            shutil.rmtree(bm25_path)
            print("   ✅ BM25 index deleted")
        else:
            print("   ℹ️  No BM25 index to delete")
    
    async def get_index_stats(self) -> dict:
        """Get statistics about existing indices"""
        print("\n📊 Getting index statistics...")
        
        stats = {
            'vector_store': None,
            'bm25': None,
            'database_documents': 0
        }
        
        # Vector store stats
        if not self.embedding_service:
            print("   ⚠️  Embedding service not initialized")
            return stats
        
        vs_manager = GlobalVectorStoreManager(embeddings=self.embedding_service.embeddings)
        if vs_manager.exists():
            try:
                vs_stats = vs_manager.get_stats()
                stats['vector_store'] = vs_stats
                print(f"   FAISS: {vs_stats.get('vector_count', 0)} vectors, {vs_stats.get('document_count', 0)} docs")
            except Exception as e:
                print(f"   ⚠️  Could not get vector store stats: {e}")
        else:
            print("   FAISS: Not found")
        
        # BM25 stats
        bm25_path = Path(Config.BASE_DIR) / 'data' / 'bm25' / 'global'
        if (bm25_path / 'corpus.pkl').exists():
            try:
                import pickle
                with open(bm25_path / 'corpus.pkl', 'rb') as f:
                    corpus = pickle.load(f)
                doc_count = len(corpus) if corpus else 0
                stats['bm25'] = {'document_count': doc_count}
                print(f"   BM25: {doc_count} documents")
            except Exception as e:
                print(f"   ⚠️  Could not get BM25 stats: {e}")
        else:
            print("   BM25: Not found")
        
        # ✅ NEW: Database document count from GMP documents in reference DB
        try:
            import asyncpg
            
            ref_db_url = os.getenv('REFERENCE_DATABASE_URL')
            if ref_db_url:
                ref_conn = await asyncpg.connect(ref_db_url)
                try:
                    doc_count = await ref_conn.fetchval(
                        "SELECT COUNT(*) FROM \"GMPDocument\" WHERE filename IS NOT NULL"
                    )
                    stats['database_documents'] = doc_count or 0
                    print(f"   Database (GMP): {stats['database_documents']} documents")
                finally:
                    await ref_conn.close()
            else:
                print("   ⚠️  REFERENCE_DATABASE_URL not configured")
                stats['database_documents'] = 0
                
        except Exception as e:
            print(f"   ⚠️  Could not get database document count: {e}")
            stats['database_documents'] = 0
        
        # 🔕 COMMENTED OUT: Old table queries
        # query = """
        # SELECT 
        #     (SELECT COUNT(*) FROM documents WHERE file_url IS NOT NULL) +
        #     (SELECT COUNT(*) FROM ttd_documents WHERE file_url IS NOT NULL) +
        #     (SELECT COUNT(*) FROM packaging_trial_documents WHERE file_url IS NOT NULL) as total
        # """
        # doc_count = await get_db.fetchval(query)
        # stats['database_documents'] = doc_count or 0
        # print(f"   Database: {stats['database_documents']} documents")
        
        return stats
    
    async def confirm_rebuild(self, force: bool = False) -> bool:
        """Ask user to confirm rebuild operation"""
        if force:
            return True
        
        print("\n⚠️  WARNING: This will REBUILD all indices from scratch!")
        print("   Existing indices will be backed up, then deleted and recreated.")
        print("   This operation may take several minutes and incur embedding costs.")
        
        stats = await self.get_index_stats()
        
        if stats['database_documents'] == 0:
            print("\n❌ No documents found in database. Nothing to rebuild.")
            return False
        
        response = input("\n❓ Do you want to continue? (yes/no): ").strip().lower()
        return response in ['yes', 'y']
    
    async def rebuild(self, admin_user_id: str = 'system') -> dict:
        """Execute the rebuild"""
        print("\n" + "="*70)
        print("🔨 STARTING INDEX REBUILD")
        print("="*70)
        
        start_time = datetime.now()
        
        try:
            # Validate services are initialized
            if not self.sync_service:
                raise RuntimeError("Document sync service not initialized")
            
            # Backup existing indices
            backup_info = await self.backup_existing_indices()
            
            # Delete existing indices
            await self.delete_existing_indices()
            
            # Run full sync
            print("\n🔄 Syncing documents and rebuilding indices...")
            result = await self.sync_service.sync_all_documents(user_id=admin_user_id)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "="*70)
            print("✅ INDEX REBUILD COMPLETE")
            print("="*70)
            
            print(f"\n⏱️  Duration: {duration:.1f} seconds")
            print(f"\n📊 RESULTS:")
            print(f"   ✅ Documents processed: {result.get('documents_processed', 0)}")
            print(f"   ❌ Documents failed: {result.get('documents_failed', 0)}")
            print(f"   📦 Total chunks: {result.get('total_chunks', 0)}")
            
            if 'embedding_cost_inr' in result:
                print(f"   💰 Embedding cost: ₹{result['embedding_cost_inr']:.2f}")
            
            result['duration_seconds'] = duration
            result['backup_info'] = backup_info
            
            return result
            
        except Exception as e:
            print(f"\n❌ Rebuild failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'documents_processed': 0,
                'documents_failed': 0,
                'total_chunks': 0
            }
    
    async def verify_rebuild(self) -> bool:
        """Verify that rebuild was successful"""
        print("\n🔍 Verifying rebuild...")
        
        stats = await self.get_index_stats()
        
        success = True
        
        # Check vector store
        if stats['vector_store']:
            vector_count = stats['vector_store'].get('vector_count', 0)
            if vector_count > 0:
                print(f"   ✅ FAISS index: {vector_count} vectors")
            else:
                print("   ❌ FAISS index is empty!")
                success = False
        else:
            print("   ❌ FAISS index not found!")
            success = False
        
        # Check BM25
        if stats['bm25']:
            doc_count = stats['bm25'].get('document_count', 0)
            if doc_count > 0:
                print(f"   ✅ BM25 index: {doc_count} documents")
            else:
                print("   ❌ BM25 index is empty!")
                success = False
        else:
            print("   ❌ BM25 index not found!")
            success = False
        
        if success:
            print("\n✅ Verification passed! Indices rebuilt successfully.")
        else:
            print("\n❌ Verification failed! Some indices are missing or empty.")
        
        return success
    
    async def cleanup(self):
        """Cleanup services"""
        print("\n🧹 Cleaning up...")
        await get_db().close()
        print("✅ Cleanup complete")


async def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Rebuild RAG vector store indices')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup step')
    parser.add_argument('--admin-id', type=str, default='system', help='Admin user ID for cost tracking')
    args = parser.parse_args()
    
    rebuilder = IndexRebuilder()
    
    try:
        # Initialize
        await rebuilder.initialize_services()
        
        # Confirm
        if not await rebuilder.confirm_rebuild(force=args.force):
            print("\n❌ Rebuild cancelled by user")
            return
        
        # Rebuild
        result = await rebuilder.rebuild(admin_user_id=args.admin_id)
        
        if result:
            # Verify
            success = await rebuilder.verify_rebuild()
            
            if success:
                print("\n🎉 Index rebuild completed successfully!")
            else:
                print("\n⚠️  Rebuild completed but verification failed")
        else:
            print("\n❌ Rebuild failed")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await rebuilder.cleanup()


if __name__ == '__main__':
    asyncio.run(main())