import React, { useEffect, useRef } from 'react';
import { motion, useScroll, useTransform, useInView } from 'framer-motion';
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
  Monitor,
  Sparkles,
  Cpu,
  Database,
  Layers,
  Users
} from 'lucide-react';

const AnimatedSection = ({ children, className = "" }: { children: React.ReactNode, className?: string }) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 75 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 75 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

const FloatingCard = ({ children, delay = 0 }: { children: React.ReactNode, delay?: number }) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, delay, ease: "easeOut" }}
      whileHover={{
        y: -10,
        transition: { duration: 0.3 }
      }}
      className="h-full"
    >
      {children}
    </motion.div>
  );
};

const ParallaxBackground = () => {
  const { scrollYProgress } = useScroll();
  const y1 = useTransform(scrollYProgress, [0, 1], [0, -100]);
  const y2 = useTransform(scrollYProgress, [0, 1], [0, -200]);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <motion.div
        style={{ y: y1 }}
        className="absolute top-20 left-10 w-72 h-72 bg-primary/5 rounded-full blur-3xl"
      />
      <motion.div
        style={{ y: y2 }}
        className="absolute top-40 right-10 w-96 h-96 bg-primary/3 rounded-full blur-3xl"
      />
    </div>
  );
};

const EnhancedLanding = () => {
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"]
  });

  const backgroundY = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);
  const textY = useTransform(scrollYProgress, [0, 1], ["0%", "30%"]);

  const features = [
    {
      icon: <Brain className="h-8 w-8" />,
      title: "Cognitive Context Mirror",
      description: "Continuously tracks your development environment with AES-256-GCM encryption",
      details: ["File edits", "Terminal history", "Debug traces", "IDE usage", "Browser tabs"],
      category: "Core",
      gradient: "from-blue-500/20 to-purple-500/20"
    },
    {
      icon: <Bot className="h-8 w-8" />,
      title: "AI Prompt Generator",
      description: "Auto-generates rich, context-aware prompts when you're stuck",
      details: ["Error context", "Relevant files", "Terminal commands", "Browser context"],
      category: "AI",
      gradient: "from-green-500/20 to-teal-500/20"
    },
    {
      icon: <Code2 className="h-8 w-8" />,
      title: "Pair Programming Ghost",
      description: "Detects coding loops and provides intelligent rubber duck debugging",
      details: ["Loop detection", "Thought reconstruction", "Smart suggestions"],
      category: "AI",
      gradient: "from-orange-500/20 to-red-500/20"
    },
    {
      icon: <GitBranch className="h-8 w-8" />,
      title: "Auto Commit Writer",
      description: "AI-generated commit messages with context tags and issue linking",
      details: ["Error type detection", "File path analysis", "Jira integration"],
      category: "Git",
      gradient: "from-purple-500/20 to-pink-500/20"
    },
    {
      icon: <Zap className="h-8 w-8" />,
      title: "Flow Orchestrator",
      description: "Detects deep-work states and optimizes your environment",
      details: ["Keystroke analysis", "Notification control", "Calendar integration"],
      category: "Flow",
      gradient: "from-yellow-500/20 to-orange-500/20"
    },
    {
      icon: <BarChart3 className="h-8 w-8" />,
      title: "Energy Score Algorithm",
      description: "Calculates cognitive efficiency and burnout prevention",
      details: ["Flow duration tracking", "Test pass rates", "Context switches"],
      category: "Analytics",
      gradient: "from-cyan-500/20 to-blue-500/20"
    },
    {
      icon: <Target className="h-8 w-8" />,
      title: "Code Relationship Mapper",
      description: "Impact analysis and dependency visualization",
      details: ["Change forecasting", "Module impact", "Coverage gaps"],
      category: "Analysis",
      gradient: "from-indigo-500/20 to-purple-500/20"
    },
    {
      icon: <Clock className="h-8 w-8" />,
      title: "Git Activity Monitor",
      description: "Comprehensive Git behavior analysis",
      details: ["Stale branches", "Long PRs", "Revert patterns"],
      category: "Git",
      gradient: "from-emerald-500/20 to-green-500/20"
    },
    {
      icon: <Users className="h-8 w-8" />,
      title: "Team Collaboration Rooms",
      description: "Secure team spaces with role-based access and invite codes",
      details: ["Team rooms", "Role-based permissions", "Slack & Jira integration", "Activity tracking"],
      category: "Collaboration",
      gradient: "from-violet-500/20 to-purple-500/20"
    },
    {
      icon: <Trophy className="h-8 w-8" />,
      title: "Unified Gamification",
      description: "XP, achievements, and streaks across all platforms",
      details: ["Cross-platform sync", "Achievement system", "Leaderboards"],
      category: "Gamification",
      gradient: "from-rose-500/20 to-pink-500/20"
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
    { label: "Lines of Code Tracked", value: "10M+", icon: <Code2 className="h-6 w-6" /> },
    { label: "Commits Analyzed", value: "100K+", icon: <GitBranch className="h-6 w-6" /> },
    { label: "Flow Hours Detected", value: "50K+", icon: <Zap className="h-6 w-6" /> },
    { label: "Achievements Unlocked", value: "25+", icon: <Trophy className="h-6 w-6" /> }
  ];

  const architectureFeatures = [
    {
      icon: <Shield className="h-8 w-8" />,
      title: "Security First",
      description: "AES-256-GCM encryption, ephemeral mode, and consent gateways"
    },
    {
      icon: <Database className="h-8 w-8" />,
      title: "Real-Time Sync",
      description: "Cross-platform synchronization with active session management"
    },
    {
      icon: <Cpu className="h-8 w-8" />,
      title: "Time-Series Analytics",
      description: "TimescaleDB for high-performance temporal data analysis"
    }
  ];

  return (
    <div ref={containerRef} className="min-h-screen relative overflow-hidden">
      <ParallaxBackground />

      {/* Hero Section */}
      <section className="relative px-6 py-32 text-center min-h-screen flex items-center justify-center">
        <motion.div
          style={{ y: textY }}
          className="mx-auto max-w-5xl z-10"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="mb-8 flex justify-center"
          >
            <Badge variant="secondary" className="px-6 py-3 text-base font-medium bg-gradient-to-r from-primary/10 to-primary/5 hover:shadow-lg transition-all duration-300">
              <Sparkles className="mr-2 h-4 w-4" />
              🚀 Now with Unified Gamification & AI Auto-Training
            </Badge>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.2 }}
            className="mb-8 text-6xl font-bold tracking-tight sm:text-7xl lg:text-8xl"
          >
            <span className="bg-gradient-to-r from-primary via-primary/80 to-primary bg-clip-text text-transparent drop-shadow-lg">
              PulseDev+
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="mb-12 text-xl text-muted-foreground sm:text-2xl lg:text-3xl max-w-4xl mx-auto leading-relaxed"
          >
            The AI-powered developer companion that learns from your coding patterns,
            boosts productivity, and gamifies your development journey with continuous learning.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="flex flex-col items-center gap-6 sm:flex-row sm:justify-center"
          >
            <Button
              size="lg"
              className="px-10 py-6 text-xl font-semibold bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg hover:shadow-xl transition-all duration-300 group"
              onClick={() => window.location.hash = '#/dashboard'}
            >
              <Gamepad2 className="mr-3 h-6 w-6 group-hover:rotate-12 transition-transform" />
              Start Your Journey
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="px-10 py-6 text-xl font-semibold border-2 hover:bg-primary/5 transition-all duration-300"
              onClick={() => window.location.hash = '#/teams'}
            >
              <Users className="mr-3 h-6 w-6" />
              Team Collaboration
            </Button>
          </motion.div>
        </motion.div>

        {/* Floating Elements */}
        <motion.div
          animate={{ y: [0, -20, 0] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-20 left-10 opacity-20"
        >
          <Code2 className="h-16 w-16 text-primary" />
        </motion.div>
        <motion.div
          animate={{ y: [0, 20, 0] }}
          transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
          className="absolute top-32 right-16 opacity-20"
        >
          <Brain className="h-20 w-20 text-primary" />
        </motion.div>
        <motion.div
          animate={{ y: [0, -15, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 2 }}
          className="absolute bottom-32 left-20 opacity-20"
        >
          <Zap className="h-12 w-12 text-primary" />
        </motion.div>
      </section>

      {/* Enhanced Stats Section */}
      <AnimatedSection className="px-6 py-20 bg-gradient-to-r from-muted/30 to-muted/10">
        <div className="mx-auto max-w-6xl">
          <motion.div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            {stats.map((stat, index) => (
              <FloatingCard key={index} delay={index * 0.1}>
                <div className="text-center group">
                  <motion.div
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    className="mx-auto mb-4 w-fit p-3 rounded-full bg-primary/10 text-primary"
                  >
                    {stat.icon}
                  </motion.div>
                  <motion.div
                    initial={{ scale: 0 }}
                    whileInView={{ scale: 1 }}
                    transition={{ duration: 0.5, delay: index * 0.1 }}
                    className="text-4xl font-bold text-primary mb-2"
                  >
                    {stat.value}
                  </motion.div>
                  <div className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">
                    {stat.label}
                  </div>
                </div>
              </FloatingCard>
            ))}
          </motion.div>
        </div>
      </AnimatedSection>

      {/* Enhanced Features Grid */}
      <AnimatedSection className="px-6 py-24">
        <div className="mx-auto max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="mb-20 text-center"
          >
            <h2 className="mb-6 text-4xl font-bold sm:text-5xl lg:text-6xl">
              <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                9 Powerful Features
              </span>
              <br />
              One Unified Experience
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Every feature works together to create the ultimate developer experience with AI that learns and adapts
            </p>
          </motion.div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => (
              <FloatingCard key={index} delay={index * 0.1}>
                <Card className={`relative overflow-hidden transition-all duration-500 hover:shadow-2xl hover:scale-105 border-0 bg-gradient-to-br ${feature.gradient} backdrop-blur-sm`}>
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300"
                  />
                  <CardHeader className="relative z-10">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <motion.div
                          whileHover={{ rotate: 360 }}
                          transition={{ duration: 0.6 }}
                          className="rounded-xl bg-primary/20 p-3 text-primary backdrop-blur-sm"
                        >
                          {feature.icon}
                        </motion.div>
                        <div>
                          <CardTitle className="text-lg font-bold">{feature.title}</CardTitle>
                          <Badge variant="outline" className="mt-2 text-xs font-medium">
                            {feature.category}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <CardDescription className="text-sm leading-relaxed mt-4">
                      {feature.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="relative z-10">
                    <ul className="space-y-2">
                      {feature.details.map((detail, idx) => (
                        <motion.li
                          key={idx}
                          initial={{ opacity: 0, x: -10 }}
                          whileInView={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          className="flex items-center text-sm text-muted-foreground"
                        >
                          <div className="mr-3 h-2 w-2 rounded-full bg-primary/60" />
                          {detail}
                        </motion.li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </FloatingCard>
            ))}
          </div>
        </div>
      </AnimatedSection>

      {/* Platform Support */}
      <AnimatedSection className="px-6 py-24 bg-gradient-to-br from-muted/20 via-muted/10 to-transparent">
        <div className="mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-16 text-center"
          >
            <h2 className="mb-6 text-4xl font-bold sm:text-5xl">
              <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                Universal Platform Support
              </span>
            </h2>
            <p className="text-xl text-muted-foreground">
              Works seamlessly across all your favorite development tools
            </p>
          </motion.div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {platforms.map((platform, index) => (
              <FloatingCard key={index} delay={index * 0.1}>
                <Card className="text-center transition-all duration-500 hover:shadow-xl hover:scale-105 bg-gradient-to-br from-card to-card/50 backdrop-blur-sm border-primary/20">
                  <CardContent className="pt-8 pb-6">
                    <motion.div
                      whileHover={{ scale: 1.2, rotate: 15 }}
                      transition={{ duration: 0.3 }}
                      className="mb-6 flex justify-center"
                    >
                      <div className="rounded-xl bg-primary/10 p-4 text-primary">
                        {platform.icon}
                      </div>
                    </motion.div>
                    <h3 className="mb-3 text-lg font-semibold">{platform.name}</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {platform.description}
                    </p>
                  </CardContent>
                </Card>
              </FloatingCard>
            ))}
          </div>
        </div>
      </AnimatedSection>

      {/* Architecture Highlight */}
      <AnimatedSection className="px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <h2 className="mb-6 text-4xl font-bold sm:text-5xl">
              <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                Enterprise-Grade Architecture
              </span>
            </h2>
            <p className="mb-16 text-xl text-muted-foreground max-w-4xl mx-auto">
              Built on PostgreSQL + TimescaleDB + Redis with auto-training AI that learns during low usage periods
            </p>

            <div className="grid gap-10 md:grid-cols-3">
              {architectureFeatures.map((feature, index) => (
                <FloatingCard key={index} delay={index * 0.2}>
                  <div className="text-center group">
                    <motion.div
                      whileHover={{ scale: 1.1, y: -10 }}
                      className="mx-auto mb-6 rounded-xl bg-primary/10 p-6 w-fit group-hover:bg-primary/20 transition-all duration-300"
                    >
                      <div className="text-primary">
                        {feature.icon}
                      </div>
                    </motion.div>
                    <h3 className="mb-4 text-xl font-semibold group-hover:text-primary transition-colors">
                      {feature.title}
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </FloatingCard>
              ))}
            </div>
          </motion.div>
        </div>
      </AnimatedSection>

      {/* CTA Section */}
      <AnimatedSection className="px-6 py-24 bg-gradient-to-br from-primary/5 via-primary/10 to-primary/5">
        <div className="mx-auto max-w-4xl text-center">
          <motion.h2
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="mb-6 text-4xl font-bold sm:text-5xl"
          >
            Ready to Level Up Your Development?
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="mb-10 text-xl text-muted-foreground"
          >
            Join thousands of developers already using PulseDev+ to boost their productivity with AI that never stops learning
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.4 }}
            className="flex flex-col items-center gap-6 sm:flex-row sm:justify-center"
          >
            <Button
              size="lg"
              className="px-10 py-6 text-xl font-semibold bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg hover:shadow-xl transition-all duration-300 group"
            >
              <Trophy className="mr-3 h-6 w-6 group-hover:scale-110 transition-transform" />
              Get Started Free
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="px-10 py-6 text-xl font-semibold border-2 hover:bg-primary/5 transition-all duration-300"
            >
              View Documentation
            </Button>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.6 }}
            className="mt-8 text-sm text-muted-foreground"
          >
            No credit card required • Open source • Full data control • AI auto-trains during downtime
          </motion.p>
        </div>
      </AnimatedSection>

      {/* Enhanced Footer */}
      <footer className="border-t px-6 py-16 bg-gradient-to-br from-muted/10 to-transparent">
        <div className="mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="flex flex-col items-center justify-between gap-8 sm:flex-row"
          >
            <div className="text-center sm:text-left">
              <div className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                PulseDev+
              </div>
              <div className="text-muted-foreground mt-2">
                The AI-powered developer companion that learns with you
              </div>
            </div>

            <div className="flex gap-8 text-muted-foreground">
              {['Documentation', 'GitHub', 'Discord', 'Blog'].map((link, index) => (
                <motion.a
                  key={link}
                  href="#"
                  initial={{ opacity: 0, x: 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.05, color: 'hsl(var(--primary))' }}
                  className="hover:text-primary transition-all duration-300"
                >
                  {link}
                </motion.a>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5 }}
            className="mt-12 border-t pt-8 text-center text-sm text-muted-foreground"
          >
            © 2024 PulseDev+. Built with love by developers, for developers. Powered by continuous AI learning.
          </motion.div>
        </div>
      </footer>
    </div>
  );
};

export default EnhancedLanding;
