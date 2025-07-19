import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Trophy, 
  Zap, 
  Flame, 
  Star, 
  TrendingUp, 
  Clock,
  Target,
  Award
} from 'lucide-react';
import { ccmAPI } from '@/lib/ccm-api';

interface UserProfile {
  id: string;
  username: string;
  total_xp: number;
  level: number;
  current_streak: number;
  longest_streak: number;
  total_commits: number;
  total_flow_time: number;
}

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  xp_reward: number;
  tier: string;
  unlocked_at?: string;
}

interface LeaderboardEntry {
  username: string;
  level: number;
  value: number;
  rank: number;
}

interface GamificationData {
  user_stats: {
    profile: UserProfile;
    recent_xp: Array<{ amount: number; source: string; timestamp: string }>;
    weekly_progress: {
      total_xp: number;
      transactions: number;
      active_days: number;
    };
    next_level_xp: number;
  };
  achievements: {
    unlocked: Achievement[];
    available: Achievement[];
    progress: Record<string, number>;
  };
  leaderboards: {
    xp: LeaderboardEntry[];
    streaks: LeaderboardEntry[];
  };
}

export const GamificationDashboard: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const [data, setData] = useState<GamificationData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const response = await ccmAPI.getGamificationDashboard(sessionId);
        if (response.data.success) {
          setData(response.data.dashboard);
        }
      } catch (error) {
        console.error('Failed to load gamification dashboard:', error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
    const interval = setInterval(loadDashboard, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [sessionId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center p-8 text-muted-foreground">
        Failed to load gamification data
      </div>
    );
  }

  const { user_stats, achievements, leaderboards } = data;
  const profile = user_stats.profile;
  const levelProgress = ((profile.total_xp % 100) / 100) * 100;

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Level</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{profile.level}</div>
            <Progress value={levelProgress} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {user_stats.next_level_xp} XP to next level
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total XP</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{profile.total_xp}</div>
            <p className="text-xs text-muted-foreground">
              +{user_stats.weekly_progress.total_xp} this week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Streak</CardTitle>
            <Flame className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{profile.current_streak}</div>
            <p className="text-xs text-muted-foreground">
              Longest: {profile.longest_streak} days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Flow Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.round(profile.total_flow_time / 60)}h</div>
            <p className="text-xs text-muted-foreground">
              Deep work sessions
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="achievements" className="space-y-4">
        <TabsList>
          <TabsTrigger value="achievements">Achievements</TabsTrigger>
          <TabsTrigger value="activity">Recent Activity</TabsTrigger>
          <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
        </TabsList>

        <TabsContent value="achievements" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Unlocked Achievements */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="h-5 w-5" />
                  Unlocked Achievements
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {achievements.unlocked.slice(0, 5).map((achievement) => (
                  <div key={achievement.id} className="flex items-center gap-3">
                    <div className="text-2xl">{achievement.icon}</div>
                    <div className="flex-1">
                      <div className="font-medium">{achievement.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {achievement.description}
                      </div>
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      +{achievement.xp_reward} XP
                    </Badge>
                  </div>
                ))}
                {achievements.unlocked.length === 0 && (
                  <div className="text-center text-muted-foreground py-4">
                    No achievements unlocked yet. Start coding to earn your first!
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Available Achievements */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Available Achievements
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {achievements.available
                  .filter(a => !achievements.unlocked.some(u => u.id === a.id))
                  .slice(0, 5)
                  .map((achievement) => (
                    <div key={achievement.id} className="flex items-center gap-3 opacity-60">
                      <div className="text-2xl grayscale">{achievement.icon}</div>
                      <div className="flex-1">
                        <div className="font-medium">{achievement.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {achievement.description}
                        </div>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {achievement.xp_reward} XP
                      </Badge>
                    </div>
                  ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Recent XP Activity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {user_stats.recent_xp.map((xp, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div>
                      <div className="font-medium capitalize">
                        {xp.source.replace('_', ' ')}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {new Date(xp.timestamp).toLocaleString()}
                      </div>
                    </div>
                    <Badge variant={xp.amount > 0 ? "default" : "destructive"}>
                      {xp.amount > 0 ? "+" : ""}{xp.amount} XP
                    </Badge>
                  </div>
                ))}
                {user_stats.recent_xp.length === 0 && (
                  <div className="text-center text-muted-foreground py-4">
                    No recent activity. Start coding to earn XP!
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="leaderboard" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="h-5 w-5" />
                  XP Leaderboard
                </CardTitle>
                <CardDescription>Weekly rankings</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {leaderboards.xp.slice(0, 10).map((entry, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-6 text-center font-mono text-sm">
                          #{entry.rank}
                        </div>
                        <div>
                          <div className="font-medium">{entry.username}</div>
                          <div className="text-sm text-muted-foreground">
                            Level {entry.level}
                          </div>
                        </div>
                      </div>
                      <div className="font-mono">{entry.value} XP</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Flame className="h-5 w-5" />
                  Streak Leaderboard
                </CardTitle>
                <CardDescription>Longest active streaks</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {leaderboards.streaks.slice(0, 10).map((entry, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-6 text-center font-mono text-sm">
                          #{entry.rank}
                        </div>
                        <div>
                          <div className="font-medium">{entry.username}</div>
                          <div className="text-sm text-muted-foreground">
                            Level {entry.level}
                          </div>
                        </div>
                      </div>
                      <div className="font-mono">{entry.value} days</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};