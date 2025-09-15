# PowerShell MCP Server - Installation & Usage Guide

## Overview

This PowerShell MCP (Model Context Protocol) Server provides secure PowerShell execution capabilities for Claude Desktop and other MCP clients. It's designed specifically for local development tasks with comprehensive security measures.

## Prerequisites

Before installation, ensure you have:

- **Python 3.8+** installed and accessible via `python` command
- **pip** (Python package installer)
- **PowerShell** (Windows PowerShell 5.1+ or PowerShell Core 7+)
- **Claude Desktop** (if using with Claude)

### Optional Development Tools
- **Node.js & npm** (for Node.js/JavaScript development)
- **Git** (for version control operations)
- **Linting tools** (ESLint, Prettier, PyLint, etc.)

## Installation

### Method 1: Automated Setup (Recommended)

1. **Download the setup script** and save as `setup_powershell_mcp.ps1`

2. **Run the setup script**:
   ```powershell
   # Run with default settings
   .\setup_powershell_mcp.ps1
   
   # Custom installation directory
   .\setup_powershell_mcp.ps1 -InstallDir "C:\MyTools\powershell-mcp"
   
   # Skip Claude Desktop configuration
   .\setup_powershell_mcp.ps1 -SkipClaudeConfig
   ```

3. **Copy the server code**: Save the PowerShell MCP Server code (from the first artifact) as `powershell_mcp_server.py` in your installation directory.

### Method 2: Manual Installation

1. **Create project directory**:
   ```powershell
   mkdir powershell-mcp
   cd powershell-mcp
   ```

2. **Create virtual environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   pip install mcp pydantic
   ```

4. **Save the server files**:
   - Save the PowerShell MCP Server code as `powershell_mcp_server.py`
   - Create `requirements.txt` with the dependencies

5. **Configure Claude Desktop** (see Configuration section below)

## Configuration

### Claude Desktop Configuration

1. **Locate your Claude Desktop configuration file**:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. **Add the MCP server configuration**:
   ```json
   {
     "mcpServers": {
       "powershell-mcp": {
         "command": "python",
         "args": ["C:\\path\\to\\your\\powershell_mcp_server.py"],
         "env": {
           "PATH": "your-system-path-here"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** to load the new server

### Security Configuration

The server includes built-in security measures that can be customized by editing the `SecurityConfig` class:

#### Allowed Commands
```python
ALLOWED_COMMANDS = {
    # File operations
    'New-Item', 'Remove-Item', 'Copy-Item', 'Move-Item',
    'Get-ChildItem', 'Get-Content', 'Set-Content',
    
    # Development tools
    'node', 'npm', 'npx', 'yarn', 'git', 'python',
    
    # Linting tools
    'eslint', 'prettier', 'pylint', 'black',
    
    # Add more as needed...
}
```

#### Blocked Patterns
```python
BLOCKED_PATTERNS = [
    r'Invoke-Expression',  # Prevents arbitrary code execution
    r'Start-Process.*-Verb\s+RunAs',  # Prevents elevation
    r'Format-Volume',  # Prevents disk formatting
    # Add more security patterns...
]
```

#### Restricted Paths
```python
RESTRICTED_PATHS = [
    r'C:\\Windows\\System32',
    r'C:\\Program Files',
    # System directories are protected...
]
```

## Usage

### Starting the Server

```powershell
# Using the launcher (if created by setup script)
.\launch_server.ps1

# Or directly with Python
python powershell_mcp_server.py

# Or with virtual environment
.\venv\Scripts\python.exe powershell_mcp_server.py
```

### Available Tools

#### 1. execute_powershell
Execute PowerShell commands safely.

**Parameters:**
- `command` (required): The PowerShell command to execute
- `timeout` (optional): Timeout in seconds (default: 30)

**Example:**
```json
{
  "name": "execute_powershell",
  "arguments": {
    "command": "Get-ChildItem *.js | Measure-Object",
    "timeout": 60
  }
}
```

#### 2. create_file
Create a new file with specified content.

**Parameters:**
- `path` (required): File path to create
- `content` (required): Content to write
- `encoding` (optional): File encoding (default: utf-8)

**Example:**
```json
{
  "name": "create_file",
  "arguments": {
    "path": "package.json",
    "content": "{\n  \"name\": \"my-project\",\n  \"version\": \"1.0.0\"\n}"
  }
}
```

#### 3. read_file
Read the contents of a file.

**Parameters:**
- `path` (required): File path to read
- `encoding` (optional): File encoding (default: utf-8)

#### 4. create_directory
Create a new directory.

**Parameters:**
- `path` (required): Directory path to create

#### 5. list_directory
List contents of a directory.

**Parameters:**
- `path` (optional): Directory to list (default: current)
- `recursive` (optional): List recursively (default: false)

#### 6. run_npm_command
Run npm commands safely.

**Parameters:**
- `command` (required): npm command (e.g., "install", "run build")
- `directory` (optional): Directory to run in (default: current)

**Example:**
```json
{
  "name": "run_npm_command",
  "arguments": {
    "command": "install --save-dev eslint",
    "directory": "./my-project"
  }
}
```

#### 7. run_node_script
Run a Node.js script.

**Parameters:**
- `script` (required): Script file to run
- `args` (optional): Arguments to pass
- `directory` (optional): Directory to run in

#### 8. lint_files
Run linting tools on files.

**Parameters:**
- `tool` (required): Linting tool (eslint, prettier, pylint, black, flake8, mypy)
- `target` (optional): Files/directory to lint (default: current)
- `fix` (optional): Auto-fix issues (default: false)

**Example:**
```json
{
  "name": "lint_files",
  "arguments": {
    "tool": "eslint",
    "target": "src/",
    "fix": true
  }
}
```

#### 9. get_working_directory
Get the current working directory.

#### 10. change_directory
Change the working directory.

**Parameters:**
- `path` (required): Directory to change to

## Common Development Workflows

### Setting Up a New Node.js Project

1. **Create project directory**:
   ```json
   {"name": "create_directory", "arguments": {"path": "my-new-project"}}
   ```

2. **Change to project directory**:
   ```json
   {"name": "change_directory", "arguments": {"path": "my-new-project"}}
   ```

3. **Initialize package.json**:
   ```json
   {"name": "run_npm_command", "arguments": {"command": "init -y"}}
   ```

4. **Install dependencies**:
   ```json
   {"name": "run_npm_command", "arguments": {"command": "install express"}}
   ```

5. **Create main file**:
   ```json
   {
     "name": "create_file",
     "arguments": {
       "path": "index.js",
       "content": "const express = require('express');\nconst app = express();\n\napp.get('/', (req, res) => {\n  res.send('Hello World!');\n});\n\napp.listen(3000, () => {\n  console.log('Server running on port 3000');\n});"
     }
   }
   ```

### Code Quality Workflow

1. **Install linting tools**:
   ```json
   {"name": "run_npm_command", "arguments": {"command": "install --save-dev eslint prettier"}}
   ```

2. **Run linting**:
   ```json
   {"name": "lint_files", "arguments": {"tool": "eslint", "target": "."}}
   ```

3. **Fix linting issues**:
   ```json
   {"name": "lint_files", "arguments": {"tool": "eslint", "target": ".", "fix": true}}
   ```

4. **Format code**:
   ```json
   {"name": "lint_files", "arguments": {"tool": "prettier", "target": ".", "fix": true}}
   ```

## Troubleshooting

### Server Connection Issues

1. **Check Claude Desktop logs**:
   - Windows: `%APPDATA%\Claude\logs\mcp.log`
   - macOS: `~/Library/Logs/Claude/mcp.log`

2. **Verify Python path** in configuration
3. **Ensure all dependencies are installed**
4. **Check file permissions** on the server script

### Command Execution Issues

1. **"Command not in allowed list"**: Add the command to `ALLOWED_COMMANDS` in `SecurityConfig`
2. **"Command contains blocked pattern"**: Review the command for security issues
3. **"Path is restricted"**: Ensure you're not accessing system directories
4. **Timeout errors**: Increase the timeout parameter for long-running commands

### Common Error Messages

- **"Security validation failed"**: The command or path failed security checks
- **"Command timed out"**: The command took longer than the specified timeout
- **"Working directory validation failed"**: The current directory is restricted
- **"Error creating file"**: Check file permissions and path validity

## Security Best Practices

1. **Regularly review** the allowed commands list
2. **Monitor logs** for suspicious activity
3. **Use timeouts** to prevent long-running processes
4. **Keep the server updated** with security patches
5. **Run with minimal privileges** - don't run as administrator
6. **Validate all inputs** before processing
7. **Use virtual environments** to isolate dependencies

## Extending the Server

### Adding New Tools

1. **Create a new tool handler**:
   ```python
   async def _my_new_tool(self, arguments: dict) -> CallToolResult:
       # Implementation here
       pass
   ```

2. **Add tool to the list**:
   ```python
   Tool(
       name="my_new_tool",
       description="Description of what it does",
       inputSchema={...}
   )
   ```

3. **Add to the call handler**:
   ```python
   elif name == "my_new_tool":
       return await self._my_new_tool(arguments)
   ```

### Adding Security Rules

1. **Extend ALLOWED_COMMANDS**:
   ```python
   ALLOWED_COMMANDS = {
       # Existing commands...
       'my-new-command',
   }
   ```

2. **Add blocking patterns**:
   ```python
   BLOCKED_PATTERNS = [
       # Existing patterns...
       r'dangerous-pattern',
   ]
   ```

## Support and Contributing

For issues, feature requests, or contributions:

1. **Check logs** for detailed error information
2. **Review security settings** for command restrictions
3. **Test with simple commands** first
4. **Document any custom modifications** you make

Remember: This server is designed for development tasks. Always follow security best practices and never disable security features in production environments.