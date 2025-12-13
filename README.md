# Project Creator MCP

## Overview

`project-creator-mcp` is a **Model Context Protocol (MCP) server** built with [FastMCP](https://github.com/jlowin/fastmcp) that enables AI assistants to create, manage, and scaffold complete project structures. It provides a comprehensive suite of tools for file system operations, project generation from templates, and command execution—all accessible through natural language interactions with MCP-compatible AI clients like Claude Desktop, Cline, and others.

Whether you're building a simple HTML page, a full-stack web application, or a containerized microservice, this tool streamlines project setup and lets you focus on writing code.

## Features

*   **🚀 23+ Project Templates**: Pre-configured templates for popular frameworks and languages including React, Next.js, Vue, Angular, FastAPI, Flask, Django, Express, Go Gin, and more
*   **☁️ Infrastructure as Code**: Terraform templates for Kubernetes clusters (AWS EKS, Azure AKS, GCP GKE) with complete deployment workflows
*   **🐳 Docker Support**: Templates for Dockerfiles and Docker Compose configurations (Python, Node.js, Go, full-stack setups)
*   **🤖 AI-Native Interface**: Natural language project creation through MCP-compatible AI assistants
*   **📁 File System Tools**: Create, read, copy, and manage files and directories programmatically
*   **⚡ Command Execution**: Safe execution of npm, Python, Terraform, Docker, and system commands with proper error handling
*   **🔧 Extensible**: Easily add custom templates using Python generator scripts
*   **🎯 FastMCP Powered**: Built on FastMCP for optimal performance and developer experience

## Prerequisites

*   **Python 3.8+** installed and accessible via `python` command
*   **pip** (Python package installer)
*   **Node.js and npm** (for JavaScript/TypeScript templates)
*   **Terraform** (for Infrastructure as Code templates - optional)
*   **Docker** (for Docker templates - optional)
*   **MCP-compatible AI client** (Claude Desktop, Cline, or other MCP clients)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/jackalterman/project-creator-mcp.git
    cd project-creator-mcp
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

### Claude Desktop

1.  **Locate your Claude Desktop configuration file**:
    *   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
    *   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

2.  **Add the MCP server configuration**:
    ```json
    {
      "mcpServers": {
        "project-creator": {
          "command": "python",
          "args": ["C:\\absolute\\path\\to\\project-creator-mcp\\project_builder.py"],
          "env": {
            "PYTHONUNBUFFERED": "1"
          }
        }
      }
    }
    ```
    *Replace the path with the actual absolute path to `project_builder.py` on your system.*

3.  **Restart Claude Desktop** to load the MCP server.

### Other MCP Clients

For other MCP clients (Cline, etc.), refer to their documentation for configuring MCP servers. The server runs via:
```bash
python project_builder.py
```

## Sample AI Prompts

Here are real-world examples of how to interact with AI assistants using this MCP server:

### Basic Web Projects

```
Create a simple weather app using HTML, CSS, and JavaScript. 
Use C:\temp\weather-app as the project path. 
Use the separate files template.
```

```
Build a photo gallery web app with a modern glassmorphic design. 
Create it in D:\Projects\photo-gallery. 
Use the single-file HTML template and make it responsive.
```

### React & Next.js Projects

```
Create a React TypeScript app for a task manager. 
Use C:\dev\task-manager. 
After creating the project, install axios and react-router-dom.
```

```
Build a Next.js app with ShadCN UI and Tailwind CSS for a blog platform. 
Use D:\Projects\my-blog. 
Initialize it with the nextjs_shadcn_tailwind template.
```

### Backend APIs

```
Create a FastAPI project for a REST API that manages user authentication. 
Use C:\backend\auth-api. 
After setup, add endpoints for login, register, and token refresh.
```

```
Build a Node.js Express API for a product catalog. 
Create it in D:\apis\product-service. 
Use TypeScript and set up basic CRUD routes.
```

```
Create a Flask web app with a simple blog template. 
Use C:\temp\flask-blog. 
Set up routes for home, about, and blog posts.
```

### Docker & DevOps

```
Create a Dockerfile for a Python FastAPI application. 
Use C:\temp\my-api-docker. 
Use multi-stage builds for optimization.
```

```
Set up a full-stack Docker Compose configuration with a web app, 
PostgreSQL database, Redis cache, and Nginx reverse proxy. 
Create it in D:\docker-projects\fullstack-app.
```

```
Create a web app that displays real-time stock prices. 
Use C:\temp\stock-tracker. 
Build it with the HTML template, then create a Dockerfile for it, 
and finally set up a docker-compose.yml to run it with a Redis cache.
Build and run everything in Docker, then test it in the browser.
```

### MCP Server Development

```
Create a FastMCP Python server for managing todo lists. 
Use C:\mcp-servers\todo-server. 
Add tools for creating, reading, updating, and deleting todos.
```

```
Build a Node.js MCP server that integrates with a weather API. 
Create it in D:\mcp\weather-mcp. 
Use the fast_mcp_node template.
```

### Terraform / Infrastructure as Code

```
Create a Terraform configuration for deploying an AWS EKS cluster. 
Use D:\terraform\eks-cluster. 
After creation, initialize Terraform and run a plan to see what will be created.
```

```
Build a complete Azure AKS infrastructure with Terraform. 
Create it in C:\terraform\aks-production. 
Set up the cluster with 3 nodes and auto-scaling enabled. 
After creating the project, run terraform init and terraform plan.
```

```
Create a GCP GKE cluster using Terraform. 
Use D:\terraform\gke-cluster. 
Configure it as a regional cluster with private nodes. 
Initialize Terraform, run a plan, and if it looks good, apply it to deploy the cluster.
```

```
Deploy a complete EKS cluster on AWS:
1. Create the Terraform EKS project in C:\terraform\my-eks
2. Customize the variables to use t3.large instances
3. Initialize Terraform
4. Review the plan
5. Apply the configuration to create the cluster
6. Once deployed, configure kubectl and verify the cluster is running
```

### Advanced Workflows

```
Create a full-stack e-commerce platform:
1. Use Next.js with ShadCN UI for the frontend in C:\projects\ecommerce\frontend
2. Create a FastAPI backend in C:\projects\ecommerce\backend
3. Set up Docker Compose to run both services
4. Initialize Git repositories for both projects
5. Build and test everything in Docker
```

```
Build a microservices architecture:
1. Create a Go Gin API gateway in C:\microservices\gateway
2. Create a Python FastAPI user service in C:\microservices\users
3. Create a Node.js Express product service in C:\microservices\products
4. Set up a full-stack Docker Compose configuration
5. Test all services are communicating properly
```

## Available Templates

### Web Frontend
*   **`html_js_css_separate_files`**: Modern HTML5 page with external CSS and JavaScript files
*   **`html_js_css_single_file`**: Single-file HTML page with embedded styles and scripts
*   **`react_typescript`**: React application with TypeScript configuration
*   **`nextjs_shadcn_tailwind`**: Next.js with ShadCN UI components and Tailwind CSS
*   **`nextjs_auto`**: Next.js with default settings (non-interactive setup)
*   **`vue_js`**: Vue.js application with Vue CLI
*   **`angular_typescript`**: Angular application with TypeScript

### Backend APIs
*   **`node_express_api`**: Node.js Express API with TypeScript
*   **`python_fastapi`**: FastAPI application with modern Python async patterns
*   **`python_flask`**: Flask web application with basic template structure
*   **`python_django`**: Django project with standard configuration
*   **`go_gin_api`**: Go API using the Gin web framework

### MCP Servers
*   **`fast_mcp_python`**: FastMCP Python server template
*   **`fast_mcp_node`**: FastMCP Node.js server template

### Docker & DevOps
*   **`docker_python`**: Multi-stage Dockerfile for Python applications
*   **`docker_node`**: Multi-stage Dockerfile for Node.js applications
*   **`docker_go`**: Multi-stage Dockerfile for Go applications
*   **`docker_compose_simple`**: Simple Docker Compose with app and database
*   **`docker_compose_full_stack`**: Full-stack Docker Compose (web, database, cache, nginx)

### Infrastructure as Code (Terraform)
*   **`terraform_eks`**: Terraform configuration for AWS Elastic Kubernetes Service with VPC, node groups, and auto-scaling
*   **`terraform_aks`**: Terraform configuration for Azure Kubernetes Service with VNet, monitoring, and auto-scaling
*   **`terraform_gke`**: Terraform configuration for Google Kubernetes Engine with VPC, private nodes, and Workload Identity

## Available MCP Tools

### Project Management Tools

*   **`create_project_from_template(template_name, project_name, project_path)`**  
    Create a new project from a predefined template
    *   `template_name`: Template identifier (e.g., "react_typescript", "python_fastapi")
    *   `project_name`: Name for the new project
    *   `project_path`: Directory where project should be created (default: current directory)

*   **`list_available_templates()`**  
    List all available project templates with descriptions

*   **`create_project_structure(project_name, structure, base_path)`**  
    Create a custom project structure from a nested dictionary

*   **`get_project_info(path)`**  
    Get information about a project directory (files, structure, metadata)

### File System Tools

*   **`create_file(path, content, overwrite)`**  
    Create a file with specified content

*   **`read_file(path)`**  
    Read and return file contents

*   **`create_directory(path)`**  
    Create a directory (creates parent directories if needed)

*   **`list_directory(path)`**  
    List directory contents with detailed information

*   **`copy_file_or_directory(source, destination)`**  
    Copy a file or directory to a new location

*   **`search_and_replace_in_file(file_path, search_pattern, replacement, use_regex)`**  
    Search and replace text in a file (supports regex)

### Command Execution Tools

*   **`run_npm_command(command, cwd)`**  
    Execute npm commands safely (install, build, start, etc.)

*   **`run_python_command(command, cwd)`**  
    Execute Python commands safely (pip, scripts, etc.)

*   **`run_terraform_command(command, cwd)`**  
    Execute Terraform commands safely (init, plan, apply, destroy, etc.)

*   **`run_command(command, cwd, input)`**  
    Generic command runner with optional input for interactive prompts

*   **`initialize_git_repository(path)`**  
    Initialize a Git repository in the specified directory

## Adding New Templates

To add custom templates, see the [`Adding New Templates.md`](Adding%20New%20Templates.md) guide. Templates can be:
*   **Command-based**: Execute CLI tools (e.g., `create-react-app`, `django-admin`)
*   **Script-based**: Use Python generator scripts for custom structures

## Security

This MCP server includes security features:
*   Path validation to prevent directory traversal attacks
*   Command sanitization for safe execution
*   Configurable allowed directories and commands
*   Input validation for all tool parameters

## Contributing

Contributions are welcome! To contribute:
1.  Fork the repository
2.  Create a feature branch (`git checkout -b feature/amazing-template`)
3.  Commit your changes (`git commit -m 'Add amazing template'`)
4.  Push to the branch (`git push origin feature/amazing-template`)
5.  Open a Pull Request

## License

This project is open source and available under the MIT License.

## Acknowledgments

*   Built with [FastMCP](https://github.com/jlowin/fastmcp) by jlowin
*   Inspired by the Model Context Protocol specification
*   Thanks to all contributors and template creators

---

**Need help?** Open an issue on GitHub or check the [Adding New Templates](Adding%20New%20Templates.md) guide for customization options.
