"""
Document source abstraction for multi-table document fetching using asyncpg
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
# from .db import db_pool
import os


@dataclass
class DocumentMetadata:
    """Unified document metadata structure"""
    id: str
    filename: str
    file_url: str
    source_table: str  # 'Document', 'TtdDocument', 'PackagingTrialDocument', 'GMPDocument'
    upload_timestamp: datetime
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    project_name: Optional[str] = None
    product_name: Optional[str] = None
    sku_name: Optional[str] = None
    additional_metadata: Optional[Dict] = None
    category_info: Optional[Dict] = None  # For GMP documents


class DocumentSources:
    """Fetch documents from multiple database tables"""
    
    def __init__(self):
        """Initialize document sources"""
        # Get reference database URL from environment
        self.reference_db_url = os.getenv('REFERENCE_DATABASE_URL')
        self.main_db_url = os.getenv('DATABASE_URL')
    
    async def fetch_all_documents(self) -> List[DocumentMetadata]:
        """
        Fetch all documents from all source tables.
        
        Returns:
            List of DocumentMetadata objects
        """
        documents = []

        documents.extend(await self._fetch_search_documents())
        
        documents.extend(await self._fetch_gmp_documents())
        
        # 🔕 COMMENTED OUT: Existing tables
        # # Fetch from Document table
        # documents.extend(await self._fetch_main_documents())
        # 
        # # Fetch from TtdDocument table
        # documents.extend(await self._fetch_ttd_documents())
        # 
        # # Fetch from PackagingTrialDocument table
        # documents.extend(await self._fetch_packaging_documents())
        
        print(f"📚 Fetched {len(documents)} documents total")
        return documents

    async def _fetch_search_documents(self) -> List[DocumentMetadata]:
        """Fetch SEARCH_DOC documents uploaded via admin panel from main database"""
        try:
            import asyncpg
            
            if not self.main_db_url:
                print("⚠️ Main database URL not configured")
                return []
            
            print("📖 Fetching SEARCH_DOC documents from main database...")
            
            conn = await asyncpg.connect(self.main_db_url)
            
            try:
                query = """
                    SELECT 
                        d.id,
                        d.name,
                        d.url,
                        d."fileType",
                        d.description,
                        d."uploadedBy",
                        d."createdAt"
                    FROM "Document" d
                    WHERE d.type = 'SEARCH_DOC'
                      AND d.url IS NOT NULL
                    ORDER BY d."createdAt" DESC
                """
                
                rows = await conn.fetch(query)
                
                documents = []
                for row in rows:
                    file_url = row['url']
                    
                    if not file_url:
                        continue
                    
                    doc = DocumentMetadata(
                        id=f"search_{row['id']}",
                        filename=row['name'] or file_url.split('/')[-1],
                        file_url=file_url,
                        source_table='SearchDocument',
                        upload_timestamp=row['createdAt'],
                        file_size=None,
                        content_type=row['fileType'] or 'application/pdf',
                        project_name=None,
                        product_name=None,
                        sku_name=None,
                        additional_metadata={
                            'source': 'search_documents',
                            'document_type': 'Search Document',
                            'database': 'main',
                            'uploaded_by': row['uploadedBy'],
                            'description': row['description'],
                        }
                    )
                    documents.append(doc)
                
                print(f"🔍 Fetched {len(documents)} SEARCH_DOC documents from main database")
                return documents
                
            finally:
                await conn.close()
                
        except Exception as e:
            print(f"❌ Error fetching SEARCH_DOC documents: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _fetch_gmp_documents(self) -> List[DocumentMetadata]:
        """Fetch GMP documents from reference database"""
        try:
            import asyncpg
            
            if not self.reference_db_url:
                print("⚠️ Reference database URL not configured")
                return []
            
            print("📖 Connecting to reference database for GMP documents...")
            
            ref_conn = await asyncpg.connect(self.reference_db_url)
            
            try:
                query = """
                    SELECT 
                        gd.id,
                        gd.filename,
                        gd."uploadedAt",
                        gd."categoryId",
                        pc.product_category,
                        pc.product_sub_category,
                        pc.product_sub_sub_category,
                        pc."gmpDocumentPath",
                        pc.gmppdfurl,
                        pc.regulatorypdfurl,
                        pc.fssaicompodium
                    FROM "GMPDocument" gd
                    INNER JOIN product_categories pc ON gd."categoryId" = pc.id
                    WHERE gd.filename IS NOT NULL
                    ORDER BY gd."uploadedAt" DESC
                """
                
                rows = await ref_conn.fetch(query)
                
                documents = []
                for row in rows:
                    # ✅ FIXED: Use the filename from GMPDocument table as the file_url
                    # The filename already contains the full S3 object key
                    file_url = row['filename']
                    
                    if not file_url:
                        print(f"⚠️ Skipping GMP document {row['filename']} - no file URL")
                        continue
                    
                    doc = DocumentMetadata(
                        id=f"gmp_{row['id']}",
                        filename=row['filename'],
                        file_url=file_url,  # This is the S3 object key
                        source_table='GMPDocument',
                        upload_timestamp=row['uploadedAt'], 
                        file_size=None,
                        content_type='application/pdf',
                        project_name=None,
                        product_name=row['product_category'],
                        sku_name=None,
                        category_info={
                            'category_id': row['categoryId'],
                            'product_category': row['product_category'],
                            'product_sub_category': row['product_sub_category'],
                            'product_sub_sub_category': row['product_sub_sub_category'],
                            'gmp_pdf_url': row['gmppdfurl'],
                            'regulatory_pdf_url': row['regulatorypdfurl'],
                            'fssai_compendium': row['fssaicompodium']
                        },
                        additional_metadata={
                            'source': 'gmp_documents',
                            'document_type': 'GMP Document',
                            'database': 'reference'
                        }
                    )
                    documents.append(doc)
                
                print(f"📘 Fetched {len(documents)} GMP documents from reference database")
                return documents
                
            finally:
                await ref_conn.close()
                
        except Exception as e:
            print(f"❌ Error fetching GMP documents: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    # 🔕 COMMENTED OUT: Main documents table
    # async def _fetch_main_documents(self) -> List[DocumentMetadata]:
    #     """Fetch documents from main Document table"""
    #     try:
    #         query = """
    #             SELECT 
    #                 d.id,
    #                 d.filename,
    #                 d.file_url,
    #                 d.file_size,
    #                 d.created_at,
    #                 d.file_type,
    #                 p.name as project_name,
    #                 prod.name as product_name
    #             FROM documents d
    #             LEFT JOIN product_workflows pw ON d.product_workflow_id = pw.id
    #             LEFT JOIN products prod ON pw.product_id = prod.id
    #             LEFT JOIN projects p ON d.project_id = p.id
    #             WHERE d.file_url IS NOT NULL
    #             ORDER BY d.created_at DESC
    #         """
    #         
    #         rows = await db_pool.fetch(query)
    #         
    #         documents = []
    #         for row in rows:
    #             doc = DocumentMetadata(
    #                 id=row['id'],
    #                 filename=row['filename'],
    #                 file_url=row['file_url'],
    #                 source_table='Document',
    #                 upload_timestamp=row['created_at'],
    #                 file_size=row['file_size'],
    #                 content_type=row['file_type'],
    #                 project_name=row['project_name'],
    #                 product_name=row['product_name'],
    #                 additional_metadata={
    #                     'source': 'main_documents'
    #                 }
    #             )
    #             documents.append(doc)
    #         
    #         print(f"📄 Fetched {len(documents)} main documents")
    #         return documents
    #         
    #     except Exception as e:
    #         print(f"❌ Error fetching main documents: {e}")
    #         return []
    
    # 🔕 COMMENTED OUT: TTD documents table
    # async def _fetch_ttd_documents(self) -> List[DocumentMetadata]:
    #     """Fetch documents from TtdDocument table"""
    #     try:
    #         query = """
    #             SELECT 
    #                 td.id,
    #                 td.filename,
    #                 td.file_url,
    #                 td.file_size,
    #                 td.created_at,
    #                 p.name as project_name
    #             FROM ttd_documents td
    #             LEFT JOIN projects p ON td.project_id = p.id
    #             WHERE td.file_url IS NOT NULL
    #             ORDER BY td.created_at DESC
    #         """
    #         
    #         rows = await db_pool.fetch(query)
    #         
    #         documents = []
    #         for row in rows:
    #             doc = DocumentMetadata(
    #                 id=row['id'],
    #                 filename=row['filename'],
    #                 file_url=row['file_url'],
    #                 source_table='TtdDocument',
    #                 upload_timestamp=row['created_at'],
    #                 file_size=row['file_size'],
    #                 project_name=row['project_name'],
    #                 additional_metadata={
    #                     'source': 'ttd_documents',
    #                     'document_type': 'Technical Transfer Document'
    #                 }
    #             )
    #             documents.append(doc)
    #         
    #         print(f"📋 Fetched {len(documents)} TTD documents")
    #         return documents
    #         
    #     except Exception as e:
    #         print(f"❌ Error fetching TTD documents: {e}")
    #         return []
    
    # 🔕 COMMENTED OUT: Packaging trial documents table
    # async def _fetch_packaging_documents(self) -> List[DocumentMetadata]:
    #     """Fetch documents from PackagingTrialDocument table"""
    #     try:
    #         query = """
    #             SELECT 
    #                 ptd.id,
    #                 ptd.filename,
    #                 ptd.file_url,
    #                 ptd.file_size,
    #                 ptd.created_at,
    #                 pt.trial_number,
    #                 d.doe_number,
    #                 s.name as sku_name,
    #                 prod.name as product_name,
    #                 p.name as project_name
    #             FROM packaging_trial_documents ptd
    #             LEFT JOIN packaging_trials pt ON ptd.trial_id = pt.id
    #             LEFT JOIN does d ON pt.doe_id = d.id
    #             LEFT JOIN skus s ON d.sku_id = s.id
    #             LEFT JOIN products prod ON s.product_id = prod.id
    #             LEFT JOIN projects p ON prod.project_id = p.id
    #             WHERE ptd.file_url IS NOT NULL
    #             ORDER BY ptd.created_at DESC
    #         """
    #         
    #         rows = await db_pool.fetch(query)
    #         
    #         documents = []
    #         for row in rows:
    #             doc = DocumentMetadata(
    #                 id=row['id'],
    #                 filename=row['filename'],
    #                 file_url=row['file_url'],
    #                 source_table='PackagingTrialDocument',
    #                 upload_timestamp=row['created_at'],
    #                 file_size=row['file_size'],
    #                 project_name=row['project_name'],
    #                 product_name=row['product_name'],
    #                 sku_name=row['sku_name'],
    #                 additional_metadata={
    #                     'source': 'packaging_trial_documents',
    #                     'trial_number': row['trial_number'],
    #                     'doe_number': row['doe_number'],
    #                     'document_type': 'Packaging Trial'
    #                 }
    #             )
    #             documents.append(doc)
    #         
    #         print(f"📦 Fetched {len(documents)} packaging documents")
    #         return documents
    #         
    #     except Exception as e:
    #         print(f"❌ Error fetching packaging documents: {e}")
    #         return []
    
    async def fetch_document_by_id(
        self, 
        doc_id: str, 
        source_table: str
    ) -> Optional[DocumentMetadata]:
        """
        Fetch a specific document by ID and source table.
        
        Args:
            doc_id: Document ID
            source_table: Source table name
            
        Returns:
            DocumentMetadata or None
        """
        if source_table == 'GMPDocument':
            docs = await self._fetch_gmp_documents()
            for doc in docs:
                if doc.id == doc_id:
                    return doc
        
        # 🔕 COMMENTED OUT: Other source tables
        # if source_table == 'Document':
        #     docs = await self._fetch_main_documents()
        # elif source_table == 'TtdDocument':
        #     docs = await self._fetch_ttd_documents()
        # elif source_table == 'PackagingTrialDocument':
        #     docs = await self._fetch_packaging_documents()
        # else:
        #     print(f"❌ Unknown source table: {source_table}")
        #     return None
        # 
        # # Find matching document
        # for doc in docs:
        #     if doc.id == doc_id:
        #         return doc
        
        return None
    
    async def get_document_count(self) -> Dict[str, int]:
        """
        Get document count from each source.
        
        Returns:
            Dictionary with counts per source
        """
        try:
            import asyncpg
            
            gmp_count = 0
            search_count = 0
            
            # Count SEARCH_DOC from main DB
            if self.main_db_url:
                main_conn = await asyncpg.connect(self.main_db_url)
                try:
                    search_count = await main_conn.fetchval(
                        "SELECT COUNT(*) FROM \"Document\" WHERE type = 'SEARCH_DOC' AND url IS NOT NULL"
                    )
                finally:
                    await main_conn.close()
            
            if self.reference_db_url:
                ref_conn = await asyncpg.connect(self.reference_db_url)
                try:
                    gmp_count = await ref_conn.fetchval(
                        "SELECT COUNT(*) FROM \"GMPDocument\" WHERE filename IS NOT NULL"
                    )
                finally:
                    await ref_conn.close()
            
            total = (gmp_count or 0) + (search_count or 0)
            
            return {
                'SearchDocument': search_count or 0,
                'GMPDocument': gmp_count or 0,
                'total': total
            }
            
        except Exception as e:
            print(f"❌ Error getting document count: {e}")
            return {
                'SearchDocument': 0,
                'GMPDocument': 0,
                'total': 0
            }