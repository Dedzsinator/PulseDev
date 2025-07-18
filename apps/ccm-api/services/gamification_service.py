"""
PulseDev+ Gamification Service
Handles XP, achievements, streaks, and leaderboards across all platforms
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import asyncpg
import redis
import json
import logging
from dataclasses import dataclass
from .encryption_service import EncryptionService

logger = logging.getLogger(__name__)

@dataclass
class Achievement:
    id: str
    name: str
    description: str
    icon: str
    category: str
    xp_reward: int
    unlock_criteria: Dict[str, Any]
    tier: str

@dataclass
class UserProfile:
    id: str
    username: str
    email: str
    session_id: str
    total_xp: int
    level: int
    current_streak: int
    longest_streak: int
    total_commits: int
    total_flow_time: int
    total_coding_minutes: int

@dataclass
class XPTransaction:
    amount: int
    source: str
    description: str
    metadata: Dict[str, Any]

class GamificationService:
    def __init__(self, db_pool: asyncpg.Pool, redis_client: redis.Redis):
        self.db_pool = db_pool
        self.redis = redis_client
        self.encryption = EncryptionService()
        
        # XP multipliers for different activities
        self.xp_rates = {
            'file_edit': 2,
            'commit': 15,
            'flow_state': 5,  # per minute
            'test_pass': 10,
            'error_resolve': 8,
            'context_switch': -1,  # penalty
            'stuck_state_resolve': 20,
            'pair_programming': 3,  # per minute
            'weekend_coding': 1.5,  # multiplier
            'night_coding': 1.2,   # multiplier
        }
    
    async def get_or_create_user_profile(self, session_id: str, username: str = None, email: str = None) -> UserProfile:
        """Get existing user profile or create new one"""
        async with self.db_pool.acquire() as conn:
            # Check if user exists
            user = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE session_id = $1",
                session_id
            )
            
            if user:
                return UserProfile(**dict(user))
            
            # Create new user
            if not username:
                username = f"dev_{session_id[:8]}"
            if not email:
                email = f"{username}@pulsedev.local"
            
            user_data = await conn.fetchrow("""
                INSERT INTO user_profiles (username, email, session_id)
                VALUES ($1, $2, $3)
                RETURNING *
            """, username, email, session_id)
            
            return UserProfile(**dict(user_data))
    
    async def award_xp(self, session_id: str, source: str, base_amount: int = None, 
                      description: str = None, metadata: Dict[str, Any] = None) -> int:
        """Award XP for an activity and check for achievements"""
        if base_amount is None:
            base_amount = self.xp_rates.get(source, 1)
        
        # Apply multipliers
        multiplier = 1.0
        current_time = datetime.now()
        
        # Weekend bonus
        if current_time.weekday() >= 5:  # Saturday or Sunday
            multiplier *= self.xp_rates.get('weekend_coding', 1.0)
        
        # Night owl bonus (10 PM - 6 AM)
        if current_time.hour >= 22 or current_time.hour <= 6:
            multiplier *= self.xp_rates.get('night_coding', 1.0)
        
        final_amount = int(base_amount * multiplier)
        
        async with self.db_pool.acquire() as conn:
            # Get user profile
            user = await self.get_or_create_user_profile(session_id)
            
            # Record XP transaction
            await conn.execute("""
                INSERT INTO xp_transactions (user_id, session_id, amount, source, description, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, user.id, session_id, final_amount, source, description, 
                json.dumps(metadata or {}))
            
            # Update user profile
            new_xp = user.total_xp + final_amount
            new_level = self._calculate_level(new_xp)
            
            await conn.execute("""
                UPDATE user_profiles 
                SET total_xp = $1, level = $2, updated_at = NOW()
                WHERE id = $3
            """, new_xp, new_level, user.id)
            
            # Update daily streak
            await self._update_daily_streak(conn, user.id, final_amount, source)
            
            # Check for achievements
            await self._check_achievements(conn, user.id, session_id, source, metadata or {})
            
            # Cache updated profile
            await self._cache_user_profile(session_id, user.id)
            
            return final_amount
    
    async def sync_session_activity(self, session_id: str, platform: str) -> Dict[str, Any]:
        """Mark session as active and sync with other platforms"""
        async with self.db_pool.acquire() as conn:
            user = await self.get_or_create_user_profile(session_id)
            
            # Deactivate other sessions for this user
            await conn.execute("""
                UPDATE active_sessions 
                SET is_active = false 
                WHERE user_id = $1 AND session_id != $2
            """, user.id, session_id)
            
            # Activate current session
            await conn.execute("""
                INSERT INTO active_sessions (user_id, session_id, platform, sync_token)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (session_id) 
                DO UPDATE SET 
                    is_active = true,
                    last_activity = NOW(),
                    platform = $3
            """, user.id, session_id, platform, f"sync_{datetime.now().timestamp()}")
            
            # Get current stats
            stats = await self._get_session_stats(conn, user.id)
            
            return {
                'active_session': session_id,
                'platform': platform,
                'user_profile': user.__dict__,
                'session_stats': stats
            }
    
    async def get_achievements(self, session_id: str) -> Dict[str, Any]:
        """Get user achievements and available achievements"""
        async with self.db_pool.acquire() as conn:
            user = await self.get_or_create_user_profile(session_id)
            
            # Get unlocked achievements
            unlocked = await conn.fetch("""
                SELECT a.*, ua.unlocked_at, ua.metadata
                FROM user_achievements ua
                JOIN achievements a ON ua.achievement_id = a.id
                WHERE ua.user_id = $1
                ORDER BY ua.unlocked_at DESC
            """, user.id)
            
            # Get all available achievements
            all_achievements = await conn.fetch("SELECT * FROM achievements ORDER BY category, tier")
            
            return {
                'unlocked': [dict(row) for row in unlocked],
                'available': [dict(row) for row in all_achievements],
                'progress': await self._get_achievement_progress(conn, user.id)
            }
    
    async def get_leaderboards(self, category: str = 'xp', period: str = 'weekly') -> List[Dict[str, Any]]:
        """Get leaderboard for specified category and period"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT 
                    up.username,
                    up.level,
                    l.value,
                    l.date,
                    RANK() OVER (ORDER BY l.value DESC) as rank
                FROM leaderboards l
                JOIN user_profiles up ON l.user_id = up.id
                WHERE l.category = $1 AND l.period = $2
                AND l.date >= $3
                ORDER BY l.value DESC
                LIMIT 100
            """
            
            # Calculate date range
            if period == 'daily':
                start_date = date.today()
            elif period == 'weekly':
                start_date = date.today() - timedelta(days=7)
            elif period == 'monthly':
                start_date = date.today() - timedelta(days=30)
            else:
                start_date = date(2020, 1, 1)  # all time
            
            results = await conn.fetch(query, category, period, start_date)
            return [dict(row) for row in results]
    
    async def get_user_stats(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        async with self.db_pool.acquire() as conn:
            user = await self.get_or_create_user_profile(session_id)
            
            # Recent XP transactions
            recent_xp = await conn.fetch("""
                SELECT * FROM xp_transactions
                WHERE user_id = $1
                ORDER BY timestamp DESC
                LIMIT 20
            """, user.id)
            
            # Weekly progress
            weekly_progress = await conn.fetchrow("""
                SELECT 
                    SUM(amount) as total_xp,
                    COUNT(*) as transactions,
                    COUNT(DISTINCT DATE(timestamp)) as active_days
                FROM xp_transactions
                WHERE user_id = $1 AND timestamp >= NOW() - INTERVAL '7 days'
            """, user.id)
            
            # Current streak info
            current_streak = await conn.fetchrow("""
                SELECT * FROM daily_streaks
                WHERE user_id = $1 AND date = CURRENT_DATE
            """, user.id)
            
            return {
                'profile': user.__dict__,
                'recent_xp': [dict(row) for row in recent_xp],
                'weekly_progress': dict(weekly_progress) if weekly_progress else {},
                'current_streak': dict(current_streak) if current_streak else {},
                'next_level_xp': self._xp_for_level(user.level + 1) - user.total_xp
            }
    
    def _calculate_level(self, total_xp: int) -> int:
        """Calculate level based on total XP"""
        # Exponential XP curve: level^2 * 100
        level = 1
        while self._xp_for_level(level + 1) <= total_xp:
            level += 1
        return level
    
    def _xp_for_level(self, level: int) -> int:
        """Calculate XP required for a specific level"""
        return (level ** 2) * 100
    
    async def _update_daily_streak(self, conn: asyncpg.Connection, user_id: str, xp_earned: int, source: str):
        """Update daily streak data"""
        today = date.today()
        
        # Update or create today's streak record
        await conn.execute("""
            INSERT INTO daily_streaks (user_id, date, xp_earned)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, date)
            DO UPDATE SET
                xp_earned = daily_streaks.xp_earned + $3,
                coding_minutes = CASE WHEN $4 = 'flow_state' THEN daily_streaks.coding_minutes + 1 ELSE daily_streaks.coding_minutes END,
                commits = CASE WHEN $4 = 'commit' THEN daily_streaks.commits + 1 ELSE daily_streaks.commits END
        """, user_id, today, xp_earned, source)
        
        # Calculate current streak
        streak_query = """
            WITH consecutive_days AS (
                SELECT 
                    date,
                    ROW_NUMBER() OVER (ORDER BY date DESC) as rn,
                    date + INTERVAL '1 day' * ROW_NUMBER() OVER (ORDER BY date DESC) as expected_date
                FROM daily_streaks
                WHERE user_id = $1 AND date <= CURRENT_DATE
                ORDER BY date DESC
            )
            SELECT COUNT(*) as streak_length
            FROM consecutive_days
            WHERE expected_date = CURRENT_DATE + INTERVAL '1 day'
        """
        
        streak_result = await conn.fetchrow(streak_query, user_id)
        current_streak = streak_result['streak_length'] if streak_result else 0
        
        # Update user profile with streak
        await conn.execute("""
            UPDATE user_profiles
            SET 
                current_streak = $1,
                longest_streak = GREATEST(longest_streak, $1)
            WHERE id = $2
        """, current_streak, user_id)
    
    async def _check_achievements(self, conn: asyncpg.Connection, user_id: str, session_id: str, 
                                source: str, metadata: Dict[str, Any]):
        """Check and unlock achievements"""
        # Get all achievements that user hasn't unlocked yet
        available_achievements = await conn.fetch("""
            SELECT a.* FROM achievements a
            WHERE a.id NOT IN (
                SELECT achievement_id FROM user_achievements WHERE user_id = $1
            )
        """, user_id)
        
        for achievement in available_achievements:
            criteria = json.loads(achievement['unlock_criteria'])
            
            if await self._check_achievement_criteria(conn, user_id, criteria, source, metadata):
                # Unlock achievement
                await conn.execute("""
                    INSERT INTO user_achievements (user_id, achievement_id, session_id, metadata)
                    VALUES ($1, $2, $3, $4)
                """, user_id, achievement['id'], session_id, json.dumps(metadata))
                
                # Award XP
                await conn.execute("""
                    INSERT INTO xp_transactions (user_id, session_id, amount, source, description)
                    VALUES ($1, $2, $3, $4, $5)
                """, user_id, session_id, achievement['xp_reward'], 
                    'achievement', f"Achievement unlocked: {achievement['name']}")
                
                logger.info(f"Achievement unlocked: {achievement['name']} for user {user_id}")
    
    async def _check_achievement_criteria(self, conn: asyncpg.Connection, user_id: str, 
                                        criteria: Dict[str, Any], source: str, 
                                        metadata: Dict[str, Any]) -> bool:
        """Check if achievement criteria are met"""
        # Get user stats
        user = await conn.fetchrow("SELECT * FROM user_profiles WHERE id = $1", user_id)
        
        for criterion, required_value in criteria.items():
            if criterion == 'event_count' and criteria.get('event_type') == source:
                # Count events of this type
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM xp_transactions
                    WHERE user_id = $1 AND source = $2
                """, user_id, source)
                if count < required_value:
                    return False
                    
            elif criterion == 'total_commits':
                if user['total_commits'] < required_value:
                    return False
                    
            elif criterion == 'streak_days':
                if user['current_streak'] < required_value:
                    return False
                    
            elif criterion == 'flow_duration':
                if user['total_flow_time'] < required_value:
                    return False
                    
            elif criterion == 'daily_xp':
                today_xp = await conn.fetchval("""
                    SELECT COALESCE(SUM(amount), 0) FROM xp_transactions
                    WHERE user_id = $1 AND DATE(timestamp) = CURRENT_DATE
                """, user_id)
                if today_xp < required_value:
                    return False
        
        return True
    
    async def _get_achievement_progress(self, conn: asyncpg.Connection, user_id: str) -> Dict[str, Any]:
        """Get progress towards achievements"""
        user = await conn.fetchrow("SELECT * FROM user_profiles WHERE id = $1", user_id)
        
        # Calculate progress for common achievement types
        total_commits = user['total_commits']
        current_streak = user['current_streak']
        total_flow_time = user['total_flow_time']
        
        return {
            'commits': total_commits,
            'streak': current_streak,
            'flow_time': total_flow_time,
            'level': user['level'],
            'xp': user['total_xp']
        }
    
    async def _get_session_stats(self, conn: asyncpg.Connection, user_id: str) -> Dict[str, Any]:
        """Get current session statistics"""
        today_stats = await conn.fetchrow("""
            SELECT 
                COALESCE(SUM(amount), 0) as xp_today,
                COUNT(*) as activities_today
            FROM xp_transactions
            WHERE user_id = $1 AND DATE(timestamp) = CURRENT_DATE
        """, user_id)
        
        return dict(today_stats) if today_stats else {'xp_today': 0, 'activities_today': 0}
    
    async def _cache_user_profile(self, session_id: str, user_id: str):
        """Cache user profile for fast access"""
        async with self.db_pool.acquire() as conn:
            user_data = await conn.fetchrow("SELECT * FROM user_profiles WHERE id = $1", user_id)
            
        if user_data:
            await self.redis.setex(
                f"user_profile:{session_id}",
                3600,  # 1 hour
                json.dumps(dict(user_data), default=str)
            )