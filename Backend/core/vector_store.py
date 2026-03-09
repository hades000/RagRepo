"""
FAISS vector store management for document embeddings
"""
import os
import json
from typing import List, Optional, Tuple
from pathlib import Path
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from config import Config


class VectorStoreManager:
    """Manage FAISS vector stores for users"""
    
    def __init__(self, user_id: str, embeddings: Embeddings):
        self.user_id = user_id
        self.embeddings = embeddings
        self.store_path = Config.get_vector_store_path(user_id)
        self.index_file = self.store_path / "index.faiss"
        self.pkl_file = self.store_path / "index.pkl"
        self.metadata_file = self.store_path / "metadata.json"
    
    def exists(self) -> bool:
        """Check if vector store exists for user"""
        return (
            self.index_file.exists() and 
            self.pkl_file.exists()
        )
    
    def create(self, documents: List[Document]) -> FAISS:
        """
        Create new vector store from documents.
        
        Args:
            documents: List of Document objects to index
        
        Returns:
            FAISS vector store instance
        """
        if not documents:
            raise ValueError("Cannot create vector store with empty documents")
        
        print(f"Creating vector store for user {self.user_id} with {len(documents)} documents")
        
        vector_store = FAISS.from_documents(documents, self.embeddings)
        self.save(vector_store, documents)
        
        return vector_store
    
    def load(self) -> Tuple[FAISS, List[dict]]:
        """
        Load existing vector store.
        
        Returns:
            Tuple of (FAISS instance, metadata list)
        
        Raises:
            FileNotFoundError: If vector store doesn't exist
        """
        if not self.exists():
            raise FileNotFoundError(f"No vector store found for user {self.user_id}")
        
        print(f"Loading vector store for user {self.user_id}")
        
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
    
    def add_documents(self, vector_store: FAISS, documents: List[Document]) -> FAISS:
        """
        Add new documents to existing vector store.
        
        Args:
            vector_store: Existing FAISS instance
            documents: New documents to add
        
        Returns:
            Updated FAISS instance
        """
        print(f"Adding {len(documents)} documents to vector store for user {self.user_id}")
        
        vector_store.add_documents(documents)
        
        # Update metadata
        new_metadata = [doc.metadata for doc in documents]
        existing_metadata = []
        
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                existing_metadata = json.load(f)
        
        all_metadata = existing_metadata + new_metadata
        
        with open(self.metadata_file, 'w') as f:
            json.dump(all_metadata, f, indent=2)
        
        # Save updated store
        vector_store.save_local(str(self.store_path))
        
        return vector_store
    
    def save(self, vector_store: FAISS, documents: List[Document]):
        """
        Save vector store to disk.
        
        Args:
            vector_store: FAISS instance to save
            documents: Documents for metadata extraction
        """
        print(f"Saving vector store for user {self.user_id}")
        
        # Save FAISS index
        vector_store.save_local(str(self.store_path))
        
        # Save metadata
        metadata = [doc.metadata for doc in documents]
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def delete(self):
        """Delete vector store for user"""
        import shutil
        
        if self.store_path.exists():
            shutil.rmtree(self.store_path)
            print(f"🗑️ Deleted vector store for user {self.user_id}")
    
    def search(
        self, 
        vector_store: FAISS, 
        query: str, 
        k: int = None
    ) -> List[Document]:
        """
        Search vector store for similar documents.
        
        Args:
            vector_store: FAISS instance
            query: Query string
            k: Number of results (default from config)
        
        Returns:
            List of similar Document objects
        """
        k = k or Config.MAX_CONTEXT_CHUNKS
        return vector_store.similarity_search(query, k=k)
    
    def search_with_scores(
        self, 
        vector_store: FAISS, 
        query: str, 
        k: int = None
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
        k = k or Config.MAX_CONTEXT_CHUNKS
        return vector_store.similarity_search_with_score(query, k=k)