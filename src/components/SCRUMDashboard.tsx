import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { scrumAPI } from '@/lib/ccm-api';
import { Calendar, Clock, Users, Target, Plus, CheckCircle, AlertTriangle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Sprint {
  id: string;
  name: string;
  goal: string;
  start_date: string;
  end_date: string;
  status: 'planning' | 'active' | 'completed';
  velocity: number;
  stories: UserStory[];
}

interface UserStory {
  id: string;
  title: string;
  description: string;
  story_points: number;
  status: 'backlog' | 'in_progress' | 'review' | 'done';
  assignee?: string;
  acceptance_criteria: string[];
  tasks: Task[];
}

interface Task {
  id: string;
  title: string;
  description: string;
  status: 'todo' | 'in_progress' | 'done';
  estimated_hours: number;
  actual_hours?: number;
  assignee?: string;
}

const getOrCreateTeamId = () => {
  let teamId = localStorage.getItem('scrum_team_id');
  if (!teamId) {
    teamId = 'team_' + Date.now();
    localStorage.setItem('scrum_team_id', teamId);
  }
  return teamId;
};

export default function SCRUMDashboard() {
  const [teamId, setTeamId] = useState(getOrCreateTeamId());
  const [newSprintName, setNewSprintName] = useState('');
  const [newSprintGoal, setNewSprintGoal] = useState('');
  const [newStoryTitle, setNewStoryTitle] = useState('');
  const [newStoryDescription, setNewStoryDescription] = useState('');
  const [newStoryPoints, setNewStoryPoints] = useState(1);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch current sprint
  const { data: currentSprint, isLoading: sprintLoading } = useQuery({
    queryKey: ['current-sprint', teamId],
    queryFn: () => scrumAPI.getCurrentSprint(teamId).then(res => res.data),
    enabled: !!teamId,
  });

  // Fetch backlog
  const { data: backlog } = useQuery({
    queryKey: ['backlog', teamId],
    queryFn: () => scrumAPI.getBacklog(teamId).then(res => res.data),
    enabled: !!teamId,
  });

  // Fetch sprint metrics
  const { data: sprintMetrics } = useQuery({
    queryKey: ['sprint-metrics', teamId, currentSprint?.id],
    queryFn: () => scrumAPI.getSprintMetrics(teamId, currentSprint?.id).then(res => res.data),
    enabled: !!teamId && !!currentSprint?.id,
  });

  // Create sprint mutation
  const createSprintMutation = useMutation({
    mutationFn: scrumAPI.createSprint,
    onSuccess: () => {
      toast({ title: 'Sprint Created Successfully' });
      setNewSprintName('');
      setNewSprintGoal('');
      queryClient.invalidateQueries({ queryKey: ['current-sprint'] });
    },
  });

  // Create story mutation
  const createStoryMutation = useMutation({
    mutationFn: scrumAPI.createUserStory,
    onSuccess: () => {
      toast({ title: 'User Story Created Successfully' });
      setNewStoryTitle('');
      setNewStoryDescription('');
      setNewStoryPoints(1);
      queryClient.invalidateQueries({ queryKey: ['backlog'] });
    },
  });

  // Start sprint mutation
  const startSprintMutation = useMutation({
    mutationFn: () => scrumAPI.startSprint(teamId, currentSprint?.id || ''),
    onSuccess: () => {
      toast({ title: 'Sprint Started!' });
      queryClient.invalidateQueries({ queryKey: ['current-sprint'] });
    },
  });

  // Update story status mutation
  const updateStoryMutation = useMutation({
    mutationFn: ({ storyId, status }: { storyId: string; status: string }) =>
      scrumAPI.updateUserStoryStatus(teamId, storyId, status),
    onSuccess: () => {
      toast({ title: 'Story Status Updated' });
      queryClient.invalidateQueries({ queryKey: ['current-sprint'] });
      queryClient.invalidateQueries({ queryKey: ['backlog'] });
    },
  });

  const handleCreateSprint = () => {
    if (!newSprintName || !newSprintGoal) {
      toast({ title: 'Error', description: 'Please fill in all fields', variant: 'destructive' });
      return;
    }

    const startDate = new Date();
    const endDate = new Date();
    endDate.setDate(startDate.getDate() + 14); // 2-week sprint

    createSprintMutation.mutate({
      team_id: teamId,
      name: newSprintName,
      goal: newSprintGoal,
      start_date: startDate.toISOString(),
      end_date: endDate.toISOString(),
    });
  };

  const handleCreateStory = () => {
    if (!newStoryTitle || !newStoryDescription) {
      toast({ title: 'Error', description: 'Please fill in all fields', variant: 'destructive' });
      return;
    }

    createStoryMutation.mutate({
      team_id: teamId,
      title: newStoryTitle,
      description: newStoryDescription,
      story_points: newStoryPoints,
      acceptance_criteria: [],
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'done': return 'default';
      case 'in_progress': return 'secondary';
      case 'review': return 'outline';
      default: return 'outline';
    }
  };

  const calculateSprintProgress = () => {
    if (!currentSprint?.stories) return 0;
    const totalStories = currentSprint.stories.length;
    const completedStories = currentSprint.stories.filter(s => s.status === 'done').length;
    return totalStories > 0 ? (completedStories / totalStories) * 100 : 0;
  };

  const calculateVelocity = () => {
    if (!currentSprint?.stories) return 0;
    return currentSprint.stories
      .filter(s => s.status === 'done')
      .reduce((sum, s) => sum + s.story_points, 0);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">SCRUM Dashboard</h2>
        <Badge variant="outline" className="text-lg px-4 py-2">
          Team: {teamId.slice(-8)}
        </Badge>
      </div>

      {/* Sprint Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Sprint</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {currentSprint?.name || 'No Active Sprint'}
            </div>
            <p className="text-xs text-muted-foreground">
              {currentSprint?.status || 'Create a sprint to get started'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sprint Progress</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.round(calculateSprintProgress())}%</div>
            <Progress value={calculateSprintProgress()} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Velocity</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{calculateVelocity()}</div>
            <p className="text-xs text-muted-foreground">Story Points</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Team Stories</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(currentSprint?.stories?.length || 0) + (backlog?.length || 0)}
            </div>
            <p className="text-xs text-muted-foreground">Total Stories</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="sprint" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="sprint">Current Sprint</TabsTrigger>
          <TabsTrigger value="backlog">Product Backlog</TabsTrigger>
          <TabsTrigger value="planning">Sprint Planning</TabsTrigger>
          <TabsTrigger value="metrics">Metrics & Reports</TabsTrigger>
        </TabsList>

        <TabsContent value="sprint" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Sprint Board</CardTitle>
              {currentSprint && (
                <div className="text-sm text-muted-foreground">
                  Goal: {currentSprint.goal}
                </div>
              )}
            </CardHeader>
            <CardContent>
              {!currentSprint && (
                <div className="text-center py-8">
                  <p className="text-muted-foreground mb-4">No active sprint</p>
                  <Button onClick={() => toast({ title: 'Create a sprint in Sprint Planning tab' })}>
                    Go to Sprint Planning
                  </Button>
                </div>
              )}
              
              {currentSprint && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {['backlog', 'in_progress', 'review', 'done'].map((status) => (
                    <div key={status} className="space-y-2">
                      <h4 className="font-semibold capitalize flex items-center gap-2">
                        {status === 'done' && <CheckCircle className="h-4 w-4 text-green-600" />}
                        {status === 'in_progress' && <AlertTriangle className="h-4 w-4 text-yellow-600" />}
                        {status.replace('_', ' ')}
                        <Badge variant="secondary">
                          {currentSprint.stories?.filter(s => s.status === status).length || 0}
                        </Badge>
                      </h4>
                      
                      <div className="space-y-2 min-h-[200px] border-2 border-dashed border-muted rounded-lg p-2">
                        {currentSprint.stories
                          ?.filter(story => story.status === status)
                          .map((story) => (
                            <Card key={story.id} className="cursor-pointer hover:shadow-md transition-shadow">
                              <CardContent className="p-3">
                                <div className="flex justify-between items-start mb-2">
                                  <h5 className="font-medium text-sm">{story.title}</h5>
                                  <Badge variant="outline">{story.story_points}pts</Badge>
                                </div>
                                <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
                                  {story.description}
                                </p>
                                <div className="flex gap-1">
                                  {['backlog', 'in_progress', 'review', 'done'].map((newStatus) => (
                                    <Button
                                      key={newStatus}
                                      size="sm"
                                      variant={story.status === newStatus ? "default" : "ghost"}
                                      className="text-xs px-2 py-1 h-6"
                                      onClick={() => updateStoryMutation.mutate({
                                        storyId: story.id,
                                        status: newStatus
                                      })}
                                    >
                                      {newStatus.replace('_', ' ')}
                                    </Button>
                                  ))}
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="backlog" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Product Backlog</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 border rounded-lg">
                <Input
                  placeholder="Story title"
                  value={newStoryTitle}
                  onChange={(e) => setNewStoryTitle(e.target.value)}
                />
                <Input
                  type="number"
                  placeholder="Story points"
                  value={newStoryPoints}
                  min={1}
                  max={13}
                  onChange={(e) => setNewStoryPoints(parseInt(e.target.value) || 1)}
                />
                <Button onClick={handleCreateStory} disabled={createStoryMutation.isPending}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Story
                </Button>
                <Textarea
                  placeholder="Story description"
                  value={newStoryDescription}
                  onChange={(e) => setNewStoryDescription(e.target.value)}
                  className="md:col-span-3"
                />
              </div>
              
              <div className="space-y-2">
                {backlog?.map((story: UserStory) => (
                  <Card key={story.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-medium">{story.title}</h4>
                          <p className="text-sm text-muted-foreground mt-1">{story.description}</p>
                        </div>
                        <div className="flex items-center gap-2 ml-4">
                          <Badge variant="outline">{story.story_points} pts</Badge>
                          <Badge variant={getStatusColor(story.status)}>
                            {story.status.replace('_', ' ')}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="planning" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Sprint Planning</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 border rounded-lg">
                <Input
                  placeholder="Sprint name (e.g., Sprint 1)"
                  value={newSprintName}
                  onChange={(e) => setNewSprintName(e.target.value)}
                />
                <Button
                  onClick={handleCreateSprint}
                  disabled={createSprintMutation.isPending}
                  className="md:col-start-2"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Create Sprint
                </Button>
                <Textarea
                  placeholder="Sprint goal"
                  value={newSprintGoal}
                  onChange={(e) => setNewSprintGoal(e.target.value)}
                  className="md:col-span-2"
                />
              </div>

              {currentSprint && currentSprint.status === 'planning' && (
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium mb-2">Ready to Start Sprint?</h4>
                  <p className="text-sm text-muted-foreground mb-4">
                    Sprint: {currentSprint.name} | Goal: {currentSprint.goal}
                  </p>
                  <Button
                    onClick={() => startSprintMutation.mutate()}
                    disabled={startSprintMutation.isPending}
                  >
                    Start Sprint
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Sprint Metrics & Reports</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-4">Burndown Chart</h4>
                  <div className="h-48 border rounded-lg flex items-center justify-center text-muted-foreground">
                    Chart visualization would go here
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-4">Velocity Trend</h4>
                  <div className="h-48 border rounded-lg flex items-center justify-center text-muted-foreground">
                    Velocity chart would go here
                  </div>
                </div>
                
                <div className="md:col-span-2">
                  <h4 className="font-medium mb-4">Sprint Retrospective</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg text-green-600">What Went Well</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground">
                          Retrospective items would be listed here
                        </p>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg text-red-600">What Didn't Go Well</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground">
                          Issues and blockers would be listed here
                        </p>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg text-blue-600">Action Items</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground">
                          Improvement actions would be listed here
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}