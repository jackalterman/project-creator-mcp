import os
import json
from typing import Any, Dict, List, Union



from .security import is_safe_path, is_safe_filename, get_file_extension
from src.config import SecurityConfig
from .project_templates import ProjectTemplates, TEMPLATES_DIR
from .mcp_instance import mcp
from .command_execution_tools import run_npm_command, run_npx_command, run_command, run_python_command

@mcp.tool()
def create_project_from_template(
    template_name: str,
    project_name: str,
    project_path: str = "."
) -> Dict[str, Any]:
    """
    Create a new project from a predefined template.
    
    IMPORTANT FOR AI: If none of the available templates fit the user's needs, you should:
    1. Use create_project_structure() to create a custom project layout
    2. Use write_file() or other file tools to create necessary files
    3. Use run_npm_command(), run_python_command(), run_docker_command(), etc. to set up the environment
    4. Consider using Docker to run any technology stack (Ruby, PHP, Rust, etc.)
    
    Examples of custom setups:
    - Ruby on Rails: Use Docker with ruby:latest image
    - PHP/Laravel: Use Docker with php:apache image
    - Rust: Use Docker with rust:latest image
    - Apache/Bash scripts: Create files manually and use Docker
    - Any other stack: Combine file creation + Docker + command execution
    
    Args:
        template_name: Name of the template to use (react-typescript, node-express-api, python-fastapi, etc.)
                      Run list_available_templates() to see all options.
        project_name: Name for the new project
        project_path: Directory where project should be created (default: current directory)
        
    Returns:
        Dictionary with creation results
    """
    # Validate inputs
    is_safe, message = is_safe_path(project_path)
    if not is_safe:
        return {
            "success": False,
            "error": f"Project path blocked: {message}"
        }
    
    is_safe, message = is_safe_filename(project_name)
    if not is_safe:
        return {
            "success": False,
            "error": f"Invalid project name: {message}"
        }
    
    # Get template
    templates = {
        "react-typescript": ProjectTemplates.REACT_TYPESCRIPT,
        "node-express-api": ProjectTemplates.NODE_EXPRESS_API,
        "python-fastapi": ProjectTemplates.PYTHON_FASTAPI,
        "nextjs-shadcn-tailwind": ProjectTemplates.NEXTJS_SHADCN_TAILWIND,
        "nextjs-auto": ProjectTemplates.NEXTJS_AUTO,
        "html-js-css-single-file": ProjectTemplates.HTML_JS_CSS_SINGLE_FILE,
        "html-js-css-separate-files": ProjectTemplates.HTML_JS_CSS_SEPARATE_FILES,
        "python-django": ProjectTemplates.PYTHON_DJANGO,
        "python-flask": ProjectTemplates.PYTHON_FLASK,
        "vue-js": ProjectTemplates.VUE_JS,
        "angular-typescript": ProjectTemplates.ANGULAR_TYPESCRIPT,
        "go-gin-api": ProjectTemplates.GO_GIN_API,
        "fastmcp-python": ProjectTemplates.FAST_MCP_PYTHON,
        "fastmcp-node": ProjectTemplates.FAST_MCP_NODE,
        "docker-python": ProjectTemplates.DOCKER_PYTHON,
        "docker-node": ProjectTemplates.DOCKER_NODE,
        "docker-go": ProjectTemplates.DOCKER_GO,
        "docker-compose-simple": ProjectTemplates.DOCKER_COMPOSE_SIMPLE,
        "docker-compose-full-stack": ProjectTemplates.DOCKER_COMPOSE_FULL_STACK
    }
    
    if template_name not in templates:
        return {
            "success": False,
            "error": f"Template not found: {template_name}",
            "available_templates": list(templates.keys())
        }
    
    template = templates[template_name]
    
    try:
        full_project_path = os.path.join(project_path, project_name)

        if template.get("type") == "command_based":
            # Format command with project name and templates directory
            command = template["command"].format(
                project_name=project_name, 
                templates_dir=TEMPLATES_DIR
            )
            
            # Determine which command runner to use
            # Determine which command runner to use
            if "npx" in command:
                # Strip 'npx ' prefix if present to avoid duplication (e.g. 'npx npx ...')
                clean_command = command.replace("npx ", "", 1) if command.startswith("npx ") else command
                result = run_npx_command.fn(command=clean_command, cwd=project_path)
            elif "npm" in command:
                # Strip 'npm ' prefix if present
                clean_command = command.replace("npm ", "", 1) if command.startswith("npm ") else command
                result = run_npm_command.fn(command=clean_command, cwd=project_path)
            elif command.startswith("python"):
                result = run_python_command.fn(command=command, cwd=project_path)
            else:
                result = run_command.fn(command=command, cwd=project_path)
            
            if result.get("success"):
                # Additional steps for nextjs-shadcn-tailwind
                if template_name == "nextjs-shadcn-tailwind":
                    # Install Tailwind CSS
                    tailwind_install_result = run_npm_command.fn(command="install -D tailwindcss postcss autoprefixer", cwd=full_project_path)
                    if not tailwind_install_result.get("success"):
                        return {
                            "success": False,
                            "error": f"Tailwind CSS installation failed: {tailwind_install_result.get('stderr', tailwind_install_result.get('error'))}"
                        }
                    
                    # Initialize Tailwind config
                    tailwind_init_result = run_npx_command.fn(command="tailwindcss init -p", cwd=full_project_path)
                    if not tailwind_init_result.get("success"):
                        return {
                            "success": False,
                            "error": f"Tailwind CSS initialization failed: {tailwind_init_result.get('stderr', tailwind_init_result.get('error'))}"
                        }
                    
                    # Initialize Shadcn UI
                    shadcn_result = run_npx_command.fn(command="shadcn-ui@latest init --default", cwd=full_project_path)
                    if not shadcn_result.get("success"):
                        return {
                            "success": False,
                            "error": f"Shadcn UI initialization failed: {shadcn_result.get('stderr', shadcn_result.get('error'))}"
                        }
                    
                    return {
                        "success": True,
                        "message": f"Project '{project_name}' created successfully with Next.js, Tailwind CSS, and Shadcn UI.",
                        "template": template_name,
                        "project_path": full_project_path,
                        "next_steps": f"1. cd {project_name}\n2. Configure Tailwind CSS and Shadcn UI as per their documentation."
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Project '{project_name}' created successfully using command: {command}",
                        "template": template_name,
                        "project_path": full_project_path,
                        "next_steps": f"1. cd {project_name}\n2. Follow README.md instructions (if any)"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Command '{command}' failed: {result.get('stderr', result.get('error'))}"
                }
        else: # file_based template
            os.makedirs(full_project_path, exist_ok=True)
            
            created_files = []
            
            # Create files from template
            for file_path, content in template["files"].items():
                full_file_path = os.path.join(full_project_path, file_path)
                
                # Create subdirectories if needed
                os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
                
                # Write file content
                if isinstance(content, dict):
                    # JSON content
                    with open(full_file_path, 'w', encoding='utf-8') as f:
                        json.dump(content, f, indent=2)
                else:
                    # Text content
                    with open(full_file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                created_files.append(file_path)
            
            return {
                "success": True,
                "message": f"Project '{project_name}' created successfully",
                "template": template_name,
                "project_path": full_project_path,
                "files_created": created_files,
                "next_steps": f"1. cd {project_name}\n2. Follow README.md instructions"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Project creation failed: {str(e)}"}

@mcp.tool()
def create_project_structure(
    project_name: str,
    structure: Dict[str, Union[str, Dict]],
    base_path: str = "."
) -> Dict[str, Any]:
    """
    Create a custom project structure from a nested dictionary.
    
    Args:
        project_name: Name of the project directory
        structure: Nested dictionary defining the project structure
        base_path: Base directory to create project in (default: current directory)
        
    Returns:
        Dictionary with creation results
    """
    # Validate inputs
    is_safe, message = is_safe_path(base_path)
    if not is_safe:
        return {
            "success": False,
            "error": f"Base path blocked: {message}"
        }
    
    is_safe, message = is_safe_filename(project_name)
    if not is_safe:
        return {
            "success": False,
            "error": f"Invalid project name: {message}"
        }
    
    def create_structure_recursive(current_path: str, structure_dict: Dict[str, Union[str, Dict]]) -> List[str]:
        """Recursively create directory structure and files."""
        created_items = []
        
        for name, content in structure_dict.items():
            item_path = os.path.join(current_path, name)
            
            if isinstance(content, dict):
                # It's a directory
                os.makedirs(item_path, exist_ok=True)
                created_items.append(f"📁 {item_path}")
                # Recurse into subdirectory
                sub_items = create_structure_recursive(item_path, content)
                created_items.extend(sub_items)
            else:
                # It's a file
                # Validate file extension
                ext = get_file_extension(name)
                if ext and ext not in SecurityConfig.ALLOWED_EXTENSIONS:
                    continue  # Skip disallowed file types
                
                # Create parent directory if needed
                os.makedirs(os.path.dirname(item_path), exist_ok=True)
                
                # Write file content
                with open(item_path, 'w', encoding='utf-8') as f:
                    f.write(str(content))
                created_items.append(f"📄 {item_path}")
        
        return created_items
    
    try:
        # Create project root directory
        project_path = os.path.join(base_path, project_name)
        os.makedirs(project_path, exist_ok=True)
        
        # Create the structure
        created_items = [f"📁 {project_path}"]
        structure_items = create_structure_recursive(project_path, structure)
        created_items.extend(structure_items)
        
        return {
            "success": True,
            "message": f"Project structure created successfully: {project_name}",
            "project_path": project_path,
            "items_created": created_items,
            "total_items": len(created_items)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create project structure: {str(e)}"
        }

@mcp.tool()
def update_project_state(
    project_path: str,
    current_phase: str,
    progress_summary: str,
    completed_tasks: List[str] = None,
    current_task: str = None,
    next_steps: List[str] = None,
    blockers: List[str] = None,
    context: str = None,
    file_structure: Dict[str, str] = None
) -> Dict[str, Any]:
    """
    Update the project state file to track progress and enable resuming work.
    
    This is critical for complex projects that may hit token limits. Save state after
    each major step so AI can resume exactly where it left off.
    
    Args:
        project_path: Path to the project directory
        current_phase: Current phase (e.g., "Setup", "Implementation", "Testing", "Deployment")
        progress_summary: Brief summary of what's been accomplished
        completed_tasks: List of completed tasks
        current_task: Description of the task currently in progress
        next_steps: List of next steps to take
        blockers: List of any blockers or issues
        context: Important context needed to resume work
        file_structure: Dictionary of key files and their purpose
        
    Returns:
        Dictionary with update results
    """
    # Validate path safety
    is_safe, message = is_safe_path(project_path)
    if not is_safe:
        return {
            "success": False,
            "error": f"Project path blocked: {message}"
        }
    
    try:
        # Ensure project directory exists
        if not os.path.exists(project_path):
            os.makedirs(project_path, exist_ok=True)
        
        # Get project name from path
        project_name = os.path.basename(os.path.abspath(project_path))
        
        # Create state file content
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        state_content = f"""# Project State: {project_name}

**Last Updated**: {timestamp}
**Current Phase**: {current_phase}

## Progress Summary

{progress_summary}

"""
        
        # Add completed tasks
        if completed_tasks:
            state_content += "## Completed Tasks\n\n"
            for task in completed_tasks:
                state_content += f"- [x] {task}\n"
            state_content += "\n"
        
        # Add current task
        if current_task:
            state_content += f"## Current Task\n\n- [/] {current_task}\n\n"
        
        # Add next steps
        if next_steps:
            state_content += "## Next Steps\n\n"
            for i, step in enumerate(next_steps, 1):
                state_content += f"{i}. {step}\n"
            state_content += "\n"
        
        # Add blockers
        if blockers:
            state_content += "## Blockers/Issues\n\n"
            for blocker in blockers:
                state_content += f"- ⚠️ {blocker}\n"
            state_content += "\n"
        
        # Add context
        if context:
            state_content += f"## Context\n\n{context}\n\n"
        
        # Add file structure
        if file_structure:
            state_content += "## File Structure\n\n"
            for file_path, description in file_structure.items():
                state_content += f"- `{file_path}`: {description}\n"
            state_content += "\n"
        
        # Add instructions for AI
        state_content += """---

## Instructions for AI

When resuming work on this project:
1. Read this state file first using `get_project_state()`
2. Review the progress summary and completed tasks
3. Check for any blockers that need resolution
4. Continue with the next steps listed above
5. Update this state file after completing each major step
"""
        
        # Write state file
        state_file_path = os.path.join(project_path, ".project-state.md")
        with open(state_file_path, 'w', encoding='utf-8') as f:
            f.write(state_content)
        
        return {
            "success": True,
            "message": "Project state updated successfully",
            "state_file": state_file_path,
            "current_phase": current_phase,
            "timestamp": timestamp
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update project state: {str(e)}"
        }

@mcp.tool()
def get_project_state(project_path: str) -> Dict[str, Any]:
    """
    Read the project state file to understand current progress and resume work.
    
    Use this when:
    - Starting work on an existing project
    - Resuming after hitting token limits
    - Understanding what's been done and what's next
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Dictionary with project state information
    """
    # Validate path safety
    is_safe, message = is_safe_path(project_path)
    if not is_safe:
        return {
            "success": False,
            "error": f"Project path blocked: {message}"
        }
    
    try:
        state_file_path = os.path.join(project_path, ".project-state.md")
        
        if not os.path.exists(state_file_path):
            return {
                "success": False,
                "error": "No project state file found",
                "suggestion": "This project may not have state tracking enabled. Use update_project_state() to create one."
            }
        
        # Read state file
        with open(state_file_path, 'r', encoding='utf-8') as f:
            state_content = f.read()
        
        # Parse basic information (simple parsing)
        lines = state_content.split('\n')
        state_data = {
            "raw_content": state_content,
            "state_file": state_file_path
        }
        
        # Extract key information
        for line in lines:
            if line.startswith("**Last Updated**:"):
                state_data["last_updated"] = line.split(":", 1)[1].strip()
            elif line.startswith("**Current Phase**:"):
                state_data["current_phase"] = line.split(":", 1)[1].strip()
        
        return {
            "success": True,
            "state": state_data,
            "message": "Project state loaded successfully. Review the raw_content for full details."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read project state: {str(e)}"
        }

@mcp.tool()
def get_project_info(path: str = ".") -> Dict[str, Any]:
    """
    Get information about a project directory.
    
    Args:
        path: Project directory path (default: current directory)
        
    Returns:
        Dictionary with project information
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
                "error": "Directory does not exist"
            }
        
        project_info = {
            "path": os.path.abspath(path),
            "name": os.path.basename(os.path.abspath(path)),
            "type": "unknown"
        }
        
        # Detect project type
        config_files = {
            "package.json": "node",
            "requirements.txt": "python",
            "Pipfile": "python",
            "pyproject.toml": "python",
            "Cargo.toml": "rust",
            "pom.xml": "java",
            "build.gradle": "java",
            "composer.json": "php",
            "Gemfile": "ruby",
            "go.mod": "go"
        }
        
        detected_types = []
        config_info = {}
        
        for config_file, project_type in config_files.items():
            config_path = os.path.join(path, config_file)
            if os.path.exists(config_path):
                detected_types.append(project_type)
                
                # Extract specific info from config files
                try:
                    if config_file == "package.json":
                        with open(config_path, 'r', encoding='utf-8') as f:
                            package_data = json.load(f)
                        config_info["package.json"] = {
                            "name": package_data.get("name"),
                            "version": package_data.get("version"),
                            "description": package_data.get("description"),
                            "scripts": list(package_data.get("scripts", {}).keys())
                        }
                    elif config_file == "requirements.txt":
                        with open(config_path, 'r', encoding='utf-8') as f:
                            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                        config_info["requirements.txt"] = {
                            "dependencies": len(requirements),
                            "packages": requirements[:10]  # First 10 packages
                        }
                except Exception:
                    # If we can't parse the config, just note it exists
                    config_info[config_file] = {"exists": True}
        
        project_info["type"] = detected_types[0] if detected_types else "unknown"
        project_info["detected_types"] = detected_types
        project_info["config_files"] = config_info
        
        # Check for Git repository
        git_path = os.path.join(path, '.git')
        project_info["git_repository"] = os.path.exists(git_path)
        
        # Get directory stats
        total_files = 0
        total_dirs = 0
        file_extensions = {}
        
        for root, dirs, files in os.walk(path):
            # Skip common build/dependency directories
            dirs[:] = [d for d in dirs if d not in [
                'node_modules', '.git', '__pycache__', '.venv', 'venv',
                'env', 'build', 'dist', '.next', 'target'
            ]]
            
            total_dirs += len(dirs)
            total_files += len(files)
            
            for file in files:
                ext = get_file_extension(file)
                if ext:
                    file_extensions[ext] = file_extensions.get(ext, 0) + 1
        
        project_info["stats"] = {
            "total_files": total_files,
            "total_directories": total_dirs,
            "file_extensions": dict(sorted(file_extensions.items(), key=lambda x: x[1], reverse=True)[:10])
        }
        
        return {
            "success": True,
            "project_info": project_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get project info: {str(e)}"
        }

@mcp.tool()
def list_available_templates() -> Dict[str, Any]:
    """
    List all available project templates.
    
    Returns:
        Dictionary with template information
    """
    templates = {
        "react-typescript": ProjectTemplates.REACT_TYPESCRIPT,
        "node-express-api": ProjectTemplates.NODE_EXPRESS_API,
        "python-fastapi": ProjectTemplates.PYTHON_FASTAPI,
        "nextjs-shadcn-tailwind": ProjectTemplates.NEXTJS_SHADCN_TAILWIND,
        "nextjs-auto": ProjectTemplates.NEXTJS_AUTO,
        "html-js-css-single-file": ProjectTemplates.HTML_JS_CSS_SINGLE_FILE,
        "html-js-css-separate-files": ProjectTemplates.HTML_JS_CSS_SEPARATE_FILES,
        "python-django": ProjectTemplates.PYTHON_DJANGO,
        "python-flask": ProjectTemplates.PYTHON_FLASK,
        "vue-js": ProjectTemplates.VUE_JS,
        "angular-typescript": ProjectTemplates.ANGULAR_TYPESCRIPT,
        "go-gin-api": ProjectTemplates.GO_GIN_API,
        "fastmcp-python": ProjectTemplates.FAST_MCP_PYTHON,
        "fastmcp-node": ProjectTemplates.FAST_MCP_NODE,
        "docker-python": ProjectTemplates.DOCKER_PYTHON,
        "docker-node": ProjectTemplates.DOCKER_NODE,
        "docker-go": ProjectTemplates.DOCKER_GO,
        "docker-compose-simple": ProjectTemplates.DOCKER_COMPOSE_SIMPLE,
        "docker-compose-full-stack": ProjectTemplates.DOCKER_COMPOSE_FULL_STACK
    }
    
    template_list = []
    for name, template in templates.items():
        template_list.append({
            "name": name,
            "display_name": template["name"],
            "description": template["description"],
            "file_count": len(template.get("files", []))
        })
    
    return {
        "success": True,
        "templates": template_list,
        "total_count": len(template_list)
    }

@mcp.tool()
def get_tool_usage_guide() -> str:
    """
    Returns a guide for AI agents on how to use this MCP server's tools effectively.
    
    Returns:
        Markdown-formatted usage guide.
    """
    return """
# Project Creator MCP Usage Guide

This MCP server provides tools for scaffolding and managing software projects.

## Recommended Workflow

1. **Explore Templates**: Always start by listing available templates to see what's supported.
   - Tool: `list_available_templates()`
   
2. **Create Project**: Use a template to scaffold a new project.
   - Tool: `create_project_from_template(template_name, project_name)`
   - Example: `create_project_from_template("python-fastapi", "my-api")`
   
3. **Inspect Project**: After creation, or when working with an existing project, get details about it.
   - Tool: `get_project_info(path)`

## Key Tools

### `create_project_from_template`
- **Purpose**: Scaffolds a new project from a pre-defined template.
- **Best For**: Standard projects like React, FastAPI, Node.js, Docker, etc.
- **Note**: This handles dependency installation (e.g., `npm install`) automatically for most templates.

### `create_project_structure`
- **Purpose**: Creates a custom directory and file structure from a dictionary.
- **Best For**: Custom project layouts that don't fit existing templates.

### `get_project_info`
- **Purpose**: Analyzes a directory to identify project type, config files, and stats.
- **Best For**: Understanding the context of an existing project.

## Docker Development & Debugging

### Running Code in Docker Containers
You can use Docker containers for development, testing, and debugging:

**Pull any Docker image you need:**
```python
run_docker_command(command="pull python:3.11-slim")
run_docker_command(command="pull node:20-alpine")
run_docker_command(command="pull postgres:15")
```

**Run code in isolated containers:**
```python
# Run Python script in container
run_docker_command(
    command="run --rm -v $(pwd):/app -w /app python:3.11-slim python script.py"
)

# Start development server in container
run_docker_command(
    command="run -d -p 8000:8000 -v $(pwd):/app -w /app python:3.11-slim python -m http.server 8000"
)
```

**Debug inside running containers:**
```python
# Execute commands in running container
run_docker_command(command="exec my-container ls -la /app")
run_docker_command(command="exec my-container cat /app/logs/error.log")

# Interactive debugging
run_docker_command(command="exec -it my-container /bin/bash")
```

**Database operations in containers:**
```python
# Run PostgreSQL query in container
run_database_command(
    command='psql -U postgres -d mydb -c "SELECT * FROM users"',
    db_type="postgresql",
    docker_container="my-postgres-container"
)

# Import SQL script
run_database_command(
    command="psql -U postgres -d mydb",
    db_type="postgresql",
    docker_container="my-postgres-container",
    input=sql_script_content
)
```

### Docker Compose for Multi-Service Development
```python
# Start all services
run_docker_compose_command(command="up -d", cwd="./my-app")

# View logs
run_docker_compose_command(command="logs -f web", cwd="./my-app")

# Execute commands in service
run_docker_command(command="exec my-app-web-1 npm test")

# Stop services
run_docker_compose_command(command="down", cwd="./my-app")
```

### Debugging Workflow Example
When debugging issues:
1. Check container logs: `run_docker_command(command="logs my-container")`
2. Inspect container: `run_docker_command(command="inspect my-container")`
3. Execute diagnostic commands: `run_docker_command(command="exec my-container <diagnostic-cmd>")`
4. Access database: `run_database_command(...)` with docker_container parameter
5. Test fixes by rebuilding: `run_docker_command(command="build -t my-app .")`

## Testing Generated Code

### Web Applications
Use `test_web_application` to verify web apps are working:
```python
test_web_application(
    url="http://localhost:3000",
    test_type="accessibility"  # or "functionality", "performance"
)
```

### API Endpoints
Test APIs directly:
```python
test_web_application(
    url="http://localhost:8000/api/users",
    test_type="functionality"
)
```

## Command Execution Tools

### Available Commands
- `run_npm_command` - Node.js package management
- `run_npx_command` - Execute npm packages
- `run_python_command` - Python/pip commands
- `run_go_command` - Go commands
- `run_docker_command` - Docker operations (pull, run, exec, build, etc.)
- `run_docker_compose_command` - Multi-container orchestration
- `run_database_command` - PostgreSQL, MySQL, SQLite, MongoDB
- `run_command` - Safe system commands

### Docker Image Permissions
**You are allowed to pull ANY Docker images needed to complete tasks:**
- Official images: `python`, `node`, `golang`, `postgres`, `mysql`, `redis`, `nginx`, etc.
- Community images: Any image from Docker Hub or other registries
- Use cases: Testing, debugging, development, building, deployment

## Tips for AI Agents

- **Paths**: Always use relative paths (e.g., `.`) or absolute paths provided by the user. Default to c:\temp\ if no path is provided.
- **Project Names**: Use kebab-case (e.g., `my-cool-project`) for project names to ensure compatibility across OSs.
- **Verification**: After creating a project, it's good practice to list the directory contents or read the `README.md` to confirm success.
- **Docker First**: When debugging or testing, consider using Docker containers for isolation and consistency.
- **Database Development**: Use Docker containers for databases to avoid local installation requirements.
- **Iterative Testing**: Build, test, debug, and rebuild using Docker commands in a loop until issues are resolved.

## Building Custom Projects (Beyond Templates)

**IMPORTANT**: You are NOT limited to the predefined templates! If the user needs a technology stack that isn't listed, you can build it yourself.

### When to Build Custom

If the user requests:
- Ruby on Rails, PHP/Laravel, Rust, Elixir, Scala, etc.
- Apache with bash scripts
- Custom combinations (e.g., Svelte + Deno)
- Specialized frameworks not in templates
- Legacy or niche technologies

**Don't say "template not available" - BUILD IT!**

### How to Build Custom Projects

**Approach 1: Docker-Based (Recommended)**
```python
# 1. Create project structure
create_project_structure(
    project_name="my-rails-app",
    structure={
        "app": {},
        "config": {},
        "Dockerfile": "FROM ruby:3.2\\nRUN gem install rails\\n...",
        "docker-compose.yml": "..."
    }
)

# 2. Pull necessary images
run_docker_command(command="pull ruby:3.2")

# 3. Initialize the project in container
run_docker_command(
    command="run --rm -v $(pwd)/my-rails-app:/app -w /app ruby:3.2 rails new ."
)
```

**Approach 2: File-Based**
```python
# Create custom project files directly
from file_tools import write_file

# Create PHP project
write_file("my-php-app/index.php", "<?php echo 'Hello'; ?>")
write_file("my-php-app/Dockerfile", "FROM php:8.2-apache\\nCOPY . /var/www/html")

# Create Rust project  
write_file("my-rust-app/Cargo.toml", "[package]\\nname = 'my-app'\\n...")
write_file("my-rust-app/src/main.rs", "fn main() { println!(\\\"Hello\\\"); }")
```

**Approach 3: Command-Based**
```python
# Use existing CLIs via Docker
run_docker_command(
    command="run --rm -v $(pwd):/app -w /app composer create-project laravel/laravel my-app"
)

run_docker_command(
    command="run --rm -v $(pwd):/app -w /app elixir mix phx.new my_app"
)
```

### Technology Stack Examples

**Ruby on Rails:**
- Docker image: `ruby:3.2`
- Init: `rails new app_name`
- Run: `rails server`

**PHP/Laravel:**
- Docker image: `php:8.2-apache` or `composer`
- Init: `composer create-project laravel/laravel`
- Run: `php artisan serve`

**Rust:**
- Docker image: `rust:latest`
- Init: `cargo new app_name`
- Run: `cargo run`

**Elixir/Phoenix:**
- Docker image: `elixir:latest`
- Init: `mix phx.new app_name`
- Run: `mix phx.server`

**Apache + Bash:**
- Docker image: `httpd:latest`
- Create: Custom .sh scripts + HTML
- Run: Apache serves static content

### Remember

- **Any technology is possible** with Docker
- **Combine tools**: file creation + Docker + commands
- **Test as you build**: Use test_web_application() to verify
- **Document**: Create README.md with setup instructions

## Project State Management (Critical for Complex Projects)

**IMPORTANT**: For complex projects that may hit token limits, use state management to save progress and resume work seamlessly.

### When to Save State

Save state after:
- Completing a major phase (setup, implementation, testing)
- Creating significant files or structure
- Before running long-running commands
- After encountering blockers
- Every 3-5 major steps

### How to Use State Management

**Save State:**
```python
update_project_state(
    project_path="c:/temp/my-app",
    current_phase="Implementation",
    progress_summary="Created project structure, set up Docker, implemented auth module",
    completed_tasks=[
        "Created project directory structure",
        "Set up Dockerfile and docker-compose.yml",
        "Implemented user authentication",
        "Created database schema"
    ],
    current_task="Implementing API endpoints for user management",
    next_steps=[
        "Create REST API endpoints (GET, POST, PUT, DELETE)",
        "Add input validation",
        "Write unit tests",
        "Test with Postman/curl"
    ],
    blockers=[
        "Need to decide on pagination strategy"
    ],
    context="Using FastAPI with PostgreSQL. Auth uses JWT tokens. Database connection in db.py.",
    file_structure={
        "main.py": "FastAPI application entry point",
        "auth.py": "Authentication and JWT handling",
        "db.py": "Database connection and models",
        "Dockerfile": "Multi-stage build for production"
    }
)
```

**Resume Work:**
```python
# First thing when resuming
state = get_project_state(project_path="c:/temp/my-app")

# Review the state
print(state["state"]["raw_content"])

# Continue with next steps from the state file
```

### State File Format

The `.project-state.md` file is created in the project root and includes:
- Last updated timestamp
- Current phase
- Progress summary
- Completed tasks (checklist)
- Current task in progress
- Next steps (numbered list)
- Blockers/issues
- Important context
- File structure with descriptions
- Instructions for AI to resume

### Best Practices

1. **Update frequently** - Don't wait until hitting token limits
2. **Be specific** - Include exact commands, file paths, decisions made
3. **Note blockers** - Document anything that needs user input
4. **Provide context** - Explain architectural decisions, why certain approaches were chosen
5. **List next steps** - Make it easy to continue without re-analyzing

### Example Workflow

```python
# 1. Start project
create_project_from_template("docker-python", "my-api", "c:/temp")

# 2. Save initial state
update_project_state(
    project_path="c:/temp/my-api",
    current_phase="Setup",
    progress_summary="Created project from template",
    next_steps=["Customize Dockerfile", "Add dependencies", "Create API structure"]
)

# 3. Do work...
# ... make changes ...

# 4. Update state after major step
update_project_state(
    project_path="c:/temp/my-api",
    current_phase="Implementation",
    progress_summary="Customized Docker setup, added FastAPI dependencies",
    completed_tasks=["Updated Dockerfile", "Added requirements.txt"],
    next_steps=["Create API routes", "Add database models"]
)

# 5. If token limit hit, user can resume by:
# - Opening new conversation
# - Running: get_project_state("c:/temp/my-api")
# - Continuing from next steps
```