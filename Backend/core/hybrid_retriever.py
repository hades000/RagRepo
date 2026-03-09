"""
Hybrid retriever combining semantic search (FAISS) and keyword search (BM25)
with optional neural reranking
"""
from typing import List, Tuple, Optional
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
import numpy as np

from .bm25_service import BM25Service
from .reranker_service import RerankerService


class HybridRetriever:
    """
    Hybrid retrieval combining:
    1. Semantic search (FAISS)
    2. Keyword search (BM25)
    3. Score normalization and combination
    4. Optional neural reranking
    """
    
    def __init__(
        self,
        vector_store: FAISS,
        bm25_service: BM25Service,
        reranker_service: Optional[RerankerService] = None,
        semantic_weight: float = 0.7,
        bm25_weight: float = 0.3
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            vector_store: FAISS vector store for semantic search
            bm25_service: BM25 service for keyword search
            reranker_service: Optional reranker service
            semantic_weight: Weight for semantic scores (0-1)
            bm25_weight: Weight for BM25 scores (0-1)
        """
        self.vector_store = vector_store
        self.bm25_service = bm25_service
        self.reranker_service = reranker_service
        
        # Ensure weights sum to 1
        total_weight = semantic_weight + bm25_weight
        self.semantic_weight = semantic_weight / total_weight
        self.bm25_weight = bm25_weight / total_weight
        
        print(f"🔀 Hybrid retriever initialized:")
        print(f"   Semantic weight: {self.semantic_weight:.2f}")
        print(f"   BM25 weight: {self.bm25_weight:.2f}")
        print(f"   Reranking: {'Enabled' if reranker_service else 'Disabled'}")
    
    @staticmethod
    def normalize_scores(scores: List[float]) -> List[float]:
        """
        Normalize scores to 0-1 range using min-max normalization.
        
        Args:
            scores: List of scores
            
        Returns:
            Normalized scores
        """
        if not scores:
            return []
        
        scores_array = np.array(scores)
        
        min_score = scores_array.min()
        max_score = scores_array.max()
        
        # Handle edge case where all scores are the same
        if max_score - min_score == 0:
            return [0.5] * len(scores)
        
        normalized = (scores_array - min_score) / (max_score - min_score)
        return normalized.tolist()
    
    def retrieve(
        self, 
        query: str, 
        k: int = 20,
        rerank: bool = True,
        final_k: int = 5
    ) -> List[Document]:
        """
        Perform hybrid retrieval.
        
        Pipeline:
        1. Semantic search → 20 candidates
        2. BM25 search → 20 candidates
        3. Normalize and combine scores (70% semantic, 30% BM25)
        4. Take top 15
        5. Rerank with CrossEncoder → top 5
        
        Args:
            query: Search query
            k: Number of candidates to retrieve from each method
            rerank: Whether to apply neural reranking
            final_k: Final number of results to return
            
        Returns:
            List of retrieved documents
        """
        # Stage 1: Semantic Search
        semantic_results = self._semantic_search(query, k)
        
        # Stage 2: BM25 Search
        bm25_results = self._bm25_search(query, k)
        
        # Stage 3: Combine and normalize scores
        combined_docs = self._combine_results(
            semantic_results, 
            bm25_results, 
            top_k=min(15, k)  # Take top 15 for reranking
        )
        
        # Stage 4: Optional reranking
        if rerank and self.reranker_service:
            print(f"🔄 Applying neural reranking to top {len(combined_docs)} documents")
            final_docs = self.reranker_service.rerank(query, combined_docs, top_k=final_k)
        else:
            final_docs = combined_docs[:final_k]
        
        print(f"✅ Hybrid retrieval complete: {len(final_docs)} final documents")
        return final_docs
    
    def _semantic_search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """
        Perform semantic search using FAISS.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of (document, distance) tuples
        """
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            print(f"🔍 Semantic search: {len(results)} results")
            return results
        except Exception as e:
            print(f"❌ Semantic search error: {e}")
            return []
    
    def _bm25_search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """
        Perform BM25 keyword search.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of (document, score) tuples
        """
        try:
            results = self.bm25_service.search(query, top_k=k)
            print(f"🔍 BM25 search: {len(results)} results")
            return results
        except Exception as e:
            print(f"❌ BM25 search error: {e}")
            return []
    
    def _combine_results(
        self, 
        semantic_results: List[Tuple[Document, float]],
        bm25_results: List[Tuple[Document, float]],
        top_k: int = 15
    ) -> List[Document]:
        """
        Combine and normalize scores from both retrievers.
        
        Args:
            semantic_results: Results from semantic search (doc, distance)
            bm25_results: Results from BM25 search (doc, score)
            top_k: Number of top results to return
            
        Returns:
            Combined list of documents sorted by combined score
        """
        # Normalize semantic scores (distances - lower is better, so invert)
        semantic_scores = [1 / (1 + dist) for doc, dist in semantic_results]
        normalized_semantic = self.normalize_scores(semantic_scores)
        
        # Normalize BM25 scores (higher is better)
        bm25_scores = [score for doc, score in bm25_results]
        normalized_bm25 = self.normalize_scores(bm25_scores)
        
        # Create document score map
        doc_scores = {}
        
        # Add semantic results
        for idx, (doc, _) in enumerate(semantic_results):
            doc_id = id(doc)
            doc_scores[doc_id] = {
                'doc': doc,
                'score': normalized_semantic[idx] * self.semantic_weight
            }
        
        # Add BM25 results
        for idx, (doc, _) in enumerate(bm25_results):
            doc_id = id(doc)
            bm25_contribution = normalized_bm25[idx] * self.bm25_weight
            
            if doc_id in doc_scores:
                # Document found by both methods - combine scores
                doc_scores[doc_id]['score'] += bm25_contribution
            else:
                # Document only found by BM25
                doc_scores[doc_id] = {
                    'doc': doc,
                    'score': bm25_contribution
                }
        
        # Sort by combined score
        sorted_results = sorted(
            doc_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        print(f"🔀 Combined {len(semantic_results)} semantic + {len(bm25_results)} BM25 results")
        print(f"   Unique documents: {len(doc_scores)}")
        print(f"   Returning top {top_k}")
        
        return [item['doc'] for item in sorted_results[:top_k]]