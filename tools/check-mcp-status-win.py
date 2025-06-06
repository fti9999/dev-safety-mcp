#!/usr/bin/env python3
"""
External MCP Status Checker - Windows Compatible Version

Lightweight external script to check if the dev-safety MCP server is running.
"""

import json
import os
import sys
import time
from datetime import datetime

def format_time_since(seconds):
    """Format seconds into human-readable time"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}m {int(seconds%60)}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"

def check_mcp_status():
    """Check MCP server status and return status info"""
    try:
        # Look for status file in standard location
        config_dir = os.path.expanduser("~/.dev-safety")
        status_file = os.path.join(config_dir, "mcp_status.json")
        
        if not os.path.exists(status_file):
            return {
                "status": "no_status_file",
                "message": f"Status file not found: {status_file}",
                "exit_code": 2
            }
        
        # Read status file with error handling
        try:
            with open(status_file, 'r') as f:
                content = f.read().strip()
                
            # Handle potential JSON corruption
            if content.count('{') > content.count('}'):
                # Incomplete JSON - server might be writing
                return {
                    "status": "writing",
                    "message": "Status file is being updated...",
                    "exit_code": 1
                }
                
            status_data = json.loads(content)
            
        except json.JSONDecodeError as e:
            return {
                "status": "corrupted",
                "message": f"Status file is corrupted or being written: {e}",
                "exit_code": 3
            }
        
        # Parse last heartbeat time
        try:
            last_heartbeat = datetime.fromisoformat(status_data['last_heartbeat'])
            now = datetime.now()
            time_since_heartbeat = (now - last_heartbeat).total_seconds()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Could not parse heartbeat time: {e}",
                "exit_code": 3
            }
        
        # Determine health status
        if time_since_heartbeat <= 60:
            # Healthy - recent heartbeat
            return {
                "status": "healthy",
                "message": f"MCP server is ACTIVE (last seen: {format_time_since(time_since_heartbeat)} ago)",
                "data": status_data,
                "time_since_heartbeat": time_since_heartbeat,
                "exit_code": 0
            }
        elif time_since_heartbeat <= 300:  # 5 minutes
            # Warning - old heartbeat but not too old
            return {
                "status": "warning", 
                "message": f"MCP server may be struggling (last seen: {format_time_since(time_since_heartbeat)} ago)",
                "data": status_data,
                "time_since_heartbeat": time_since_heartbeat,
                "exit_code": 1
            }
        else:
            # Down - very old heartbeat
            return {
                "status": "down",
                "message": f"MCP server appears DOWN (last seen: {format_time_since(time_since_heartbeat)} ago)",
                "data": status_data,
                "time_since_heartbeat": time_since_heartbeat,
                "exit_code": 1
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking status: {e}",
            "exit_code": 3
        }

def main():
    """Main function with Windows-compatible output"""
    result = check_mcp_status()
    
    # Print status message (no colors to avoid encoding issues)
    if result["status"] == "healthy":
        print(f"[OK] {result['message']}")
        
        # Show additional details for healthy status
        if "data" in result:
            data = result["data"]
            print(f"     PID: {data.get('server_pid', 'unknown')}")
            print(f"     Started: {data.get('startup_time', 'unknown')}")
            print(f"     Tools: {data.get('tools_registered', 'unknown')}")
            print(f"     Config: {data.get('config_dir', 'unknown')}")
            
    elif result["status"] == "warning":
        print(f"[WARNING] {result['message']}")
        
    elif result["status"] == "down":
        print(f"[ERROR] {result['message']}")
        print("        Your development protection may be lost!")
        
    elif result["status"] == "no_status_file":
        print(f"[INFO] {result['message']}")
        print("       MCP server may not be running or monitoring not enabled")
        
    elif result["status"] == "writing":
        print(f"[INFO] {result['message']}")
        
    elif result["status"] == "corrupted":
        print(f"[WARNING] {result['message']}")
        
    else:
        print(f"[ERROR] {result['message']}")
    
    # Exit with appropriate code for scripting
    sys.exit(result["exit_code"])

if __name__ == "__main__":
    main()
