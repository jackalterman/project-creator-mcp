# Project Creator MCP

## Overview

`project-creator-mcp` is a command-line tool designed to streamline the creation of new project structures from a collection of predefined templates. It helps developers quickly set up the boilerplate for various types of applications, including web frontends, backends, and full-stack projects. This project also functions as an MCP (Model Context Protocol) server, allowing integration with MCP clients like Claude Desktop for enhanced interactive development.

## Features

*   **Multiple Project Templates**: Supports a variety of popular project types (e.g., HTML/JS/CSS, Next.js, Node.js/Express, Django, FastAPI, Flask, React).
*   **Easy Project Generation**: Simple command-line interface to select a template and create a new project.
*   **Extensible**: Easily add new project templates to expand the tool's capabilities.
*   **MCP Server**: Exposes a set of tools via the Model Context Protocol for programmatic interaction.

## Prerequisites

Before installation, ensure you have:

*   **Python 3.8+** installed and accessible via `python` command
*   **pip** (Python package installer)
*   **Claude Desktop** (if using with Claude or other MCP clients)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/project-creator-mcp.git
    cd project-creator-mcp
    ```
2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\Activate.ps1
    # On macOS/Linux:
    source venv/bin/activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Running as an MCP Server

The `project_builder.py` script is designed to be run as an MCP server, allowing MCP clients (like Claude Desktop) to interact with its exposed tools programmatically.

To start the MCP server:

```bash
# Ensure your virtual environment is activated if you created one
python project_builder.py
```

The server will start and listen for MCP client connections.

### Claude Desktop Configuration

1.  **Locate your Claude Desktop configuration file**:
    *   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
    *   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

2.  **Add the MCP server configuration**:
    Add an entry under `"mcpServers"` in your `claude_desktop_config.json`. Replace `/path/to/your/project-creator-mcp/project_builder.py` with the actual absolute path to the `project_builder.py` file in your cloned repository.

    ```json
    {
      "mcpServers": {
        "project-creator-mcp": {
          "command": "python",
          "args": ["/path/to/your/project-creator-mcp/project_builder.py"],
          "env": {
            "PYTHONUNBUFFERED": "1"
          }
        }
      }
    }
    ```
    *Note: The `PYTHONUNBUFFERED: "1"` environment variable is often helpful for ensuring real-time output from Python processes in some environments.*

3.  **Restart Claude Desktop** to load the new server.

## Available MCP Tools

This MCP server exposes the following tools:

### File System Tools (`file_system_tools.py`)

*   **`create_file(path: str, content: str, overwrite: bool = False)`**: Create a file with specified content.
*   **`read_file(path: str)`**: Read file contents.
*   **`create_directory(path: str)`**: Create a directory.
*   **`list_directory(path: str = ".")`**: List directory contents with detailed information.
*   **`copy_file_or_directory(source: str, destination: str)`**: Copy a file or directory to a new location.
*   **`search_and_replace_in_file(file_path: str, search_pattern: str, replacement: str, use_regex: bool = False)`**: Search and replace text in a file.

### Project Management Tools (`project_management_tools.py`)

*   **`create_project_from_template(template_name: str, project_name: str, project_path: str = ".")`**: Create a new project from a predefined template.
    *   `template_name`: Name of the template (e.g., "react-typescript", "node-express-api").
    *   `project_name`: Name for the new project.
    *   `project_path`: Directory where project should be created (default: current directory).
*   **`create_project_structure(project_name: str, structure: Dict[str, Union[str, Dict]], base_path: str = ".")`**: Create a custom project structure from a nested dictionary.
*   **`get_project_info(path: str = ".")`**: Get information about a project directory.
*   **`list_available_templates()`**: List all available project templates.

### Command Execution Tools (`command_execution_tools.py`)

*   **`run_npm_command(command: str, cwd: str = ".")`**: Execute npm commands safely.
*   **`run_python_command(command: str, cwd: str = ".")`**: Execute Python commands safely (pip, python scripts, etc.).
*   **`run_command(command: str, cwd: str = ".")`**: Generic command runner, dispatches to `run_python_command`.
*   **`initialize_git_repository(path: str = ".")`**: Initialize a Git repository in the specified directory.

## Available Templates

The following templates are currently available:

*   `html_js_css_separate_files`: A simple web project with separate HTML, JavaScript, and CSS files.
*   `html_js_css_single_file`: A simple web project with HTML, JavaScript, and CSS all in one file.
*   `nextjs_shadcn_tailwind`: A Next.js project configured with Shadcn UI and Tailwind CSS.
*   `node_express_api`: A basic Node.js Express API project.
*   `python_django`: A basic Django project structure.
*   `python_fastapi`: A basic FastAPI project.
*   `python_flask`: A basic Flask web application with a simple template.
*   `react_typescript`: A React project set up with TypeScript.

## Adding New Templates

For instructions on how to add your own custom project templates, please refer to the `Adding New Templates.md` file.

## Contributing

Contributions are welcome! If you have suggestions for new templates, improvements, or bug fixes, please open an issue or submit a pull request.
