"""
This module is used to run a command by `subprocess.run` with timeout and retry times.

Example:

```python
from Kkit import timeout
result = timeout.run_command_with_timeout(["sleep", "10"], timeout=1, retry_times=3)
#or
result = timeout.run_shell_with_timeout("sleep 10", timeout=1, retry_times=3)
```
"""

import subprocess


def run_command_with_timeout(command: list, timeout=1, retry_times=3, **kwargs):
    """
    Run a command with timeout and retry times

    Parameters
    ----------
    command : list
        The command to run
    timeout : int
        The timeout for the command
    retry_times : int
        The retry times for the command
    **kwargs
        Other parameters for subprocess.run

    Returns
    -------
    subprocess.CompletedProcess or None
        The result of the command
    """
    for i in range(retry_times):
        try:
            result = subprocess.run(command, timeout=timeout, **kwargs)
            return result
        except subprocess.TimeoutExpired:
            print(f"command <{' '.join(command)}> timeouts {i+1} times")
            continue
    return None

def run_shell_with_timeout(shell: str, timeout=1, retry_times=3, **kwargs):
    """
    Run a shell command with timeout and retry times

    Parameters
    ----------
    shell : str
        The shell command to run
    timeout : int
        The timeout for the command
    retry_times : int
        The retry times for the command
    **kwargs
        Other parameters for subprocess.run

    Returns
    -------
    subprocess.CompletedProcess or None
        The result of the command
    """
    for i in range(retry_times):
        try:
            result = subprocess.run(shell, shell=True, timeout=timeout, **kwargs)
            return result
        except subprocess.TimeoutExpired:
            print(f"command <{shell}> timeouts {i+1} times")
            continue
    return None

