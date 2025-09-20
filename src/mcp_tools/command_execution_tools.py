import os
import subprocess
import sys
import signal
import threading
from typing import Any, Dict

from .security import is_safe_path, SecurityConfig
from .mcp_instance import mcp

# Default timeout if SecurityConfig is not available
DEFAULT_TIMEOUT = 120

def get_timeout_value():
    """Get timeout value, with fallback if SecurityConfig is not available"""
    try:
        return SecurityConfig.COMMAND_TIMEOUT
    except (AttributeError, NameError):
        return DEFAULT_TIMEOUT

def create_safe_env():
    """Create a safe environment for command execution"""
    env = os.environ.copy()
    # Ensure non-interactive mode
    env['PYTHONUNBUFFERED'] = '1'
    env['DEBIAN_FRONTEND'] = 'noninteractive'
    env['TERM'] = 'dumb'
    env['NO_COLOR'] = '1'
    # Disable pip's interactive features
    env['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    env['PIP_NO_INPUT'] = '1'
    # Disable npm interactive features
    env['CI'] = 'true'
    env['NODE_ENV'] = 'production'
    return env

def run_command_with_timeout(cmd, shell=False, cwd=".", timeout=None, env=None):
    """
    Run command with proper timeout and process cleanup
    """
    if timeout is None:
        timeout = get_timeout_value()
    
    if env is None:
        env = create_safe_env()
    
    try:
        # Use Popen for better process control
        if shell:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,  # Prevent hanging on input
                text=True,
                cwd=cwd,
                env=env,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )
        else:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,  # Prevent hanging on input
                text=True,
                cwd=cwd,
                env=env,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )
        
        # Use communicate with timeout
        stdout, stderr = process.communicate(timeout=timeout)
        
        return {
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": False
        }
        
    except subprocess.TimeoutExpired:
        # Kill the process group to ensure cleanup
        try:
            if hasattr(os, 'killpg'):
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                process.terminate()
            
            # Give it a moment to terminate gracefully
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
                process.wait()
        except (ProcessLookupError, OSError):
            pass  # Process already terminated
        
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "timed_out": True
        }
    
    except Exception as e:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command execution failed: {str(e)}",
            "timed_out": False
        }

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
    
    # Validate npm command
    allowed_npm_commands = [
        'install', 'i', 'update', 'run', 'start', 'test', 'build',
        'lint', 'audit', 'list', 'ls', 'outdated', 'version',
        'init', 'create', 'config', 'info', 'search', 'pack',
        'publish', 'unpublish', 'deprecate', 'docs', 'repo', 'npx'
    ]
    
    base_cmd = command.split()[0] if command.split() else ""
    if base_cmd not in allowed_npm_commands:
        return {
            "success": False,
            "error": f"npm command not allowed: {base_cmd}",
            "allowed_commands": allowed_npm_commands
        }
    
    # Check if package.json exists for commands that need it
    package_json_path = os.path.join(cwd, 'package.json')
    if not os.path.exists(package_json_path) and base_cmd not in ['init', 'create', 'version']:
        return {
            "success": False,
            "error": "package.json not found in working directory"
        }
    
    # Create safe environment
    env = create_safe_env()
    
    # Handle special cases that might hang
    full_command = f"npm {command}"
    if base_cmd == 'version' and len(command.split()) == 1:
        # npm version without arguments shows current version, shouldn't hang
        full_command = "npm --version"
    
    try:
        result = run_command_with_timeout(
            full_command,
            shell=True,
            cwd=cwd,
            timeout=get_timeout_value() * 3,  # npm commands can take longer
            env=env
        )
        
        return {
            "success": not result["timed_out"] and result["returncode"] == 0,
            "output": result["stdout"].strip(),
            "error": result["stderr"].strip() if result["stderr"] else None,
            "return_code": result["returncode"],
            "command": full_command,
            "working_directory": cwd,
            "timed_out": result["timed_out"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run npm command: {str(e)}"
        }


@mcp.tool()
def run_npx_command(command: str, cwd: str = ".") -> Dict[str, Any]:
    """
    Execute npx commands safely.
    
    Args:
        command: npx command to run (e.g., 'create-react-app my-app')
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
    
    # Create safe environment
    env = create_safe_env()
    
    full_command = f"npx {command}"
    
    try:
        result = run_command_with_timeout(
            full_command,
            shell=True,
            cwd=cwd,
            timeout=get_timeout_value() * 5,  # npx commands can take longer
            env=env
        )
        
        return {
            "success": not result["timed_out"] and result["returncode"] == 0,
            "output": result["stdout"].strip(),
            "error": result["stderr"].strip() if result["stderr"] else None,
            "return_code": result["returncode"],
            "command": full_command,
            "working_directory": cwd,
            "timed_out": result["timed_out"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run npx command: {str(e)}"
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
    
    # Create safe environment
    env = create_safe_env()
    
    try:
        if base_cmd == 'python' or base_cmd == 'python3':
            # Use sys.executable for direct Python execution
            cmd_list = [sys.executable] + command_parts[1:]
            
            # Special handling for potentially problematic Python commands
            if len(command_parts) > 1 and command_parts[1] == '-c':
                # For -c commands, ensure they don't wait for input
                python_code = ' '.join(command_parts[2:])
                # Add timeout and input handling to the Python code
                safe_code = f"import sys; sys.stdin.close(); {python_code}"
                cmd_list = [sys.executable, '-c', safe_code]
            
            result = run_command_with_timeout(
                cmd_list,
                shell=False,
                cwd=cwd,
                timeout=get_timeout_value() * 2,
                env=env
            )
        elif base_cmd == 'pip':
            # Use sys.executable -m pip for pip commands
            pip_args = command_parts[1:]
            # Add non-interactive flags
            if 'install' in pip_args and '--yes' not in pip_args and '-y' not in pip_args:
                pip_args.append('--no-input')
            
            cmd_list = [sys.executable, '-m', 'pip'] + pip_args
            result = run_command_with_timeout(
                cmd_list,
                shell=False,
                cwd=cwd,
                timeout=get_timeout_value() * 2,
                env=env
            )
        else:
            # For other commands, use shell but with safe environment
            result = run_command_with_timeout(
                command,
                shell=True,
                cwd=cwd,
                timeout=get_timeout_value() * 2,
                env=env
            )
        
        return {
            "success": not result["timed_out"] and result["returncode"] == 0,
            "output": result["stdout"].strip(),
            "error": result["stderr"].strip() if result["stderr"] else None,
            "return_code": result["returncode"],
            "command": command,
            "working_directory": cwd,
            "timed_out": result["timed_out"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Python command failed: {str(e)}"
        }

@mcp.tool()
def run_go_command(command: str, cwd: str = ".") -> Dict[str, Any]:
    """
    Execute Go commands safely.
    
    Args:
        command: Go command to run (e.g., 'mod tidy', 'run main.go', 'build')
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
    
    # Validate Go command
    allowed_go_commands = [
        'mod', 'run', 'build', 'test', 'fmt', 'vet', 'get', 'install'
    ]
    
    command_parts = command.split()
    base_cmd = command_parts[0] if command_parts else ""

    if base_cmd not in allowed_go_commands:
        return {
            "success": False,
            "error": f"Go command not allowed: {base_cmd}",
            "allowed_commands": allowed_go_commands
        }
    
    try:
        result = run_command_with_timeout(
            f"go {command}",
            shell=True,
            cwd=cwd,
            timeout=get_timeout_value() * 2,
            env=create_safe_env()
        )
        
        return {
            "success": not result["timed_out"] and result["returncode"] == 0,
            "output": result["stdout"].strip(),
            "error": result["stderr"].strip() if result["stderr"] else None,
            "return_code": result["returncode"],
            "command": f"go {command}",
            "working_directory": cwd,
            "timed_out": result["timed_out"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run Go command: {str(e)}"
        }

@mcp.tool()
def run_command(command: str, cwd: str = ".") -> Dict[str, Any]:
    """
    Generic command runner that safely executes basic system commands.
    
    Args:
        command: The command string to execute.
        cwd: Working directory (default: current directory).
        
    Returns:
        Dictionary with command results.
    """
    # Validate path safety
    is_safe, message = is_safe_path(cwd)
    if not is_safe:
        return {
            "success": False,
            "error": f"Working directory blocked: {message}"
        }
    
    # Basic command validation - only allow safe, non-interactive commands
    safe_commands = [
        'echo', 'ls', 'pwd', 'whoami', 'date', 'cat', 'head', 'tail',
        'wc', 'grep', 'find', 'which', 'type', 'env', 'dir'
    ]
    
    command_parts = command.split()
    base_cmd = command_parts[0] if command_parts else ""
    
    if base_cmd not in safe_commands:
        return {
            "success": False,
            "error": f"Command not allowed: {base_cmd}. Use specific tool functions for python, npm, or go commands.",
            "allowed_commands": safe_commands
        }
    
    try:
        result = run_command_with_timeout(
            command,
            shell=True,
            cwd=cwd,
            timeout=get_timeout_value(),
            env=create_safe_env()
        )
        
        return {
            "success": not result["timed_out"] and result["returncode"] == 0,
            "output": result["stdout"].strip(),
            "error": result["stderr"].strip() if result["stderr"] else None,
            "return_code": result["returncode"],
            "command": command,
            "working_directory": cwd,
            "timed_out": result["timed_out"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Command execution failed: {str(e)}"
        }

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
        git_result = run_command_with_timeout(
            ["git", "--version"],
            shell=False,
            cwd=path,
            timeout=10,
            env=create_safe_env()
        )
        
        if git_result["returncode"] != 0:
            return {
                "success": False,
                "error": "Git is not installed or not available"
            }
        
        # Initialize Git repository
        init_result = run_command_with_timeout(
            ["git", "init"],
            shell=False,
            cwd=path,
            timeout=get_timeout_value(),
            env=create_safe_env()
        )
        
        if init_result["returncode"] != 0:
            return {
                "success": False,
                "error": f"Failed to initialize Git repository: {init_result['stderr']}"
            }
        
        # Create basic .gitignore if it doesn't exist
        gitignore_path = os.path.join(path, '.gitignore')
        gitignore_created = False
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
            gitignore_created = True
        
        return {
            "success": True,
            "message": "Git repository initialized successfully",
            "path": path,
            "git_version": git_result["stdout"].strip(),
            "gitignore_created": gitignore_created
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to initialize Git repository: {str(e)}"
        }