# PulseDev+ Browser Extension

## Overview
The browser extension brings PulseDev+ features to your web workflow, with real-time session sync and gamification.

## Features
- Tab, navigation, and dev site tracking
- AI prompt and stuck state detection
- Auto commit writer
- Flow orchestrator
- Gamification: XP, achievements, streaks, leaderboards
- Real-time session sync (only one active session at a time)
- Badge indicator for active/inactive session

## Setup
- Load from `apps/browser-extension/` in your browser (see README for instructions)
- Configure API URL and settings via environment or popup

## Session Sync
- Calls `/api/v1/gamification/session/sync` on window focus/blur and at intervals
- Only tracks/notifies if active
- Badge shows current session state

## Extensibility
- Add new features in `src/gamification-tracker.ts`
- See `docs/session-sync.md` for session logic

## References
- [Session Sync & Active Session Logic](./session-sync.md)
- [Browser Extension Source](../apps/browser-extension/) 