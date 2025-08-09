import re
import subprocess
from typing import List, Union

# Patterns that should never appear in any command
DANGEROUS_PATTERNS = [
    re.compile(r';'),
    re.compile(r'&&'),
    re.compile(r'\|\|'),
    re.compile(r'\|'),
    re.compile(r'>'),
    re.compile(r'<'),
    re.compile(r'\brm\s+-rf\b'),
    re.compile(r'\bshutdown\b'),
    re.compile(r'\breboot\b'),
    re.compile(r'\bmkfs\b'),
    re.compile(r'\bdd\b'),
    re.compile(r'#.*'),  # comments can hide injection
]

class CommandExecutionError(Exception):
    """Raised when a command execution fails."""
    pass

def _is_command_safe(command: Union[str, List[str]]) -> bool:
    """Check if the command contains dangerous patterns."""
    cmd_str = ' '.join(command) if isinstance(command, list) else command
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(cmd_str):
            return False
    return True

def _execute_command(command: Union[str, List[str]]) -> dict:
    """Run a safe command and return its output."""
    if not _is_command_safe(command):
        raise CommandExecutionError(f"Blocked potentially dangerous command: {command}")

    try:
        result = subprocess.run(
            command if isinstance(command, list) else command.split(),
            capture_output=True,
            text=True,
            check=True
        )
        return {
            "success": True,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }
    except subprocess.CalledProcessError as e:
        raise CommandExecutionError(f"Command failed: {e.stderr.strip()}")

def get_command_executor():
    """
    Returns a callable that executes a given command safely.
    Usage:
        executor = get_command_executor()
        output = executor(["ls", "-la"])
    """
    return _execute_command
