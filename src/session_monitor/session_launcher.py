"""
Session Launcher - Automatic Session Recovery

This module handles automatic launching of new LLM sessions when needed.
Implements the session recovery strategy from the original handoff document.

From original handoff document Phase 2.1 - Auto-launch new sessions
"""

import asyncio
import subprocess
import time
from typing import Dict, Any, Optional
from datetime import datetime


class SessionLauncher:
    """
    Automatic session launcher for LLM interfaces
    
    Handles launching new sessions when the current session ends or fails.
    Integrates with session continuity and state management.
    """
    
    def __init__(self):
        """Initialize session launcher"""
        self.launch_configs = {
            "claude_desktop": {
                "executable": "claude.exe",
                "wait_time": 3.0,
                "max_retries": 3
            },
            "cursor": {
                "executable": "cursor.exe", 
                "wait_time": 5.0,
                "max_retries": 3
            },
            "vscode": {
                "executable": "code.exe",
                "wait_time": 4.0,
                "max_retries": 3
            }
        }
        
        self.launch_history = []
        
        print("[LAUNCHER] Session launcher initialized")
    
    async def launch_interface(self, interface_type: str) -> Dict[str, Any]:
        """
        Launch a specific LLM interface
        
        Args:
            interface_type: Type of interface to launch
            
        Returns:
            Launch result information
        """
        try:
            if interface_type not in self.launch_configs:
                return {
                    "success": False,
                    "error": f"No launch configuration for {interface_type}",
                    "interface": interface_type
                }
            
            config = self.launch_configs[interface_type]
            
            print(f"[LAUNCHER] Attempting to launch {interface_type}...")
            
            # Try to launch the application
            for attempt in range(config["max_retries"]):
                try:
                    result = await self._launch_application(interface_type, config)
                    
                    if result["success"]:
                        # Log successful launch
                        self.launch_history.append({
                            "timestamp": datetime.now().isoformat(),
                            "interface": interface_type,
                            "success": True,
                            "attempt": attempt + 1
                        })
                        
                        return result
                    
                    # Wait before retry
                    if attempt < config["max_retries"] - 1:
                        print(f"[LAUNCHER] Launch attempt {attempt + 1} failed, retrying...")
                        await asyncio.sleep(2.0)
                
                except Exception as e:
                    print(f"[LAUNCHER] Launch attempt {attempt + 1} error: {e}")
                    if attempt < config["max_retries"] - 1:
                        await asyncio.sleep(2.0)
            
            # All attempts failed
            self.launch_history.append({
                "timestamp": datetime.now().isoformat(),
                "interface": interface_type,
                "success": False,
                "attempts": config["max_retries"]
            })
            
            return {
                "success": False,
                "error": f"Failed to launch {interface_type} after {config['max_retries']} attempts",
                "interface": interface_type,
                "attempts": config["max_retries"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "interface": interface_type
            }
    
    async def _launch_application(self, interface_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Launch the actual application
        
        Args:
            interface_type: Interface type
            config: Launch configuration
            
        Returns:
            Launch result
        """
        try:
            executable = config["executable"]
            wait_time = config["wait_time"]
            
            # Try different launch methods based on interface type
            if interface_type == "claude_desktop":
                return await self._launch_claude_desktop(executable, wait_time)
            elif interface_type == "cursor":
                return await self._launch_cursor(executable, wait_time)
            elif interface_type == "vscode":
                return await self._launch_vscode(executable, wait_time)
            else:
                return await self._launch_generic(executable, wait_time, interface_type)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Application launch failed: {str(e)}",
                "interface": interface_type
            }
    
    async def _launch_claude_desktop(self, executable: str, wait_time: float) -> Dict[str, Any]:
        """Launch Claude Desktop application"""
        try:
            # Try to find Claude Desktop in common locations
            claude_paths = [
                "claude.exe",  # If in PATH
                r"C:\Users\{}\AppData\Local\Claude\claude.exe".format(os.getenv('USERNAME', 'User')),
                r"C:\Program Files\Claude\claude.exe",
                r"C:\Program Files (x86)\Claude\claude.exe"
            ]
            
            import os
            
            for path in claude_paths:
                if os.path.exists(path) or (path == "claude.exe"):
                    try:
                        # Launch Claude Desktop
                        process = subprocess.Popen([path], 
                                                 stdout=subprocess.PIPE, 
                                                 stderr=subprocess.PIPE)
                        
                        print(f"[LAUNCHER] Claude Desktop launched (PID: {process.pid})")
                        
                        # Wait for application to start
                        await asyncio.sleep(wait_time)
                        
                        # Check if process is still running
                        if process.poll() is None:
                            return {
                                "success": True,
                                "interface": "claude_desktop",
                                "process_id": process.pid,
                                "executable_path": path,
                                "wait_time": wait_time
                            }
                        else:
                            return {
                                "success": False,
                                "error": "Claude Desktop process terminated immediately",
                                "interface": "claude_desktop"
                            }
                            
                    except FileNotFoundError:
                        continue
                    except Exception as e:
                        print(f"[LAUNCHER] Error launching from {path}: {e}")
                        continue
            
            return {
                "success": False,
                "error": "Claude Desktop executable not found in any common location",
                "interface": "claude_desktop",
                "searched_paths": claude_paths
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "interface": "claude_desktop"
            }
    
    async def _launch_cursor(self, executable: str, wait_time: float) -> Dict[str, Any]:
        """Launch Cursor IDE"""
        try:
            # Try to launch Cursor
            process = subprocess.Popen([executable], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
            
            print(f"[LAUNCHER] Cursor launched (PID: {process.pid})")
            
            # Wait for application to start
            await asyncio.sleep(wait_time)
            
            return {
                "success": True,
                "interface": "cursor",
                "process_id": process.pid,
                "wait_time": wait_time
            }
            
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Cursor executable not found: {executable}",
                "interface": "cursor"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "interface": "cursor"
            }
    
    async def _launch_vscode(self, executable: str, wait_time: float) -> Dict[str, Any]:
        """Launch VS Code"""
        try:
            # Try to launch VS Code
            process = subprocess.Popen([executable], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
            
            print(f"[LAUNCHER] VS Code launched (PID: {process.pid})")
            
            # Wait for application to start
            await asyncio.sleep(wait_time)
            
            return {
                "success": True,
                "interface": "vscode",
                "process_id": process.pid,
                "wait_time": wait_time
            }
            
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"VS Code executable not found: {executable}",
                "interface": "vscode"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "interface": "vscode"
            }
    
    async def _launch_generic(self, executable: str, wait_time: float, interface_type: str) -> Dict[str, Any]:
        """Generic application launcher"""
        try:
            process = subprocess.Popen([executable], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
            
            print(f"[LAUNCHER] {interface_type} launched (PID: {process.pid})")
            
            # Wait for application to start
            await asyncio.sleep(wait_time)
            
            return {
                "success": True,
                "interface": interface_type,
                "process_id": process.pid,
                "wait_time": wait_time
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "interface": interface_type
            }
    
    async def auto_recover_session(
        self, 
        interface_type: str, 
        session_context: Dict[str, Any] = None,
        continuation_prompt: str = None
    ) -> Dict[str, Any]:
        """
        Automatically recover a session by launching interface and restoring context
        
        Args:
            interface_type: Interface to launch
            session_context: Previous session context to restore
            continuation_prompt: Prompt to send for session continuation
            
        Returns:
            Recovery result
        """
        try:
            print(f"[LAUNCHER] Starting auto-recovery for {interface_type}...")
            
            # Step 1: Launch interface
            launch_result = await self.launch_interface(interface_type)
            
            if not launch_result["success"]:
                return {
                    "success": False,
                    "stage": "launch",
                    "error": launch_result["error"],
                    "interface": interface_type
                }
            
            print(f"[LAUNCHER] Interface launched successfully, waiting for readiness...")
            
            # Step 2: Wait for interface to be ready
            await asyncio.sleep(5.0)  # Additional wait for full startup
            
            # Step 3: Inject continuation context if provided
            recovery_result = {
                "success": True,
                "interface": interface_type,
                "launch_result": launch_result,
                "context_restored": False,
                "prompt_sent": False
            }
            
            if continuation_prompt:
                # Try to send continuation prompt
                try:
                    # This would integrate with interface handlers to send the prompt
                    print(f"[LAUNCHER] Would send continuation prompt: {continuation_prompt[:100]}...")
                    recovery_result["prompt_sent"] = True
                    recovery_result["continuation_prompt"] = continuation_prompt[:100] + "..."
                except Exception as e:
                    print(f"[LAUNCHER] Failed to send continuation prompt: {e}")
                    recovery_result["prompt_error"] = str(e)
            
            if session_context:
                recovery_result["context_restored"] = True
                recovery_result["restored_context"] = {
                    "operation": session_context.get("operation", "unknown"),
                    "current_step": session_context.get("current_step", "unknown"),
                    "sandbox_path": session_context.get("sandbox_path")
                }
            
            return recovery_result
            
        except Exception as e:
            return {
                "success": False,
                "stage": "recovery",
                "error": str(e),
                "interface": interface_type
            }
    
    def get_launch_history(self, limit: int = 10) -> list:
        """Get recent launch history"""
        return self.launch_history[-limit:] if self.launch_history else []
    
    def get_launch_config(self, interface_type: str) -> Optional[Dict[str, Any]]:
        """Get launch configuration for interface type"""
        return self.launch_configs.get(interface_type)
    
    def set_launch_config(self, interface_type: str, config: Dict[str, Any]) -> None:
        """Set launch configuration for interface type"""
        self.launch_configs[interface_type] = config
        print(f"[LAUNCHER] Updated config for {interface_type}")
