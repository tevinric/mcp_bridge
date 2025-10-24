#!/usr/bin/env python3
"""
Streamable HTTP -> MCP stdio bridge for markitdown_mcp_server.

This adapter creates an HTTP server that accepts MCP messages and forwards them
to the MCP server, returning responses via SSE (Server-Sent Events).
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


class AsyncStreamReader:
    """Async stream reader that reads from a queue."""

    def __init__(self):
        self.queue = asyncio.Queue()
        self._closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._closed = True
        return False

    async def read(self, n: int = -1) -> bytes:
        """Read up to n bytes from the stream."""
        if self._closed and self.queue.empty():
            return b""

        try:
            data = await asyncio.wait_for(self.queue.get(), timeout=0.1)
            return data
        except asyncio.TimeoutError:
            return b""

    async def readline(self) -> bytes:
        """Read a line from the stream."""
        if self._closed and self.queue.empty():
            return b""

        try:
            data = await asyncio.wait_for(self.queue.get(), timeout=0.1)
            if not data.endswith(b'\n'):
                data += b'\n'
            return data
        except asyncio.TimeoutError:
            return b""

    async def readexactly(self, n: int) -> bytes:
        """Read exactly n bytes from the stream."""
        data = await self.read(n)
        if len(data) < n:
            raise asyncio.IncompleteReadError(data, n)
        return data

    def feed_data(self, data: bytes):
        """Feed data into the stream."""
        self.queue.put_nowait(data)


class AsyncStreamWriter:
    """Async stream writer that writes to a queue."""

    def __init__(self):
        self.queue = asyncio.Queue()
        self._closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._closed = True
        return False

    async def write(self, data: bytes):
        """Write data to the stream."""
        if not self._closed:
            await self.queue.put(data)

    async def drain(self):
        """Drain the stream (no-op for queue-based writer)."""
        pass

    async def close(self):
        """Close the stream."""
        self._closed = True

    async def get_data(self) -> bytes:
        """Get data from the stream."""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return b""


async def mcp_handler(request: web.Request) -> web.StreamResponse:
    """Handle MCP requests over HTTP with SSE streaming."""
    logger.debug("Received MCP request")

    resp = web.StreamResponse(
        status=200,
        reason="OK",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
    await resp.prepare(request)

    # Read the request body
    try:
        request_data = await request.read()
        logger.debug(f"Request data: {request_data[:200]}")

        if not request_data:
            logger.error("Empty request body")
            await resp.write(b'data: {"error": "Empty request body"}\n\n')
            await resp.write_eof()
            return resp

    except Exception as e:
        logger.error(f"Error reading request: {e}")
        await resp.write(f'data: {json.dumps({"error": str(e)})}\n\n'.encode())
        await resp.write_eof()
        return resp

    # Create input/output streams
    input_stream = AsyncStreamReader()
    output_stream = AsyncStreamWriter()

    # Feed the request data into the input stream
    input_stream.feed_data(request_data)

    # Run the MCP server in a background task
    async def run_mcp_server():
        try:
            from mcp.server.models import InitializationOptions
            from mcp.server import NotificationOptions

            async with input_stream, output_stream:
                await mcp_module.app.run(
                    input_stream,
                    output_stream,
                    InitializationOptions(
                        server_name="markitdown_mcp_server",
                        server_version="0.1.0",
                        capabilities=mcp_module.app.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )
        except Exception as e:
            logger.error(f"MCP server error: {e}", exc_info=True)
            await output_stream.write(
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(e)}
                }).encode() + b"\n"
            )

    # Start the MCP server task
    server_task = asyncio.create_task(run_mcp_server())

    # Stream the output back to the client
    try:
        while not server_task.done() or not output_stream.queue.empty():
            data = await output_stream.get_data()
            if data:
                logger.debug(f"Sending data: {data[:200]}")
                # Send as SSE format
                await resp.write(b"data: " + data.rstrip(b"\n") + b"\n\n")
            else:
                # Small delay to prevent tight loop
                await asyncio.sleep(0.01)

        # Wait for server task to complete
        await server_task

    except Exception as e:
        logger.error(f"Error streaming response: {e}", exc_info=True)
        await resp.write(f'data: {json.dumps({"error": str(e)})}\n\n'.encode())

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
