from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import redis.asyncio as redis
import json
import uuid

from models.events import (
    ContextEvent, AIPromptRequest, CommitSuggestion,
    BranchSuggestion, EventType, Agent
)
from services.ai_service import AIService
from services.git_service import GitService
from services.flow_service import FlowService
from services.energy_service import EnergyService
from dependencies import get_db, get_redis

# Initialize services
ai_service = AIService()
git_service = GitService()
flow_service = FlowService()
energy_service = EnergyService()

# Create router
router = APIRouter()

@router.post("/context/events")
async def create_context_event(
    event: ContextEvent,
    background_tasks: BackgroundTasks,
    db: asyncpg.Connection = Depends(get_db)
):
    """Store a context event and trigger analysis"""
    try:
        print(f"Debug: Received event for session {event.sessionId}")

        # Store in PostgreSQL
        event_id = str(uuid.uuid4())
        print(f"Debug: Storing event {event_id} in database")

        await db.execute("""
            INSERT INTO context_events (id, session_id, agent, type, payload, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, event_id, event.sessionId, event.agent.value, event.type.value,
            json.dumps(event.payload), datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')))

        print(f"Debug: Database insert successful")

        # Cache in Redis
        try:
            from dependencies import redis_client
            if redis_client is not None:
                cache_key = f"session:{event.sessionId}:recent"
                event_data = {
                    "id": event_id,
                    "agent": event.agent.value,
                    "type": event.type.value,
                    "payload": event.payload,
                    "timestamp": event.timestamp
                }

                await redis_client.lpush(cache_key, json.dumps(event_data))
                await redis_client.ltrim(cache_key, 0, 99)
                await redis_client.expire(cache_key, 86400)
                print("Debug: Redis operations successful")
            else:
                print("Debug: Redis not available, skipping cache")
        except Exception as redis_error:
            print(f"Debug: Redis error (non-fatal): {redis_error}")

        # Background analysis
        try:
            from dependencies import redis_client as redis_client_for_background
            background_tasks.add_task(analyze_event_context, event.sessionId, event_id, db, redis_client_for_background)
            print("Debug: Background task started")
        except Exception as bg_error:
            print(f"Debug: Background task error (non-fatal): {bg_error}")

        return {"status": "success", "event_id": event_id}

    except Exception as e:
        print(f"Error storing context event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store event: {str(e)}")

@router.post("/ai/prompt")
async def generate_ai_prompt(
    request: AIPromptRequest,
    db: asyncpg.Connection = Depends(get_db)
):
    """Generate AI prompt from context"""
    try:
        # Get recent events
        since_time = datetime.utcnow() - timedelta(minutes=request.context_window_minutes)

        query = """
            SELECT session_id, agent, type, payload, timestamp
            FROM context_events
            WHERE session_id = $1 AND timestamp > $2
            ORDER BY timestamp DESC
            LIMIT 1000
        """

        print(f"Debug AI: Executing query for session {request.session_id}")
        rows = await db.fetch(query, request.session_id, since_time)
        print(f"Debug AI: Found {len(rows)} rows")

        events = []
        for row in rows:
            # Handle JSONB payload from PostgreSQL - this is the key fix!
            payload = row["payload"]
            print(f"Debug AI: Raw payload: {payload}, type: {type(payload)}")

            # The issue: Pydantic validation happens BEFORE we can process the payload
            # We need to create the ContextEvent with raw data, not with parsed payload
            try:
                # Create a dictionary that matches ContextEvent structure
                event_data = {
                    "sessionId": row["session_id"],
                    "agent": row["agent"],  # Keep as string, let Pydantic convert
                    "type": row["type"],    # Keep as string, let Pydantic convert
                    "payload": payload if isinstance(payload, dict) else json.loads(payload) if isinstance(payload, str) else {},
                    "timestamp": row["timestamp"].isoformat()
                }

                print(f"Debug AI: Event data before validation: {event_data}")

                # Let Pydantic handle the validation with proper data types
                event = ContextEvent(**event_data)
                events.append(event)
                print(f"Debug AI: Successfully created ContextEvent")

            except Exception as parse_error:
                print(f"Debug AI: Error parsing event: {parse_error}")
                # Skip problematic events instead of failing completely
                continue

        print(f"Debug AI: Successfully created {len(events)} events")

        # Generate prompt
        prompt = await ai_service.generate_context_prompt(events, request)

        # Check for stuck state
        stuck_state = await ai_service.detect_stuck_state(events)

        result = {
            "prompt": prompt,
            "event_count": len(events),
            "time_window_minutes": request.context_window_minutes,
            "stuck_state": stuck_state
        }

        # If stuck state detected, generate AI suggestion
        if stuck_state:
            suggestion = await ai_service.generate_ai_suggestion(prompt, "debug")
            result["ai_suggestion"] = suggestion

        return result

    except Exception as e:
        print(f"Error generating AI prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate prompt: {str(e)}")

@router.post("/git/auto-commit")
async def auto_commit(
    session_id: str,
    custom_message: Optional[str] = None,
    auto_stage: bool = False
):
    """Auto-generate and create commit"""
    try:
        # Get git status
        status = await git_service.get_current_status()
        if "error" in status:
            raise HTTPException(status_code=400, detail=status["error"])

        if not status["is_dirty"]:
            return {"message": "No changes to commit"}

        # Get git diff for commit message generation
        diff = await git_service.get_diff()

        # Generate commit message if not provided
        if not custom_message:
            # Get context events for commit message generation
            context_events = []  # Could fetch from DB if needed
            custom_message = await ai_service.generate_commit_message(diff, context_events)

        # Auto-stage files if requested
        if auto_stage:
            await git_service.stage_all()

        # Create commit
        result = await git_service.create_commit(custom_message)

        return {
            "status": "success",
            "commit_hash": result.get("hash"),
            "message": custom_message,
            "files_changed": status["files"]
        }

    except Exception as e:
        print(f"Error in auto-commit: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-commit failed: {str(e)}")

@router.get("/git/status")
async def get_git_status():
    """Get current git status"""
    try:
        status = await git_service.get_current_status()
        return status
    except Exception as e:
        print(f"Error getting git status: {e}")
        raise HTTPException(status_code=500, detail=f"Git status failed: {str(e)}")

@router.post("/git/suggest-branch")
async def suggest_branch(
    session_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Suggest branch name based on context"""
    try:
        # Get recent context events
        since_time = datetime.utcnow() - timedelta(hours=1)

        query = """
            SELECT session_id, agent, type, payload, timestamp
            FROM context_events
            WHERE session_id = $1 AND timestamp > $2
            ORDER BY timestamp DESC
            LIMIT 100
        """

        rows = await db.fetch(query, session_id, since_time)

        events = []
        for row in rows:
            payload = row["payload"]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {"raw": payload}

            events.append(ContextEvent(
                sessionId=row["session_id"],
                agent=Agent(row["agent"]),
                type=EventType(row["type"]),
                payload=payload or {},
                timestamp=row["timestamp"].isoformat()
            ))

        # Generate branch suggestion
        branch_name = await ai_service.suggest_branch_name(events)

        return {
            "suggested_branch": branch_name,
            "confidence": 0.8,  # Could be calculated based on context quality
            "reasoning": f"Based on {len(events)} recent context events"
        }

    except Exception as e:
        print(f"Error suggesting branch: {e}")
        raise HTTPException(status_code=500, detail=f"Branch suggestion failed: {str(e)}")

@router.get("/flow/status/{session_id}")
async def get_flow_status(
    session_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get current flow status"""
    try:
        # Get recent events for flow analysis
        since_time = datetime.utcnow() - timedelta(minutes=30)

        query = """
            SELECT session_id, agent, type, payload, timestamp
            FROM context_events
            WHERE session_id = $1 AND timestamp > $2
            ORDER BY timestamp DESC
            LIMIT 200
        """

        rows = await db.fetch(query, session_id, since_time)

        events = []
        for row in rows:
            payload = row["payload"]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {"raw": payload}

            events.append(ContextEvent(
                sessionId=row["session_id"],
                agent=Agent(row["agent"]),
                type=EventType(row["type"]),
                payload=payload or {},
                timestamp=row["timestamp"].isoformat()
            ))

        # Detect flow state
        flow_state = await flow_service.detect_flow_state(events, session_id)

        return flow_state

    except Exception as e:
        print(f"Error getting flow status: {e}")
        raise HTTPException(status_code=500, detail=f"Flow status failed: {str(e)}")

@router.get("/energy/score/{session_id}")
async def get_energy_score(
    session_id: str,
    time_range: str = "day",
    db: asyncpg.Connection = Depends(get_db)
):
    """Get energy score for session"""
    try:
        # Calculate time window based on range
        if time_range == "hour":
            since_time = datetime.utcnow() - timedelta(hours=1)
        elif time_range == "day":
            since_time = datetime.utcnow() - timedelta(days=1)
        else:  # week
            since_time = datetime.utcnow() - timedelta(weeks=1)

        query = """
            SELECT session_id, agent, type, payload, timestamp
            FROM context_events
            WHERE session_id = $1 AND timestamp > $2
            ORDER BY timestamp DESC
        """

        rows = await db.fetch(query, session_id, since_time)

        events = []
        for row in rows:
            payload = row["payload"]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {"raw": payload}

            events.append(ContextEvent(
                sessionId=row["session_id"],
                agent=Agent(row["agent"]),
                type=EventType(row["type"]),
                payload=payload or {},
                timestamp=row["timestamp"].isoformat()
            ))

        # Calculate energy score
        energy_data = await energy_service.calculate_energy_score(events, session_id)

        return energy_data

    except Exception as e:
        print(f"Error calculating energy score: {e}")
        raise HTTPException(status_code=500, detail=f"Energy score failed: {str(e)}")

@router.get("/health")
async def health_check(db: asyncpg.Connection = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        await db.execute("SELECT 1")

        # Test AI service
        ai_health = await ai_service.health_check()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "ai_service": ai_health
        }
    except Exception as e:
        print(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Background task function
async def analyze_event_context(session_id: str, event_id: str, db: asyncpg.Connection, redis_conn):
    """Background analysis of events for triggers"""
    try:
        # Get recent events for analysis
        since_time = datetime.utcnow() - timedelta(minutes=10)

        query = """
            SELECT session_id, agent, type, payload, timestamp
            FROM context_events
            WHERE session_id = $1 AND timestamp > $2
            ORDER BY timestamp DESC
            LIMIT 100
        """

        rows = await db.fetch(query, session_id, since_time)

        events = []
        for row in rows:
            # Handle JSONB payload from PostgreSQL
            payload = row["payload"]

            # asyncpg returns JSONB as dict directly, but handle edge cases
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {"raw": payload}
            elif payload is None:
                payload = {}

            events.append(ContextEvent(
                sessionId=row["session_id"],
                agent=Agent(row["agent"]),
                type=EventType(row["type"]),
                payload=payload,
                timestamp=row["timestamp"].isoformat()
            ))

        # Check for stuck state
        stuck_state = await ai_service.detect_stuck_state(events)
        if stuck_state and redis_conn is not None:
            # Cache stuck state alert only if Redis is available
            try:
                await redis_conn.setex(
                    f"stuck_state:{session_id}",
                    3600,  # 1 hour expiry
                    json.dumps(stuck_state)
                )
            except Exception as redis_error:
                print(f"Redis error in background task (non-fatal): {redis_error}")

        # Check flow state
        flow_state = await flow_service.detect_flow_state(events, session_id)
        if redis_conn is not None:
            try:
                await redis_conn.setex(
                    f"flow_state:{session_id}",
                    1800,  # 30 minutes expiry
                    json.dumps(flow_state)
                )
            except Exception as redis_error:
                print(f"Redis error in background task (non-fatal): {redis_error}")

    except Exception as e:
        print(f"Background analysis error (non-fatal): {e}")
