import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration management for Basic API Wrapper MCP Server."""
    
    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://api.example.com")
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    
    # Server Configuration
    SERVER_NAME: str = "basic-api-wrapper"
    SERVER_VERSION: str = "1.0.0"
    
    # Security
    KEYRING_SERVICE: str = "basic-api-wrapper"
    KEYRING_USERNAME: str = "api_token"
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings."""
        required_vars = ["API_BASE_URL"]
        missing = [var for var in required_vars if not getattr(cls, var)]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True 