import os
import sys
import argparse
import json

def create_fastmcp_node_project(project_name, target_dir):
    project_path = os.path.join(target_dir, project_name)
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, "src"), exist_ok=True)

    # package.json
    package_json = {
        "name": project_name,
        "version": "0.1.0",
        "description": "A FastMCP Node.js server",
        "type": "module",
        "main": "build/index.js",
        "scripts": {
            "build": "tsc",
            "start": "node build/index.js",
            "dev": "tsc --watch"
        },
        "dependencies": {
            "@modelcontextprotocol/sdk": "^0.6.0",
            "zod": "^3.23.8"
        },
        "devDependencies": {
            "@types/node": "^20.11.0",
            "typescript": "^5.3.3"
        }
    }
    with open(os.path.join(project_path, "package.json"), "w") as f:
        json.dump(package_json, f, indent=2)

    # tsconfig.json
    tsconfig = {
        "compilerOptions": {
            "target": "ES2022",
            "module": "Node16",
            "moduleResolution": "Node16",
            "outDir": "./build",
            "rootDir": "./src",
            "strict": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "forceConsistentCasingInFileNames": True
        },
        "include": ["src/**/*"]
    }
    with open(os.path.join(project_path, "tsconfig.json"), "w") as f:
        json.dump(tsconfig, f, indent=2)

    # src/index.ts
    index_ts_content = """import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// Create an MCP server
const server = new McpServer({
  name: "my-fastmcp-server",
  version: "1.0.0",
});

// Add a tool
server.tool(
  "add",
  "Add two numbers",
  {
    a: z.number(),
    b: z.number(),
  },
  async ({ a, b }) => {
    return {
      content: [
        {
          type: "text",
          text: String(a + b),
        },
      ],
    };
  }
);

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("FastMCP Node Server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
"""
    with open(os.path.join(project_path, "src", "index.ts"), "w") as f:
        f.write(index_ts_content)

    # README.md
    readme_content = f"""# {project_name}

A FastMCP Node.js server.

## Installation

```bash
npm install
```

## Usage

```bash
npm run build
npm start
```
"""
    with open(os.path.join(project_path, "README.md"), "w") as f:
        f.write(readme_content)

    print(f"FastMCP Node project '{project_name}' created at {project_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a FastMCP Node project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--target-dir", default=".", help="Target directory")
    args = parser.parse_args()

    create_fastmcp_node_project(args.project_name, args.target_dir)
