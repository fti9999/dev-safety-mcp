"""
Basic Workflow Example for Development Safety MCP Server

This example demonstrates how to use the Development Safety MCP Server
for a typical development workflow with session continuity.
"""

import asyncio
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_server import DevSafetyMCP


async def example_workflow():
    """
    Demonstrate a complete development workflow using the MCP server.
    
    This example shows:
    1. Creating a sandbox for safe development
    2. Saving session state when taking a break
    3. Loading session state to continue work
    4. Monitoring activity
    5. Syncing approved changes back to main
    """
    
    print("Development Safety MCP Server - Example Workflow")
    print("=" * 60)
    
    # Initialize the MCP server
    server = DevSafetyMCP()
    print("✅ MCP Server initialized")
    
    # Create a temporary project for this example
    temp_dir = tempfile.mkdtemp()
    project_path = create_example_project(temp_dir)
    print(f"✅ Example project created at: {project_path}")
    
    try:
        # Step 1: Create a sandbox for safe development
        print("\n🏗️ Step 1: Creating Development Sandbox")
        print("-" * 40)
        
        # Get the create_sandbox tool from the server
        tools = server.server._tools
        create_sandbox = tools["create_sandbox"]
        
        sandbox_result = await create_sandbox(project_path)
        
        if sandbox_result["status"] == "created":
            sandbox_path = sandbox_result["sandbox_path"]
            print(f"✅ Sandbox created: {sandbox_path}")
            print(f"   Original project: {sandbox_result['original_path']}")
        else:
            print(f"❌ Failed to create sandbox: {sandbox_result.get('error', 'Unknown error')}")
            return
        
        # Step 2: Simulate some development work
        print("\n💻 Step 2: Simulating Development Work")
        print("-" * 40)
        
        # Add a new feature file
        new_feature_path = os.path.join(sandbox_path, "src", "new_feature.py")
        os.makedirs(os.path.dirname(new_feature_path), exist_ok=True)
        
        with open(new_feature_path, "w") as f:
            f.write("""
# New Feature Implementation
class AwesomeFeature:
    def __init__(self):
        self.name = "Awesome Feature"
        self.version = "1.0.0"
    
    def execute(self):
        print(f"Executing {self.name} v{self.version}")
        return {"status": "success", "message": "Feature executed successfully"}

if __name__ == "__main__":
    feature = AwesomeFeature()
    feature.execute()
""")
        
        print("✅ Added new feature: src/new_feature.py")
        
        # Step 3: Save session state (taking a break)
        print("\n💾 Step 3: Saving Session State")
        print("-" * 40)
        
        save_session = tools["save_session_state"]
        session_result = await save_session(
            operation="Implementing awesome new feature",
            current_step="Created new_feature.py with basic structure",
            next_steps=[
                "Add unit tests for AwesomeFeature",
                "Integrate with main application",
                "Update documentation",
                "Create API endpoints"
            ],
            sandbox_path=sandbox_path,
            context={
                "feature_name": "Awesome Feature",
                "complexity": "medium",
                "estimated_time": "4 hours",
                "dependencies": ["requests", "asyncio"],
                "team_member": "developer",
                "priority": "high"
            }
        )
        
        if session_result["status"] == "saved":
            print("✅ Session state saved successfully")
            print(f"   Session file: {session_result['session_file']}")
        else:
            print(f"❌ Failed to save session: {session_result.get('error', 'Unknown error')}")
        
        # Step 4: Load session state (continuing work)
        print("\n🔄 Step 4: Loading Session State")
        print("-" * 40)
        
        load_session = tools["load_session_state"]
        load_result = await load_session()
        
        if load_result["status"] == "loaded":
            print("✅ Session state loaded successfully")
            print("\n📋 Continuation Prompt:")
            print(load_result["continuation_prompt"])
        else:
            print(f"❌ Failed to load session: {load_result.get('error', 'No previous session')}")
        
        # Step 5: Check activity
        print("\n📊 Step 5: Checking Development Activity")
        print("-" * 40)
        
        check_activity = tools["check_activity"]
        activity_result = await check_activity(sandbox_path, minutes=1)
        
        if activity_result["status"] == "success":
            print(f"✅ Activity check completed")
            print(f"   Active development: {activity_result['active']}")
            print(f"   Files changed: {len(activity_result['recent_files'])}")
            
            for suggestion in activity_result["suggestions"]:
                print(f"   💡 {suggestion}")
        
        # Step 6: Sync changes to main (after approval)
        print("\n🔄 Step 6: Syncing Approved Changes")
        print("-" * 40)
        
        # In a real scenario, you'd review changes before syncing
        print("   📝 In a real workflow, you would:")
        print("   1. Review all changes in the sandbox")
        print("   2. Test thoroughly")
        print("   3. Get approval from team/code review")
        print("   4. Then sync specific approved files")
        
        sync_to_main = tools["sync_to_main"]
        sync_result = await sync_to_main(
            sandbox_path=sandbox_path,
            main_path=project_path,
            files=["src/new_feature.py"]  # Only sync specific approved files
        )
        
        if sync_result["status"] == "synced":
            print("✅ Changes synced successfully")
            print(f"   Files synced: {len(sync_result['files_synced'])}")
            print(f"   Backup created: {sync_result['backup_created']}")
            
            for file in sync_result["files_synced"]:
                print(f"   ✅ {file}")
        else:
            print(f"❌ Failed to sync: {sync_result.get('error', 'Unknown error')}")
        
        print("\n🎉 Workflow completed successfully!")
        print("\n📝 Summary:")
        print("   • Created isolated sandbox for safe development")
        print("   • Implemented new feature in sandbox")
        print("   • Saved session state for later continuation")
        print("   • Loaded session state with continuation prompt")
        print("   • Monitored development activity")
        print("   • Synced approved changes back to main project")
        print("\n💡 Benefits achieved:")
        print("   • Main project never at risk during development")
        print("   • Complete session continuity across breaks")
        print("   • Clear tracking of progress and next steps")
        print("   • Safe synchronization of only approved changes")
        
    finally:
        # Clean up
        print(f"\n🧹 Cleaning up temporary files...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("✅ Cleanup completed")


def create_example_project(temp_dir: str) -> str:
    """Create an example project for the workflow demonstration"""
    
    project_path = os.path.join(temp_dir, "example_project")
    project = Path(project_path)
    project.mkdir(parents=True)
    
    # Create basic project structure
    (project / "src").mkdir()
    
    # main.py
    with open(project / "src" / "main.py", "w") as f:
        f.write("""
#!/usr/bin/env python3
\"\"\"
Example Project - Main Application
\"\"\"

def main():
    print("Welcome to the Example Project!")
    print("This is a sample application for demonstrating")
    print("the Development Safety MCP Server workflow.")

if __name__ == "__main__":
    main()
""")
    
    # requirements.txt
    with open(project / "requirements.txt", "w") as f:
        f.write("""
requests>=2.25.1
asyncio-extras>=1.3.2
pytest>=6.2.4
""")
    
    # README.md
    with open(project / "README.md", "w") as f:
        f.write("""
# Example Project

This is an example project used to demonstrate the Development Safety MCP Server.

## Features

- Basic Python application structure
- Requirements management
- Ready for MCP server workflow demonstration

## Usage

1. Run the main application: `python src/main.py`
2. Use with MCP server for safe development workflows
""")
    
    return str(project_path)


if __name__ == "__main__":
    asyncio.run(example_workflow())