import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Mock mcp.tool decorator
mock_mcp_instance = MagicMock()
mock_mcp = MagicMock()
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

sys.modules['src.mcp_tools.mcp_instance'] = mock_mcp_instance

from src.mcp_tools.project_management_tools import get_tool_usage_guide

def test_usage_guide():
    print("Testing get_tool_usage_guide...")
    guide = get_tool_usage_guide()
    print(guide)

if __name__ == "__main__":
    test_usage_guide()
