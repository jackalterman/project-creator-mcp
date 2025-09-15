
#!/usr/bin/env python3
"""
Project Builder FastMCP Server

A comprehensive Model Context Protocol server for project creation, management,
and development tasks using FastMCP for optimal performance.
"""



from src.mcp_tools.project_templates import ProjectTemplates
from src.mcp_tools.security import *
from src.mcp_tools.file_system_tools import *
from src.mcp_tools.project_management_tools import *
from src.mcp_tools.command_execution_tools import *
from src.mcp_tools.mcp_instance import mcp


if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()
