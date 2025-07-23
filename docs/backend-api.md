# PulseDev+ Backend API

## Overview
The backend API powers all PulseDev+ features, including context tracking, gamification, session sync, and integrations.

## Key Endpoints
- `/api/v1/gamification/session/sync` — Session sync for all platforms
- `/api/v1/gamification/xp/award` — Award XP
- `/api/v1/gamification/activity/track` — Track activity
- `/api/v1/gamification/dashboard/{session_id}` — Get dashboard data
- `/ccm/context/events` — Store context event
- `/ccm/flow/state/{session_id}` — Get flow state
- `/ccm/auto-commit/suggest/{session_id}` — Suggest commit message
- `/ccm/auto-commit/execute/{session_id}` — Execute auto-commit
- `/ccm/code-analysis/impact/{session_id}` — Analyze code impact
- `/ccm/integrations/slack/pr-summary` — Post PR summary to Slack

## Session Sync
- See `docs/session-sync.md` for details

## Gamification
- XP, achievements, streaks, leaderboards
- See `apps/ccm-api/services/gamification_service.py`

## Extensibility
- Add new endpoints in `apps/ccm-api/api/`
- See `apps/ccm-api/database/schema.sql` for schema

## References
- [Session Sync & Active Session Logic](./session-sync.md)
- [Database Schema](../apps/ccm-api/database/schema.sql)
- [Backend Source](../apps/ccm-api/) 