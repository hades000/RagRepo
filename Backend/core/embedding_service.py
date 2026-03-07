"""
Embedding service for document and query vectorization
"""
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings
from langchain.schema import Document
from openai import api_key
from config import Config # pyright: ignore[reportAttributeAccessIssue]
from pydantic.v1 import SecretStr


class EmbeddingService:
    """Service for generating embeddings"""
    
    def __init__(self, provider: str = 'openai', model: str = None): # pyright: ignore[reportArgumentType]
        self.provider = provider
        self.model = model or Config.DEFAULT_EMBEDDING_MODEL
        self._embeddings: Optional[Embeddings] = None
    
    def initialize(self) -> Embeddings:
        """Initialize embeddings based on provider"""
        if self.provider == 'openai':

            api_key_value = SecretStr(Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None

            self._embeddings = OpenAIEmbeddings(
                model=self.model,
                api_key=api_key_value
            )
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")
        
        return self._embeddings
    

    
    @property
    def embeddings(self) -> Embeddings:
        """Get embeddings instance"""
        if self._embeddings is None:
            self.initialize()
        assert self._embeddings is not None
        return self._embeddings
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        if self._embeddings is None:
            self.initialize()
        assert self._embeddings is not None
        return self._embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        if self._embeddings is None:
            self.initialize()
        assert self._embeddings is not None
        return self._embeddings.embed_query(text)
    

    async def create_vector_store(self, documents: List[Document]):
        """
        Create FAISS vector store from documents.
        
        Args:
            documents: List of Document objects
            
        Returns:
            FAISS vector store
        """
        from langchain_community.vectorstores import FAISS
        
        print(f"🔢 Creating embeddings for {len(documents)} documents...")
        
        # FAISS.from_documents is synchronous, but we mark as async for consistency
        vector_store = FAISS.from_documents(documents, self.embeddings)
        
        print(f"✅ Vector store created successfully")
        return vector_store
    
    @property
    def model_name(self) -> str:
        """Get the model name"""
        return self.model


def get_embeddings_from_settings(settings: dict) -> Embeddings:
    """
    Create embeddings instance from user settings.
    
    Args:
        settings: Dictionary with 'embedding' key containing provider and model
    
    Returns:
        Initialized embeddings instance
    """
    embed_config = settings.get('embedding', {})
    provider = embed_config.get('provider', 'openai')
    model = embed_config.get('model', Config.DEFAULT_EMBEDDING_MODEL)
    
    embedding_service = EmbeddingService(provider, model)
    return embedding_service.embeddings

