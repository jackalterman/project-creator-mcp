# Multi-stage Dockerfile for Project Creator MCP Server
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm (required for JavaScript/TypeScript templates)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose the MCP server (stdio-based, no port needed)
# The server communicates via stdin/stdout

# Create a volume mount point for project creation
VOLUME ["/workspace"]

# Set the default working directory for created projects
WORKDIR /workspace

# Run the MCP server
CMD ["python", "/app/project_builder.py"]
