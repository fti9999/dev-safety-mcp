#!/usr/bin/env python3
"""
CLI interface for Development Safety MCP Server

Simple command-line interface for common operations.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.mcp_server import DevSafetyMCP


async def main():
    parser = argparse.ArgumentParser(description='Development Safety MCP Server CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Start the MCP server')
    server_parser.add_argument('--host', default='localhost', help='Host to bind to')
    server_parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    
    # Sandbox command
    sandbox_parser = subparsers.add_parser('sandbox', help='Sandbox operations')
    sandbox_parser.add_argument('--create', metavar='PROJECT_PATH', help='Create sandbox from project')
    sandbox_parser.add_argument('--name', help='Custom sandbox name')
    
    # Session command
    session_parser = subparsers.add_parser('session', help='Session operations')
    session_parser.add_argument('--load', action='store_true', help='Load latest session')
    session_parser.add_argument('--list', action='store_true', help='List recent sessions')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    server = DevSafetyMCP()
    
    if args.command == 'server':
        print(f"Starting MCP server on {args.host}:{args.port}")
        await server.run_server(args.host, args.port)
    
    elif args.command == 'sandbox':
        if args.create:
            tools = server.server._tools
            create_sandbox = tools["create_sandbox"]
            result = await create_sandbox(args.create, args.name)
            if result["status"] == "created":
                print(f"✅ Sandbox created: {result['sandbox_path']}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
        else:
            sandbox_parser.print_help()
    
    elif args.command == 'session':
        if args.load:
            tools = server.server._tools
            load_session = tools["load_session_state"]
            result = await load_session()
            if result["status"] == "loaded":
                print("✅ Session loaded:")
                print(result["continuation_prompt"])
            else:
                print("❌ No previous session found")
        else:
            session_parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())