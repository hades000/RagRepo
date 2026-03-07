"""
Configuration management for RAG application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

__all__ = ['Config', 'DEFAULT_USER_SETTINGS']

class Config:
    """Application configuration"""
    
    # ============= Flask Settings =============
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # ============= Database =============
    DATABASE_URL = os.getenv('DATABASE_URL')
    REFERENCE_DATABASE_URL = os.getenv('REFERENCE_DATABASE_URL')
    
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required")
    
    if not REFERENCE_DATABASE_URL:
        raise ValueError("REFERENCE_DATABASE_URL environment variable is required")
    
    # ============= File Storage =============
    BASE_DIR = Path(__file__).parent
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    VECTOR_STORE_PATH = BASE_DIR / 'data' / 'vector_stores'
    
    # Create directories if they don't exist
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)
    
    # File upload settings
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'pdf', 'txt'}
    
    # ============= LLM Provider =============
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Default LLM settings
    DEFAULT_LLM_MODEL = 'gpt-4o-mini'  # Cost-effective option
    DEFAULT_LLM_TEMPERATURE = 0.0
    
    # ============= Embedding Provider =============
    EMBEDDING_PROVIDER = os.getenv('EMBEDDING_PROVIDER', 'openai')
    DEFAULT_EMBEDDING_MODEL = 'text-embedding-3-small'  # Cost-effective
    
    # Validate OpenAI key if using OpenAI
    if LLM_PROVIDER == 'openai' or EMBEDDING_PROVIDER == 'openai':
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
    
    # ============= RAG Settings =============
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 150
    MAX_CONTEXT_CHUNKS = 5  # Number of chunks to retrieve
    
    # ============= Chat Settings =============
    MAX_HISTORY_MESSAGES = 10  # Store last 10 messages in context
    
    # ============= CORS Settings =============
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:3001',
        os.getenv('NEXT_PUBLIC_URL', 'http://localhost:3000')
    ]
    
    # ============= Logging =============
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def get_vector_store_path(user_id: str) -> Path:
        """Get vector store path for specific user"""
        user_path = Config.VECTOR_STORE_PATH / user_id
        user_path.mkdir(parents=True, exist_ok=True)
        return user_path
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# Default user settings structure
DEFAULT_USER_SETTINGS = {
    'llm': {
        'provider': 'gemini',
        'model': 'gemini-2.5-flash',
        'temperature': 0.0
    },
    'embedding': {
        'provider': 'openai',
        'model': 'text-embedding-ada-002'
    }
}