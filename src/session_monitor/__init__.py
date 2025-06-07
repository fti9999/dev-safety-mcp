"""
Session Monitor Package

Visual session monitoring system for LLM interfaces.
Implements Phase 2 of the autonomous development safety system.

Components:
- visual_monitor: Core visual monitoring with AI analysis
- session_detector: Interface-agnostic session state detection
- session_launcher: Automatic session recovery and launching
- interface_handlers: Platform-specific automation handlers
"""

from .visual_monitor import VisualSessionMonitor
from .session_detector import SessionDetector  
from .session_launcher import SessionLauncher

__all__ = [
    'VisualSessionMonitor',
    'SessionDetector', 
    'SessionLauncher'
]
