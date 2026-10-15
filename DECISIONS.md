# DECISIONS

1. **Python + official `mcp` SDK (FastMCP API).** Slides allow Python; simplest for a beginner.
2. **Pinned `mcp<2`.** Version 2.x renamed FastMCP and changed APIs; 1.x matches the stable docs.
3. **Streamable HTTP transport.** Required for a shared, remote server (stdio only for local testing).
4. **Token auth treated as required.** Rubric caps the score if the public endpoint is open.
