import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration management for GraphQL Direct MCP Server."""
    
    # GraphQL Configuration
    GRAPHQL_ENDPOINT: str = os.getenv("GRAPHQL_ENDPOINT", "https://api.example.com/graphql")
    GRAPHQL_TIMEOUT: int = int(os.getenv("GRAPHQL_TIMEOUT", "30"))
    
    # Query Limits
    MAX_RESPONSE_SIZE: int = int(os.getenv("MAX_RESPONSE_SIZE", "5000"))  # characters
    SCHEMA_CACHE_TTL: int = int(os.getenv("SCHEMA_CACHE_TTL", "3600"))    # seconds
    
    # Server Configuration
    SERVER_NAME: str = "graphql-direct-mcp"
    SERVER_VERSION: str = "1.0.0"
    
    # Security
    KEYRING_SERVICE: str = "graphql-direct-mcp"
    KEYRING_USERNAME: str = "api_token"
    
    # Rate Limiting
    MAX_QUERIES_PER_MINUTE: int = int(os.getenv("MAX_QUERIES_PER_MINUTE", "100"))
    
    # Schema Configuration
    INTROSPECTION_ENABLED: bool = os.getenv("INTROSPECTION_ENABLED", "true").lower() == "true"
    INCLUDE_DEPRECATED: bool = os.getenv("INCLUDE_DEPRECATED", "false").lower() == "true"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings."""
        required_vars = ["GRAPHQL_ENDPOINT"]
        missing = [var for var in required_vars if not getattr(cls, var)]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        # Validate GraphQL endpoint format
        if not cls.GRAPHQL_ENDPOINT.startswith(("http://", "https://")):
            raise ValueError("GRAPHQL_ENDPOINT must be a valid HTTP(S) URL")
        
        return True 