import pytest
import os
from src.mcp_tools.file_system_tools import create_file, read_file, create_directory, list_directory

def test_create_file(temp_dir):
    file_path = os.path.join(temp_dir, "test.txt")
    result = create_file.fn(file_path, "Hello World")
    assert result["success"]
    assert os.path.exists(file_path)
    with open(file_path, 'r') as f:
        assert f.read() == "Hello World"

def test_create_file_overwrite(temp_dir):
    file_path = os.path.join(temp_dir, "test.txt")
    create_file.fn(file_path, "Initial")
    
    # Fail without overwrite
    result = create_file.fn(file_path, "New")
    assert not result["success"]
    
    # Success with overwrite
    result = create_file.fn(file_path, "New", overwrite=True)
    assert result["success"]
    with open(file_path, 'r') as f:
        assert f.read() == "New"

def test_read_file(temp_dir):
    file_path = os.path.join(temp_dir, "read_test.txt")
    with open(file_path, 'w') as f:
        f.write("Content")
        
    result = read_file.fn(file_path)
    assert result["success"]
    assert result["content"] == "Content"

def test_create_directory(temp_dir):
    dir_path = os.path.join(temp_dir, "subdir")
    result = create_directory.fn(dir_path)
    assert result["success"]
    assert os.path.isdir(dir_path)

def test_list_directory(temp_dir):
    os.makedirs(os.path.join(temp_dir, "d1"))
    with open(os.path.join(temp_dir, "f1.txt"), 'w') as f:
        f.write("test")
        
    result = list_directory.fn(temp_dir)
    assert result["success"]
    assert result["directories"] == 1
    assert result["files"] == 1
