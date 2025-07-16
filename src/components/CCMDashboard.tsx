import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { contextAPI, aiAPI, gitAPI, flowAPI, energyAPI } from '@/lib/api';
import { Brain, GitBranch, Zap, Activity, Plus, Play, Square } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export default function CCMDashboard() {
  const [sessionId, setSessionId] = useState('');
  const [repoPath, setRepoPath] = useState('');
  const [isFlowActive, setIsFlowActive] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  useEffect(() => {
    // Generate session ID on mount
    const newSessionId = `session_${Date.now()}`;
    setSessionId(newSessionId);
  }, []);

  // Context Events Query
  const { data: events, refetch: refetchEvents } = useQuery({
    queryKey: ['events', sessionId],
    queryFn: () => contextAPI.getEvents(sessionId).then(res => res.data),
    enabled: !!sessionId,
  });

  // AI Services
  const generatePromptMutation = useMutation({
    mutationFn: aiAPI.generatePrompt,
    onSuccess: (data) => {
      toast({ title: 'AI Prompt Generated', description: 'Check console for details' });
      console.log('Generated Prompt:', data.data);
    },
  });

  const detectStuckMutation = useMutation({
    mutationFn: aiAPI.detectStuckState,
    onSuccess: (data) => {
      toast({ 
        title: data.data.is_stuck ? 'Stuck State Detected' : 'Flow State Good',
        description: data.data.reason || 'Analysis complete'
      });
    },
  });

  // Git Services
  const analyzeRepoMutation = useMutation({
    mutationFn: gitAPI.analyzeRepo,
    onSuccess: (data) => {
      toast({ title: 'Repo Analysis Complete', description: `${data.data.total_commits} commits analyzed` });
    },
  });

  const autoCommitMutation = useMutation({
    mutationFn: gitAPI.autoCommit,
    onSuccess: (data) => {
      toast({ title: 'Auto Commit Success', description: data.data.message });
    },
  });

  // Flow Services
  const startFlowMutation = useMutation({
    mutationFn: flowAPI.startSession,
    onSuccess: () => {
      setIsFlowActive(true);
      toast({ title: 'Flow Session Started' });
    },
  });

  const endFlowMutation = useMutation({
    mutationFn: () => flowAPI.endSession(sessionId),
    onSuccess: () => {
      setIsFlowActive(false);
      toast({ title: 'Flow Session Ended' });
      queryClient.invalidateQueries({ queryKey: ['flow-insights'] });
    },
  });

  // Energy Score Query
  const { data: energyScore } = useQuery({
    queryKey: ['energy-score', sessionId],
    queryFn: () => energyAPI.getScore({ session_id: sessionId }).then(res => res.data),
    enabled: !!sessionId,
  });

  // Create test context event
  const createTestEvent = async () => {
    try {
      await contextAPI.createEvent({
        session_id: sessionId,
        agent: 'vscode',
        type: 'file_edit',
        payload: {
          file_path: '/test/example.ts',
          change_type: 'edit',
          lines_added: 10,
          lines_removed: 2,
        },
      });
      refetchEvents();
      toast({ title: 'Test Event Created' });
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to create event', variant: 'destructive' });
    }
  };

  return (
    <div className="min-h-screen bg-background p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">PulseDev+ CCM Dashboard</h1>
        <Badge variant="outline" className="text-lg px-4 py-2">
          Session: {sessionId.slice(-8)}
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Events Captured</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{events?.length || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Energy Score</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{energyScore?.score || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Flow State</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <Badge variant={isFlowActive ? "default" : "secondary"}>
              {isFlowActive ? "Active" : "Inactive"}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Git Status</CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <Badge variant="outline">Ready</Badge>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="context" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="context">Context</TabsTrigger>
          <TabsTrigger value="ai">AI Services</TabsTrigger>
          <TabsTrigger value="git">Git Services</TabsTrigger>
          <TabsTrigger value="flow">Flow Control</TabsTrigger>
          <TabsTrigger value="energy">Energy Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="context" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Context Events</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={createTestEvent} className="w-full">
                <Plus className="mr-2 h-4 w-4" />
                Create Test Event
              </Button>
              <div className="max-h-60 overflow-y-auto space-y-2">
                {events?.map((event: any, index: number) => (
                  <div key={index} className="p-3 border rounded-lg">
                    <div className="flex justify-between items-start">
                      <div>
                        <Badge variant="outline">{event.agent}</Badge>
                        <span className="ml-2 font-medium">{event.type}</span>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <pre className="mt-2 text-xs bg-muted p-2 rounded">
                      {JSON.stringify(event.payload, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI Services</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button 
                onClick={() => generatePromptMutation.mutate({ session_id: sessionId })}
                disabled={generatePromptMutation.isPending}
                className="w-full"
              >
                Generate AI Prompt
              </Button>
              <Button 
                onClick={() => detectStuckMutation.mutate(sessionId)}
                disabled={detectStuckMutation.isPending}
                variant="outline"
                className="w-full"
              >
                Detect Stuck State
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="git" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Git Services</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                placeholder="Repository path (e.g., /path/to/repo)"
                value={repoPath}
                onChange={(e) => setRepoPath(e.target.value)}
              />
              <Button 
                onClick={() => analyzeRepoMutation.mutate({ session_id: sessionId, repo_path: repoPath })}
                disabled={!repoPath || analyzeRepoMutation.isPending}
                className="w-full"
              >
                Analyze Repository
              </Button>
              <Button 
                onClick={() => autoCommitMutation.mutate({ session_id: sessionId, repo_path: repoPath })}
                disabled={!repoPath || autoCommitMutation.isPending}
                variant="outline"
                className="w-full"
              >
                Auto Commit Changes
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="flow" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Flow Control</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {!isFlowActive ? (
                <Button 
                  onClick={() => startFlowMutation.mutate({ session_id: sessionId })}
                  disabled={startFlowMutation.isPending}
                  className="w-full"
                >
                  <Play className="mr-2 h-4 w-4" />
                  Start Flow Session
                </Button>
              ) : (
                <Button 
                  onClick={() => endFlowMutation.mutate()}
                  disabled={endFlowMutation.isPending}
                  variant="destructive"
                  className="w-full"
                >
                  <Square className="mr-2 h-4 w-4" />
                  End Flow Session
                </Button>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="energy" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Energy Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span>Current Score:</span>
                  <span className="font-bold">{energyScore?.score || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Flow Time:</span>
                  <span>{energyScore?.flow_time || 0}m</span>
                </div>
                <div className="flex justify-between">
                  <span>Context Switches:</span>
                  <span>{energyScore?.context_switches || 0}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}