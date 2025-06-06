"""
Utility functions for Development Safety System

Common helper functions used across the MCP server components.
"""

import os
import shutil
from pathlib import Path
from typing import Union, Optional
from datetime import datetime


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        Path object of the ensured directory
    """
    path_obj = Path(path).expanduser().resolve()
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def validate_path(path: Union[str, Path], must_exist: bool = True) -> bool:
    """
    Validate that a path is safe and optionally exists.
    
    Args:
        path: Path to validate
        must_exist: Whether the path must already exist
        
    Returns:
        True if path is valid, False otherwise
    """
    try:
        path_obj = Path(path).expanduser().resolve()
        
        # Check if path must exist
        if must_exist and not path_obj.exists():
            return False
        
        # Basic security checks - ensure we're not dealing with dangerous paths
        path_str = str(path_obj)
        dangerous_patterns = ['..', '/etc/', '/bin/', '/usr/bin/', 'C:\\Windows\\']
        
        for pattern in dangerous_patterns:
            if pattern in path_str:
                return False
        
        return True
        
    except Exception:
        return False


def create_backup(file_path: Union[str, Path], backup_suffix: Optional[str] = None) -> Optional[str]:
    """
    Create a backup of a file.
    
    Args:
        file_path: Path to file to backup
        backup_suffix: Optional suffix for backup file
        
    Returns:
        Path to backup file, or None if backup failed
    """
    try:
        path_obj = Path(file_path)
        if not path_obj.exists():
            return None
        
        if backup_suffix is None:
            backup_suffix = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        backup_path = f"{file_path}.backup.{backup_suffix}"
        shutil.copy2(file_path, backup_path)
        return backup_path
        
    except Exception:
        return None


def safe_remove_directory(path: Union[str, Path]) -> bool:
    """
    Safely remove a directory and its contents.
    
    Args:
        path: Directory path to remove
        
    Returns:
        True if removal was successful, False otherwise
    """
    try:
        path_obj = Path(path)
        
        # Safety check - don't remove system directories
        if not validate_path(path_obj, must_exist=False):
            return False
        
        # Additional safety - ensure it's in a reasonable location
        path_str = str(path_obj.resolve())
        if any(sys_dir in path_str for sys_dir in ['/bin', '/usr', '/etc', 'C:\\Windows']):
            return False
        
        if path_obj.exists():
            shutil.rmtree(path_obj)
        
        return True
        
    except Exception:
        return False


def get_file_timestamp(file_path: Union[str, Path]) -> Optional[datetime]:
    """
    Get the last modification timestamp of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        datetime object of last modification, or None if file doesn't exist
    """
    try:
        path_obj = Path(file_path)
        if path_obj.exists():
            timestamp = path_obj.stat().st_mtime
            return datetime.fromtimestamp(timestamp)
        return None
    except Exception:
        return None


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def is_text_file(file_path: Union[str, Path]) -> bool:
    """
    Check if a file is likely a text file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file appears to be text, False otherwise
    """
    try:
        path_obj = Path(file_path)
        
        # Check by extension first
        text_extensions = {
            '.txt', '.md', '.py', '.js', '.jsx', '.ts', '.tsx', '.json', 
            '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.css', 
            '.scss', '.html', '.xml', '.csv', '.log'
        }
        
        if path_obj.suffix.lower() in text_extensions:
            return True
        
        # Try to read first few bytes
        try:
            with open(path_obj, 'rb') as f:
                chunk = f.read(1024)
                # Check if chunk contains mostly printable ASCII characters
                text_chars = sum(1 for byte in chunk if byte in range(32, 127) or byte in [9, 10, 13])
                return text_chars / len(chunk) > 0.8 if chunk else True
        except:
            return False
            
    except Exception:
        return False