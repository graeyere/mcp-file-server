# PLAN_LOG

## 2026-10-16
- [done] M1: environment, dependencies (pinned mcp<2), structure, handoff files
- [next] M2: sandbox.py with path-escape protection, then tools, then tests

## 2026-10-16 (later)
- [done] M2: sandbox, 10 tools, 90 tests, server.py with token auth + logging
- [done] M3a: smoke_test.py passed against running server (evidence/smoke_test_output.txt)
- [next] M3b: MCP Inspector / real client, then M4 tunnel + process manager

## 2026-10-16 (04:30)
- [done] M4a: public HTTPS tunnel (Cloudflare quick tunnel). /health 200, /mcp without token 401, smoke_test.py passes through the tunnel (evidence/*public*)
- [next] M4b: process manager so the server and tunnel survive a restart; then M3b real MCP client
