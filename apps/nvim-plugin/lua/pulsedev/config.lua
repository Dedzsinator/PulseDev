-- lua/pulsedev/config.lua
-- Configuration management for PulseDev

local M = {}

-- Default configuration
local defaults = {
  enabled = true,
  debug = false,
  
  -- Redis configuration
  redis = {
    host = 'localhost',
    port = 6379,
    password = nil,
    database = 0
  },
  
  -- API configuration
  api = {
    endpoint = 'http://localhost:8000',
    timeout = 30,
    retry_count = 3
  },
  
  -- Context tracking
  context = {
    track_cursor = true,
    track_buffers = true,
    track_activity = true,
    track_flow = true,
    cursor_throttle = 2000, -- ms
    activity_timeout = 60000, -- ms
    flow_check_interval = 10000 -- ms
  },
  
  -- Auto-commit settings
  auto_commit = {
    enabled = true,
    on_test_pass = true,
    on_stable_context = true,
    message_template = '{action} | {context} | {timestamp}'
  },
  
  -- Flow detection
  flow = {
    enabled = true,
    keystroke_threshold = 5, -- keystrokes per second
    idle_threshold = 30, -- seconds
    context_switch_penalty = 0.2
  },
  
  -- UI settings
  ui = {
    notifications = true,
    statusline = true,
    virtual_text = false
  },
  
  -- Security settings
  security = {
    encrypt_context = true,
    auto_expire_hours = 24,
    redact_secrets = true
  }
}

-- Current configuration
local current_config = {}

-- Setup configuration
function M.setup(user_config)
  user_config = user_config or {}
  
  -- Deep merge user config with defaults
  current_config = vim.tbl_deep_extend('force', defaults, user_config)
  
  -- Validate configuration
  M.validate()
  
  -- Save to storage if needed
  M.save()
end

-- Get configuration value
function M.get(key)
  if key == nil then
    return current_config
  end
  
  local keys = vim.split(key, '.', { plain = true })
  local value = current_config
  
  for _, k in ipairs(keys) do
    if type(value) == 'table' and value[k] ~= nil then
      value = value[k]
    else
      return nil
    end
  end
  
  return value
end

-- Set configuration value
function M.set(key, value)
  local keys = vim.split(key, '.', { plain = true })
  local config = current_config
  
  for i = 1, #keys - 1 do
    local k = keys[i]
    if type(config[k]) ~= 'table' then
      config[k] = {}
    end
    config = config[k]
  end
  
  config[keys[#keys]] = value
  
  -- Save configuration
  M.save()
end

-- Get all configuration
function M.get_all()
  return vim.deepcopy(current_config)
end

-- Validate configuration
function M.validate()
  local errors = {}
  
  -- Validate Redis configuration
  if type(current_config.redis.host) ~= 'string' then
    table.insert(errors, 'redis.host must be a string')
  end
  
  if type(current_config.redis.port) ~= 'number' or 
     current_config.redis.port < 1 or 
     current_config.redis.port > 65535 then
    table.insert(errors, 'redis.port must be a valid port number')
  end
  
  -- Validate API configuration
  if type(current_config.api.endpoint) ~= 'string' then
    table.insert(errors, 'api.endpoint must be a string')
  end
  
  if type(current_config.api.timeout) ~= 'number' or 
     current_config.api.timeout < 1 then
    table.insert(errors, 'api.timeout must be a positive number')
  end
  
  -- Validate context configuration
  if type(current_config.context.cursor_throttle) ~= 'number' or 
     current_config.context.cursor_throttle < 100 then
    table.insert(errors, 'context.cursor_throttle must be >= 100ms')
  end
  
  -- Report errors
  if #errors > 0 then
    vim.notify('PulseDev configuration errors:\n' .. table.concat(errors, '\n'), 
               vim.log.levels.ERROR)
  end
  
  return #errors == 0
end

-- Save configuration to file
function M.save()
  local config_path = vim.fn.stdpath('data') .. '/pulsedev_config.json'
  local file = io.open(config_path, 'w')
  
  if file then
    file:write(vim.json.encode(current_config))
    file:close()
  end
end

-- Load configuration from file
function M.load()
  local config_path = vim.fn.stdpath('data') .. '/pulsedev_config.json'
  local file = io.open(config_path, 'r')
  
  if file then
    local content = file:read('*a')
    file:close()
    
    local ok, loaded_config = pcall(vim.json.decode, content)
    if ok and type(loaded_config) == 'table' then
      current_config = vim.tbl_deep_extend('force', defaults, loaded_config)
      return true
    end
  end
  
  return false
end

-- Reset to defaults
function M.reset()
  current_config = vim.deepcopy(defaults)
  M.save()
end

-- Get configuration schema for validation
function M.get_schema()
  return {
    type = 'object',
    properties = {
      enabled = { type = 'boolean' },
      debug = { type = 'boolean' },
      redis = {
        type = 'object',
        properties = {
          host = { type = 'string' },
          port = { type = 'integer', minimum = 1, maximum = 65535 },
          password = { type = 'string' },
          database = { type = 'integer', minimum = 0 }
        },
        required = { 'host', 'port' }
      },
      api = {
        type = 'object',
        properties = {
          endpoint = { type = 'string' },
          timeout = { type = 'number', minimum = 1 },
          retry_count = { type = 'integer', minimum = 0 }
        },
        required = { 'endpoint' }
      }
    }
  }
end

return M