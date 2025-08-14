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
        return {"status": "success", "event_id": event_id}

    except Exception as e:
        print(f"Error storing context event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store event: {str(e)}")

@router.post("/ai/prompt")
async def generate_ai_prompt(
    request: AIPromptRequest,
    db: asyncpg.Connection = Depends(get_db)
):
    """Generate AI prompt from context - FIXED JSONB PARSING"""
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
            # FIXED: Handle JSONB payload from PostgreSQL properly
            payload = row["payload"]
            print(f"Debug AI: Raw payload: {payload}, type: {type(payload)}")
            
            # The key fix: ensure payload is always a dict before creating ContextEvent
            if payload is None:
                payload = {}
            elif isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except (json.JSONDecodeError, TypeError):
                    print(f"Debug AI: Failed to parse payload as JSON: {payload}")
                    payload = {"raw_payload": str(payload)}
            elif not isinstance(payload, dict):
                # Convert any other type to dict
                payload = {"value": payload}
            
            print(f"Debug AI: Processed payload: {payload}, type: {type(payload)}")

            try:
                # Create ContextEvent with validated payload
                event = ContextEvent(
                    sessionId=row["session_id"],
                    agent=Agent(row["agent"]),
                    type=EventType(row["type"]),
                    payload=payload,  # Now guaranteed to be a dict
                    timestamp=row["timestamp"].isoformat()
                )
                events.append(event)
                print(f"Debug AI: Successfully created ContextEvent")
                
            except Exception as validation_error:
                print(f"Debug AI: ContextEvent validation failed: {validation_error}")
                # Skip this event rather than failing completely
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
