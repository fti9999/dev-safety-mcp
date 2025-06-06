"""
Sandbox Manager for Development Safety System

Handles creation, management, and cleanup of development sandboxes.
"""

import os
import shutil
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path


class SandboxManager:
    """Manages development sandboxes for safe isolated development."""
    
    def __init__(self, base_config_dir: str = "~/.dev-safety"):
        self.config_dir = os.path.expanduser(base_config_dir)
        self.sandboxes_file = os.path.join(self.config_dir, "sandboxes.json")
        os.makedirs(self.config_dir, exist_ok=True)
    
    def create_sandbox(self, project_path: str, sandbox_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new sandbox from a project
        
        Args:
            project_path: Path to the original project
            sandbox_name: Optional custom name for the sandbox
            
        Returns:
            Dictionary with sandbox information
        """
        try:
            # Validate project path
            if not os.path.exists(project_path):
                raise ValueError(f"Project path does not exist: {project_path}")
            
            # Generate sandbox name if not provided
            if not sandbox_name:
                timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                sandbox_name = f"session-{timestamp}"
            
            # Create sandbox path
            project_name = os.path.basename(project_path.rstrip(os.sep))
            sandbox_path = f"{project_path}-sandbox-{sandbox_name}"
            
            # Copy project files (excluding common ignore patterns)
            ignore_patterns = shutil.ignore_patterns(
                'node_modules', '__pycache__', '.git', 'venv', '.venv', 
                'dist', 'build', '*.pyc', '.DS_Store'
            )
            
            shutil.copytree(project_path, sandbox_path, ignore=ignore_patterns)
            
            # Initialize git repository
            self._init_git_repo(sandbox_path, sandbox_name)
            
            # Register sandbox
            sandbox_info = {
                "name": sandbox_name,
                "path": sandbox_path,
                "original_path": project_path,
                "created_at": datetime.now().isoformat(),
                "active": True
            }
            
            self._register_sandbox(sandbox_info)
            
            return {
                "status": "success",
                "sandbox_path": sandbox_path,
                "sandbox_name": sandbox_name,
                "original_path": project_path,
                "message": f"Sandbox '{sandbox_name}' created successfully"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _init_git_repo(self, sandbox_path: str, sandbox_name: str):
        """Initialize git repository in sandbox"""
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
                         
        except subprocess.CalledProcessError as e:
            # Git operations are nice-to-have, not critical
            print(f"Warning: Git initialization failed: {e}")
        finally:
            os.chdir(original_dir)    
    def _register_sandbox(self, sandbox_info: Dict[str, Any]):
        """Register sandbox in tracking file"""
        import json
        
        sandboxes = []
        if os.path.exists(self.sandboxes_file):
            try:
                with open(self.sandboxes_file, 'r') as f:
                    sandboxes = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                sandboxes = []
        
        sandboxes.append(sandbox_info)
        
        with open(self.sandboxes_file, 'w') as f:
            json.dump(sandboxes, f, indent=2)
    
    def list_sandboxes(self) -> List[Dict[str, Any]]:
        """List all registered sandboxes"""
        import json
        
        if not os.path.exists(self.sandboxes_file):
            return []
        
        try:
            with open(self.sandboxes_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def cleanup_sandbox(self, sandbox_path: str) -> Dict[str, Any]:
        """Remove a sandbox and clean up tracking"""
        try:
            if os.path.exists(sandbox_path):
                shutil.rmtree(sandbox_path)
            
            # Remove from tracking
            self._unregister_sandbox(sandbox_path)
            
            return {
                "status": "success",
                "message": f"Sandbox cleaned up: {sandbox_path}"
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e)
            }
    
    def _unregister_sandbox(self, sandbox_path: str):
        """Remove sandbox from tracking file"""
        import json
        
        sandboxes = self.list_sandboxes()
        sandboxes = [s for s in sandboxes if s.get("path") != sandbox_path]
        
        with open(self.sandboxes_file, 'w') as f:
            json.dump(sandboxes, f, indent=2)
    
    def sync_changes(self, sandbox_path: str, main_path: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Sync approved changes from sandbox to main project"""
        try:
            if not os.path.exists(sandbox_path):
                raise ValueError(f"Sandbox path does not exist: {sandbox_path}")
            
            if not os.path.exists(main_path):
                raise ValueError(f"Main path does not exist: {main_path}")
            
            # Get files to sync
            if files is None:
                files = self._get_changed_files(sandbox_path)
            
            synced_files = []
            backup_files = []
            
            for file_path in files:
                if not file_path.strip():
                    continue
                
                src_file = os.path.join(sandbox_path, file_path)
                dest_file = os.path.join(main_path, file_path)
                
                if os.path.exists(src_file):
                    # Create backup of destination
                    if os.path.exists(dest_file):
                        backup_path = f"{dest_file}.backup.{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                        shutil.copy2(dest_file, backup_path)
                        backup_files.append(backup_path)
                    
                    # Ensure destination directory exists
                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(src_file, dest_file)
                    synced_files.append(file_path)
            
            return {
                "status": "success",
                "files_synced": synced_files,
                "backup_files": backup_files,
                "message": f"Synced {len(synced_files)} files successfully"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _get_changed_files(self, sandbox_path: str) -> List[str]:
        """Get list of changed files in sandbox using git"""
        original_dir = os.getcwd()
        try:
            os.chdir(sandbox_path)
            result = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')
        except:
            pass
        finally:
            os.chdir(original_dir)
        
        # Fallback: return empty list
        return []