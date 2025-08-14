# Dependencies module to avoid circular imports
from fastapi import Depends, HTTPException
import asyncpg
import redis.asyncio as redis

# Global references to be set by main.py
db_pool = None
redis_client = None

def set_db_pool(pool):
    """Set database pool from main.py"""
    global db_pool
    db_pool = pool

def set_redis_client(client):
    """Set Redis client from main.py"""
    global redis_client
    redis_client = client

# Dependency functions
async def get_db():
    """Database dependency"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not initialized")
    async with db_pool.acquire() as connection:
        yield connection

async def get_redis():
    """Redis dependency (optional)"""
    return redis_client
