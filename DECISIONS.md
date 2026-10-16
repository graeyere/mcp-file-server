# DECISIONS

1. **Python + official `mcp` SDK (FastMCP API).** Slides allow Python; simplest for a beginner.
2. **Pinned `mcp<2`.** Version 2.x renamed FastMCP and changed APIs; 1.x matches the stable docs.
3. **Streamable HTTP transport.** Required for a shared, remote server (stdio only for local testing).
4. **Token auth treated as required.** Rubric caps the score if the public endpoint is open.

6. **ngrok abandoned, Cloudflare quick tunnel used.** The ngrok agent was too old for free accounts (ERR_NGROK_121), the winget copy was blocked ("Access is denied"), and the zip download was reset by the network. `cloudflared tunnel --url http://127.0.0.1:8000` needs no account. Tradeoff: the URL changes on every restart and has no uptime guarantee. A named Cloudflare tunnel or ngrok static domain would fix this.
7. **Token auth in the server itself, not the tunnel.** The tunnel is just a pipe; `/mcp` returns 401 without the bearer token. `/health` is open and returns only "ok".
8. **NSSM as process manager.** Slides list pm2/systemd/Docker; pm2 needs Node.js and systemd does not exist on Windows. NSSM runs the venv Python and cloudflared as auto-restarting Windows services. The venv python.exe is referenced by full path so the service finds its packages. Crash recovery was tested by killing the server process (new PID, health 200).
9. **Token as a URL path prefix for the Claude connector.** The Free-plan Add dialog had no Request headers option, so Claude cannot send a bearer header. The server accepts the token in either place. Cost: the URL is a credential, so the token must be rotated after use. Access logging is off so URLs are not written to disk.
10. **Call log committed as evidence/demo_calls.txt.** .gitignore excludes *.log, so the log was renamed to .txt to keep it in the repository.
