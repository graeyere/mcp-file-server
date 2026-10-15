"""Connects to the running server with the token, lists tools, and calls them."""
import asyncio
import os
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = os.environ.get("MCP_URL", "http://127.0.0.1:8000/mcp")
TOKEN = os.environ.get("MCP_TOKEN", "")


async def call(session, name, **args):
    result = await session.call_tool(name, args)
    text = result.content[0].text if result.content else ""
    flag = "ERROR" if result.isError else "ok"
    print(f"--- {name}({args}) -> {flag}\n{text}\n")
    return result


async def main():
    if not TOKEN:
        sys.exit("Set MCP_TOKEN first (same value the server uses).")
    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with streamablehttp_client(URL, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print(f"{len(names)} tools: {names}\n")

            await call(session, "make_dir", path="smoke")
            await call(session, "write_file", path="smoke/a.txt", content="hello world\n")
            await call(session, "append_file", path="smoke/a.txt", content="second line\n")
            await call(session, "read_file", path="smoke/a.txt")
            await call(session, "str_replace", path="smoke/a.txt", old_str="hello", new_str="goodbye")
            await call(session, "search_text", query="goodbye")
            await call(session, "file_info", path="smoke/a.txt")
            await call(session, "move_file", src="smoke/a.txt", dst="smoke/b.txt")
            await call(session, "list_files", path="smoke", recursive=True)
            print("=== Things that MUST fail ===\n")
            await call(session, "read_file", path="../PROJECT_STATE.md")
            await call(session, "read_file", path="C:\\Windows\\win.ini")
            await call(session, "delete_file", path="smoke/b.txt")
            await call(session, "delete_file", path="smoke/b.txt", confirm=True)
            await call(session, "delete_file", path="smoke", confirm=True)


asyncio.run(main())
