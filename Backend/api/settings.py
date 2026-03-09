"""
Settings API endpoints - model configuration and available models
"""
from fastapi import APIRouter

router = APIRouter()

# Models actually supported by the RAG service
AVAILABLE_LLM_PROVIDERS = {
    "openai": {
        "label": "OpenAI",
        "models": [
            {"value": "gpt-4", "label": "GPT-4"},
            {"value": "gpt-4o", "label": "GPT-4o"},
            {"value": "gpt-4o-mini", "label": "GPT-4o Mini"},
            {"value": "gpt-4-turbo", "label": "GPT-4 Turbo"},
            {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo"},
        ]
    },
    "anthropic": {
        "label": "Anthropic",
        "models": [
            {"value": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet"},
            {"value": "claude-3-opus-20240229", "label": "Claude 3 Opus"},
            {"value": "claude-3-haiku-20240307", "label": "Claude 3 Haiku"},
        ]
    }
}

AVAILABLE_EMBEDDING_MODELS = [
    {"value": "text-embedding-3-small", "label": "text-embedding-3-small (OpenAI)"},
    {"value": "text-embedding-3-large", "label": "text-embedding-3-large (OpenAI)"},
    {"value": "text-embedding-ada-002", "label": "text-embedding-ada-002 (OpenAI)"},
]


@router.get('/models/available')
def get_available_models():
    """Return all models supported by this RAG service."""
    return {
        "llmProviders": AVAILABLE_LLM_PROVIDERS,
        "embeddingModels": AVAILABLE_EMBEDDING_MODELS,
    }
