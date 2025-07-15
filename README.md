# PulseDev+ Cognitive Context Mirror (CCM)

A developer productivity tool that captures and analyzes your development context in real-time.

## 🚀 Quick Start

### Local Development

1. **Start the backend services**:
   ```bash
   docker-compose up -d
   ```

2. **Install VSCode plugin dependencies**:
   ```bash
   cd apps/vscode-plugin
   npm install
   ```

3. **Build and install the VSCode plugin**:
   ```bash
   npm run compile
   # Then install the extension in VSCode by opening the folder in VSCode and pressing F5
   ```

### Kubernetes Deployment

1. **Build the API image**:
   ```bash
   npm run build:api
   ```

2. **Deploy to Kubernetes**:
   ```bash
   npm run k8s:deploy
   ```

## 📋 Features

### MVP (Current)
- **File System Monitoring**: Tracks file creation, modification, and deletion
- **Editor Activity**: Captures cursor movement, text changes, saves, and focus changes
- **Terminal Integration**: Monitors terminal sessions and commands
- **Git Integration**: Tracks git status changes and branch information
- **Real-time Storage**: PostgreSQL with TimescaleDB for time-series data
- **Fast Access Cache**: Redis for recent context events

### VSCode Plugin Commands
- `PulseDev: Start Context Capture` - Begin capturing context
- `PulseDev: Stop Context Capture` - Stop capturing context  
- `PulseDev: View Context Dashboard` - View recent context events
- `PulseDev: Wipe Context Data` - Clear all context data

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   VSCode Plugin │───▶│    CCM API      │───▶│   PostgreSQL    │
│                 │    │   (FastAPI)     │    │  (TimescaleDB)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       │
                       ┌─────────────────┐             │
                       │      Redis      │◀────────────┘
                       │    (Cache)      │
                       └─────────────────┘
```

## 📊 API Endpoints

- `GET /health` - Health check
- `POST /context/events` - Store context event
- `GET /context/recent?hours=1` - Get recent events
- `DELETE /context/wipe` - Clear context data
- `GET /context/stats` - Get context statistics

## 🔧 Configuration

VSCode plugin settings:
- `pulsedev.apiUrl`: CCM API endpoint (default: http://localhost:8000)
- `pulsedev.enableFileWatcher`: Enable file monitoring (default: true)
- `pulsedev.enableTerminalCapture`: Enable terminal monitoring (default: true)
- `pulsedev.sessionTimeout`: Session timeout in minutes (default: 1440)

## 🛠️ Development

### Project Structure
```
pulsedev-plus/
├── apps/
│   ├── vscode-plugin/      # VSCode extension
│   └── ccm-api/           # FastAPI backend
├── k8s/                   # Kubernetes manifests
├── docker-compose.yml     # Local development
└── package.json           # Workspace root
```

### Available Scripts
- `npm run dev` - Start both API and VSCode plugin in development mode
- `npm run build` - Build all components
- `npm run k8s:deploy` - Deploy to Kubernetes
- `npm run k8s:delete` - Remove from Kubernetes

## 🔐 Security

- Context events are stored with session isolation
- Redis cache has automatic expiry (24 hours)
- PostgreSQL with proper indexing for performance
- CORS configured for VSCode extension access

## 📈 Next Steps

1. **AI Prompt Generator**: Analyze context patterns to generate helpful prompts
2. **Flow Detection**: Monitor keystroke patterns and activity for flow state detection
3. **Auto Commit Writer**: Generate commit messages based on context
4. **Intent Drift Detection**: Use vector embeddings to detect goal deviation
5. **Merge Conflict Resolution**: AST-based conflict resolution with context

## 🤝 Contributing

This is currently a solo project for MVP development. Future collaboration welcome!

## 📄 License

MIT License - see LICENSE file for details.
