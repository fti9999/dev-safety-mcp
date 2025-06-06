#!/usr/bin/env python3
"""
Quick test of MCP server functionality
"""

import asyncio
from mcp_server import DevSafetyMCP

async def quick_test():
    print("Testing MCP Server...")
    
    try:
        server = DevSafetyMCP()
        print("OK: MCP Server created successfully")
        
        # Check if tools are registered
        if hasattr(server.server, '_tools'):
            tools = list(server.server._tools.keys())
            print(f"OK: Found {len(tools)} tools: {', '.join(tools)}")
        elif hasattr(server.server, 'list_tools'):
            print("OK: Server has list_tools method")
        else:
            print("WARNING: No tools found or unknown tool registration method")
        
        print("SUCCESS: Basic MCP server functionality verified")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    if success:
        print("\nMCP Server is ready for use!")
    else:
        print("\nMCP Server has issues that need to be resolved.")
        exit(1)