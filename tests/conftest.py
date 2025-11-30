import pytest
import os
import shutil
import tempfile

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    test_dir = tempfile.mkdtemp()
    yield test_dir
    shutil.rmtree(test_dir)

@pytest.fixture
def mock_mcp():
    """Mock MCP instance if needed."""
    pass
