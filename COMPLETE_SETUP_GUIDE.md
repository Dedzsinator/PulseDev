# PulseDev+ Complete Setup & Testing Guide

## 🚀 Backend Setup & Startup

### 1. Start Backend Services

#### Option 1: Quick Start (Automated)
```bash
# From project root
./scripts/start-all-services.sh
```

#### Option 2: Manual Backend Setup
```bash
# 1. Setup Python environment
cd apps/ccm-api
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or .\venv\Scripts\activate  # Windows

# 2. Install dependencies  
pip install -r requirements.txt

# 3. Start the API server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Option 3: With Database (Full Setup)
```bash
# 1. Start databases with Docker
docker-compose up -d postgres redis

# 2. Start API (same as above)
cd apps/ccm-api
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Verify Backend is Running

```bash
# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/ai/training/status

# Or use the test script
./scripts/test-services.sh
```

✅ **Backend Ready When**: 
- API responds at http://localhost:8000
- Health check returns 200 OK
- AI training endpoints are accessible

---

## 🔧 Neovim Plugin Setup (Lazy.nvim Compatible)

### 1. Plugin Installation

Add this to your Neovim configuration:

#### For lazy.nvim users:
```lua
-- ~/.config/nvim/lua/plugins/pulsedev.lua
return {
  {
    "PulseDev+",
    dir = "/path/to/PulseDev/apps/nvim-plugin", -- Update this path
    name = "pulsedev",
    config = function()
      require("pulsedev").setup({
        enabled = true,
        debug = true, -- Enable for testing
        api = {
          endpoint = "http://localhost:8000",
          timeout = 30,
        },
        redis = {
          host = "localhost",
          port = 6379,
        },
        context = {
          track_cursor = true,
          track_buffers = true,
          track_activity = true,
          track_flow = true,
        },
        auto_commit = {
          enabled = true,
          on_test_pass = true,
          on_stable_context = true,
        },
        gamification = {
          enabled = true,
          show_level = true,
          show_xp = true,
        },
      })
    end,
    dependencies = {
      "nvim-lua/plenary.nvim",
    },
    event = "VimEnter",
  }
}
```

#### Alternative Installation Methods:

**Direct Local Plugin:**
```lua
-- Add to your init.lua or plugins config
vim.opt.rtp:prepend("/path/to/PulseDev/apps/nvim-plugin")
require("pulsedev").setup({
  -- config options here
})
```

**Git Clone Method:**
```bash
# Clone to Neovim plugins directory
git clone /path/to/PulseDev/apps/nvim-plugin ~/.config/nvim/pack/plugins/start/pulsedev

# Or for lazy.nvim managed plugins
git clone /path/to/PulseDev/apps/nvim-plugin ~/.local/share/nvim/lazy/pulsedev
```

### 2. Plugin Configuration

Create a configuration file:

```lua
-- ~/.config/nvim/lua/config/pulsedev.lua
local M = {}

function M.setup()
  require("pulsedev").setup({
    enabled = true,
    debug = true, -- Enable for initial testing
    
    -- API Configuration
    api = {
      endpoint = "http://localhost:8000",
      timeout = 30,
      retry_count = 3,
    },
    
    -- Redis Configuration (optional)
    redis = {
      host = "localhost", 
      port = 6379,
      password = nil,
    },
    
    -- Context Tracking
    context = {
      track_cursor = true,
      track_buffers = true, 
      track_activity = true,
      track_flow = true,
      cursor_throttle = 2000,
      activity_timeout = 60000,
    },
    
    -- Auto-commit Features
    auto_commit = {
      enabled = true,
      on_test_pass = true,
      on_stable_context = true,
      message_template = "PulseDev: {action} | {context}",
    },
    
    -- Flow State Detection
    flow = {
      enabled = true,
      keystroke_threshold = 5,
      idle_threshold = 30,
      context_switch_penalty = 0.2,
    },
    
    -- Gamification
    gamification = {
      enabled = true,
      show_level = true,
      show_xp = true,
      show_achievements = true,
      notifications = true,
    },
    
    -- UI Settings
    ui = {
      show_status = true,
      show_metrics = true,
      update_interval = 5000,
    },
  })
end

return M
```

### 3. Plugin Commands & Usage

Once installed, PulseDev provides these commands:

```vim
:PulseDev status           " Show plugin status
:PulseDev start            " Start tracking
:PulseDev stop             " Stop tracking  
:PulseDev dashboard        " Open dashboard
:PulseDev commit           " Trigger smart commit
:PulseDev sync             " Sync context to server
:PulseDev metrics          " Show productivity metrics
:PulseDev achievements     " Show achievements
:PulseDev flow             " Check flow state
```

### 4. Testing the Plugin

After installation:

1. **Restart Neovim**
2. **Check plugin loaded**: `:PulseDev status`
3. **Start tracking**: `:PulseDev start`
4. **Test connection**: `:PulseDev sync`
5. **View metrics**: `:PulseDev metrics`

---

## 🧪 Complete Testing Workflow

### Step 1: Start Backend
```bash
cd /path/to/PulseDev
./scripts/start-all-services.sh
```

### Step 2: Verify Backend
```bash
# Should return 200 OK
curl http://localhost:8000/health

# Test AI endpoints
curl http://localhost:8000/api/v1/ai/training/status
```

### Step 3: Install & Configure Neovim Plugin
```bash
# Update this path in your config
echo "Update plugin path to: $(pwd)/apps/nvim-plugin"
```

### Step 4: Test Plugin Integration
1. Open Neovim
2. Run `:PulseDev status` - should show "enabled"
3. Run `:PulseDev start` - begins tracking
4. Edit some code - plugin tracks activity
5. Run `:PulseDev metrics` - view productivity data
6. Run `:PulseDev dashboard` - see web dashboard

### Step 5: Verify Full Integration
1. **Code Activity**: Edit files, see tracking in logs
2. **Context Sync**: Changes sync to backend API
3. **Flow Detection**: Plugin detects coding flow states  
4. **Auto-commits**: Smart commits on stable states
5. **Gamification**: XP points and achievements
6. **AI Training**: Your activity trains the AI models

---

## 🎯 Expected Results

### Backend Ready Signs:
- ✅ API server running on port 8000
- ✅ Health endpoint returns OK  
- ✅ AI training endpoints accessible
- ✅ Web dashboard loads at http://localhost:5173

### Plugin Working Signs:
- ✅ `:PulseDev status` shows "enabled: true"
- ✅ Activity tracking logs appear
- ✅ Context syncs to backend successfully
- ✅ Flow state detection works
- ✅ Gamification features active

### Full Integration Success:
- ✅ Neovim activity appears in web dashboard
- ✅ AI models train from your coding patterns
- ✅ Smart commits work automatically
- ✅ Productivity metrics track over time
- ✅ Real-time flow state feedback

---

## 🚨 Troubleshooting

### Plugin Not Loading:
```bash
# Check plugin path
:echo &rtp | grep pulsedev

# Check for errors
:messages

# Enable debug mode
:lua require("pulsedev").setup({debug = true})
```

### Connection Issues:
```bash
# Test API manually
curl http://localhost:8000/health

# Check plugin config
:PulseDev status
```

### Dependencies Missing:
```bash
# Install plenary.nvim for lazy.nvim
# Or add to your plugin manager
```

---

**Your PulseDev+ system is now ready for complete testing with Neovim integration!** 🚀
