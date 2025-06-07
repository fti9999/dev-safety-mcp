"""
Session Detector - Interface-Agnostic Detection

This module provides high-level session detection that works across
different LLM interfaces by coordinating interface-specific handlers.

From original handoff document Phase 2.1 - Interface Detection
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from .interface_handlers.claude_desktop import ClaudeDesktopHandler


class SessionDetector:
    """
    High-level session state detector that coordinates multiple interface handlers
    
    Automatically detects which LLM interface is active and uses the appropriate
    handler for session state detection and automation.
    """
    
    def __init__(self):
        """Initialize session detector with all interface handlers"""
        self.handlers = {
            "claude_desktop": ClaudeDesktopHandler(),
            # Future handlers will be added here:
            # "cursor": CursorHandler(),
            # "vscode": VSCodeHandler(), 
            # "web_llm": WebLLMHandler()
        }
        
        self.active_interface = None
        self.last_detection = None
        
        print("[DETECTOR] Session detector initialized with handlers:", list(self.handlers.keys()))
    
    async def detect_active_interface(self) -> Optional[str]:
        """
        Detect which LLM interface is currently active
        
        Returns:
            Interface name if detected, None if no interface found
        """
        try:
            # Check each interface handler to see which one detects an active session
            for interface_name, handler in self.handlers.items():
                try:
                    # Try to detect session state for this interface
                    if hasattr(handler, 'detect_session_state'):
                        state = await handler.detect_session_state()
                        
                        # If we successfully detected a window/session, this is the active interface
                        if state.get("status") not in ["window_not_found", "error", "screenshot_failed"]:
                            print(f"[DETECTOR] Active interface detected: {interface_name}")
                            self.active_interface = interface_name
                            return interface_name
                            
                except Exception as e:
                    print(f"[DETECTOR] Error checking {interface_name}: {e}")
                    continue
            
            print("[DETECTOR] No active interface detected")
            self.active_interface = None
            return None
            
        except Exception as e:
            print(f"[ERROR] Interface detection failed: {e}")
            return None
    
    async def get_session_state(self, interface_name: str = None) -> Dict[str, Any]:
        """
        Get current session state for specified interface or active interface
        
        Args:
            interface_name: Specific interface to check, or None for active interface
            
        Returns:
            Session state information
        """
        try:
            # Use specified interface or detect active one
            if interface_name:
                target_interface = interface_name
            else:
                target_interface = await self.detect_active_interface()
            
            if not target_interface:
                return {
                    "status": "no_interface_detected",
                    "confidence": 1.0,
                    "evidence": "No active LLM interface found",
                    "recommended_action": "launch_interface",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Get session state from the appropriate handler
            handler = self.handlers.get(target_interface)
            if not handler:
                return {
                    "status": "handler_not_found",
                    "confidence": 1.0,
                    "evidence": f"No handler available for {target_interface}",
                    "recommended_action": "manual_review",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Get state from handler
            state = await handler.detect_session_state()
            
            # Add metadata
            state["interface"] = target_interface
            state["timestamp"] = datetime.now().isoformat()
            state["detector"] = "session_detector"
            
            self.last_detection = state
            return state
            
        except Exception as e:
            return {
                "status": "error",
                "confidence": 0.0,
                "evidence": f"Session state detection failed: {str(e)}",
                "recommended_action": "retry",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def take_action(self, action: str, interface_name: str = None) -> Dict[str, Any]:
        """
        Take an action on the specified interface
        
        Args:
            action: Action to take ("continue", "new_session", "send_message", etc.)
            interface_name: Interface to act on, or None for active interface
            
        Returns:
            Result of the action
        """
        try:
            # Determine target interface
            if interface_name:
                target_interface = interface_name
            else:
                target_interface = self.active_interface or await self.detect_active_interface()
            
            if not target_interface:
                return {
                    "success": False,
                    "error": "No active interface found",
                    "action": action
                }
            
            # Get handler
            handler = self.handlers.get(target_interface)
            if not handler:
                return {
                    "success": False,
                    "error": f"No handler for {target_interface}",
                    "action": action
                }
            
            # Execute action based on type
            result = {"success": False, "action": action, "interface": target_interface}
            
            if action == "continue" and hasattr(handler, 'click_continue'):
                success = await handler.click_continue()
                result["success"] = success
                result["message"] = "Continue button clicked" if success else "Continue button click failed"
                
            elif action == "new_session" and hasattr(handler, 'start_new_conversation'):
                success = await handler.start_new_conversation()
                result["success"] = success
                result["message"] = "New conversation started" if success else "New conversation failed"
                
            elif action.startswith("send_message:") and hasattr(handler, 'send_message'):
                message = action[13:]  # Remove "send_message:" prefix
                success = await handler.send_message(message)
                result["success"] = success
                result["message"] = f"Message sent: {message[:50]}..." if success else "Message send failed"
                
            else:
                result["error"] = f"Action '{action}' not supported for {target_interface}"
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action": action
            }
    
    def get_last_detection(self) -> Optional[Dict[str, Any]]:
        """Get the most recent session detection result"""
        return self.last_detection
    
    def get_active_interface(self) -> Optional[str]:
        """Get the currently active interface name"""
        return self.active_interface
    
    def get_available_handlers(self) -> list:
        """Get list of available interface handlers"""
        return list(self.handlers.keys())
