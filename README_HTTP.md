# MarkItDown MCP Server - HTTP Deployment

This is a streamable HTTP adapter for the MarkItDown MCP server, allowing it to be deployed as a web application.

## Quick Start

### Build and Run with Docker

```bash
# Build the image
docker build -t markitdown-mcp-server .

# Run the server
docker run -p 8080:8080 markitdown-mcp-server

# Test the server
curl http://localhost:8080/health
```

### Test the Server

```bash
# Install test dependencies
pip install aiohttp

# Run the test script
python test_http_server.py
```

## What Changed

### Fixed Issues

1. **Async Context Manager Support**: Added `__aenter__` and `__aexit__` methods to stream adapters
2. **Proper Stream Handling**: Implemented queue-based async streams for bidirectional communication
3. **MCP Protocol Support**: Properly handles MCP JSON-RPC messages over HTTP
4. **SSE Streaming**: Uses Server-Sent Events for streaming responses back to clients

### New Files

- `streamable_http_adapter.py`: HTTP server that bridges MCP stdio to HTTP/SSE
- `test_http_server.py`: Test script to verify the HTTP server works correctly
- `DEPLOYMENT.md`: Comprehensive deployment guide
- `.dockerignore`: Optimizes Docker builds
- `Dockerfile`: Updated to work with pip instead of uv

### Architecture

```
HTTP Client → POST /mcp → HTTP Adapter → MCP Server → MarkItDown
                           ↓
HTTP Client ← SSE Stream ← Response Queue
```

The adapter:
1. Receives MCP JSON-RPC messages via HTTP POST
2. Forwards them to the MCP server via async streams
3. Streams responses back to the client using SSE

## API

### Endpoints

- `GET /health` - Health check (returns "ok")
- `POST /mcp` - MCP message endpoint (accepts JSON-RPC, returns SSE stream)

### Example Request

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "prompts/list"
  }'
```

### Example Response

```
data: {"jsonrpc":"2.0","id":1,"result":{"prompts":[...]}}
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions including:
- Docker deployment
- Cloud Run (GCP)
- AWS ECS
- Heroku
- Docker Compose

## Troubleshooting

If you encounter errors:

1. **Check logs**: `docker logs -f <container-id>`
2. **Verify port**: Make sure port 8080 is available
3. **Test health**: `curl http://localhost:8080/health`
4. **Run tests**: `python test_http_server.py`

Common issues:
- Port already in use: Change the port mapping `-p 9090:8080`
- Module import errors: Rebuild the Docker image
- Timeout errors: Check if the MCP server is responding

## Development

To run locally without Docker:

```bash
# Install dependencies
pip install -e .

# Run the adapter
python streamable_http_adapter.py
```

## License

Same as the original markitdown_mcp_server project.
