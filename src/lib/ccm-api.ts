import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface CCMContextEvent {
  sessionId: string;
  agent: string;
  type: string;
  payload: Record<string, any>;
  timestamp?: string;
  file_path?: string;
  line_number?: number;
}

export interface FlowState {
  session_id: string;
  is_in_flow: boolean;
  flow_duration: number;
  focus_score: number;
  keystroke_rhythm: number;
  context_switches: number;
  test_intensity: number;
}

export interface PairProgrammingResponse {
  rubber_duck_response: string;
  stuck_analysis: {
    stuck_detected: boolean;
    loop_type?: string;
    confidence?: number;
    suggestions?: string[];
    looping_files?: string[];
  };
  thought_process: {
    timeline: Array<{
      timestamp: string;
      activity: string;
      file: string;
      summary: string;
    }>;
    focus_areas: Record<string, number>;
    debugging_strategy: {
      test_frequency: number;
      test_driven: boolean;
      command_usage: number;
      debugging_tools_used: string[];
    };
    productivity_score: number;
  };
}

// CCM Core API
export const ccmAPI = {
  // Context Events
  storeContextEvent: (event: CCMContextEvent) => 
    api.post('/ccm/context/events', event),
  
  getTemporalContext: (sessionId: string, windowMinutes: number = 30) => 
    api.get(`/ccm/context/temporal/${sessionId}?window_minutes=${windowMinutes}`),
  
  analyzePatterns: (sessionId: string) => 
    api.get(`/ccm/context/patterns/${sessionId}`),
  
  wipeContextData: (sessionId: string, confirm: boolean = false) => 
    api.post('/ccm/context/wipe', { session_id: sessionId, confirm }),
  
  // Flow Orchestrator
  getFlowState: (sessionId: string) => 
    api.get(`/ccm/flow/state/${sessionId}`),
  
  getFlowInsights: (sessionId: string, days: number = 7) => 
    api.get(`/ccm/flow/insights/${sessionId}?days=${days}`),
  
  suggestBreak: (sessionId: string) => 
    api.post(`/ccm/flow/break-suggestion/${sessionId}`),
  
  // Pair Programming Ghost
  getRubberDuckResponse: (sessionId: string) => 
    api.get(`/ccm/pair-programming/ghost/${sessionId}`),
  
  // Auto Commit
  suggestCommitMessage: (sessionId: string, repoPath: string) => 
    api.post(`/ccm/auto-commit/suggest/${sessionId}?repo_path=${encodeURIComponent(repoPath)}`),
  
  executeAutoCommit: (sessionId: string, repoPath: string) => 
    api.post(`/ccm/auto-commit/execute/${sessionId}?repo_path=${encodeURIComponent(repoPath)}`),
  
  // Code Analysis
  analyzeChangeImpact: (sessionId: string, filePath: string, projectRoot: string) => 
    api.post(`/ccm/code-analysis/impact/${sessionId}?file_path=${encodeURIComponent(filePath)}&project_root=${encodeURIComponent(projectRoot)}`),
  
  storeRelationshipGraph: (sessionId: string, projectRoot: string) => 
    api.post(`/ccm/code-analysis/relationships/${sessionId}?project_root=${encodeURIComponent(projectRoot)}`),
  
  // Integrations
  postPRSummary: (sessionId: string, prData: Record<string, any>) => 
    api.post(`/ccm/integrations/slack/pr-summary?session_id=${sessionId}`, prData),
  
  postDailyChangelog: (sessionId: string, date: string) => 
    api.post(`/ccm/integrations/slack/daily-changelog?session_id=${sessionId}&date=${date}`),
  
  postStuckAlert: (sessionId: string, stuckAnalysis: Record<string, any>) => 
    api.post(`/ccm/integrations/slack/stuck-alert?session_id=${sessionId}`, stuckAnalysis),
  
  // Energy Analysis
  getComprehensiveEnergy: (sessionId: string, timeRange: string = 'hour') => 
    api.get(`/ccm/energy/comprehensive/${sessionId}?time_range=${timeRange}`),
  
  // Gamification
  getGamificationDashboard: (sessionId: string) => 
    api.get(`/gamification/dashboard/${sessionId}`),
  
  awardXP: (sessionId: string, source: string, amount: number, metadata?: Record<string, any>) => 
    api.post(`/gamification/xp/${sessionId}`, { source, amount, metadata }),
  
  updateStreak: (sessionId: string) => 
    api.post(`/gamification/streak/${sessionId}`),
  
  getUserProfile: (sessionId: string) => 
    api.get(`/gamification/profile/${sessionId}`),
  
  getAchievements: (sessionId: string) => 
    api.get(`/gamification/achievements/${sessionId}`),
  
  getLeaderboard: (metric: string = 'xp', timeframe: string = 'weekly') => 
    api.get(`/gamification/leaderboard?metric=${metric}&timeframe=${timeframe}`),
};

export default api;