# Report: MCP File Server (Week 06, Midterms Pt 1)

**Author:** graeyere  **Date:** 2026-10-16  **Repo:** https://github.com/graeyere/mcp-file-server

## 1. Summary

I built and deployed an MCP file-server connector in Python. It exposes 10 tools over Streamable HTTP, restricted to one sandboxed folder (`workspace/`), protected by a secret token, reachable over HTTPS through a Cloudflare tunnel, and kept running by two Windows services. I connected Claude to it as a real MCP client and ran one multi-step task across two separate chat sessions that shared state only through files.

## 2. Stack and why

| Layer | Choice | Reason |
|---|---|---|
| Language / SDK | Python, official `mcp` SDK (FastMCP API), pinned `mcp<2` | The slides allow Python. Version 2.x renamed FastMCP and changed other APIs; I hit that error on first install, so I pinned 1.x to match the documentation I was following. |
| Transport | Streamable HTTP | Needed for a shared remote server. stdio only reaches the host that launched it. |
| Validation | Type-annotated tool arguments plus explicit checks in `tools.py` and `sandbox.py` | The SDK builds each tool's JSON input schema from the annotations. I did not add pydantic models of my own. |
| Tunnel | Cloudflare quick tunnel (`cloudflared`) | ngrok failed three ways: the agent was too old for a free account (ERR_NGROK_121), the winget copy was blocked ("Access is denied"), and the zip download was reset by the network. A quick tunnel needs no account. |
| Process manager | NSSM (Windows services) | The slides list pm2, systemd or Docker. pm2 needs Node.js and systemd does not exist on Windows. NSSM gives the same behaviour (start at boot, restart on crash). |
| Tests | pytest | 90 passed, 1 skipped. |
| Version control | git + GitHub, one commit per milestone | |

## 3. Architecture

`sandbox.py` (path safety) is used by `tools.py` (tool logic, no MCP code), which `server.py` wraps as MCP tools. A small ASGI wrapper (`TokenAuth`) checks the token before any request reaches the MCP app. Keeping the logic out of `server.py` let me test every tool directly without a network. Config comes from environment variables (`MCP_TOKEN`, `WORKSPACE_ROOT`, `LOG_FILE`, `PORT`); the token is stored only in the Windows service settings.

## 4. Tool design

Ten single-purpose tools: `list_files`, `read_file`, `write_file`, `append_file`, `str_replace`, `delete_file`, `make_dir`, `move_file`, `search_text`, `file_info`.

- **Descriptions say when to use the tool and how it fails** (for example, `str_replace` must match exactly once, and says to widen the match).
- **Outputs are kept small on purpose:** `read_file` returns at most 20,000 characters and tells the agent which offset to use next; `list_files` and `search_text` are capped and say when they stopped; `search_text` exists so agents do not have to read whole files.
- **Destructive actions are gated:** `delete_file` refuses unless `confirm=true`, will not delete the root or a non-empty folder; `move_file` and `write_file(overwrite=false)` refuse to replace existing files.
- **Errors are readable and recoverable:** failures return `isError=true` with a short message and never a stack trace or a disk path. Unexpected exceptions are logged server-side and reported as a generic message.
- **I did not implement git-lite tools.** I chose `search_text` as the allowed alternative, and blocked `.git` so agents cannot tamper with repository internals.

## 5. Security and tradeoffs

- **Sandbox:** every path goes through `Sandbox.resolve()`. It rejects non-strings, null bytes, `:` (drive letters and alternate data streams), absolute and UNC paths, any `..` segment, and any `.git` segment, then resolves the real path and checks it is inside the workspace. Tests cover 14 forbidden path forms, and a second set runs five escape attempts against every one of the 11 tool entry points.
- **Auth:** every request except `/health` needs the token, compared in constant time. Verified: no token gives 401, wrong token gives 401, correct token reaches the server, locally and through the public tunnel.
- **Tradeoff 1, token in the URL.** The Free-plan Claude connector dialog on my account had no Request headers option, so Claude cannot send a bearer header. I added a secret URL prefix (`/t/<token>/mcp`), which the Slides list as an acceptable option ("a secret path"). The cost is that the token is stored inside the connector URL, so the URL is a credential and the token must be rotated after use. Uvicorn's access log is disabled so URLs are not written to disk, and the server never logs the request path on a rejected call.
- **Tradeoff 2, quick tunnel.** No account and no setup, but the URL changes on every restart and there is no uptime guarantee.
- **Tradeoff 3, one shared token.** No per-agent identity, rate limits or approval step. `delete_file` is gated only by an argument.
- **Tradeoff 4, host-header check disabled.** The SDK's DNS-rebinding protection assumes a local hostname, so I turned it off and rely on the token.

## 6. Agent efficiency and management

Numbers below come from the server's own call log (`evidence/demo_calls.txt`, 35 calls), not from what the agents said about themselves. The agents reported about 20 and 16 calls; the server saw fewer (probably because loading tools is not a server call).

| Group | Server calls | Limit given | Notes |
|---|---|---|---|
| Session 1 (new chat) | 17 | 25 | 9 file creations, then read-before-edit for sections 1 and 2, then logs |
| Session 2 (new chat) | 13 | 20 | 5 reads first, then 2 edits, 1 rejected call, 1 recovery, then logs |
| My read-only verification checks | 5 | n/a | 2 after Session 1, 3 after Session 2 |

- **Read before write:** Session 2's first five calls were all `read_file`; its first edit came after them.
- **Error recovery:** its one failure (`search_text` given a file path instead of a folder) was followed by a changed call, not a blind retry, and the lesson was written into the handoff files.
- **Small outputs:** `search_text` was used instead of reading whole files; no call was retried unchanged; `delete_file` was never called.
- **Roles and tools:** the agents were told which folder they could use and which tool not to use, but they were all given all 10 tools. Per-agent tool scoping is not implemented (see section 7).
- **Handoff:** each session read `PROJECT_STATE.md` and `CHECKPOINTS.md` first. Session 2 had no memory of Session 1 and correctly reported steps 1 to 6 done and 7 to 8 left, which matched the files and the final `report.md`. Its Checkpoint 2 marks Checkpoint 1 as superseded.

## 7. What is not done or not proven

- **Real-client coverage:** Claude (Free plan) and my own Python MCP client were used. I did **not** run MCP Inspector.
- **Symlink escape test:** implemented via path resolution, but the test is skipped on this machine because Windows blocked symlink creation without Developer Mode.
- **Reboot test:** only a process-crash recovery test was run (killed the server process: new PID, health 200). I did not reboot the PC.
- **Not implemented:** git-lite tools, `search_code`, repo map, `if_version` locking, per-agent tool scoping, human approval for deletes.
- **Concurrency:** two agents writing the same file at once could overwrite each other. The handoff protocol avoids this by convention only.
- **Honesty about the demo:** the two sessions were real, separate Claude chats using the same connector, with no shared conversation history. It was one task, run once.

## 8. Evidence

All in the repository: `evidence/` (smoke-test output locally, through the public tunnel and through the services; 401 and health checks; crash-recovery test; Session 1 and Session 2 transcripts; `demo_calls.txt`), `workspace/demo/` (the agents' own PROJECT_STATE, PLAN_LOG, CHECKPOINTS, DECISIONS and the finished `report.md`), and the git history, one commit per milestone.

