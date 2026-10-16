# PROJECT_STATE

**Last updated:** 2026-10-16 11:50

## Status
M1, M2, M3a, M4 done. Server and tunnel run as Windows services (NSSM), reachable over public HTTPS, token required. Crash recovery verified. NOT yet done: real MCP client (M3b), two-session demo (M5), README/report/transcript/demo script (M6), full reboot test.

## Completed
- Sandbox + 10 tools + 90 tests; all escape attempts rejected
- server.py: Streamable HTTP, bearer token (MCP_TOKEN env var), call log
- Services: `mcp-file-server` (venv python -m mcp_file_server.server) and `mcp-tunnel` (cloudflared quick tunnel), both auto-start and auto-restart
- Token lives only in the mcp-file-server service settings (`nssm get mcp-file-server AppEnvironmentExtra` in an admin PowerShell), never in the repo
- Evidence in evidence/: smoke tests (local, public, via services), 401/health checks, service_restart_test.txt
- Repo: https://github.com/graeyere/mcp-file-server

## Remaining
- M3b: connect a real MCP client (Claude custom connector or MCP Inspector); check whether the client supports a bearer token
- M5: two-session demo using PROJECT_STATE / PLAN_LOG / CHECKPOINTS
- M6: README, report, transcript, 5-minute demo script, final checklist
- Optional: full PC reboot test

## Key facts
- Quick-tunnel URL changes whenever mcp-tunnel restarts. Read it with:
  Select-String -Path logs\tunnel_err.log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -AllMatches | ForEach-Object { $_.Matches.Value } | Select-Object -Last 1
- Run smoke test with the venv python: `.\.venv\Scripts\python.exe scripts\smoke_test.py` (needs MCP_TOKEN and MCP_URL set)
- Tests: `pytest -q` (90 passed, 1 skipped)
- Dependencies pinned: mcp<2

## Next action
M3b: connect a real MCP client to the public URL.
