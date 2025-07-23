import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ccmAPI, CCMContextEvent, FlowState, PairProgrammingResponse } from '@/lib/ccm-api';
import { Brain, GitBranch, Zap, Bot, Code, MessageSquare, Activity, Shield } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { notify } from '@/utils/notifications';
import { pickFile, readFile, writeFile, getDndStatus, setDndStatus } from '@/utils/tauri-native';
import { Tooltip } from '@/components/ui/tooltip';

const getOrCreateSessionId = () => {
  let sessionId = localStorage.getItem('ccm_session_id');
  if (!sessionId) {
    sessionId = 'ccm_session_' + Date.now();
    localStorage.setItem('ccm_session_id', sessionId);
  }
  return sessionId;
};

export default function CCMFeatures() {
  const [sessionId, setSessionId] = useState(getOrCreateSessionId());
  const [flowState, setFlowState] = useState<FlowState | null>(null);
  const [pairResponse, setPairResponse] = useState<PairProgrammingResponse | null>(null);
  const [repoPath, setRepoPath] = useState('/path/to/repo');
  const [filePath, setFilePath] = useState('/path/to/file.py');
  const [loading, setLoading] = useState(false);
  const [originalIntent, setOriginalIntent] = useState('');
  const [mergeConflicts, setMergeConflicts] = useState<any[] | null>(null);
  const [intentDrift, setIntentDrift] = useState<any | null>(null);
  const [branchSuggestion, setBranchSuggestion] = useState<string | null>(null);
  const { toast } = useToast();
  const [nativeLoading, setNativeLoading] = useState<string | null>(null);
  const [nativeError, setNativeError] = useState<string | null>(null);
  const [isActiveSession, setIsActiveSession] = useState(true); // Assume active by default

  // Focus/blur event-based session sync
  useEffect(() => {
    const syncSession = async () => {
      try {
        const res = await fetch('/api/v1/gamification/session/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId, platform: 'tauri' })
        });
        const data = await res.json();
        if (data && data.success) {
          setIsActiveSession(data.sync_data.active_session === sessionId);
        }
      } catch (e) {
        setIsActiveSession(false);
      }
    };
    // Sync on mount
    syncSession();
    // Sync on focus/blur
    const onFocus = () => syncSession();
    const onBlur = () => syncSession();
    window.addEventListener('focus', onFocus);
    window.addEventListener('blur', onBlur);
    return () => {
      window.removeEventListener('focus', onFocus);
      window.removeEventListener('blur', onBlur);
    };
  }, [sessionId]);

  // Show notification on session state change
  const prevActiveRef = useRef<boolean | null>(null);
  useEffect(() => {
    if (prevActiveRef.current !== null && prevActiveRef.current !== isActiveSession) {
      notify(
        'Session State Changed',
        isActiveSession
          ? 'This Tauri app is now the active PulseDev+ session.'
          : 'This Tauri app is now inactive (not primary).'
      );
    }
    prevActiveRef.current = isActiveSession;
  }, [isActiveSession]);

  // Only allow tracking if isActiveSession is true
  const safeTrack = (fn: (...args: any[]) => any) =>
    (...args: any[]) => {
      if (isActiveSession) return fn(...args);
    };

  // Real-time flow state monitoring
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await ccmAPI.getFlowState(sessionId);
        setFlowState(response.data);
      } catch (error) {
        console.error('Failed to get flow state:', error);
      }
    }, 10000); // Update every 10 seconds

    return () => clearInterval(interval);
  }, [sessionId]);

  const simulateContextEvent = async (agent: string, type: string, payload: Record<string, any>) => {
    try {
      const event: CCMContextEvent = {
        sessionId,
        agent,
        type,
        payload,
        timestamp: new Date().toISOString()
      };

      await ccmAPI.storeContextEvent(event);
      toast({
        title: "Context Event Stored",
        description: `${agent}: ${type}`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to store context event",
        variant: "destructive"
      });
    }
  };

  const getRubberDuckResponse = async () => {
    setLoading(true);
    try {
      const response = await ccmAPI.getRubberDuckResponse(sessionId);
      setPairResponse(response.data);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to get rubber duck response",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const suggestCommit = async () => {
    setLoading(true);
    try {
      const response = await ccmAPI.suggestCommitMessage(sessionId, repoPath);
      toast({
        title: "Commit Suggestion",
        description: response.data.suggested_message,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to suggest commit message",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const analyzeCodeImpact = async () => {
    setLoading(true);
    try {
      const response = await ccmAPI.analyzeChangeImpact(sessionId, filePath, repoPath);
      toast({
        title: "Impact Analysis",
        description: `${response.data.direct_impact.count} files affected`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to analyze code impact",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-secondary/20 p-6">
      <div className="flex items-center gap-4 mb-4">
        <span
          className={`inline-block w-3 h-3 rounded-full ${isActiveSession ? 'bg-green-500' : 'bg-red-500'}`}
          title={isActiveSession ? 'Active Session' : 'Inactive (Not Primary)'}
        ></span>
        <Badge variant={isActiveSession ? 'default' : 'destructive'}>
          {isActiveSession ? 'Active Session' : 'Inactive (Not Primary)'}
        </Badge>
        <span className="text-xs text-muted-foreground">Only the active session can track and notify.</span>
      </div>
      <button
        className="mb-4 px-4 py-2 bg-primary text-white rounded"
        onClick={() => notify('PulseDev+ Context', 'This is a native notification test!')}
      >
        Test Native Notification
      </button>
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            PulseDev+ Cognitive Context Mirror
          </h1>
          <p className="text-xl text-muted-foreground">
            Complete AI-powered development workflow tracking with all 9 core features
          </p>
          <div className="flex items-center justify-center gap-4">
            <Badge variant="outline" className="px-4 py-2">
              Session: {sessionId.slice(-8)}
            </Badge>
            {flowState?.is_in_flow && (
              <Badge className="px-4 py-2 bg-green-500">
                🚀 In Flow State
              </Badge>
            )}
          </div>
        </div>

        <Tabs defaultValue="context-mirror" className="w-full">
          <TabsList className="grid w-full grid-cols-4 lg:grid-cols-9">
            <TabsTrigger value="context-mirror">
              <Shield className="w-4 h-4 mr-2" />
              CCM
            </TabsTrigger>
            <TabsTrigger value="ai-prompt">
              <Brain className="w-4 h-4 mr-2" />
              AI Prompt
            </TabsTrigger>
            <TabsTrigger value="pair-ghost">
              <Bot className="w-4 h-4 mr-2" />
              Pair Ghost
            </TabsTrigger>
            <TabsTrigger value="auto-commit">
              <GitBranch className="w-4 h-4 mr-2" />
              Auto Commit
            </TabsTrigger>
            <TabsTrigger value="flow">
              <Activity className="w-4 h-4 mr-2" />
              Flow
            </TabsTrigger>
            <TabsTrigger value="energy">
              <Zap className="w-4 h-4 mr-2" />
              Energy
            </TabsTrigger>
            <TabsTrigger value="code-mapper">
              <Code className="w-4 h-4 mr-2" />
              Code Map
            </TabsTrigger>
            <TabsTrigger value="git-monitor">
              <GitBranch className="w-4 h-4 mr-2" />
              Git Monitor
            </TabsTrigger>
            <TabsTrigger value="integrations">
              <MessageSquare className="w-4 h-4 mr-2" />
              Integrations
            </TabsTrigger>
            <TabsTrigger value="merge-resolver">
              <Shield className="w-4 h-4 mr-2" />
              Merge Resolver
            </TabsTrigger>
            <TabsTrigger value="intent-drift">
              <Brain className="w-4 h-4 mr-2" />
              Intent Drift
            </TabsTrigger>
            <TabsTrigger value="branch-suggest">
              <GitBranch className="w-4 h-4 mr-2" />
              Branch Suggest
            </TabsTrigger>
            <TabsTrigger value="native-utils">
              <Shield className="w-4 h-4 mr-2" />
              Native Utilities
            </TabsTrigger>
          </TabsList>

          {/* 1. Cognitive Context Mirror */}
          <TabsContent value="context-mirror">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Cognitive Context Mirror
                </CardTitle>
                <CardDescription>
                  Encrypted temporal context tracking with AES-256-GCM
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Button onClick={safeTrack(simulateContextEvent)('file', 'file_modified', { path: '/src/app.py', changes: 15 })}>
                    Simulate File Edit
                  </Button>
                  <Button onClick={safeTrack(simulateContextEvent)('terminal', 'command_executed', { command: 'npm test', output: 'Tests passed' })}>
                    Simulate Terminal
                  </Button>
                  <Button onClick={safeTrack(simulateContextEvent)('browser', 'tab_switch', { url: 'https://stackoverflow.com', title: 'Stack Overflow' })}>
                    Simulate Browser
                  </Button>
                  <Button onClick={safeTrack(simulateContextEvent)('debug', 'error_occurred', { error: 'TypeError: Cannot read property', line: 42 })}>
                    Simulate Error
                  </Button>
                </div>

                <Card className="bg-secondary/50">
                  <CardContent className="pt-6">
                    <h4 className="font-semibold mb-2">Context Features</h4>
                    <ul className="space-y-1 text-sm">
                      <li>✅ File edits tracking</li>
                      <li>✅ Terminal history capture</li>
                      <li>✅ Debug stack traces</li>
                      <li>✅ Browser tabs monitoring</li>
                      <li>✅ AES-256-GCM encryption</li>
                      <li>✅ Temporal context graph</li>
                      <li>✅ Auto-wipe (ephemeral mode)</li>
                    </ul>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 2. Context-Aware AI Prompt Generator */}
          <TabsContent value="ai-prompt">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="w-5 h-5" />
                  Context-Aware AI Prompt Generator
                </CardTitle>
                <CardDescription>
                  Auto-generates rich prompts with error context and code snippets
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={safeTrack(simulateContextEvent)('ai', 'prompt_generated', {
                    model: 'gpt-4',
                    context_window: 30,
                    includes: ['error_messages', 'recent_files', 'terminal_output']
                  })}
                  className="w-full"
                >
                  Generate AI Prompt from Context
                </Button>

                <div className="grid md:grid-cols-3 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <h4 className="font-semibold">OpenAI</h4>
                      <p className="text-sm text-muted-foreground">GPT-4, GPT-3.5</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <h4 className="font-semibold">Claude</h4>
                      <p className="text-sm text-muted-foreground">Anthropic models</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <h4 className="font-semibold">Local</h4>
                      <p className="text-sm text-muted-foreground">Ollama, LLaMA3</p>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 3. Pair Programming Ghost */}
          <TabsContent value="pair-ghost">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bot className="w-5 h-5" />
                  Pair Programming Ghost
                </CardTitle>
                <CardDescription>
                  Smart rubber duck that detects when you're stuck
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={getRubberDuckResponse}
                  disabled={loading}
                  className="w-full"
                >
                  Ask the Rubber Duck
                </Button>

                {pairResponse && (
                  <Card className="bg-secondary/50">
                    <CardContent className="pt-6">
                      <h4 className="font-semibold mb-2">🦆 Rubber Duck Says:</h4>
                      <p className="text-sm mb-4">{pairResponse.rubber_duck_response}</p>

                      {pairResponse.stuck_analysis.stuck_detected && (
                        <div className="space-y-2">
                          <Badge variant="destructive">Stuck Detected</Badge>
                          <div className="space-y-1">
                            {pairResponse.stuck_analysis.suggestions?.map((suggestion, i) => (
                              <p key={i} className="text-xs">• {suggestion}</p>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="mt-4">
                        <p className="text-xs text-muted-foreground">
                          Productivity Score: {Math.round((pairResponse.thought_process.productivity_score || 0) * 100)}%
                        </p>
                        <Progress
                          value={(pairResponse.thought_process.productivity_score || 0) * 100}
                          className="mt-2"
                        />
                      </div>
                    </CardContent>
                  </Card>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* 4. Auto Commit Message Writer */}
          <TabsContent value="auto-commit">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <GitBranch className="w-5 h-5" />
                  Auto Commit Message Writer
                </CardTitle>
                <CardDescription>
                  AI-generated commit messages with context tags
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Repository Path</label>
                  <Input
                    value={repoPath}
                    onChange={(e) => setRepoPath(e.target.value)}
                    placeholder="/path/to/your/repo"
                  />
                </div>

                <Button
                  onClick={suggestCommit}
                  disabled={loading}
                  className="w-full"
                >
                  Generate Commit Message
                </Button>

                <Card className="bg-secondary/50">
                  <CardContent className="pt-6">
                    <h4 className="font-semibold mb-2">Example Generated Message:</h4>
                    <code className="text-xs block p-2 bg-background rounded">
                      Fix JWT expiry issue in auth.js | Adds clock skew test | Context: auth+security | Relates to PROJ-142
                    </code>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 5. Flow Orchestrator */}
          <TabsContent value="flow">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  Flow Orchestrator
                </CardTitle>
                <CardDescription>
                  Deep-work state detection with automatic environment adjustments
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {flowState && (
                  <div className="grid md:grid-cols-2 gap-4">
                    <Card>
                      <CardContent className="pt-6">
                        <h4 className="font-semibold">Flow State</h4>
                        <div className="space-y-2 mt-2">
                          <div className="flex justify-between">
                            <span className="text-sm">Focus Score</span>
                            <span className="text-sm font-mono">
                              {Math.round(flowState.focus_score * 100)}%
                            </span>
                          </div>
                          <Progress value={flowState.focus_score * 100} />

                          <div className="flex justify-between">
                            <span className="text-sm">Keystroke Rhythm</span>
                            <span className="text-sm font-mono">
                              {Math.round(flowState.keystroke_rhythm * 100)}%
                            </span>
                          </div>
                          <Progress value={flowState.keystroke_rhythm * 100} />
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="pt-6">
                        <h4 className="font-semibold">Session Metrics</h4>
                        <div className="space-y-2 mt-2 text-sm">
                          <div className="flex justify-between">
                            <span>Flow Duration</span>
                            <span className="font-mono">{flowState.flow_duration}m</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Context Switches</span>
                            <span className="font-mono">{flowState.context_switches}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Test Intensity</span>
                            <span className="font-mono">{Math.round(flowState.test_intensity * 100)}%</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}

                <Button
                  onClick={safeTrack(simulateContextEvent)('flow', 'flow_start', { trigger: 'manual' })}
                  variant="outline"
                  className="w-full"
                >
                  Simulate Flow State Start
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Continue with other tabs... */}
          <TabsContent value="energy">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  Energy Score Algorithm
                </CardTitle>
                <CardDescription>
                  Cognitive efficiency tracking with burnout detection
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center space-y-4">
                  <div className="text-6xl font-bold text-primary">8.2</div>
                  <p className="text-muted-foreground">Current Energy Score</p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold">95%</div>
                      <div className="text-sm text-muted-foreground">Test Pass Rate</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">12</div>
                      <div className="text-sm text-muted-foreground">Context Switches</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">0.3</div>
                      <div className="text-sm text-muted-foreground">Error Frequency</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">145m</div>
                      <div className="text-sm text-muted-foreground">Flow Duration</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="code-mapper">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Code className="w-5 h-5" />
                  Code Relationship Mapper
                </CardTitle>
                <CardDescription>
                  Impact forecasting with dependency analysis
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">File Path</label>
                  <Input
                    value={filePath}
                    onChange={(e) => setFilePath(e.target.value)}
                    placeholder="/src/components/Button.tsx"
                  />
                </div>

                <Button
                  onClick={analyzeCodeImpact}
                  disabled={loading}
                  className="w-full"
                >
                  Analyze Change Impact
                </Button>

                <div className="grid md:grid-cols-3 gap-4">
                  <Card className="bg-green-50 dark:bg-green-950/20">
                    <CardContent className="pt-6 text-center">
                      <div className="text-2xl font-bold text-green-600">Low</div>
                      <div className="text-sm">Risk Level</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-blue-50 dark:bg-blue-950/20">
                    <CardContent className="pt-6 text-center">
                      <div className="text-2xl font-bold text-blue-600">73%</div>
                      <div className="text-sm">Coverage</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-orange-50 dark:bg-orange-950/20">
                    <CardContent className="pt-6 text-center">
                      <div className="text-2xl font-bold text-orange-600">5</div>
                      <div className="text-sm">Affected Files</div>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="git-monitor">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <GitBranch className="w-5 h-5" />
                  Git Activity Monitor
                </CardTitle>
                <CardDescription>
                  Branch health and PR optimization
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-4">
                  <Card className="bg-secondary/50">
                    <CardContent className="pt-6">
                      <h4 className="font-semibold mb-2">Branch Health</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Stale Branches</span>
                          <Badge variant="destructive">2</Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>Long-running PRs</span>
                          <Badge variant="outline">1</Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>Recent Reverts</span>
                          <Badge variant="secondary">0</Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-secondary/50">
                    <CardContent className="pt-6">
                      <h4 className="font-semibold mb-2">Commit Patterns</h4>
                      <div className="space-y-2 text-sm">
                        <div>📈 Productivity trending up</div>
                        <div>🎯 Good commit message quality</div>
                        <div>⚡ Fast review cycles</div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="integrations">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  Slack & Jira Integration
                </CardTitle>
                <CardDescription>
                  Automated reporting and ticket management
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <Button variant="outline" className="h-20 flex-col">
                    <MessageSquare className="w-6 h-6 mb-2" />
                    Post Daily Changelog
                  </Button>
                  <Button variant="outline" className="h-20 flex-col">
                    <GitBranch className="w-6 h-6 mb-2" />
                    Generate PR Summary
                  </Button>
                </div>

                <Card className="bg-secondary/50">
                  <CardContent className="pt-6">
                    <h4 className="font-semibold mb-2">Auto-Integration Features</h4>
                    <ul className="space-y-1 text-sm">
                      <li>✅ Auto-close JIRA tickets on fix commits</li>
                      <li>✅ Daily changelog posts to Slack</li>
                      <li>✅ Stuck state alerts to team</li>
                      <li>✅ AI-generated PR summaries</li>
                      <li>✅ Commit linking to issues</li>
                    </ul>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Merge Conflict Resolver */}
          <TabsContent value="merge-resolver">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Merge Conflict Resolver
                </CardTitle>
                <CardDescription>
                  Detect and resolve merge conflicts with AI-powered suggestions.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  value={repoPath}
                  onChange={e => setRepoPath(e.target.value)}
                  placeholder="/path/to/your/repo"
                  className="mb-2"
                />
                <Button
                  onClick={async () => {
                    setMergeConflicts(null);
                    try {
                      const res = await ccmAPI.detectMergeConflicts(repoPath);
                      setMergeConflicts(res.data.conflicts || []);
                      notify('Merge Conflict Resolver', res.data.conflicts?.length ? `${res.data.conflicts.length} conflict(s) found.` : 'No conflicts detected.');
                    } catch (e) {
                      notify('Merge Conflict Resolver', 'Error detecting conflicts.');
                    }
                  }}
                  className="w-full"
                >
                  Scan for Merge Conflicts
                </Button>
                {mergeConflicts && (
                  <div className="mt-2">
                    {mergeConflicts.length === 0 ? (
                      <div className="text-muted-foreground text-sm">No conflicts detected.</div>
                    ) : (
                      <ul className="text-sm">
                        {mergeConflicts.map((c, i) => (
                          <li key={i}>{c.file} ({c.type})</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Intent Drift Detector */}
          <TabsContent value="intent-drift">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="w-5 h-5" />
                  Intent Drift Detector
                </CardTitle>
                <CardDescription>
                  Detects when your recent commits drift from your original intent/task.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  value={originalIntent}
                  onChange={e => setOriginalIntent(e.target.value)}
                  placeholder="Describe your original intent/task"
                  className="mb-2"
                />
                <Button
                  onClick={async () => {
                    setIntentDrift(null);
                    try {
                      const res = await ccmAPI.detectIntentDrift(sessionId, originalIntent);
                      setIntentDrift(res.data);
                      notify('Intent Drift Detector', res.data.drift_detected ? 'Drift detected!' : 'No drift detected.');
                    } catch (e) {
                      notify('Intent Drift Detector', 'Error detecting drift.');
                    }
                  }}
                  className="w-full"
                >
                  Check for Intent Drift
                </Button>
                {intentDrift && (
                  <div className="mt-2 text-sm">
                    <div>Drift Detected: <b>{intentDrift.drift_detected ? 'Yes' : 'No'}</b></div>
                    <div>Confidence: {Math.round((intentDrift.confidence || 0) * 100)}%</div>
                    <div>Recent Commits Analyzed: {intentDrift.recent_commits}</div>
                    <div>Analysis: {intentDrift.analysis}</div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Auto Branch Suggestion */}
          <TabsContent value="branch-suggest">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <GitBranch className="w-5 h-5" />
                  Auto Branch Suggestion
                </CardTitle>
                <CardDescription>
                  Suggests new branch names based on your recent activity and TODOs.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={async () => {
                    setBranchSuggestion(null);
                    try {
                      const res = await ccmAPI.suggestBranch(sessionId);
                      setBranchSuggestion(res.data.suggested_branch);
                      notify('Auto Branch Suggestion', `Suggested: ${res.data.suggested_branch}`);
                    } catch (e) {
                      notify('Auto Branch Suggestion', 'Error suggesting branch.');
                    }
                  }}
                  className="w-full"
                >
                  Suggest Branch Name
                </Button>
                {branchSuggestion && (
                  <div className="mt-2 text-sm">
                    Suggested Branch: <b>{branchSuggestion}</b>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Native Utilities */}
          <TabsContent value="native-utils">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Native Utilities
                </CardTitle>
                <CardDescription>
                  Access advanced native features: file picker, read/write, DND mode.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {nativeError && (
                  <div className="text-red-500 text-sm mb-2">{nativeError}</div>
                )}
                <span title="Open a file picker dialog and select a file.">
                  <Button
                    onClick={async () => {
                      setNativeLoading('pick'); setNativeError(null);
                      try {
                        const file = await pickFile();
                        notify('File Picker', file ? `Picked: ${file}` : 'No file selected.');
                      } catch (e) {
                        setNativeError('Failed to pick file.');
                      } finally {
                        setNativeLoading(null);
                      }
                    }}
                    className="w-full"
                    disabled={!!nativeLoading}
                  >
                    {nativeLoading === 'pick' ? 'Picking...' : 'Pick File'}
                  </Button>
                </span>
                <span title="Pick a file and display its contents (first 100 chars).">
                  <Button
                    onClick={async () => {
                      setNativeLoading('read'); setNativeError(null);
                      try {
                        const file = await pickFile();
                        if (file) {
                          const contents = await readFile(file);
                          notify('Read File', contents.slice(0, 100) + (contents.length > 100 ? '...' : ''));
                        } else {
                          notify('Read File', 'No file selected.');
                        }
                      } catch (e) {
                        setNativeError('Failed to read file.');
                      } finally {
                        setNativeLoading(null);
                      }
                    }}
                    className="w-full"
                    disabled={!!nativeLoading}
                  >
                    {nativeLoading === 'read' ? 'Reading...' : 'Pick and Read File'}
                  </Button>
                </span>
                <span title="Pick a file and write a test string to it.">
                  <Button
                    onClick={async () => {
                      setNativeLoading('write'); setNativeError(null);
                      try {
                        const file = await pickFile();
                        if (file) {
                          await writeFile(file, 'PulseDev+ was here!');
                          notify('Write File', 'Wrote to file successfully.');
                        } else {
                          notify('Write File', 'No file selected.');
                        }
                      } catch (e) {
                        setNativeError('Failed to write file.');
                      } finally {
                        setNativeLoading(null);
                      }
                    }}
                    className="w-full"
                    disabled={!!nativeLoading}
                  >
                    {nativeLoading === 'write' ? 'Writing...' : 'Pick and Write File'}
                  </Button>
                </span>
                <span title="Check if Do Not Disturb (DND) mode is enabled (mocked).">
                  <Button
                    onClick={async () => {
                      setNativeLoading('dnd-status'); setNativeError(null);
                      try {
                        const status = await getDndStatus();
                        notify('DND Status', status ? 'DND is ON' : 'DND is OFF');
                      } catch (e) {
                        setNativeError('Failed to get DND status.');
                      } finally {
                        setNativeLoading(null);
                      }
                    }}
                    className="w-full"
                    disabled={!!nativeLoading}
                  >
                    {nativeLoading === 'dnd-status' ? 'Checking...' : 'Get DND Status'}
                  </Button>
                </span>
                <span title="Enable Do Not Disturb mode (mocked, not real).">
                  <Button
                    onClick={async () => {
                      setNativeLoading('dnd-on'); setNativeError(null);
                      try {
                        const enabled = await setDndStatus(true);
                        notify('Set DND', enabled ? 'DND enabled (mock)' : 'Failed to enable DND');
                      } catch (e) {
                        setNativeError('Failed to enable DND.');
                      } finally {
                        setNativeLoading(null);
                      }
                    }}
                    className="w-full"
                    disabled={!!nativeLoading}
                  >
                    {nativeLoading === 'dnd-on' ? 'Enabling...' : 'Enable DND (Mock)'}
                  </Button>
                </span>
                <span title="Disable Do Not Disturb mode (mocked, not real).">
                  <Button
                    onClick={async () => {
                      setNativeLoading('dnd-off'); setNativeError(null);
                      try {
                        const enabled = await setDndStatus(false);
                        notify('Set DND', !enabled ? 'DND disabled (mock)' : 'Failed to disable DND');
                      } catch (e) {
                        setNativeError('Failed to disable DND.');
                      } finally {
                        setNativeLoading(null);
                      }
                    }}
                    className="w-full"
                    disabled={!!nativeLoading}
                  >
                    {nativeLoading === 'dnd-off' ? 'Disabling...' : 'Disable DND (Mock)'}
                  </Button>
                </span>
                <div className="text-xs text-muted-foreground mt-2">
                  All native features are local and secure. DND is a mock for demo purposes.
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}