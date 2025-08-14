# PulseDev+ Neovim Plugin Setup Guide

## 🚀 Complete Setup with Kubernetes Backend

### Step 1: Deploy the Backend (if not already done)

```bash
cd /path/to/PulseDev
bash scripts/deploy-k8s.sh
```

### Step 2: Port Forward the API Service

The Kubernetes service needs to be accessible from your local machine. Run this in a separate terminal:

```bash
kubectl port-forward svc/ccm-api-service 8000:8000 -n pulsedev-ccm
```

Keep this running while using the Neovim plugin.

### Step 3: Install the Neovim Plugin

#### For lazy.nvim users:

Create or update `~/.config/nvim/lua/plugins/pulsedev.lua`:

```lua
-- PulseDev+ Plugin Configuration
return {
  {
    "PulseDev+",
    dir = "/home/deginandor/Documents/Programming/PulseDev/apps/nvim-plugin",
    name = "pulsedev",
    config = function()
      require("pulsedev").setup({
        -- Core settings
        enabled = true,
        debug = true,
        
        -- Backend API connection (via port-forward)
        api = {
          endpoint = "http://localhost:8000",
          timeout = 30,
          retry_count = 3,
        },
        
        -- Features
        auto_track = true,
        flow_detection = true,
        gamification = true,
        
        -- AI settings (using NVIDIA NIM)
        ai = {
          enabled = true,
          provider = "nvidia_nim",
        },
        
        -- Event tracking
        events = {
          code_change = true,
          file_access = true,
          test_run = true,
          build = true,
          debug = true,
        },
        
        -- UI settings
        notifications = true,
        status_line = true,
        
        -- Keymaps
        keymaps = {
          toggle = "<leader>pt",
          status = "<leader>ps",
          metrics = "<leader>pm",
          leaderboard = "<leader>pl",
        }
      })
    end,
    dependencies = { "nvim-lua/plenary.nvim" },
    event = "VimEnter",
  }
}
```

#### For packer.nvim users:

Add to your `~/.config/nvim/lua/plugins.lua`:

```lua
use {
  "PulseDev+",
  config = function()
    require("pulsedev").setup({
      -- Same configuration as above
    })
  end,
  requires = { "nvim-lua/plenary.nvim" }
}
```

### Step 4: Restart Neovim

After adding the plugin configuration, restart Neovim to load the plugin.

### Step 5: Test the Plugin

Run these commands in Neovim:

```vim
:PulseDev status    " Check connection status
:PulseDev start     " Start tracking
:PulseDev metrics   " View your metrics
:PulseDev help      " Show all commands
```

## 📊 Available Commands

### Core Commands
- `:PulseDev status` - Check backend connection and plugin status
- `:PulseDev start` - Start activity tracking
- `:PulseDev stop` - Stop activity tracking
- `:PulseDev toggle` - Toggle tracking on/off

### Metrics & Analytics
- `:PulseDev metrics` - Show current session metrics
- `:PulseDev flow` - Show flow state information
- `:PulseDev energy` - Show energy/focus score
- `:PulseDev daily` - Show daily statistics

### Gamification
- `:PulseDev points` - Show current points
- `:PulseDev leaderboard` - Show leaderboard (if multiplayer)
- `:PulseDev achievements` - Show earned achievements
- `:PulseDev streak` - Show coding streak

### AI Features (NVIDIA NIM powered)
- `:PulseDev suggest` - Get AI suggestions for current context
- `:PulseDev analyze` - Analyze current code/project
- `:PulseDev optimize` - Get optimization suggestions

### Settings & Debug
- `:PulseDev config` - Show current configuration
- `:PulseDev logs` - Show plugin logs
- `:PulseDev help` - Show all available commands

## 🔧 Configuration Options

```lua
require("pulsedev").setup({
  -- Backend connection
  api = {
    endpoint = "http://localhost:8000",  -- Your K8s port-forward
    timeout = 30,
    retry_count = 3,
    auth_token = nil,  -- Optional API token
  },
  
  -- Feature toggles
  auto_track = true,           -- Auto-start tracking when Neovim opens
  flow_detection = true,       -- Enable flow state detection
  gamification = true,         -- Enable points and achievements
  ai_suggestions = true,       -- Enable AI-powered suggestions
  
  -- Event tracking configuration
  events = {
    code_change = true,        -- Track when you edit code
    file_access = true,        -- Track file opens/closes
    test_run = true,          -- Track test execution
    build = true,             -- Track build events
    debug = true,             -- Track debug sessions
    git_operations = true,    -- Track git commits, branches
  },
  
  -- AI configuration
  ai = {
    enabled = true,
    provider = "nvidia_nim",
    auto_suggestions = false,  -- Don't auto-suggest (can be distracting)
    context_window = 1000,    -- Lines of context to send to AI
  },
  
  -- UI preferences
  notifications = {
    enabled = true,
    level = "info",           -- error, warn, info, debug
    achievements = true,      -- Notify on achievements
    flow_state = true,       -- Notify on flow state changes
  },
  
  status_line = {
    enabled = true,
    position = "right",       -- left, right, center
    format = "points: %p | flow: %f",
  },
  
  -- Keybinding customization
  keymaps = {
    toggle = "<leader>pt",
    status = "<leader>ps",
    metrics = "<leader>pm",
    leaderboard = "<leader>pl",
    ai_suggest = "<leader>pa",
  },
  
  -- Performance settings
  update_interval = 5,        -- Seconds between updates
  batch_size = 10,           -- Events to batch before sending
  offline_mode = false,      -- Enable offline tracking
})
```

## 🚀 Usage Workflow

### 1. Start Your Coding Session
```bash
# Terminal 1: Ensure K8s is running
kubectl get pods -n pulsedev-ccm

# Terminal 2: Port forward the API
kubectl port-forward svc/ccm-api-service 8000:8000 -n pulsedev-ccm

# Terminal 3: Start Neovim
nvim
```

### 2. In Neovim
```vim
:PulseDev status      " Verify connection
:PulseDev start       " Begin tracking
```

### 3. Code Normally
The plugin automatically tracks:
- File edits and saves
- Time spent in different files
- Flow state based on your activity patterns
- Git operations (commits, branch switches)
- Test runs and builds

### 4. Check Your Progress
```vim
:PulseDev metrics     " See real-time stats
:PulseDev flow        " Check if you're in flow
:PulseDev points      " See gamification progress
```

### 5. Get AI Help
```vim
:PulseDev suggest     " Get context-aware suggestions
:PulseDev analyze     " Analyze current code quality
```

## 🎯 Features You'll Get

### ✅ Automatic Tracking
- **Code Changes**: Every edit, save, and modification
- **File Navigation**: Which files you spend time in
- **Git Activity**: Commits, branches, merges
- **Build Events**: Test runs, compilation, debugging
- **Flow State**: When you're in the zone vs. when you're distracted

### ✅ Real-time Analytics
- **Energy Score**: How focused you are (0-100)
- **Flow Duration**: How long you've been in flow
- **Productivity Metrics**: Lines changed, files touched, commits made
- **Time Tracking**: Detailed breakdowns of where time is spent

### ✅ Gamification
- **Points System**: Earn points for various coding activities
- **Achievements**: Unlock badges for milestones
- **Streaks**: Daily coding streaks
- **Leaderboards**: Compete with team members (if configured)

### ✅ AI-Powered Insights (NVIDIA NIM)
- **Context-Aware Suggestions**: Based on current file and project
- **Code Quality Analysis**: Identify potential improvements
- **Productivity Tips**: Personalized recommendations
- **Pattern Recognition**: Learn your optimal coding times/conditions

### ✅ Team Integration
- **Shared Metrics**: Team productivity dashboards
- **Code Review Integration**: Track review participation
- **Collaboration Patterns**: See how you work with others

## 🛠️ Troubleshooting

### Plugin Not Loading
```vim
:messages           " Check for errors
:PulseDev logs     " Check plugin logs
```

### Connection Issues
```bash
# Check if port-forward is running
curl http://localhost:8000/health

# Check Kubernetes status
kubectl get pods -n pulsedev-ccm

# Restart port-forward
kubectl port-forward svc/ccm-api-service 8000:8000 -n pulsedev-ccm
```

### Debug Mode
Enable debug mode in your config:
```lua
debug = true,
```

Then check logs:
```vim
:PulseDev logs
```

## 🌟 Tips for Maximum Productivity

1. **Keep Port-Forward Running**: The plugin needs continuous connection to the backend
2. **Enable Flow Detection**: Let the system learn your productivity patterns  
3. **Use AI Suggestions Sparingly**: Don't let it interrupt your flow
4. **Check Metrics Regularly**: Use `:PulseDev metrics` to stay aware of your patterns
5. **Set Up Keybindings**: Quick access to commands improves adoption

Your PulseDev+ system is now ready to provide comprehensive insights into your coding habits and help optimize your development workflow! 🚀
