import pytest
from unittest.mock import patch, MagicMock
from src.mcp_tools.command_execution_tools import run_command, run_python_command

@patch('src.mcp_tools.command_execution_tools.run_command_with_timeout')
def test_run_command_success(mock_run):
    mock_run.return_value = {
        "returncode": 0,
        "stdout": "success",
        "stderr": "",
        "timed_out": False
    }
    
    result = run_command.fn("echo test")
    assert result["success"]
    assert result["output"] == "success"

@patch('src.mcp_tools.command_execution_tools.run_command_with_timeout')
def test_run_command_fail(mock_run):
    mock_run.return_value = {
        "returncode": 1,
        "stdout": "",
        "stderr": "error",
        "timed_out": False
    }
    
    result = run_command.fn("ls nonexist")
    assert not result["success"]
    assert result["error"] == "error"

def test_run_command_blocked():
    result = run_command.fn("rm -rf /")
    assert not result["success"]
    assert "Command not allowed" in result["error"]

@patch('src.mcp_tools.command_execution_tools.run_command_with_timeout')
def test_run_python_command(mock_run):
    mock_run.return_value = {
        "returncode": 0,
        "stdout": "Python 3.8",
        "stderr": "",
        "timed_out": False
    }
    
    result = run_python_command.fn("python --version")
    assert result["success"]
