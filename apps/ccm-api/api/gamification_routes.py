"""
PulseDev+ Gamification API Routes
RESTful endpoints for gamification features
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncpg
import redis
from datetime import datetime
import logging

from ..services.gamification_service import GamificationService
from ..config import get_db_connection, get_redis_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/gamification", tags=["gamification"])

# Request/Response models
class XPAwardRequest(BaseModel):
    session_id: str
    source: str
    amount: Optional[int] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SessionSyncRequest(BaseModel):
    session_id: str
    platform: str  # vscode, browser, nvim

class UserProfileResponse(BaseModel):
    id: str
    username: str
    total_xp: int
    level: int
    current_streak: int
    longest_streak: int
    total_commits: int
    total_flow_time: int

# Dependency injection
async def get_gamification_service(
    db: asyncpg.Connection = Depends(get_db_connection),
    redis_conn: redis.Redis = Depends(get_redis_connection)
) -> GamificationService:
    return GamificationService(db, redis_conn)

@router.post("/xp/award")
async def award_xp(
    request: XPAwardRequest,
    gamification: GamificationService = Depends(get_gamification_service)
):
    """Award XP to a user"""
    try:
        xp_earned = await gamification.award_xp(
            session_id=request.session_id,
            source=request.source,
            base_amount=request.amount,
            description=request.description,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "xp_earned": xp_earned,
            "session_id": request.session_id,
            "source": request.source
        }
    except Exception as e:
        logger.error(f"Error awarding XP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/sync")
async def sync_session(
    request: SessionSyncRequest,
    gamification: GamificationService = Depends(get_gamification_service)
):
    """Sync session across platforms"""
    try:
        sync_data = await gamification.sync_session_activity(
            session_id=request.session_id,
            platform=request.platform
        )
        
        return {
            "success": True,
            "sync_data": sync_data
        }
    except Exception as e:
        logger.error(f"Error syncing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{session_id}")
async def get_user_profile(
    session_id: str,
    gamification: GamificationService = Depends(get_gamification_service)
):
    """Get user profile and stats"""
    try:
        stats = await gamification.get_user_stats(session_id)
        return {
            "success": True,
            "profile": stats
        }
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/achievements/{session_id}")
async def get_user_achievements(
    session_id: str,
    gamification: GamificationService = Depends(get_gamification_service)
):
    """Get user achievements"""
    try:
        achievements = await gamification.get_achievements(session_id)
        return {
            "success": True,
            "achievements": achievements
        }
    except Exception as e:
        logger.error(f"Error getting achievements: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leaderboard")
async def get_leaderboard(
    category: str = "xp",
    period: str = "weekly",
    gamification: GamificationService = Depends(get_gamification_service)
):
    """Get leaderboard data"""
    try:
        leaderboard = await gamification.get_leaderboards(category, period)
        return {
            "success": True,
            "leaderboard": leaderboard,
            "category": category,
            "period": period
        }
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/activity/track")
async def track_activity(
    activity_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    gamification: GamificationService = Depends(get_gamification_service)
):
    """Track activity and award XP in background"""
    try:
        session_id = activity_data.get("session_id")
        activity_type = activity_data.get("type")
        
        if not session_id or not activity_type:
            raise HTTPException(status_code=400, detail="session_id and type are required")
        
        # Award XP in background
        background_tasks.add_task(
            _process_activity_xp,
            gamification,
            session_id,
            activity_type,
            activity_data
        )
        
        return {
            "success": True,
            "message": "Activity tracked successfully"
        }
    except Exception as e:
        logger.error(f"Error tracking activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/{session_id}")
async def get_gamification_dashboard(
    session_id: str,
    gamification: GamificationService = Depends(get_gamification_service)
):
    """Get comprehensive gamification dashboard data"""
    try:
        # Get all data in parallel
        user_stats = await gamification.get_user_stats(session_id)
        achievements = await gamification.get_achievements(session_id)
        leaderboard_xp = await gamification.get_leaderboards("xp", "weekly")
        leaderboard_streaks = await gamification.get_leaderboards("streaks", "weekly")
        
        return {
            "success": True,
            "dashboard": {
                "user_stats": user_stats,
                "achievements": achievements,
                "leaderboards": {
                    "xp": leaderboard_xp[:10],  # Top 10
                    "streaks": leaderboard_streaks[:10]
                }
            }
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def _process_activity_xp(
    gamification: GamificationService,
    session_id: str,
    activity_type: str,
    activity_data: Dict[str, Any]
):
    """Process activity and award XP"""
    try:
        # Map activity types to XP sources
        xp_mapping = {
            'file_edit': 'file_edit',
            'commit': 'commit',
            'flow_start': 'flow_state',
            'test_pass': 'test_pass',
            'error_resolve': 'error_resolve',
            'context_switch': 'context_switch'
        }
        
        source = xp_mapping.get(activity_type, activity_type)
        
        await gamification.award_xp(
            session_id=session_id,
            source=source,
            description=f"Activity: {activity_type}",
            metadata=activity_data
        )
        
        logger.info(f"XP awarded for {activity_type} to session {session_id}")
    except Exception as e:
        logger.error(f"Error processing activity XP: {e}")