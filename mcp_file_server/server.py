"""MCP file server: exposes FileTools over Streamable HTTP with bearer-token auth."""
import argparse
import hmac
import logging
import os
import sys
import time
from pathlib import Path

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from .sandbox import Sandbox, SandboxError
from .tools import FileTools, ToolError

ROOT = Path(os.environ.get("WORKSPACE_ROOT", "workspace"))
LOG_FILE = Path(os.environ.get("LOG_FILE", "logs/calls.log"))

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("mcp_file_server")

tools = FileTools(Sandbox(ROOT))

# Host-header checking is turned off because requests arrive through a tunnel
# with a public hostname. Access is protected by the bearer token instead.
mcp = FastMCP(
    "file-server",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


def _short(value):
    s = repr(value)
    return s if len(s) <= 80 else s[:77] + "..."


def _run(name, fn, **kwargs):
    """Call a tool, log it, and turn failures into readable errors (isError=true)."""
    shown = ", ".join(f"{k}={_short(v)}" for k, v in kwargs.items())
    start = time.time()
    try:
        result = fn(**kwargs)
        log.info("CALL %s(%s) ok %.0fms", name, shown, (time.time() - start) * 1000)
        return result
    except (SandboxError, ToolError) as e:
        log.warning("CALL %s(%s) rejected: %s", name, shown, e)
        raise ToolError(str(e))
    except Exception as e:  # never leak stack traces or disk paths to the agent
        log.exception("CALL %s(%s) crashed", name, shown)
        raise ToolError(f"Unexpected server error ({type(e).__name__}). Check the server log.")


@mcp.tool()
def list_files(path: str = ".", recursive: bool = False, max_entries: int = 200) -> str:
    """List files and folders inside a workspace folder. Folders end with '/'.
    Use recursive=true for a whole tree. Output is capped at max_entries, so
    narrow the path if you see a truncation note."""
    return _run("list_files", tools.list_files, path=path, recursive=recursive, max_entries=max_entries)


@mcp.tool()
def read_file(path: str, offset: int = 0, limit: int = 20000) -> str:
    """Read a UTF-8 text file in chunks (limit is at most 20000 characters).
    The header says if more is available and which offset to use next.
    Fails if the file is missing, too large, or not text."""
    return _run("read_file", tools.read_file, path=path, offset=offset, limit=limit)


@mcp.tool()
def write_file(path: str, content: str, overwrite: bool = True) -> str:
    """Create or replace a text file. Parent folders are created automatically.
    Set overwrite=false to fail instead of replacing an existing file.
    To change part of a file, prefer str_replace."""
    return _run("write_file", tools.write_file, path=path, content=content, overwrite=overwrite)


@mcp.tool()
def append_file(path: str, content: str) -> str:
    """Add text to the end of a file, creating it if needed. Use this for logs
    such as PLAN_LOG.md. Include a leading newline in content if required."""
    return _run("append_file", tools.append_file, path=path, content=content)


@mcp.tool()
def str_replace(path: str, old_str: str, new_str: str) -> str:
    """Replace one exact occurrence of old_str in a file. old_str must appear
    exactly once or the call fails, so widen the match with surrounding text.
    Read the file first so you copy the text exactly."""
    return _run("str_replace", tools.str_replace, path=path, old_str=old_str, new_str=new_str)


@mcp.tool()
def delete_file(path: str, confirm: bool = False) -> str:
    """DESTRUCTIVE: delete one file or one empty folder. Refuses unless
    confirm=true. Cannot delete the workspace root or non-empty folders."""
    return _run("delete_file", tools.delete_file, path=path, confirm=confirm)


@mcp.tool()
def make_dir(path: str) -> str:
    """Create a folder (and any missing parents). Safe to call if it exists."""
    return _run("make_dir", tools.make_dir, path=path)


@mcp.tool()
def move_file(src: str, dst: str) -> str:
    """Move or rename a file or folder. Fails if dst already exists, so it
    never overwrites anything."""
    return _run("move_file", tools.move_file, src=src, dst=dst)


@mcp.tool()
def search_text(query: str, path: str = ".", max_results: int = 50) -> str:
    """Case-insensitive text search across files under a folder. Returns
    'file:line: text' lines, capped at max_results. Use this instead of
    reading whole files to find something."""
    return _run("search_text", tools.search_text, query=query, path=path, max_results=max_results)


@mcp.tool()
def file_info(path: str) -> str:
    """Return type (file/directory), size in bytes, and last-modified time."""
    return _run("file_info", tools.file_info, path=path)


class TokenAuth:
    """ASGI wrapper: every HTTP request needs 'Authorization: Bearer <token>'."""

    def __init__(self, app, token: str):
        self.app = app
        self.expected = f"Bearer {token}".encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope["path"] == "/health":
            await self._reply(send, 200, b"ok")
            return
        given = dict(scope["headers"]).get(b"authorization", b"")
        if hmac.compare_digest(given, self.expected):
            await self.app(scope, receive, send)
        else:
            log.warning("AUTH rejected request to %s", scope["path"])
            await self._reply(send, 401, b"unauthorized")

    @staticmethod
    async def _reply(send, status: int, body: bytes):
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"text/plain")]})
        await send({"type": "http.response.body", "body": body})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdio", action="store_true", help="local stdio mode (no auth)")
    args = parser.parse_args()

    if args.stdio:
        mcp.run()
        return

    token = os.environ.get("MCP_TOKEN", "")
    if len(token) < 16:
        sys.exit("Set MCP_TOKEN (at least 16 characters) before starting the server.")
    port = int(os.environ.get("PORT", "8000"))
    app = TokenAuth(mcp.streamable_http_app(), token)
    log.info("Starting on 127.0.0.1:%s, workspace=%s", port, tools.sb.root)
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()

