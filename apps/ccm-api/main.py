from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import redis.asyncio as redis
import json
import uuid
import os
from contextlib import asynccontextmanager

# Models
class ContextEvent(BaseModel):
    sessionId: str = Field(..., description="Session identifier")
    agent: str = Field(..., description="Context agent (file, editor, terminal, git)")
    type: str = Field(..., description="Event type")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    timestamp: str = Field(..., description="ISO timestamp")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "0.1.0"

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

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/context/events")
async def create_context_event(
    event: ContextEvent,
    db: asyncpg.Connection = Depends(get_db),
    redis_conn: redis.Redis = Depends(get_redis)
):
    """Store a context event"""
    try:
        # Store in PostgreSQL
        event_id = str(uuid.uuid4())
        await db.execute("""
            INSERT INTO context_events (id, session_id, agent, type, payload, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, event_id, event.sessionId, event.agent, event.type, 
            json.dumps(event.payload), datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')))
        
        # Cache recent events in Redis (last 100 events per session)
        cache_key = f"session:{event.sessionId}:recent"
        event_data = {
            "id": event_id,
            "agent": event.agent,
            "type": event.type,
            "payload": event.payload,
            "timestamp": event.timestamp
        }
        
        await redis_conn.lpush(cache_key, json.dumps(event_data))
        await redis_conn.ltrim(cache_key, 0, 99)  # Keep only last 100 events
        await redis_conn.expire(cache_key, 86400)  # 24 hour expiry
        
        return {"status": "success", "event_id": event_id}
        
    except Exception as e:
        print(f"Error storing context event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store event: {str(e)}")

@app.get("/context/recent")
async def get_recent_context(
    hours: int = 1,
    session_id: Optional[str] = None,
    agent: Optional[str] = None,
    db: asyncpg.Connection = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get recent context events"""
    try:
        # Build query conditions
        conditions = ["timestamp > $1"]
        params = [datetime.utcnow() - timedelta(hours=hours)]
        param_count = 1
        
        if session_id:
            param_count += 1
            conditions.append(f"session_id = ${param_count}")
            params.append(session_id)
            
        if agent:
            param_count += 1
            conditions.append(f"agent = ${param_count}")
            params.append(agent)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT session_id, agent, type, payload, timestamp
            FROM context_events
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT 1000
        """
        
        rows = await db.fetch(query, *params)
        
        events = []
        for row in rows:
            events.append({
                "sessionId": row["session_id"],
                "agent": row["agent"],
                "type": row["type"],
                "payload": row["payload"],
                "timestamp": row["timestamp"].isoformat()
            })
            
        return events
        
    except Exception as e:
        print(f"Error fetching recent context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch context: {str(e)}")

@app.delete("/context/wipe")
async def wipe_context(
    session_id: Optional[str] = None,
    db: asyncpg.Connection = Depends(get_db),
    redis_conn: redis.Redis = Depends(get_redis)
):
    """Wipe context data"""
    try:
        if session_id:
            # Wipe specific session
            await db.execute("DELETE FROM context_events WHERE session_id = $1", session_id)
            await redis_conn.delete(f"session:{session_id}:recent")
        else:
            # Wipe all context data
            await db.execute("DELETE FROM context_events")
            # Clear all session caches
            keys = await redis_conn.keys("session:*:recent")
            if keys:
                await redis_conn.delete(*keys)
        
        return {"status": "success", "message": "Context data wiped"}
        
    except Exception as e:
        print(f"Error wiping context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to wipe context: {str(e)}")

@app.get("/context/stats")
async def get_context_stats(
    session_id: Optional[str] = None,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get context statistics"""
    try:
        base_query = """
            SELECT 
                agent,
                COUNT(*) as event_count,
                MIN(timestamp) as first_event,
                MAX(timestamp) as last_event
            FROM context_events
        """
        
        if session_id:
            query = base_query + " WHERE session_id = $1 GROUP BY agent"
            rows = await db.fetch(query, session_id)
        else:
            query = base_query + " GROUP BY agent"
            rows = await db.fetch(query)
        
        stats = {}
        for row in rows:
            stats[row["agent"]] = {
                "event_count": row["event_count"],
                "first_event": row["first_event"].isoformat(),
                "last_event": row["last_event"].isoformat()
            }
            
        return stats
        
    except Exception as e:
        print(f"Error fetching context stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)