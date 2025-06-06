"""
Activity Monitor for Development Safety System

Monitors file activity to suggest when to save session state.
"""

import time
import os
import glob
from typing import Dict, Any
from datetime import datetime, timedelta


class SimpleActivityMonitor:
    """Simple file-based activity detection for development sessions."""
    
    def __init__(self, sandbox_path: str):
        self.sandbox_path = sandbox_path
        self.last_check = datetime.now()
        
    def check_recent_activity(self, minutes: int = 15) -> Dict[str, Any]:
        """
        Simple file-based activity detection
        
        IMPLEMENTATION:
        1. Check modification times of code files
        2. Compare against threshold
        3. Return activity status with helpful suggestions
        """
        now = datetime.now()
        cutoff = now - timedelta(minutes=minutes)
        
        # File patterns to monitor
        patterns = [
            "**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx",
            "**/*.py", "**/*.json", "**/*.md", "**/*.css"
        ]
        
        recent_files = []
        for pattern in patterns:
            files = glob.glob(os.path.join(self.sandbox_path, pattern), recursive=True)
            for file in files:
                # Skip hidden files and common ignore patterns
                if any(part.startswith('.') for part in file.split(os.sep)):
                    continue
                if 'node_modules' in file or '__pycache__' in file:
                    continue
                    
                try:
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file))
                    if mod_time > cutoff:
                        recent_files.append({
                            "file": os.path.relpath(file, self.sandbox_path),
                            "modified": mod_time.isoformat()
                        })
                except OSError:
                    # Skip files that can't be accessed
                    continue
        
        # Generate suggestions based on activity
        suggestions = []
        if not recent_files:
            suggestions.append(f"No file changes in {minutes} minutes")
            suggestions.append("Consider saving session state if you're taking a break")
            suggestions.append("Use save_session_state tool to preserve your progress")
        else:
            suggestions.append(f"Active development detected ({len(recent_files)} files changed)")
            suggestions.append("Continue working or save state when you reach a good stopping point")
        
        return {
            "active": len(recent_files) > 0,
            "recent_files": recent_files,
            "minutes_checked": minutes,
            "suggestions": suggestions,
            "check_time": now.isoformat()
        }    
    def get_file_patterns_for_project_type(self, project_type: str) -> list[str]:
        """Get file patterns based on project type"""
        patterns_map = {
            "react": ["**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx", "**/*.json", "**/*.css"],
            "python": ["**/*.py", "**/*.pyx", "**/*.pyi", "**/*.json", "**/*.yaml", "**/*.yml"],
            "node": ["**/*.js", "**/*.mjs", "**/*.ts", "**/*.json"],
            "generic": ["**/*.*"]
        }
        return patterns_map.get(project_type, patterns_map["generic"])
    
    def detect_project_type(self) -> str:
        """Detect project type based on files present"""
        if os.path.exists(os.path.join(self.sandbox_path, "package.json")):
            package_json = os.path.join(self.sandbox_path, "package.json")
            try:
                import json
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    if "react" in str(data.get("dependencies", {})):
                        return "react"
                    return "node"
            except:
                return "node"
        elif os.path.exists(os.path.join(self.sandbox_path, "requirements.txt")) or \
             os.path.exists(os.path.join(self.sandbox_path, "pyproject.toml")):
            return "python"
        else:
            return "generic"
    
    def should_save_state(self, inactive_minutes: int = 15) -> bool:
        """Determine if session state should be saved based on inactivity"""
        activity = self.check_recent_activity(inactive_minutes)
        return not activity["active"]