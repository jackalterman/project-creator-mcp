import os
import json

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')

def _load_template_files(template_name):
    template_path = os.path.join(TEMPLATES_DIR, template_name)
    files = {}
    for root, _, filenames in os.walk(template_path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, template_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Attempt to parse as JSON if it's a .json file
                if filename.endswith('.json'):
                    try:
                        files[relative_path] = json.loads(content)
                    except json.JSONDecodeError:
                        files[relative_path] = content
                else:
                    files[relative_path] = content
    return files

class ProjectTemplates:
    '''Pre-defined project templates for common development scenarios.'''
    
    REACT_TYPESCRIPT = {
        "name": "React TypeScript",
        "description": "Modern React application with TypeScript",
        "files": _load_template_files("react_typescript")
    }
    
    NODE_EXPRESS_API = {
        "name": "Node.js Express API",
        "description": "RESTful API server with Express.js and TypeScript",
        "files": _load_template_files("node_express_api")
    }
    
    PYTHON_FASTAPI = {
        "name": "Python FastAPI",
        "description": "Modern Python API with FastAPI",
        "files": _load_template_files("python_fastapi")
    }
    
    NEXTJS_SHADCN_TAILWIND = {
        "name": "Next.js ShadCN/UI Tailwind",
        "description": "Next.js project with ShadCN/UI components and Tailwind CSS",
        "files": _load_template_files("nextjs_shadcn_tailwind")
    }
    
    HTML_JS_CSS_SINGLE_FILE = {
        "name": "HTML/JS/CSS (Single File)",
        "description": "Basic HTML page with embedded JavaScript and CSS",
        "files": _load_template_files("html_js_css_single_file")
    }
    
    HTML_JS_CSS_SEPARATE_FILES = {
        "name": "HTML/JS/CSS (Separate Files)",
        "description": "Basic HTML page with external JavaScript and CSS files",
        "files": _load_template_files("html_js_css_separate_files")
    }
    
    PYTHON_DJANGO = {
        "name": "Python Django",
        "description": "Full-stack web framework for perfectionists with deadlines",
        "files": _load_template_files("python_django")
    }
    
    PYTHON_FLASK = {
        "name": "Python Flask",
        "description": "Lightweight WSGI web application framework",
        "files": _load_template_files("python_flask")
    }
    
    BLAZOR_DOTNET = {
        "name": "Blazor .NET",
        "description": "Web application using Blazor and .NET",
        "files": _load_template_files("blazor_dotnet")
    }

    VUE_JS = {
        "name": "Vue.js Application",
        "description": "A basic Vue.js project with a single component.",
        "files": _load_template_files("vue_js")
    }

    ANGULAR_TYPESCRIPT = {
        "name": "Angular TypeScript Application",
        "description": "A basic Angular project with TypeScript.",
        "files": _load_template_files("angular_typescript")
    }

    GO_GIN_API = {
        "name": "Go Gin API",
        "description": "A basic Go API using the Gin web framework.",
        "files": _load_template_files("go_gin_api")
    }
