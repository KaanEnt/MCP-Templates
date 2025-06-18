import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration management for Database-Enhanced MCP Server."""
    
    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://api.example.com")
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    
    # Database Configuration
    DB_PATH: Path = Path(os.getenv("DB_PATH", "data/analytics.duckdb"))
    MAX_QUERY_ROWS: int = int(os.getenv("MAX_QUERY_ROWS", "1000"))
    
    # Sync Configuration
    DEFAULT_SYNC_DAYS: int = int(os.getenv("DEFAULT_SYNC_DAYS", "30"))
    MAX_SYNC_DAYS: int = int(os.getenv("MAX_SYNC_DAYS", "365"))
    
    # Server Configuration
    SERVER_NAME: str = "database-enhanced-mcp"
    SERVER_VERSION: str = "1.0.0"
    
    # Security
    KEYRING_SERVICE: str = "database-enhanced-mcp"
    KEYRING_USERNAME: str = "api_token"
    
    # Company Configuration (for meeting type detection)
    COMPANY_DOMAIN: str = os.getenv("COMPANY_DOMAIN", "example.com")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings."""
        required_vars = ["API_BASE_URL", "COMPANY_DOMAIN"]
        missing = [var for var in required_vars if not getattr(cls, var)]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        # Ensure database directory exists
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        return True 