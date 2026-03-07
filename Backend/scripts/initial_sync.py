"""
Initial Document Synchronization Script
Syncs all documents from database (documents, ttd_documents, packaging_trial_documents) to FAISS/BM25
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

from core.db import get_db, init_db
from core.document_sync_service import DocumentSyncService
from core.minio_fetcher import MinIOFetcher
from core.embedding_service import EmbeddingService
from core.bm25_service import BM25Service
from core.cost_tracker import CostTracker
from config import Config # pyright: ignore[reportAttributeAccessIssue]


class InitialSyncOrchestrator:
    """Orchestrate initial document synchronization"""
    
    def __init__(self):
        self.minio_fetcher = None
        self.embedding_service = None
        self.bm25_service = None
        self.cost_tracker = None
        self.sync_service = None
    
    async def initialize_services(self):
        """Initialize all required services"""
        print("\n" + "="*70)
        print("🚀 INITIAL DOCUMENT SYNCHRONIZATION")
        print("="*70)
        
        # Initialize database pool
        print("\n1️⃣  Initializing database connection...")
        init_db()
        db = get_db()
        await db.initialize(Config.DATABASE_URL)
        
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
    
    async def check_existing_indices(self) -> dict:
        """Check if indices already exist"""
        print("\n🔍 Checking for existing indices...")
        
        if self.sync_service is None:
            raise RuntimeError("DocumentSyncService not initialized. Call initialize_services() first.")
        
        vs_manager = self.sync_service.vs_manager
        bm25_path = Path(Config.BASE_DIR) / 'data' / 'bm25' / 'global'
        
        vector_store_exists = vs_manager.exists()
        bm25_exists = (bm25_path / 'corpus.pkl').exists()
        
        status = {
            'vector_store': vector_store_exists,
            'bm25': bm25_exists
        }
        
        if vector_store_exists:
            print("   ✅ FAISS vector store exists")
        else:
            print("   ❌ FAISS vector store NOT found")
        
        if bm25_exists:
            print("   ✅ BM25 index exists")
        else:
            print("   ❌ BM25 index NOT found")
        
        return status
    
    async def get_document_count(self) -> int:
        """Get total document count from GMP documents in reference database"""
        try:
            import asyncpg
            
            ref_db_url = os.getenv('REFERENCE_DATABASE_URL')
            if not ref_db_url:
                print("⚠️ REFERENCE_DATABASE_URL not configured")
                return 0
            
            ref_conn = await asyncpg.connect(ref_db_url)
            try:
                count = await ref_conn.fetchval(
                    "SELECT COUNT(*) FROM \"GMPDocument\" WHERE filename IS NOT NULL"
                )
                return count or 0
            finally:
                await ref_conn.close()
                
        except Exception as e:
            print(f"⚠️ Error getting document count: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    async def confirm_sync(self, force: bool = False) -> bool:
        """Ask user to confirm sync operation"""
        if force:
            return True
        
        print("\n⚠️  WARNING: This will rebuild all indices from scratch!")
        print("   Existing FAISS and BM25 indices will be replaced.")
        
        doc_count = await self.get_document_count()
        print(f"\n📚 Total documents to sync: {doc_count}")
        
        if doc_count == 0:
            print("❌ No documents found in database. Aborting.")
            return False
        
        response = input("\n❓ Do you want to continue? (yes/no): ").strip().lower()
        return response in ['yes', 'y']
    
    async def run_sync(self, admin_user_id: str = 'system'):
        """Execute the synchronization"""
        print("\n" + "="*70)
        print("🔄 STARTING SYNCHRONIZATION")
        print("="*70)
        
        if self.sync_service is None:
            raise RuntimeError("DocumentSyncService not initialized. Call initialize_services() first.")
        
        try:
            result = await self.sync_service.sync_all_documents(user_id=admin_user_id)
            
            print("\n" + "="*70)
            print("✅ SYNCHRONIZATION COMPLETE")
            print("="*70)
            
            print(f"\n📊 RESULTS:")
            print(f"   ✅ Documents processed: {result.get('documents_processed', 0)}")
            print(f"   ❌ Documents failed: {result.get('documents_failed', 0)}")
            print(f"   📦 Total chunks: {result.get('total_chunks', 0)}")
            
            if 'embedding_cost_inr' in result:
                print(f"   💰 Embedding cost: ₹{result['embedding_cost_inr']:.2f}")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Synchronization failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def verify_indices(self):
        """Verify that indices were created successfully"""
        print("\n🔍 Verifying indices...")
        
        if self.sync_service is None:
            raise RuntimeError("DocumentSyncService not initialized. Call initialize_services() first.")
        
        status = await self.check_existing_indices()
        
        if status['vector_store'] and status['bm25']:
            print("✅ All indices created successfully!")
            
            # Get stats
            stats = self.sync_service.vs_manager.get_stats()
            print(f"\n📈 Index Statistics:")
            print(f"   Vector count: {stats.get('vector_count', 0)}")
            print(f"   Document count: {stats.get('document_count', 0)}")
            
            return True
        else:
            print("❌ Some indices are missing!")
            return False
    
    async def cleanup(self):
        """Cleanup services"""
        print("\n🧹 Cleaning up...")
        db = get_db()
        await db.close()
        print("✅ Cleanup complete")


async def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Initial RAG document synchronization')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--admin-id', type=str, default=None, 
                   help='Admin user ID for cost tracking (auto-detects if not provided)')
    args = parser.parse_args()
    
    orchestrator = InitialSyncOrchestrator()
    
    try:
        # Initialize
        await orchestrator.initialize_services()
        
        # Check existing indices
        await orchestrator.check_existing_indices()
        
        # Confirm
        if not await orchestrator.confirm_sync(force=args.force):
            print("\n❌ Synchronization cancelled by user")
            return
        
        # Run sync
        result = await orchestrator.run_sync(admin_user_id=args.admin_id)
        
        if result:
            # Verify
            success = await orchestrator.verify_indices()
            
            if success:
                print("\n🎉 Initial synchronization completed successfully!")
            else:
                print("\n⚠️  Synchronization completed but verification failed")
        else:
            print("\n❌ Synchronization failed")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await orchestrator.cleanup()


if __name__ == '__main__':
    asyncio.run(main())