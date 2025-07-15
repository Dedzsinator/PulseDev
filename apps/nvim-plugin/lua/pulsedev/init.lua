-- lua/pulsedev/init.lua
-- Main PulseDev module

local M = {}

-- Submodules
local config = require('pulsedev.config')
local context = require('pulsedev.context')
local integrations = require('pulsedev.integrations')
local commands = require('pulsedev.commands')
local ui = require('pulsedev.ui')
local utils = require('pulsedev.utils')

-- Module state
M.state = {
  initialized = false,
  enabled = false,
  session_id = nil
}

-- Initialize the plugin
function M.setup(opts)
  opts = opts or {}
  
  -- Load configuration
  config.setup(opts)
  
  -- Early exit if disabled
  if not config.get('enabled') then
    return
  end
  
  -- Initialize logger
  utils.logger.setup(config.get('debug'))
  utils.logger.info('Initializing PulseDev plugin')
  
  -- Initialize session
  M.state.session_id = utils.session.create()
  
  -- Initialize integrations
  local integration_success = integrations.setup()
  if not integration_success then
    utils.logger.error('Failed to initialize integrations')
    return
  end
  
  -- Initialize context tracking
  context.setup()
  
  -- Initialize commands
  commands.setup()
  
  -- Initialize UI
  ui.setup()
  
  -- Mark as initialized and enabled
  M.state.initialized = true
  M.state.enabled = true
  
  utils.logger.info('PulseDev plugin initialized successfully')
  
  -- Start tracking
  M.start()
end

-- Start the plugin
function M.start()
  if not M.state.initialized or M.state.enabled then
    return
  end
  
  utils.logger.info('Starting PulseDev tracking')
  
  -- Start context tracking
  context.start()
  
  -- Start integrations
  integrations.start()
  
  -- Notify UI
  ui.notify('PulseDev started', vim.log.levels.INFO)
  
  M.state.enabled = true
end

-- Stop the plugin
function M.stop()
  if not M.state.initialized or not M.state.enabled then
    return
  end
  
  utils.logger.info('Stopping PulseDev tracking')
  
  -- Stop context tracking
  context.stop()
  
  -- Stop integrations
  integrations.stop()
  
  -- Notify UI
  ui.notify('PulseDev stopped', vim.log.levels.INFO)
  
  M.state.enabled = false
end

-- Toggle plugin state
function M.toggle()
  if M.state.enabled then
    M.stop()
  else
    M.start()
  end
end

-- Get plugin status
function M.status()
  return {
    initialized = M.state.initialized,
    enabled = M.state.enabled,
    session_id = M.state.session_id,
    config = config.get_all(),
    integrations = integrations.status(),
    context = context.status()
  }
end

-- Get session ID
function M.get_session_id()
  return M.state.session_id
end

-- Health check
function M.health()
  local health = {
    ok = true,
    issues = {}
  }
  
  -- Check Neovim version
  if vim.fn.has('nvim-0.8') == 0 then
    health.ok = false
    table.insert(health.issues, 'Neovim 0.8+ required')
  end
  
  -- Check integrations
  local integration_health = integrations.health()
  if not integration_health.ok then
    health.ok = false
    for _, issue in ipairs(integration_health.issues) do
      table.insert(health.issues, issue)
    end
  end
  
  return health
end

return M