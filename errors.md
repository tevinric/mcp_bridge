DEBUG:**main**:Received MCP request
DEBUG:**main**:Request data: b'{"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"mcp","version":"0.1.0"}},"jsonrpc":"2.0","id":0}'
ERROR:root:Unhandled exception in receive loop: 'bytes' object has no attribute 'message'
Traceback (most recent call last):
File "C:\Users\E100545\DNA-AI\MCP_SERVERS\mcp_bridge\.venv\Lib\site-packages\mcp\shared\session.py", line 340, in \_receive_loop
elif isinstance(message.message.root, JSONRPCRequest):
^^^^^^^^^^^^^^^
AttributeError: 'bytes' object has no attribute 'message'
INFO:aiohttp.access:127.0.0.1 [24/Oct/2025:14:28:12 +0200] "POST /mcp HTTP/1.1" 200 207 "-" "python-httpx/0.28.1"
