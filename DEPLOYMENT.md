# Deployment Guide for MarkItDown MCP Server

This guide explains how to deploy the MarkItDown MCP server as a web application using Docker.

## Architecture

The deployment consists of:
- **MCP Server**: The core MarkItDown server that handles document conversion
- **HTTP Adapter**: A streamable HTTP bridge that exposes the MCP server over HTTP using Server-Sent Events (SSE)
- **Docker Container**: Packages everything together for easy deployment

## Building the Docker Image

1. Make sure you're in the project root directory:
```bash
cd /path/to/mcp_bridge
```

2. Build the Docker image:
```bash
docker build -t markitdown-mcp-server .
```

## Running the Server

### Local Testing

Run the server locally:
```bash
docker run -p 8080:8080 markitdown-mcp-server
```

The server will be available at `http://localhost:8080`

### Production Deployment

For production, you can use environment variables and volume mounts:

```bash
docker run -d \
  --name markitdown-mcp \
  -p 8080:8080 \
  --restart unless-stopped \
  markitdown-mcp-server
```

### Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  markitdown-mcp:
    build: .
    ports:
      - "8080:8080"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

Run with:
```bash
docker-compose up -d
```

## API Endpoints

### Health Check
```
GET /health
```

Returns `ok` if the server is running.

### MCP Endpoint
```
POST /mcp
Content-Type: application/json
```

Accepts MCP JSON-RPC messages and returns responses via Server-Sent Events (SSE).

Example request:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "test-client",
      "version": "1.0.0"
    }
  }
}
```

## Testing the Deployment

1. Test the health endpoint:
```bash
curl http://localhost:8080/health
```

2. Run the test script:
```bash
python test_http_server.py http://localhost:8080
```

3. Test with curl:
```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "prompts/list",
    "params": {}
  }'
```

## Deployment Platforms

### Deploy to Cloud Run (GCP)

1. Tag and push the image:
```bash
docker tag markitdown-mcp-server gcr.io/YOUR_PROJECT_ID/markitdown-mcp-server
docker push gcr.io/YOUR_PROJECT_ID/markitdown-mcp-server
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy markitdown-mcp-server \
  --image gcr.io/YOUR_PROJECT_ID/markitdown-mcp-server \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

### Deploy to AWS ECS

1. Push to ECR:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker tag markitdown-mcp-server YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/markitdown-mcp-server
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/markitdown-mcp-server
```

2. Create an ECS task definition and service using the AWS Console or CLI.

### Deploy to Heroku

1. Install Heroku CLI and login:
```bash
heroku login
heroku container:login
```

2. Create and deploy:
```bash
heroku create your-app-name
heroku container:push web -a your-app-name
heroku container:release web -a your-app-name
```

## Monitoring

The server includes debug logging. To view logs:

```bash
# Docker logs
docker logs -f markitdown-mcp

# Docker Compose logs
docker-compose logs -f
```

## Troubleshooting

### Server not starting
- Check that port 8080 is not already in use
- Verify all dependencies are installed in the Docker image
- Check Docker logs for error messages

### MCP messages not being processed
- Verify the request format matches the MCP JSON-RPC specification
- Check that the Content-Type header is set to `application/json`
- Review server logs for error messages

### Timeout issues
- The server has a 30-second timeout for MCP operations
- For large file conversions, you may need to adjust this in `streamable_http_adapter.py`

## Security Considerations

1. **Authentication**: Add authentication middleware if deploying publicly
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **CORS**: Configure CORS headers if accessed from web browsers
4. **HTTPS**: Always use HTTPS in production (configured at the load balancer level)

## Environment Variables

You can customize the server with environment variables:

```bash
docker run -p 8080:8080 \
  -e PORT=8080 \
  -e LOG_LEVEL=INFO \
  markitdown-mcp-server
```

To use these, update `streamable_http_adapter.py`:
```python
import os

def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    log_level = os.getenv("LOG_LEVEL", "DEBUG")

    logging.basicConfig(level=getattr(logging, log_level))
    # ... rest of main
```
