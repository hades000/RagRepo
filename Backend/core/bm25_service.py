"""
BM25 service for keyword-based document retrieval
"""
import pickle
import string
from pathlib import Path
from typing import List, Dict, Tuple
from langchain.schema import Document
from rank_bm25 import BM25Okapi
import numpy as np

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    
    # Download stopwords if not already available
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    
    STOPWORDS = set(stopwords.words('english'))
    stemmer = PorterStemmer()
    NLTK_AVAILABLE = True
except ImportError:
    # Fallback stopwords if NLTK unavailable
    STOPWORDS = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                 'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                 'can', 'could', 'may', 'might', 'must', 'shall'}
    stemmer = None
    NLTK_AVAILABLE = False


class BM25Service:
    """BM25 keyword-based search service"""
    
    def __init__(self, index_path: Path = None): # pyright: ignore[reportArgumentType]
        """
        Initialize BM25 service.
        
        Args:
            index_path: Path to save/load BM25 index
        """
        if index_path is None:
            from config import Config
            index_path = Config.BASE_DIR / 'data' / 'bm25' / 'global'
        self.index_path = index_path
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.bm25_index: BM25Okapi = None # pyright: ignore[reportAttributeAccessIssue]
        self.documents: List[Document] = []
        self.tokenized_corpus: List[List[str]] = []
    
    @staticmethod
    def preprocess_text(text: str) -> List[str]:
        """
        Preprocess text for BM25 indexing.
        
        Args:
            text: Input text
            
        Returns:
            List of preprocessed tokens
        """
        # Remove punctuation and lowercase
        text = text.translate(str.maketrans('', '', string.punctuation)).lower()
        
        # Tokenize
        tokens = text.split()
        
        # Remove stopwords
        tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
        
        # Apply stemming if available
        if stemmer and NLTK_AVAILABLE:
            tokens = [stemmer.stem(t) for t in tokens]
        
        return tokens
    
    def build_index(self, documents: List[Document]) -> bool:
        """
        Build BM25 index from document chunks.
        
        Args:
            documents: List of Document objects with page_content
            
        Returns:
            True if successful
        """
        if not documents:
            print("❌ No documents provided for BM25 indexing")
            return False
        
        try:
            print(f"🔨 Building BM25 index with {len(documents)} documents...")
            
            self.documents = documents
            self.tokenized_corpus = [
                self.preprocess_text(doc.page_content) 
                for doc in documents
            ]
            
            # Build BM25 index
            self.bm25_index = BM25Okapi(self.tokenized_corpus)
            
            print(f"✅ BM25 index built with {len(self.tokenized_corpus)} tokenized chunks")
            return True
            
        except Exception as e:
            print(f"❌ Error building BM25 index: {e}")
            return False
    
    def save_index(self) -> bool:
        """
        Save BM25 index to disk.
        
        Returns:
            True if successful
        """
        try:
            index_file = self.index_path / 'bm25_index.pkl'
            docs_file = self.index_path / 'bm25_documents.pkl'
            corpus_file = self.index_path / 'tokenized_corpus.pkl'
            
            with open(index_file, 'wb') as f:
                pickle.dump(self.bm25_index, f)
            
            with open(docs_file, 'wb') as f:
                pickle.dump(self.documents, f)
            
            with open(corpus_file, 'wb') as f:
                pickle.dump(self.tokenized_corpus, f)
            
            print(f"✅ BM25 index saved to {self.index_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving BM25 index: {e}")
            return False
    
    def load_index(self) -> bool:
        """
        Load BM25 index from disk.
        
        Returns:
            True if successful
        """
        try:
            index_file = self.index_path / 'bm25_index.pkl'
            docs_file = self.index_path / 'bm25_documents.pkl'
            corpus_file = self.index_path / 'tokenized_corpus.pkl'
            
            if not all([index_file.exists(), docs_file.exists(), corpus_file.exists()]):
                print("⚠️ BM25 index files not found")
                return False
            
            with open(index_file, 'rb') as f:
                self.bm25_index = pickle.load(f)
            
            with open(docs_file, 'rb') as f:
                self.documents = pickle.load(f)
            
            with open(corpus_file, 'rb') as f:
                self.tokenized_corpus = pickle.load(f)
            
            print(f"✅ BM25 index loaded from {self.index_path}")
            print(f"   Documents: {len(self.documents)}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading BM25 index: {e}")
            return False
        
    def create_index(self, texts: List[str], documents: List[Document]) -> bool:
        """
        Create BM25 index from texts and documents.
        
        This is a wrapper for build_index that accepts both texts and documents.
        
        Args:
            texts: List of text strings (ignored, we extract from documents)
            documents: List of Document objects
            
        Returns:
            True if successful
        """
        # Use the documents list (texts parameter is redundant)
        return self.build_index(documents)
    
    def index_exists(self) -> bool:
        """
        Check if BM25 index exists on disk.
        
        Returns:
            True if index files exist
        """
        bm25_file = self.index_path / 'bm25_index.pkl'
        corpus_file = self.index_path / 'tokenized_corpus.pkl'
        docs_file = self.index_path / 'bm25_documents.pkl'
        
        return bm25_file.exists() and corpus_file.exists() and docs_file.exists()
    
    def delete_index(self) -> bool:
        """
        Delete BM25 index from disk.
        
        Returns:
            True if successful
        """
        try:
            import shutil
            if self.index_path.exists():
                shutil.rmtree(self.index_path)
                self.index_path.mkdir(parents=True, exist_ok=True)
                print("🗑️ BM25 index deleted")
            return True
        except Exception as e:
            print(f"❌ Error deleting BM25 index: {e}")
            return False
    
    def search(self, query: str, top_k: int = 20) -> List[Tuple[Document, float]]:
        """
        Search using BM25.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (document, score) tuples
        """
        if not self.bm25_index or not self.documents:
            print("⚠️ BM25 index not initialized")
            return []
        
        try:
            # Preprocess query
            tokenized_query = self.preprocess_text(query)
            
            if not tokenized_query:
                print("⚠️ Query produced no tokens after preprocessing")
                return []
            
            # Get BM25 scores for all documents
            scores = self.bm25_index.get_scores(tokenized_query)
            
            # Get top k indices
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            # Return documents with scores
            results = [
                (self.documents[idx], float(scores[idx]))
                for idx in top_indices
                if scores[idx] > 0  # Only return documents with positive scores
            ]
            
            print(f"🔍 BM25 search returned {len(results)} results")
            return results
            
        except Exception as e:
            print(f"❌ BM25 search error: {e}")
            return []
    
    def add_documents(self, new_documents: List[Document]) -> bool:
        """
        Add new documents to existing index.
        
        Args:
            new_documents: Documents to add
            
        Returns:
            True if successful
        """
        try:
            self.documents.extend(new_documents)
            
            # Re-tokenize all documents
            self.tokenized_corpus = [
                self.preprocess_text(doc.page_content) 
                for doc in self.documents
            ]
            
            # Rebuild index
            self.bm25_index = BM25Okapi(self.tokenized_corpus)
            
            print(f"✅ Added {len(new_documents)} documents to BM25 index")
            return True
            
        except Exception as e:
            print(f"❌ Error adding documents to BM25 index: {e}")
            return False