"""
Session Manager for Development Safety System

Handles saving and loading session state for development continuity.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


class SessionManager:
    """Manages session state persistence and loading."""
    
    def __init__(self, config_dir: str = "~/.dev-safety"):
        self.config_dir = os.path.expanduser(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)
        
    def save_session(self, session_data: Dict[str, Any]) -> str:
        """
        Save session state with timestamp
        
        IMPLEMENTATION:
        1. Add timestamp to session data
        2. Save to both global and project locations
        3. Return file path
        """
        session_data["saved_at"] = datetime.now().isoformat()
        session_data["session_id"] = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save to global location (latest session)
        global_file = os.path.join(self.config_dir, "last_session.json")
        with open(global_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        # Save to project-specific location if sandbox path provided
        if "sandbox_path" in session_data and os.path.exists(session_data["sandbox_path"]):
            project_file = os.path.join(session_data["sandbox_path"], ".dev-safety-session.json")
            with open(project_file, 'w') as f:
                json.dump(session_data, f, indent=2)
        
        return global_file
    
    def load_latest_session(self) -> Optional[Dict[str, Any]]:
        """
        Load the most recent session
        
        IMPLEMENTATION:
        1. Read global session file
        2. Validate session data
        3. Return session or None
        """
        global_file = os.path.join(self.config_dir, "last_session.json")
        
        if not os.path.exists(global_file):
            return None
            
        try:
            with open(global_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None    
    def create_continuation_prompt(self, session_data: Dict[str, Any]) -> str:
        """
        Create a prompt for continuing the session
        
        IMPLEMENTATION:
        1. Format session data into clear instructions
        2. Include context and next steps
        3. Return ready-to-use prompt
        """
        return f"""
🔄 CONTINUING PREVIOUS SESSION

Operation: {session_data.get('operation', 'Unknown')}
Last Step: {session_data.get('current_step', 'Unknown')}
Sandbox: {session_data.get('sandbox_path', 'Unknown')}

📋 NEXT STEPS:
{chr(10).join(f"  {i+1}. {step}" for i, step in enumerate(session_data.get('next_steps', [])))}

🎯 CONTEXT:
{json.dumps(session_data.get('context', {}), indent=2)}

💡 INSTRUCTIONS:
1. Continue from where the previous session ended
2. Work in the sandbox environment (main project is safe)
3. Save session state again when you reach a good stopping point
4. Use sync_to_main only after human approval

Ready to continue!
"""

    def get_session_history(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Get list of recent sessions"""
        # For now, just return the latest session
        # In future, could maintain a history file
        latest = self.load_latest_session()
        return [latest] if latest else []
    
    def cleanup_old_sessions(self, days_old: int = 30):
        """Clean up session files older than specified days"""
        # Implementation for cleaning up old session files
        # Could be added in future phases
        pass