/**
 * PulseDev+ VSCode Gamification Integration
 * Tracks activities and syncs with gamification API
 */

import * as vscode from 'vscode';
import axios from 'axios';

interface GamificationConfig {
    apiUrl: string;
    sessionId: string;
    enabled: boolean;
}

interface UserProfile {
    id: string;
    username: string;
    total_xp: number;
    level: number;
    current_streak: number;
    longest_streak: number;
}

interface Achievement {
    id: string;
    name: string;
    description: string;
    icon: string;
    xp_reward: number;
    unlocked_at?: string;
}

export class GamificationTracker {
    private config: GamificationConfig;
    private isActiveSession = false;
    private statusBarItem: vscode.StatusBarItem;
    private userProfile: UserProfile | null = null;
    private activityBuffer: Array<any> = [];
    private lastSync = Date.now();
    private lastActiveState: boolean | null = null;

    constructor(context: vscode.ExtensionContext, sessionId: string) {
        this.config = {
            apiUrl: vscode.workspace.getConfiguration('pulsedev').get('apiUrl', 'http://localhost:8000'),
            sessionId,
            enabled: vscode.workspace.getConfiguration('pulsedev').get('gamificationEnabled', true)
        };

        // Create status bar item
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.command = 'pulsedev.showGamificationDashboard';
        context.subscriptions.push(this.statusBarItem);

        // Initialize tracking
        this.initializeTracking(context);
        this.syncSession();
        this.loadUserProfile();

        // Sync every 5 minutes
        setInterval(() => this.syncSession(), 5 * 60 * 1000);
        // Focus/blur event-based session sync
        vscode.window.onDidChangeWindowState((state) => {
            if (state.focused) {
                this.syncSession();
            } else {
                this.syncSession();
            }
        });
    }

    private initializeTracking(context: vscode.ExtensionContext) {
        // Track file edits
        vscode.workspace.onDidChangeTextDocument((event) => {
            if (event.document.uri.scheme === 'file') {
                this.trackActivity('file_edit', {
                    file_path: event.document.fileName,
                    changes: event.contentChanges.length
                });
            }
        });

        // Track file saves
        vscode.workspace.onDidSaveTextDocument((document) => {
            this.trackActivity('file_save', {
                file_path: document.fileName
            });
        });

        // Track debug sessions
        vscode.debug.onDidStartDebugSession(() => {
            this.trackActivity('debug_start', {});
        });

        vscode.debug.onDidTerminateDebugSession(() => {
            this.trackActivity('debug_end', {});
        });

        // Track terminal usage
        vscode.window.onDidOpenTerminal(() => {
            this.trackActivity('terminal_open', {});
        });

        // Track test runs (if test extension is available)
        this.setupTestTracking();

        // Register commands
        context.subscriptions.push(
            vscode.commands.registerCommand('pulsedev.showGamificationDashboard', () => {
                this.showGamificationDashboard();
            })
        );

        context.subscriptions.push(
            vscode.commands.registerCommand('pulsedev.viewAchievements', () => {
                this.showAchievements();
            })
        );
    }

    private async trackActivity(type: string, metadata: any) {
        if (!this.config.enabled || !this.isActiveSession) return;

        const activity = {
            type,
            session_id: this.config.sessionId,
            timestamp: new Date().toISOString(),
            metadata
        };

        this.activityBuffer.push(activity);

        // Flush buffer if it gets too large or enough time has passed
        if (this.activityBuffer.length >= 10 || Date.now() - this.lastSync > 30000) {
            await this.flushActivities();
        }

        // Award immediate XP for certain activities
        await this.awardXP(type, metadata);
    }

    private async awardXP(source: string, metadata: any) {
        if (!this.config.enabled || !this.isActiveSession) return;
        try {
            const response = await axios.post(`${this.config.apiUrl}/api/v1/gamification/xp/award`, {
                session_id: this.config.sessionId,
                source,
                metadata
            });

            if (response.data.success) {
                const xpEarned = response.data.xp_earned;
                if (xpEarned > 0) {
                    this.showXPNotification(xpEarned, source);
                    await this.loadUserProfile(); // Refresh profile
                }
            }
        } catch (error) {
            console.error('Failed to award XP:', error);
        }
    }

    private async flushActivities() {
        if (this.activityBuffer.length === 0) return;

        try {
            for (const activity of this.activityBuffer) {
                await axios.post(`${this.config.apiUrl}/api/v1/gamification/activity/track`, activity);
            }
            this.activityBuffer = [];
            this.lastSync = Date.now();
        } catch (error) {
            console.error('Failed to flush activities:', error);
        }
    }

    private async syncSession() {
        try {
            const response = await axios.post(`${this.config.apiUrl}/api/v1/gamification/session/sync`, {
                session_id: this.config.sessionId,
                platform: 'vscode'
            });
            const result = response.data;
            if (result.success) {
                this.isActiveSession = result.sync_data.active_session === this.config.sessionId;
                this.updateStatusBar();
            }
        } catch (error) {
            this.isActiveSession = false;
            this.updateStatusBar();
        }
    }

    private async loadUserProfile() {
        try {
            const response = await axios.get(
                `${this.config.apiUrl}/api/v1/gamification/profile/${this.config.sessionId}`
            );

            if (response.data.success) {
                this.userProfile = response.data.profile.profile;
                this.updateStatusBar();
            }
        } catch (error) {
            console.error('Failed to load user profile:', error);
            this.statusBarItem.text = "$(pulse) PulseDev+";
            this.statusBarItem.show();
        }
    }

    private updateStatusBar() {
        if (this.isActiveSession) {
            this.statusBarItem.text = '$(rocket) PulseDev+ (Active)';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
        } else {
            this.statusBarItem.text = '$(circle-slash) PulseDev+ (Inactive)';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
        }
        this.statusBarItem.show();
        // Show notification if state changed
        if (this.lastActiveState !== null && this.lastActiveState !== this.isActiveSession) {
            if (this.isActiveSession) {
                vscode.window.showInformationMessage('PulseDev+ is now the active session in VSCode.');
            } else {
                vscode.window.showWarningMessage('PulseDev+ is now inactive (not primary) in VSCode.');
            }
        }
        this.lastActiveState = this.isActiveSession;
    }

    private showXPNotification(xpEarned: number, source: string) {
        const message = `+${xpEarned} XP earned from ${source}!`;
        vscode.window.showInformationMessage(message, 'View Dashboard').then((selection) => {
            if (selection === 'View Dashboard') {
                this.showGamificationDashboard();
            }
        });
    }

    private async showGamificationDashboard() {
        try {
            const response = await axios.get(
                `${this.config.apiUrl}/api/v1/gamification/dashboard/${this.config.sessionId}`
            );

            if (response.data.success) {
                const dashboard = response.data.dashboard;
                this.createDashboardWebview(dashboard);
            }
        } catch (error) {
            vscode.window.showErrorMessage('Failed to load gamification dashboard');
        }
    }

    private createDashboardWebview(dashboard: any) {
        const panel = vscode.window.createWebviewPanel(
            'pulsedevGamification',
            'PulseDev+ Gamification Dashboard',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        panel.webview.html = this.getDashboardHtml(dashboard);
    }

    private getDashboardHtml(dashboard: any): string {
        const profile = dashboard.user_stats.profile;
        const achievements = dashboard.achievements.unlocked.slice(0, 5);
        const leaderboard = dashboard.leaderboards.xp.slice(0, 5);

        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { 
                    font-family: var(--vscode-font-family); 
                    color: var(--vscode-foreground);
                    background: var(--vscode-editor-background);
                    padding: 20px;
                }
                .header { display: flex; align-items: center; margin-bottom: 20px; }
                .level-badge { 
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    padding: 4px 12px;
                    border-radius: 16px;
                    margin-right: 12px;
                }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }
                .stat-card { 
                    background: var(--vscode-editor-background);
                    border: 1px solid var(--vscode-panel-border);
                    padding: 16px;
                    border-radius: 8px;
                }
                .achievement { 
                    display: flex; 
                    align-items: center; 
                    padding: 8px 0;
                    border-bottom: 1px solid var(--vscode-panel-border);
                }
                .achievement:last-child { border-bottom: none; }
                .achievement-icon { font-size: 24px; margin-right: 12px; }
                .leaderboard-item { 
                    display: flex; 
                    justify-content: space-between; 
                    padding: 8px 0;
                    border-bottom: 1px solid var(--vscode-panel-border);
                }
                .progress-bar {
                    background: var(--vscode-progressBar-background);
                    height: 8px;
                    border-radius: 4px;
                    overflow: hidden;
                    margin-top: 8px;
                }
                .progress-fill {
                    background: var(--vscode-progressBar-foreground);
                    height: 100%;
                    transition: width 0.3s ease;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="level-badge">Level ${profile.level}</div>
                <h1>PulseDev+ Dashboard</h1>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total XP</h3>
                    <div style="font-size: 24px; font-weight: bold;">${profile.total_xp}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${((profile.total_xp % 100) / 100) * 100}%"></div>
                    </div>
                </div>
                
                <div class="stat-card">
                    <h3>Current Streak</h3>
                    <div style="font-size: 24px; font-weight: bold;">🔥 ${profile.current_streak} days</div>
                    <div style="color: var(--vscode-descriptionForeground);">Longest: ${profile.longest_streak} days</div>
                </div>
                
                <div class="stat-card">
                    <h3>Commits</h3>
                    <div style="font-size: 24px; font-weight: bold;">${profile.total_commits}</div>
                    <div style="color: var(--vscode-descriptionForeground);">Total commits made</div>
                </div>
                
                <div class="stat-card">
                    <h3>Flow Time</h3>
                    <div style="font-size: 24px; font-weight: bold;">${Math.round(profile.total_flow_time / 60)} hrs</div>
                    <div style="color: var(--vscode-descriptionForeground);">Deep work sessions</div>
                </div>
            </div>
            
            <h2>Recent Achievements</h2>
            <div class="achievements">
                ${achievements.map(achievement => `
                    <div class="achievement">
                        <div class="achievement-icon">${achievement.icon}</div>
                        <div>
                            <div style="font-weight: bold;">${achievement.name}</div>
                            <div style="color: var(--vscode-descriptionForeground); font-size: 0.9em;">${achievement.description}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <h2>Leaderboard (Weekly)</h2>
            <div class="leaderboard">
                ${leaderboard.map((user, index) => `
                    <div class="leaderboard-item">
                        <span>#${index + 1} ${user.username} (Lv.${user.level})</span>
                        <span>${user.value} XP</span>
                    </div>
                `).join('')}
            </div>
        </body>
        </html>
        `;
    }

    private async showAchievements() {
        try {
            const response = await axios.get(
                `${this.config.apiUrl}/api/v1/gamification/achievements/${this.config.sessionId}`
            );

            if (response.data.success) {
                const achievements = response.data.achievements;
                vscode.window.showQuickPick(
                    achievements.unlocked.map((a: Achievement) => ({
                        label: `${a.icon} ${a.name}`,
                        description: a.description,
                        detail: `+${a.xp_reward} XP | Unlocked: ${new Date(a.unlocked_at!).toLocaleDateString()}`
                    })),
                    { placeHolder: 'Your Achievements' }
                );
            }
        } catch (error) {
            vscode.window.showErrorMessage('Failed to load achievements');
        }
    }

    private setupTestTracking() {
        // Listen for test results if Test Explorer is available
        const testResults = vscode.extensions.getExtension('ms-vscode.test-adapter-converter');
        if (testResults) {
            // Track test runs
            vscode.tests.onDidChangeTestResults((e) => {
                const passed = e.added.filter(result => result.outcome === vscode.TestRunOutcome.Passed).length;
                const failed = e.added.filter(result => result.outcome === vscode.TestRunOutcome.Failed).length;
                
                if (passed > 0) {
                    this.trackActivity('test_pass', { passed, failed });
                }
                if (failed > 0) {
                    this.trackActivity('test_fail', { passed, failed });
                }
            });
        }
    }

    dispose() {
        this.statusBarItem.dispose();
        this.flushActivities(); // Ensure all activities are sent
    }
}