#!/usr/bin/env python3
"""
Simple test of the Development Safety MCP Server

Tests basic functionality without emojis for Windows compatibility.
"""

import asyncio
import os
import tempfile
import shutil
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_server import DevSafetyMCP


async def simple_test():
    """Test basic MCP server functionality"""
    
    print("Development Safety MCP Server - Simple Test")
    print("=" * 50)
    
    # Initialize the MCP server
    server = DevSafetyMCP()
    print("OK: MCP Server initialized")
    
    # Create a temporary project for testing
    temp_dir = tempfile.mkdtemp()
    project_path = os.path.join(temp_dir, "test_project")
    os.makedirs(project_path)
    
    # Create a simple test file
    with open(os.path.join(project_path, "main.py"), "w") as f:
        f.write("print('Hello, World!')")
    
    print(f"OK: Test project created at: {project_path}")
    
    try:
        # Test 1: Create sandbox
        print("\nTest 1: Creating sandbox")
        tools = server.server._tools if hasattr(server.server, '_tools') else {}
        
        if "create_sandbox" in tools:
            create_sandbox = tools["create_sandbox"]
            result = await create_sandbox(project_path)
            
            if result.get("status") == "created":
                sandbox_path = result["sandbox_path"]
                print(f"OK: Sandbox created at {sandbox_path}")
            else:
                print(f"ERROR: {result.get('error', 'Unknown error')}")
                return False
        else:
            print("ERROR: create_sandbox tool not found")
            return False
        
        # Test 2: Save session state
        print("\nTest 2: Saving session state")
        if "save_session_state" in tools:
            save_session = tools["save_session_state"]
            result = await save_session(
                operation="Test operation",
                current_step="Created sandbox",
                next_steps=["Add test code", "Run tests"],
                sandbox_path=sandbox_path,
                context={"test": True}
            )
            
            if result.get("status") == "saved":
                print("OK: Session state saved")
            else:
                print(f"ERROR: {result.get('error', 'Unknown error')}")
                return False
        else:
            print("ERROR: save_session_state tool not found")
            return False
        
        # Test 3: Load session state
        print("\nTest 3: Loading session state")
        if "load_session_state" in tools:
            load_session = tools["load_session_state"]
            result = await load_session()
            
            if result.get("status") == "loaded":
                print("OK: Session state loaded")
                print("Continuation prompt preview:")
                prompt_lines = result["continuation_prompt"].split('\n')[:5]
                for line in prompt_lines:
                    print(f"  {line}")
                print("  ...")
            else:
                print(f"ERROR: {result.get('error', 'No session found')}")
                return False
        else:
            print("ERROR: load_session_state tool not found")
            return False
        
        # Test 4: Check activity
        print("\nTest 4: Checking activity")
        if "check_activity" in tools:
            check_activity = tools["check_activity"]
            result = await check_activity(sandbox_path, minutes=1)
            
            if result.get("status") == "success":
                print(f"OK: Activity check completed - Active: {result.get('active', False)}")
            else:
                print(f"ERROR: {result.get('error', 'Unknown error')}")
                return False
        else:
            print("ERROR: check_activity tool not found")
            return False
        
        print("\n" + "=" * 50)
        print("SUCCESS: All tests passed!")
        print("\nCore functionality verified:")
        print("- Sandbox creation works")
        print("- Session state persistence works")
        print("- Session loading works")
        print("- Activity monitoring works")
        print("\nThe Development Safety MCP Server is ready for use!")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: Test failed with exception: {e}")
        return False
        
    finally:
        # Clean up
        print(f"\nCleaning up test files...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("OK: Cleanup completed")


if __name__ == "__main__":
    success = asyncio.run(simple_test())
    if not success:
        sys.exit(1)