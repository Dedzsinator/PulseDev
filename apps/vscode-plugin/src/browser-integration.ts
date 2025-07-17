import * as vscode from 'vscode';
import { ApiClient } from './apiClient';

export interface BrowserContext {
    tabs: Array<{
        url: string;
        title: string;
        active: boolean;
        timestamp: string;
    }>;
    focusTime: number;
    switchCount: number;
}

export class BrowserIntegration {
    private apiClient: ApiClient;
    private sessionId: string;
    
    constructor(apiClient: ApiClient, sessionId: string) {
        this.apiClient = apiClient;
        this.sessionId = sessionId;
        this.setupBrowserTracking();
    }
    
    private async setupBrowserTracking() {
        // Check if browser extension is available
        const hasExtension = await this.checkBrowserExtension();
        
        if (!hasExtension) {
            vscode.window.showInformationMessage(
                'Install PulseDev+ browser extension for complete context tracking',
                'Install Extension'
            ).then(selection => {
                if (selection === 'Install Extension') {
                    vscode.env.openExternal(vscode.Uri.parse('chrome://extensions/'));
                }
            });
        }
    }
    
    private async checkBrowserExtension(): Promise<boolean> {
        try {
            // Try to ping the browser extension
            const response = await fetch('http://localhost:8080/ping');
            return response.ok;
        } catch {
            return false;
        }
    }
    
    async getBrowserContext(): Promise<BrowserContext | null> {
        try {
            const response = await fetch('http://localhost:8080/context');
            if (!response.ok) {
                return null;
            }
            
            const context = await response.json();
            
            // Send browser context to CCM API
            await this.apiClient.sendContextEvent({
                sessionId: this.sessionId,
                agent: 'browser',
                type: 'context_snapshot',
                payload: context,
                timestamp: new Date().toISOString()
            });
            
            return context;
        } catch (error) {
            console.log('Browser extension not available:', error);
            return null;
        }
    }
    
    async trackBrowserActivity() {
        const context = await this.getBrowserContext();
        
        if (context) {
            // Analyze developer-relevant tabs
            const devTabs = context.tabs.filter(tab => 
                tab.url.includes('localhost') ||
                tab.url.includes('github.com') ||
                tab.url.includes('stackoverflow.com') ||
                tab.url.includes('docs.') ||
                tab.url.includes('developer.')
            );
            
            // Calculate focus score
            const focusScore = devTabs.length / Math.max(context.tabs.length, 1);
            
            await this.apiClient.sendContextEvent({
                sessionId: this.sessionId,
                agent: 'browser',
                type: 'activity_analysis',
                payload: {
                    totalTabs: context.tabs.length,
                    developmentTabs: devTabs.length,
                    focusScore,
                    switchCount: context.switchCount,
                    patterns: this.identifyBrowsingPatterns(context)
                },
                timestamp: new Date().toISOString()
            });
        }
    }
    
    private identifyBrowsingPatterns(context: BrowserContext): string[] {
        const patterns = [];
        
        if (context.switchCount > 10) {
            patterns.push('high_switching');
        }
        
        if (context.tabs.length > 15) {
            patterns.push('tab_hoarding');
        }
        
        const devTabRatio = context.tabs.filter(tab => 
            tab.url.includes('localhost') || tab.url.includes('github.com')
        ).length / context.tabs.length;
        
        if (devTabRatio > 0.7) {
            patterns.push('focused_development');
        }
        
        return patterns;
    }
    
    async startBrowserMonitoring() {
        // Start periodic browser monitoring
        const interval = setInterval(async () => {
            await this.trackBrowserActivity();
        }, 30000); // Every 30 seconds
        
        return () => clearInterval(interval);
    }
}