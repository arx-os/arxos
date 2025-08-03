
# Example of Safe Command Execution

import subprocess
import shlex
from typing import List, Optional

def safe_execute_command(command: str, args: List[str] = None, timeout: int = 30):
    """
    Execute command safely with input validation.
    """
    # Validate command
    allowed_commands = [
        'git', 'docker', 'npm', 'python', 'python3',
        'pip', 'pip3', 'node', 'npm', 'yarn',
        'ls', 'cat', 'echo', 'mkdir', 'rm', 'cp', 'mv'
    ]
    
    if command not in allowed_commands:
        raise ValueError(f"Command '{command}' is not allowed")
    
    # Prepare command
    cmd = [command] + (args or [])
    
    # Execute safely
    result = subprocess.run(
        cmd,
        shell=False,  # Prevent shell injection
        capture_output=True,
        text=True,
        timeout=timeout
    )
    
    return result

# Usage examples
try:
    # Safe command execution
    result = safe_execute_command('git', ['status'])
    print(f"Git status: {result.stdout}")
    
    # Safe file listing
    result = safe_execute_command('ls', ['-la'])
    print(f"Directory contents: {result.stdout}")
    
except ValueError as e:
    print(f"Command not allowed: {e}")
except subprocess.TimeoutExpired:
    print("Command timed out")
except subprocess.CalledProcessError as e:
    print(f"Command failed: {e}")
