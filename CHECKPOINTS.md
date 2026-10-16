# CHECKPOINTS

## CP-1 (2026-10-16): Setup complete
- Done: venv, dependencies, folders, handoff files
- Resume at: M2, create `mcp_file_server/sandbox.py`

## CP-2 (2026-10-16): Server verified locally
- Done: sandbox, 10 tools, auth, logging, smoke test, 90 tests passing
- Resume at: test with MCP Inspector, then tunnel (M4)

## CP-3 (2026-10-16): Public HTTPS verified
- Done: tunnel works, token auth verified over HTTPS, all 10 tools pass via the public URL
- Resume at: process manager (keep server + tunnel alive after restart), then real MCP client, then 2-session demo
- Note: the quick-tunnel URL is temporary and changes on restart; the current one is not stored in the repo

## CP-4 (2026-10-16): Deployment complete
- Done: services auto-start/auto-restart, crash recovery verified, token only in service settings
- Resume at: connect a real MCP client (M3b), then two-session demo (M5)
- Note: quick-tunnel URL changes on restart; read it from logs\tunnel_err.log

## CP-5 (2026-10-16): Submission-ready
- Done: all mandatory requirements; demo evidence in repo
- Resume at: live demo, then rotate the token
- Note: do not restart mcp-tunnel before the demo (the URL would change)
