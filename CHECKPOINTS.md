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
