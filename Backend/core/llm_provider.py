"""
LLM provider abstraction layer
"""
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from config import Config
from pydantic.v1 import SecretStr


class LLMProvider:
    """LLM provider manager"""
    
    def __init__(self, provider: str = 'openai', model: Optional[str] = None, temperature: float = 0.0):
        self.provider = provider
        self.model = model or Config.DEFAULT_LLM_MODEL
        self.temperature = temperature
        self._llm: Optional[BaseChatModel] = None
    
    def initialize(self) -> BaseChatModel:
        """Initialize LLM based on provider"""
        if self.provider == 'openai':

            api_key_value = SecretStr(Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
            self._llm = ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                api_key=api_key_value
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
        return self._llm
    
    @property
    def llm(self) -> BaseChatModel:
        """Get LLM instance"""
        if self._llm is None:
            self.initialize()
        assert self._llm is not None, "LLM initialization failed"
        return self._llm
    
    def generate(self, prompt: str) -> str:
        """Generate response from LLM"""
        if self._llm is None:
            self.initialize()
        
        assert self._llm is not None, "LLM initialization failed"
        response = self._llm.invoke(prompt)
        
        # Handle different content types
        content = response.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Convert list to string representation
            return " ".join(str(item) for item in content)
        else:
            return str(content)


def get_llm_from_settings(settings: Dict[str, Any]) -> BaseChatModel:
    """
    Create LLM instance from user settings.
    
    Args:
        settings: Dictionary with 'llm' key containing provider, model, temperature
    
    Returns:
        Initialized LLM instance
    """
    llm_config = settings.get('llm', {})
    provider = llm_config.get('provider', 'openai')
    model = llm_config.get('model', Config.DEFAULT_LLM_MODEL)
    temperature = llm_config.get('temperature', Config.DEFAULT_LLM_TEMPERATURE)
    
    llm_provider = LLMProvider(provider, model, temperature)
    return llm_provider.llm