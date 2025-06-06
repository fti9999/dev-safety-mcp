"""
Basic functionality tests for Development Safety MCP Server

Tests core functionality of the MCP server components.
"""

import pytest
import asyncio
import tempfile
import os
import shutil
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_server import DevSafetyMCP
from session_manager import SessionManager
from sandbox_manager import SandboxManager
from activity_monitor import SimpleActivityMonitor


class TestSessionManager:
    """Test session management functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.session_manager = SessionManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_session(self):
        """Test saving and loading session state"""
        session_data = {
            "operation": "Test operation",
            "current_step": "Testing save/load",
            "next_steps": ["Verify data", "Clean up"],
            "sandbox_path": "/test/sandbox",
            "context": {"test": True}
        }
        
        # Save session
        saved_file = self.session_manager.save_session(session_data)
        assert os.path.exists(saved_file)
        
        # Load session
        loaded_data = self.session_manager.load_latest_session()
        assert loaded_data is not None
        assert loaded_data["operation"] == session_data["operation"]
        assert loaded_data["current_step"] == session_data["current_step"]
        assert "session_id" in loaded_data
        assert "saved_at" in loaded_data
    
    def test_continuation_prompt(self):
        """Test continuation prompt generation"""
        session_data = {
            "operation": "Add feature",
            "current_step": "Created files",
            "next_steps": ["Add tests", "Update docs"],
            "sandbox_path": "/test/sandbox",
            "context": {"feature": "payment"}
        }
        
        prompt = self.session_manager.create_continuation_prompt(session_data)
        assert "Add feature" in prompt
        assert "Created files" in prompt
        assert "Add tests" in prompt
        assert "Update docs" in prompt


class TestSandboxManager:
    """Test sandbox management functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.sandbox_manager = SandboxManager(self.temp_dir)
        
        # Create a test project
        self.test_project = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.test_project)
        
        # Add some test files
        with open(os.path.join(self.test_project, "main.py"), "w") as f:
            f.write("print('Hello, World!')")
        
        with open(os.path.join(self.test_project, "README.md"), "w") as f:
            f.write("# Test Project")
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)    
    def test_create_sandbox(self):
        """Test sandbox creation"""
        result = self.sandbox_manager.create_sandbox(self.test_project)
        
        assert result["status"] == "success"
        assert "sandbox_path" in result
        assert os.path.exists(result["sandbox_path"])
        
        # Check files were copied
        sandbox_main = os.path.join(result["sandbox_path"], "main.py")
        sandbox_readme = os.path.join(result["sandbox_path"], "README.md")
        assert os.path.exists(sandbox_main)
        assert os.path.exists(sandbox_readme)
    
    def test_list_sandboxes(self):
        """Test listing sandboxes"""
        # Initially no sandboxes
        sandboxes = self.sandbox_manager.list_sandboxes()
        assert len(sandboxes) == 0
        
        # Create a sandbox
        self.sandbox_manager.create_sandbox(self.test_project, "test-sandbox")
        
        # Should now have one sandbox
        sandboxes = self.sandbox_manager.list_sandboxes()
        assert len(sandboxes) == 1
        assert sandboxes[0]["name"] == "test-sandbox"


class TestActivityMonitor:
    """Test activity monitoring functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.test_file = os.path.join(self.temp_dir, "test.py")
        with open(self.test_file, "w") as f:
            f.write("print('test')")
        
        self.monitor = SimpleActivityMonitor(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detect_project_type(self):
        """Test project type detection"""
        # Test Python project
        with open(os.path.join(self.temp_dir, "requirements.txt"), "w") as f:
            f.write("requests==2.25.1")
        
        project_type = self.monitor.detect_project_type()
        assert project_type == "python"
    
    def test_check_recent_activity(self):
        """Test activity detection"""
        # Should detect recent activity since file was just created
        result = self.monitor.check_recent_activity(minutes=1)
        assert result["active"] == True
        assert len(result["recent_files"]) > 0
        
        # Should not detect activity from long ago
        result = self.monitor.check_recent_activity(minutes=0)
        assert result["active"] == False


@pytest.mark.asyncio
class TestMCPServer:
    """Test MCP server functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test project
        self.test_project = os.path.join(self.temp_dir, "test_project")
        os.makedirs(self.test_project)
        with open(os.path.join(self.test_project, "app.py"), "w") as f:
            f.write("# Test app")
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def test_server_initialization(self):
        """Test that MCP server initializes correctly"""
        server = DevSafetyMCP()
        assert server.server.name == "dev-safety"
        assert hasattr(server, "session_manager")


if __name__ == "__main__":
    pytest.main([__file__])