"""
Development Safety MCP Server

A Model Control Protocol server that provides session continuity and sandbox safety
for LLM-assisted development workflows.

CRITICAL SAFETY FEATURES:
- Automatic git commits during session saves
- Periodic auto-commits during development  
- Manual progress commits to prevent work loss
- Complete session state preservation
"""

__version__ = "0.2.0"
__author__ = "Dev Safety Team"
__email__ = "dev@example.com"

from .mcp_server import DevSafetyMCP
from .session_manager import SessionManager
from .sandbox_manager import SandboxManager
from .activity_monitor import SimpleActivityMonitor

__all__ = [
    "DevSafetyMCP",
    "SessionManager", 
    "SandboxManager",
    "SimpleActivityMonitor"
]