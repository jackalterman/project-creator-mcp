import os
import platform

class SecurityConfig:
    """Security settings for file operations and command execution."""
    
    # Allowed file extensions for reading/writing
    ALLOWED_EXTENSIONS = {
        '.txt', '.md', '.json', '.js', '.ts', '.jsx', '.tsx',
        '.py', '.html', '.css', '.scss', '.sass', '.less',
        '.yml', '.yaml', '.xml', '.csv', '.env', '.gitignore',
        '.dockerfile', '.dockerignore', '.sql', '.sh', '.bat',
        '.ps1', '.toml', '.ini', '.cfg', '.conf', '.tcss', 'tfvars'
    }
    
    # Restricted directories
    # Use platform-agnostic paths where possible
    if platform.system() == 'Windows':
        RESTRICTED_PATHS = [
            os.path.expandvars('%SystemRoot%\\System32'),
            os.path.expandvars('%SystemRoot%\\SysWOW64'),
            os.path.expandvars('%ProgramFiles%'),
            os.path.expandvars('%ProgramFiles(x86)%'),
        ]
    else:
        RESTRICTED_PATHS = [
            '/System', '/usr/bin', '/usr/sbin', '/bin', '/sbin',
            '/etc/passwd', '/etc/shadow'
        ]
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Command timeout in seconds
    COMMAND_TIMEOUT = 60
