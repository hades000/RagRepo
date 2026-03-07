"""
Global FAISS vector store management for all documents
"""
import os
import json
from typing import List, Optional, Tuple
from pathlib import Path
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from config import Config


class GlobalVectorStoreManager:
    """Manage global FAISS vector store for all documents"""
    
    def __init__(self, embeddings: Embeddings):
        """
        Initialize global vector store manager.
        
        Args:
            embeddings: Embeddings instance for vector store
        """
        self.embeddings = embeddings
        self.store_path = Path(Config.VECTOR_STORE_PATH) / "global"
        self.index_file = self.store_path / "index.faiss"
        self.pkl_file = self.store_path / "index.pkl"
        self.metadata_file = self.store_path / "metadata.json"
        
        # Ensure directory exists
        self.store_path.mkdir(parents=True, exist_ok=True)
    
    def exists(self) -> bool:
        """Check if global vector store exists"""
        return (
            self.index_file.exists() and 
            self.pkl_file.exists()
        )
    
    def create(self, documents: List[Document]) -> FAISS:
        """
        Create new global vector store from documents.
        
        Args:
            documents: List of Document objects to index
        
        Returns:
            FAISS vector store instance
        """
        if not documents:
            raise ValueError("Cannot create vector store with empty documents")
        
        print(f"📊 Creating global vector store with {len(documents)} documents")
        
        vector_store = FAISS.from_documents(documents, self.embeddings)
        self.save(vector_store, documents)
        
        return vector_store
    
    def load(self) -> Tuple[FAISS, List[dict]]:
        """
        Load existing global vector store.
        
        Returns:
            Tuple of (FAISS instance, metadata list)
        
        Raises:
            FileNotFoundError: If vector store doesn't exist
        """
        if not self.exists():
            raise FileNotFoundError("No global vector store found")
        
        print("📂 Loading global vector store")
        
        vector_store = FAISS.load_local(
            str(self.store_path),
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Load metadata
        metadata = []
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
        
        return vector_store, metadata
    
    def save(self, vector_store: FAISS, documents: List[Document]):
        """
        Save global vector store to disk.
        
        Args:
            vector_store: FAISS instance to save
            documents: Documents for metadata extraction
        """
        print("💾 Saving global vector store")
        
        # Save FAISS index
        vector_store.save_local(str(self.store_path))
        
        # Save metadata
        metadata = [doc.metadata for doc in documents]
        with open(self.metadata_file, 'w') as f:
            import json
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Saved {len(documents)} documents to global vector store")
    
    def delete(self):
        """Delete global vector store"""
        
        
        if self.store_path.exists():
            import shutil
            shutil.rmtree(self.store_path)
            print("🗑️ Deleted global vector store")
    
    def get_stats(self) -> dict:
        """
        Get statistics about the global vector store.
        
        Returns:
            Dictionary with statistics
        """
        if not self.exists():
            return {
                'exists': False,
                'document_count': 0,
                'index_size_mb': 0
            }
        
        # Count documents from metadata
        doc_count = 0
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                import json
                metadata = json.load(f)
                doc_count = len(metadata)
        
        # Get index file size
        index_size = self.index_file.stat().st_size / (1024 * 1024)  # MB
        if self.index_file.exists():
            index_size = self.index_file.stat().st_size / (1024 * 1024)  # MB
        
        return {
            'exists': True,
            'document_count': doc_count,
            'index_size_mb': round(index_size, 2),
            'path': str(self.store_path)
        }
    
    def search(
        self, 
        vector_store: FAISS, 
        query: str, 
        k: int = 10
    ) -> List[Document]:
        """
        Search global vector store for similar documents.
        
        Args:
            vector_store: FAISS instance
            query: Query string
            k: Number of results
        
        Returns:
            List of similar Document objects
        """
        return vector_store.similarity_search(query, k=k)
    
    def search_with_scores(
        self, 
        vector_store: FAISS, 
        query: str, 
        k: int = 10
    ) -> List[Tuple[Document, float]]:
        """
        Search with similarity scores.
        
        Args:
            vector_store: FAISS instance
            query: Query string
            k: Number of results
        
        Returns:
            List of (Document, score) tuples
        """
        return vector_store.similarity_search_with_score(query, k=k)