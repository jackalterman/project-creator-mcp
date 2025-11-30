#!/usr/bin/env python3
"""
Docker Compose Template Generator
Creates a Docker Compose project structure with multi-service setup
"""

import os
import sys
import argparse

DOCKER_COMPOSE_TEMPLATES = {
    "full-stack": """version: '3.8'

services:
  # Web Application
  web:
    build:
      context: ./web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/appdb
      - REDIS_URL=redis://cache:6379
    depends_on:
      - db
      - cache
    networks:
      - app-network
    volumes:
      - ./web:/app
      - /app/node_modules
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=appdb
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  cache:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Nginx Reverse Proxy (Optional)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    networks:
      - app-network
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:

networks:
  app-network:
    driver: bridge
""",
    "simple": """version: '3.8'

services:
  # Application
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
    volumes:
      - .:/app
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Database
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=database
    ports:
      - "5432:5432"
    volumes:
      - db-data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  db-data:
"""
}

ENV_TEMPLATE = """# Application Configuration
NODE_ENV=development
PORT=3000

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/appdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=appdb

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Add your application-specific environment variables here
"""

NGINX_CONFIG = """events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:3000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
"""

README_TEMPLATE = """# {project_name}

Docker Compose multi-service application.

## Services

{services_description}

## Prerequisites

- Docker and Docker Compose installed on your system

## Quick Start

### 1. Configure Environment Variables

Copy the example environment file and update values:

```bash
cp .env.example .env
```

Edit `.env` with your configuration.

### 2. Start All Services

```bash
docker-compose up -d
```

### 3. View Logs

```bash
docker-compose logs -f
```

### 4. Stop All Services

```bash
docker-compose down
```

## Common Commands

### Build and start services
```bash
docker-compose up --build -d
```

### View running services
```bash
docker-compose ps
```

### View logs for specific service
```bash
docker-compose logs -f <service-name>
```

### Execute command in service
```bash
docker-compose exec <service-name> <command>
```

### Restart a service
```bash
docker-compose restart <service-name>
```

### Stop and remove all containers, networks, and volumes
```bash
docker-compose down -v
```

## Service URLs

{service_urls}

## Development

For development with live reload, the source code is mounted as a volume.
Changes to your code will be reflected immediately.

## Production Deployment

For production:
1. Update environment variables in `.env`
2. Remove volume mounts for source code
3. Use specific version tags for images
4. Configure proper secrets management
5. Set up SSL/TLS certificates for nginx
6. Configure monitoring and logging

## Troubleshooting

### Services not starting
```bash
docker-compose logs <service-name>
```

### Reset everything
```bash
docker-compose down -v
docker-compose up --build -d
```

### Check service health
```bash
docker-compose ps
```
"""

WEB_DOCKERFILE = """FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
"""

WEB_PACKAGE_JSON = """{
  "name": "{project_name}-web",
  "version": "1.0.0",
  "description": "Web application",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  }
}
"""

WEB_INDEX_JS = """const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy' });
});

// Main endpoint
app.get('/', (req, res) => {
    res.send('<h1>Hello from Docker Compose!</h1>');
});

app.listen(port, '0.0.0.0', () => {
    console.log(`Server running on port ${port}`);
});
"""

SERVICES_INFO = {
    "full-stack": """- **web**: Node.js web application (port 3000)
- **db**: PostgreSQL database (port 5432)
- **cache**: Redis cache (port 6379)
- **nginx**: Nginx reverse proxy (ports 80, 443)""",
    "simple": """- **app**: Main application (port 8000)
- **db**: PostgreSQL database (port 5432)"""
}

SERVICE_URLS = {
    "full-stack": """- Web Application: http://localhost:3000
- Nginx Proxy: http://localhost:80
- PostgreSQL: localhost:5432
- Redis: localhost:6379""",
    "simple": """- Application: http://localhost:8000
- PostgreSQL: localhost:5432"""
}

def create_docker_compose_project(project_name, template_type="simple"):
    """Create a Docker Compose project structure"""
    
    # Validate template type
    if template_type not in DOCKER_COMPOSE_TEMPLATES:
        print(f"Error: Unsupported template type '{template_type}'. Supported: {', '.join(DOCKER_COMPOSE_TEMPLATES.keys())}")
        sys.exit(1)
    
    # Create project directory
    os.makedirs(project_name, exist_ok=True)
    
    # Create docker-compose.yml
    compose_path = os.path.join(project_name, "docker-compose.yml")
    with open(compose_path, 'w') as f:
        f.write(DOCKER_COMPOSE_TEMPLATES[template_type])
    
    # Create .env.example
    env_path = os.path.join(project_name, ".env.example")
    with open(env_path, 'w') as f:
        f.write(ENV_TEMPLATE)
    
    # Create README
    readme_path = os.path.join(project_name, "README.md")
    with open(readme_path, 'w') as f:
        f.write(README_TEMPLATE.format(
            project_name=project_name,
            services_description=SERVICES_INFO[template_type],
            service_urls=SERVICE_URLS[template_type]
        ))
    
    # Create additional files for full-stack template
    if template_type == "full-stack":
        # Create web directory
        web_dir = os.path.join(project_name, "web")
        os.makedirs(web_dir, exist_ok=True)
        
        # Create web Dockerfile
        web_dockerfile = os.path.join(web_dir, "Dockerfile")
        with open(web_dockerfile, 'w') as f:
            f.write(WEB_DOCKERFILE)
        
        # Create web package.json
        web_package = os.path.join(web_dir, "package.json")
        with open(web_package, 'w') as f:
            f.write(WEB_PACKAGE_JSON.format(project_name=project_name))
        
        # Create web index.js
        web_index = os.path.join(web_dir, "index.js")
        with open(web_index, 'w') as f:
            f.write(WEB_INDEX_JS)
        
        # Create nginx directory
        nginx_dir = os.path.join(project_name, "nginx")
        os.makedirs(nginx_dir, exist_ok=True)
        
        # Create nginx config
        nginx_conf = os.path.join(nginx_dir, "nginx.conf")
        with open(nginx_conf, 'w') as f:
            f.write(NGINX_CONFIG)
    
    print(f"✓ Docker Compose project '{project_name}' created successfully!")
    print(f"  Template: {template_type}")
    print(f"  Files created:")
    print(f"    - docker-compose.yml")
    print(f"    - .env.example")
    print(f"    - README.md")
    if template_type == "full-stack":
        print(f"    - web/Dockerfile")
        print(f"    - web/package.json")
        print(f"    - web/index.js")
        print(f"    - nginx/nginx.conf")

def main():
    parser = argparse.ArgumentParser(description='Create a Docker Compose project template')
    parser.add_argument('project_name', help='Name of the project')
    parser.add_argument('--type', choices=['simple', 'full-stack'], 
                       default='simple', help='Template type (default: simple)')
    
    args = parser.parse_args()
    create_docker_compose_project(args.project_name, args.type)

if __name__ == '__main__':
    main()
