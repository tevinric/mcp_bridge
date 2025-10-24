DEBUG:**main**:Starting MCP server
ERROR:**main**:MCP server error: unhandled errors in a TaskGroup (1 sub-exception)

- Exception Group Traceback (most recent call last):
  | File "C:\Users\E100545\DNA-AI\MCP_SERVERS\markitdown_mcp_server\streamable_http_adapter.py", line 138, in mcp_handler
  | await mcp_module.app.run(
  | ...<10 lines>...
  | )
  | File "C:\Users\E100545\DNA-AI\MCP_SERVERS\markitdown_mcp_server\.venv\Lib\site-packages\mcp\server\lowlevel\server.py", line 616, in run
  | async with AsyncExitStack() as stack:
  | ~~~~~~~~~~~~~~^^
  | File "C:\Python313\Lib\contextlib.py", line 768, in **aexit**
  | raise exc
  | File "C:\Python313\Lib\contextlib.py", line 751, in **aexit**
  | cb_suppress = await cb(\*exc_details)
  | ^^^^^^^^^^^^^^^^^^^^^^
  | File "C:\Users\E100545\DNA-AI\MCP_SERVERS\markitdown_mcp_server\.venv\Lib\site-packages\mcp\shared\session.py", line 218, in **aexit**
  | return await self.\_task_group.**aexit**(exc_type, exc_val, exc_tb)
  | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  | File "C:\Users\E100545\DNA-AI\MCP_SERVERS\markitdown_mcp_server\.venv\Lib\site-packages\anyio_backends_asyncio.py", line 781, in **aexit**
  | raise BaseExceptionGroup(
  | "unhandled errors in a TaskGroup", self.\_exceptions
  | ) from None
  | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
  | Traceback (most recent call last):
  | File "C:\Users\E100545\DNA-AI\MCP_SERVERS\markitdown_mcp_server\.venv\Lib\site-packages\mcp\server\session.py", line 140, in \_receive_loop
  | await super().\_receive_loop()
  | File "C:\Users\E100545\DNA-AI\MCP_SERVERS\markitdown_mcp_server\.venv\Lib\site-packages\mcp\shared\session.py", line 333, in \_receive_loop
  | self.\_read_stream,
  | ^^^^^^^^^^^^^^^^^
  | TypeError: 'StringIOAdapter' object does not support the asynchronous context manager protocol
