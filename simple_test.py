#!/usr/bin/env python3
"""
Simple MCP monitoring test - no emoji characters for Windows compatibility
"""

import os
import sys
import json
import time
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_monitoring():
    """Test basic monitoring functionality"""
    print("Testing MCP Monitoring System")
    print("=" * 40)
    
    try:
        # Import and create MCP server instance
        from mcp_server import DevSafetyMCP
        
        print("1. Creating MCP server instance...")
        server = DevSafetyMCP()
        
        # Check if status file was created
        config_path = os.path.expanduser("~/.dev-safety")
        status_file = os.path.join(config_path, "mcp_status.json")
        
        print(f"2. Looking for status file: {status_file}")
        
        if os.path.exists(status_file):
            print("   Status file found!")
            
            # Read and display status
            with open(status_file, 'r') as f:
                status_data = json.load(f)
            
            print(f"   Status: {status_data.get('status')}")
            print(f"   PID: {status_data.get('server_pid')}")
            print(f"   Tools: {status_data.get('tools_registered')}")
            print(f"   Version: {status_data.get('version')}")
            print(f"   Heartbeat: {status_data.get('last_heartbeat')}")
            
            # Wait a bit to see if heartbeat updates
            print("3. Waiting 5 seconds to check heartbeat updates...")
            time.sleep(5)
            
            with open(status_file, 'r') as f:
                updated_status = json.load(f)
            
            if updated_status['last_heartbeat'] != status_data['last_heartbeat']:
                print("   Heartbeat is updating correctly!")
            else:
                print("   Note: Heartbeat may update every 30 seconds")
            
            return True
        else:
            print("   Status file was not created")
            return False
            
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_monitoring()
    if success:
        print("\nBasic monitoring test completed successfully!")
        sys.exit(0)
    else:
        print("\nBasic monitoring test failed!")
        sys.exit(1)
