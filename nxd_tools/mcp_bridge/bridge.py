"""
MCP stdio bridge for Claude Desktop.
Creates a stdio MCP server that proxies all requests to a remote streamable HTTP MCP server.
"""

import argparse
import asyncio
import logging
from contextlib import AsyncExitStack

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MCPProxyServer:
    """MCP server that proxies to a remote streamable HTTP MCP server."""

    def __init__(self, base_url: str, token: str, no_ssl_verify: bool = False):
        self.base_url = base_url
        self.token = token
        self.no_ssl_verify = no_ssl_verify
        self.mcp_url = f"{base_url}/mcp"
        self.server = Server("mcp-stdio-bridge")
        self.remote_session: ClientSession | None = None
        self.tools_cache: list[Tool] = []
        self.exit_stack = AsyncExitStack()

        # Register handlers
        self.server.list_tools()(self.handle_list_tools)
        self.server.call_tool()(self.handle_call_tool)

    def create_httpx_client(self, headers=None, timeout=None, auth=None):
        """Create httpx client with SSL verification settings."""
        return httpx.AsyncClient(
            verify=not self.no_ssl_verify,
            headers=headers,
            timeout=timeout or 30.0,
            auth=auth,
        )

    async def connect_to_remote(self):
        """Connect to the remote MCP server."""
        logger.info(f"Connecting to remote MCP server at {self.mcp_url}")
        headers = {"X-Nextdata-Token": self.token}

        # Use AsyncExitStack to properly manage context managers
        read_stream, write_stream, _ = await self.exit_stack.enter_async_context(
            streamablehttp_client(
                self.mcp_url,
                headers=headers,
                httpx_client_factory=self.create_httpx_client,
            )
        )

        # Create and enter the client session context
        self.remote_session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        # Initialize the remote session
        await self.remote_session.initialize()
        logger.info("Remote MCP session initialized successfully")

        # Cache available tools
        tools_result = await self.remote_session.list_tools()
        self.tools_cache = tools_result.tools
        logger.info(f"Cached {len(self.tools_cache)} tools from remote server")

    async def handle_list_tools(self) -> list[Tool]:
        """Handle list_tools request by returning cached tools from remote server."""
        logger.info(f"Handling list_tools request, returning {len(self.tools_cache)} tools")
        return self.tools_cache

    async def handle_call_tool(self, name: str, arguments: dict):
        """Handle call_tool request by proxying to remote server."""
        logger.info(f"Handling call_tool request for {name} with args: {arguments}")

        if not self.remote_session:
            raise RuntimeError("Not connected to remote server")

        # Call the tool on the remote server
        result = await self.remote_session.call_tool(name, arguments)

        if result.isError:
            logger.error(f"Tool call failed: {result.content}")
            raise RuntimeError(f"Tool call failed: {result.content}")

        logger.info(f"Tool call successful, returning {len(result.content)} content items")
        return result.content

    async def cleanup(self):
        """Clean up all connections."""
        await self.exit_stack.aclose()


async def async_main(args):
    """Async main function."""
    # Create proxy server
    proxy = MCPProxyServer(args.base_url, args.token, args.no_ssl_verify)

    try:
        # Connect to remote server first
        await proxy.connect_to_remote()

        # Run stdio server
        logger.info("Starting stdio MCP server...")
        async with stdio_server() as (read_stream, write_stream):
            await proxy.server.run(
                read_stream, write_stream, proxy.server.create_initialization_options()
            )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error running MCP bridge: {e}", exc_info=True)
        raise
    finally:
        await proxy.cleanup()


def main():
    """Main entry point for the MCP bridge."""
    parser = argparse.ArgumentParser(description="MCP stdio bridge for Claude Desktop")
    parser.add_argument("--base-url", required=True, help="Base URL for MCP server")
    parser.add_argument("--token", required=True, help="PAT token for authentication")
    parser.add_argument("--no-ssl-verify", action="store_true", help="Disable SSL verification")
    args = parser.parse_args()

    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
