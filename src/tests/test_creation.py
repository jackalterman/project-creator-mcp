import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Mock mcp.tool decorator
import sys
from unittest.mock import MagicMock

# Create a mock module for mcp_instance
mock_mcp_instance = MagicMock()
mock_mcp = MagicMock()
# Define tool as a pass-through decorator that adds .fn
def mock_tool():
    def decorator(func):
        class ToolWrapper:
            def __init__(self, fn):
                self.fn = fn
            def __call__(self, *args, **kwargs):
                return self.fn(*args, **kwargs)
        return ToolWrapper(func)
    return decorator
mock_mcp.tool = mock_tool
mock_mcp_instance.mcp = mock_mcp

# Inject into sys.modules
sys.modules['src.mcp_tools.mcp_instance'] = mock_mcp_instance
# Also inject for relative import if needed, but since we import from src.mcp_tools.project_management_tools
# which does `from .mcp_instance import mcp`, we need to make sure it picks up our mock.
# Since we are running as a script, imports might be tricky.
# Let's try to patch it by pre-importing.

from src.mcp_tools.project_management_tools import create_project_from_template

def test_vue_creation():
    print("Testing Vue.js project creation...")
    result = create_project_from_template(
        template_name="vue-js",
        project_name="test-vue-project",
        project_path="."
    )
    print(result)

if __name__ == "__main__":
    test_vue_creation()
