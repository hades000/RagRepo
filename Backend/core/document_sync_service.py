"""
Document synchronization service using asyncpg
"""
from typing import Dict, List, Optional
from pathlib import Path
import asyncio
from .document_sources import DocumentSources, DocumentMetadata
from .minio_fetcher import MinIOFetcher
from .embedding_service import EmbeddingService
from .bm25_service import BM25Service
from .cost_tracker import CostTracker
from .global_vector_store_manager import GlobalVectorStoreManager
from .document_processor import DocumentProcessor
# from .db import db_pool


class DocumentSyncService:
    """Orchestrate document synchronization from database to vector stores"""
    
    def __init__(
        self,
        minio_fetcher: MinIOFetcher,
        embedding_service: EmbeddingService,
        bm25_service: BM25Service,
        cost_tracker: CostTracker
    ):
        """
        Initialize sync service.
        
        Args:
            minio_fetcher: MinIO document fetcher
            embedding_service: Embedding service
            bm25_service: BM25 service
            cost_tracker: Cost tracking service
        """
        self.doc_sources = DocumentSources()
        self.minio_fetcher = minio_fetcher
        self.embedding_service = embedding_service
        self.bm25_service = bm25_service
        self.cost_tracker = cost_tracker
        self.doc_processor = DocumentProcessor()
        
        # Initialize vector store manager
        self.vs_manager = GlobalVectorStoreManager(
            embeddings=embedding_service.embeddings
        )
    
    async def sync_all_documents(self, user_id: str) -> Dict:
        """
        Sync all documents from database.
        
        Args:
            user_id: Admin user ID for cost tracking
            
        Returns:
            Sync results dictionary
        """
        print("\n" + "="*60)
        print("🔄 Starting full document synchronization")
        print("="*60)
        
        try:
            # Fetch all documents from database
            print("📚 Fetching documents from database...")
            documents = await self.doc_sources.fetch_all_documents()
            
            if not documents:
                return {
                    'success': True,
                    'message': 'No documents found in database',
                    'documents_processed': 0,
                    'documents_failed': 0
                }
            
            print(f"✅ Found {len(documents)} documents")
            
            # Process documents
            all_chunks = []
            all_texts = []
            processed_count = 0
            failed_count = 0
            total_tokens = 0
            
            for i, doc_meta in enumerate(documents, 1):
                print(f"\n[{i}/{len(documents)}] Processing: {doc_meta.filename}")
                
                try:
                    # Download from MinIO
                    content = await self.minio_fetcher.fetch_document(doc_meta.file_url)
                    
                    if not content:
                        print(f"⚠️ Could not fetch document from MinIO")
                        failed_count += 1
                        continue
                    
                    # Process document into chunks
                    chunks = self.doc_processor.process_document(
                        content=content,
                        filename=doc_meta.filename,
                        metadata={
                            'source': doc_meta.source_table,
                            'doc_id': doc_meta.id,
                            'project': doc_meta.project_name or 'Unknown',
                            'product': doc_meta.product_name or 'Unknown',
                            'sku': doc_meta.sku_name or 'Unknown',
                            'upload_date': doc_meta.upload_timestamp.isoformat(),
                            **(doc_meta.additional_metadata or {})
                        }
                    )
                    
                    if chunks:
                        all_chunks.extend(chunks)
                        all_texts.extend([chunk.page_content for chunk in chunks])
                        
                        # Estimate tokens
                        chunk_tokens = sum(
                            self.cost_tracker.estimate_tokens(chunk.page_content)
                            for chunk in chunks
                        )
                        total_tokens += chunk_tokens
                        
                        print(f"✅ Created {len(chunks)} chunks ({chunk_tokens} tokens)")
                        processed_count += 1
                    else:
                        print(f"⚠️ No chunks created")
                        failed_count += 1
                        
                except Exception as e:
                    print(f"❌ Error processing document: {e}")
                    failed_count += 1
                    continue
            
            if not all_chunks:
                return {
                    'success': False,
                    'message': 'No chunks created from documents',
                    'documents_processed': 0,
                    'documents_failed': failed_count
                }
            
            # Create vector store
            print(f"\n📊 Creating vector store with {len(all_chunks)} chunks...")
            vector_store = await self.embedding_service.create_vector_store(all_chunks)
            
            # Save vector store
            print("💾 Saving global vector store...")
            self.vs_manager.save(vector_store, all_chunks)
            
            # Create BM25 index
            print("🔍 Creating BM25 index...")
            self.bm25_service.create_index(all_texts, all_chunks)
            self.bm25_service.save_index()
            
            # Log cost
            print("💰 Logging embedding costs...")
            await self.cost_tracker.log_document_sync(
                user_id=user_id,
                document_count=processed_count,
                embedding_tokens=total_tokens,
                embedding_model=self.embedding_service.model_name
            )
            
            print("\n" + "="*60)
            print("✅ Synchronization complete!")
            print("="*60)
            
            return {
                'success': True,
                'message': 'Documents synchronized successfully',
                'documents_processed': processed_count,
                'documents_failed': failed_count,
                'total_chunks': len(all_chunks),
                'total_tokens': total_tokens,
                'sources': {
                    'Document': sum(1 for d in documents if d.source_table == 'Document'),
                    'TtdDocument': sum(1 for d in documents if d.source_table == 'TtdDocument'),
                    'PackagingTrialDocument': sum(1 for d in documents if d.source_table == 'PackagingTrialDocument')
                }
            }
            
        except Exception as e:
            print(f"\n❌ Sync error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'message': f'Synchronization failed: {str(e)}',
                'documents_processed': 0,
                'documents_failed': 0
            }
    
    async def get_sync_status(self) -> Dict:
        """
        Get current sync status.
        
        Returns:
            Status dictionary
        """
        try:
            # Check vector store
            vs_exists = self.vs_manager.exists()
            vs_stats = self.vs_manager.get_stats() if vs_exists else None
            
            # Check BM25 index
            bm25_exists = self.bm25_service.index_exists()
            
            # Get document counts
            doc_counts = await self.doc_sources.get_document_count()
            document_count = vs_stats.get('document_count', 0) if vs_stats else 0
            
            return {
                'indices_exist': vs_exists and bm25_exists,
                'has_bm25': bm25_exists,
                'has_vector_store': vs_exists,
                'document_count': document_count,
                'chunk_count': document_count,  # In this system, chunks = documents
                'last_sync': None,  # TODO: Store last sync timestamp
                
                # Keep additional details for debugging
                'database_documents': doc_counts,
                'ready_for_search': vs_exists and bm25_exists
            }
            
        except Exception as e:
            print(f"❌ Status check error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'indices_exist': False,
                'has_bm25': False,
                'has_vector_store': False,
                'document_count': 0,
                'chunk_count': 0,
                'ready_for_search': False,
                'error': str(e)
            }
    
    async def sync_incremental(self, doc_ids: List[str], user_id: str) -> Dict:
        """
        Sync specific documents (incremental update).
        
        Args:
            doc_ids: List of document IDs to sync
            user_id: Admin user ID
            
        Returns:
            Sync results
        """
        print(f"🔄 Incremental sync for {len(doc_ids)} documents")
        
        # For now, fall back to full sync
        # TODO: Implement true incremental sync with FAISS merge
        print("⚠️ Incremental sync not yet implemented, running full sync")
        return await self.sync_all_documents(user_id)
    
    async def rebuild_indices(self, user_id: str) -> Dict:
        """
        Rebuild all indices from scratch.
        
        Args:
            user_id: Admin user ID
            
        Returns:
            Rebuild results
        """
        print("🔨 Rebuilding all indices...")
        
        # Delete existing indices
        if self.vs_manager.exists():
            print("🗑️ Deleting old vector store...")
            self.vs_manager.delete()
        
        if self.bm25_service.index_exists():
            print("🗑️ Deleting old BM25 index...")
            self.bm25_service.delete_index()
        
        # Run full sync
        return await self.sync_all_documents(user_id)