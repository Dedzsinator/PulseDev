// src/background/index.ts
// Background script entry point

import { TabManager } from './tab-manager';
import { ActivityTracker } from './activity-tracker';
import { EventHandler } from './event-handler';
import { SessionManager } from './session-manager';
import { Config } from '../utils/config';
import { Logger } from '../utils/logger';
import { RedisClient } from '../integrations/redis-client';
import { ApiClient } from '../integrations/api-client';

class PulseDevBackground {
  private tabManager: TabManager;
  private activityTracker: ActivityTracker;
  private eventHandler: EventHandler;
  private sessionManager: SessionManager;
  private config: Config;
  private logger: Logger;
  private redisClient: RedisClient;
  private apiClient: ApiClient;

  constructor() {
    this.config = new Config();
    this.logger = new Logger(this.config.get('debug'));
    this.redisClient = new RedisClient(this.config.get('redis'));
    this.apiClient = new ApiClient(this.config.get('api'));
    
    this.sessionManager = new SessionManager(this.config, this.logger);
    this.tabManager = new TabManager(this.config, this.logger, this.