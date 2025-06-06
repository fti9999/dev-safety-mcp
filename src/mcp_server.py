"""
Main MCP Server Implementation for Development Safety System

This module implements the core MCP server with tools for:
- Sandbox creation and management
- Session state persistence  
- Activity monitoring
- Safe synchronization of changes
"""

from mcp.server import FastMCP
import asyncio
import json
import os
import shutil
import subprocess
import time
import glob
import threading
import signal
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from session_manager import SessionManager
from sandbox_manager import SandboxManager
from activity_monitor import SimpleActivityMonitor
from utils import ensure_directory, validate_path, create_backup


class DevSafetyMCP:
    """Main MCP server class for development safety tools."""
    
    def __init__(self):
        self.server = FastMCP("dev-safety")
        self.config_dir = "~/.dev-safety"
        self.session_manager = SessionManager(self.config_dir)
        self.ensure_config_dir()
        self.register_tools()
        
        # MONITORING ENHANCEMENT: Initialize status monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        self.server_pid = os.getpid()
        self.startup_time = datetime.now()
        self.status_lock = threading.Lock()  # Prevent concurrent file writes
        self.start_status_monitoring()
        
    def ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        config_path = os.path.expanduser(self.config_dir)
        os.makedirs(config_path, exist_ok=True)
        
    def register_tools(self):
        """Register all MCP tools with the server"""
        
        @self.server.tool("create_sandbox")
        async def create_sandbox(
            project_path: str,
            sandbox_name: str = None
        ) -> Dict[str, Any]:
            """
            Create isolated sandbox for safe development
            
            SIMPLE IMPLEMENTATION:
            1. Generate sandbox name if not provided
            2. Copy project to {project_path}-sandbox-{name}
            3. Start git branch in sandbox
            4. Return sandbox info
            """
            try:
                if not sandbox_name:
                    sandbox_name = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                
                # Validate project path exists
                if not os.path.exists(project_path):
                    return {
                        "status": "error",
                        "error": f"Project path does not exist: {project_path}"
                    }
                
                sandbox_path = f"{project_path}-sandbox-{sandbox_name}"
                
                # Copy project (simple shell command)
                shutil.copytree(project_path, sandbox_path, 
                              ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.git'))
                
                # Initialize git branch
                original_dir = os.getcwd()
                try:
                    os.chdir(sandbox_path)
                    
                    # Initialize git if not already a repo
                    if not os.path.exists('.git'):
                        subprocess.run(['git', 'init'], check=True, capture_output=True)
                        subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
                        subprocess.run(['git', 'commit', '-m', 'Initial sandbox commit'], 
                                     check=True, capture_output=True)
                    
                    # Create sandbox branch
                    subprocess.run(['git', 'checkout', '-b', f'sandbox/{sandbox_name}'], 
                                 check=True, capture_output=True)
                finally:
                    os.chdir(original_dir)
                
                return {
                    "sandbox_path": sandbox_path,
                    "sandbox_name": sandbox_name,
                    "original_path": project_path,
                    "status": "created",
                    "message": f"Sandbox created successfully at {sandbox_path}"
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e)
                }

        @self.server.tool("save_session_state") 
        async def save_session_state(
            operation: str,
            current_step: str,
            next_steps: List[str],
            sandbox_path: str,
            context: Dict[str, Any]
        ) -> Dict[str, Any]:
            """
            Save session state for continuation
            
            CRITICAL ENHANCEMENT:
            1. COMMIT ALL CHANGES before saving session
            2. Create session state object
            3. Save to ~/.dev-safety/last_session.json
            4. Also save to project-specific file
            5. Return confirmation with commit hash
            """
            try:
                # CRITICAL: Auto-commit all changes before saving session
                commit_result = self._auto_commit_changes(sandbox_path, f"Session save: {current_step}")
                
                session_state = {
                    "timestamp": datetime.now().isoformat(),
                    "operation": operation,
                    "current_step": current_step,
                    "next_steps": next_steps,
                    "sandbox_path": sandbox_path,
                    "context": context,
                    "app_status": "functional",
                    "commit_hash": commit_result.get("commit_hash"),
                    "files_committed": commit_result.get("files_committed", [])
                }
                
                # Use session manager to save
                saved_file = self.session_manager.save_session(session_state)
                
                return {
                    "status": "saved", 
                    "session_file": saved_file,
                    "commit_hash": commit_result.get("commit_hash"),
                    "files_committed": commit_result.get("files_committed", []),
                    "message": f"Session state saved with commit {commit_result.get('commit_hash', 'N/A')}"
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e)
                }

        @self.server.tool("load_session_state")
        async def load_session_state() -> Dict[str, Any]:
            """
            Load most recent session state
            
            SIMPLE IMPLEMENTATION:
            1. Read ~/.dev-safety/last_session.json
            2. Return session data
            3. Include continuation prompt
            """
            try:
                session_data = self.session_manager.load_latest_session()
                
                if not session_data:
                    return {"status": "no_previous_session"}
                
                # Create continuation prompt
                continuation_prompt = self.session_manager.create_continuation_prompt(session_data)
                
                return {
                    "status": "loaded",
                    "session_data": session_data,
                    "continuation_prompt": continuation_prompt
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e)
                }

        @self.server.tool("check_activity")
        async def check_activity(sandbox_path: str, minutes: int = 10) -> Dict[str, Any]:
            """
            Check if there has been recent file activity
            
            ENHANCED IMPLEMENTATION:
            1. Check file modification times in sandbox
            2. Return whether there's been activity in last X minutes
            3. CRITICAL: Auto-commit if significant changes detected
            4. Suggest saving state if no activity
            """
            try:
                if not os.path.exists(sandbox_path):
                    return {
                        "status": "error",
                        "error": f"Sandbox path does not exist: {sandbox_path}"
                    }
                
                monitor = SimpleActivityMonitor(sandbox_path)
                activity_result = monitor.check_recent_activity(minutes)
                
                # CRITICAL ENHANCEMENT: Auto-commit if there are uncommitted changes
                commit_result = None
                if activity_result.get("active", False):
                    # Check if there are uncommitted changes
                    original_dir = os.getcwd()
                    try:
                        os.chdir(sandbox_path)
                        status_check = subprocess.run(['git', 'status', '--porcelain'], 
                                                    capture_output=True, text=True)
                        if status_check.stdout.strip():
                            # There are uncommitted changes - auto-commit them
                            commit_result = self._auto_commit_changes(
                                sandbox_path, 
                                f"Auto-commit during activity check - {len(activity_result.get('recent_files', []))} files changed"
                            )
                    except:
                        pass  # Git operations are nice-to-have
                    finally:
                        os.chdir(original_dir)
                
                result = {
                    "status": "success",
                    **activity_result
                }
                
                # Add commit information if a commit was made
                if commit_result and commit_result.get("status") == "committed":
                    result["auto_commit"] = commit_result
                    result["suggestions"].insert(0, f"Auto-committed changes (commit: {commit_result.get('commit_hash')})")
                
                return result
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e)
                }

        @self.server.tool("sync_to_main")
        async def sync_to_main(
            sandbox_path: str,
            main_path: str,
            files: List[str] = None
        ) -> Dict[str, Any]:
            """
            Copy approved changes from sandbox to main
            
            SIMPLE IMPLEMENTATION:
            1. If no files specified, copy all changed files
            2. Create backup of main files first
            3. Copy files from sandbox to main
            4. Return sync results
            """
            try:
                if not os.path.exists(sandbox_path):
                    return {
                        "status": "error",
                        "error": f"Sandbox path does not exist: {sandbox_path}"
                    }
                
                if not os.path.exists(main_path):
                    return {
                        "status": "error", 
                        "error": f"Main path does not exist: {main_path}"
                    }
                
                if files is None:
                    # CRITICAL: Commit all changes before detecting what to sync
                    commit_result = self._auto_commit_changes(sandbox_path, "Pre-sync auto-commit")
                    
                    # Get all changed files from git
                    original_dir = os.getcwd()
                    try:
                        os.chdir(sandbox_path)
                        result = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1'], 
                                              capture_output=True, text=True)
                        files = result.stdout.strip().split('\n') if result.stdout.strip() else []
                    except:
                        # If git fails, fallback to scanning for recent changes
                        files = []
                        for pattern in ["**/*.py", "**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx"]:
                            files.extend(glob.glob(os.path.join(sandbox_path, pattern), recursive=True))
                        files = [os.path.relpath(f, sandbox_path) for f in files]
                    finally:
                        os.chdir(original_dir)
                
                synced_files = []
                backup_files = []
                
                for file in files:
                    if not file or file.strip() == '':
                        continue
                        
                    sandbox_file = os.path.join(sandbox_path, file)
                    main_file = os.path.join(main_path, file)
                    
                    if os.path.exists(sandbox_file):
                        # Create backup
                        if os.path.exists(main_file):
                            backup_file = f"{main_file}.backup.{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                            shutil.copy2(main_file, backup_file)
                            backup_files.append(backup_file)
                        
                        # Copy from sandbox to main
                        os.makedirs(os.path.dirname(main_file), exist_ok=True)
                        shutil.copy2(sandbox_file, main_file)
                        synced_files.append(file)
                
                return {
                    "status": "synced",
                    "files_synced": synced_files,
                    "backup_files": backup_files,
                    "backup_created": len(backup_files) > 0,
                    "message": f"Successfully synced {len(synced_files)} files"
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e)
                }

        @self.server.tool("commit_progress")
        async def commit_progress(
            sandbox_path: str,
            message: str = "Progress checkpoint"
        ) -> Dict[str, Any]:
            """
            CRITICAL SAFETY TOOL: Manually commit current progress
            
            Use this tool to save incremental progress during development.
            Prevents work loss at session boundaries.
            
            Args:
                sandbox_path: Path to the sandbox
                message: Commit message describing the progress
            """
            try:
                if not os.path.exists(sandbox_path):
                    return {
                        "status": "error",
                        "error": f"Sandbox path does not exist: {sandbox_path}"
                    }
                
                commit_result = self._auto_commit_changes(sandbox_path, message)
                
                if commit_result.get("status") == "committed":
                    return {
                        "status": "success",
                        "commit_hash": commit_result.get("commit_hash"),
                        "files_committed": commit_result.get("files_committed", []),
                        "message": f"Progress committed: {commit_result.get('commit_hash')}"
                    }
                elif commit_result.get("status") == "no_changes":
                    return {
                        "status": "no_changes",
                        "commit_hash": commit_result.get("commit_hash"),
                        "message": "No changes to commit - already up to date"
                    }
                else:
                    return {
                        "status": "error",
                        "error": commit_result.get("error", "Commit failed")
                    }
                    
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e)
                }

        @self.server.tool("check_mcp_status")
        async def check_mcp_status() -> Dict[str, Any]:
            """
            Check the current status of the MCP server monitoring system
            
            Returns status file information and server health data.
            """
            try:
                config_path = os.path.expanduser(self.config_dir)
                status_file = os.path.join(config_path, "mcp_status.json")
                
                if not os.path.exists(status_file):
                    return {
                        "status": "no_status_file",
                        "message": "Status file not found - monitoring may not be active"
                    }
                
                with open(status_file, 'r') as f:
                    status_data = json.load(f)
                
                # Calculate how long ago the last heartbeat was
                try:
                    last_heartbeat = datetime.fromisoformat(status_data['last_heartbeat'])
                    time_since_heartbeat = (datetime.now() - last_heartbeat).total_seconds()
                    status_data['seconds_since_heartbeat'] = int(time_since_heartbeat)
                    
                    if time_since_heartbeat > 60:
                        status_data['health'] = "warning"
                        status_data['health_message'] = f"Last heartbeat was {int(time_since_heartbeat)}s ago"
                    else:
                        status_data['health'] = "healthy"
                        status_data['health_message'] = "Recent heartbeat detected"
                        
                except Exception:
                    status_data['health'] = "unknown"
                    status_data['health_message'] = "Could not parse heartbeat time"
                
                return {
                    "status": "success",
                    "monitoring_data": status_data
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e)
                }

    def _auto_commit_changes(self, sandbox_path: str, commit_message: str) -> Dict[str, Any]:
        """
        CRITICAL SAFETY METHOD: Auto-commit all changes in sandbox
        
        This prevents work loss during session boundaries.
        """
        try:
            if not os.path.exists(sandbox_path):
                return {"status": "error", "error": "Sandbox path does not exist"}
            
            original_dir = os.getcwd()
            try:
                os.chdir(sandbox_path)
                
                # Check if there are any changes to commit
                status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                             capture_output=True, text=True)
                
                if not status_result.stdout.strip():
                    # No changes to commit
                    current_commit = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                                  capture_output=True, text=True)
                    return {
                        "status": "no_changes",
                        "commit_hash": current_commit.stdout.strip()[:8],
                        "files_committed": []
                    }
                
                # Get list of changed files
                changed_files = []
                for line in status_result.stdout.strip().split('\n'):
                    if line.strip():
                        status = line[:2]
                        filename = line[3:].strip()
                        changed_files.append(f"{status} {filename}")
                
                # Add all changes
                subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
                
                # Commit with timestamp and message
                full_commit_message = f"{commit_message} - {datetime.now().strftime('%Y%m%d-%H%M%S')}"
                subprocess.run(['git', 'commit', '-m', full_commit_message], 
                             check=True, capture_output=True)
                
                # Get the new commit hash
                commit_result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                             capture_output=True, text=True)
                commit_hash = commit_result.stdout.strip()[:8]
                
                return {
                    "status": "committed",
                    "commit_hash": commit_hash,
                    "files_committed": changed_files,
                    "message": f"Auto-committed {len(changed_files)} changes"
                }
                
            finally:
                os.chdir(original_dir)
                
        except subprocess.CalledProcessError as e:
            return {
                "status": "error", 
                "error": f"Git commit failed: {e}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Auto-commit failed: {e}"
            }

    def start_status_monitoring(self):
        """
        CRITICAL MONITORING FEATURE: Start status file monitoring
        
        Creates heartbeat file every 30 seconds to enable external monitoring.
        Provides startup notification and continuous health status.
        """
        try:
            # Create initial status file
            self.write_status_file("starting", "MCP server initializing...")
            
            # Show startup notification  
            self.show_startup_notification()
            
            # Start background monitoring thread with a small delay
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop, 
                daemon=True
            )
            self.monitoring_thread.start()
            
            # Small delay to let the monitoring thread initialize
            time.sleep(0.1)
            
            # Update status to active
            self.write_status_file("active", "MCP server running normally")
            
            print("[OK] Dev-Safety MCP: Status monitoring started")
            
        except Exception as e:
            print(f"[WARNING] Dev-Safety MCP: Monitoring failed to start: {e}")

    def write_status_file(self, status: str, message: str = ""):
        """Write current status to monitoring file with atomic write and thread safety"""
        with self.status_lock:  # Ensure only one thread writes at a time
            try:
                config_path = os.path.expanduser(self.config_dir)
                status_file = os.path.join(config_path, "mcp_status.json")
                temp_file = status_file + ".tmp"
                
                status_data = {
                    "status": status,
                    "last_heartbeat": datetime.now().isoformat(),
                    "server_pid": self.server_pid,
                    "startup_time": self.startup_time.isoformat(),
                    "tools_registered": 7,  # Updated: now includes check_mcp_status
                    "version": "0.2.0",
                    "message": message,
                    "config_dir": config_path
                }
                
                # Write to temporary file first, then rename (atomic operation)
                with open(temp_file, 'w') as f:
                    json.dump(status_data, f, indent=2)
                
                # Atomic rename
                os.replace(temp_file, status_file)
                    
            except Exception as e:
                # Don't fail the server if status writing fails
                print(f"Warning: Could not write status file: {e}")
                # Clean up temp file if it exists
                try:
                    temp_file = os.path.join(os.path.expanduser(self.config_dir), "mcp_status.json.tmp")
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass

    def show_startup_notification(self):
        """Show startup notification to user"""
        try:
            startup_msg = f"""
================================================================================
*** Development Safety MCP Server Started ***
================================================================================
[OK] Status: Active
[PID] Process ID: {self.server_pid}
[TIME] Started: {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}
[TOOLS] Tools: 7 registered (sandbox, session, activity, sync, commit, status)
[CONFIG] Config: {os.path.expanduser(self.config_dir)}

*** Your development is now protected! ***
================================================================================
"""
            print(startup_msg)
            
            # Try to show desktop notification (optional - requires plyer)
            try:
                import plyer
                plyer.notification.notify(
                    title="Dev-Safety MCP Started",
                    message=f"MCP server active (PID: {self.server_pid})",
                    timeout=5
                )
            except ImportError:
                # plyer not installed - that's fine, console notification is enough
                pass
            except Exception:
                # Notification failed - that's fine too
                pass
                
        except Exception as e:
            print(f"Note: Startup notification error: {e}")

    def _monitoring_loop(self):
        """Background thread for continuous status monitoring"""
        while self.monitoring_active:
            try:
                # Update heartbeat every 30 seconds
                self.write_status_file("active", "Heartbeat - server running normally")
                time.sleep(30)
            except Exception as e:
                print(f"Monitoring loop error: {e}")
                time.sleep(30)  # Continue monitoring even if one update fails

    def stop_monitoring(self):
        """Stop the status monitoring (called on shutdown)"""
        try:
            self.monitoring_active = False
            self.write_status_file("stopping", "MCP server shutting down...")
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=2)
                
            print("[STOP] Dev-Safety MCP: Status monitoring stopped")
            
        except Exception as e:
            print(f"Note: Monitoring cleanup error: {e}")

    async def run_server(self, host: str = "localhost", port: int = 8000):
        """Run the MCP server with proper shutdown handling"""
        try:
            await self.server.run(host=host, port=port)
        finally:
            self.stop_monitoring()


async def main():
    """Main entry point for stdio MCP server"""
    server = DevSafetyMCP()
    
    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n[SIGNAL] Received signal {signum}, shutting down...")
        server.stop_monitoring()
        
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Use FastMCP's built-in stdio support
        await server.server.run_stdio_async()
    finally:
        server.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())