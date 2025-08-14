# 🚀 PulseDev+ Fixed Startup Guide

## Issues Fixed:

1. **Python 3.13 compatibility** - Added fallbacks for scikit-learn compilation issues
2. **Import errors** - Fixed relative import issues in API routes
3. **ML dependencies** - Made AI/ML features optional to avoid blocking startup

## Quick Start Options:

### Option 1: Minimal Backend (Recommended for Testing)
```bash
# Starts core features without ML dependencies
./scripts/minimal-backend-start.sh
```

### Option 2: Full Backend (With ML Features)  
```bash
# Installs everything including AI training
./scripts/quick-test-setup.sh
```

### Option 3: Manual Setup
```bash
cd apps/ccm-api
python -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Core dependencies
pip install fastapi uvicorn[standard] pydantic sqlalchemy asyncpg redis

# Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## What's Fixed:

✅ **Import Errors**: Changed relative imports to absolute imports  
✅ **Python 3.13 Issues**: Added fallbacks for scikit-learn compilation  
✅ **Optional ML**: Backend works without AI/ML dependencies  
✅ **Error Handling**: Graceful degradation when packages missing  

## Testing Steps:

1. **Test imports first**:
   ```bash
   python scripts/test-backend.py
   ```

2. **Start minimal backend**:
   ```bash
   ./scripts/minimal-backend-start.sh
   ```

3. **Verify it's working**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/docs
   ```

4. **Set up Neovim plugin** (copy from script output)

## Neovim Plugin Setup:

Add to your lazy.nvim config:
```lua
return {
  {
    "PulseDev+",
    dir = "/home/deginandor/Documents/Programming/PulseDev/apps/nvim-plugin",
    name = "pulsedev", 
    config = function()
      require("pulsedev").setup({
        enabled = true,
        debug = true,
        api = { endpoint = "http://localhost:8000" },
      })
    end,
    dependencies = { "nvim-lua/plenary.nvim" },
    event = "VimEnter",
  }
}
```

## Expected Results:

- ✅ Backend starts without compilation errors
- ✅ Health check works: `curl http://localhost:8000/health` 
- ✅ API docs available: http://localhost:8000/docs
- ✅ Core context tracking enabled
- ✅ Neovim plugin connects successfully
- ⚠️  AI training optional (enable later with ML packages)

The system now has graceful fallbacks and should work even with Python 3.13 and missing ML dependencies!
