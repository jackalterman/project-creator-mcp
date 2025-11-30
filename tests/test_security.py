import pytest
import os
from src.mcp_tools.security import is_safe_path, is_safe_filename, get_file_extension
from src.config import SecurityConfig

def test_is_safe_path_valid(temp_dir):
    safe_path = os.path.join(temp_dir, "test.txt")
    is_safe, msg = is_safe_path(safe_path)
    assert is_safe
    assert msg == "Path is safe"

def test_is_safe_path_restricted():
    # Test a known restricted path
    restricted = SecurityConfig.RESTRICTED_PATHS[0]
    is_safe, msg = is_safe_path(restricted)
    assert not is_safe
    assert "Access to restricted path" in msg

def test_is_safe_filename_valid():
    is_safe, msg = is_safe_filename("test.txt")
    assert is_safe

def test_is_safe_filename_invalid():
    invalid_names = ["..", "test/file", "test\\file", "test:file"]
    for name in invalid_names:
        is_safe, msg = is_safe_filename(name)
        assert not is_safe

def test_get_file_extension():
    assert get_file_extension("test.txt") == ".txt"
    assert get_file_extension("test.tar.gz") == ".gz"
    assert get_file_extension("test") == ""
