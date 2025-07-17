from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from services.context_graph_service import TemporalContextGraph

class PairProgrammingGhost:
    def __init__(self, db_pool, context_graph: TemporalContextGraph):
        self.db_pool = db_pool
        self.context_graph = context_graph
    
    async def detect_looping_behavior(self, session_id: str) -> Dict[str, Any]:
        """Detect if developer is stuck in loops"""
        patterns = await self.context_graph.detect_patterns(session_id)
        
        if patterns['pattern_score'] > 5:
            suggestions = await self._generate_loop_suggestions(session_id, patterns)
            return {
                "stuck_detected": True,
                "loop_type": "repeated_edits",
                "confidence": min(patterns['pattern_score'] / 10.0, 1.0),
                "suggestions": suggestions,
                "looping_files": patterns['looping_files']
            }
        
        return {"stuck_detected": False}
    
    async def _generate_loop_suggestions(self, session_id: str, patterns: Dict) -> List[str]:
        """Generate suggestions for breaking out of loops"""
        suggestions = []
        
        if patterns['recent_errors'] > 3:
            suggestions.append("You've encountered multiple errors recently. Consider reviewing the error messages carefully.")
            suggestions.append("Try running tests in isolation to identify the specific failure point.")
        
        if len(patterns['looping_files']) > 0:
            file_list = ", ".join(patterns['looping_files'][:3])
            suggestions.append(f"You've been editing {file_list} repeatedly. Consider stepping back and reviewing the overall approach.")
            suggestions.append("Try creating a minimal test case to reproduce the issue.")
        
        suggestions.append("Consider checking your git history to see what was working before.")
        suggestions.append("Take a 5-minute break and come back with fresh perspective.")
        
        return suggestions
    
    async def analyze_thought_process(self, session_id: str, time_window: int = 30) -> Dict[str, Any]:
        """Analyze developer's thought process from context"""
        context_nodes = await self.context_graph.get_temporal_context(session_id, time_window)
        
        # Categorize activities
        file_edits = [n for n in context_nodes if n['type'] == 'file_modified']
        test_runs = [n for n in context_nodes if n['type'] == 'test_run']
        terminal_commands = [n for n in context_nodes if n['type'] == 'command_executed']
        
        # Analyze patterns
        analysis = {
            "timeline": self._build_activity_timeline(context_nodes),
            "focus_areas": self._identify_focus_areas(file_edits),
            "debugging_strategy": self._analyze_debugging_approach(test_runs, terminal_commands),
            "productivity_score": self._calculate_productivity_score(context_nodes)
        }
        
        return analysis
    
    def _build_activity_timeline(self, nodes: List[Dict]) -> List[Dict]:
        """Build chronological timeline of activities"""
        timeline = []
        for node in sorted(nodes, key=lambda x: x['timestamp']):
            timeline.append({
                "timestamp": node['timestamp'],
                "activity": f"{node['agent']}: {node['type']}",
                "file": node.get('file_path', ''),
                "summary": self._summarize_activity(node)
            })
        return timeline[-10:]  # Last 10 activities
    
    def _identify_focus_areas(self, file_edits: List[Dict]) -> Dict[str, int]:
        """Identify which files/areas are getting most attention"""
        focus_areas = {}
        for edit in file_edits:
            file_path = edit.get('file_path', 'unknown')
            if file_path:
                focus_areas[file_path] = focus_areas.get(file_path, 0) + 1
        
        return dict(sorted(focus_areas.items(), key=lambda x: x[1], reverse=True)[:5])
    
    def _analyze_debugging_approach(self, test_runs: List[Dict], commands: List[Dict]) -> Dict[str, Any]:
        """Analyze debugging strategy"""
        return {
            "test_frequency": len(test_runs),
            "test_driven": len(test_runs) > len(commands),
            "command_usage": len(commands),
            "debugging_tools_used": self._extract_debugging_tools(commands)
        }
    
    def _extract_debugging_tools(self, commands: List[Dict]) -> List[str]:
        """Extract debugging tools from terminal commands"""
        tools = set()
        for cmd in commands:
            command_text = cmd.get('payload', {}).get('command', '').lower()
            if 'debug' in command_text or 'gdb' in command_text:
                tools.add('debugger')
            if 'log' in command_text or 'tail' in command_text:
                tools.add('logs')
            if 'test' in command_text:
                tools.add('testing')
        return list(tools)
    
    def _calculate_productivity_score(self, nodes: List[Dict]) -> float:
        """Calculate productivity score based on activity patterns"""
        if not nodes:
            return 0.0
        
        # Score based on variety and progression
        unique_files = len(set(n.get('file_path') for n in nodes if n.get('file_path')))
        activity_types = len(set(n['type'] for n in nodes))
        
        # Bonus for test runs and commits
        test_bonus = len([n for n in nodes if n['type'] == 'test_run']) * 0.1
        commit_bonus = len([n for n in nodes if n['type'] == 'commit_created']) * 0.2
        
        base_score = (unique_files * 0.1 + activity_types * 0.05)
        return min(base_score + test_bonus + commit_bonus, 1.0)
    
    def _summarize_activity(self, node: Dict) -> str:
        """Create human-readable summary of activity"""
        activity_type = node['type']
        payload = node.get('payload', {})
        
        if activity_type == 'file_modified':
            return f"Modified {node.get('file_path', 'file')}"
        elif activity_type == 'test_run':
            status = payload.get('status', 'unknown')
            return f"Ran tests ({status})"
        elif activity_type == 'command_executed':
            cmd = payload.get('command', '')[:50]
            return f"Executed: {cmd}"
        else:
            return activity_type.replace('_', ' ').title()
    
    async def generate_rubber_duck_response(self, session_id: str) -> str:
        """Generate rubber duck debugging response"""
        loop_analysis = await self.detect_looping_behavior(session_id)
        thought_analysis = await self.analyze_thought_process(session_id)
        
        if loop_analysis['stuck_detected']:
            return self._generate_stuck_response(loop_analysis, thought_analysis)
        else:
            return self._generate_encouragement_response(thought_analysis)
    
    def _generate_stuck_response(self, loop_analysis: Dict, thought_analysis: Dict) -> str:
        """Generate response for stuck state"""
        suggestions = loop_analysis['suggestions']
        timeline = thought_analysis['timeline']
        
        response = f"🤔 I notice you've been working on this for a while. "
        
        if loop_analysis['looping_files']:
            files = ', '.join(loop_analysis['looping_files'][:2])
            response += f"You've been editing {files} repeatedly. "
        
        response += f"Here's what might help:\n\n"
        response += f"• {suggestions[0]}\n• {suggestions[1]}\n"
        
        if thought_analysis['productivity_score'] < 0.3:
            response += "\n💡 Your recent activity suggests you might be stuck. Consider taking a step back and reviewing your approach."
        
        return response
    
    def _generate_encouragement_response(self, thought_analysis: Dict) -> str:
        """Generate encouraging response for good progress"""
        score = thought_analysis['productivity_score']
        
        if score > 0.7:
            return "🚀 You're making great progress! Your activity shows focused work with good testing habits."
        elif score > 0.4:
            return "👍 Steady progress. You're working systematically through the problem."
        else:
            return "🎯 I see you're exploring different approaches. Sometimes the best solutions come from experimentation!"