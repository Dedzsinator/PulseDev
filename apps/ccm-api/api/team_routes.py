from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import json
import uuid
import secrets
from ..models.teams import (
    TeamRoom, TeamRoomCreate, TeamMember, TeamInviteCode,
    InviteCodeCreate, JoinTeamRequest, TeamIntegrationUpdate,
    TeamRole, TeamMemberStatus, generate_invite_code, TeamActivity, TeamAnalytics
)

router = APIRouter(prefix="/teams", tags=["teams"])

# Dependency injection will be handled in main.py
async def get_db():
    pass

@router.post("/rooms", response_model=Dict[str, Any])
async def create_team_room(
    room_data: TeamRoomCreate,
    db: asyncpg.Connection = Depends(get_db)
):
    """Create a new team room with scrum master"""
    try:
        room_id = str(uuid.uuid4())
        scrum_master_id = str(uuid.uuid4())  # In real app, this would be from auth

        # Create team room
        await db.execute("""
            INSERT INTO team_rooms (
                id, name, description, scrum_master_id, created_at, is_active,
                slack_webhook_url, slack_channel, jira_project_key, jira_base_url,
                settings
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """, room_id, room_data.name, room_data.description, scrum_master_id,
             datetime.utcnow(), True, room_data.slack_webhook_url, room_data.slack_channel,
             room_data.jira_project_key, room_data.jira_base_url, json.dumps({}))

        # Add scrum master as team member
        member_id = str(uuid.uuid4())
        await db.execute("""
            INSERT INTO team_members (
                id, team_id, user_id, username, role, status, joined_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, member_id, room_id, scrum_master_id, room_data.scrum_master_username,
             TeamRole.SCRUM_MASTER.value, TeamMemberStatus.ACTIVE.value, datetime.utcnow())

        # Generate initial invite codes
        dev_code = generate_invite_code()
        po_code = generate_invite_code()

        # Create developer invite code
        await db.execute("""
            INSERT INTO team_invite_codes (
                id, team_id, code, role, created_by, created_at, expires_at, is_active
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, str(uuid.uuid4()), room_id, dev_code, TeamRole.DEVELOPER.value,
             scrum_master_id, datetime.utcnow(), datetime.utcnow() + timedelta(hours=72), True)

        # Create product owner invite code
        await db.execute("""
            INSERT INTO team_invite_codes (
                id, team_id, code, role, created_by, created_at, expires_at, is_active
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, str(uuid.uuid4()), room_id, po_code, TeamRole.PRODUCT_OWNER.value,
             scrum_master_id, datetime.utcnow(), datetime.utcnow() + timedelta(hours=72), True)

        return {
            "room_id": room_id,
            "name": room_data.name,
            "scrum_master_id": scrum_master_id,
            "invite_codes": {
                "developer": dev_code,
                "product_owner": po_code
            },
            "status": "created",
            "message": f"Team room '{room_data.name}' created successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create team room: {str(e)}")

@router.get("/rooms/{room_id}", response_model=Dict[str, Any])
async def get_team_room(
    room_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get team room details with members"""
    try:
        # Get room details
        room = await db.fetchrow("""
            SELECT id, name, description, scrum_master_id, created_at, is_active,
                   slack_webhook_url, slack_channel, jira_project_key, jira_base_url,
                   settings
            FROM team_rooms
            WHERE id = $1 AND is_active = true
        """, room_id)

        if not room:
            raise HTTPException(status_code=404, detail="Team room not found")

        # Get team members
        members = await db.fetch("""
            SELECT id, user_id, username, email, role, status, joined_at, last_active,
                   total_commits, total_xp, current_streak
            FROM team_members
            WHERE team_id = $1 AND status != 'removed'
            ORDER BY joined_at
        """, room_id)

        # Get active invite codes
        invite_codes = await db.fetch("""
            SELECT id, code, role, created_at, expires_at, uses_remaining
            FROM team_invite_codes
            WHERE team_id = $1 AND is_active = true AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY role, created_at
        """, room_id)

        return {
            "id": room['id'],
            "name": room['name'],
            "description": room['description'],
            "scrum_master_id": room['scrum_master_id'],
            "created_at": room['created_at'].isoformat(),
            "integrations": {
                "slack_channel": room['slack_channel'],
                "jira_project_key": room['jira_project_key']
            },
            "members": [dict(member) for member in members],
            "invite_codes": [dict(code) for code in invite_codes],
            "member_count": len(members)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team room: {str(e)}")

@router.post("/rooms/{room_id}/invite-codes", response_model=Dict[str, str])
async def create_invite_code(
    room_id: str,
    invite_data: InviteCodeCreate,
    db: asyncpg.Connection = Depends(get_db)
):
    """Generate a new invite code for specific role"""
    try:
        # Verify team room exists
        room_exists = await db.fetchval("""
            SELECT EXISTS(SELECT 1 FROM team_rooms WHERE id = $1 AND is_active = true)
        """, room_id)

        if not room_exists:
            raise HTTPException(status_code=404, detail="Team room not found")

        code = generate_invite_code()
        expires_at = datetime.utcnow() + timedelta(hours=invite_data.expires_hours)

        await db.execute("""
            INSERT INTO team_invite_codes (
                id, team_id, code, role, created_by, created_at, expires_at,
                uses_remaining, is_active
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, str(uuid.uuid4()), room_id, code, invite_data.role.value,
             "system", datetime.utcnow(), expires_at, invite_data.max_uses, True)

        return {
            "invite_code": code,
            "role": invite_data.role.value,
            "expires_at": expires_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create invite code: {str(e)}")

@router.post("/join", response_model=Dict[str, Any])
async def join_team_with_code(
    join_data: JoinTeamRequest,
    db: asyncpg.Connection = Depends(get_db)
):
    """Join a team using an invite code"""
    try:
        # Find and validate invite code
        invite = await db.fetchrow("""
            SELECT ic.id, ic.team_id, ic.role, ic.uses_remaining, ic.expires_at,
                   tr.name as team_name
            FROM team_invite_codes ic
            JOIN team_rooms tr ON ic.team_id = tr.id
            WHERE ic.code = $1 AND ic.is_active = true AND tr.is_active = true
        """, join_data.invite_code.upper())

        if not invite:
            raise HTTPException(status_code=404, detail="Invalid or expired invite code")

        # Check expiration
        if invite['expires_at'] and invite['expires_at'] < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Invite code has expired")

        # Check usage limit
        if invite['uses_remaining'] is not None and invite['uses_remaining'] <= 0:
            raise HTTPException(status_code=400, detail="Invite code has no uses remaining")

        # Check if user already in team
        existing_member = await db.fetchval("""
            SELECT EXISTS(SELECT 1 FROM team_members
                         WHERE team_id = $1 AND username = $2 AND status != 'removed')
        """, invite['team_id'], join_data.username)

        if existing_member:
            raise HTTPException(status_code=400, detail="User already in team")

        # Add member to team
        member_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())  # In real app, this would be from auth

        await db.execute("""
            INSERT INTO team_members (
                id, team_id, user_id, username, email, role, status, joined_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, member_id, invite['team_id'], user_id, join_data.username,
             join_data.email, invite['role'], TeamMemberStatus.ACTIVE.value, datetime.utcnow())

        # Update invite code usage
        if invite['uses_remaining'] is not None:
            new_uses = invite['uses_remaining'] - 1
            await db.execute("""
                UPDATE team_invite_codes
                SET uses_remaining = $1,
                    is_active = CASE WHEN $1 <= 0 THEN false ELSE is_active END
                WHERE id = $2
            """, new_uses, invite['id'])

        return {
            "status": "joined",
            "team_id": invite['team_id'],
            "team_name": invite['team_name'],
            "member_id": member_id,
            "role": invite['role'],
            "message": f"Successfully joined team '{invite['team_name']}' as {invite['role']}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to join team: {str(e)}")

@router.get("/rooms/{room_id}/members", response_model=List[Dict[str, Any]])
async def get_team_members(
    room_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get all team members with their activity stats"""
    try:
        members = await db.fetch("""
            SELECT tm.id, tm.user_id, tm.username, tm.email, tm.role, tm.status,
                   tm.joined_at, tm.last_active, tm.total_commits, tm.total_xp, tm.current_streak,
                   COUNT(ce.id) as recent_activity_count
            FROM team_members tm
            LEFT JOIN context_events ce ON ce.session_id LIKE tm.user_id || '%'
                AND ce.timestamp > NOW() - INTERVAL '24 hours'
            WHERE tm.team_id = $1 AND tm.status != 'removed'
            GROUP BY tm.id, tm.user_id, tm.username, tm.email, tm.role, tm.status,
                     tm.joined_at, tm.last_active, tm.total_commits, tm.total_xp, tm.current_streak
            ORDER BY tm.role, tm.joined_at
        """, room_id)

        return [dict(member) for member in members]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team members: {str(e)}")

@router.patch("/rooms/{room_id}/integrations", response_model=Dict[str, str])
async def update_team_integrations(
    room_id: str,
    integration_data: TeamIntegrationUpdate,
    db: asyncpg.Connection = Depends(get_db)
):
    """Update team integration settings (Slack, Jira)"""
    try:
        # Verify team room exists
        room_exists = await db.fetchval("""
            SELECT EXISTS(SELECT 1 FROM team_rooms WHERE id = $1 AND is_active = true)
        """, room_id)

        if not room_exists:
            raise HTTPException(status_code=404, detail="Team room not found")

        # Update integration settings
        await db.execute("""
            UPDATE team_rooms
            SET slack_webhook_url = COALESCE($2, slack_webhook_url),
                slack_channel = COALESCE($3, slack_channel),
                jira_project_key = COALESCE($4, jira_project_key),
                jira_base_url = COALESCE($5, jira_base_url)
            WHERE id = $1
        """, room_id, integration_data.slack_webhook_url, integration_data.slack_channel,
             integration_data.jira_project_key, integration_data.jira_base_url)

        return {
            "status": "updated",
            "message": "Team integrations updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update integrations: {str(e)}")

@router.get("/rooms/{room_id}/activity", response_model=List[Dict[str, Any]])
async def get_team_activity(
    room_id: str,
    hours: int = 24,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get recent team activity for mobile app"""
    try:
        # Get team member user IDs
        member_ids = await db.fetch("""
            SELECT user_id, username FROM team_members
            WHERE team_id = $1 AND status = 'active'
        """, room_id)

        if not member_ids:
            return []

        # Get recent context events for team members
        activities = await db.fetch("""
            SELECT ce.session_id, ce.agent, ce.type, ce.payload, ce.timestamp,
                   tm.username, tm.role
            FROM context_events ce
            JOIN team_members tm ON ce.session_id LIKE tm.user_id || '%'
            WHERE tm.team_id = $1
              AND tm.status = 'active'
              AND ce.timestamp > NOW() - INTERVAL '%s hours'
            ORDER BY ce.timestamp DESC
            LIMIT 50
        """ % hours, room_id)

        formatted_activities = []
        for activity in activities:
            payload = json.loads(activity['payload']) if isinstance(activity['payload'], str) else activity['payload']

            formatted_activities.append({
                "member_username": activity['username'],
                "member_role": activity['role'],
                "activity_type": activity['type'],
                "description": f"{activity['username']} performed {activity['type']}",
                "details": payload,
                "timestamp": activity['timestamp'].isoformat()
            })

        return formatted_activities

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team activity: {str(e)}")

@router.get("/rooms/{room_id}/analytics", response_model=Dict[str, Any])
async def get_team_analytics(
    room_id: str,
    period: str = "week",  # today, week, month
    db: asyncpg.Connection = Depends(get_db)
):
    """Get team analytics summary for mobile dashboard"""
    try:
        # Determine time window
        time_windows = {
            "today": "1 day",
            "week": "7 days",
            "month": "30 days"
        }

        window = time_windows.get(period, "7 days")

        # Get team members
        members = await db.fetch("""
            SELECT user_id, username, total_commits, total_xp, current_streak
            FROM team_members
            WHERE team_id = $1 AND status = 'active'
        """, room_id)

        if not members:
            return {"error": "No active team members"}

        member_ids = [m['user_id'] for m in members]

        # Get activity metrics
        activity_stats = await db.fetchrow(f"""
            SELECT
                COUNT(CASE WHEN type = 'commit_created' THEN 1 END) as total_commits,
                COUNT(CASE WHEN type = 'file_modified' THEN 1 END) as total_files_changed,
                COUNT(CASE WHEN type = 'flow_start' THEN 1 END) as flow_sessions,
                COUNT(*) as total_events
            FROM context_events
            WHERE session_id = ANY($1)
              AND timestamp > NOW() - INTERVAL '{window}'
        """, member_ids)

        # Get current sprint info
        sprint_info = await db.fetchrow("""
            SELECT s.name, s.velocity, s.status,
                   COUNT(us.id) as total_stories,
                   COUNT(CASE WHEN us.status = 'done' THEN 1 END) as completed_stories
            FROM sprints s
            LEFT JOIN user_stories us ON s.id = us.sprint_id
            WHERE s.team_id = $1 AND s.status IN ('planning', 'active')
            GROUP BY s.id, s.name, s.velocity, s.status
            ORDER BY s.created_at DESC
            LIMIT 1
        """, room_id)

        # Calculate top performers
        top_committer = max(members, key=lambda m: m['total_commits'])['username'] if members else None
        top_xp_earner = max(members, key=lambda m: m['total_xp'])['username'] if members else None
        longest_streak = max(members, key=lambda m: m['current_streak'])['username'] if members else None

        completion_rate = 0
        if sprint_info and sprint_info['total_stories'] > 0:
            completion_rate = (sprint_info['completed_stories'] / sprint_info['total_stories']) * 100

        return {
            "team_id": room_id,
            "period": period,
            "active_members": len(members),
            "total_commits": activity_stats['total_commits'] or 0,
            "total_files_changed": activity_stats['total_files_changed'] or 0,
            "total_flow_sessions": activity_stats['flow_sessions'] or 0,
            "total_events": activity_stats['total_events'] or 0,
            "sprint_completion_rate": completion_rate,
            "avg_velocity": sprint_info['velocity'] if sprint_info else 0,
            "top_performers": {
                "top_committer": top_committer,
                "top_xp_earner": top_xp_earner,
                "longest_streak": longest_streak
            },
            "current_sprint": {
                "name": sprint_info['name'] if sprint_info else None,
                "status": sprint_info['status'] if sprint_info else None,
                "completion_rate": completion_rate
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team analytics: {str(e)}")

@router.delete("/rooms/{room_id}/members/{member_id}")
async def remove_team_member(
    room_id: str,
    member_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Remove a team member (scrum master only)"""
    try:
        # Update member status to removed
        result = await db.execute("""
            UPDATE team_members
            SET status = 'removed'
            WHERE id = $1 AND team_id = $2 AND role != 'scrum_master'
        """, member_id, room_id)

        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Member not found or cannot be removed")

        return {"status": "removed", "message": "Team member removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove team member: {str(e)}")
