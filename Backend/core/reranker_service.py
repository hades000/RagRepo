"""
Reranker service using CrossEncoder for neural reranking
"""
from typing import List, Tuple
from langchain.schema import Document

try:
    from sentence_transformers import CrossEncoder
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    print("⚠️ sentence-transformers not installed. Reranking will not be available.")


class RerankerService:
    """Neural reranking service using CrossEncoder"""
    
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        Initialize reranker.
        
        Args:
            model_name: HuggingFace model name for cross-encoder
        """
        self.model_name = model_name
        self.model: CrossEncoder = None
        self.is_loaded = False
    
    def load_model(self) -> bool:
        """
        Load the CrossEncoder model.
        
        Returns:
            True if successful
        """
        if not RERANKER_AVAILABLE:
            print("❌ Reranker unavailable - sentence-transformers not installed")
            return False
        
        try:
            print(f"📥 Loading reranker model: {self.model_name}")
            self.model = CrossEncoder(self.model_name)
            self.is_loaded = True
            print(f"✅ Reranker model loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error loading reranker model: {e}")
            self.is_loaded = False
            return False
    
    def rerank(
        self, 
        query: str, 
        documents: List[Document], 
        top_k: int = 5
    ) -> List[Document]:
        """
        Rerank documents using CrossEncoder.
        
        Args:
            query: Search query
            documents: List of candidate documents
            top_k: Number of top results to return
            
        Returns:
            Reranked list of documents
        """
        if not self.is_loaded:
            print("⚠️ Reranker not loaded, attempting to load...")
            if not self.load_model():
                print("⚠️ Reranking failed, returning original order")
                return documents[:top_k]
        
        if not documents:
            return []
        
        # If fewer documents than top_k, return all
        if len(documents) <= top_k:
            return documents
        
        try:
            print(f"🔄 Reranking {len(documents)} documents to top {top_k}")
            
            # Create query-document pairs (truncate content for speed)
            pairs = [
                [query, doc.page_content[:512]] 
                for doc in documents
            ]
            
            # Score all pairs
            scores = self.model.predict(pairs)
            
            # Sort by score (higher is better)
            doc_scores = list(zip(documents, scores))
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return top k documents
            reranked_docs = [doc for doc, score in doc_scores[:top_k]]
            
            print(f"✅ Reranking complete, returning top {len(reranked_docs)} documents")
            return reranked_docs
            
        except Exception as e:
            print(f"❌ Reranking error: {e}")
            return documents[:top_k]
    
    def rerank_with_scores(
        self, 
        query: str, 
        documents: List[Document], 
        top_k: int = 5
    ) -> List[Tuple[Document, float]]:
        """
        Rerank documents and return with scores.
        
        Args:
            query: Search query
            documents: List of candidate documents
            top_k: Number of top results to return
            
        Returns:
            List of (document, score) tuples
        """
        if not self.is_loaded:
            if not self.load_model():
                return [(doc, 0.0) for doc in documents[:top_k]]
        
        if not documents:
            return []
        
        try:
            # Create query-document pairs
            pairs = [
                [query, doc.page_content[:512]] 
                for doc in documents
            ]
            
            # Score all pairs
            scores = self.model.predict(pairs)
            
            # Sort by score
            doc_scores = list(zip(documents, scores))
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            return doc_scores[:top_k]
            
        except Exception as e:
            print(f"❌ Reranking error: {e}")
            return [(doc, 0.0) for doc in documents[:top_k]]