#!/usr/bin/env python3
"""
Streamable HTTP -> MCP stdio bridge for markitdown_mcp_server.

This adapter creates an HTTP server that accepts MCP messages and forwards them
to the MCP server using proper async streams.
"""
import asyncio
import json
import logging
import sys
import os
from aiohttp import web

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


class MemoryReader:
    """Memory-based stream reader compatible with MCP."""

    def __init__(self):
        self._data = b""
        self._position = 0
        self._eof = False

    def write(self, data: bytes):
        """Write data to the stream."""
        self._data += data

    def set_eof(self):
        """Mark end of stream."""
        self._eof = True

    async def read(self, n: int = -1) -> bytes:
        """Read n bytes from the stream."""
        if self._position >= len(self._data):
            if self._eof:
                return b""
            # Wait a bit for more data
            await asyncio.sleep(0.01)
            if self._position >= len(self._data):
                return b""

        if n == -1:
            result = self._data[self._position:]
            self._position = len(self._data)
        else:
            end = min(self._position + n, len(self._data))
            result = self._data[self._position:end]
            self._position = end

        return result

    async def readline(self) -> bytes:
        """Read a line from the stream."""
        start = self._position

        # Look for newline
        while self._position < len(self._data):
            if self._data[self._position:self._position + 1] == b'\n':
                self._position += 1
                return self._data[start:self._position]
            self._position += 1

        # No newline found
        if self._eof and start < len(self._data):
            # Return remaining data
            result = self._data[start:]
            self._position = len(self._data)
            return result

        if self._eof:
            return b""

        # Reset position and wait
        self._position = start
        await asyncio.sleep(0.01)
        return b""

    async def readexactly(self, n: int) -> bytes:
        """Read exactly n bytes."""
        result = await self.read(n)
        if len(result) < n:
            raise asyncio.IncompleteReadError(result, n)
        return result


class MemoryWriter:
    """Memory-based stream writer compatible with MCP."""

    def __init__(self):
        self._data = []

    async def write(self, data: bytes):
        """Write data to the stream."""
        self._data.append(data)

    async def drain(self):
        """Drain the stream."""
        pass

    async def close(self):
        """Close the stream."""
        pass

    def get_data(self) -> bytes:
        """Get all written data."""
        return b"".join(self._data)


async def mcp_handler(request: web.Request) -> web.StreamResponse:
    """Handle MCP requests over HTTP with SSE streaming."""
    logger.debug("Received MCP request")

    resp = web.StreamResponse(
        status=200,
        reason="OK",
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        },
    )
    await resp.prepare(request)

    # Read the request body
    try:
        request_data = await request.read()
        logger.debug(f"Request data: {request_data[:200]}")

        if not request_data:
            logger.error("Empty request body")
            error_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Empty request body"}
            }
            await resp.write(json.dumps(error_resp).encode() + b"\n")
            await resp.write_eof()
            return resp

    except Exception as e:
        logger.error(f"Error reading request: {e}")
        error_resp = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32603, "message": str(e)}
        }
        await resp.write(json.dumps(error_resp).encode() + b"\n")
        await resp.write_eof()
        return resp

    # Parse the JSON-RPC message
    try:
        message = json.loads(request_data.decode('utf-8'))
        logger.debug(f"Parsed message: {message}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        error_resp = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
        }
        await resp.write(json.dumps(error_resp).encode() + b"\n")
        await resp.write_eof()
        return resp

    # Handle the message directly based on method
    try:
        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params", {})

        if method == "initialize":
            # Handle initialize
            from mcp.server import NotificationOptions

            result = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "prompts": {
                            "listChanged": False
                        }
                    },
                    "serverInfo": {
                        "name": "markitdown_mcp_server",
                        "version": "0.1.0"
                    }
                }
            }
            await resp.write(json.dumps(result).encode() + b"\n")

        elif method == "prompts/list":
            # Get prompts from the server
            prompts_list = await mcp_module.list_prompts()

            result = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "prompts": [
                        {
                            "name": p.name,
                            "description": p.description,
                            "arguments": [
                                {
                                    "name": arg.name,
                                    "description": arg.description,
                                    "required": arg.required
                                }
                                for arg in (p.arguments or [])
                            ]
                        }
                        for p in prompts_list
                    ]
                }
            }
            await resp.write(json.dumps(result).encode() + b"\n")

        elif method == "prompts/get":
            # Get a specific prompt
            name = params.get("name")
            arguments = params.get("arguments")

            prompt_result = await mcp_module.get_prompt(name, arguments)

            result = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "messages": [
                        {
                            "role": msg.role,
                            "content": {
                                "type": msg.content.type,
                                "text": msg.content.text
                            }
                        }
                        for msg in prompt_result.messages
                    ]
                }
            }
            await resp.write(json.dumps(result).encode() + b"\n")

        else:
            # Unknown method
            error_resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            await resp.write(json.dumps(error_resp).encode() + b"\n")

    except Exception as e:
        logger.error(f"Error handling request: {e}", exc_info=True)
        error_resp = {
            "jsonrpc": "2.0",
            "id": message.get("id") if isinstance(message, dict) else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }
        await resp.write(json.dumps(error_resp).encode() + b"\n")

    try:
        await resp.write_eof()
    except Exception:
        pass

    return resp


async def health(request):
    """Health check endpoint."""
    return web.Response(text="ok")


def main(host="0.0.0.0", port=8080):
    """Start the HTTP server."""
    app = web.Application()
    app.add_routes([
        web.post("/mcp", mcp_handler),
        web.get("/health", health)
    ])

    logger.info(f"Starting server on {host}:{port}")
    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    main()
