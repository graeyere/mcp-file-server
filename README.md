# MCP File Server

A sandboxed file-server connector built with the official Python MCP SDK (`mcp<2`, FastMCP API). It gives AI agents 10 file tools inside one folder (`workspace/`), served over Streamable HTTP behind a token, so that several agent sessions can share files and hand work off through them.

Built for CS 3A / CS 3B, Week 06 (Model Context Protocol), Midterms Pt 1.

## What it does

- Exposes 10 tools: list, read, write, append, str_replace, delete, make_dir, move, search_text, file_info.
- Every path goes through one sandbox check before any file is touched.
- Requires a secret token on every request (`/health` is the only open endpoint).
- Logs every tool call to `logs/calls.log`.
- Runs on Windows as two services (server + HTTPS tunnel) that restart themselves after a crash.

## Repository layout

| Path | Purpose |
|---|---|
| `mcp_file_server/sandbox.py` | Path safety (the security core) |
| `mcp_file_server/tools.py` | Tool logic, no MCP code, easy to test |
| `mcp_file_server/server.py` | MCP wiring, token auth, logging, HTTP server |
| `tests/` | pytest tests (sandbox + every tool + escape attempts on every tool) |
| `scripts/smoke_test.py` | Real MCP client that calls every tool over HTTP(S) |
| `workspace/` | The only folder the agents may touch |
| `workspace/demo/` | Files written by the two-session demo (agent handoff files) |
| `evidence/` | Smoke-test output, status checks, call log, session transcripts |
| `PROJECT_STATE.md`, `PLAN_LOG.md`, `CHECKPOINTS.md`, `DECISIONS.md` | Handoff files for the project itself |

## Prerequisites (Windows)

- Windows 10/11, PowerShell
- Python 3.10 or newer (tested with 3.13)
- Git
- For the public deployment: `winget` (to install NSSM and cloudflared) and an administrator PowerShell

## Setup

Run from the folder where you want the project:

```powershell
git clone https://github.com/graeyere/mcp-file-server.git
cd mcp-file-server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks the activate script, run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` once.

`requirements.txt` pins `mcp<2`. Version 2.x renamed `FastMCP` and changed other APIs, so the code here will not run on it.

## Run the tests

```powershell
pytest -q
```

Expected: `90 passed, 1 skipped`. The skipped test needs symlink permission (Windows Developer Mode). See Limitations.

## Run locally

```powershell
$env:MCP_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
python -m mcp_file_server.server
```

The server listens on `127.0.0.1:8000` only. The MCP endpoint is `/mcp`; `/health` returns `ok`.

Environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `MCP_TOKEN` | none (required, 16+ chars) | The secret. Never put it in a file in this repo. |
| `WORKSPACE_ROOT` | `workspace` | The only folder agents can reach |
| `LOG_FILE` | `logs/calls.log` | Tool-call log |
| `PORT` | `8000` | Local port |

To use it without the network (for example with MCP Inspector), `python -m mcp_file_server.server --stdio` runs it over stdio with no auth.

## Test it with a real MCP client

In a second terminal:

```powershell
$env:MCP_TOKEN = "<the same token>"
python scripts\smoke_test.py
```

This connects with the bearer token, lists the 10 tools, calls each one, then confirms that escape attempts and an unconfirmed delete fail with readable errors. Set `MCP_URL` to test a public URL.

## Deploy on Windows (HTTPS + process manager)

1. **Tunnel.** `cloudflared tunnel --url http://127.0.0.1:8000` gives a public `https://....trycloudflare.com` address with no account. TLS ends at Cloudflare; the server itself stays on `127.0.0.1`.
2. **Process manager.** NSSM runs the venv's Python and cloudflared as Windows services that start at boot and restart after a crash.

In an **administrator** PowerShell, from the project folder:

```powershell
winget install --id NSSM.NSSM
winget install --id Cloudflare.cloudflared
# restart the shell so PATH updates, then:
$proj = (Get-Location).Path
$token = & "$proj\.venv\Scripts\python.exe" -c "import secrets; print(secrets.token_urlsafe(32))"
nssm install mcp-file-server "$proj\.venv\Scripts\python.exe" "-m mcp_file_server.server"
nssm set mcp-file-server AppDirectory $proj
nssm set mcp-file-server AppEnvironmentExtra "MCP_TOKEN=$token"
nssm set mcp-file-server AppStdout "$proj\logs\service_out.log"
nssm set mcp-file-server AppStderr "$proj\logs\service_err.log"
nssm set mcp-file-server Start SERVICE_AUTO_START
nssm set mcp-file-server AppExit Default Restart
nssm set mcp-file-server AppRestartDelay 5000
nssm start mcp-file-server

$cf = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
nssm install mcp-tunnel $cf "tunnel --no-autoupdate --url http://127.0.0.1:8000"
nssm set mcp-tunnel AppDirectory $proj
nssm set mcp-tunnel AppStdout "$proj\logs\tunnel_out.log"
nssm set mcp-tunnel AppStderr "$proj\logs\tunnel_err.log"
nssm set mcp-tunnel Start SERVICE_AUTO_START
nssm set mcp-tunnel AppExit Default Restart
nssm set mcp-tunnel AppRestartDelay 5000
nssm start mcp-tunnel
```

The token lives only in the service settings on that PC. `nssm get mcp-file-server AppEnvironmentExtra` prints it, so keep that output private.

**Health checks:**

```powershell
curl.exe -i http://127.0.0.1:8000/health                        # 200 ok
curl.exe -i -X POST https://<tunnel-url>/mcp                    # 401 without a token
```

**Find the current public URL** (it changes whenever the tunnel service restarts):

```powershell
Select-String -Path logs\tunnel_err.log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -AllMatches | ForEach-Object { $_.Matches.Value } | Select-Object -Last 1
```

## Connect an MCP client

- **Clients that can send headers** (the smoke test, MCP Inspector, Claude Code): send `Authorization: Bearer <token>` to `https://<tunnel-url>/mcp`.
- **Claude custom connector** (tested on the Free plan): the Add dialog had no Request headers option on this account, so the connector uses **No sign-in** with the token inside the URL: `https://<tunnel-url>/t/<token>/mcp`. The server accepts the token as that URL prefix and strips it before routing.

Do not restart the tunnel service while a connector depends on the URL, because the quick-tunnel address changes.

## Tools

| Tool | Purpose | Limits and safety |
|---|---|---|
| `list_files` | List a folder, optionally recursive | Max 200 entries; `.git` and symlinks hidden |
| `read_file` | Read UTF-8 text in chunks | Max 20,000 chars per call; header gives the next offset; files over 2 MB refused |
| `write_file` | Create or replace a text file | `overwrite=false` to refuse replacement; 1 MB cap |
| `append_file` | Add text to the end of a file | 1 MB cap |
| `str_replace` | Replace one exact, unique match | Fails with a clear message if 0 or 2+ matches |
| `delete_file` | Delete a file or empty folder | Destructive: refuses unless `confirm=true`; cannot delete the root |
| `make_dir` | Create a folder | Creates parents |
| `move_file` | Move or rename | Never overwrites an existing destination |
| `search_text` | Case-insensitive text search | Max 50 results; skips big files and symlinks |
| `file_info` | Type, size, modified time | Read-only |

Tool failures return `isError=true` with a short readable message (no stack traces or disk paths).

## Security

- **Sandbox.** All paths pass through `Sandbox.resolve()`, which rejects: non-strings, null bytes, `:` (drive letters and alternate data streams), absolute and UNC paths, any `..` segment, and any `.git` segment. The final path is also resolved to its real location and must be inside the workspace, which catches symlink escapes.
- **Auth.** Every request except `/health` needs the token (header or URL prefix), compared in constant time. Without it, the server returns 401.
- **Local binding.** The server listens on `127.0.0.1` only. The tunnel is the only way in.
- **No code execution.** Nothing in a file is ever run or evaluated.
- **No secrets in the repo.** `.gitignore` excludes `.env`, `logs/`, and the venv. The token is only in the service settings.
- **Logs.** `logs/calls.log` records each call and its arguments (truncated). Uvicorn's access log is off, because it would print URLs, which can contain the token.
- **Tests.** Every tool is tested against `../x`, `/etc/passwd`, `C:\Windows`, `a/../../x` and `.git/config`.

## Known limitations (read these)

- **Quick tunnel.** The URL changes on every restart and Cloudflare gives no uptime guarantee. A named Cloudflare tunnel or an ngrok static domain would fix this.
- **Token in the URL.** The Claude connector stores the token inside the URL, so anyone who sees that URL has full access to the workspace. Rotate the token after use: set a new `MCP_TOKEN` on the service with `nssm set`, restart it, and re-add the connector.
- **One shared token.** There is no per-agent identity, rate limiting, or per-tool permission. `delete_file` is gated only by the `confirm=true` argument, not by a human approval.
- **No write locking.** Two agents writing the same file at the same time can overwrite each other (the `if_version` stretch feature is not implemented). The handoff files are the coordination protocol.
- **Symlink test skipped here.** The test that creates a symlink pointing outside the workspace needs Windows Developer Mode, which was off, so the symlink protection is implemented but not covered by a passing test on this machine.
- **Host-header protection disabled.** The SDK's DNS-rebinding check is turned off because requests arrive with a public hostname. The token protects the endpoint instead.
- **Not done:** git-lite tools, `search_code`, repo map, `if_version` locking, and a full computer-reboot test (only a process-crash recovery test was run).

## Handoff protocol

Agents hand work over through files, not conversation history. Each agent session reads `PROJECT_STATE.md` and `CHECKPOINTS.md` first, works, then appends to `PLAN_LOG.md`, records choices in `DECISIONS.md`, and updates the other two. The demo in `workspace/demo/` shows two separate Claude chats finishing one report this way. The evidence is in `evidence/` (transcripts and `demo_calls.txt`).

