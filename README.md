# nxd-tools

Collection of tools for working with MCP (Model Context Protocol) and other protocols.

## Installation

```bash
# Install the MCP bridge
pip install nxd-tools[mcp-bridge]

# Or with uv
uv pip install nxd-tools[mcp-bridge]
```

## Components

### MCP Bridge (`nxd-tools[mcp-bridge]`)

A stdio-to-HTTP proxy that enables stdio-based MCP clients (like Claude Desktop) to communicate with remote streamable HTTP MCP servers.

**Usage:**

```bash
# Using the console script
nxd-bridge --base-url https://server.example.com --token YOUR_TOKEN

# Using module invocation
python -m nxd_tools.mcp_bridge --base-url https://server.example.com --token YOUR_TOKEN

# Disable SSL verification (for development)
nxd-bridge --base-url https://server.example.com --token YOUR_TOKEN --no-ssl-verify
```

**Claude Desktop Configuration:**

Add to your Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "my-remote-server": {
      "command": "nxd-bridge",
      "args": [
        "--base-url",
        "https://server.example.com",
        "--token",
        "YOUR_TOKEN"
      ]
    }
  }
}
```

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev,mcp-bridge]"

# Install pre-commit hooks
pre-commit install

# Run quality checks
ruff check . --fix
ruff format .

# Build package
python -m build
```

## License

MIT
