#!/usr/bin/env python3
"""
Docker Project Template Generator
Creates a Docker project structure with Dockerfile, .dockerignore, and README
"""

import os
import sys
import argparse

DOCKERFILE_TEMPLATES = {
    "python": """# Multi-stage build for Python application
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
""",
    "node": """# Multi-stage build for Node.js application
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Final stage
FROM node:20-alpine

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /app/node_modules ./node_modules

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Run the application
CMD ["node", "index.js"]
""",
    "go": """# Multi-stage build for Go application
FROM golang:1.21-alpine as builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Copy the binary from builder
COPY --from=builder /app/main .

# Expose port
EXPOSE 8080

# Run the application
CMD ["./main"]
"""
}

DOCKERIGNORE_TEMPLATE = """# Git
.git
.gitignore
.gitattributes

# CI/CD
.github
.gitlab-ci.yml
.travis.yml

# Documentation
README.md
CHANGELOG.md
docs/

# Dependencies
node_modules/
venv/
env/
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd

# Build outputs
dist/
build/
*.egg-info/
target/

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Logs
*.log
logs/

# Environment
.env
.env.local
.env.*.local

# Testing
coverage/
.coverage
*.test
test/
tests/
"""

README_TEMPLATE = """# {project_name}

Docker-based {app_type} application.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, for multi-container setups)

## Building the Docker Image

```bash
docker build -t {project_name}:latest .
```

## Running the Container

```bash
docker run -p {port}:{port} {project_name}:latest
```

## Docker Compose (Optional)

If using Docker Compose:

```bash
docker-compose up -d
```

To stop:

```bash
docker-compose down
```

## Environment Variables

Configure the following environment variables:

- `PORT` - Application port (default: {port})
- Add your application-specific variables here

## Development

For development with live reload, mount your source code as a volume:

```bash
docker run -p {port}:{port} -v $(pwd):/app {project_name}:latest
```

## Common Docker Commands

### View running containers
```bash
docker ps
```

### View logs
```bash
docker logs <container-id>
```

### Stop container
```bash
docker stop <container-id>
```

### Remove container
```bash
docker rm <container-id>
```

### Remove image
```bash
docker rmi {project_name}:latest
```

## Production Deployment

For production, consider:
- Using specific version tags instead of `latest`
- Setting up health checks
- Configuring resource limits
- Using secrets management for sensitive data
- Setting up monitoring and logging
"""

SAMPLE_APP_FILES = {
    "python": {
        "main.py": """#!/usr/bin/env python3
\"\"\"Sample Python application\"\"\"

import os
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>Hello from Docker!</h1>')

def main():
    port = int(os.getenv('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f'Server running on port {port}')
    server.serve_forever()

if __name__ == '__main__':
    main()
""",
        "requirements.txt": "# Add your Python dependencies here\n"
    },
    "node": {
        "index.js": """const http = require('http');

const port = process.env.PORT || 3000;

const server = http.createServer((req, res) => {
    res.statusCode = 200;
    res.setHeader('Content-Type', 'text/html');
    res.end('<h1>Hello from Docker!</h1>');
});

server.listen(port, '0.0.0.0', () => {
    console.log(`Server running on port ${port}`);
});
""",
        "package.json": """{
  "name": "{project_name}",
  "version": "1.0.0",
  "description": "Docker-based Node.js application",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {}
}
"""
    },
    "go": {
        "main.go": """package main

import (
\t"fmt"
\t"log"
\t"net/http"
\t"os"
)

func handler(w http.ResponseWriter, r *http.Request) {
\tfmt.Fprintf(w, "<h1>Hello from Docker!</h1>")
}

func main() {
\tport := os.Getenv("PORT")
\tif port == "" {
\t\tport = "8080"
\t}

\thttp.HandleFunc("/", handler)
\tlog.Printf("Server running on port %s", port)
\tlog.Fatal(http.ListenAndServe(":"+port, nil))
}
""",
        "go.mod": """module {project_name}

go 1.21
""",
        "go.sum": ""
    }
}

PORT_DEFAULTS = {
    "python": 8000,
    "node": 3000,
    "go": 8080
}

def create_docker_project(project_name, app_type="python"):
    """Create a Docker project structure"""
    
    # Validate app type
    if app_type not in DOCKERFILE_TEMPLATES:
        print(f"Error: Unsupported app type '{app_type}'. Supported: {', '.join(DOCKERFILE_TEMPLATES.keys())}")
        sys.exit(1)
    
    # Create project directory
    os.makedirs(project_name, exist_ok=True)
    
    # Create Dockerfile
    dockerfile_path = os.path.join(project_name, "Dockerfile")
    with open(dockerfile_path, 'w') as f:
        f.write(DOCKERFILE_TEMPLATES[app_type])
    
    # Create .dockerignore
    dockerignore_path = os.path.join(project_name, ".dockerignore")
    with open(dockerignore_path, 'w') as f:
        f.write(DOCKERIGNORE_TEMPLATE)
    
    # Create README
    readme_path = os.path.join(project_name, "README.md")
    port = PORT_DEFAULTS[app_type]
    with open(readme_path, 'w') as f:
        f.write(README_TEMPLATE.format(
            project_name=project_name,
            app_type=app_type.capitalize(),
            port=port
        ))
    
    # Create sample application files
    if app_type in SAMPLE_APP_FILES:
        for filename, content in SAMPLE_APP_FILES[app_type].items():
            file_path = os.path.join(project_name, filename)
            with open(file_path, 'w') as f:
                # Only format with project_name - content doesn't have other placeholders
                formatted_content = content.replace("{project_name}", project_name)
                f.write(formatted_content)
    
    print(f"✓ Docker project '{project_name}' created successfully!")
    print(f"  Type: {app_type}")
    print(f"  Files created:")
    print(f"    - Dockerfile")
    print(f"    - .dockerignore")
    print(f"    - README.md")
    for filename in SAMPLE_APP_FILES.get(app_type, {}).keys():
        print(f"    - {filename}")

def main():
    parser = argparse.ArgumentParser(description='Create a Docker project template')
    parser.add_argument('project_name', help='Name of the project')
    parser.add_argument('--type', choices=['python', 'node', 'go'], 
                       default='python', help='Application type (default: python)')
    
    args = parser.parse_args()
    create_docker_project(args.project_name, args.type)

if __name__ == '__main__':
    main()
