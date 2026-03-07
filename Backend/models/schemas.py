"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role enum"""
    USER = "user"
    ASSISTANT = "assistant"


# ============= Document Schemas =============

class DocumentUploadResponse(BaseModel):
    """Response for document upload"""
    success: bool
    message: str
    document_id: str
    filename: str
    chunks_created: int
    file_size: int


class DocumentListItem(BaseModel):
    """Document list item"""
    id: str
    filename: str
    upload_timestamp: datetime
    file_size: Optional[int]
    processing_status: str


class DocumentDeleteRequest(BaseModel):
    """Request to delete document"""
    document_id: str


# ============= Chat Schemas =============

class ChatQueryRequest(BaseModel):
    """Request for chat query"""
    query: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None


class SourceChunk(BaseModel):
    """Source document chunk"""
    content: str
    filename: str
    page: Optional[int] = None


class ChatQueryResponse(BaseModel):
    """Response for chat query"""
    answer: str
    sources: List[SourceChunk]
    session_id: str
    message_id: str


class ChatSession(BaseModel):
    """Chat session"""
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ChatMessage(BaseModel):
    """Chat message"""
    id: str
    role: MessageRole
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    """Chat history response"""
    session: ChatSession
    messages: List[ChatMessage]


# ============= Settings Schemas =============

class LLMSettings(BaseModel):
    """LLM configuration"""
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = Field(0.0, ge=0.0, le=2.0)


class EmbeddingSettings(BaseModel):
    """Embedding configuration"""
    provider: str = "openai"
    model: str = "text-embedding-3-small"


class UserSettings(BaseModel):
    """User settings"""
    llm: LLMSettings
    embedding: EmbeddingSettings


class SettingsUpdateRequest(BaseModel):
    """Request to update settings"""
    llm: Optional[LLMSettings] = None
    embedding: Optional[EmbeddingSettings] = None


# ============= Stats Schemas =============

class StatsResponse(BaseModel):
    """Statistics response"""
    doc_count: int
    total_documents_size: int  # in bytes