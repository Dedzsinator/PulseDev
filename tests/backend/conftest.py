"""
Pytest configuration for backend tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock
import os
import sys

# Add the apps directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'apps'))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_asyncpg_connection():
    """Mock asyncpg database connection"""
    connection = AsyncMock()
    connection.execute = AsyncMock()
    connection.fetch = AsyncMock()
    connection.fetchrow = AsyncMock()
    connection.fetchval = AsyncMock()
    return connection

@pytest.fixture
def mock_redis_connection():
    """Mock Redis connection"""
    redis = AsyncMock()
    redis.get = AsyncMock()
    redis.set = AsyncMock()
    redis.setex = AsyncMock()
    redis.lpush = AsyncMock()
    redis.ltrim = AsyncMock()
    redis.expire = AsyncMock()
    return redis

@pytest.fixture(autouse=True)
def env_setup():
    """Set up environment variables for testing"""
    os.environ.update({
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_pulsedev',
        'REDIS_URL': 'redis://localhost:6379/0',
        'ENCRYPTION_KEY': 'test-key-32-bytes-long-for-testing',
        'AI_PROVIDER': 'mock',
        'OPENAI_API_KEY': 'test-key'
    })
    
    yield
    
    # Clean up
    test_vars = ['DATABASE_URL', 'REDIS_URL', 'ENCRYPTION_KEY', 'AI_PROVIDER', 'OPENAI_API_KEY']
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]