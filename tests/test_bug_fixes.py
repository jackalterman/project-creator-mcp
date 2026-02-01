import pytest
import os
from unittest.mock import patch
from src.mcp_tools.security import is_safe_filename
from src.mcp_tools.file_system_tools import delete_file, write_file
from src.mcp_tools.command_execution_tools import run_git_command

def test_dotfile_security():
    # Should be safe now
    assert is_safe_filename(".gitignore")[0] == True
    assert is_safe_filename(".env")[0] == True
    assert is_safe_filename(".config")[0] == True
    
    # Should be unsafe
    assert is_safe_filename(".")[0] == False
    assert is_safe_filename("..")[0] == False
    assert is_safe_filename("foo..bar")[0] == False # Contains ".."
    assert is_safe_filename("/etc/passwd")[0] == False

def test_delete_file(temp_dir):
    # Create file
    f = os.path.join(temp_dir, "to_delete.txt")
    with open(f, 'w') as file:
        file.write("bye")
    
    # Delete
    result = delete_file.fn(f)
    assert result["success"]
    assert not os.path.exists(f)
    
    # Delete non-existent
    result = delete_file.fn(f)
    assert not result["success"]

def test_write_file(temp_dir):
    f = os.path.join(temp_dir, "written.txt")
    result = write_file.fn(f, "content")
    assert result["success"]
    assert os.path.exists(f)
    with open(f, 'r') as file:
        assert file.read() == "content"

@patch('src.mcp_tools.command_execution_tools.run_command_with_timeout')
def test_run_git_command(mock_run):
    mock_run.return_value = {
        "returncode": 0,
        "stdout": "On branch main",
        "stderr": "",
        "timed_out": False
    }
    
    result = run_git_command.fn("status")
    assert result["success"]
    assert "On branch main" in result["output"]
    
    # Forbidden command
    result = run_git_command.fn("rm file") # 'rm' not in allowed list
    assert not result["success"]
    assert "Git command not allowed" in result["error"]
