#!/usr/bin/env python3
"""
Streamable HTTP -> MCP stdio bridge for markitdown_mcp_server.

Place this file at the repository root (next to pyproject.toml / src/).
Run it inside the existing repository image while mounting your repo into /app.

This adapter:
- Accepts POST /mcp with chunked request body (raw MCP messages).
- Returns chunked response streaming MCP outputs.
"""
import asyncio
import json
import logging
import sys
import os
from aiohttp import web
from mcp import types
from mcp.server import NotificationOptions
from mcp.server.models import InitializationOptions

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    import markitdown_mcp_server.server as mcp_module
except ImportError:
    # Fallback import path
    from src.markitdown_mcp_server import server as mcp_module

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def mcp_handler(request: web.Request) -> web.StreamResponse:
    logger.debug("Received MCP request")

    resp = web.StreamResponse(
        status=200,
        reason="OK",
        headers={
            "Content-Type": "application/json",
            "Transfer-Encoding": "chunked",
            "Cache-Control": "no-cache",
        },
    )
    await resp.prepare(request)

    # Read the entire request body
    try:
        request_data = await request.read()
        logger.debug(f"Request data: {request_data}")

        if not request_data:
            logger.error("Empty request body")
            await resp.write(b'{"error": "Empty request body"}\n')
            return resp

    except Exception as e:
        logger.error(f"Error reading request: {e}")
        await resp.write(json.dumps({"error": str(e)}).encode() + b"\n")
        return resp

    # Parse the incoming JSON-RPC message
    try:
        message_text = request_data.decode("utf-8")
        logger.debug(f"Decoded message: {message_text}")
    except Exception as e:
        logger.error(f"Error decoding request: {e}")
        await resp.write(
            json.dumps({"error": f"Decode error: {str(e)}"}).encode() + b"\n"
        )
        return resp

    # Create input/output streams for MCP
    class StringIOAdapter:
        def __init__(self, data: str):
            self._data = data.encode("utf-8") + b"\n"
            self._pos = 0

        async def read(self, n: int = -1) -> bytes:
            if self._pos >= len(self._data):
                return b""

            if n == -1:
                result = self._data[self._pos :]
                self._pos = len(self._data)
            else:
                result = self._data[self._pos : self._pos + n]
                self._pos += len(result)

            return result

        async def readexactly(self, n: int) -> bytes:
            data = await self.read(n)
            if len(data) < n:
                raise asyncio.IncompleteReadError(data, n)
            return data

        async def readline(self) -> bytes:
            start = self._pos
            while (
                self._pos < len(self._data)
                and self._data[self._pos : self._pos + 1] != b"\n"
            ):
                self._pos += 1

            if self._pos < len(self._data):
                self._pos += 1  # Include the newline

            return self._data[start : self._pos]

    class ResponseCollector:
        def __init__(self):
            self._responses = []

        async def write(self, data: bytes):
            self._responses.append(data)

        async def drain(self):
            pass

        async def close(self):
            pass

        def get_response(self) -> bytes:
            return b"".join(self._responses)

    input_stream = StringIOAdapter(message_text)
    output_collector = ResponseCollector()

    # Run the MCP server
    try:
        logger.debug("Starting MCP server")

        # Use the existing server instance directly
        await mcp_module.app.run(
            input_stream,
            output_collector,
            InitializationOptions(
                server_name="markitdown_stream_http",
                server_version="0.1.0",
                capabilities=mcp_module.app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

        # Get the response and send it
        response_data = output_collector.get_response()
        logger.debug(f"MCP response: {response_data}")

        if response_data:
            await resp.write(response_data)
        else:
            # Send a default response if nothing was collected
            default_response = {
                "jsonrpc": "2.0",
                "id": 0,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "serverInfo": {"name": "markitdown_mcp_server", "version": "0.1.0"},
                },
            }
            await resp.write(json.dumps(default_response).encode() + b"\n")

    except Exception as e:
        logger.error(f"MCP server error: {e}", exc_info=True)
        error_response = {
            "jsonrpc": "2.0",
            "id": 0,
            "error": {"code": -32603, "message": str(e)},
        }
        await resp.write(json.dumps(error_response).encode() + b"\n")

    try:
        await resp.write_eof()
    except Exception:
        pass

    return resp


async def health(request):
    return web.Response(text="ok")


def main(host="0.0.0.0", port=8080):
    app = web.Application()
    app.add_routes([web.post("/mcp", mcp_handler), web.get("/health", health)])
    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    main()
