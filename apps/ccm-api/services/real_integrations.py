# 🔗 Slack & Jira Integration Setup Guide

This guide explains how to connect PulseDev+ with Slack and Jira to enable seamless team collaboration and ticket synchronization.

## 🎯 Overview

PulseDev+ integrates with:
- **Slack**: Real-time team notifications via webhooks
- **Jira**: Ticket creation and status synchronization via REST API

## 🔧 Slack Integration Setup

### Option 1: Incoming Webhooks (Recommended - Simplest)

1. **Create a Slack App**:
   - Go to [Slack API Apps](https://api.slack.com/apps)
   - Click "Create New App" → "From scratch"
   - Name your app (e.g., "PulseDev+ Bot")
   - Select your workspace

2. **Enable Incoming Webhooks**:
   - In your app settings, go to "Incoming Webhooks"
   - Toggle "Activate Incoming Webhooks" to ON
   - Click "Add New Webhook to Workspace"
   - Select the channel for notifications (e.g., #development)
   - Copy the webhook URL (starts with `https://hooks.slack.com/services/`)

3. **Configure in PulseDev+**:
   ```
   Webhook URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   Channel: #development (or your chosen channel)
   ```

### Option 2: Bot Token (Advanced - More Features)

1. **Create Bot User**:
   - In your Slack app, go to "OAuth & Permissions"
   - Add Bot Token Scopes:
     - `chat:write` - Send messages
     - `chat:write.public` - Send to public channels
     - `channels:read` - List public channels
     - `groups:read` - List private channels

2. **Install to Workspace**:
   - Click "Install to Workspace"
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

3. **Environment Variables**:
   ```bash
   SLACK_BOT_TOKEN=xoxb-your-bot-token-here
   SLACK_SIGNING_SECRET=your-signing-secret-here
   ```

## 🎫 Jira Integration Setup

### Step 1: Create Jira API Token

1. **Generate API Token**:
   - Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
   - Click "Create API token"
   - Give it a name (e.g., "PulseDev+ Integration")
   - Copy the token (you won't see it again!)

2. **Get Your Jira Details**:
   - **Base URL**: Your Jira instance URL (e.g., `https://yourcompany.atlassian.net`)
   - **Project Key**: The key of your project (e.g., "PROJ", "DEV")
   - **Email**: Your Jira account email

### Step 2: Environment Configuration

Add these to your `.env` file or environment variables:

```bash
# Jira Configuration
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token-here
JIRA_PROJECT_KEY=PROJ
```

## 🚀 Implementation Examples

### Updated Integration Service

Here's how to enhance the integration service with real API calls:

<function_calls>
<invoke name="create_file">
<parameter name="content">"""
Enhanced integration services with real API authentication
"""
import os
import base64
from typing import Dict, Any, Optional
import aiohttp
import asyncpg


class RealSlackIntegrationService:
    """Real Slack integration with bot tokens"""

    def __init__(self, db: asyncpg.Connection):
        self.db = db
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")

    async def send_message_with_bot(
        self,
        channel: str,
        message: str,
        attachments: Optional[list] = None
    ) -> bool:
        """Send message using Slack Bot API"""
        if not self.bot_token:
            return False

        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "channel": channel,
            "text": message,
            "username": "PulseDev+ Bot",
            "icon_emoji": ":robot_face:"
        }

        if attachments:
            payload["attachments"] = attachments

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://slack.com/api/chat.postMessage",
                json=payload,
                headers=headers
            ) as response:
                result = await response.json()
                return result.get("ok", False)


class RealJiraIntegrationService:
    """Real Jira integration with API authentication"""

    def __init__(self, db: asyncpg.Connection):
        self.db = db
        self.base_url = os.getenv("JIRA_BASE_URL")
        self.email = os.getenv("JIRA_EMAIL")
        self.api_token = os.getenv("JIRA_API_TOKEN")

    def _get_auth_header(self) -> str:
        """Generate basic auth header for Jira API"""
        auth_string = f"{self.email}:{self.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        return f"Basic {auth_b64}"

    async def create_jira_ticket(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task"
    ) -> Optional[str]:
        """Create actual Jira ticket via REST API"""
        if not all([self.base_url, self.email, self.api_token]):
            return None

        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {"name": issue_type},
                "labels": ["pulsedev", "auto-created"]
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/rest/api/3/issue",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        return result["key"]  # Returns ticket ID like "PROJ-123"
                    else:
                        error_text = await response.text()
                        print(f"Jira API error: {response.status} - {error_text}")
                        return None

        except Exception as e:
            print(f"Failed to create Jira ticket: {e}")
            return None

    async def update_ticket_status(
        self,
        ticket_id: str,
        status_name: str
    ) -> bool:
        """Update Jira ticket status"""
        if not all([self.base_url, self.email, self.api_token]):
            return False

        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json"
        }

        # Get available transitions
        try:
            async with aiohttp.ClientSession() as session:
                # Get transitions
                async with session.get(
                    f"{self.base_url}/rest/api/3/issue/{ticket_id}/transitions",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return False

                    transitions = await response.json()

                    # Find transition ID for desired status
                    transition_id = None
                    for transition in transitions["transitions"]:
                        if transition["to"]["name"].lower() == status_name.lower():
                            transition_id = transition["id"]
                            break

                    if not transition_id:
                        return False

                    # Execute transition
                    payload = {
                        "transition": {"id": transition_id}
                    }

                    async with session.post(
                        f"{self.base_url}/rest/api/3/issue/{ticket_id}/transitions",
                        json=payload,
                        headers=headers
                    ) as response:
                        return response.status == 204

        except Exception as e:
            print(f"Failed to update Jira ticket status: {e}")
            return False
