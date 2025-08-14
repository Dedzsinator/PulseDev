"""
Integration services for Slack and Jira
"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import aiohttp
import asyncpg
from ..models.teams import TeamActivity


class SlackIntegrationService:
    """Service for Slack webhook integrations"""

    def __init__(self, db: asyncpg.Connection):
        self.db = db

    async def send_team_notification(
        self,
        team_id: str,
        message: str,
        emoji: str = "🔔",
        color: str = "good"
    ) -> bool:
        """Send notification to team Slack channel"""
        try:
            # Get team Slack configuration
            team_config = await self.db.fetchrow("""
                SELECT slack_webhook_url, slack_channel, name
                FROM team_rooms
                WHERE id = $1 AND slack_webhook_url IS NOT NULL
            """, team_id)

            if not team_config or not team_config['slack_webhook_url']:
                return False

            # Prepare Slack message
            slack_payload = {
                "channel": team_config['slack_channel'] or "#general",
                "username": "PulseDev+ Bot",
                "icon_emoji": emoji,
                "attachments": [{
                    "color": color,
                    "title": f"Team: {team_config['name']}",
                    "text": message,
                    "footer": "PulseDev+",
                    "ts": int(datetime.utcnow().timestamp())
                }]
            }

            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    team_config['slack_webhook_url'],
                    json=slack_payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    return response.status == 200

        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
            return False

    async def notify_sprint_started(self, team_id: str, sprint_name: str, sprint_goal: str):
        """Notify team when sprint starts"""
        message = f"🚀 **Sprint Started!**\n**{sprint_name}**\n*Goal:* {sprint_goal}"
        await self.send_team_notification(team_id, message, "🚀", "good")

    async def notify_sprint_completed(self, team_id: str, sprint_name: str, velocity: int):
        """Notify team when sprint completes"""
        message = f"🏁 **Sprint Completed!**\n**{sprint_name}**\n*Velocity:* {velocity} story points"
        await self.send_team_notification(team_id, message, "🏁", "good")

    async def notify_member_joined(self, team_id: str, username: str, role: str):
        """Notify team when new member joins"""
        message = f"👋 **New Team Member!**\n{username} joined as {role.replace('_', ' ').title()}"
        await self.send_team_notification(team_id, message, "👋", "good")

    async def notify_achievement_unlocked(self, team_id: str, username: str, achievement: str):
        """Notify team when member unlocks achievement"""
        message = f"🏆 **Achievement Unlocked!**\n{username} earned: {achievement}"
        await self.send_team_notification(team_id, message, "🏆", "good")

    async def send_daily_standup_reminder(self, team_id: str):
        """Send daily standup reminder"""
        message = "📅 **Daily Standup Reminder**\nTime for your daily standup meeting!"
        await self.send_team_notification(team_id, message, "📅", "warning")

    async def send_retrospective_summary(self, team_id: str, sprint_id: str):
        """Send sprint retrospective summary"""
        try:
            # Get retrospective items
            retro_items = await self.db.fetch("""
                SELECT category, content FROM retrospective_items
                WHERE team_id = $1 AND sprint_id = $2
                ORDER BY category, created_at
            """, team_id, sprint_id)

            if not retro_items:
                return

            # Group by category
            went_well = [item['content'] for item in retro_items if item['category'] == 'went_well']
            didnt_go_well = [item['content'] for item in retro_items if item['category'] == 'didnt_go_well']
            action_items = [item['content'] for item in retro_items if item['category'] == 'action_items']

            message = "📊 **Sprint Retrospective Summary**\n\n"

            if went_well:
                message += "✅ **What Went Well:**\n" + "\n".join(f"• {item}" for item in went_well[:3]) + "\n\n"

            if didnt_go_well:
                message += "⚠️ **What Didn't Go Well:**\n" + "\n".join(f"• {item}" for item in didnt_go_well[:3]) + "\n\n"

            if action_items:
                message += "📋 **Action Items:**\n" + "\n".join(f"• {item}" for item in action_items[:3])

            await self.send_team_notification(team_id, message, "📊", "good")

        except Exception as e:
            print(f"Failed to send retrospective summary: {e}")


class JiraIntegrationService:
    """Service for Jira API integrations"""

    def __init__(self, db: asyncpg.Connection):
        self.db = db

    async def get_team_jira_config(self, team_id: str) -> Optional[Dict[str, str]]:
        """Get team's Jira configuration"""
        config = await self.db.fetchrow("""
            SELECT jira_base_url, jira_project_key
            FROM team_rooms
            WHERE id = $1 AND jira_base_url IS NOT NULL AND jira_project_key IS NOT NULL
        """, team_id)

        if config:
            return {
                'base_url': config['jira_base_url'],
                'project_key': config['jira_project_key']
            }
        return None

    async def create_jira_ticket(
        self,
        team_id: str,
        title: str,
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium"
    ) -> Optional[str]:
        """Create a Jira ticket from user story"""
        try:
            jira_config = await self.get_team_jira_config(team_id)
            if not jira_config:
                return None

            # Note: In real implementation, you'd use Jira API with proper authentication
            # This is a mock implementation showing the structure

            jira_payload = {
                "fields": {
                    "project": {"key": jira_config['project_key']},
                    "summary": title,
                    "description": description,
                    "issuetype": {"name": issue_type},
                    "priority": {"name": priority},
                    "labels": ["pulsedev", "auto-created"]
                }
            }

            # In real implementation, use Jira REST API
            # For now, return mock ticket ID
            mock_ticket_id = f"{jira_config['project_key']}-{hash(title) % 1000}"

            print(f"Mock Jira ticket created: {mock_ticket_id}")
            return mock_ticket_id

        except Exception as e:
            print(f"Failed to create Jira ticket: {e}")
            return None

    async def sync_user_story_to_jira(self, team_id: str, story_id: str) -> Optional[str]:
        """Sync user story to Jira as ticket"""
        try:
            # Get user story details
            story = await self.db.fetchrow("""
                SELECT title, description, story_points, status
                FROM user_stories
                WHERE id = $1 AND team_id = $2
            """, story_id, team_id)

            if not story:
                return None

            # Create description with story points
            jira_description = f"{story['description']}\n\nStory Points: {story['story_points']}"

            # Create Jira ticket
            ticket_id = await self.create_jira_ticket(
                team_id=team_id,
                title=story['title'],
                description=jira_description,
                issue_type="Story"
            )

            if ticket_id:
                # Store Jira ticket ID in user story
                await self.db.execute("""
                    UPDATE user_stories
                    SET jira_ticket_id = $1
                    WHERE id = $2
                """, ticket_id, story_id)

            return ticket_id

        except Exception as e:
            print(f"Failed to sync story to Jira: {e}")
            return None

    async def update_jira_ticket_status(self, team_id: str, ticket_id: str, new_status: str):
        """Update Jira ticket status when story status changes"""
        try:
            jira_config = await self.get_team_jira_config(team_id)
            if not jira_config:
                return False

            # Map PulseDev status to Jira status
            status_mapping = {
                'backlog': 'To Do',
                'in_progress': 'In Progress',
                'review': 'In Review',
                'done': 'Done'
            }

            jira_status = status_mapping.get(new_status, 'To Do')

            # In real implementation, update Jira ticket status via API
            print(f"Mock Jira update: {ticket_id} → {jira_status}")
            return True

        except Exception as e:
            print(f"Failed to update Jira ticket: {e}")
            return False


class IntegrationOrchestrator:
    """Orchestrates all team integrations"""

    def __init__(self, db: asyncpg.Connection):
        self.db = db
        self.slack = SlackIntegrationService(db)
        self.jira = JiraIntegrationService(db)

    async def handle_team_event(self, team_id: str, event_type: str, data: Dict[str, Any]):
        """Handle team events and trigger appropriate integrations"""
        try:
            if event_type == "member_joined":
                await self.slack.notify_member_joined(
                    team_id, data['username'], data['role']
                )

            elif event_type == "sprint_started":
                await self.slack.notify_sprint_started(
                    team_id, data['sprint_name'], data['sprint_goal']
                )

            elif event_type == "sprint_completed":
                await self.slack.notify_sprint_completed(
                    team_id, data['sprint_name'], data['velocity']
                )
                await self.slack.send_retrospective_summary(team_id, data['sprint_id'])

            elif event_type == "story_created":
                # Auto-sync to Jira if configured
                jira_ticket_id = await self.jira.sync_user_story_to_jira(
                    team_id, data['story_id']
                )
                if jira_ticket_id:
                    await self.slack.send_team_notification(
                        team_id,
                        f"📝 New story synced to Jira: {jira_ticket_id}",
                        "📝"
                    )

            elif event_type == "story_status_changed":
                await self.jira.update_jira_ticket_status(
                    team_id, data.get('jira_ticket_id'), data['new_status']
                )

            elif event_type == "achievement_unlocked":
                await self.slack.notify_achievement_unlocked(
                    team_id, data['username'], data['achievement']
                )

        except Exception as e:
            print(f"Failed to handle team event {event_type}: {e}")

    async def schedule_daily_reminders(self):
        """Schedule daily standup reminders for all teams"""
        try:
            # Get teams with Slack integration
            teams = await self.db.fetch("""
                SELECT id FROM team_rooms
                WHERE slack_webhook_url IS NOT NULL AND is_active = true
            """)

            for team in teams:
                await self.slack.send_daily_standup_reminder(team['id'])
                # Add small delay to avoid rate limiting
                await asyncio.sleep(1)

        except Exception as e:
            print(f"Failed to send daily reminders: {e}")


# Background task for handling integrations
async def process_team_integration_events(db: asyncpg.Connection):
    """Background task to process integration events"""
    orchestrator = IntegrationOrchestrator(db)

    # In real implementation, this would listen to a message queue
    # For now, it's a placeholder for the integration system
    print("Team integration orchestrator started")

    # Example: Schedule daily reminders
    await orchestrator.schedule_daily_reminders()
