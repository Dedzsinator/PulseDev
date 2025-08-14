from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import secrets
import string

class TeamRole(str, Enum):
    SCRUM_MASTER = "scrum_master"
    DEVELOPER = "developer"
    PRODUCT_OWNER = "product_owner"
    STAKEHOLDER = "stakeholder"

class TeamMemberStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    REMOVED = "removed"

class TeamRoom(BaseModel):
    id: str = Field(..., description="Unique team room identifier")
    name: str = Field(..., description="Team room name")
    description: Optional[str] = Field(None, description="Team room description")
    scrum_master_id: str = Field(..., description="Scrum master user ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

    # Integration settings
    slack_webhook_url: Optional[str] = Field(None, description="Slack webhook URL")
    slack_channel: Optional[str] = Field(None, description="Slack channel name")
    jira_project_key: Optional[str] = Field(None, description="Jira project key")
    jira_base_url: Optional[str] = Field(None, description="Jira base URL")

    # Room settings
    settings: Dict[str, Any] = Field(default_factory=dict)

class TeamInviteCode(BaseModel):
    id: str = Field(..., description="Invite code ID")
    team_id: str = Field(..., description="Team room ID")
    code: str = Field(..., description="Invitation code")
    role: TeamRole = Field(..., description="Role for this invite code")
    created_by: str = Field(..., description="User who created the code")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    uses_remaining: Optional[int] = Field(None, description="Number of uses remaining")
    is_active: bool = Field(default=True)

class TeamMember(BaseModel):
    id: str = Field(..., description="Member ID")
    team_id: str = Field(..., description="Team room ID")
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username/Display name")
    email: Optional[str] = Field(None, description="User email")
    role: TeamRole = Field(..., description="Team role")
    status: TeamMemberStatus = Field(default=TeamMemberStatus.ACTIVE)
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = Field(None, description="Last activity time")

    # Activity metrics
    total_commits: int = Field(default=0)
    total_xp: int = Field(default=0)
    current_streak: int = Field(default=0)

class TeamRoomCreate(BaseModel):
    name: str = Field(..., description="Team room name")
    description: Optional[str] = Field(None, description="Team room description")
    scrum_master_username: str = Field(..., description="Scrum master username")

    # Optional integration setup
    slack_webhook_url: Optional[str] = Field(None)
    slack_channel: Optional[str] = Field(None)
    jira_project_key: Optional[str] = Field(None)
    jira_base_url: Optional[str] = Field(None)

class InviteCodeCreate(BaseModel):
    team_id: str = Field(..., description="Team room ID")
    role: TeamRole = Field(..., description="Role for invitees")
    expires_hours: Optional[int] = Field(24, description="Hours until expiration")
    max_uses: Optional[int] = Field(None, description="Maximum number of uses")

class JoinTeamRequest(BaseModel):
    invite_code: str = Field(..., description="Invitation code")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="Email address")

class TeamIntegrationUpdate(BaseModel):
    slack_webhook_url: Optional[str] = Field(None)
    slack_channel: Optional[str] = Field(None)
    jira_project_key: Optional[str] = Field(None)
    jira_base_url: Optional[str] = Field(None)
    jira_api_token: Optional[str] = Field(None)

def generate_invite_code(length: int = 8) -> str:
    """Generate a random invite code"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

class TeamActivity(BaseModel):
    """Real-time team activity for mobile app"""
    team_id: str
    member_id: str
    activity_type: str  # 'commit', 'file_edit', 'flow_session', 'achievement'
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TeamAnalytics(BaseModel):
    """Team analytics summary for mobile dashboard"""
    team_id: str
    period: str  # 'today', 'week', 'month'

    # Productivity metrics
    total_commits: int = 0
    total_files_changed: int = 0
    total_flow_time: float = 0  # hours
    total_xp_earned: int = 0

    # Team metrics
    active_members: int = 0
    avg_velocity: float = 0
    sprint_completion_rate: float = 0

    # Top performers
    top_committer: Optional[str] = None
    top_xp_earner: Optional[str] = None
    longest_streak: Optional[str] = None

    generated_at: datetime = Field(default_factory=datetime.utcnow)
