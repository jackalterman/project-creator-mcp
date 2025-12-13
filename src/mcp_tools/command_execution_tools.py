import os
import subprocess
import sys
import signal
import threading
import shlex
from typing import Any, Dict

from .security import is_safe_path
from src.config import SecurityConfig
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

def run_command_with_timeout(cmd, shell=False, cwd=".", timeout=None, env=None, input_text=None):
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
                stdin=subprocess.PIPE if input_text else subprocess.DEVNULL,
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
                stdin=subprocess.PIPE if input_text else subprocess.DEVNULL,
                text=True,
                cwd=cwd,
                env=env,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )
        
        # Use communicate with timeout
        stdout, stderr = process.communicate(input=input_text, timeout=timeout)
        
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
def run_npm_command(command: str, cwd: str = ".", input: str = None) -> Dict[str, Any]:
    """
    Execute npm commands safely.
    
    Args:
        command: npm command to run (e.g., 'install', 'run build', 'test')
        cwd: Working directory (default: current directory)
        input: Optional input text to send to the command (stdin)
        
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
            env=env,
            input_text=input
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
def run_npx_command(command: str, cwd: str = ".", input: str = None) -> Dict[str, Any]:
    """
    Execute npx commands safely.
    
    Args:
        command: npx command to run (e.g., 'create-react-app my-app')
        cwd: Working directory (default: current directory)
        input: Optional input text to send to the command (stdin)
        
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
            env=env,
            input_text=input
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
def run_python_command(command: str, cwd: str = ".", input: str = None) -> Dict[str, Any]:
    """
    Execute Python commands safely (pip, python scripts, etc.).
    
    Args:
        command: Python command to run (e.g., 'pip install fastapi', 'python main.py')
        cwd: Working directory (default: current directory)
        input: Optional input text to send to the command (stdin)
        
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
    
    try:
        # posix=False to handle Windows paths with backslashes correctly
        command_parts = shlex.split(command, posix=False)
        # Strip quotes from arguments since subprocess handles quoting
        command_parts = [part.strip('"').strip("'") for part in command_parts]
    except ValueError:
        # Fallback for simple split if shlex fails (e.g. unmatched quotes)
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
                env=env,
                input_text=input
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
                env=env,
                input_text=input
            )
        else:
            # For other commands, use shell but with safe environment
            result = run_command_with_timeout(
                command,
                shell=True,
                cwd=cwd,
                timeout=get_timeout_value() * 2,
                env=env,
                input_text=input
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
def run_go_command(command: str, cwd: str = ".", input: str = None) -> Dict[str, Any]:
    """
    Execute Go commands safely.
    
    Args:
        command: Go command to run (e.g., 'mod tidy', 'run main.go', 'build')
        cwd: Working directory (default: current directory)
        input: Optional input text to send to the command (stdin)
        
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
            env=create_safe_env(),
            input_text=input
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
def run_command(command: str, cwd: str = ".", input: str = None) -> Dict[str, Any]:
    """
    Generic command runner that safely executes basic system commands.
    
    Args:
        command: The command string to execute.
        cwd: Working directory (default: current directory).
        input: Optional input text to send to the command (stdin)
        
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
            env=create_safe_env(),
            input_text=input
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
def run_docker_command(command: str, cwd: str = ".", input: str = None) -> Dict[str, Any]:
    """
    Execute Docker commands safely.
    
    Args:
        command: Docker command to run (e.g., 'build -t myapp .', 'ps', 'run -p 8000:8000 myapp')
        cwd: Working directory (default: current directory)
        input: Optional input text to send to the command (stdin)
        
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
    
    # Validate Docker command
    allowed_docker_commands = [
        'build', 'run', 'ps', 'stop', 'start', 'rm', 'rmi', 'images',
        'logs', 'exec', 'inspect', 'pull', 'push', 'tag', 'network',
        'volume', 'version', '--version', 'info', 'stats', 'top',
        'port', 'diff', 'commit', 'cp', 'create', 'pause', 'unpause',
        'restart', 'wait', 'attach', 'export', 'import', 'save', 'load',
        'history', 'search', 'login', 'logout'
    ]
    
    command_parts = command.split()
    base_cmd = command_parts[0] if command_parts else ""
    
    if base_cmd not in allowed_docker_commands:
        return {
            "success": False,
            "error": f"Docker command not allowed: {base_cmd}",
            "allowed_commands": allowed_docker_commands
        }
    
    # Create safe environment
    env = create_safe_env()
    
    try:
        result = run_command_with_timeout(
            f"docker {command}",
            shell=True,
            cwd=cwd,
            timeout=get_timeout_value() * 3,  # Docker commands can take longer
            env=env,
            input_text=input
        )
        
        return {
            "success": not result["timed_out"] and result["returncode"] == 0,
            "output": result["stdout"].strip(),
            "error": result["stderr"].strip() if result["stderr"] else None,
            "return_code": result["returncode"],
            "command": f"docker {command}",
            "working_directory": cwd,
            "timed_out": result["timed_out"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run Docker command: {str(e)}"
        }

@mcp.tool()
def run_docker_compose_command(command: str, cwd: str = ".", input: str = None) -> Dict[str, Any]:
    """
    Execute Docker Compose commands safely.
    
    Args:
        command: Docker Compose command to run (e.g., 'up -d', 'down', 'ps', 'logs')
        cwd: Working directory (default: current directory)
        input: Optional input text to send to the command (stdin)
        
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
    
    # Check if docker-compose.yml exists (except for version command)
    compose_file = os.path.join(cwd, 'docker-compose.yml')
    compose_yaml = os.path.join(cwd, 'docker-compose.yaml')
    command_parts = command.split()
    base_cmd = command_parts[0] if command_parts else ""
    
    if base_cmd not in ['version', '--version'] and not os.path.exists(compose_file) and not os.path.exists(compose_yaml):
        return {
            "success": False,
            "error": "docker-compose.yml or docker-compose.yaml not found in working directory"
        }
    
    # Validate Docker Compose command
    allowed_compose_commands = [
        'up', 'down', 'ps', 'logs', 'start', 'stop', 'restart',
        'build', 'pull', 'push', 'config', 'exec', 'run', 'rm',
        'create', 'kill', 'pause', 'unpause', 'top', 'events',
        'port', 'images', 'version', '--version', 'ls'
    ]
    
    if base_cmd not in allowed_compose_commands:
        return {
            "success": False,
            "error": f"Docker Compose command not allowed: {base_cmd}",
            "allowed_commands": allowed_compose_commands
        }
    
    # Create safe environment
    env = create_safe_env()
    
    try:
        # Try docker compose (v2) first, fall back to docker-compose (v1)
        result = run_command_with_timeout(
            f"docker compose {command}",
            shell=True,
            cwd=cwd,
            timeout=get_timeout_value() * 4,  # Docker Compose can take even longer
            env=env,
            input_text=input
        )
        
        # If docker compose fails, try docker-compose
        if result["returncode"] != 0 and "not a docker command" in result["stderr"].lower():
            result = run_command_with_timeout(
                f"docker-compose {command}",
                shell=True,
                cwd=cwd,
                timeout=get_timeout_value() * 4,
                env=env,
                input_text=input
            )
        
        return {
            "success": not result["timed_out"] and result["returncode"] == 0,
            "output": result["stdout"].strip(),
            "error": result["stderr"].strip() if result["stderr"] else None,
            "return_code": result["returncode"],
            "command": f"docker compose {command}",
            "working_directory": cwd,
            "timed_out": result["timed_out"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run Docker Compose command: {str(e)}"
        }

@mcp.tool()
def run_database_command(
    command: str, 
    db_type: str, 
    cwd: str = ".", 
    docker_container: str = None,
    input: str = None
) -> Dict[str, Any]:
    """
    Execute database commands safely, with optional Docker container support.
    
    Args:
        command: Database command to run (e.g., 'psql -U postgres -d mydb -c "SELECT * FROM users"')
        db_type: Database type ('postgresql', 'mysql', 'sqlite', 'mongodb')
        cwd: Working directory (default: current directory)
        docker_container: Optional Docker container name/ID to execute command in
        input: Optional input text to send to the command (stdin, e.g., SQL script content)
        
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
    
    # Database command mappings
    db_commands = {
        "postgresql": {
            "commands": ['psql', 'pg_dump', 'pg_restore', 'createdb', 'dropdb', 
                        'pg_isready', 'pg_basebackup', 'vacuumdb', 'reindexdb'],
            "prefix": ""
        },
        "mysql": {
            "commands": ['mysql', 'mysqldump', 'mysqladmin', 'mysqlcheck', 
                        'mysqlimport', 'mysqlshow', 'mysqlbinlog'],
            "prefix": ""
        },
        "sqlite": {
            "commands": ['sqlite3'],
            "prefix": ""
        },
        "mongodb": {
            "commands": ['mongosh', 'mongodump', 'mongorestore', 'mongoexport', 
                        'mongoimport', 'mongostat', 'mongotop'],
            "prefix": ""
        }
    }
    
    # Validate database type
    if db_type not in db_commands:
        return {
            "success": False,
            "error": f"Unsupported database type: {db_type}",
            "supported_types": list(db_commands.keys())
        }
    
    # Extract base command
    command_parts = command.split()
    base_cmd = command_parts[0] if command_parts else ""
    
    # Validate command
    allowed_commands = db_commands[db_type]["commands"]
    if base_cmd not in allowed_commands:
        return {
            "success": False,
            "error": f"{db_type} command not allowed: {base_cmd}",
            "allowed_commands": allowed_commands
        }
    
    # Create safe environment
    env = create_safe_env()
    
    try:
        # If Docker container is specified, use docker exec
        if docker_container:
            # Check if container exists and is running
            check_result = run_command_with_timeout(
                f"docker ps --filter name={docker_container} --format {{{{.Names}}}}",
                shell=True,
                cwd=cwd,
                timeout=10,
                env=env
            )
            
            if check_result["returncode"] != 0 or not check_result["stdout"].strip():
                return {
                    "success": False,
                    "error": f"Docker container '{docker_container}' not found or not running"
                }
            
            # Execute command in container
            # Use -i flag if we have input, -t for interactive commands
            docker_flags = "-i" if input else ""
            full_command = f"docker exec {docker_flags} {docker_container} {command}"
        else:
            # Execute command locally
            full_command = command
        
        result = run_command_with_timeout(
            full_command,
            shell=True,
            cwd=cwd,
            timeout=get_timeout_value() * 3,  # Database operations can take time
            env=env,
            input_text=input
        )
        
        return {
            "success": not result["timed_out"] and result["returncode"] == 0,
            "output": result["stdout"].strip(),
            "error": result["stderr"].strip() if result["stderr"] else None,
            "return_code": result["returncode"],
            "command": full_command,
            "working_directory": cwd,
            "docker_container": docker_container,
            "timed_out": result["timed_out"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run database command: {str(e)}"
        }

@mcp.tool()
def test_web_application(
    url: str,
    test_type: str = "functionality",
    method: str = "GET",
    data: str = None,
    headers: Dict[str, str] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Test a web application or API endpoint and return results suitable for AI analysis.
    
    Args:
        url: URL to test (e.g., 'http://localhost:3000' or 'http://localhost:8000/api/users')
        test_type: Type of test ('functionality', 'accessibility', 'performance')
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        data: Optional request body data (JSON string)
        headers: Optional HTTP headers
        timeout: Request timeout in seconds (default: 30)
        
    Returns:
        Dictionary with test results including status, content, performance metrics, and issues
    """
    import urllib.request
    import urllib.error
    import json as json_module
    import time
    from html.parser import HTMLParser
    
    class SimpleHTMLParser(HTMLParser):
        """Simple HTML parser to extract basic information"""
        def __init__(self):
            super().__init__()
            self.title = None
            self.headings = []
            self.links = []
            self.forms = []
            self.images = []
            self.scripts = []
            
        def handle_starttag(self, tag, attrs):
            attrs_dict = dict(attrs)
            if tag == 'a' and 'href' in attrs_dict:
                self.links.append(attrs_dict['href'])
            elif tag == 'form':
                self.forms.append(attrs_dict)
            elif tag == 'img' and 'src' in attrs_dict:
                self.images.append(attrs_dict['src'])
            elif tag == 'script' and 'src' in attrs_dict:
                self.scripts.append(attrs_dict['src'])
            elif tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                self.current_heading = tag
                
        def handle_data(self, data):
            if hasattr(self, 'current_heading'):
                self.headings.append((self.current_heading, data.strip()))
                delattr(self, 'current_heading')
            elif self.title is None and hasattr(self, 'in_title'):
                self.title = data.strip()
                
        def handle_starttag(self, tag, attrs):
            if tag == 'title':
                self.in_title = True
            super().handle_starttag(tag, attrs)
            
        def handle_endtag(self, tag):
            if tag == 'title' and hasattr(self, 'in_title'):
                delattr(self, 'in_title')
    
    try:
        # Prepare request
        if headers is None:
            headers = {}
        
        # Add default headers
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Mozilla/5.0 (MCP Test Agent)'
        
        # Prepare data
        request_data = None
        if data:
            if method in ['POST', 'PUT', 'PATCH']:
                request_data = data.encode('utf-8')
                if 'Content-Type' not in headers:
                    headers['Content-Type'] = 'application/json'
        
        # Create request
        req = urllib.request.Request(
            url,
            data=request_data,
            headers=headers,
            method=method
        )
        
        # Measure performance
        start_time = time.time()
        
        try:
            response = urllib.request.urlopen(req, timeout=timeout)
            response_time = time.time() - start_time
            
            # Read response
            content = response.read()
            content_type = response.headers.get('Content-Type', '')
            status_code = response.status
            
            # Decode content
            try:
                decoded_content = content.decode('utf-8')
            except UnicodeDecodeError:
                decoded_content = content.decode('latin-1')
            
            # Parse response based on content type
            parsed_data = {}
            issues = []
            
            if 'application/json' in content_type:
                try:
                    parsed_data = json_module.loads(decoded_content)
                except json_module.JSONDecodeError as e:
                    issues.append(f"Invalid JSON response: {str(e)}")
                    parsed_data = {"raw": decoded_content[:500]}
            
            elif 'text/html' in content_type:
                parser = SimpleHTMLParser()
                try:
                    parser.feed(decoded_content)
                    parsed_data = {
                        "title": parser.title,
                        "headings": parser.headings[:10],  # First 10 headings
                        "links_count": len(parser.links),
                        "forms_count": len(parser.forms),
                        "images_count": len(parser.images),
                        "scripts_count": len(parser.scripts)
                    }
                    
                    # Accessibility checks
                    if test_type == "accessibility":
                        if not parser.title:
                            issues.append("Missing page title")
                        if not parser.headings:
                            issues.append("No heading tags found")
                        if parser.images:
                            # Check for alt attributes would require more parsing
                            issues.append("Note: Image alt text validation not implemented")
                            
                except Exception as e:
                    issues.append(f"HTML parsing error: {str(e)}")
                    parsed_data = {"raw_preview": decoded_content[:500]}
            
            else:
                # Plain text or other content
                parsed_data = {"content_preview": decoded_content[:500]}
            
            # Performance analysis
            performance = {
                "response_time_ms": round(response_time * 1000, 2),
                "content_size_bytes": len(content),
                "status": "fast" if response_time < 1 else "slow" if response_time < 3 else "very_slow"
            }
            
            if test_type == "performance":
                if response_time > 3:
                    issues.append(f"Slow response time: {performance['response_time_ms']}ms")
                if len(content) > 1000000:  # 1MB
                    issues.append(f"Large response size: {len(content)} bytes")
            
            return {
                "success": True,
                "status_code": status_code,
                "content_type": content_type,
                "performance": performance,
                "parsed_data": parsed_data,
                "issues": issues,
                "headers": dict(response.headers),
                "url": url,
                "test_type": test_type
            }
            
        except urllib.error.HTTPError as e:
            response_time = time.time() - start_time
            error_content = e.read().decode('utf-8', errors='ignore')
            
            return {
                "success": False,
                "status_code": e.code,
                "error": f"HTTP {e.code}: {e.reason}",
                "error_content": error_content[:500],
                "response_time_ms": round(response_time * 1000, 2),
                "url": url,
                "test_type": test_type
            }
            
        except urllib.error.URLError as e:
            response_time = time.time() - start_time
            
            return {
                "success": False,
                "error": f"Connection failed: {str(e.reason)}",
                "response_time_ms": round(response_time * 1000, 2),
                "url": url,
                "test_type": test_type,
                "suggestion": "Check if the server is running and the URL is correct"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Test failed: {str(e)}",
            "url": url,
            "test_type": test_type
        }

@mcp.tool()
def run_terraform_command(command: str, cwd: str = ".", input: str = None) -> Dict[str, Any]:
    """
    Execute Terraform commands safely.
    
    Args:
        command: Terraform command to run (e.g., 'init', 'plan', 'apply -auto-approve', 'destroy')
        cwd: Working directory (default: current directory)
        input: Optional input text to send to the command (stdin)
        
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
    
    # Validate Terraform command
    allowed_terraform_commands = [
        'init', 'plan', 'apply', 'destroy', 'validate', 'fmt',
        'output', 'show', 'state', 'refresh', 'import', 'taint',
        'untaint', 'workspace', 'version', '--version', 'providers',
        'graph', 'console'
    ]
    
    command_parts = command.split()
    base_cmd = command_parts[0] if command_parts else ""
    
    if base_cmd not in allowed_terraform_commands:
        return {
            "success": False,
            "error": f"Terraform command not allowed: {base_cmd}",
            "allowed_commands": allowed_terraform_commands
        }
    
    # Create safe environment
    env = create_safe_env()
    
    try:
        result = run_command_with_timeout(
            f"terraform {command}",
            shell=True,
            cwd=cwd,
            timeout=get_timeout_value() * 10,  # Terraform operations can take very long
            env=env,
            input_text=input
        )
        
        return {
            "success": not result["timed_out"] and result["returncode"] == 0,
            "output": result["stdout"].strip(),
            "error": result["stderr"].strip() if result["stderr"] else None,
            "return_code": result["returncode"],
            "command": f"terraform {command}",
            "working_directory": cwd,
            "timed_out": result["timed_out"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run Terraform command: {str(e)}"
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