import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from models.events import ContextEvent, FlowSession

class EnergyService:
    def __init__(self):
        self.scoring_weights = {
            "flow_time": 0.25,
            "test_pass_rate": 0.20,
            "commit_quality": 0.15,
            "context_stability": 0.15,
            "error_frequency": -0.10,
            "distraction_rate": -0.10,
            "productivity_momentum": 0.05
        }

    async def calculate_energy_score(self, events: List[ContextEvent], session_duration_hours: float) -> Dict[str, Any]:
        """Calculate comprehensive energy score"""

        # Initialize score components
        scores = {
            "flow_time": 0,
            "test_pass_rate": 0,
            "commit_quality": 0,
            "context_stability": 0,
            "error_frequency": 0,
            "distraction_rate": 0,
            "productivity_momentum": 0
        }

        # 1. Flow Time Score (0-100)
        flow_events = [e for e in events if e.type in ["flow_start", "flow_end"]]
        total_flow_time = await self._calculate_flow_time(flow_events)
        scores["flow_time"] = min((total_flow_time / session_duration_hours) * 100, 100)

        # 2. Test Pass Rate (0-100)
        test_events = [e for e in events if e.type == "test_run"]
        scores["test_pass_rate"] = await self._calculate_test_pass_rate(test_events)

        # 3. Commit Quality Score (0-100)
        commit_events = [e for e in events if e.type == "commit_created"]
        scores["commit_quality"] = await self._calculate_commit_quality(commit_events, events)

        # 4. Context Stability (0-100)
        scores["context_stability"] = await self._calculate_context_stability(events)

        # 5. Error Frequency (penalty, 0-100 where higher is worse)
        scores["error_frequency"] = await self._calculate_error_frequency(events)

        # 6. Distraction Rate (penalty, 0-100 where higher is worse)
        scores["distraction_rate"] = await self._calculate_distraction_rate(events)

        # 7. Productivity Momentum (0-100)
        scores["productivity_momentum"] = await self._calculate_productivity_momentum(events)

        # Calculate weighted final score
        final_score = 0
        for component, score in scores.items():
            weight = self.scoring_weights[component]
            final_score += score * weight

        # Ensure score is between 0-100
        final_score = max(0, min(100, final_score))

        return {
            "final_score": round(final_score, 2),
            "components": scores,
            "weights": self.scoring_weights,
            "session_duration_hours": session_duration_hours,
            "grade": self._get_energy_grade(final_score),
            "insights": await self._generate_insights(scores)
        }

    async def _calculate_flow_time(self, flow_events: List[ContextEvent]) -> float:
        """Calculate total time spent in flow state"""
        total_flow_hours = 0
        flow_start = None

        for event in sorted(flow_events, key=lambda x: x.timestamp):
            if event.type == "flow_start":
                flow_start = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
            elif event.type == "flow_end" and flow_start:
                flow_end = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
                total_flow_hours += (flow_end - flow_start).total_seconds() / 3600
                flow_start = None

        return total_flow_hours

    async def _calculate_test_pass_rate(self, test_events: List[ContextEvent]) -> float:
        """Calculate test pass rate"""
        if not test_events:
            return 50  # Neutral score if no tests

        passed_tests = sum(1 for e in test_events if e.payload.get('status') == 'passed')
        pass_rate = (passed_tests / len(test_events)) * 100

        return pass_rate

    async def _calculate_commit_quality(self, commit_events: List[ContextEvent], all_events: List[ContextEvent]) -> float:
        """Calculate commit quality score"""
        if not commit_events:
            return 50  # Neutral if no commits

        quality_score = 0

        for commit in commit_events:
            commit_score = 50  # Base score

            # Good commit messages
            message = commit.payload.get('message', '')
            if len(message) > 20:  # Descriptive message
                commit_score += 10
            if any(word in message.lower() for word in ['fix', 'add', 'update', 'refactor']):
                commit_score += 10

            # Commits with tests
            files = commit.payload.get('files', [])
            if any('test' in f.lower() for f in files):
                commit_score += 15

            # Small, focused commits (fewer files = better)
            if len(files) <= 3:
                commit_score += 10
            elif len(files) > 10:
                commit_score -= 10

            quality_score += min(commit_score, 100)

        return quality_score / len(commit_events)

    async def _calculate_context_stability(self, events: List[ContextEvent]) -> float:
        """Calculate context stability (fewer file switches = better)"""
        file_switches = 0
        last_file = None

        for event in events:
            if event.type in ["file_modified", "editor_focus"]:
                current_file = event.payload.get("file_path")
                if current_file and current_file != last_file:
                    file_switches += 1
                    last_file = current_file

        # Score inversely related to switches (fewer switches = higher score)
        if file_switches == 0:
            return 100

        stability_score = max(0, 100 - (file_switches * 2))
        return stability_score

    async def _calculate_error_frequency(self, events: List[ContextEvent]) -> float:
        """Calculate error frequency (penalty score)"""
        error_events = [e for e in events if 'error' in str(e.payload).lower() or 'failed' in str(e.payload).lower()]

        if not error_events:
            return 0  # No penalty

        # Penalty increases with error frequency
        error_rate = len(error_events) / max(len(events), 1)
        penalty = min(error_rate * 500, 100)  # Cap at 100

        return penalty

    async def _calculate_distraction_rate(self, events: List[ContextEvent]) -> float:
        """Calculate distraction rate (penalty score)"""
        distraction_events = [e for e in events if e.agent == "browser" or e.type in ["editor_blur"]]

        if not distraction_events:
            return 0  # No penalty

        distraction_rate = len(distraction_events) / max(len(events), 1)
        penalty = min(distraction_rate * 300, 100)  # Cap at 100

        return penalty

    async def _calculate_productivity_momentum(self, events: List[ContextEvent]) -> float:
        """Calculate productivity momentum"""
        # Look for patterns of increasing activity
        time_buckets = {}

        for event in events:
            try:
                hour = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')).hour
                time_buckets.setdefault(hour, 0)
                time_buckets[hour] += 1
            except:
                continue

        if len(time_buckets) < 2:
            return 50  # Neutral if not enough data

        # Check if activity is increasing over time
        hours = sorted(time_buckets.keys())
        activity_trend = 0

        for i in range(1, len(hours)):
            if time_buckets[hours[i]] > time_buckets[hours[i-1]]:
                activity_trend += 1
            else:
                activity_trend -= 1

        momentum_score = 50 + (activity_trend * 10)  # Base 50, +/- 10 per trend
        return max(0, min(100, momentum_score))

    def _get_energy_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        else:
            return "D"

    async def _generate_insights(self, scores: Dict[str, float]) -> List[str]:
        """Generate insights based on scores"""
        insights = []

        if scores["flow_time"] > 70:
            insights.append("🔥 Excellent flow state maintenance")
        elif scores["flow_time"] < 30:
            insights.append("⚠️ Low flow time - consider minimizing distractions")

        if scores["test_pass_rate"] > 80:
            insights.append("✅ High test pass rate - good code quality")
        elif scores["test_pass_rate"] < 50:
            insights.append("🔴 Low test pass rate - focus on testing")

        if scores["context_stability"] < 40:
            insights.append("🔀 High context switching - try staying focused on fewer files")

        if scores["error_frequency"] > 50:
            insights.append("🐛 High error frequency - take breaks and double-check code")

        if scores["productivity_momentum"] > 70:
            insights.append("📈 Strong productivity momentum")

        return insights

    async def get_energy_trends(self, session_id: str, days: int = 7) -> Dict[str, Any]:
        """Get energy trends over time"""
        # This would typically query the database for historical energy scores
        # For now, return placeholder data

        return {
            "average_score": 75.5,
            "trend": "increasing",
            "best_day": "Tuesday",
            "peak_hours": ["9-11 AM", "2-4 PM"],
            "improvement_areas": ["test_pass_rate", "context_stability"],
            "streaks": {
                "current_good_days": 3,
                "best_streak": 7
            }
        }
