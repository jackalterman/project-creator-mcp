
import os

from src.config import SecurityConfig

def is_safe_path(path: str) -> tuple[bool, str]:
    """Validate if a path is safe to access."""
    try:
        abs_path = os.path.abspath(path)
        for restricted in SecurityConfig.RESTRICTED_PATHS:
            if abs_path.startswith(restricted):
                return False, f"Access to restricted path: {restricted}"
        return True, "Path is safe"
    except Exception as e:
        return False, f"Invalid path: {str(e)}"

def is_safe_filename(filename: str) -> tuple[bool, str]:
    """Validate if a filename is safe."""
    if not filename or filename.startswith('.'):
        return False, "Invalid filename"
    
    # Check for dangerous characters
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in filename for char in dangerous_chars):
        return False, "Filename contains dangerous characters"
    
    return True, "Filename is safe"

def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return os.path.splitext(filename)[1].lower()
