import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Brain, 
  Zap, 
  Trophy, 
  Clock, 
  GitBranch, 
  Target, 
  Shield, 
  Bot,
  Code2,
  Gamepad2,
  BarChart3,
  Globe,
  Smartphone,
  Monitor
} from 'lucide-react';

const Landing = () => {
  const features = [
    {
      icon: <Brain className="h-8 w-8" />,
      title: "Cognitive Context Mirror",
      description: "Continuously tracks your development environment with AES-256-GCM encryption",
      details: ["File edits", "Terminal history", "Debug traces", "IDE usage", "Browser tabs"],
      category: "Core"
    },
    {
      icon: <Bot className="h-8 w-8" />,
      title: "AI Prompt Generator",
      description: "Auto-generates rich, context-aware prompts when you're stuck",
      details: ["Error context", "Relevant files", "Terminal commands", "Browser context"],
      category: "AI"
    },
    {
      icon: <Code2 className="h-8 w-8" />,
      title: "Pair Programming Ghost",
      description: "Detects coding loops and provides intelligent rubber duck debugging",
      details: ["Loop detection", "Thought reconstruction", "Smart suggestions"],
      category: "AI"
    },
    {
      icon: <GitBranch className="h-8 w-8" />,
      title: "Auto Commit Writer",
      description: "AI-generated commit messages with context tags and issue linking",
      details: ["Error type detection", "File path analysis", "Jira integration"],
      category: "Git"
    },
    {
      icon: <Zap className="h-8 w-8" />,
      title: "Flow Orchestrator",
      description: "Detects deep-work states and optimizes your environment",
      details: ["Keystroke analysis", "Notification control", "Calendar integration"],
      category: "Flow"
    },
    {
      icon: <BarChart3 className="h-8 w-8" />,
      title: "Energy Score Algorithm",
      description: "Calculates cognitive efficiency and burnout prevention",
      details: ["Flow duration tracking", "Test pass rates", "Context switches"],
      category: "Analytics"
    },
    {
      icon: <Target className="h-8 w-8" />,
      title: "Code Relationship Mapper",
      description: "Impact analysis and dependency visualization",
      details: ["Change forecasting", "Module impact", "Coverage gaps"],
      category: "Analysis"
    },
    {
      icon: <Clock className="h-8 w-8" />,
      title: "Git Activity Monitor",
      description: "Comprehensive Git behavior analysis",
      details: ["Stale branches", "Long PRs", "Revert patterns"],
      category: "Git"
    },
    {
      icon: <Trophy className="h-8 w-8" />,
      title: "Unified Gamification",
      description: "XP, achievements, and streaks across all platforms",
      details: ["Cross-platform sync", "Achievement system", "Leaderboards"],
      category: "Gamification"
    }
  ];

  const platforms = [
    {
      icon: <Monitor className="h-6 w-6" />,
      name: "VSCode Extension",
      description: "Full IDE integration with real-time tracking"
    },
    {
      icon: <Globe className="h-6 w-6" />,
      name: "Browser Extension",
      description: "Tab tracking and development site recognition"
    },
    {
      icon: <Code2 className="h-6 w-6" />,
      name: "Neovim Plugin",
      description: "Lua-based plugin for Vim enthusiasts"
    },
    {
      icon: <Smartphone className="h-6 w-6" />,
      name: "Desktop App",
      description: "Tauri-based desktop application"
    }
  ];

  const stats = [
    { label: "Lines of Code Tracked", value: "10M+" },
    { label: "Commits Analyzed", value: "100K+" },
    { label: "Flow Hours Detected", value: "50K+" },
    { label: "Achievements Unlocked", value: "25+" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      {/* Hero Section */}
      <section className="px-6 py-20 text-center">
        <div className="mx-auto max-w-4xl">
          <div className="mb-6 flex justify-center">
            <Badge variant="secondary" className="px-4 py-2 text-sm font-medium">
              🚀 Now with Unified Gamification
            </Badge>
          </div>
          
          <h1 className="mb-6 text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
            <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              PulseDev+
            </span>
          </h1>
          
          <p className="mb-8 text-xl text-muted-foreground sm:text-2xl">
            The AI-powered developer companion that learns from your coding patterns,
            boosts productivity, and gamifies your development journey.
          </p>
          
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Button size="lg" className="px-8 py-4 text-lg">
              <Gamepad2 className="mr-2 h-5 w-5" />
              Start Your Journey
            </Button>
            <Button variant="outline" size="lg" className="px-8 py-4 text-lg">
              View Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="px-6 py-16">
        <div className="mx-auto max-w-6xl">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl font-bold text-primary">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
              9 Powerful Features, One Unified Experience
            </h2>
            <p className="text-lg text-muted-foreground">
              Every feature works together to create the ultimate developer experience
            </p>
          </div>
          
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => (
              <Card key={index} className="relative overflow-hidden transition-all hover:shadow-lg hover:scale-105">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-primary/10 p-2 text-primary">
                        {feature.icon}
                      </div>
                      <div>
                        <CardTitle className="text-lg">{feature.title}</CardTitle>
                        <Badge variant="outline" className="mt-1 text-xs">
                          {feature.category}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <CardDescription className="text-sm">
                    {feature.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1">
                    {feature.details.map((detail, idx) => (
                      <li key={idx} className="flex items-center text-sm text-muted-foreground">
                        <div className="mr-2 h-1.5 w-1.5 rounded-full bg-primary/60" />
                        {detail}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Platform Support */}
      <section className="px-6 py-20 bg-muted/30">
        <div className="mx-auto max-w-6xl">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
              Universal Platform Support
            </h2>
            <p className="text-lg text-muted-foreground">
              Works seamlessly across all your favorite development tools
            </p>
          </div>
          
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {platforms.map((platform, index) => (
              <Card key={index} className="text-center transition-all hover:shadow-md">
                <CardContent className="pt-6">
                  <div className="mb-4 flex justify-center">
                    <div className="rounded-lg bg-primary/10 p-3 text-primary">
                      {platform.icon}
                    </div>
                  </div>
                  <h3 className="mb-2 font-semibold">{platform.name}</h3>
                  <p className="text-sm text-muted-foreground">{platform.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture Highlight */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <div className="text-center">
            <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
              Enterprise-Grade Architecture
            </h2>
            <p className="mb-12 text-lg text-muted-foreground">
              Built on PostgreSQL + TimescaleDB + Redis for maximum performance and scalability
            </p>
            
            <div className="grid gap-8 md:grid-cols-3">
              <div className="text-center">
                <div className="mx-auto mb-4 rounded-lg bg-primary/10 p-4 w-fit">
                  <Shield className="h-8 w-8 text-primary" />
                </div>
                <h3 className="mb-2 font-semibold">Security First</h3>
                <p className="text-sm text-muted-foreground">
                  AES-256-GCM encryption, ephemeral mode, and consent gateways
                </p>
              </div>
              
              <div className="text-center">
                <div className="mx-auto mb-4 rounded-lg bg-primary/10 p-4 w-fit">
                  <Zap className="h-8 w-8 text-primary" />
                </div>
                <h3 className="mb-2 font-semibold">Real-Time Sync</h3>
                <p className="text-sm text-muted-foreground">
                  Cross-platform synchronization with active session management
                </p>
              </div>
              
              <div className="text-center">
                <div className="mx-auto mb-4 rounded-lg bg-primary/10 p-4 w-fit">
                  <BarChart3 className="h-8 w-8 text-primary" />
                </div>
                <h3 className="mb-2 font-semibold">Time-Series Analytics</h3>
                <p className="text-sm text-muted-foreground">
                  TimescaleDB for high-performance temporal data analysis
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20 bg-gradient-to-r from-primary/5 to-primary/10">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Ready to Level Up Your Development?
          </h2>
          <p className="mb-8 text-lg text-muted-foreground">
            Join thousands of developers already using PulseDev+ to boost their productivity
          </p>
          
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Button size="lg" className="px-8 py-4 text-lg">
              <Trophy className="mr-2 h-5 w-5" />
              Get Started Free
            </Button>
            <Button variant="outline" size="lg" className="px-8 py-4 text-lg">
              View Documentation
            </Button>
          </div>
          
          <p className="mt-6 text-sm text-muted-foreground">
            No credit card required • Open source • Full data control
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t px-6 py-12">
        <div className="mx-auto max-w-6xl">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="text-center sm:text-left">
              <div className="text-lg font-bold">PulseDev+</div>
              <div className="text-sm text-muted-foreground">
                The AI-powered developer companion
              </div>
            </div>
            
            <div className="flex gap-6 text-sm text-muted-foreground">
              <a href="#" className="hover:text-foreground transition-colors">
                Documentation
              </a>
              <a href="#" className="hover:text-foreground transition-colors">
                GitHub
              </a>
              <a href="#" className="hover:text-foreground transition-colors">
                Discord
              </a>
              <a href="#" className="hover:text-foreground transition-colors">
                Blog
              </a>
            </div>
          </div>
          
          <div className="mt-8 border-t pt-8 text-center text-sm text-muted-foreground">
            © 2024 PulseDev+. Built with love by developers, for developers.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;