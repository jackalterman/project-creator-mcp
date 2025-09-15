
import os
import subprocess
import sys  # Import sys module
from typing import Any, Dict



from .security import is_safe_path, SecurityConfig
from .mcp_instance import mcp



@mcp.tool()
def run_npm_command(command: str, cwd: str = ".") -> Dict[str, Any]:
    """
    Execute npm commands safely.
    
    Args:
        command: npm command to run (e.g., 'install', 'run build', 'test')
        cwd: Working directory (default: current directory)
        
    Returns:
        Dictionary with command results
    """
    # Validate path safety
    is_safe, message = is_safe_path(cwd)
    if not is_safe:
        return {
            "success": False,
            "error": f"Working directory blocked: {message}"
        }
    
    # Check if cwd exists
    if not os.path.isdir(cwd):
        return {
            "success": False,
            "error": f"Working directory does not exist: {cwd}"
        }
    
    # Check if cwd exists
    if not os.path.isdir(cwd):
        return {
            "success": False,
            "error": f"Working directory does not exist: {cwd}"
        }
    
    # Validate npm command
    allowed_npm_commands = [
        'install', 'i', 'update', 'run', 'start', 'test', 'build',
        'lint', 'audit', 'list', 'ls', 'outdated', 'version',
        'init', 'create', 'config', 'info', 'search', 'pack',
        'publish', 'unpublish', 'deprecate', 'docs', 'repo'
    ]
    
    base_cmd = command.split()[0] if command.split() else ""
    if base_cmd not in allowed_npm_commands:
        return {
            "success": False,
            "error": f"npm command not allowed: {base_cmd}",
            "allowed_commands": allowed_npm_commands
        }
    
    try:
        # Check if package.json exists
        package_json_path = os.path.join(cwd, 'package.json')
        if not os.path.exists(package_json_path) and base_cmd not in ['init', 'create']:
            return {
                "success": False,
                "error": "package.json not found in working directory"
            }
        
        result = subprocess.run(
            f"npm {command}",
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=SecurityConfig.COMMAND_TIMEOUT * 3  # npm commands can take longer
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
            "error": result.stderr.strip() if result.stderr else None,
            "return_code": result.returncode,
            "command": f"npm {command}",
            "working_directory": cwd
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"npm command timed out after {SecurityConfig.COMMAND_TIMEOUT * 3} seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run npm command: {str(e)}"
        }

@mcp.tool()
def run_python_command(command: str, cwd: str = ".") -> Dict[str, Any]:
    """
    Execute Python commands safely (pip, python scripts, etc.).
    
    Args:
        command: Python command to run (e.g., 'pip install fastapi', 'python main.py')
        cwd: Working directory (default: current directory)
        
    Returns:
        Dictionary with command results
    """
    # Validate path safety
    is_safe, message = is_safe_path(cwd)
    if not is_safe:
        return {
            "success": False,
            "error": f"Working directory blocked: {message}"
        }
    
    # Check if cwd exists
    if not os.path.isdir(cwd):
        return {
            "success": False,
            "error": f"Working directory does not exist: {cwd}"
        }
    
    # Validate Python command
    allowed_python_commands = [
        'pip', 'python', 'python3', 'pytest', 'black', 'flake8',
        'mypy', 'pylint', 'isort', 'coverage'
    ]
    
    command_parts = command.split()
    base_cmd = command_parts[0] if command_parts else ""

    if base_cmd not in allowed_python_commands:
        return {
            "success": False,
            "error": f"Python command not allowed: {base_cmd}",
            "allowed_commands": allowed_python_commands
        }
    
    # Additional validation for pip commands
    if base_cmd == 'pip':
        pip_subcommand = command_parts[1] if len(command_parts) > 1 else ""
        allowed_pip_commands = ['install', 'uninstall', 'list', 'show', 'freeze', 'check']
        if pip_subcommand not in allowed_pip_commands:
            return {
                "success": False,
                "error": f"pip subcommand not allowed: {pip_subcommand}"
            }
    
    try:
        if base_cmd == 'python' or base_cmd == 'python3':
            # Use sys.executable for direct Python execution
            cmd_list = [sys.executable] + command_parts[1:]
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=SecurityConfig.COMMAND_TIMEOUT * 2
            )
        elif base_cmd == 'pip':
            # Use sys.executable -m pip for pip commands
            cmd_list = [sys.executable, '-m', 'pip'] + command_parts[1:]
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=SecurityConfig.COMMAND_TIMEOUT * 2
            )
        else:
            # For other commands (pytest, black, etc.), keep shell=True
            # as they might be console scripts not directly executable
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=SecurityConfig.COMMAND_TIMEOUT * 2
            )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
            "error": result.stderr.strip() if result.stderr else None,
            "return_code": result.returncode,
            "command": command,
            "working_directory": cwd
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Python command timed out after {SecurityConfig.COMMAND_TIMEOUT * 2} seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Python command failed: {str(e)}"
        }

@mcp.tool()
def run_command(command: str, cwd: str = ".") -> Dict[str, Any]:
    """
    Generic command runner, dispatches to run_python_command.
    This tool is added to address the 'project-creator:run_command' not found error.
    
    Args:
        command: The command string to execute.
        cwd: Working directory (default: current directory).
        
    Returns:
        Dictionary with command results from run_python_command.
    """
    return run_python_command(command, cwd)

@mcp.tool()
def initialize_git_repository(path: str = ".") -> Dict[str, Any]:
    """
    Initialize a Git repository in the specified directory.
    
    Args:
        path: Directory to initialize Git repository (default: current directory)
        
    Returns:
        Dictionary with initialization results
    """
    # Validate path safety
    is_safe, message = is_safe_path(path)
    if not is_safe:
        return {
            "success": False,
            "error": f"Working directory blocked: {message}"
        }
    
    try:
        # Check if Git is available
        git_check = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if git_check.returncode != 0:
            return {
                "success": False,
                "error": "Git is not installed or not available"
            }
        
        # Initialize Git repository
        result = subprocess.run(
            ["git", "init"],
            capture_output=True,
            text=True,
            cwd=path,
            timeout=SecurityConfig.COMMAND_TIMEOUT
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Failed to initialize Git repository: {result.stderr}"
            }
        
        # Create basic .gitignore if it doesn't exist
        gitignore_path = os.path.join(path, '.gitignore')
        if not os.path.exists(gitignore_path):
            basic_gitignore = """# Dependencies
node_modules/
venv/
env/
.env

# Build outputs
dist/
build/
*.egg-info/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
logs/
"""
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(basic_gitignore)
        
        return {
            "success": True,
            "message": "Git repository initialized successfully",
            "path": path,
            "git_version": git_check.stdout.strip(),
            "gitignore_created": not os.path.exists(gitignore_path)
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Git initialization timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to initialize Git repository: {str(e)}"
        }
