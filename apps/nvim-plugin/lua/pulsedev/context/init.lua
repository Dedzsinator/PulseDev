-- lua/pulsedev/context/init.lua
-- Context tracking coordinator

local M = {}

-- Submodules
local cursor = require('pulsedev.context.cursor')
local buffer = require('pulsedev.context.buffer')
local activity = require('pulsedev.context.activity')
local flow = require('pulsedev.context.flow')

-- Dependencies
local config = require('pulsedev.config')
local utils = require('pulsedev.utils')
local integrations = require('pulsedev.integrations')

-- Context state
M.state = {
  active = false,
  trackers = {},
  events = {},
  last_context = nil
}

-- Setup context tracking
function M.setup()
  utils.logger.info('Setting up context tracking')
  
  -- Initialize trackers if enabled
  if config.get('context.track_cursor') then
    cursor.setup()
    M.state.trackers.cursor = cursor
  end
  
  if config.get('context.track_buffers') then
    buffer.setup()
    M.state.trackers.buffer = buffer
  end
  
  if config.get('context.track_activity') then
    activity.setup()
    M.state.trackers.activity = activity
  end
  
  if config.get('context.track_flow') then
    flow.setup()
    M.state.trackers.flow = flow
  end
  
  -- Setup event handlers
  M.setup_events()
end

-- Start context tracking
function M.start()
  if M.state.active then
    return
  end
  
  utils.logger.info('Starting context tracking')
  
  -- Start all trackers
  for name, tracker in pairs(M.state.trackers) do
    if tracker.start then
      tracker.start()
      utils.logger.debug('Started tracker: ' .. name)
    end
  end
  
  M.state.active = true
  
  -- Publish startup event
  M.publish_event({
    type = 'context_start',
    timestamp = utils.get_timestamp(),
    session_id = require('pulsedev').get_session_id()
  })
end

-- Stop context tracking
function M.stop()
  if not M.state.active then
    return
  end
  
  utils.logger.info('Stopping context tracking')
  
  -- Stop all trackers
  for name, tracker in pairs(M.state.trackers) do
    if tracker.stop then
      tracker.stop()
      utils.logger.debug('Stopped tracker: ' .. name)
    end
  end
  
  M.state.active = false
  
  -- Publish shutdown event
  M.publish_event({
    type = 'context_stop',
    timestamp = utils.get_timestamp(),
    session_id = require('pulsedev').get_session_id()
  })
end

-- Setup event handlers
function M.setup_events()
  -- Create event handlers group
  local group = vim.api.nvim_create_augroup('PulseDevContext', { clear = true })
  
  -- Global event handlers
  vim.api.nvim_create_autocmd('VimEnter', {
    group = group,
    callback = function()
      M.publish_event({
        type = 'vim_enter',
        timestamp = utils.get_timestamp(),
        session_id = require('pulsedev').get_session_id()
      })
    end
  })
  
  vim.api.nvim_create_autocmd('VimLeave', {
    group = group,
    callback = function()
      M.publish_event({
        type = 'vim_leave',
        timestamp = utils.get_timestamp(),
        session_id = require('pulsedev').get_session_id()
      })
    end
  })
  
  vim.api.nvim_create_autocmd('FocusGained', {
    group = group,
    callback = function()
      M.publish_event({
        type = 'focus_gained',
        timestamp = utils.get_timestamp(),
        session_id = require('pulsedev').get_session_id()
      })
    end
  })
  
  vim.api.nvim_create_autocmd('FocusLost', {
    group = group,
    callback = function()
      M.publish_event({
        type = 'focus_lost',
        timestamp = utils.get_timestamp(),
        session_id = require('pulsedev').get_session_id()
      })
    end
  })
end

-- Publish context event
function M.publish_event(event)
  if not M.state.active then
    return
  end
  
  -- Add common fields
  event.source = 'neovim'
  event.plugin_version = '1.0.0'
  
  -- Store in local buffer
  table.insert(M.state.events, event)
  
  -- Keep only last 100 events
  if #M.state.events > 100 then
    table.remove(M.state.events, 1)
  end
  
  -- Publish to integrations
  integrations.publish('pulse:context', event)
  
  utils.logger.debug('Published context event: ' .. event.type)
end

-- Get current context
function M.get_current_context()
  local context = {
    timestamp = utils.get_timestamp(),
    session_id = require('pulsedev').get_session_id(),
    active = M.state.active,
    trackers = {}
  }
  
  -- Get context from each tracker
  for name, tracker in pairs(M.state.trackers) do
    if tracker.get_context then
      context.trackers[name] = tracker.get_context()
    end
  end
  
  return context
end

-- Get recent events
function M.get_recent_events(count)
  count = count or 10
  local events = {}
  
  local start_idx = math.max(1, #M.state.events - count + 1)
  for i = start_idx, #M.state.events do
    table.insert(events, M.state.events[i])
  end
  
  return events
end

-- Get context summary
function M.get_summary()
  local summary = {
    active = M.state.active,
    trackers = {},
    event_count = #M.state.events,
    recent_events = M.get_recent_events(5)
  }
  
  -- Get summary from each tracker
  for name, tracker in pairs(M.state.trackers) do
    if tracker.get_summary then
      summary.trackers[name] = tracker.get_summary()
    else
      summary.trackers[name] = { active = true }
    end
  end
  
  return summary
end

-- Get status
function M.status()
  return {
    active = M.state.active,
    trackers = vim.tbl_keys(M.state.trackers),
    event_count = #M.state.events,
    last_event = M.state.events[#M.state.events]
  }
end

-- Health check
function M.health()
  local health = {
    ok = true,
    issues = {}
  }
  
  -- Check if any trackers are configured
  if vim.tbl_isempty(M.state.trackers) then
    health.ok = false
    table.insert(health.issues, 'No context trackers enabled')
  end
  
  -- Check tracker health
  for name, tracker in pairs(M.state.trackers) do
    if tracker.health then
      local tracker_health = tracker.health()
      if not tracker_health.ok then
        health.ok = false
        for _, issue in ipairs(tracker_health.issues) do
          table.insert(health.issues, name .. ': ' .. issue)
        end
      end
    end
  end
  
  return health
end

return M