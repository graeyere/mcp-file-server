# PROJECT_STATE

**Last updated:** 2026-10-16

## Status
M1, M2 done. M3 half done: server verified with a Python MCP client over HTTP + token. Not yet deployed.

## Completed
- Sandbox (`mcp_file_server/sandbox.py`) + tests; all escape attempts rejected
- 10 tools (`mcp_file_server/tools.py`) + 90 passing tests
- `server.py`: Streamable HTTP, bearer-token auth (MCP_TOKEN env var), call logging to `logs/calls.log`
- `scripts/smoke_test.py` passes; output saved in `evidence/`
- Pushed to https://github.com/graeyere/mcp-file-server

## Remaining
- M3: connect a real MCP client (Inspector / Claude)
- M4: HTTPS tunnel + process manager, survive restart
- M5: two-session demo (PLAN_LOG, CHECKPOINTS used by agents)
- M6: README, report, transcript, demo script

## Key facts
- Run: set `$env:MCP_TOKEN`, then `python -m mcp_file_server.server` (127.0.0.1:8000, endpoint /mcp, /health is open)
- Sandbox root: `workspace/` (env WORKSPACE_ROOT overrides)
- Tests: `pytest -q` (90 passed, 1 skipped: symlink test needs Developer Mode)
- Dependencies pinned: `mcp<2`

## Next action
Test with MCP Inspector, then set up the tunnel.
