from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
from dataclasses import dataclass

@dataclass
class FlowState:
    session_id: str
    is_in_flow: bool
    flow_start: Optional[datetime]
    flow_duration: int  # minutes
    keystroke_rhythm: float
    context_switches: int
    test_intensity: float
    focus_score: float

class FlowOrchestrator:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.active_sessions = {}
        self.notification_handlers = []
    
    async def analyze_keystroke_rhythm(self, session_id: str, time_window: int = 5) -> float:
        """Analyze keystroke rhythm for flow detection"""
        async with self.db_pool.acquire() as conn:
            keystrokes = await conn.fetch("""
                SELECT timestamp FROM context_nodes
                WHERE session_id = $1 
                AND event_type IN ('text_changed', 'cursor_moved')
                AND timestamp >= NOW() - INTERVAL '%s minutes'
                ORDER BY timestamp
            """ % time_window, session_id)
            
            if len(keystrokes) < 10:
                return 0.0
            
            # Calculate rhythm consistency
            intervals = []
            for i in range(1, len(keystrokes)):
                delta = (keystrokes[i]['timestamp'] - keystrokes[i-1]['timestamp']).total_seconds()
                if delta < 10:  # Ignore long pauses
                    intervals.append(delta)
            
            if not intervals:
                return 0.0
            
            # Rhythm score based on consistency
            avg_interval = sum(intervals) / len(intervals)
            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
            rhythm_score = max(0, 1 - (variance / (avg_interval ** 2 + 0.1)))
            
            return min(rhythm_score, 1.0)
    
    async def calculate_context_switches(self, session_id: str, time_window: int = 10) -> int:
        """Count context switches (file changes, app switches)"""
        async with self.db_pool.acquire() as conn:
            switches = await conn.fetchval("""
                SELECT COUNT(DISTINCT file_path) as switches
                FROM context_nodes
                WHERE session_id = $1 
                AND event_type = 'editor_focus'
                AND timestamp >= NOW() - INTERVAL '%s minutes'
            """ % time_window, session_id)
            
            return switches or 0
    
    async def calculate_test_intensity(self, session_id: str, time_window: int = 15) -> float:
        """Calculate test/debug intensity"""
        async with self.db_pool.acquire() as conn:
            test_events = await conn.fetchval("""
                SELECT COUNT(*) as test_count
                FROM context_nodes
                WHERE session_id = $1 
                AND event_type IN ('test_run', 'debug_start', 'code_executed')
                AND timestamp >= NOW() - INTERVAL '%s minutes'
            """ % time_window, session_id)
            
            # Normalize to 0-1 scale
            return min((test_events or 0) / 10.0, 1.0)
    
    async def detect_flow_state(self, session_id: str) -> FlowState:
        """Detect current flow state"""
        rhythm = await self.analyze_keystroke_rhythm(session_id)
        context_switches = await self.calculate_context_switches(session_id)
        test_intensity = await self.calculate_test_intensity(session_id)
        
        # Flow scoring algorithm
        focus_score = (
            rhythm * 0.4 +
            max(0, 1 - (context_switches / 5.0)) * 0.3 +
            test_intensity * 0.3
        )
        
        is_in_flow = focus_score > 0.7 and rhythm > 0.6
        
        # Update or create flow session
        current_flow = self.active_sessions.get(session_id)
        if is_in_flow:
            if not current_flow or not current_flow.is_in_flow:
                # Flow state started
                flow_start = datetime.utcnow()
                await self._trigger_flow_start(session_id)
            else:
                flow_start = current_flow.flow_start
            
            flow_duration = int((datetime.utcnow() - flow_start).total_seconds() / 60)
        else:
            if current_flow and current_flow.is_in_flow:
                # Flow state ended
                await self._trigger_flow_end(session_id, current_flow)
            flow_start = None
            flow_duration = 0
        
        flow_state = FlowState(
            session_id=session_id,
            is_in_flow=is_in_flow,
            flow_start=flow_start,
            flow_duration=flow_duration,
            keystroke_rhythm=rhythm,
            context_switches=context_switches,
            test_intensity=test_intensity,
            focus_score=focus_score
        )
        
        self.active_sessions[session_id] = flow_state
        return flow_state
    
    async def _trigger_flow_start(self, session_id: str):
        """Trigger flow start actions"""
        # Store flow start event
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO context_nodes (
                    session_id, agent, event_type, encrypted_payload, timestamp
                ) VALUES ($1, 'flow', 'flow_start', $2, $3)
            """, session_id, '{"action": "flow_detected"}', datetime.utcnow())
        
        # Trigger notifications snoozing (placeholder)
        await self._snooze_notifications(session_id, True)
    
    async def _trigger_flow_end(self, session_id: str, flow_state: FlowState):
        """Trigger flow end actions"""
        duration = int((datetime.utcnow() - flow_state.flow_start).total_seconds() / 60)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO context_nodes (
                    session_id, agent, event_type, encrypted_payload, timestamp
                ) VALUES ($1, 'flow', 'flow_end', $2, $3)
            """, session_id, json.dumps({
                "duration_minutes": duration,
                "peak_focus": flow_state.focus_score
            }), datetime.utcnow())
        
        # Re-enable notifications
        await self._snooze_notifications(session_id, False)
    
    async def _snooze_notifications(self, session_id: str, snooze: bool):
        """Snooze/unsnooze notifications (integration point)"""
        # This would integrate with OS notification system
        # For now, just log the action
        action = "snoozed" if snooze else "enabled"
        print(f"Notifications {action} for session {session_id}")
    
    async def suggest_break(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Suggest break based on flow analysis"""
        flow_state = await self.detect_flow_state(session_id)
        
        if flow_state.flow_duration > 90:  # 90+ minutes of flow
            return {
                "suggestion": "You've been in flow for 90+ minutes. Consider a 15-minute break.",
                "reason": "prolonged_focus",
                "flow_duration": flow_state.flow_duration,
                "recommended_break": 15
            }
        
        if flow_state.focus_score < 0.3 and flow_state.context_switches > 8:
            return {
                "suggestion": "High context switching detected. Take a 5-minute break to refocus.",
                "reason": "fragmented_attention", 
                "context_switches": flow_state.context_switches,
                "recommended_break": 5
            }
        
        return None
    
    async def get_flow_insights(self, session_id: str, days: int = 7) -> Dict[str, Any]:
        """Get flow insights over time period"""
        async with self.db_pool.acquire() as conn:
            flows = await conn.fetch("""
                SELECT 
                    DATE(timestamp) as flow_date,
                    COUNT(*) as flow_sessions,
                    AVG(CAST(encrypted_payload->>'duration_minutes' AS INTEGER)) as avg_duration
                FROM context_nodes
                WHERE session_id = $1 
                AND event_type = 'flow_end'
                AND timestamp >= NOW() - INTERVAL '%s days'
                GROUP BY DATE(timestamp)
                ORDER BY flow_date DESC
            """ % days, session_id)
            
            total_flow_time = await conn.fetchval("""
                SELECT SUM(CAST(encrypted_payload->>'duration_minutes' AS INTEGER))
                FROM context_nodes
                WHERE session_id = $1 
                AND event_type = 'flow_end'
                AND timestamp >= NOW() - INTERVAL '%s days'
            """ % days, session_id)
            
            return {
                "total_flow_minutes": total_flow_time or 0,
                "daily_flows": [dict(row) for row in flows],
                "avg_session_length": sum(row['avg_duration'] or 0 for row in flows) / max(len(flows), 1),
                "flow_frequency": len(flows) / days
            }