import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx

from config import Config
from models.events import ContextEvent, AIPromptRequest

class AIService:
    def __init__(self):
        self.config = Config()
        print(f"🤖 AI Service initialized with NVIDIA NIM")
        print(f"   Model: {self.config.DEFAULT_MODEL}")
        print(f"   Base URL: {self.config.NVIDIA_NIM_BASE_URL}")

    async def generate_context_prompt(self, events: List[ContextEvent], request: AIPromptRequest) -> str:
        """Generate a comprehensive context prompt from recent events"""

        # Group events by type
        file_events = [e for e in events if e.agent == "file"]
        editor_events = [e for e in events if e.agent == "editor"]
        terminal_events = [e for e in events if e.agent == "terminal"]
        git_events = [e for e in events if e.agent == "git"]

        # Build context sections
        prompt_sections = [
            "# Developer Context Analysis",
            "",
            "## Current Session Overview",
            f"Session ID: {request.session_id}",
            f"Time Window: Last {request.context_window_minutes} minutes",
            f"Generated at: {datetime.utcnow().isoformat()}",
            ""
        ]

        # Recent file activity
        if file_events:
            prompt_sections.extend([
                "## Recent File Activity",
                ""
            ])
            for event in file_events[-10:]:  # Last 10 file events
                prompt_sections.append(f"- {event.timestamp}: {event.type} - {event.payload.get('file_path', 'unknown')}")
            prompt_sections.append("")

        # Editor activity
        if editor_events:
            prompt_sections.extend([
                "## Editor Activity",
                ""
            ])

            # Test runs and their results
            test_events = [e for e in editor_events if e.type == "test_run"]
            if test_events:
                prompt_sections.append("### Test Results:")
                for event in test_events[-5:]:
                    status = event.payload.get('status', 'unknown')
                    output = event.payload.get('output', '')[:200]  # Truncate long output
                    prompt_sections.append(f"- {event.timestamp}: {status}")
                    if output:
                        prompt_sections.append(f"  Output: {output}")
                prompt_sections.append("")

            # Current cursor position and file
            cursor_events = [e for e in editor_events if e.type == "cursor_moved"]
            if cursor_events:
                latest_cursor = cursor_events[-1]
                prompt_sections.extend([
                    "### Current Position:",
                    f"- File: {latest_cursor.payload.get('file_path', 'unknown')}",
                    f"- Line: {latest_cursor.payload.get('line', 'unknown')}",
                    f"- Column: {latest_cursor.payload.get('column', 'unknown')}",
                    ""
                ])

        # Terminal activity
        if terminal_events and request.include_terminal:
            prompt_sections.extend([
                "## Terminal Activity",
                ""
            ])
            for event in terminal_events[-10:]:
                if event.type == "command_executed":
                    cmd = event.payload.get('command', 'unknown')
                    exit_code = event.payload.get('exit_code', 'unknown')
                    prompt_sections.append(f"- {event.timestamp}: `{cmd}` (exit: {exit_code})")
            prompt_sections.append("")

        # Git activity
        if git_events and request.include_git:
            prompt_sections.extend([
                "## Git Activity",
                ""
            ])
            for event in git_events[-5:]:
                if event.type == "commit_created":
                    msg = event.payload.get('message', 'unknown')
                    prompt_sections.append(f"- {event.timestamp}: Commit - {msg}")
                elif event.type == "branch_switched":
                    branch = event.payload.get('branch', 'unknown')
                    prompt_sections.append(f"- {event.timestamp}: Switched to {branch}")
            prompt_sections.append("")

        # Error analysis
        error_events = [e for e in events if 'error' in str(e.payload).lower()]
        if error_events and request.include_errors:
            prompt_sections.extend([
                "## Recent Errors",
                ""
            ])
            for event in error_events[-5:]:
                error_msg = str(event.payload.get('error', event.payload))[:300]
                prompt_sections.append(f"- {event.timestamp}: {error_msg}")
            prompt_sections.append("")

        # Custom context
        if request.custom_context:
            prompt_sections.extend([
                "## Additional Context",
                "",
                request.custom_context,
                ""
            ])

        return "\n".join(prompt_sections)

    async def detect_stuck_state(self, events: List[ContextEvent]) -> Optional[Dict[str, Any]]:
        """Detect if developer is in a stuck state"""

        # Pattern 1: Looping file edits (same file edited multiple times quickly)
        file_edits = {}
        for event in events:
            if event.type == "file_modified":
                file_path = event.payload.get('file_path')
                if file_path:
                    file_edits.setdefault(file_path, []).append(event.timestamp)

        for file_path, timestamps in file_edits.items():
            if len(timestamps) > 5:  # More than 5 edits
                return {
                    "pattern": "looping_edits",
                    "file": file_path,
                    "edit_count": len(timestamps),
                    "confidence": min(len(timestamps) / 10.0, 1.0)
                }

        # Pattern 2: Repeated test failures
        test_events = [e for e in events if e.type == "test_run"]
        failed_tests = [e for e in test_events if e.payload.get('status') == 'failed']

        if len(failed_tests) > 3:
            return {
                "pattern": "repeated_errors",
                "failed_test_count": len(failed_tests),
                "confidence": min(len(failed_tests) / 5.0, 1.0)
            }

        # Pattern 3: Long idle with failures (no activity but last test failed)
        if test_events and len(events) < 5:  # Low activity
            last_test = test_events[-1]
            if last_test.payload.get('status') == 'failed':
                return {
                    "pattern": "idle_with_failures",
                    "last_test_status": "failed",
                    "confidence": 0.8
                }

        return None

    async def generate_ai_suggestion(self, prompt: str, context_type: str = "debug") -> str:
        """Generate AI suggestion using NVIDIA NIM"""

        system_prompts = {
            "debug": "You are a senior developer helping debug code issues. Analyze the context and provide specific, actionable suggestions.",
            "commit": "You are helping write commit messages. Create clear, conventional commit messages based on the changes.",
            "branch": "You are helping suggest branch names. Create descriptive branch names following conventions.",
            "flow": "You are analyzing developer productivity. Provide insights about work patterns and suggestions for improvement."
        }

        system_prompt = system_prompts.get(context_type, system_prompts["debug"])

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.config.NVIDIA_NIM_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.config.NVIDIA_NIM_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.config.DEFAULT_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 500,
                        "temperature": 0.3,
                        "stream": False
                    }
                )

                if response.status_code != 200:
                    error_detail = f"Status: {response.status_code}, Response: {response.text[:200]}"
                    print(f"❌ NVIDIA NIM API error: {error_detail}")
                    return f"AI service temporarily unavailable (API error: {response.status_code})"

                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                if not content:
                    print(f"❌ Empty response from NVIDIA NIM API")
                    return "AI service returned empty response"

                return content.strip()

        except httpx.TimeoutException:
            print("❌ NVIDIA NIM API request timed out")
            return "AI service timed out - please try again"
        except httpx.RequestError as e:
            print(f"❌ NVIDIA NIM API request error: {str(e)}")
            return "AI service connection error - please try again"
        except Exception as e:
            print(f"❌ Unexpected NVIDIA NIM API error: {str(e)}")
            return f"AI service error: {str(e)}"

    async def generate_commit_message(self, git_diff: str, context_events: List[ContextEvent]) -> str:
        """Generate commit message from git diff and context"""

        # Extract test results and error context
        test_events = [e for e in context_events if e.type == "test_run"]
        last_test = test_events[-1] if test_events else None

        prompt = f"""
Generate a conventional commit message for these changes:

## Git Diff:
{git_diff[:2000]}  # Truncate very long diffs

## Context:
- Tests: {'PASSED' if last_test and last_test.payload.get('status') == 'passed' else 'FAILED/UNKNOWN'}
- Files changed: {len(git_diff.split('diff --git')) - 1}

Rules:
- Use conventional commit format: type(scope): description
- Be specific and descriptive
- Mention test status if relevant
- Keep under 72 characters for the title
"""

        return await self.generate_ai_suggestion(prompt, "commit")

    async def suggest_branch_name(self, context_events: List[ContextEvent]) -> str:
        """Suggest branch name based on recent activity"""

        # Look for TODO comments, Jira IDs, or file patterns
        file_events = [e for e in context_events if e.agent == "file"]
        recent_files = [e.payload.get('file_path', '') for e in file_events[-10:]]

        prompt = f"""
Suggest a git branch name based on recent development activity:

## Recent Files Modified:
{chr(10).join(f"- {f}" for f in recent_files if f)}

## Context Events:
{len(context_events)} events in the last session

Rules:
- Use kebab-case format
- Be descriptive but concise
- Include feature/fix/refactor prefix
- Examples: feature/user-auth, fix/login-validation, refactor/api-client
"""

        suggestion = await self.generate_ai_suggestion(prompt, "branch")

        # Clean up the suggestion to ensure it's a valid branch name
        clean_name = suggestion.strip().lower()
        clean_name = ''.join(c if c.isalnum() or c in '-_/' else '-' for c in clean_name)

        return clean_name[:50]  # Limit length

    async def analyze_productivity_patterns(self, events: List[ContextEvent]) -> Dict[str, Any]:
        """Analyze productivity patterns using NVIDIA NIM"""

        # Group events by hour
        hourly_activity = {}
        for event in events:
            hour = event.timestamp.hour
            hourly_activity.setdefault(hour, []).append(event)

        # Calculate flow states
        flow_periods = []
        current_flow = None

        for event in sorted(events, key=lambda e: e.timestamp):
            if hasattr(event, 'flow_state') and event.flow_state:
                if event.flow_state == "in_flow":
                    if not current_flow:
                        current_flow = {"start": event.timestamp, "events": []}
                    current_flow["events"].append(event)
                elif current_flow:
                    current_flow["end"] = event.timestamp
                    current_flow["duration"] = (current_flow["end"] - current_flow["start"]).total_seconds() / 60
                    flow_periods.append(current_flow)
                    current_flow = None

        # Generate analysis prompt
        prompt = f"""
Analyze this developer's productivity patterns:

## Activity Summary:
- Total events: {len(events)}
- Time span: {events[0].timestamp.strftime('%Y-%m-%d %H:%M')} to {events[-1].timestamp.strftime('%Y-%m-%d %H:%M')}
- Flow periods detected: {len(flow_periods)}
- Average flow duration: {sum(fp.get('duration', 0) for fp in flow_periods) / len(flow_periods) if flow_periods else 0:.1f} minutes

## Hourly Distribution:
{chr(10).join(f"- Hour {hour}: {len(events_list)} events" for hour, events_list in sorted(hourly_activity.items()))}

Provide insights about:
1. Peak productivity hours
2. Flow state patterns
3. Recommendations for improvement
4. Warning signs or concerns
"""

        analysis = await self.generate_ai_suggestion(prompt, "flow")

        return {
            "analysis": analysis,
            "metrics": {
                "total_events": len(events),
                "flow_periods": len(flow_periods),
                "avg_flow_duration": sum(fp.get('duration', 0) for fp in flow_periods) / len(flow_periods) if flow_periods else 0,
                "peak_hour": max(hourly_activity.keys(), key=lambda k: len(hourly_activity[k])) if hourly_activity else None,
                "hourly_distribution": {str(k): len(v) for k, v in hourly_activity.items()}
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check AI service health"""
        try:
            test_prompt = "Respond with 'OK' if you can process this request."
            response = await self.generate_ai_suggestion(test_prompt, "debug")

            return {
                "status": "healthy",
                "provider": "nvidia_nim",
                "model": self.config.DEFAULT_MODEL,
                "base_url": self.config.NVIDIA_NIM_BASE_URL,
                "test_response": response[:50] + "..." if len(response) > 50 else response
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "nvidia_nim",
                "model": self.config.DEFAULT_MODEL,
                "base_url": self.config.NVIDIA_NIM_BASE_URL,
                "error": str(e)
            }
