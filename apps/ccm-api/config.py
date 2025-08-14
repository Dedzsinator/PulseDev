import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/pulsedev_ccm")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    # NVIDIA NIM Configuration (ONLY AI provider)
    NVIDIA_NIM_API_KEY = os.getenv("NVIDIA_NIM_API_KEY")
    NVIDIA_NIM_BASE_URL = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct")

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
        if not cls.NVIDIA_NIM_API_KEY:
            raise ValueError("NVIDIA_NIM_API_KEY is required")

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
