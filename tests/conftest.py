import pytest
import os
import shutil
import tempfile

def _force_remove(func, path, exc_info):
    """rmtree error handler: git marks object files read-only, which blocks deletion on Windows."""
    import stat
    os.chmod(path, stat.S_IWRITE)
    func(path)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    test_dir = tempfile.mkdtemp()
    yield test_dir
    shutil.rmtree(test_dir, onerror=_force_remove)

@pytest.fixture(autouse=True)
def isolated_trash(tmp_path, monkeypatch):
    """Keep delete_file's trash out of the real ~/.project-creator-mcp during tests."""
    monkeypatch.setenv("PROJECT_CREATOR_TRASH", str(tmp_path / "_trash"))


@pytest.fixture
def mock_mcp():
    """Mock MCP instance if needed."""
    pass
