from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import json
import uuid
from pydantic import BaseModel

# Pydantic models for SCRUM
class SprintCreate(BaseModel):
    team_id: str
    name: str
    goal: str
    start_date: str
    end_date: str

class UserStoryCreate(BaseModel):
    team_id: str
    title: str
    description: str
    story_points: int
    acceptance_criteria: List[str] = []

class UserStoryStatusUpdate(BaseModel):
    team_id: str
    status: str

class RetrospectiveItemCreate(BaseModel):
    team_id: str
    sprint_id: str
    category: str  # 'went_well', 'didnt_go_well', 'action_items'
    content: str

router = APIRouter(prefix="/scrum", tags=["scrum"])

# Dependency injection will be handled in main.py
async def get_db():
    pass

@router.post("/sprint")
async def create_sprint(
    sprint_data: SprintCreate,
    db: asyncpg.Connection = Depends(get_db)
):
    """Create a new sprint"""
    try:
        sprint_id = str(uuid.uuid4())
        
        await db.execute("""
            INSERT INTO sprints (
                id, team_id, name, goal, start_date, end_date, status, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, sprint_id, sprint_data.team_id, sprint_data.name, sprint_data.goal,
             datetime.fromisoformat(sprint_data.start_date.replace('Z', '+00:00')),
             datetime.fromisoformat(sprint_data.end_date.replace('Z', '+00:00')),
             'planning', datetime.utcnow())
        
        return {
            "sprint_id": sprint_id,
            "status": "created",
            "message": f"Sprint '{sprint_data.name}' created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create sprint: {str(e)}")

@router.get("/sprint/current/{team_id}")
async def get_current_sprint(
    team_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get current active sprint for team"""
    try:
        # Get current sprint
        sprint_row = await db.fetchrow("""
            SELECT id, name, goal, start_date, end_date, status, velocity
            FROM sprints
            WHERE team_id = $1 AND status IN ('planning', 'active')
            ORDER BY created_at DESC
            LIMIT 1
        """, team_id)
        
        if not sprint_row:
            return None
        
        # Get stories for this sprint
        story_rows = await db.fetch("""
            SELECT id, title, description, story_points, status, assignee
            FROM user_stories
            WHERE sprint_id = $1
            ORDER BY created_at
        """, sprint_row['id'])
        
        stories = []
        for story in story_rows:
            # Get tasks for each story
            task_rows = await db.fetch("""
                SELECT id, title, description, status, estimated_hours, actual_hours, assignee
                FROM tasks
                WHERE story_id = $1
                ORDER BY created_at
            """, story['id'])
            
            stories.append({
                "id": story['id'],
                "title": story['title'],
                "description": story['description'],
                "story_points": story['story_points'],
                "status": story['status'],
                "assignee": story['assignee'],
                "acceptance_criteria": [],  # Would be stored separately
                "tasks": [dict(task) for task in task_rows]
            })
        
        return {
            "id": sprint_row['id'],
            "name": sprint_row['name'],
            "goal": sprint_row['goal'],
            "start_date": sprint_row['start_date'].isoformat(),
            "end_date": sprint_row['end_date'].isoformat(),
            "status": sprint_row['status'],
            "velocity": sprint_row['velocity'] or 0,
            "stories": stories
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current sprint: {str(e)}")

@router.post("/sprint/{sprint_id}/start")
async def start_sprint(
    sprint_id: str,
    team_data: Dict[str, str],
    db: asyncpg.Connection = Depends(get_db)
):
    """Start a sprint"""
    try:
        await db.execute("""
            UPDATE sprints 
            SET status = 'active', start_date = $1
            WHERE id = $2 AND team_id = $3
        """, datetime.utcnow(), sprint_id, team_data.get('team_id'))
        
        return {"status": "started", "sprint_id": sprint_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start sprint: {str(e)}")

@router.post("/sprint/{sprint_id}/complete")
async def complete_sprint(
    sprint_id: str,
    team_data: Dict[str, str],
    db: asyncpg.Connection = Depends(get_db)
):
    """Complete a sprint"""
    try:
        # Calculate velocity
        completed_points = await db.fetchval("""
            SELECT COALESCE(SUM(story_points), 0)
            FROM user_stories
            WHERE sprint_id = $1 AND status = 'done'
        """, sprint_id)
        
        await db.execute("""
            UPDATE sprints 
            SET status = 'completed', end_date = $1, velocity = $2
            WHERE id = $3 AND team_id = $4
        """, datetime.utcnow(), completed_points, sprint_id, team_data.get('team_id'))
        
        return {
            "status": "completed", 
            "sprint_id": sprint_id,
            "velocity": completed_points
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete sprint: {str(e)}")

@router.post("/story")
async def create_user_story(
    story_data: UserStoryCreate,
    db: asyncpg.Connection = Depends(get_db)
):
    """Create a new user story"""
    try:
        story_id = str(uuid.uuid4())
        
        await db.execute("""
            INSERT INTO user_stories (
                id, team_id, title, description, story_points, status, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, story_id, story_data.team_id, story_data.title, story_data.description,
             story_data.story_points, 'backlog', datetime.utcnow())
        
        return {
            "story_id": story_id,
            "status": "created",
            "message": f"User story '{story_data.title}' created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user story: {str(e)}")

@router.get("/backlog/{team_id}")
async def get_backlog(
    team_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get product backlog for team"""
    try:
        rows = await db.fetch("""
            SELECT id, title, description, story_points, status, assignee, created_at
            FROM user_stories
            WHERE team_id = $1 AND sprint_id IS NULL
            ORDER BY created_at DESC
        """, team_id)
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get backlog: {str(e)}")

@router.patch("/story/{story_id}/status")
async def update_story_status(
    story_id: str,
    status_data: UserStoryStatusUpdate,
    db: asyncpg.Connection = Depends(get_db)
):
    """Update user story status"""
    try:
        await db.execute("""
            UPDATE user_stories 
            SET status = $1, updated_at = $2
            WHERE id = $3 AND team_id = $4
        """, status_data.status, datetime.utcnow(), story_id, status_data.team_id)
        
        return {
            "story_id": story_id,
            "status": status_data.status,
            "message": "Story status updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update story status: {str(e)}")

@router.get("/metrics/{team_id}/{sprint_id}")
async def get_sprint_metrics(
    team_id: str,
    sprint_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get sprint metrics"""
    try:
        # Get sprint info
        sprint = await db.fetchrow("""
            SELECT name, start_date, end_date, status, velocity
            FROM sprints
            WHERE id = $1 AND team_id = $2
        """, sprint_id, team_id)
        
        if not sprint:
            return {"error": "Sprint not found"}
        
        # Calculate metrics
        total_points = await db.fetchval("""
            SELECT COALESCE(SUM(story_points), 0)
            FROM user_stories
            WHERE sprint_id = $1
        """, sprint_id)
        
        completed_points = await db.fetchval("""
            SELECT COALESCE(SUM(story_points), 0)
            FROM user_stories
            WHERE sprint_id = $1 AND status = 'done'
        """, sprint_id)
        
        in_progress_points = await db.fetchval("""
            SELECT COALESCE(SUM(story_points), 0)
            FROM user_stories
            WHERE sprint_id = $1 AND status = 'in_progress'
        """, sprint_id)
        
        story_counts = await db.fetch("""
            SELECT status, COUNT(*) as count
            FROM user_stories
            WHERE sprint_id = $1
            GROUP BY status
        """, sprint_id)
        
        return {
            "sprint_name": sprint['name'],
            "total_points": total_points,
            "completed_points": completed_points,
            "in_progress_points": in_progress_points,
            "remaining_points": total_points - completed_points,
            "completion_percentage": (completed_points / total_points * 100) if total_points > 0 else 0,
            "story_counts": {row['status']: row['count'] for row in story_counts},
            "velocity": sprint['velocity'] or 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sprint metrics: {str(e)}")

@router.get("/burndown/{team_id}/{sprint_id}")
async def get_burndown_data(
    team_id: str,
    sprint_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get burndown chart data"""
    try:
        # This would require daily snapshots of remaining work
        # For now, return mock data structure
        sprint = await db.fetchrow("""
            SELECT start_date, end_date FROM sprints
            WHERE id = $1 AND team_id = $2
        """, sprint_id, team_id)
        
        if not sprint:
            return {"error": "Sprint not found"}
        
        # Generate mock burndown data
        start_date = sprint['start_date']
        end_date = sprint['end_date']
        
        total_points = await db.fetchval("""
            SELECT COALESCE(SUM(story_points), 0)
            FROM user_stories WHERE sprint_id = $1
        """, sprint_id)
        
        return {
            "sprint_id": sprint_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_points": total_points,
            "burndown_data": []  # Would contain daily remaining work
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get burndown data: {str(e)}")

@router.get("/velocity/{team_id}")
async def get_velocity_history(
    team_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get team velocity history"""
    try:
        rows = await db.fetch("""
            SELECT name, velocity, start_date, end_date
            FROM sprints
            WHERE team_id = $1 AND status = 'completed'
            ORDER BY start_date DESC
            LIMIT 10
        """, team_id)
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get velocity history: {str(e)}")

@router.post("/retrospective")
async def create_retrospective_item(
    item_data: RetrospectiveItemCreate,
    db: asyncpg.Connection = Depends(get_db)
):
    """Create retrospective item"""
    try:
        item_id = str(uuid.uuid4())
        
        await db.execute("""
            INSERT INTO retrospective_items (
                id, team_id, sprint_id, category, content, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """, item_id, item_data.team_id, item_data.sprint_id, 
             item_data.category, item_data.content, datetime.utcnow())
        
        return {
            "item_id": item_id,
            "status": "created",
            "message": "Retrospective item added successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create retrospective item: {str(e)}")

@router.get("/retrospective/{team_id}/{sprint_id}")
async def get_retrospective_items(
    team_id: str,
    sprint_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get retrospective items for sprint"""
    try:
        rows = await db.fetch("""
            SELECT id, category, content, created_at
            FROM retrospective_items
            WHERE team_id = $1 AND sprint_id = $2
            ORDER BY category, created_at
        """, team_id, sprint_id)
        
        # Group by category
        items = {
            'went_well': [],
            'didnt_go_well': [],
            'action_items': []
        }
        
        for row in rows:
            items[row['category']].append({
                'id': row['id'],
                'content': row['content'],
                'created_at': row['created_at'].isoformat()
            })
        
        return items
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get retrospective items: {str(e)}")