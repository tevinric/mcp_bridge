DEBUG:**main**:Received MCP request
DEBUG:**main**:Request data: b'{"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"mcp","version":"0.1.0"}},"jsonrpc":"2.0","id":0}'
ERROR:root:Unhandled exception in receive loop: 'async for' requires an object with **aiter** method, got AsyncStreamReader
Traceback (most recent call last):
File "C:\Users\E100545\DNA-AI\MCP_SERVERS\mcp_bridge\.venv\Lib\site-packages\mcp\shared\session.py", line 337, in \_receive_loop
async for message in self.\_read_stream:
^^^^^^^^^^^^^^^^^
TypeError: 'async for' requires an object with **aiter** method, got AsyncStreamReader
INFO:aiohttp.access:127.0.0.1 [24/Oct/2025:14:22:07 +0200] "POST /mcp HTTP/1.1" 200 207 "-" "python-httpx/0.28.1"
