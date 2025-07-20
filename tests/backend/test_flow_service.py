import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from apps.ccm_api.services.flow_service import FlowService
from apps.ccm_api.models.events import ContextEvent, EventType, Agent


class TestFlowService:
    @pytest.fixture
    def flow_service(self):
        """Create FlowService instance"""
        return FlowService()
    
    @pytest.fixture
    def sample_events(self):
        """Create sample context events for testing"""
        base_time = datetime.utcnow()
        
        events = []
        for i in range(10):
            event = ContextEvent(
                sessionId="test-session",
                agent=Agent.VSCODE,
                type=EventType.FILE_EDIT,
                payload={"file": f"test{i}.ts", "changes": 5},
                timestamp=(base_time - timedelta(minutes=i)).isoformat()
            )
            events.append(event)
        
        return events
    
    def test_detect_flow_state_high_activity(self, flow_service, sample_events):
        """Test flow state detection with high activity"""
        session_id = "test-session"
        
        # Create events with high activity (many recent events)
        recent_events = sample_events[:8]  # 8 events in last 10 minutes
        
        flow_state = flow_service.detect_flow_state(recent_events, session_id)
        
        assert flow_state is not None
        assert 'flow_score' in flow_state
        assert 'activity_score' in flow_state
        assert 'focus_score' in flow_state
        assert 'momentum_score' in flow_state
        assert flow_state['flow_score'] > 0.6  # Should indicate flow state
    
    def test_detect_flow_state_low_activity(self, flow_service):
        """Test flow state detection with low activity"""
        session_id = "test-session"
        
        # Create sparse events (low activity)
        base_time = datetime.utcnow()
        sparse_events = [
            ContextEvent(
                sessionId=session_id,
                agent=Agent.VSCODE,
                type=EventType.FILE_EDIT,
                payload={"file": "test.ts", "changes": 1},
                timestamp=(base_time - timedelta(minutes=30)).isoformat()
            )
        ]
        
        flow_state = flow_service.detect_flow_state(sparse_events, session_id)
        
        assert flow_state['flow_score'] < 0.3  # Should indicate no flow state
    
    def test_calculate_activity_score(self, flow_service, sample_events):
        """Test activity score calculation"""
        # High activity events
        score = flow_service._calculate_activity_score(sample_events)
        assert 0 <= score <= 1
        assert score > 0.5  # Should be high for many recent events
        
        # Low activity events
        old_events = []
        base_time = datetime.utcnow() - timedelta(hours=2)
        for i in range(3):
            event = ContextEvent(
                sessionId="test-session",
                agent=Agent.VSCODE,
                type=EventType.FILE_EDIT,
                payload={"file": f"old{i}.ts"},
                timestamp=(base_time - timedelta(minutes=i)).isoformat()
            )
            old_events.append(event)
        
        low_score = flow_service._calculate_activity_score(old_events)
        assert low_score < 0.3  # Should be low for old events
    
    def test_calculate_focus_score(self, flow_service):
        """Test focus score calculation"""
        session_id = "test-session"
        base_time = datetime.utcnow()
        
        # Focused events (same file)
        focused_events = []
        for i in range(5):
            event = ContextEvent(
                sessionId=session_id,
                agent=Agent.VSCODE,
                type=EventType.FILE_EDIT,
                payload={"file": "main.ts", "changes": 2},
                timestamp=(base_time - timedelta(minutes=i)).isoformat()
            )
            focused_events.append(event)
        
        focus_score = flow_service._calculate_focus_score(focused_events)
        assert focus_score > 0.7  # Should be high for same file edits
        
        # Scattered events (different files)
        scattered_events = []
        for i in range(5):
            event = ContextEvent(
                sessionId=session_id,
                agent=Agent.VSCODE,
                type=EventType.FILE_EDIT,
                payload={"file": f"file{i}.ts", "changes": 1},
                timestamp=(base_time - timedelta(minutes=i)).isoformat()
            )
            scattered_events.append(event)
        
        scattered_score = flow_service._calculate_focus_score(scattered_events)
        assert scattered_score < 0.4  # Should be low for different files
    
    def test_calculate_momentum_score(self, flow_service, sample_events):
        """Test momentum score calculation"""
        momentum_score = flow_service._calculate_momentum_score(sample_events)
        
        assert 0 <= momentum_score <= 1
        assert momentum_score > 0  # Should have some momentum with regular events
    
    def test_count_context_switches(self, flow_service):
        """Test context switch counting"""
        base_time = datetime.utcnow()
        session_id = "test-session"
        
        events_with_switches = [
            ContextEvent(
                sessionId=session_id,
                agent=Agent.VSCODE,
                type=EventType.FILE_EDIT,
                payload={"file": "file1.ts"},
                timestamp=(base_time - timedelta(minutes=1)).isoformat()
            ),
            ContextEvent(
                sessionId=session_id,
                agent=Agent.VSCODE,
                type=EventType.FILE_EDIT,
                payload={"file": "file2.ts"},
                timestamp=(base_time - timedelta(minutes=2)).isoformat()
            ),
            ContextEvent(
                sessionId=session_id,
                agent=Agent.BROWSER,
                type=EventType.TAB_SWITCH,
                payload={"url": "stackoverflow.com"},
                timestamp=(base_time - timedelta(minutes=3)).isoformat()
            )
        ]
        
        switches = flow_service._count_context_switches(events_with_switches)
        assert switches >= 2  # File switch + agent switch
    
    def test_start_flow_session(self, flow_service, sample_events):
        """Test flow session start"""
        session_id = "test-session"
        
        # Verify no active session initially
        assert session_id not in flow_service.active_sessions
        
        flow_service._start_flow_session(session_id, sample_events)
        
        # Verify session was created
        assert session_id in flow_service.active_sessions
        
        session = flow_service.active_sessions[session_id]
        assert session.session_id == session_id
        assert session.start_time is not None
        assert session.productivity_score > 0
    
    def test_end_flow_session(self, flow_service, sample_events):
        """Test flow session end"""
        session_id = "test-session"
        
        # Start a session first
        flow_service._start_flow_session(session_id, sample_events)
        assert session_id in flow_service.active_sessions
        
        # End the session
        flow_service._end_flow_session(session_id)
        
        # Verify session was removed
        assert session_id not in flow_service.active_sessions
    
    def test_calculate_energy_score(self, flow_service):
        """Test energy score calculation"""
        # Create mock flow session
        session = MagicMock()
        session.duration = 7200  # 2 hours
        session.productivity_score = 0.8
        session.total_keystrokes = 1500
        
        energy_score = flow_service._calculate_energy_score(session)
        
        assert 0 <= energy_score <= 1
        assert energy_score > 0.5  # Should be good for productive 2-hour session
    
    def test_is_recent_timestamp(self, flow_service):
        """Test recent timestamp checking"""
        now = datetime.utcnow()
        
        # Recent timestamp (2 minutes ago)
        recent = (now - timedelta(minutes=2)).isoformat()
        assert flow_service._is_recent(recent, minutes=5) is True
        
        # Old timestamp (10 minutes ago)
        old = (now - timedelta(minutes=10)).isoformat()
        assert flow_service._is_recent(old, minutes=5) is False
    
    def test_suggest_break_conditions(self, flow_service):
        """Test break suggestion logic"""
        session_id = "test-session"
        base_time = datetime.utcnow()
        
        # Create session that should trigger break suggestion
        # (long duration + high error rate)
        long_session_events = []
        for i in range(20):
            event_type = EventType.ERROR if i % 3 == 0 else EventType.FILE_EDIT
            event = ContextEvent(
                sessionId=session_id,
                agent=Agent.VSCODE,
                type=event_type,
                payload={"file": "test.ts", "error": "syntax error"} if event_type == EventType.ERROR else {"file": "test.ts"},
                timestamp=(base_time - timedelta(minutes=i*5)).isoformat()  # 5-minute intervals
            )
            long_session_events.append(event)
        
        # Start a long session
        flow_service._start_flow_session(session_id, long_session_events)
        session = flow_service.active_sessions[session_id]
        session.start_time = base_time - timedelta(hours=2)  # 2 hours ago
        
        break_suggestion = flow_service.suggest_break(session_id, long_session_events)
        
        assert break_suggestion is not None
        assert 'reason' in break_suggestion
        assert 'suggested_duration' in break_suggestion
    
    def test_get_flow_insights(self, flow_service, sample_events):
        """Test flow insights retrieval"""
        session_id = "test-session"
        
        # Start a session to have data
        flow_service._start_flow_session(session_id, sample_events)
        
        insights = flow_service.get_flow_insights(session_id, days=7)
        
        assert insights is not None
        assert 'session_id' in insights
        
        # Should have insights from active session
        if session_id in flow_service.active_sessions:
            assert 'current_session' in insights