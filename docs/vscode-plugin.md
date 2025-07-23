# PulseDev+ VSCode Plugin

## Overview
The VSCode plugin brings PulseDev+ features directly into your IDE, with real-time session sync and gamification.

## Features
- Context tracking (file edits, commands, tests)
- AI prompt and stuck state detection
- Auto commit writer
- Flow orchestrator
- Gamification: XP, achievements, streaks, leaderboards
- Real-time session sync (only one active session at a time)
- Status bar indicator for active/inactive session

## Setup
- Install from the VSCode marketplace or load from `apps/vscode-plugin/`
- Configure API URL and settings in VSCode settings (`pulsedev.apiUrl`)

## Session Sync
- Calls `/api/v1/gamification/session/sync` on window focus/blur and at intervals
- Only tracks/notifies if active
- Status bar shows current session state

## Extensibility
- Add new features in `src/gamification.ts` and related files
- See `docs/session-sync.md` for session logic

## References
- [Session Sync & Active Session Logic](./session-sync.md)
- [VSCode Plugin Source](../apps/vscode-plugin/) 