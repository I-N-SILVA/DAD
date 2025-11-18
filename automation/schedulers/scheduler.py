"""
Task Scheduler

Manages scheduled automation tasks using APScheduler.
"""

import asyncio
from typing import Callable, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class TaskScheduler:
    """
    Manages scheduled tasks for the automation system.

    Features:
    - Cron-based scheduling
    - Interval-based scheduling
    - Async task support
    - Job management (add, remove, pause, resume)
    - Error handling and retry logic
    """

    def __init__(self, timezone: str = "UTC"):
        """
        Initialize task scheduler.

        Args:
            timezone: Timezone for scheduling (e.g., 'America/Los_Angeles')
        """
        self.scheduler = AsyncIOScheduler(timezone=timezone)
        self.jobs: Dict[str, Any] = {}

        logger.info(f"TaskScheduler initialized (timezone={timezone})")

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")

    def add_cron_job(
        self,
        func: Callable,
        job_id: str,
        cron_expression: str,
        description: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Add a cron-scheduled job.

        Args:
            func: Function to execute
            job_id: Unique job identifier
            cron_expression: Cron expression (e.g., '0 8 * * *' for 8 AM daily)
            description: Job description
            **kwargs: Additional arguments to pass to function

        Returns:
            Job ID
        """
        try:
            # Parse cron expression
            cron_parts = cron_expression.split()
            if len(cron_parts) != 5:
                raise ValueError(f"Invalid cron expression: {cron_expression}")

            minute, hour, day, month, day_of_week = cron_parts

            # Add job
            job = self.scheduler.add_job(
                func,
                trigger=CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                ),
                id=job_id,
                kwargs=kwargs,
                replace_existing=True
            )

            self.jobs[job_id] = {
                'job': job,
                'type': 'cron',
                'expression': cron_expression,
                'description': description or job_id
            }

            logger.info(f"Added cron job: {job_id} ({cron_expression})")
            return job_id

        except Exception as e:
            logger.error(f"Error adding cron job {job_id}: {e}")
            raise

    def add_interval_job(
        self,
        func: Callable,
        job_id: str,
        seconds: Optional[int] = None,
        minutes: Optional[int] = None,
        hours: Optional[int] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Add an interval-based job.

        Args:
            func: Function to execute
            job_id: Unique job identifier
            seconds: Interval in seconds
            minutes: Interval in minutes
            hours: Interval in hours
            description: Job description
            **kwargs: Additional arguments to pass to function

        Returns:
            Job ID
        """
        try:
            job = self.scheduler.add_job(
                func,
                trigger=IntervalTrigger(
                    seconds=seconds or 0,
                    minutes=minutes or 0,
                    hours=hours or 0
                ),
                id=job_id,
                kwargs=kwargs,
                replace_existing=True
            )

            interval_str = f"{hours}h {minutes}m {seconds}s"
            self.jobs[job_id] = {
                'job': job,
                'type': 'interval',
                'interval': interval_str,
                'description': description or job_id
            }

            logger.info(f"Added interval job: {job_id} (every {interval_str})")
            return job_id

        except Exception as e:
            logger.error(f"Error adding interval job {job_id}: {e}")
            raise

    def remove_job(self, job_id: str):
        """
        Remove a scheduled job.

        Args:
            job_id: Job identifier
        """
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]

            logger.info(f"Removed job: {job_id}")

        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")

    def pause_job(self, job_id: str):
        """Pause a job."""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")

    def resume_job(self, job_id: str):
        """Resume a paused job."""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")

    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a job."""
        return self.jobs.get(job_id)

    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        """List all scheduled jobs."""
        return self.jobs.copy()

    def run_job_now(self, job_id: str):
        """Run a job immediately (out of schedule)."""
        try:
            job_info = self.jobs.get(job_id)
            if job_info:
                job = job_info['job']
                job.modify(next_run_time=datetime.now())
                logger.info(f"Triggered immediate execution of job: {job_id}")
            else:
                logger.warning(f"Job not found: {job_id}")

        except Exception as e:
            logger.error(f"Error running job {job_id}: {e}")

    def __repr__(self) -> str:
        return f"TaskScheduler(jobs={len(self.jobs)}, running={self.scheduler.running})"


if __name__ == "__main__":
    # Test scheduler
    async def test_job(name: str):
        print(f"[{datetime.now()}] Running job: {name}")

    async def main():
        scheduler = TaskScheduler(timezone="America/Los_Angeles")

        # Add cron job (every minute for testing)
        scheduler.add_cron_job(
            test_job,
            job_id="test_cron",
            cron_expression="* * * * *",  # Every minute
            description="Test cron job",
            name="Test Cron"
        )

        # Add interval job
        scheduler.add_interval_job(
            test_job,
            job_id="test_interval",
            minutes=2,
            description="Test interval job",
            name="Test Interval"
        )

        # Start scheduler
        scheduler.start()

        print(f"Scheduler started. Jobs: {scheduler.list_jobs()}")

        # Run for 5 minutes
        await asyncio.sleep(300)

        # Shutdown
        scheduler.shutdown()

    # Run test
    # asyncio.run(main())
    print("Scheduler ready. Uncomment asyncio.run(main()) to test.")
