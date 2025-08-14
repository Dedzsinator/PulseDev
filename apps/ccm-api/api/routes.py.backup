from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import json

router = APIRouter(prefix="/ccm", tags=["CCM Core"])

class ContextEventRequest(BaseModel):
    sessionId: str
    agent: str
    type: str
    payload: Dict[str, Any]
    timestamp: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None

class WipeRequest(BaseModel):
    session_id: str
    confirm: bool = False

@router.post("/context/events")
async def store_context_event(event: ContextEventRequest):
    """Store context event in temporal graph"""
    try:
        from api.routes import context_graph, encryption_service
        
        # Prepare node data
        node_data = {
            'agent': event.agent,
            'type': event.type,
            'payload': event.payload,
            'timestamp': event.timestamp or datetime.utcnow().isoformat(),
            'file_path': event.file_path,
            'line_number': event.line_number
        }
        
        # Store in temporal context graph
        node_id = await context_graph.store_context_node(event.sessionId, node_data)
        
        # Auto-detect relationships and patterns
        patterns = await context_graph.detect_patterns(event.sessionId)
        
        return {
            "status": "stored",
            "node_id": node_id,
            "patterns_detected": patterns
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store context: {str(e)}")

@router.get("/context/temporal/{session_id}")
async def get_temporal_context(session_id: str, window_minutes: int = 30):
    """Get temporal context within time window"""
    try:
        from api.routes import context_graph
        
        context_nodes = await context_graph.get_temporal_context(session_id, window_minutes)
        return {
            "session_id": session_id,
            "window_minutes": window_minutes,
            "nodes": context_nodes,
            "count": len(context_nodes)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")

@router.get("/context/patterns/{session_id}")
async def analyze_patterns(session_id: str):
    """Analyze behavioral patterns"""
    try:
        from api.routes import context_graph
        
        patterns = await context_graph.detect_patterns(session_id)
        return patterns
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")

@router.post("/context/wipe")
async def wipe_context_data(request: WipeRequest):
    """Wipe context data (ephemeral mode)"""
    try:
        from api.routes import context_graph
        
        if not request.confirm:
            raise HTTPException(status_code=400, detail="Confirmation required")
        
        deleted_count = await context_graph.auto_wipe_old_data(hours=0)  # Wipe all
        
        return {
            "status": "wiped",
            "deleted_nodes": deleted_count,
            "session_id": request.session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to wipe context: {str(e)}")

@router.get("/flow/state/{session_id}")
async def get_flow_state(session_id: str):
    """Get current flow state"""
    try:
        from api.routes import flow_orchestrator
        
        flow_state = await flow_orchestrator.detect_flow_state(session_id)
        
        return {
            "session_id": session_id,
            "is_in_flow": flow_state.is_in_flow,
            "flow_duration": flow_state.flow_duration,
            "focus_score": flow_state.focus_score,
            "keystroke_rhythm": flow_state.keystroke_rhythm,
            "context_switches": flow_state.context_switches,
            "test_intensity": flow_state.test_intensity
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get flow state: {str(e)}")

@router.get("/flow/insights/{session_id}")
async def get_flow_insights(session_id: str, days: int = 7):
    """Get flow insights over time period"""
    try:
        from api.routes import flow_orchestrator
        
        insights = await flow_orchestrator.get_flow_insights(session_id, days)
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get flow insights: {str(e)}")

@router.post("/flow/break-suggestion/{session_id}")
async def suggest_break(session_id: str):
    """Suggest break based on flow analysis"""
    try:
        from api.routes import flow_orchestrator
        
        suggestion = await flow_orchestrator.suggest_break(session_id)
        
        if suggestion:
            return suggestion
        else:
            return {"suggestion": None, "message": "No break needed at this time"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suggest break: {str(e)}")

@router.get("/pair-programming/ghost/{session_id}")
async def get_rubber_duck_response(session_id: str):
    """Get rubber duck debugging response"""
    try:
        from api.routes import pair_programming
        
        response = await pair_programming.generate_rubber_duck_response(session_id)
        loop_analysis = await pair_programming.detect_looping_behavior(session_id)
        thought_analysis = await pair_programming.analyze_thought_process(session_id)
        
        return {
            "rubber_duck_response": response,
            "stuck_analysis": loop_analysis,
            "thought_process": thought_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")

@router.post("/auto-commit/suggest/{session_id}")
async def suggest_commit_message(session_id: str, repo_path: str):
    """Suggest commit message based on context"""
    try:
        from api.routes import auto_commit
        
        suggestion = await auto_commit.suggest_commit_message(session_id, repo_path)
        return suggestion
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suggest commit: {str(e)}")

@router.post("/auto-commit/execute/{session_id}")
async def execute_auto_commit(session_id: str, repo_path: str):
    """Execute auto-commit if fix detected"""
    try:
        from api.routes import auto_commit
        
        commit_message = await auto_commit.auto_commit_if_appropriate(session_id, repo_path)
        
        if commit_message:
            return {
                "status": "committed",
                "commit_message": commit_message
            }
        else:
            return {
                "status": "no_commit",
                "message": "No fix detected or auto-commit disabled"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute auto-commit: {str(e)}")

@router.post("/code-analysis/impact/{session_id}")
async def analyze_change_impact(session_id: str, file_path: str, project_root: str):
    """Analyze impact of changing a file"""
    try:
        from api.routes import code_mapper
        
        impact = await code_mapper.forecast_change_impact(file_path, project_root)
        return impact
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze impact: {str(e)}")

@router.post("/code-analysis/relationships/{session_id}")
async def store_relationship_graph(session_id: str, project_root: str):
    """Store complete relationship graph for project"""
    try:
        from api.routes import code_mapper
        
        await code_mapper.store_relationship_graph(session_id, project_root)
        
        return {
            "status": "stored",
            "message": "Relationship graph stored successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store relationships: {str(e)}")

@router.post("/integrations/slack/pr-summary")
async def post_pr_summary(session_id: str, pr_data: Dict[str, Any]):
    """Post AI-generated PR summary to Slack"""
    try:
        from api.routes import integrations
        
        success = await integrations.post_ai_pr_summary(session_id, pr_data)
        
        return {
            "status": "posted" if success else "failed",
            "platform": "slack"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to post PR summary: {str(e)}")

@router.post("/integrations/slack/daily-changelog")
async def post_daily_changelog(session_id: str, date: str):
    """Post daily changelog to Slack"""
    try:
        from api.routes import integrations
        
        success = await integrations.post_daily_changelog(session_id, date)
        
        return {
            "status": "posted" if success else "failed",
            "date": date
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to post changelog: {str(e)}")

@router.post("/integrations/slack/stuck-alert")
async def post_stuck_alert(session_id: str, stuck_analysis: Dict[str, Any]):
    """Post stuck state alert to Slack"""
    try:
        from api.routes import integrations
        
        success = await integrations.post_stuck_alert(session_id, stuck_analysis)
        
        return {
            "status": "posted" if success else "failed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to post stuck alert: {str(e)}")

@router.get("/energy/comprehensive/{session_id}")
async def get_comprehensive_energy(session_id: str, time_range: str = "hour"):
    """Get comprehensive energy analysis"""
    try:
        from api.routes import energy_service
        
        score = await energy_service.calculate_energy_score(session_id, time_range)
        metrics = await energy_service.get_energy_metrics(session_id)
        trends = await energy_service.get_energy_trends(session_id)
        
        return {
            "current_score": score,
            "metrics": metrics,
            "trends": trends,
            "time_range": time_range
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get energy analysis: {str(e)}")