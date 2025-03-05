from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings """
    # OpenRouter API settings
    OPENROUTER_API_KEY: str
    MODEL_NAME: str = "google/gemini-2.0-flash-exp:free"
    
    # Application settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Model parameters
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.3
    
    class Config:
        env_file = ".env"

# Create global settings instance
settings = Settings()