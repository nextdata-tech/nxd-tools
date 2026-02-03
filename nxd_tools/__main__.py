"""Main entry point for python -m nxd_tools."""

import sys


def main():
    """Main entry point showing available subcommands."""
    print("nxd-tools: Available commands:")
    print("  python -m nxd_tools.mcp_bridge  - Run the MCP stdio bridge")
    print("\nOr use the console scripts:")
    print("  nxd-bridge                       - Run the MCP stdio bridge")
    sys.exit(0)


if __name__ == "__main__":
    main()
