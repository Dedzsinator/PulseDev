import os
from typing import Optional

class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/pulsedev_ccm")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # AI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # openai, ollama
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4")
    
    # Security
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")  # 32-byte key for AES-256
    SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-key")
    
    # Features
    AUTO_COMMIT_ENABLED = os.getenv("AUTO_COMMIT_ENABLED", "true").lower() == "true"
    FLOW_DETECTION_ENABLED = os.getenv("FLOW_DETECTION_ENABLED", "true").lower() == "true"
    ENERGY_SCORING_ENABLED = os.getenv("ENERGY_SCORING_ENABLED", "true").lower() == "true"
    
    # Thresholds
    STUCK_STATE_THRESHOLD_MINUTES = int(os.getenv("STUCK_STATE_THRESHOLD_MINUTES", "10"))
    FLOW_IDLE_THRESHOLD_SECONDS = int(os.getenv("FLOW_IDLE_THRESHOLD_SECONDS", "300"))
    INTENT_DRIFT_THRESHOLD = float(os.getenv("INTENT_DRIFT_THRESHOLD", "0.7"))
    
    # Git
    DEFAULT_GIT_REPO_PATH = os.getenv("DEFAULT_GIT_REPO_PATH", ".")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if cls.AI_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
        
        if not cls.ENCRYPTION_KEY:
            print("Warning: ENCRYPTION_KEY not set, using development key")
            cls.ENCRYPTION_KEY = b"dev-key-32-bytes-long-for-testing"

# Dependency functions for API routes
async def get_db_connection():
    """Get database connection from main app"""
    from main import db_pool
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not initialized")
    async with db_pool.acquire() as connection:
        yield connection

async def get_redis_connection():
    """Get Redis connection from main app"""
    from main import redis_client
    if not redis_client:
        raise HTTPException(status_code=500, detail="Redis not initialized")
    return redis_client