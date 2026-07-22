"""Windows Task Scheduler integration for AI-OS workflows.

Creates and manages Windows scheduled tasks using `schtasks`.
"""

import argparse
import os
import subprocess
import sys
from typing import Optional

from loguru import logger

TASK_NAME = "AI-OS_Workflow_Runner"
DEFAULT_SCRIPT_PATH = r"C:\Users\Himavanth Mallela\AI-OS\workflows\run_all.py"


def create_task(
    task_name: str = TASK_NAME,
    script_path: str = DEFAULT_SCRIPT_PATH,
    interval_hours: int = 2,
    python_exe: Optional[str] = None,
) -> bool:
    """Create a Windows Task Scheduler entry to run the AI-OS workflow periodically.

    Args:
        task_name: Name of the Windows scheduled task.
        script_path: Absolute path to the workflow python script.
        interval_hours: Repeat interval in hours (default 2).
        python_exe: Path to Python executable. Defaults to sys.executable.

    Returns:
        bool: True if task creation succeeded, False otherwise.
    """
    if python_exe is None:
        python_exe = sys.executable

    # Format action command to execute Python script
    task_run_cmd = f'"{python_exe}" "{script_path}"'

    # Build schtasks command line
    cmd = [
        "schtasks",
        "/create",
        "/tn", task_name,
        "/tr", task_run_cmd,
        "/sc", "HOURLY",
        "/mo", str(interval_hours),
        "/f",  # Force overwrite if task already exists
    ]

    logger.info(f"Creating Windows task '{task_name}' to run every {interval_hours} hours...")
    print(f"Executing command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            msg = f"[SUCCESS] Task '{task_name}' successfully created in Windows Task Scheduler."
            logger.info(msg)
            print(msg)
            if result.stdout:
                print(f"Details: {result.stdout.strip()}")
            return True
        else:
            msg = f"[FAILURE] Failed to create task '{task_name}'. Exit code: {result.returncode}"
            logger.error(msg)
            print(msg)
            if result.stderr:
                print(f"Error output:\n{result.stderr.strip()}")
            return False
    except Exception as exc:
        msg = f"[FAILURE] Exception encountered while creating task '{task_name}': {exc}"
        logger.exception(msg)
        print(msg)
        return False


def remove_task(task_name: str = TASK_NAME) -> bool:
    """Remove a Windows Task Scheduler entry for AI-OS workflows.

    Args:
        task_name: Name of the scheduled task to remove.

    Returns:
        bool: True if task removal succeeded, False otherwise.
    """
    cmd = [
        "schtasks",
        "/delete",
        "/tn", task_name,
        "/f",  # Force deletion without interactive prompt
    ]

    logger.info(f"Removing Windows task '{task_name}'...")
    print(f"Executing command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            msg = f"[SUCCESS] Task '{task_name}' successfully removed from Windows Task Scheduler."
            logger.info(msg)
            print(msg)
            if result.stdout:
                print(f"Details: {result.stdout.strip()}")
            return True
        else:
            msg = f"[FAILURE] Failed to remove task '{task_name}'. Exit code: {result.returncode}"
            logger.error(msg)
            print(msg)
            if result.stderr:
                print(f"Error output:\n{result.stderr.strip()}")
            return False
    except Exception as exc:
        msg = f"[FAILURE] Exception encountered while removing task '{task_name}': {exc}"
        logger.exception(msg)
        print(msg)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Manage Windows Task Scheduler entry for AI-OS main workflow."
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove the scheduled task instead of creating it.",
    )
    args = parser.parse_args()

    if args.remove:
        remove_task()
    else:
        create_task()
