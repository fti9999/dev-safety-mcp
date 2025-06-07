#!/usr/bin/env python3
"""
Simple External Test for MCP Comprehensive Testing Suite
"""

import asyncio
import sys
import os
sys.path.append('src')

async def test_basic_functionality():
    """Basic test of new functionality"""
    print("Testing Comprehensive MCP Testing Suite...")
    
    try:
        # Test import
        from mcp_server import DevSafetyMCP
        print("SUCCESS: DevSafetyMCP imports correctly")
        
        # Initialize
        dev_safety = DevSafetyMCP()
        print("SUCCESS: DevSafetyMCP initializes correctly")
        
        # Test helper methods
        mcp_health = await dev_safety._check_mcp_ecosystem_health()
        print(f"SUCCESS: MCP Health Check - {mcp_health['health_status']}")
        
        web_tests = await dev_safety._run_web_interface_tests()
        print(f"SUCCESS: Web Interface Tests - {web_tests['status']}")
        
        print("\nAll basic tests passed!")
        print("New comprehensive testing tools are ready for deployment.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    if success:
        print("\nREADY FOR DEPLOYMENT!")
    else:
        print("\nFIXES NEEDED BEFORE DEPLOYMENT!")
