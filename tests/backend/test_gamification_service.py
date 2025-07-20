import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
import json

from apps.ccm_api.services.gamification_service import GamificationService


class TestGamificationService:
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = AsyncMock()
        return db
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis connection"""
        redis = AsyncMock()
        return redis
    
    @pytest.fixture
    def gamification_service(self, mock_db, mock_redis):
        """Create GamificationService instance with mocked dependencies"""
        return GamificationService(mock_db, mock_redis)
    
    @pytest.mark.asyncio
    async def test_award_xp_new_user(self, gamification_service, mock_db, mock_redis):
        """Test XP awarding for a new user"""
        session_id = "test-session-123"
        source = "commit"
        
        # Mock database responses
        mock_db.fetchrow.return_value = None  # No existing user profile
        mock_db.execute = AsyncMock()
        
        result = await gamification_service.award_xp(
            session_id=session_id,
            source=source,
            base_amount=100
        )
        
        # Verify user profile creation
        assert mock_db.execute.call_count >= 2  # Profile creation + XP transaction
        assert result > 0  # Should return XP amount
    
    @pytest.mark.asyncio
    async def test_award_xp_existing_user(self, gamification_service, mock_db, mock_redis):
        """Test XP awarding for existing user"""
        session_id = "test-session-123"
        source = "file_edit"
        
        # Mock existing user profile
        mock_profile = {
            'id': 'user-123',
            'session_id': session_id,
            'username': 'testuser',
            'total_xp': 500,
            'level': 3,
            'current_streak': 5,
            'longest_streak': 10,
            'total_commits': 25,
            'total_flow_time': 120,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        mock_db.fetchrow.return_value = mock_profile
        mock_db.execute = AsyncMock()
        
        result = await gamification_service.award_xp(
            session_id=session_id,
            source=source,
            base_amount=50
        )
        
        # Verify XP transaction and profile update
        assert mock_db.execute.call_count >= 2  # XP transaction + profile update
        assert result > 0
    
    @pytest.mark.asyncio
    async def test_calculate_level_from_xp(self, gamification_service):
        """Test level calculation from XP"""
        # Test level boundaries
        assert gamification_service._calculate_level_from_xp(0) == 1
        assert gamification_service._calculate_level_from_xp(100) == 1
        assert gamification_service._calculate_level_from_xp(500) == 2
        assert gamification_service._calculate_level_from_xp(1200) == 3
        assert gamification_service._calculate_level_from_xp(10000) == 10
    
    @pytest.mark.asyncio
    async def test_update_streak(self, gamification_service, mock_db, mock_redis):
        """Test streak calculation and update"""
        session_id = "test-session-123"
        
        # Mock recent activity (today)
        today = datetime.utcnow().date()
        mock_db.fetchval.return_value = today
        
        # Mock profile update
        mock_db.execute = AsyncMock()
        
        await gamification_service._update_streak(session_id)
        
        # Verify streak update call
        mock_db.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_check_achievements(self, gamification_service, mock_db, mock_redis):
        """Test achievement checking and unlocking"""
        session_id = "test-session-123"
        
        # Mock user stats that should trigger achievements
        user_stats = {
            'total_commits': 1,  # Should trigger "first-commit"
            'current_streak': 5,  # Should trigger "streak-5"
            'total_xp': 1000,
            'level': 5
        }
        
        # Mock no existing achievements
        mock_db.fetch.return_value = []
        mock_db.execute = AsyncMock()
        
        new_achievements = await gamification_service._check_achievements(session_id, user_stats)
        
        # Should unlock multiple achievements
        assert len(new_achievements) > 0
        assert any(ach['id'] == 'first-commit' for ach in new_achievements)
    
    @pytest.mark.asyncio
    async def test_get_user_stats(self, gamification_service, mock_db, mock_redis):
        """Test user stats retrieval"""
        session_id = "test-session-123"
        
        mock_profile = {
            'id': 'user-123',
            'session_id': session_id,
            'username': 'testuser',
            'total_xp': 1500,
            'level': 5,
            'current_streak': 12,
            'longest_streak': 20,
            'total_commits': 45,
            'total_flow_time': 300
        }
        
        mock_db.fetchrow.return_value = mock_profile
        
        stats = await gamification_service.get_user_stats(session_id)
        
        assert stats['total_xp'] == 1500
        assert stats['level'] == 5
        assert stats['current_streak'] == 12
    
    @pytest.mark.asyncio
    async def test_get_leaderboards(self, gamification_service, mock_db, mock_redis):
        """Test leaderboard data retrieval"""
        category = "xp"
        period = "weekly"
        
        mock_leaderboard = [
            {'username': 'user1', 'total_xp': 2000, 'level': 7},
            {'username': 'user2', 'total_xp': 1500, 'level': 5},
            {'username': 'user3', 'total_xp': 1000, 'level': 4}
        ]
        
        mock_db.fetch.return_value = mock_leaderboard
        
        result = await gamification_service.get_leaderboards(category, period)
        
        assert len(result) == 3
        assert result[0]['username'] == 'user1'
        assert result[0]['total_xp'] == 2000
    
    @pytest.mark.asyncio
    async def test_sync_session_activity(self, gamification_service, mock_db, mock_redis):
        """Test session activity synchronization"""
        session_id = "test-session-123"
        platform = "vscode"
        
        # Mock Redis session data
        mock_redis.get.return_value = json.dumps({
            'last_activity': datetime.utcnow().isoformat(),
            'platform': platform,
            'events_count': 150
        })
        
        # Mock database operations
        mock_db.fetchrow.return_value = {'total_xp': 1000}
        mock_db.execute = AsyncMock()
        
        result = await gamification_service.sync_session_activity(session_id, platform)
        
        assert result is not None
        assert 'session_id' in result
        assert 'platform' in result
    
    @pytest.mark.asyncio
    async def test_get_achievements(self, gamification_service, mock_db, mock_redis):
        """Test achievement retrieval"""
        session_id = "test-session-123"
        
        mock_achievements = [
            {
                'id': 'first-commit',
                'name': 'First Commit',
                'description': 'Made your first commit',
                'icon': 'trophy',
                'unlocked_at': datetime.utcnow()
            }
        ]
        
        mock_db.fetch.return_value = mock_achievements
        
        achievements = await gamification_service.get_achievements(session_id)
        
        assert len(achievements) == 1
        assert achievements[0]['name'] == 'First Commit'
    
    def test_xp_sources_configuration(self, gamification_service):
        """Test XP source configurations"""
        xp_sources = gamification_service.xp_sources
        
        # Verify all expected sources exist
        expected_sources = ['commit', 'file_edit', 'flow_state', 'test_pass', 'error_resolve']
        for source in expected_sources:
            assert source in xp_sources
            assert 'base_xp' in xp_sources[source]
            assert 'multiplier' in xp_sources[source]
    
    def test_achievement_definitions(self, gamification_service):
        """Test achievement definitions"""
        achievements = gamification_service.achievements
        
        # Verify essential achievements exist
        achievement_ids = [ach['id'] for ach in achievements]
        assert 'first-commit' in achievement_ids
        assert 'streak-5' in achievement_ids
        assert 'flow-master' in achievement_ids
        
        # Verify achievement structure
        for achievement in achievements:
            assert 'id' in achievement
            assert 'name' in achievement
            assert 'description' in achievement
            assert 'condition' in achievement