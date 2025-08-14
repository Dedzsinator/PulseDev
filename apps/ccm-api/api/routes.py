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

# Initialize services
ai_service = AIService()
git_service = GitService()
flow_service = FlowService()
energy_service = EnergyService()

# Create router
router = APIRouter()

# Dependency functions (same as main.py)
async def get_db():
    # This will be injected from main.py
    pass

async def get_redis():
    # This will be injected from main.py
    pass

@router.post("/context/events")
async def create_context_event(
    event: ContextEvent,
    background_tasks: BackgroundTasks,
    db: asyncpg.Connection = Depends(get_db),
    redis_conn: redis.Redis = Depends(get_redis)
):
    """Store a context event and trigger analysis"""
    try:
        # Store in PostgreSQL (same as before)
        event_id = str(uuid.uuid4())
        await db.execute("""
            INSERT INTO context_events (id, session_id, agent, type, payload, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, event_id, event.sessionId, event.agent.value, event.type.value,
            json.dumps(event.payload), datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')))

        # Cache in Redis
        cache_key = f"session:{event.sessionId}:recent"
        event_data = {
            "id": event_id,
            "agent": event.agent.value,
            "type": event.type.value,
            "payload": event.payload,
            "timestamp": event.timestamp
        }

        await redis_conn.lpush(cache_key, json.dumps(event_data))
        await redis_conn.ltrim(cache_key, 0, 99)
        await redis_conn.expire(cache_key, 86400)

        # Background analysis
        background_tasks.add_task(analyze_event_context, event.sessionId, event_id, db, redis_conn)

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

        rows = await db.fetch(query, request.session_id, since_time)

        events = []
        for row in rows:
            events.append(ContextEvent(
                sessionId=row["session_id"],
                agent=Agent(row["agent"]),
                type=EventType(row["type"]),
                payload=row["payload"],
                timestamp=row["timestamp"].isoformat()
            ))

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

        # Get diff for AI analysis
        diff = await git_service.get_diff(cached=auto_stage)

        if custom_message:
            commit_message = custom_message
        else:
            # Get recent context for commit message generation
            # This would get events from the database
            context_events = []  # Simplified for now
            commit_message = await ai_service.generate_commit_message(diff, context_events)

        # Create commit
        result = await git_service.create_commit(
            message=commit_message,
            auto_stage=auto_stage
        )

        return result

    except Exception as e:
        print(f"Error in auto-commit: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-commit failed: {str(e)}")

@router.get("/git/status")
async def get_git_status():
    """Get current git status"""
    return await git_service.get_current_status()

@router.post("/git/suggest-branch")
async def suggest_branch(
    session_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Suggest branch name based on context"""
    try:
        # Get recent events
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
            events.append(ContextEvent(
                sessionId=row["session_id"],
                agent=Agent(row["agent"]),
                type=EventType(row["type"]),
                payload=row["payload"],
                timestamp=row["timestamp"].isoformat()
            ))

        branch_name = await ai_service.suggest_branch_name(events)

        return {
            "suggested_branch": branch_name,
            "session_id": session_id,
            "confidence": 0.8  # AI confidence score
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
        # Get recent events
        since_time = datetime.utcnow() - timedelta(minutes=30)

        query = """
            SELECT session_id, agent, type, payload, timestamp
            FROM context_events
            WHERE session_id = $1 AND timestamp > $2
            ORDER BY timestamp DESC
        """

        rows = await db.fetch(query, session_id, since_time)

        events = []
        for row in rows:
            events.append(ContextEvent(
                sessionId=row["session_id"],
                agent=Agent(row["agent"]),
                type=EventType(row["type"]),
                payload=row["payload"],
                timestamp=row["timestamp"].isoformat()
            ))

        flow_state = await flow_service.detect_flow_state(events, session_id)
        flow_insights = await flow_service.get_flow_insights(session_id)
        break_suggestion = await flow_service.suggest_break(session_id, events)

        return {
            "flow_state": flow_state,
            "insights": flow_insights,
            "break_suggestion": break_suggestion
        }

    except Exception as e:
        print(f"Error getting flow status: {e}")
        raise HTTPException(status_code=500, detail=f"Flow status failed: {str(e)}")

@router.get("/energy/score/{session_id}")
async def get_energy_score(
    session_id: str,
    hours: int = 8,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get energy score for session"""
    try:
        # Get events for the time window
        since_time = datetime.utcnow() - timedelta(hours=hours)

        query = """
            SELECT session_id, agent, type, payload, timestamp
            FROM context_events
            WHERE session_id = $1 AND timestamp > $2
            ORDER BY timestamp DESC
        """

        rows = await db.fetch(query, session_id, since_time)

        events = []
        for row in rows:
            events.append(ContextEvent(
                sessionId=row["session_id"],
                agent=Agent(row["agent"]),
                type=EventType(row["type"]),
                payload=row["payload"],
                timestamp=row["timestamp"].isoformat()
            ))

        energy_score = await energy_service.calculate_energy_score(events, hours)
        energy_trends = await energy_service.get_energy_trends(session_id)

        return {
            "energy_score": energy_score,
            "trends": energy_trends,
            "session_id": session_id
        }

    except Exception as e:
        print(f"Error calculating energy score: {e}")
        raise HTTPException(status_code=500, detail=f"Energy score calculation failed: {str(e)}")

@router.get("/analytics/dashboard/{session_id}")
async def get_dashboard_data(
    session_id: str,
    days: int = 7,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get comprehensive dashboard data"""
    try:
        # This would aggregate data for dashboard
        since_time = datetime.utcnow() - timedelta(days=days)

        # Get event counts by type
        query = """
            SELECT agent, type, COUNT(*) as count
            FROM context_events
            WHERE session_id = $1 AND timestamp > $2
            GROUP BY agent, type
            ORDER BY count DESC
        """

        rows = await db.fetch(query, session_id, since_time)

        event_counts = {}
        for row in rows:
            event_counts[f"{row['agent']}.{row['type']}"] = row['count']

        # Get recent git activity
        git_commits = await git_service.get_recent_commits(count=20)

        return {
            "session_id": session_id,
            "time_window_days": days,
            "event_counts": event_counts,
            "recent_commits": git_commits,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard data failed: {str(e)}")

# Background task functions
async def analyze_event_context(session_id: str, event_id: str, db: asyncpg.Connection, redis_conn: redis.Redis):
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
            events.append(ContextEvent(
                sessionId=row["session_id"],
                agent=Agent(row["agent"]),
                type=EventType(row["type"]),
                payload=row["payload"],
                timestamp=row["timestamp"].isoformat()
            ))

        # Check for stuck state
        stuck_state = await ai_service.detect_stuck_state(events)
        if stuck_state:
            # Cache stuck state alert
            await redis_conn.setex(
                f"stuck_state:{session_id}",
                3600,  # 1 hour expiry
                json.dumps(stuck_state)
            )

        # Check flow state
        flow_state = await flow_service.detect_flow_state(events, session_id)
        await redis_conn.setex(
            f"flow_state:{session_id}",
            300,  # 5 minute expiry
            json.dumps(flow_state)
        )

    except Exception as e:
        print(f"Error in background analysis: {e}")
