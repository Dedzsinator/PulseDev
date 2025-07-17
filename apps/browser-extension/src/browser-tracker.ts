interface BrowserTab {
  id: number;
  url: string;
  title: string;
  active: boolean;
  timestamp: string;
}

interface BrowserContext {
  sessionId: string;
  tabs: BrowserTab[];
  activeTab: BrowserTab | null;
  focusTime: number;
  switchCount: number;
}

class BrowserContextTracker {
  private context: BrowserContext;
  private apiUrl: string = 'http://localhost:8000';
  private lastActivityTime: number = Date.now();
  
  constructor(sessionId: string) {
    this.context = {
      sessionId,
      tabs: [],
      activeTab: null,
      focusTime: 0,
      switchCount: 0
    };
    
    this.initializeTracking();
  }
  
  private async initializeTracking() {
    // Track tab changes
    chrome.tabs.onActivated.addListener(async (activeInfo) => {
      await this.handleTabSwitch(activeInfo.tabId);
    });
    
    // Track new tabs
    chrome.tabs.onCreated.addListener(async (tab) => {
      await this.handleTabCreated(tab);
    });
    
    // Track tab updates (URL changes)
    chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
      if (changeInfo.url) {
        await this.handleTabUpdated(tab);
      }
    });
    
    // Track tab closing
    chrome.tabs.onRemoved.addListener(async (tabId) => {
      await this.handleTabClosed(tabId);
    });
    
    // Track window focus changes
    chrome.windows.onFocusChanged.addListener(async (windowId) => {
      if (windowId === chrome.windows.WINDOW_ID_NONE) {
        await this.handleWindowBlur();
      } else {
        await this.handleWindowFocus();
      }
    });
    
    // Initialize current tabs
    await this.loadCurrentTabs();
  }
  
  private async loadCurrentTabs() {
    try {
      const tabs = await chrome.tabs.query({});
      this.context.tabs = tabs.map(tab => ({
        id: tab.id!,
        url: tab.url || '',
        title: tab.title || '',
        active: tab.active,
        timestamp: new Date().toISOString()
      }));
      
      const activeTab = tabs.find(tab => tab.active);
      if (activeTab) {
        this.context.activeTab = {
          id: activeTab.id!,
          url: activeTab.url || '',
          title: activeTab.title || '',
          active: true,
          timestamp: new Date().toISOString()
        };
      }
      
      await this.sendContextEvent('browser', 'tabs_loaded', {
        tabs: this.context.tabs,
        activeTab: this.context.activeTab
      });
    } catch (error) {
      console.error('Failed to load current tabs:', error);
    }
  }
  
  private async handleTabSwitch(tabId: number) {
    try {
      const tab = await chrome.tabs.get(tabId);
      
      // Update switch count
      this.context.switchCount++;
      
      // Update active tab
      this.context.activeTab = {
        id: tab.id!,
        url: tab.url || '',
        title: tab.title || '',
        active: true,
        timestamp: new Date().toISOString()
      };
      
      await this.sendContextEvent('browser', 'tab_switch', {
        tabId: tab.id,
        url: tab.url,
        title: tab.title,
        switchCount: this.context.switchCount
      });
      
      this.lastActivityTime = Date.now();
    } catch (error) {
      console.error('Failed to handle tab switch:', error);
    }
  }
  
  private async handleTabCreated(tab: chrome.tabs.Tab) {
    const browserTab: BrowserTab = {
      id: tab.id!,
      url: tab.url || '',
      title: tab.title || '',
      active: tab.active,
      timestamp: new Date().toISOString()
    };
    
    this.context.tabs.push(browserTab);
    
    await this.sendContextEvent('browser', 'tab_created', {
      tab: browserTab,
      totalTabs: this.context.tabs.length
    });
  }
  
  private async handleTabUpdated(tab: chrome.tabs.Tab) {
    // Update tab in context
    const tabIndex = this.context.tabs.findIndex(t => t.id === tab.id);
    if (tabIndex !== -1) {
      this.context.tabs[tabIndex] = {
        id: tab.id!,
        url: tab.url || '',
        title: tab.title || '',
        active: tab.active,
        timestamp: new Date().toISOString()
      };
    }
    
    // Check if it's a development-related site
    const devSites = ['localhost', 'github.com', 'stackoverflow.com', 'developer.mozilla.org'];
    const isDev = devSites.some(site => tab.url?.includes(site));
    
    await this.sendContextEvent('browser', 'tab_updated', {
      tabId: tab.id,
      url: tab.url,
      title: tab.title,
      isDevelopmentRelated: isDev
    });
  }
  
  private async handleTabClosed(tabId: number) {
    // Remove tab from context
    this.context.tabs = this.context.tabs.filter(tab => tab.id !== tabId);
    
    // Clear active tab if it was closed
    if (this.context.activeTab?.id === tabId) {
      this.context.activeTab = null;
    }
    
    await this.sendContextEvent('browser', 'tab_closed', {
      tabId,
      remainingTabs: this.context.tabs.length
    });
  }
  
  private async handleWindowFocus() {
    await this.sendContextEvent('browser', 'window_focus', {
      timestamp: new Date().toISOString(),
      activeTab: this.context.activeTab
    });
    
    this.lastActivityTime = Date.now();
  }
  
  private async handleWindowBlur() {
    const blurDuration = Date.now() - this.lastActivityTime;
    
    await this.sendContextEvent('browser', 'window_blur', {
      timestamp: new Date().toISOString(),
      focusDuration: blurDuration
    });
  }
  
  private async sendContextEvent(agent: string, type: string, payload: any) {
    try {
      const event = {
        sessionId: this.context.sessionId,
        agent,
        type,
        payload,
        timestamp: new Date().toISOString()
      };
      
      await fetch(`${this.apiUrl}/context/events`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(event)
      });
    } catch (error) {
      console.error('Failed to send context event:', error);
    }
  }
  
  public async getContextSnapshot(): Promise<BrowserContext> {
    // Update focus time
    this.context.focusTime = Date.now() - this.lastActivityTime;
    
    return { ...this.context };
  }
  
  public async analyzeBrowsingPatterns(): Promise<any> {
    const devTabs = this.context.tabs.filter(tab => 
      ['localhost', 'github.com', 'stackoverflow.com', 'docs.'].some(pattern => 
        tab.url.includes(pattern)
      )
    );
    
    const socialTabs = this.context.tabs.filter(tab =>
      ['twitter.com', 'facebook.com', 'instagram.com', 'linkedin.com'].some(pattern =>
        tab.url.includes(pattern)
      )
    );
    
    return {
      totalTabs: this.context.tabs.length,
      developmentTabs: devTabs.length,
      socialTabs: socialTabs.length,
      focusScore: this.calculateFocusScore(),
      switchFrequency: this.context.switchCount,
      patterns: this.identifyBrowsingPatterns()
    };
  }
  
  private calculateFocusScore(): number {
    if (this.context.tabs.length === 0) return 1;
    
    const devTabRatio = this.context.tabs.filter(tab => 
      ['localhost', 'github.com', 'docs.', 'stackoverflow.com'].some(pattern => 
        tab.url.includes(pattern)
      )
    ).length / this.context.tabs.length;
    
    const switchPenalty = Math.min(this.context.switchCount / 20, 0.5);
    
    return Math.max(0, devTabRatio - switchPenalty);
  }
  
  private identifyBrowsingPatterns(): string[] {
    const patterns = [];
    
    if (this.context.switchCount > 10) {
      patterns.push('high_switching');
    }
    
    if (this.context.tabs.length > 15) {
      patterns.push('tab_hoarding');
    }
    
    const devTabs = this.context.tabs.filter(tab => 
      ['localhost', 'github.com', 'docs.'].some(pattern => tab.url.includes(pattern))
    );
    
    if (devTabs.length > this.context.tabs.length * 0.7) {
      patterns.push('focused_development');
    }
    
    return patterns;
  }
}

// Background script initialization
if (typeof chrome !== 'undefined' && chrome.runtime) {
  let tracker: BrowserContextTracker;
  
  chrome.runtime.onStartup.addListener(() => {
    const sessionId = 'browser_' + Date.now();
    tracker = new BrowserContextTracker(sessionId);
  });
  
  chrome.runtime.onInstalled.addListener(() => {
    const sessionId = 'browser_' + Date.now();
    tracker = new BrowserContextTracker(sessionId);
  });
}

export { BrowserContextTracker };