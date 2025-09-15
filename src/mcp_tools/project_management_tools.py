
import os
import json
from typing import Any, Dict, List, Union



from .security import is_safe_path, is_safe_filename, get_file_extension, SecurityConfig
from .project_templates import ProjectTemplates
from .mcp_instance import mcp



@mcp.tool()
def create_project_from_template(
    template_name: str,
    project_name: str,
    project_path: str = "."
) -> Dict[str, Any]:
    """
    Create a new project from a predefined template.
    
    Args:
        template_name: Name of the template to use (react-typescript, node-express-api, python-fastapi)
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
        "html-js-css-single-file": ProjectTemplates.HTML_JS_CSS_SINGLE_FILE,
        "html-js-css-separate-files": ProjectTemplates.HTML_JS_CSS_SEPARATE_FILES,
        "python-django": ProjectTemplates.PYTHON_DJANGO,
        "python-flask": ProjectTemplates.PYTHON_FLASK,
        "blazor-dotnet": ProjectTemplates.BLAZOR_DOTNET,
        "vue-js": ProjectTemplates.VUE_JS,
        "angular-typescript": ProjectTemplates.ANGULAR_TYPESCRIPT,
        "go-gin-api": ProjectTemplates.GO_GIN_API
    }
    
    if template_name not in templates:
        return {
            "success": False,
            "error": f"Template not found: {template_name}",
            "available_templates": list(templates.keys())
        }
    
    template = templates[template_name]
    
    try:
        # Create project directory
        full_project_path = os.path.join(project_path, project_name)
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
            "error": f"npm command failed: {str(e)}"
        }

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
        "html-js-css-single-file": ProjectTemplates.HTML_JS_CSS_SINGLE_FILE,
        "html-js-css-separate-files": ProjectTemplates.HTML_JS_CSS_SEPARATE_FILES,
        "python-django": ProjectTemplates.PYTHON_DJANGO,
        "python-flask": ProjectTemplates.PYTHON_FLASK,
        "blazor-dotnet": ProjectTemplates.BLAZOR_DOTNET,
        "vue-js": ProjectTemplates.VUE_JS,
        "angular-typescript": ProjectTemplates.ANGULAR_TYPESCRIPT,
        "go-gin-api": ProjectTemplates.GO_GIN_API
    }
    
    template_list = []
    for name, template in templates.items():
        template_list.append({
            "name": name,
            "display_name": template["name"],
            "description": template["description"],
            "file_count": len(template["files"])
        })
    
    return {
        "success": True,
        "templates": template_list,
        "total_count": len(template_list)
    }
