# PulseDev+ Neovim Plugin

## Overview
The Neovim plugin brings PulseDev+ features to Vim users, with real-time session sync and gamification.

## Features
- Context tracking (cursor, buffer, activity, flow)
- AI prompt and stuck state detection
- Auto commit writer
- Flow orchestrator
- Gamification: XP, achievements, streaks, leaderboards
- Real-time session sync (only one active session at a time)
- Statusline indicator for active/inactive session

## Setup
- Install from `apps/nvim-plugin/` (see README for instructions)
- Configure API URL and settings in `config.lua`

## Session Sync
- Calls `/api/v1/gamification/session/sync` on FocusGained/FocusLost and at intervals
- Only tracks/notifies if active
- Statusline shows current session state

## Extensibility
- Add new features in `lua/pulsedev/`
- See `docs/session-sync.md` for session logic

## References
- [Session Sync & Active Session Logic](./session-sync.md)
- [Neovim Plugin Source](../apps/nvim-plugin/) 