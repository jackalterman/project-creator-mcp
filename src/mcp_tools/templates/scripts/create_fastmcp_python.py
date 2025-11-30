import os
import sys
import argparse

def create_fastmcp_python_project(project_name, target_dir):
    project_path = os.path.join(target_dir, project_name)
    os.makedirs(project_path, exist_ok=True)

    # requirements.txt
    with open(os.path.join(project_path, "requirements.txt"), "w") as f:
        f.write("fastmcp\n")

    # main.py
    main_py_content = """from fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("My FastMCP Server")

@mcp.tool()
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers\"\"\"
    return a + b

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    \"\"\"Get a greeting for a name\"\"\"
    return f"Hello, {name}!"

if __name__ == "__main__":
    # Run the server
    mcp.run()
"""
    with open(os.path.join(project_path, "main.py"), "w") as f:
        f.write(main_py_content)

    # README.md
    readme_content = f"""# {project_name}

A FastMCP Python server.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Or use with an MCP client (e.g., Claude Desktop, mcp-cli).
"""
    with open(os.path.join(project_path, "README.md"), "w") as f:
        f.write(readme_content)

    print(f"FastMCP Python project '{project_name}' created at {project_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a FastMCP Python project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--target-dir", default=".", help="Target directory")
    args = parser.parse_args()

    create_fastmcp_python_project(args.project_name, args.target_dir)
