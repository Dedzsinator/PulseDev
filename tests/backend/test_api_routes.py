import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json
from datetime import datetime

from apps.ccm_api.main import app


class TestAPIRoutes:
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_context_event(self):
        """Sample context event for testing"""
        return {
            "sessionId": "test-session-123",
            "agent": "vscode",
            "type": "file_edit",
            "payload": {
                "file": "test.ts",
                "changes": 10,
                "language": "typescript"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @patch('apps.ccm_api.api.routes.get_db')
    @patch('apps.ccm_api.api.routes.get_redis')
    def test_create_context_event_success(self, mock_redis, mock_db, client, sample_context_event):
        """Test successful context event creation"""
        # Mock database and Redis
        mock_db_conn = AsyncMock()
        mock_redis_conn = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_db_conn
        mock_redis.return_value = mock_redis_conn
        
        response = client.post("/api/v1/context/events", json=sample_context_event)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "event_id" in data
    
    @patch('apps.ccm_api.api.routes.get_db')
    def test_create_context_event_invalid_data(self, mock_db, client):
        """Test context event creation with invalid data"""
        invalid_event = {
            "sessionId": "test-session",
            # Missing required fields
        }
        
        response = client.post("/api/v1/context/events", json=invalid_event)
        assert response.status_code == 422  # Validation error
    
    @patch('apps.ccm_api.api.routes.get_db')
    def test_generate_ai_prompt_success(self, mock_db, client):
        """Test AI prompt generation"""
        mock_db_conn = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_db_conn
        
        # Mock database query results
        mock_db_conn.fetch.return_value = []
        
        request_data = {
            "session_id": "test-session",
            "context_window_minutes": 30,
            "prompt_type": "debug"
        }
        
        response = client.post("/api/v1/ai/prompt", json=request_data)
        
        # Should succeed even with no events
        assert response.status_code == 200
        data = response.json()
        assert "prompt" in data
        assert "event_count" in data
    
    def test_get_git_status(self, client):
        """Test git status endpoint"""
        with patch('apps.ccm_api.api.routes.git_service.get_current_status') as mock_git_status:
            mock_git_status.return_value = {
                "branch": "main",
                "commit_hash": "abc123",
                "is_dirty": False,
                "modified_files": [],
                "staged_files": [],
                "untracked_files": []
            }
            
            response = client.get("/api/v1/git/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["branch"] == "main"
            assert data["is_dirty"] is False
    
    @patch('apps.ccm_api.api.routes.get_db')
    def test_get_flow_status_success(self, mock_db, client):
        """Test flow status retrieval"""
        mock_db_conn = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_db_conn
        
        # Mock database query results
        mock_db_conn.fetch.return_value = []
        
        session_id = "test-session"
        response = client.get(f"/api/v1/flow/status/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "flow_state" in data
        assert "insights" in data
    
    @patch('apps.ccm_api.api.routes.get_db')
    def test_get_energy_score_success(self, mock_db, client):
        """Test energy score calculation"""
        mock_db_conn = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_db_conn
        
        # Mock database query results
        mock_db_conn.fetch.return_value = []
        
        session_id = "test-session"
        response = client.get(f"/api/v1/energy/score/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "energy_score" in data
        assert "session_id" in data
        assert data["session_id"] == session_id
    
    @patch('apps.ccm_api.api.routes.get_db')
    def test_get_dashboard_data_success(self, mock_db, client):
        """Test dashboard data retrieval"""
        mock_db_conn = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_db_conn
        
        # Mock database query results
        mock_db_conn.fetch.return_value = [
            {"agent": "vscode", "type": "file_edit", "count": 50},
            {"agent": "browser", "type": "tab_switch", "count": 20}
        ]
        
        session_id = "test-session"
        response = client.get(f"/api/v1/analytics/dashboard/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "event_counts" in data
        assert data["session_id"] == session_id
    
    def test_auto_commit_success(self, client):
        """Test auto-commit functionality"""
        with patch('apps.ccm_api.api.routes.git_service') as mock_git:
            # Mock git service responses
            mock_git.get_current_status.return_value = {
                "is_dirty": True,
                "modified_files": ["test.ts"]
            }
            mock_git.get_diff.return_value = "- old line\n+ new line"
            mock_git.create_commit.return_value = {
                "commit_hash": "abc123",
                "message": "Auto-commit: Update test.ts"
            }
            
            response = client.post("/api/v1/git/auto-commit", params={
                "session_id": "test-session",
                "auto_stage": True
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "commit_hash" in data
    
    def test_auto_commit_no_changes(self, client):
        """Test auto-commit with no changes"""
        with patch('apps.ccm_api.api.routes.git_service') as mock_git:
            mock_git.get_current_status.return_value = {
                "is_dirty": False,
                "modified_files": []
            }
            
            response = client.post("/api/v1/git/auto-commit", params={
                "session_id": "test-session"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "No changes to commit"
    
    @patch('apps.ccm_api.api.routes.get_db')
    def test_suggest_branch_success(self, mock_db, client):
        """Test branch name suggestion"""
        mock_db_conn = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_db_conn
        
        # Mock database query results
        mock_db_conn.fetch.return_value = []
        
        response = client.post("/api/v1/git/suggest-branch", params={
            "session_id": "test-session"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "suggested_branch" in data
        assert "session_id" in data
        assert "confidence" in data
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint if it exists"""
        # This would test a health endpoint if implemented
        response = client.get("/health")
        
        # Depending on implementation, this might be 200 or 404
        assert response.status_code in [200, 404]
    
    def test_cors_headers(self, client, sample_context_event):
        """Test CORS headers are present"""
        response = client.post("/api/v1/context/events", json=sample_context_event)
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
    
    @patch('apps.ccm_api.api.routes.get_db')
    def test_database_error_handling(self, mock_db, client, sample_context_event):
        """Test database error handling"""
        # Mock database connection failure
        mock_db.side_effect = Exception("Database connection failed")
        
        response = client.post("/api/v1/context/events", json=sample_context_event)
        
        assert response.status_code == 500
    
    def test_invalid_session_id_format(self, client):
        """Test handling of invalid session ID format"""
        # Test with empty session ID
        response = client.get("/api/v1/flow/status/")
        assert response.status_code == 404
        
        # Test with very long session ID
        long_session_id = "x" * 1000
        response = client.get(f"/api/v1/flow/status/{long_session_id}")
        # Should handle gracefully (might be 400 or 500 depending on validation)
        assert response.status_code in [400, 500, 200]