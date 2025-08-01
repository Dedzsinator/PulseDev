from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import asyncpg
import redis.asyncio as redis
import uuid
import json
import os
from contextlib import asynccontextmanager

# Import services and models
from config import Config
from models.events import ContextEvent, EventType, Agent
from api.routes import router
from api.gamification_routes import router as gamification_router
from services.ai_service import AIService
from services.git_service import GitService
from services.flow_service import FlowService
from services.energy_service import EnergyService

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"
    features: list = ["ccm", "ai", "git", "flow", "energy"]

# Global connections
db_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[redis.Redis] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_pool, redis_client
    
    # Initialize PostgreSQL connection
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/pulsedev_ccm")
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    
    # Initialize Redis connection
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    # Initialize database schema
    await init_database()
    
    print("🚀 CCM API started successfully")
    
    yield
    
    # Shutdown
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()

app = FastAPI(
    title="PulseDev+ Cognitive Context Mirror API",
    description="Captures and analyzes developer context",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db():
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not initialized")
    async with db_pool.acquire() as connection:
        yield connection

async def get_redis():
    if not redis_client:
        raise HTTPException(status_code=500, detail="Redis not initialized")
    return redis_client

async def init_database():
    """Initialize database schema"""
    if not db_pool:
        return
        
    async with db_pool.acquire() as conn:
        # Create TimescaleDB extension if not exists
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
        except Exception as e:
            print(f"TimescaleDB extension not available: {e}")
        
        # Create context events table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS context_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id VARCHAR(255) NOT NULL,
                agent VARCHAR(50) NOT NULL,
                type VARCHAR(100) NOT NULL,
                payload JSONB NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        
        # Create hypertable for time-series data (TimescaleDB)
        try:
            await conn.execute("""
                SELECT create_hypertable('context_events', 'timestamp', 
                    if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 hour');
            """)
        except Exception as e:
            print(f"Hypertable creation skipped: {e}")
        
        # Create indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_context_events_session 
            ON context_events (session_id, timestamp DESC);
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_context_events_agent 
            ON context_events (agent, timestamp DESC);
        """)

# Include API routes
app.include_router(router, prefix="/api/v1")
app.include_router(gamification_router)

# Include SCRUM routes
from api.scrum_routes import router as scrum_router
app.include_router(scrum_router, prefix="/api/v1")

# Initialize services
Config.validate()

# ... keep existing code (database initialization, dependencies, and legacy endpoints)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)