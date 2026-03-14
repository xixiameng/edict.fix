# Changelog

All notable changes to this project are documented in this file.

## [2026-03-14]

### Added
- Added OpenClaw compatibility guidance for newer versions in:
  - `README.md`
  - `README_EN.md`
  - `docs/task-dispatch-architecture.md`
- Added an explicit Agent-to-Agent example using `sessions_spawn` + `agentId`.

### Changed
- Updated dispatch/collaboration instructions from legacy `sessions_send` to `sessions_spawn` in core orchestration SOUL files:
  - `agents/taizi/SOUL.md`
  - `agents/zhongshu/SOUL.md`
  - `agents/shangshu/SOUL.md`
- Updated six ministry SOUL files to return results directly in current subagent session (auto-return via spawn chain), and explicitly avoid `sessions_send`:
  - `agents/hubu/SOUL.md`
  - `agents/libu/SOUL.md`
  - `agents/bingbu/SOUL.md`
  - `agents/xingbu/SOUL.md`
  - `agents/gongbu/SOUL.md`
  - `agents/libu_hr/SOUL.md`

### Fixed
- Enhanced `install.sh` agent registration logic:
  - Safely handles missing/wrong config types (`dict`/`list` guards).
  - Updates existing agents when needed (workspace fill + `subagents.allowAgents` merge).
  - Reports both added and updated agents.
- Filled missing OpenClaw collaboration defaults in generated `openclaw.json`:
  - `agents.defaults.subagents.maxSpawnDepth` (official path)
  - `agents.defaults.subagents.maxChildrenPerAgent`
  - `agents.defaults.subagents.maxConcurrent`
  - `agents.defaults.subagents.runTimeoutSeconds`
  - `agents.defaults.subagents.archiveAfterMinutes`
  - `tools.agentToAgent.enabled`
  - `tools.agentToAgent.allow` (merged with project agent IDs)
  - `tools.sessions.visibility`
  - `tools.subagents.tools.allow` default template
  - `tools.subagents.tools.deny` baseline (`gateway`, `cron`, `sessions_send`)
