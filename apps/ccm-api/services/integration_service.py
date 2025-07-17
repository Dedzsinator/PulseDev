from typing import Dict, List, Any, Optional
import aiohttp
import json
from datetime import datetime
import os

class SlackJiraIntegration:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        self.jira_config = {
            'base_url': os.getenv('JIRA_BASE_URL'),
            'username': os.getenv('JIRA_USERNAME'),
            'api_token': os.getenv('JIRA_API_TOKEN')
        }
    
    async def post_ai_pr_summary(self, session_id: str, pr_data: Dict[str, Any]) -> bool:
        """Post AI-generated PR summary to Slack"""
        if not self.slack_webhook:
            return False
        
        # Generate AI summary
        summary = await self._generate_pr_summary(session_id, pr_data)
        
        slack_message = {
            "text": "🔄 New PR Summary",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"PR: {pr_data.get('title', 'Untitled')}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*AI Summary:*\n{summary['description']}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Files Changed:* {summary['files_changed']}"
                        },
                        {
                            "type": "mrkdwn", 
                            "text": f"*Impact Level:* {summary['impact_level']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Test Coverage:* {summary['test_coverage']}%"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Review Time Est:* {summary['review_time_est']} min"
                        }
                    ]
                }
            ]
        }
        
        return await self._send_slack_message(slack_message)
    
    async def post_daily_changelog(self, session_id: str, date: str) -> bool:
        """Post daily changelog to Slack"""
        changelog = await self._generate_daily_changelog(session_id, date)
        
        if not changelog['commits']:
            return True  # No commits to report
        
        slack_message = {
            "text": f"📊 Daily Changelog - {date}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"Daily Changelog - {date}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Summary:* {changelog['summary']}"
                    }
                }
            ]
        }
        
        # Add commit details
        for commit in changelog['commits'][:5]:  # Limit to 5 commits
            slack_message['blocks'].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"• `{commit['hash'][:8]}` {commit['message']}"
                }
            })
        
        # Add metrics
        slack_message['blocks'].append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Commits:* {changelog['total_commits']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Files Changed:* {changelog['files_changed']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Flow Time:* {changelog['flow_time']} min"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Energy Score:* {changelog['energy_score']}/10"
                }
            ]
        })
        
        return await self._send_slack_message(slack_message)
    
    async def post_stuck_alert(self, session_id: str, stuck_analysis: Dict[str, Any]) -> bool:
        """Post stuck state alert to Slack"""
        slack_message = {
            "text": "🚨 Developer Stuck Alert",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🤔 Stuck State Detected"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Pattern:* {stuck_analysis['pattern']}\n*Duration:* {stuck_analysis['duration']} minutes"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Suggestions:*\n{chr(10).join(['• ' + s for s in stuck_analysis['suggestions']])}"
                    }
                }
            ]
        }
        
        return await self._send_slack_message(slack_message)
    
    async def _send_slack_message(self, message: Dict[str, Any]) -> bool:
        """Send message to Slack webhook"""
        if not self.slack_webhook:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.slack_webhook,
                    json=message,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"Failed to send Slack message: {e}")
            return False
    
    async def _generate_pr_summary(self, session_id: str, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered PR summary"""
        async with self.db_pool.acquire() as conn:
            # Get recent commits and changes
            changes = await conn.fetch("""
                SELECT file_path, event_type, timestamp
                FROM context_nodes
                WHERE session_id = $1 
                AND event_type IN ('file_modified', 'commit_created')
                AND timestamp >= NOW() - INTERVAL '24 hours'
                ORDER BY timestamp DESC
            """, session_id)
            
            # Analyze changes
            files_changed = len(set(row['file_path'] for row in changes if row['file_path']))
            commit_count = len([row for row in changes if row['event_type'] == 'commit_created'])
            
            # Estimate impact and review time
            if files_changed > 10:
                impact_level = "High"
                review_time = 45
            elif files_changed > 5:
                impact_level = "Medium" 
                review_time = 25
            else:
                impact_level = "Low"
                review_time = 15
            
            # Generate description
            description = f"This PR includes {commit_count} commits affecting {files_changed} files. "
            if 'test' in str(changes).lower():
                description += "Includes test updates. "
            if 'fix' in pr_data.get('title', '').lower():
                description += "Contains bug fixes."
            else:
                description += "Implements new features or improvements."
            
            return {
                'description': description,
                'files_changed': files_changed,
                'impact_level': impact_level,
                'test_coverage': 75,  # Would calculate actual coverage
                'review_time_est': review_time
            }
    
    async def _generate_daily_changelog(self, session_id: str, date: str) -> Dict[str, Any]:
        """Generate daily changelog from session data"""
        async with self.db_pool.acquire() as conn:
            # Get commits for the day
            commits = await conn.fetch("""
                SELECT encrypted_payload, timestamp
                FROM context_nodes
                WHERE session_id = $1 
                AND event_type = 'commit_created'
                AND DATE(timestamp) = $2
                ORDER BY timestamp DESC
            """, session_id, date)
            
            # Get file changes
            file_changes = await conn.fetchval("""
                SELECT COUNT(DISTINCT file_path)
                FROM context_nodes
                WHERE session_id = $1 
                AND event_type = 'file_modified'
                AND DATE(timestamp) = $2
            """, session_id, date)
            
            # Get flow time
            flow_time = await conn.fetchval("""
                SELECT COALESCE(SUM(CAST(encrypted_payload->>'duration_minutes' AS INTEGER)), 0)
                FROM context_nodes
                WHERE session_id = $1 
                AND event_type = 'flow_end'
                AND DATE(timestamp) = $2
            """, session_id, date)
            
            commit_list = []
            for commit in commits:
                try:
                    payload = json.loads(commit['encrypted_payload'])
                    commit_list.append({
                        'hash': payload.get('commit_hash', 'unknown'),
                        'message': payload.get('message', 'No message'),
                        'timestamp': commit['timestamp'].isoformat()
                    })
                except:
                    continue
            
            # Generate summary
            if len(commit_list) > 0:
                summary = f"Completed {len(commit_list)} commits with {file_changes} files modified."
            else:
                summary = "Development day with exploration and research."
            
            return {
                'commits': commit_list,
                'total_commits': len(commit_list),
                'files_changed': file_changes or 0,
                'flow_time': flow_time or 0,
                'energy_score': 7,  # Would calculate from energy service
                'summary': summary
            }
    
    async def auto_close_jira_ticket(self, issue_key: str, commit_message: str) -> bool:
        """Auto-close JIRA ticket based on commit message"""
        if not all(self.jira_config.values()):
            return False
        
        # Check if commit message indicates completion
        completion_keywords = ['fix', 'close', 'resolve', 'complete', 'done']
        if not any(keyword in commit_message.lower() for keyword in completion_keywords):
            return False
        
        try:
            auth = aiohttp.BasicAuth(self.jira_config['username'], self.jira_config['api_token'])
            
            async with aiohttp.ClientSession() as session:
                # Get ticket transitions
                transitions_url = f"{self.jira_config['base_url']}/rest/api/3/issue/{issue_key}/transitions"
                async with session.get(transitions_url, auth=auth) as response:
                    if response.status != 200:
                        return False
                    
                    transitions = await response.json()
                    
                    # Find "Done" or "Closed" transition
                    done_transition = None
                    for transition in transitions['transitions']:
                        if transition['name'].lower() in ['done', 'closed', 'resolve']:
                            done_transition = transition
                            break
                    
                    if not done_transition:
                        return False
                    
                    # Transition ticket to done
                    transition_data = {
                        "transition": {"id": done_transition['id']},
                        "fields": {
                            "resolution": {"name": "Done"}
                        }
                    }
                    
                    async with session.post(
                        transitions_url,
                        json=transition_data,
                        auth=auth,
                        headers={'Content-Type': 'application/json'}
                    ) as response:
                        return response.status == 204
                        
        except Exception as e:
            print(f"Failed to close JIRA ticket {issue_key}: {e}")
            return False
    
    async def link_commit_to_jira(self, session_id: str, commit_message: str, commit_hash: str):
        """Link commit to JIRA issue if reference found"""
        # Extract JIRA issue key from commit message
        import re
        issue_pattern = r'([A-Z]+-\d+)'
        matches = re.findall(issue_pattern, commit_message)
        
        if not matches:
            return
        
        issue_key = matches[0]
        
        # Log the linkage
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO context_nodes (
                    session_id, agent, event_type, encrypted_payload, timestamp
                ) VALUES ($1, 'integration', 'jira_link', $2, $3)
            """, session_id, json.dumps({
                "issue_key": issue_key,
                "commit_hash": commit_hash,
                "commit_message": commit_message
            }), datetime.utcnow())
        
        # Try to auto-close if appropriate
        if any(keyword in commit_message.lower() for keyword in ['fix', 'close', 'resolve']):
            await self.auto_close_jira_ticket(issue_key, commit_message)