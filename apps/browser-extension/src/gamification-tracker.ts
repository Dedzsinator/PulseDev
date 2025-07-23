// Add this at the top of the file for TypeScript global chrome support
// @ts-ignore
declare const chrome: any;

/**
 * PulseDev+ Browser Extension Gamification Tracker
 * Tracks browser activities and syncs with gamification API
 *
 * Configurable via constructor or environment variables:
 *   - apiUrl: API endpoint (default: window.PULSEDEV_API_URL or 'http://localhost:8000')
 *   - sessionId: Session ID (default: generated)
 *   - enabled: Enable/disable tracking (default: true)
 */

interface GamificationConfig {
    apiUrl: string;
    sessionId: string;
    enabled: boolean;
}

interface ActivityData {
    type: string;
    session_id: string;
    timestamp: string;
    metadata: any;
}

export class BrowserGamificationTracker {
    private config: GamificationConfig;
    private activityBuffer: ActivityData[] = [];
    private lastSync = Date.now();
    private syncInterval: number;
    private isActiveSession = false;

    constructor(config?: Partial<GamificationConfig>) {
        const apiUrl = config?.apiUrl || (window as any).PULSEDEV_API_URL || process.env.PULSEDEV_API_URL || 'http://localhost:8000';
        const sessionId = config?.sessionId || this.generateSessionId();
        const enabled = config?.enabled !== undefined ? config.enabled : true;
        this.config = { apiUrl, sessionId, enabled };

        this.initializeTracking();
        this.syncSession();

        // Sync every 30 seconds
        this.syncInterval = window.setInterval(() => {
            this.flushActivities();
        }, 30000);

        // Sync session every 5 minutes
        setInterval(() => this.syncSession(), 5 * 60 * 1000);
    }

    public updateConfig(config: Partial<GamificationConfig>) {
        if (config.apiUrl) this.config.apiUrl = config.apiUrl;
        if (config.sessionId) this.config.sessionId = config.sessionId;
        if (config.enabled !== undefined) this.config.enabled = config.enabled;
    }

    private generateSessionId(): string {
        return `browser_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    private initializeTracking() {
        // Track tab switches
        if (typeof chrome !== 'undefined' && chrome.tabs) {
            chrome.tabs.onActivated.addListener((activeInfo) => {
                this.trackActivity('tab_switch', {
                    tab_id: activeInfo.tabId
                });
            });

            // Track page navigation
            chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
                if (changeInfo.status === 'complete' && tab.url) {
                    this.trackActivity('page_navigation', {
                        tab_id: tabId,
                        url: this.sanitizeUrl(tab.url),
                        title: tab.title
                    });

                    // Award XP for development-related sites
                    if (this.isDevelopmentSite(tab.url)) {
                        this.awardXP('dev_browsing', {
                            url: this.sanitizeUrl(tab.url),
                            title: tab.title
                        });
                    }
                }
            });
        }

        // Track window focus
        if (typeof chrome !== 'undefined' && chrome.windows) {
            chrome.windows.onFocusChanged.addListener((windowId) => {
                if (windowId === chrome.windows.WINDOW_ID_NONE) {
                    this.trackActivity('browser_blur', {});
                } else {
                    this.trackActivity('browser_focus', { window_id: windowId });
                }
            });
        }

        // Track bookmark creation (dev resources)
        if (typeof chrome !== 'undefined' && chrome.bookmarks) {
            chrome.bookmarks.onCreated.addListener((id, bookmark) => {
                if (bookmark.url && this.isDevelopmentSite(bookmark.url)) {
                    this.awardXP('dev_bookmark', {
                        url: this.sanitizeUrl(bookmark.url),
                        title: bookmark.title
                    });
                }
            });
        }

        // Listen for messages from content scripts
        if (typeof chrome !== 'undefined' && chrome.runtime) {
            chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
                if (message.type === 'gamification_activity') {
                    this.trackActivity(message.activity_type, message.metadata);
                    this.awardXP(message.activity_type, message.metadata);
                }
            });
        }
    }

    private async trackActivity(type: string, metadata: any) {
        if (!this.config.enabled || !this.isActiveSession) return;

        const activity: ActivityData = {
            type,
            session_id: this.config.sessionId,
            timestamp: new Date().toISOString(),
            metadata
        };

        this.activityBuffer.push(activity);

        // Flush buffer if it gets too large
        if (this.activityBuffer.length >= 20) {
            await this.flushActivities();
        }
    }

    private async awardXP(source: string, metadata: any) {
        if (!this.config.enabled || !this.isActiveSession) return;

        try {
            const response = await fetch(`${this.config.apiUrl}/api/v1/gamification/xp/award`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.config.sessionId,
                    source,
                    metadata
                })
            });

            const result = await response.json();
            if (result.success && result.xp_earned > 0) {
                this.showXPNotification(result.xp_earned, source);
            }
        } catch (error) {
            console.error('Failed to award XP:', error);
        }
    }

    private async flushActivities() {
        if (this.activityBuffer.length === 0) return;

        try {
            const activities = [...this.activityBuffer];
            this.activityBuffer = [];

            for (const activity of activities) {
                await fetch(`${this.config.apiUrl}/api/v1/gamification/activity/track`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(activity)
                });
            }

            this.lastSync = Date.now();
        } catch (error) {
            console.error('Failed to flush activities:', error);
            // Re-add activities to buffer on failure
            this.activityBuffer.unshift(...this.activityBuffer);
        }
    }

    private async syncSession() {
        try {
            const response = await fetch(`${this.config.apiUrl}/api/v1/gamification/session/sync`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.config.sessionId,
                    platform: 'browser'
                })
            });

            const result = await response.json();
            if (result.success) {
                this.isActiveSession = result.sync_data.active_session === this.config.sessionId;
                // Update badge with current stats
                if (result.sync_data.user_profile) {
                    this.updateBadge(result.sync_data.user_profile);
                }
            }
        } catch (error) {
            console.error('Failed to sync session:', error);
        }
    }

    private updateBadge(userProfile: any) {
        if (typeof chrome !== 'undefined' && chrome.action) {
            // Update extension badge with level
            chrome.action.setBadgeText({
                text: `L${userProfile.level}`
            });

            chrome.action.setBadgeBackgroundColor({
                color: '#4CAF50'
            });

            chrome.action.setTitle({
                title: `PulseDev+ | Level ${userProfile.level} | ${userProfile.total_xp} XP | 🔥${userProfile.current_streak}`
            });
        }
    }

    private showXPNotification(xpEarned: number, source: string) {
        if (typeof chrome !== 'undefined' && chrome.notifications) {
            // Create notification
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'icons/icon-48.png',
                title: 'PulseDev+ XP Earned!',
                message: `+${xpEarned} XP from ${source}`
            });

            // Auto-clear notification after 3 seconds
            setTimeout(() => {
                if (chrome.notifications) {
                    chrome.notifications.clear('xp_notification');
                }
            }, 3000);
        }
    }

    private isDevelopmentSite(url: string): boolean {
        const devSites = [
            'github.com',
            'stackoverflow.com',
            'developer.mozilla.org',
            'docs.microsoft.com',
            'nodejs.org',
            'npmjs.com',
            'developer.chrome.com',
            'firebase.google.com',
            'aws.amazon.com',
            'cloud.google.com',
            'azure.microsoft.com',
            'digitalocean.com',
            'vercel.com',
            'netlify.com',
            'heroku.com',
            'codepen.io',
            'jsfiddle.net',
            'codesandbox.io',
            'replit.com',
            'devdocs.io',
            'mdn.io'
        ];

        return devSites.some(site => url.includes(site));
    }

    private sanitizeUrl(url: string): string {
        try {
            const urlObj = new URL(url);
            // Remove query parameters and fragments for privacy
            return `${urlObj.protocol}//${urlObj.hostname}${urlObj.pathname}`;
        } catch {
            return 'invalid-url';
        }
    }

    public dispose() {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
        }
        this.flushActivities(); // Ensure all activities are sent
    }
}

// Initialize gamification tracker with default config
export const gamificationTracker = new BrowserGamificationTracker();