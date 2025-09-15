
import os

class SecurityConfig:
    """Security settings for file operations and command execution."""
    
    # Allowed file extensions for reading/writing
    ALLOWED_EXTENSIONS = {
        '.txt', '.md', '.json', '.js', '.ts', '.jsx', '.tsx',
        '.py', '.html', '.css', '.scss', '.sass', '.less',
        '.yml', '.yaml', '.xml', '.csv', '.env', '.gitignore',
        '.dockerfile', '.dockerignore', '.sql', '.sh', '.bat',
        '.ps1', '.toml', '.ini', '.cfg', '.conf'
    }
    
    # Restricted directories
    RESTRICTED_PATHS = [
        'C:\\Windows\\System32',
        'C:\\Windows\\SysWOW64',
        'C:\\Program Files',
        'C:\\Program Files (x86)', 
        '/System', '/usr/bin', '/usr/sbin', '/bin', '/sbin',
        '/etc/passwd', '/etc/shadow'
    ]
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Command timeout in seconds
    COMMAND_TIMEOUT = 60

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
