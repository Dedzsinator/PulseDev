import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ContextEvent {
  session_id: string;
  agent: string;
  type: string;
  payload: Record<string, any>;
}

export interface AIPromptRequest {
  session_id: string;
  context_window?: number;
  include_git?: boolean;
  include_flow?: boolean;
}

export interface GitAnalysisRequest {
  session_id: string;
  repo_path: string;
}

export interface FlowSessionRequest {
  session_id: string;
  start_time?: string;
  end_time?: string;
}

export interface EnergyScoreRequest {
  session_id: string;
  time_range?: 'hour' | 'day' | 'week';
}

// Context Events
export const contextAPI = {
  createEvent: (event: ContextEvent) => 
    api.post('/context/events', event),
  
  getEvents: (sessionId: string, agent?: string, limit = 50) => 
    api.get('/context/events', { 
      params: { session_id: sessionId, agent, limit } 
    }),
  
  getSession: (sessionId: string) => 
    api.get(`/context/sessions/${sessionId}`),
  
  deleteSession: (sessionId: string) => 
    api.delete(`/context/sessions/${sessionId}`),
};

// AI Services
export const aiAPI = {
  generatePrompt: (request: AIPromptRequest) => 
    api.post('/ai/prompt', request),
  
  detectStuckState: (sessionId: string) => 
    api.post('/ai/stuck-state', { session_id: sessionId }),
  
  suggestCommit: (request: GitAnalysisRequest) => 
    api.post('/ai/commit-suggestion', request),
  
  suggestBranch: (request: GitAnalysisRequest) => 
    api.post('/ai/branch-suggestion', request),
};

// Git Services
export const gitAPI = {
  analyzeRepo: (request: GitAnalysisRequest) => 
    api.post('/git/analyze', request),
  
  autoCommit: (request: GitAnalysisRequest & { message?: string }) => 
    api.post('/git/auto-commit', request),
  
  detectConflicts: (request: GitAnalysisRequest) => 
    api.post('/git/conflicts', request),
  
  analyzeIntentDrift: (request: GitAnalysisRequest) => 
    api.post('/git/intent-drift', request),
};

// Flow Services
export const flowAPI = {
  startSession: (request: FlowSessionRequest) => 
    api.post('/flow/session/start', request),
  
  endSession: (sessionId: string) => 
    api.post(`/flow/session/${sessionId}/end`),
  
  getInsights: (sessionId: string) => 
    api.get(`/flow/insights/${sessionId}`),
  
  suggestBreak: (sessionId: string) => 
    api.post(`/flow/break-suggestion/${sessionId}`),
};

// Energy Services
export const energyAPI = {
  getScore: (request: EnergyScoreRequest) => 
    api.get('/energy/score', { params: request }),
  
  getMetrics: (sessionId: string) => 
    api.get(`/energy/metrics/${sessionId}`),
  
  getTrends: (sessionId: string, days = 7) => 
    api.get(`/energy/trends/${sessionId}`, { params: { days } }),
};

export default api;