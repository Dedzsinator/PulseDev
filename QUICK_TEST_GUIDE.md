# 🚀 PulseDev+ Quick Test Guide

## Backend Startup (Required First)

### Start the Backend API Server:
```bash
# 1. Navigate to project root
cd /path/to/PulseDev

# 2. Setup backend environment
cd apps/ccm-api
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 3. Start the API server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Server will be available at: http://localhost:8000
```

### Verify Backend is Running:
```bash
# Test the health endpoint
curl http://localhost:8000/health

# Test AI training endpoints  
curl http://localhost:8000/api/v1/ai/training/status

# Expected: Both should return JSON responses
```

---

## Neovim Plugin Setup (lazy.nvim)

### 1. Add Plugin to Your Neovim Config:

**File: `~/.config/nvim/lua/plugins/pulsedev.lua`**
```lua
return {
  {
    "PulseDev+",
    dir = "/home/deginandor/Documents/Programming/PulseDev/apps/nvim-plugin", -- Update this path!
    name = "pulsedev",
    config = function()
      require("pulsedev").setup({
        enabled = true,
        debug = true,
        api = {
          endpoint = "http://localhost:8000",
        },
      })
    end,
    dependencies = { "nvim-lua/plenary.nvim" },
    event = "VimEnter",
  }
}
```

### 2. Alternative: Direct Installation
```lua
-- Add to your init.lua
vim.opt.rtp:prepend("/home/deginandor/Documents/Programming/PulseDev/apps/nvim-plugin")

require("pulsedev").setup({
  enabled = true,
  debug = true,
  api = { endpoint = "http://localhost:8000" },
})
```

---

## Testing the Integration

### 1. Start Backend
```bash
cd apps/ccm-api
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Open Neovim
```bash
nvim
```

### 3. Test Plugin Commands
```vim
:PulseDev status           " Should show 'enabled: true'
:PulseDev start            " Start tracking
:PulseDev metrics          " Show productivity metrics
:PulseDev dashboard        " Open web dashboard
```

### 4. Verify Everything Works
- ✅ Backend responds: `curl http://localhost:8000/health`
- ✅ Plugin loads: `:PulseDev status` works
- ✅ Tracking active: `:PulseDev start` succeeds
- ✅ Data flows: Activity appears in logs

---

## Expected Results

### Backend Ready:
- ✅ API server running on port 8000
- ✅ Health endpoint returns 200 OK
- ✅ AI training status accessible
- ✅ No errors in terminal

### Plugin Working:
- ✅ `:PulseDev status` shows enabled
- ✅ Commands respond without errors
- ✅ Activity tracking starts successfully
- ✅ Debug logs show connection to backend

### Full Integration:
- ✅ Coding activity tracked in real-time
- ✅ Context synced to backend API
- ✅ AI models receive training data
- ✅ Productivity metrics available

---

## Troubleshooting

### Backend Issues:
```bash
# Check if port 8000 is free
lsof -ti:8000

# Install missing packages
pip install -r requirements.txt

# Check for Python errors
python -c "import fastapi, uvicorn"
```

### Plugin Issues:
```vim
" Check plugin loaded
:echo &rtp | grep pulsedev

" View error messages
:messages

" Enable debug mode
:lua require("pulsedev").setup({debug = true})
```

### Connection Issues:
```bash
# Test API manually
curl -v http://localhost:8000/health

# Check firewall/networking
telnet localhost 8000
```

---

## Next Steps After Setup

1. **Code normally** - Plugin tracks your activity
2. **Check metrics** - Use `:PulseDev metrics` 
3. **View dashboard** - Open http://localhost:8000/docs
4. **Train AI models** - Your coding patterns improve the AI
5. **Use smart features** - Auto-commits, flow detection, gamification

**Your PulseDev+ system is now ready for testing!** 🎯
