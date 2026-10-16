# PROJECT_STATE

**Last updated:** 2026-10-16 17:55

## Status
All mandatory work done and pushed. Remaining: the live demo and token rotation afterwards.

## Completed
- Sandbox, 10 tools, 90 tests passing (1 skipped: symlink test needs Windows Developer Mode)
- Server with token auth (header or URL path prefix), call logging, access log off
- Public HTTPS via Cloudflare quick tunnel; server and tunnel run as NSSM services (auto-start, auto-restart); crash recovery tested
- Real client: Claude Free-plan custom connector (No sign-in, token in URL path) plus scripts/smoke_test.py
- Two-session demo: workspace/demo/ plus evidence/session1_transcript.txt, session2_transcript.txt, demo_calls.txt (35 server calls: 17 + 13 + 5 verification)
- README.md and REPORT.md written

## Not done
- Full PC reboot test (only a process-crash recovery test)
- MCP Inspector run
- Write locking (if_version), git-lite tools, per-agent tool scoping
- Symlink-escape test is implemented but skipped on this PC

## Key facts
- Quick-tunnel URL changes when the mcp-tunnel service restarts; do not restart it while the Claude connector is in use
- The token lives only in the mcp-file-server service settings and the Claude connector URL
- Tests: pytest -q (90 passed, 1 skipped)

## Next action
Give the 5-minute live demo, then rotate the token (nssm set mcp-file-server AppEnvironmentExtra, restart, remove the connector).
