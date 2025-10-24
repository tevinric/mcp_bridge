#!/usr/bin/env python3
"""
Test script for the MCP HTTP server.

This script tests the streamable HTTP adapter by sending MCP messages
to the server and verifying the responses.
"""
import asyncio
import json
import sys
from aiohttp import ClientSession


async def test_health_endpoint(base_url: str):
    """Test the health check endpoint."""
    print("Testing health endpoint...")
    async with ClientSession() as session:
        async with session.get(f"{base_url}/health") as resp:
            text = await resp.text()
            assert resp.status == 200
            assert text == "ok"
            print("✓ Health check passed")


async def test_initialize(base_url: str):
    """Test the MCP initialize request."""
    print("\nTesting MCP initialize request...")

    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {
                    "listChanged": True
                },
                "sampling": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }

    async with ClientSession() as session:
        async with session.post(
            f"{base_url}/mcp",
            json=initialize_request,
            headers={"Content-Type": "application/json"}
        ) as resp:
            print(f"Response status: {resp.status}")
            print(f"Response headers: {resp.headers}")

            # Read SSE stream
            responses = []
            async for line in resp.content:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    try:
                        response = json.loads(data)
                        responses.append(response)
                        print(f"Received: {json.dumps(response, indent=2)}")
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse JSON: {data}")
                        print(f"Error: {e}")

            if responses:
                print("✓ Initialize request completed")
                return responses
            else:
                print("✗ No responses received")
                return []


async def test_list_prompts(base_url: str):
    """Test listing available prompts."""
    print("\nTesting prompts/list request...")

    list_prompts_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "prompts/list",
        "params": {}
    }

    async with ClientSession() as session:
        async with session.post(
            f"{base_url}/mcp",
            json=list_prompts_request,
            headers={"Content-Type": "application/json"}
        ) as resp:
            print(f"Response status: {resp.status}")

            # Read SSE stream
            responses = []
            async for line in resp.content:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data = line[6:]
                    try:
                        response = json.loads(data)
                        responses.append(response)
                        print(f"Received: {json.dumps(response, indent=2)}")
                    except json.JSONDecodeError:
                        print(f"Failed to parse: {data}")

            if responses:
                print("✓ List prompts completed")
                return responses
            else:
                print("✗ No responses received")
                return []


async def main():
    """Run all tests."""
    base_url = "http://localhost:8080"

    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    print(f"Testing MCP HTTP server at {base_url}\n")

    try:
        await test_health_endpoint(base_url)
        await test_initialize(base_url)
        await test_list_prompts(base_url)

        print("\n" + "="*50)
        print("All tests completed!")
        print("="*50)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
