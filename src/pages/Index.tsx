import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import CCMDashboard from '@/components/CCMDashboard';
import GamificationDashboard from '@/components/GamificationDashboard';
import SCRUMDashboard from '@/components/SCRUMDashboard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Brain, Trophy, Calendar } from 'lucide-react';

const Index = () => {
  const [activeTab, setActiveTab] = useState('ccm');

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4 gradient-text">PulseDev+ Platform</h1>
          <p className="text-xl text-muted-foreground">
            The Ultimate Developer Productivity & Gamification Platform
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="ccm" className="flex items-center gap-2">
              <Brain className="h-4 w-4" />
              CCM Dashboard
            </TabsTrigger>
            <TabsTrigger value="gamification" className="flex items-center gap-2">
              <Trophy className="h-4 w-4" />
              Gamification
            </TabsTrigger>
            <TabsTrigger value="scrum" className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              SCRUM
            </TabsTrigger>
          </TabsList>

          <TabsContent value="ccm">
            <CCMDashboard />
          </TabsContent>

          <TabsContent value="gamification">
            <GamificationDashboard sessionId="default-session" />
          </TabsContent>

          <TabsContent value="scrum">
            <SCRUMDashboard />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
