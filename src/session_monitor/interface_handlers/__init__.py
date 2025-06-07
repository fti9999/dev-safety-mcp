"""
Interface Handlers Package

Platform-specific automation handlers for different LLM interfaces.
Each handler implements interface-specific session detection and automation.

Available Handlers:
- claude_desktop: Claude Desktop application automation
- cursor: Cursor IDE with AI chat automation (planned)
- vscode: VS Code with Claude integration (planned)
- web_llm: Web-based LLM interfaces (planned)
"""

from .claude_desktop import ClaudeDesktopHandler

__all__ = [
    'ClaudeDesktopHandler'
]
