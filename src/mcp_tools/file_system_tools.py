
import os
import shutil
import re
from datetime import datetime
from typing import Any, Dict, List, Union



from .security import is_safe_path, get_file_extension, SecurityConfig
from .mcp_instance import mcp



@mcp.tool()
def create_file(path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
    """
    Create a file with specified content.
    
    Args:
        path: File path to create
        content: Content to write to the file
        overwrite: Whether to overwrite if file exists (default: False)
        
    Returns:
        Dictionary with operation results
    """
    # Validate path safety
    is_safe, message = is_safe_path(path)
    if not is_safe:
        return {
            "success": False,
            "error": f"Path blocked for security: {message}"
        }
    
    # Validate file extension
    ext = get_file_extension(path)
    if ext and ext not in SecurityConfig.ALLOWED_EXTENSIONS:
        return {
            "success": False,
            "error": f"File extension not allowed: {ext}"
        }
    
    # Check file size
    if len(content.encode('utf-8')) > SecurityConfig.MAX_FILE_SIZE:
        return {
            "success": False,
            "error": f"Content too large (max {SecurityConfig.MAX_FILE_SIZE} bytes)"
        }
    
    try:
        # Check if file exists
        if os.path.exists(path) and not overwrite:
            return {
                "success": False,
                "error": "File already exists (use overwrite=True to replace)"
            }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Write file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "message": f"File created successfully: {path}",
            "path": path,
            "size": len(content),
            "lines": len(content.splitlines())
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create file: {str(e)}"
        }

@mcp.tool()
def read_file(path: str) -> Dict[str, Any]:
    """
    Read file contents.
    
    Args:
        path: File path to read
        
    Returns:
        Dictionary with file contents and metadata
    """
    # Validate path safety
    is_safe, message = is_safe_path(path)
    if not is_safe:
        return {
            "success": False,
            "error": f"Path blocked for security: {message}"
        }
    
    try:
        if not os.path.exists(path):
            return {
                "success": False,
                "error": "File not found"
            }
        
        # Check file size
        file_size = os.path.getsize(path)
        if file_size > SecurityConfig.MAX_FILE_SIZE:
            return {
                "success": False,
                "error": f"File too large (max {SecurityConfig.MAX_FILE_SIZE} bytes)"
            }
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "path": path,
            "size": len(content),
            "lines": len(content.splitlines()),
            "encoding": "utf-8"
        }
        
    except UnicodeDecodeError:
        return {
            "success": False,
            "error": "File contains non-UTF-8 content"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read file: {str(e)}"
        }

@mcp.tool()
def create_directory(path: str) -> Dict[str, Any]:
    """
    Create a directory.
    
    Args:
        path: Directory path to create
        
    Returns:
        Dictionary with operation results
    """
    # Validate path safety
    is_safe, message = is_safe_path(path)
    if not is_safe:
        return {
            "success": False,
            "error": f"Path blocked for security: {message}"
        }
    
    try:
        os.makedirs(path, exist_ok=True)
        
        return {
            "success": True,
            "message": f"Directory created successfully: {path}",
            "path": path,
            "exists": os.path.exists(path),
            "is_directory": os.path.isdir(path)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create directory: {str(e)}"
        }

@mcp.tool()
def list_directory(path: str = ".") -> Dict[str, Any]:
    """
    List directory contents with detailed information.
    
    Args:
        path: Directory path to list (default: current directory)
        
    Returns:
        Dictionary with directory contents
    """
    # Validate path safety
    is_safe, message = is_safe_path(path)
    if not is_safe:
        return {
            "success": False,
            "error": f"Path blocked for security: {message}"
        }
    
    try:
        if not os.path.exists(path):
            return {
                "success": False,
                "error": "Directory not found"
            }
        
        if not os.path.isdir(path):
            return {
                "success": False,
                "error": "Path is not a directory"
            }
        
        items = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                stat = os.stat(item_path)
                items.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "extension": get_file_extension(item) if os.path.isfile(item_path) else None
                })
            except (OSError, FileNotFoundError):
                # Skip items we can't access
                continue
        
        # Sort items: directories first, then files alphabetically
        items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
        
        return {
            "success": True,
            "path": path,
            "items": items,
            "total_count": len(items),
            "directories": len([i for i in items if i["type"] == "directory"]),
            "files": len([i for i in items if i["type"] == "file"])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list directory: {str(e)}"
        }

@mcp.tool()
def copy_file_or_directory(source: str, destination: str) -> Dict[str, Any]:
    """
    Copy a file or directory to a new location.
    
    Args:
        source: Source file or directory path
        destination: Destination path
        
    Returns:
        Dictionary with operation results
    """
    # Validate paths
    is_safe, message = is_safe_path(source)
    if not is_safe:
        return {
            "success": False,
            "error": f"Source path blocked: {message}"
        }
    
    is_safe, message = is_safe_path(destination)
    if not is_safe:
        return {
            "success": False,
            "error": f"Destination path blocked: {message}"
        }
    
    try:
        if not os.path.exists(source):
            return {
                "success": False,
                "error": "Source path does not exist"
            }
        
        if os.path.isfile(source):
            # Copy file
            shutil.copy2(source, destination)
            operation_type = "file"
        else:
            # Copy directory
            shutil.copytree(source, destination, dirs_exist_ok=True)
            operation_type = "directory"
        
        return {
            "success": True,
            "message": f"Successfully copied {operation_type}",
            "source": source,
            "destination": destination,
            "type": operation_type
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to copy: {str(e)}"
        }

@mcp.tool()
def search_and_replace_in_file(
    file_path: str,
    search_pattern: str,
    replacement: str,
    use_regex: bool = False
) -> Dict[str, Any]:
    """
    Search and replace text in a file.
    
    Args:
        file_path: Path to the file to modify
        search_pattern: Text or regex pattern to search for
        replacement: Replacement text
        use_regex: Whether to use regex matching (default: False)
        
    Returns:
        Dictionary with operation results
    """
    # Validate path safety
    is_safe, message = is_safe_path(file_path)
    if not is_safe:
        return {
            "success": False,
            "error": f"Path blocked for security: {message}"
        }
    
    # Validate file extension
    ext = get_file_extension(file_path)
    if ext and ext not in SecurityConfig.ALLOWED_EXTENSIONS:
        return {
            "success": False,
            "error": f"File extension not allowed: {ext}"
        }
    
    try:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": "File not found"
            }
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Perform search and replace
        if use_regex:
            try:
                modified_content = re.sub(search_pattern, replacement, original_content)
                matches = len(re.findall(search_pattern, original_content))
            except re.error as e:
                return {
                    "success": False,
                    "error": f"Invalid regex pattern: {str(e)}"
                }
        else:
            modified_content = original_content.replace(search_pattern, replacement)
            matches = original_content.count(search_pattern)
        
        # Write modified content back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        return {
            "success": True,
            "message": f"Successfully replaced {matches} occurrences",
            "file_path": file_path,
            "matches_found": matches,
            "use_regex": use_regex,
            "search_pattern": search_pattern,
            "replacement": replacement
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to search and replace: {str(e)}"
        }
