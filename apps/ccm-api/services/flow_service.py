import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..models.events import ContextEvent, FlowSession
from ..config import Config

class FlowService:
    def __init__(self):
        self.config = Config()
        self.active_sessions: Dict[str, FlowSession] = {}
        self.flow_patterns: Dict[str, List[datetime]] = {}
    
    async def detect_flow_state(self, events: List[ContextEvent], session_id: str) -> Dict[str, Any]:
        """Detect if developer is in flow state"""
        
        if not events:
            return {"in_flow": False, "confidence": 0.0}
        
        # Calculate activity metrics
        recent_events = [e for e in events if self._is_recent(e.timestamp, minutes=5)]
        
        # Flow indicators
        keystroke_activity = len([e for e in recent_events if e.type in ["cursor_moved", "text_selected"]])
        test_activity = len([e for e in recent_events if e.type == "test_run"])
        context_switches = self._count_context_switches(recent_events)
        
        # Flow score calculation
        activity_score = min(keystroke_activity / 50.0, 1.0)  # Normalize to 0-1
        focus_score = max(0, 1.0 - (context_switches / 10.0))  # Fewer switches = better focus
        momentum_score = min(test_activity / 3.0, 1.0)  # Test runs indicate momentum
        
        flow_score = (activity_score * 0.4 + focus_score * 0.4 + momentum_score * 0.2)
        
        # Update or create flow session
        if flow_score > 0.7:  # High flow threshold
            await self._start_flow_session(session_id, events)
        else:
            await self._end_flow_session(session_id)
        
        return {
            "in_flow": flow_score > 0.7,
            "confidence": flow_score,
            "activity_score": activity_score,
            "focus_score": focus_score,
            "momentum_score": momentum_score,
            "keystroke_activity": keystroke_activity,
            "context_switches": context_switches,
            "session_active": session_id in self.active_sessions
        }
    
    async def _start_flow_session(self, session_id: str, events: List[ContextEvent]):
        """Start a new flow session"""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = FlowSession(
                session_id=session_id,
                start_time=datetime.utcnow(),
                keystrokes=0,
                context_switches=0,
                test_runs=0,
                commits=0
            )
        
        # Update session metrics
        session = self.active_sessions[session_id]
        session.keystrokes += len([e for e in events if e.type in ["cursor_moved", "text_selected"]])
        session.test_runs += len([e for e in events if e.type == "test_run"])
        session.commits += len([e for e in events if e.type == "commit_created"])
        session.context_switches += self._count_context_switches(events)
    
    async def _end_flow_session(self, session_id: str):
        """End a flow session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.end_time = datetime.utcnow()
            
            # Calculate energy score for completed session
            duration_hours = (session.end_time - session.start_time).total_seconds() / 3600
            if duration_hours > 0.1:  # At least 6 minutes
                session.energy_score = await self._calculate_energy_score(session)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            return session
        return None
    
    async def _calculate_energy_score(self, session: FlowSession) -> float:
        """Calculate energy score for a flow session"""
        duration_hours = (session.end_time - session.start_time).total_seconds() / 3600
        
        # Base score from duration (longer focused sessions = higher score)
        duration_score = min(duration_hours * 2, 10)  # Cap at 10 for 5+ hour sessions
        
        # Productivity indicators
        productivity_score = 0
        productivity_score += session.test_runs * 2  # Test runs are valuable
        productivity_score += session.commits * 5    # Commits are very valuable
        productivity_score += max(0, 10 - session.context_switches)  # Fewer switches = better
        
        # Keystroke consistency (steady typing is good)
        keystroke_score = min(session.keystrokes / 1000, 5)  # Normalize keystrokes
        
        total_score = duration_score + productivity_score + keystroke_score
        return min(total_score, 100)  # Cap at 100
    
    def _count_context_switches(self, events: List[ContextEvent]) -> int:
        """Count context switches (file changes, app switches)"""
        switches = 0
        last_file = None
        
        for event in events:
            if event.type in ["file_modified", "editor_focus"]:
                current_file = event.payload.get("file_path")
                if current_file and current_file != last_file:
                    switches += 1
                    last_file = current_file
        
        return switches
    
    def _is_recent(self, timestamp: str, minutes: int = 5) -> bool:
        """Check if timestamp is within the last N minutes"""
        try:
            event_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return (datetime.utcnow().replace(tzinfo=event_time.tzinfo) - event_time).total_seconds() < (minutes * 60)
        except:
            return False
    
    async def get_flow_insights(self, session_id: str, days: int = 7) -> Dict[str, Any]:
        """Get flow insights for a session/user"""
        
        # This would typically query the database for historical flow sessions
        # For now, return current session data
        
        insights = {
            "total_sessions": 0,
            "total_flow_time": 0,
            "average_session_length": 0,
            "peak_flow_hours": [],
            "productivity_trends": [],
            "current_session": None
        }
        
        if session_id in self.active_sessions:
            current_session = self.active_sessions[session_id]
            duration = (datetime.utcnow() - current_session.start_time).total_seconds() / 3600
            
            insights["current_session"] = {
                "duration_hours": round(duration, 2),
                "keystrokes": current_session.keystrokes,
                "test_runs": current_session.test_runs,
                "commits": current_session.commits,
                "context_switches": current_session.context_switches
            }
        
        return insights
    
    async def suggest_break(self, session_id: str, events: List[ContextEvent]) -> Optional[Dict[str, Any]]:
        """Suggest when developer should take a break"""
        
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        duration = (datetime.utcnow() - session.start_time).total_seconds() / 3600
        
        # Fatigue indicators
        recent_errors = len([e for e in events[-20:] if 'error' in str(e.payload).lower()])
        context_switches_rate = session.context_switches / max(duration, 0.1)
        
        # Suggest break if:
        # 1. Long session (>2 hours)
        # 2. High error rate
        # 3. High context switching
        
        break_score = 0
        reasons = []
        
        if duration > 2:
            break_score += duration * 10
            reasons.append(f"Long session ({duration:.1f} hours)")
        
        if recent_errors > 5:
            break_score += recent_errors * 5
            reasons.append(f"High error rate ({recent_errors} recent errors)")
        
        if context_switches_rate > 10:
            break_score += context_switches_rate * 2
            reasons.append(f"High context switching ({context_switches_rate:.1f}/hour)")
        
        if break_score > 50:
            return {
                "suggestion": "Consider taking a break",
                "score": break_score,
                "reasons": reasons,
                "recommended_break_minutes": min(15 + int(duration * 2), 30)
            }
        
        return None