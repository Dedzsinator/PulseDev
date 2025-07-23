# PulseDev+ Tauri Desktop App

## Overview
The Tauri desktop app provides a full-featured, cross-platform PulseDev+ experience with native integrations, real-time session sync, and a modern UI.

## Features
- Cognitive Context Mirror
- AI Prompt Generator
- Auto Commit Writer
- Flow Orchestrator
- Energy Scorer
- Merge Conflict Resolver
- Intent Drift Detector
- Auto Branch Suggestion
- Pulse Points Engine (Gamification)
- Native integrations: notifications, file system, DND, tray, window management
- Real-time session sync (only one active session at a time)

## Architecture
- **Frontend:** React (see `src/components/CCMFeatures.tsx`)
- **Backend:** Rust (see `src-tauri/src/`)
- **Session Sync:** Calls `/api/v1/gamification/session/sync` on focus/blur and at intervals
- **Native Integrations:** Tauri commands for notifications, file system, DND, tray, window

## Configuration
- API URL, session ID, and other settings can be configured via environment or UI
- See `tauri.conf.json` for window and build settings

## Extensibility
- Add new Tauri commands in `src-tauri/src/commands/`
- Add new React features in `src/components/`
- See `docs/session-sync.md` for session logic

## Usage
- Run with `npm run tauri dev` or build with `tauri build`
- Only the active session will track and notify

## References
- [Session Sync & Active Session Logic](./session-sync.md)
- [Main Features](../src/components/CCMFeatures.tsx)
- [Tauri Backend](../src-tauri/src/) 