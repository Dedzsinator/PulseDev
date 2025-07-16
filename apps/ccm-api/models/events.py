from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    # File events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_RENAMED = "file_renamed"
    
    # Editor events
    EDITOR_FOCUS = "editor_focus"
    EDITOR_BLUR = "editor_blur"
    CURSOR_MOVED = "cursor_moved"
    TEXT_SELECTED = "text_selected"
    CODE_EXECUTED = "code_executed"
    TEST_RUN = "test_run"
    
    # Terminal events
    COMMAND_EXECUTED = "command_executed"
    TERMINAL_OUTPUT = "terminal_output"
    
    # Git events
    COMMIT_CREATED = "commit_created"
    BRANCH_SWITCHED = "branch_switched"
    MERGE_CONFLICT = "merge_conflict"
    
    # Flow events
    FLOW_START = "flow_start"
    FLOW_END = "flow_end"
    STUCK_STATE = "stuck_state"
    
    # AI events
    PROMPT_GENERATED = "prompt_generated"
    AI_SUGGESTION = "ai_suggestion"

class Agent(str, Enum):
    FILE = "file"
    EDITOR = "editor"
    TERMINAL = "terminal"
    GIT = "git"
    FLOW = "flow"
    AI = "ai"
    BROWSER = "browser"

class ContextEvent(BaseModel):
    sessionId: str = Field(..., description="Session identifier")
    agent: Agent = Field(..., description="Context agent")
    type: EventType = Field(..., description="Event type")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    timestamp: str = Field(..., description="ISO timestamp")
    userId: Optional[str] = Field(None, description="User identifier")
    projectId: Optional[str] = Field(None, description="Project identifier")

class FlowSession(BaseModel):
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    keystrokes: int = 0
    context_switches: int = 0
    test_runs: int = 0
    commits: int = 0
    energy_score: Optional[float] = None

class StuckState(BaseModel):
    session_id: str
    detected_at: datetime
    pattern: str  # "looping_edits", "repeated_errors", "idle_with_failures"
    context: Dict[str, Any]
    resolved: bool = False

class AIPromptRequest(BaseModel):
    session_id: str
    context_window_minutes: int = 30
    include_terminal: bool = True
    include_git: bool = True
    include_errors: bool = True
    custom_context: Optional[str] = None

class CommitSuggestion(BaseModel):
    session_id: str
    message: str
    files: List[str]
    auto_stage: bool = False
    confidence: float

class BranchSuggestion(BaseModel):
    session_id: str
    branch_name: str
    reason: str
    confidence: float