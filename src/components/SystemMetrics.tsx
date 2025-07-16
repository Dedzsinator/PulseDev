import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { energyAPI, flowAPI } from '@/lib/api';
import { Activity, Brain, GitCommit, Clock } from 'lucide-react';

interface SystemMetricsProps {
  sessionId: string;
}

export default function SystemMetrics({ sessionId }: SystemMetricsProps) {
  const { data: energyMetrics } = useQuery({
    queryKey: ['energy-metrics', sessionId],
    queryFn: () => energyAPI.getMetrics(sessionId).then(res => res.data),
    enabled: !!sessionId,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: flowInsights } = useQuery({
    queryKey: ['flow-insights', sessionId],
    queryFn: () => flowAPI.getInsights(sessionId).then(res => res.data),
    enabled: !!sessionId,
    refetchInterval: 30000,
  });

  const metrics = energyMetrics || {
    flow_time_minutes: 0,
    productivity_score: 0,
    context_switches: 0,
    test_pass_rate: 0,
    commit_frequency: 0,
    error_rate: 0,
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getProgressColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Flow Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.flow_time_minutes}m</div>
            <p className="text-xs text-muted-foreground">
              Today's focused time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Productivity</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getScoreColor(metrics.productivity_score)}`}>
              {metrics.productivity_score}%
            </div>
            <Progress 
              value={metrics.productivity_score} 
              className="mt-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Context Switches</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.context_switches}</div>
            <p className="text-xs text-muted-foreground">
              Task changes today
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Test Pass Rate</CardTitle>
            <GitCommit className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getScoreColor(metrics.test_pass_rate)}`}>
              {metrics.test_pass_rate}%
            </div>
            <Progress 
              value={metrics.test_pass_rate} 
              className="mt-2"
            />
          </CardContent>
        </Card>
      </div>

      {flowInsights && (
        <Card>
          <CardHeader>
            <CardTitle>Flow Insights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Badge variant={flowInsights.in_flow ? "default" : "secondary"}>
                {flowInsights.in_flow ? "In Flow" : "Not in Flow"}
              </Badge>
              {flowInsights.should_break && (
                <Badge variant="destructive">Break Recommended</Badge>
              )}
              {flowInsights.high_productivity && (
                <Badge variant="default">High Productivity</Badge>
              )}
            </div>
            
            {flowInsights.recommendations && (
              <div className="space-y-2">
                <h4 className="font-medium">Recommendations:</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  {flowInsights.recommendations.map((rec: string, index: number) => (
                    <li key={index}>• {rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}