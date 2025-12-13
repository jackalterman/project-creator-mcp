import os
import json

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')

import os
import json

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')

class ProjectTemplates:
    '''Pre-defined project templates for common development scenarios.'''
    
    REACT_TYPESCRIPT = {
        "name": "React TypeScript",
        "description": "Modern React application with TypeScript",
        "type": "command_based",
        "command": "npx create-react-app {project_name} --template typescript"
    }
    
    NODE_EXPRESS_API = {
        "name": "Node.js Express API",
        "description": "RESTful API server with Express.js and TypeScript",
        "type": "command_based",
        "command": "npx express-generator-typescript {project_name}"
    }
    
    PYTHON_FASTAPI = {
        "name": "Python FastAPI",
        "description": "Modern Python API with FastAPI",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_fastapi.py\" {project_name}"
    }
    
    NEXTJS_SHADCN_TAILWIND = {
        "name": "Next.js ShadCN/UI Tailwind",
        "description": "Next.js project with ShadCN/UI components and Tailwind CSS",
        "type": "command_based",
        "command": "npx create-next-app@latest {project_name}"
    }

    NEXTJS_AUTO = {
        "name": "Next.js (Auto)",
        "description": "Next.js project with default settings (no prompts)",
        "type": "command_based",
        "command": "npx create-next-app@latest {project_name} --yes"
    }
    
    HTML_JS_CSS_SINGLE_FILE = {
        "name": "HTML/JS/CSS (Single File)",
        "description": "Basic HTML page with embedded JavaScript and CSS",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_html.py\" {project_name} --type single"
    }
    
    HTML_JS_CSS_SEPARATE_FILES = {
        "name": "HTML/JS/CSS (Separate Files)",
        "description": "Basic HTML page with external JavaScript and CSS files",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_html.py\" {project_name} --type separate"
    }
    
    PYTHON_DJANGO = {
        "name": "Python Django",
        "description": "Full-stack web framework for perfectionists with deadlines",
        "type": "command_based",
        "command": "python -m pip install django && python -m django startproject {project_name}"
    }
    
    PYTHON_FLASK = {
        "name": "Python Flask",
        "description": "Lightweight WSGI web application framework",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_flask.py\" {project_name}"
    }

    VUE_JS = {
        "name": "Vue.js Application",
        "description": "A basic Vue.js project with a single component.",
        "type": "command_based",
        "command": "npx @vue/cli create {project_name} --default --packageManager npm"
    }

    ANGULAR_TYPESCRIPT = {
        "name": "Angular TypeScript Application",
        "description": "A basic Angular project with TypeScript.",
        "type": "command_based",
        "command": "npx -p @angular/cli ng new {project_name} --defaults"
    }

    GO_GIN_API = {
        "name": "Go Gin API",
        "description": "A basic Go API using the Gin web framework.",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_go_gin.py\" {project_name}"
    }

    FAST_MCP_PYTHON = {
        "name": "FastMCP Python Server",
        "description": "A lightweight MCP server using the FastMCP Python library.",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_fastmcp_python.py\" {project_name}"
    }

    FAST_MCP_NODE = {
        "name": "FastMCP Node.js Server",
        "description": "A basic MCP server using the Node.js SDK.",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_fastmcp_node.py\" {project_name}"
    }

    DOCKER_PYTHON = {
        "name": "Docker Python",
        "description": "Dockerfile for Python applications with multi-stage build",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_docker.py\" {project_name} --type python"
    }

    DOCKER_NODE = {
        "name": "Docker Node.js",
        "description": "Dockerfile for Node.js applications with multi-stage build",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_docker.py\" {project_name} --type node"
    }

    DOCKER_GO = {
        "name": "Docker Go",
        "description": "Dockerfile for Go applications with multi-stage build",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_docker.py\" {project_name} --type go"
    }

    DOCKER_COMPOSE_SIMPLE = {
        "name": "Docker Compose Simple",
        "description": "Simple Docker Compose setup with app and database",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_docker_compose.py\" {project_name} --type simple"
    }

    DOCKER_COMPOSE_FULL_STACK = {
        "name": "Docker Compose Full Stack",
        "description": "Full-stack Docker Compose with web, database, cache, and nginx",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_docker_compose.py\" {project_name} --type full-stack"
    }

    TERRAFORM_EKS = {
        "name": "Terraform AWS EKS",
        "description": "Terraform configuration for AWS Elastic Kubernetes Service (EKS) with VPC, node groups, and auto-scaling",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_terraform_eks.py\" {project_name}"
    }

    TERRAFORM_AKS = {
        "name": "Terraform Azure AKS",
        "description": "Terraform configuration for Azure Kubernetes Service (AKS) with VNet, monitoring, and auto-scaling",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_terraform_aks.py\" {project_name}"
    }

    TERRAFORM_GKE = {
        "name": "Terraform GCP GKE",
        "description": "Terraform configuration for Google Kubernetes Engine (GKE) with VPC, private nodes, and Workload Identity",
        "type": "command_based",
        "command": "python \"{templates_dir}/scripts/create_terraform_gke.py\" {project_name}"
    }

