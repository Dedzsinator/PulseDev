# PulseDev+ Cross-Platform Session Sync

## Overview
PulseDev+ ensures that only one platform (VSCode, Neovim, browser extension, Tauri app) is the "active" session at a time. Only the active session tracks, notifies, and interacts with the user. All others go idle.

## How It Works
- Each client periodically and on focus/blur calls `/api/v1/gamification/session/sync` with its session ID and platform.
- The backend marks that session as active and deactivates all others for the user.
- The backend returns which session is currently active.
- Each client checks if it is the active session and only tracks/notifies if so.
- UI indicators and notifications inform the user of session state changes.

## API
### Endpoint
`POST /api/v1/gamification/session/sync`

#### Request
```
{
  "session_id": "string",
  "platform": "vscode" | "nvim" | "browser" | "tauri"
}
```

#### Response
```
{
  "success": true,
  "sync_data": {
    "active_session": "string",
    "platform": "string",
    "user_profile": { ... },
    "session_stats": { ... }
  }
}
```

## Client Implementation
- **Sync on focus/blur and at intervals.**
- **Store `isActiveSession` state.**
- **Only track/notify if active.**
- **Show UI indicator (badge, statusline, banner, etc).**
- **Show notification when session state changes.**

## Example: Tauri App
- See `src/components/CCMFeatures.tsx` for React implementation.

## Example: VSCode Plugin
- See `apps/vscode-plugin/src/gamification.ts` for TypeScript implementation.

## Example: Neovim Plugin
- See `apps/nvim-plugin/lua/pulsedev/gamification/init.lua` and `ui/statusline.lua` for Lua implementation.

## Example: Browser Extension
- See `apps/browser-extension/src/gamification-tracker.ts` for TypeScript implementation.

## Database
- See `active_sessions` table in `apps/ccm-api/database/schema.sql`.

## Best Practices
- Always call sync on focus/blur.
- Respect the `isActiveSession` flag.
- Provide clear UI and notifications for session state. 