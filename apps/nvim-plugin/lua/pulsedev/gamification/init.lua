---
--- PulseDev+ Nvim Gamification Integration
--- Tracks activities and syncs with gamification API
---

local M = {}
local api = require('pulsedev.integrations.api')
local utils = require('pulsedev.utils')
local logger = require('pulsedev.utils.logger')

-- Configuration
M.config = {
  enabled = true,
  show_notifications = true,
  show_statusline = true,
  api_url = 'http://localhost:8000',
  sync_interval = 30000, -- 30 seconds
}

-- State
M.session_id = nil
M.user_profile = nil
M.activity_buffer = {}
M.last_sync = 0
M.is_active_session = false

-- Activity tracking
local activity_types = {
  file_edit = 'file_edit',
  file_save = 'file_save',
  insert_mode = 'insert_mode',
  normal_mode = 'normal_mode',
  visual_mode = 'visual_mode',
  command_run = 'command_run',
  search = 'search',
  jump = 'jump',
  undo = 'undo',
  redo = 'redo',
}

-- XP sources mapping
local xp_sources = {
  file_edit = 'file_edit',
  file_save = 'file_edit',
  insert_mode = 'flow_state',
  vim_command = 'vim_mastery',
  search = 'navigation',
}

function M.setup(opts)
  M.config = vim.tbl_deep_extend('force', M.config, opts or {})
  
  if not M.config.enabled then
    return
  end
  
  M.session_id = M._generate_session_id()
  M._setup_autocmds()
  M._setup_timers()
  M._sync_session()
  
  logger.info("Gamification tracking initialized")
end

function M._generate_session_id()
  return 'nvim_' .. os.time() .. '_' .. math.random(100000, 999999)
end

function M._setup_autocmds()
  local group = vim.api.nvim_create_augroup('PulseDevGamification', { clear = true })
  
  -- Track file operations
  vim.api.nvim_create_autocmd({'TextChanged', 'TextChangedI'}, {
    group = group,
    callback = function()
      M._track_activity('file_edit', {
        file_path = vim.fn.expand('%:p'),
        line_count = vim.api.nvim_buf_line_count(0)
      })
    end
  })
  
  vim.api.nvim_create_autocmd('BufWritePost', {
    group = group,
    callback = function()
      M._track_activity('file_save', {
        file_path = vim.fn.expand('%:p')
      })
      M._award_xp('file_edit', {
        file_path = vim.fn.expand('%:p')
      })
    end
  })
  
  -- Track mode changes
  vim.api.nvim_create_autocmd('ModeChanged', {
    group = group,
    callback = function()
      local mode = vim.fn.mode()
      local activity_type = 'mode_change'
      
      if mode == 'i' then
        activity_type = 'insert_mode'
      elseif mode == 'n' then
        activity_type = 'normal_mode'
      elseif mode:match('[vV]') then
        activity_type = 'visual_mode'
      end
      
      M._track_activity(activity_type, { mode = mode })
    end
  })
  
  -- Track commands
  vim.api.nvim_create_autocmd('CmdlineEnter', {
    group = group,
    callback = function()
      M._track_activity('command_start', {})
    end
  })
  
  vim.api.nvim_create_autocmd('CmdlineLeave', {
    group = group,
    callback = function()
      local cmd = vim.fn.getcmdline()
      M._track_activity('command_run', { command = cmd })
      M._award_xp('vim_command', { command = cmd })
    end
  })
  
  -- Track searches
  vim.api.nvim_create_autocmd('SearchWrapped', {
    group = group,
    callback = function()
      M._track_activity('search', { pattern = vim.fn.getreg('/') })
    end
  })
end

function M._setup_timers()
  -- Flush activities periodically
  vim.fn.timer_start(M.config.sync_interval, function()
    M._flush_activities()
  end, { ['repeat'] = -1 })
  
  -- Sync session every 5 minutes
  vim.fn.timer_start(300000, function()
    M._sync_session()
  end, { ['repeat'] = -1 })
  
  -- Update statusline every 10 seconds
  if M.config.show_statusline then
    vim.fn.timer_start(10000, function()
      M._update_statusline()
    end, { ['repeat'] = -1 })
  end
end

function M._track_activity(activity_type, metadata)
  if not M.config.enabled or not M.is_active_session then
    return
  end
  
  local activity = {
    type = activity_type,
    session_id = M.session_id,
    timestamp = os.date('!%Y-%m-%dT%H:%M:%SZ'),
    metadata = metadata or {}
  }
  
  table.insert(M.activity_buffer, activity)
  
  -- Flush if buffer gets too large
  if #M.activity_buffer >= 20 then
    M._flush_activities()
  end
end

function M._award_xp(source, metadata)
  if not M.config.enabled or not M.is_active_session then
    return
  end
  
  local xp_source = xp_sources[source] or source
  
  api.request('POST', '/api/v1/gamification/xp/award', {
    session_id = M.session_id,
    source = xp_source,
    metadata = metadata or {}
  }, function(response)
    if response and response.success and response.xp_earned > 0 then
      M._show_xp_notification(response.xp_earned, xp_source)
      M._load_user_profile() -- Refresh profile
    end
  end)
end

function M._flush_activities()
  if #M.activity_buffer == 0 then
    return
  end
  
  local activities = vim.deepcopy(M.activity_buffer)
  M.activity_buffer = {}
  
  for _, activity in ipairs(activities) do
    api.request('POST', '/api/v1/gamification/activity/track', activity, function(response)
      if not response or not response.success then
        logger.error("Failed to track activity: " .. (activity.type or 'unknown'))
      end
    end)
  end
  
  M.last_sync = vim.loop.now()
end

function M._sync_session()
  api.request('POST', '/api/v1/gamification/session/sync', {
    session_id = M.session_id,
    platform = 'nvim'
  }, function(response)
    if response and response.success then
      M.is_active_session = response.sync_data.active_session == M.session_id
      
      if response.sync_data.user_profile then
        M.user_profile = response.sync_data.user_profile
        M._update_statusline()
      end
    end
  end)
end

function M._load_user_profile()
  api.request('GET', '/api/v1/gamification/profile/' .. M.session_id, nil, function(response)
    if response and response.success then
      M.user_profile = response.profile.profile
      M._update_statusline()
    end
  end)
end

function M._show_xp_notification(xp_earned, source)
  if not M.config.show_notifications then
    return
  end
  
  local message = string.format("+%d XP earned from %s!", xp_earned, source)
  vim.notify(message, vim.log.levels.INFO, {
    title = "PulseDev+",
    timeout = 3000,
  })
end

function M._update_statusline()
  if not M.config.show_statusline or not M.user_profile then
    return
  end
  
  -- Update global variable for statusline integration
  vim.g.pulsedev_gamification = {
    level = M.user_profile.level,
    xp = M.user_profile.total_xp,
    streak = M.user_profile.current_streak,
    active = M.is_active_session
  }
end

-- Public API
function M.show_dashboard()
  api.request('GET', '/api/v1/gamification/dashboard/' .. M.session_id, nil, function(response)
    if response and response.success then
      M._create_dashboard_buffer(response.dashboard)
    else
      vim.notify("Failed to load gamification dashboard", vim.log.levels.ERROR)
    end
  end)
end

function M.show_achievements()
  api.request('GET', '/api/v1/gamification/achievements/' .. M.session_id, nil, function(response)
    if response and response.success then
      M._create_achievements_buffer(response.achievements)
    else
      vim.notify("Failed to load achievements", vim.log.levels.ERROR)
    end
  end)
end

function M._create_dashboard_buffer(dashboard)
  local buf = vim.api.nvim_create_buf(false, true)
  local win = vim.api.nvim_open_win(buf, true, {
    relative = 'editor',
    width = math.floor(vim.o.columns * 0.8),
    height = math.floor(vim.o.lines * 0.8),
    col = math.floor(vim.o.columns * 0.1),
    row = math.floor(vim.o.lines * 0.1),
    style = 'minimal',
    border = 'rounded',
    title = ' PulseDev+ Gamification Dashboard ',
    title_pos = 'center'
  })
  
  local profile = dashboard.user_stats.profile
  local achievements = dashboard.achievements.unlocked or {}
  local leaderboard = dashboard.leaderboards.xp or {}
  
  local lines = {
    "╭─────────────────────────────────────────────────────────────╮",
    "│                    PulseDev+ Dashboard                      │",
    "╰─────────────────────────────────────────────────────────────╯",
    "",
    string.format("🎯 Level: %d", profile.level),
    string.format("⭐ Total XP: %d", profile.total_xp),
    string.format("🔥 Current Streak: %d days", profile.current_streak),
    string.format("🏆 Longest Streak: %d days", profile.longest_streak),
    string.format("📦 Total Commits: %d", profile.total_commits),
    string.format("🧘 Flow Time: %.1f hours", profile.total_flow_time / 60),
    "",
    "Recent Achievements:",
    "─────────────────────",
  }
  
  for i, achievement in ipairs(vim.list_slice(achievements, 1, 5)) do
    table.insert(lines, string.format("%s %s - %s", achievement.icon, achievement.name, achievement.description))
  end
  
  table.insert(lines, "")
  table.insert(lines, "Weekly Leaderboard:")
  table.insert(lines, "─────────────────────")
  
  for i, user in ipairs(vim.list_slice(leaderboard, 1, 5)) do
    table.insert(lines, string.format("#%d %s (Lv.%d) - %d XP", i, user.username, user.level, user.value))
  end
  
  table.insert(lines, "")
  table.insert(lines, "Press 'q' to close, 'a' for achievements")
  
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, lines)
  vim.api.nvim_buf_set_option(buf, 'modifiable', false)
  vim.api.nvim_buf_set_option(buf, 'filetype', 'pulsedev-dashboard')
  
  -- Set keymaps
  local opts = { noremap = true, silent = true, buffer = buf }
  vim.keymap.set('n', 'q', '<cmd>close<cr>', opts)
  vim.keymap.set('n', 'a', function() 
    vim.api.nvim_win_close(win, true)
    M.show_achievements() 
  end, opts)
end

function M._create_achievements_buffer(achievements)
  local buf = vim.api.nvim_create_buf(false, true)
  local win = vim.api.nvim_open_win(buf, true, {
    relative = 'editor',
    width = math.floor(vim.o.columns * 0.8),
    height = math.floor(vim.o.lines * 0.8),
    col = math.floor(vim.o.columns * 0.1),
    row = math.floor(vim.o.lines * 0.1),
    style = 'minimal',
    border = 'rounded',
    title = ' Achievements ',
    title_pos = 'center'
  })
  
  local lines = {
    "╭─────────────────────────────────────────────────────────────╮",
    "│                       Achievements                          │",
    "╰─────────────────────────────────────────────────────────────╯",
    "",
    "Unlocked Achievements:",
    "─────────────────────",
  }
  
  for _, achievement in ipairs(achievements.unlocked or {}) do
    table.insert(lines, string.format("%s %s", achievement.icon, achievement.name))
    table.insert(lines, string.format("    %s (+%d XP)", achievement.description, achievement.xp_reward))
    table.insert(lines, string.format("    Unlocked: %s", achievement.unlocked_at:sub(1, 10)))
    table.insert(lines, "")
  end
  
  table.insert(lines, "Available Achievements:")
  table.insert(lines, "─────────────────────")
  
  local unlocked_ids = {}
  for _, achievement in ipairs(achievements.unlocked or {}) do
    unlocked_ids[achievement.id] = true
  end
  
  for _, achievement in ipairs(achievements.available or {}) do
    if not unlocked_ids[achievement.id] then
      table.insert(lines, string.format("🔒 %s", achievement.name))
      table.insert(lines, string.format("    %s (+%d XP)", achievement.description, achievement.xp_reward))
      table.insert(lines, "")
    end
  end
  
  table.insert(lines, "Press 'q' to close")
  
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, lines)
  vim.api.nvim_buf_set_option(buf, 'modifiable', false)
  vim.api.nvim_buf_set_option(buf, 'filetype', 'pulsedev-achievements')
  
  -- Set keymaps
  local opts = { noremap = true, silent = true, buffer = buf }
  vim.keymap.set('n', 'q', '<cmd>close<cr>', opts)
end

-- Get statusline component
function M.statusline_component()
  if not M.user_profile or not M.is_active_session then
    return ""
  end
  
  return string.format("🎯L%d ⭐%d 🔥%d", 
    M.user_profile.level, 
    M.user_profile.total_xp, 
    M.user_profile.current_streak)
end

return M