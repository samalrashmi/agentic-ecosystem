#!/usr/bin/env python3
"""
Main entry point for the Agentic Ecosystem

This module provides the main entry points for running the system.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_servers.main_server import main as server_main
from src.cli import cli


def run_server():
    """Run the MCP server."""
    print("Starting Agentic Ecosystem MCP Server...")
    asyncio.run(server_main())


def run_cli():
    """Run the CLI interface."""
    cli()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        run_server()
    elif len(sys.argv) > 1 and sys.argv[1] == "cli":
        # Remove 'cli' from argv and run CLI
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        run_cli()
    else:
        print("Agentic Ecosystem - Agent-based Software Development Platform")
        print()
        print("Usage:")
        print("  python main.py server          # Start the MCP server")
        print("  python main.py cli [command]   # Run CLI commands")
        print()
        print("CLI Commands:")
        print("  python main.py cli health                    # Check server health")
        print("  python main.py cli create                    # Create new project")
        print("  python main.py cli status <project_id>      # Get project status")
        print("  python main.py cli list                     # List all projects")
        print("  python main.py cli monitor <project_id>     # Monitor project real-time")
        print("  python main.py cli workflow <project_id>    # Show workflow history")
        print("  python main.py cli clarify <project_id>     # Send clarification")
        print()
        print("Examples:")
        print("  # Start the server")
        print("  python main.py server")
        print()
        print("  # Create a new project")
        print("  python main.py cli create")
        print()
        print("  # Check project status")
        print("  python main.py cli status abc-123-def")
        print()
        print("Environment Variables:")
        print("  MCP_SERVER_HOST     # Server host (default: 0.0.0.0)")
        print("  MCP_SERVER_PORT     # Server port (default: 8000)")
        print("  OPENAI_API_KEY      # OpenAI API key for LLM")
        print("  LOG_LEVEL           # Logging level (default: INFO)")
