# PulseDev+ AI Training System - Quick Reference

## 🚀 Quick Start

### Option 1: Automated Startup (Recommended)
```bash
# Run the complete startup script
./scripts/start-all-services.sh
```

### Option 2: Manual Step-by-Step

#### 1. **Setup Backend Environment:**
```bash
cd apps/ccm-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. **Start Backend API:**
```bash
# From apps/ccm-api with venv activated
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. **Start Frontend (New Terminal):**
```bash
# From project root
npm install  # First time only
npm run dev
```

#### 4. **Access Applications:**
- **Frontend App**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **AI Training Dashboard**: http://localhost:5173 → Navigate to AI section

#### 5. **Test AI Training:**
```bash
# Check AI status
curl http://localhost:8000/api/v1/ai/training/status

# Start training
curl -X POST http://localhost:8000/api/v1/ai/training/start

# Check dataset status
curl http://localhost:8000/api/v1/ai/datasets/status
```

## 🎯 COMPLETE STARTUP COMMANDS

### Single Command Startup (Easiest)
```bash
# Run everything with one script
./scripts/start-all-services.sh
```

### Manual Commands (Step by Step)

#### Terminal 1 - Backend API:
```bash
cd apps/ccm-api
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 - Frontend:
```bash
# From project root
npm run dev
```

#### Terminal 3 - Test Everything:
```bash
# Wait 30 seconds after starting services, then run:
./scripts/test-services.sh
```

### Expected Output After Starting
- Backend logs show: "Uvicorn running on http://0.0.0.0:8000"
- Frontend shows: "Local: http://localhost:5173"
- Test script shows all green ✅ checkmarks

### Key URLs After Startup
- **Main Application**: http://localhost:5173
- **API Server**: http://localhost:8000  
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📊 What's New

### ✅ Completed Features

- **External Dataset Integration**: Kaggle & Hugging Face
- **4 ML Models**: Stuck detection, flow prediction, productivity, anomaly detection  
- **Real Training Pipeline**: Cross-validation, model persistence
- **React Dashboard**: Complete frontend for monitoring
- **API Endpoints**: Full REST API for management
- **Setup Scripts**: Automated environment configuration

### 🧠 AI Models

| Model | Algorithm | Purpose | Expected Accuracy |
|-------|-----------|---------|------------------|
| Stuck Classifier | GradientBoosting | Detect stuck developers | 85%+ |
| Flow Predictor | GradientBoosting | Predict flow states | 82%+ |
| Productivity Predictor | RandomForest | Assess productivity | 79%+ |
| Anomaly Detector | IsolationForest | Detect unusual patterns | N/A |

### 🔌 API Endpoints

- `GET /api/v1/ai/training/status` - Training status
- `POST /api/v1/ai/training/start` - Start training
- `GET /api/v1/ai/datasets/status` - Dataset availability
- `POST /api/v1/ai/datasets/download` - Download external data
- `GET /api/v1/ai/models/metrics` - Model performance

## 🛠️ Development Notes

- Models are saved in `apps/ccm-api/models/`
- Datasets cached in `apps/ccm-api/datasets/`
- Processed data in `apps/ccm-api/processed_datasets/`
- Uses synthetic data fallback when external APIs unavailable
- Full TypeScript React dashboard with real-time updates

## 🔧 Configuration

Optional API keys for enhanced datasets:

### Kaggle (Optional)
```bash
# Create ~/.kaggle/kaggle.json with:
{
  "username": "your-username",
  "key": "your-api-key"
}
```

### Hugging Face (Optional)
```bash
huggingface-cli login
```

Without these, the system uses synthetic data and public datasets.

---

**Status**: ✅ **COMPLETE** - All AI training infrastructure is implemented and ready to use.

## 🔍 Testing & Verification

### Test the Complete System

1. **Open your browser and navigate to:** http://localhost:5173

2. **Verify Frontend is Working:**
   - You should see the PulseDev+ main interface
   - Navigate to the AI Training Dashboard section
   - Check that the dashboard loads without errors

3. **Test API Endpoints:**
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # AI training status
   curl http://localhost:8000/api/v1/ai/training/status
   
   # Dataset status
   curl http://localhost:8000/api/v1/ai/datasets/status
   ```

4. **Test AI Training Flow:**
   - In the AI Dashboard, click "Download Datasets" 
   - Then click "Start Training"
   - Monitor the training progress
   - Check model metrics after training completes

### Expected Behavior

- **Backend API** should respond at http://localhost:8000
- **Frontend App** should load at http://localhost:5173  
- **AI Training Status** should show models and training state
- **Dataset Download** should work (with synthetic data if no API keys)
- **Model Training** should complete within 2-5 minutes
- **Training Metrics** should show accuracy scores

## 🚨 Troubleshooting

### Common Issues & Solutions

#### 1. **"No module named 'sklearn'" Error**
```bash
cd apps/ccm-api
source venv/bin/activate
pip install scikit-learn pandas numpy joblib
```

#### 2. **"Port 8000 already in use" Error** 
```bash
# Kill any existing processes on port 8000
sudo lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn main:app --port 8001
```

#### 3. **Frontend Won't Start**
```bash
# Clear npm cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
npm run dev
```

#### 4. **"Kaggle not configured" Warnings**
This is normal! The system uses synthetic data as fallback.
To fix (optional):
```bash
mkdir -p ~/.kaggle
echo '{"username":"your-username","key":"your-key"}' > ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json
```

#### 5. **AI Training Fails**
```bash
# Check if models directory exists
mkdir -p apps/ccm-api/models

# Ensure all ML packages are installed
cd apps/ccm-api && source venv/bin/activate
pip install -r requirements.txt
```

#### 6. **Database Connection Errors**
The system can run without a database for AI training testing:
```bash
# Set environment variable to skip database
export SKIP_DB=true
```

### Verification Commands

```bash
# Check if all services are running
curl http://localhost:8000/health        # Backend health
curl http://localhost:5173               # Frontend check
curl http://localhost:8000/docs          # API documentation

# Check AI system specifically  
curl http://localhost:8000/api/v1/ai/training/status
curl -X POST http://localhost:8000/api/v1/ai/datasets/download
```

### Service Ports Summary

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| Frontend | 5173 | http://localhost:5173 | Main web application |
| Backend API | 8000 | http://localhost:8000 | REST API server |
| API Docs | 8000 | http://localhost:8000/docs | Interactive API documentation |
| PostgreSQL | 5432 | localhost:5432 | Database (optional) |
| Redis | 6379 | localhost:6379 | Cache (optional) |
