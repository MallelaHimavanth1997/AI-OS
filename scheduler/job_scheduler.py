"""Job Scheduler module for AI-OS.

Manages periodic background job execution using the `schedule` library,
restricting execution to configured workday hours.
"""

from datetime import datetime, time
import os
import time as time_module
from typing import Callable, Optional

from dotenv import load_dotenv
from loguru import logger
import schedule

# Load environment variables from .env if present
load_dotenv()


class JobScheduler:
    """Schedules and executes jobs during designated workday hours."""

    def __init__(
        self,
        workday_start: Optional[str] = None,
        workday_end: Optional[str] = None,
    ) -> None:
        """Initialize the JobScheduler.

        Args:
            workday_start: Start time string in HH:MM format. Defaults to WORKDAY_START env var or '07:00'.
            workday_end: End time string in HH:MM format. Defaults to WORKDAY_END env var or '21:00'.
        """
        self.workday_start_str = workday_start or os.getenv("WORKDAY_START", "07:00")
        self.workday_end_str = workday_end or os.getenv("WORKDAY_END", "21:00")
        self.running: bool = False
        logger.info(
            f"Initialized JobScheduler with workday hours: {self.workday_start_str} - {self.workday_end_str}"
        )

    def _parse_time(self, time_str: str) -> time:
        """Parse an HH:MM string into a datetime.time object.

        Args:
            time_str: Time formatted string (e.g., '07:00').

        Returns:
            time: Datetime time object.
        """
        try:
            parts = time_str.strip().split(":")
            return time(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError) as exc:
            logger.error(f"Failed to parse time string '{time_str}': {exc}")
            raise ValueError(f"Invalid time format '{time_str}'. Expected HH:MM format.") from exc

    def is_workday_hours(self) -> bool:
        """Check whether the current time falls within configured workday hours.

        Returns:
            bool: True if current time is within workday hours, False otherwise.
        """
        try:
            start_time = self._parse_time(self.workday_start_str)
            end_time = self._parse_time(self.workday_end_str)
            now = datetime.now().time()

            if start_time <= end_time:
                is_within = start_time <= now <= end_time
            else:
                # Overnight time range handling (e.g., 22:00 to 06:00)
                is_within = now >= start_time or now <= end_time

            logger.debug(
                f"is_workday_hours check: now={now.strftime('%H:%M:%S')}, "
                f"start={start_time}, end={end_time} -> {is_within}"
            )
            return is_within
        except Exception as err:
            logger.error(f"Error evaluating workday hours: {err}")
            return False

    def run_every_n_hours(self, n: int, job_function: Callable) -> schedule.Job:
        """Schedule a job function to run every `n` hours during workday hours.

        Args:
            n: Interval in hours between job runs.
            job_function: The callable job to execute.

        Returns:
            schedule.Job: The created schedule job instance.
        """

        def wrapped_job() -> None:
            job_name = getattr(job_function, "__name__", str(job_function))
            logger.info(f"Triggering scheduled evaluation for job '{job_name}'")
            if self.is_workday_hours():
                logger.info(f"Executing job '{job_name}' (within workday hours)")
                try:
                    job_function()
                    logger.info(f"Successfully completed job '{job_name}'")
                except Exception as exc:
                    logger.exception(f"Error executing job '{job_name}': {exc}")
            else:
                logger.info(
                    f"Skipped job '{job_name}' (outside workday hours: {self.workday_start_str}-{self.workday_end_str})"
                )

        job = schedule.every(n).hours.do(wrapped_job)
        job_name = getattr(job_function, "__name__", str(job_function))
        logger.info(f"Scheduled job '{job_name}' to run every {n} hour(s)")
        return job

    def start(self, poll_interval: int = 1) -> None:
        """Start running scheduled jobs in a loop.

        Args:
            poll_interval: Seconds between scheduler polling checks. Defaults to 1 second.
        """
        self.running = True
        logger.info("JobScheduler loop started.")
        try:
            while self.running:
                schedule.run_pending()
                time_module.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Stopping scheduler...")
        finally:
            self.running = False
            logger.info("JobScheduler loop stopped.")

    def stop(self) -> None:
        """Stop the scheduler execution loop."""
        logger.info("Stopping JobScheduler...")
        self.running = False

    def clear_jobs(self) -> None:
        """Clear all registered scheduled jobs."""
        schedule.clear()
        logger.info("Cleared all scheduled jobs.")
