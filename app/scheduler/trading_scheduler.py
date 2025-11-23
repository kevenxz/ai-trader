# app/scheduler/trading_scheduler.py

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job

from app.api.routers.ai_router import ChatTraderRequest
from exchanges.binance.futures import FuturesSymbol

logger = logging.getLogger(__name__)


class TradingScheduler:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.scheduler = AsyncIOScheduler()
        self.session = None
        self.jobs = {}  # Store job references

    async def start(self):
        """Start the scheduler"""
        self.session = aiohttp.ClientSession()
        self.scheduler.start()
        logger.info("Trading scheduler started")

    async def stop(self):
        """Stop the scheduler"""
        if self.session:
            await self.session.close()
        self.scheduler.shutdown()
        logger.info("Trading scheduler stopped")

    def add_trading_job(self,
                        job_id: str,
                        chatTraderRequest: ChatTraderRequest,
                        interval: int = 20,
                        type: str = "m"):
        """
        Add a scheduled job to call the trader API at specified hourly intervals

        Args:
            job_id: Unique identifier for the job
            symbol: Trading pair
            interval: Kline interval
            hours: Hourly interval (e.g., 1 for every hour, 2 for every 2 hours)
        """
        # Remove existing job if it exists
        if job_id in self.jobs:
            self.remove_job(job_id)
        if type == "m":
            # Minutes level - use standard 5-field cron: minute hour day month weekday
            cron_exp = f"*/{interval} * * * *"  # Every 'interval' minutes
        elif type == "h":
            cron_exp = f"0 */{interval} * * *"  # Every 'interval' hours at minute 0
        else:
            # Default fallback
            cron_exp = f"*/{interval} * * * *"

        job = self.scheduler.add_job(
            self._execute_trade_analysis,
            trigger=CronTrigger.from_crontab(cron_exp),
            id=job_id,
            name=f"Trading analysis for {chatTraderRequest.symbol.value}",
            kwargs={
                "chatTraderRequest": chatTraderRequest,
                "interval": interval,
                "job_id": job_id
            }
        )

        self.jobs[job_id] = {
            "job": job,
            "symbol": chatTraderRequest.symbol.value,
            "interval": interval,
            "type": type
        }

        logger.info(f"Added trading job: {job_id} with schedule '{cron_exp}'")
        return job_id

    def remove_job(self, job_id: str):
        """Remove a scheduled job"""
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            logger.info(f"Removed trading job: {job_id}")

    def update_job_interval(self, job_id: str, hours: int):
        """
        Update the interval of an existing job

        Args:
            job_id: ID of the job to update
            hours: New hourly interval
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        # Get current job details
        job_details = self.jobs[job_id]
        symbol = job_details["symbol"]
        interval = job_details["interval"]

        # Remove old job
        self.remove_job(job_id)

        # Add new job with updated interval
        return self.add_trading_job(job_id, symbol, interval, hours)

    def get_jobs_status(self):
        """Get status of all scheduled jobs"""
        status = {}
        for job_id, job_data in self.jobs.items():
            job: Job = job_data["job"]
            status[job_id] = {
                "symbol": job_data["symbol"].value,
                "interval": job_data["interval"],
                "hours": job_data["hours"],
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
            }
        return status

        # kwargs={
        #       "chatTraderRequest": chatTraderRequest,
        #       "interval": interval,
        #       "job_id": job_id
        #   }

    async def _execute_trade_analysis(self, chatTraderRequest: ChatTraderRequest, interval: str, job_id: str):
        """
        Execute trade analysis by calling the trader API

        Args:
            symbol: Trading pair
            interval: Kline interval
            job_id: ID of the job that triggered this execution
        """
        if not self.session:
            logger.error("Scheduler session not initialized")
            return

        try:
            logger.info(f"Executing trade analysis for {chatTraderRequest.symbol.value} , 间隔：{interval} , job_id : {job_id}")
            # Prepare request payload
            payload = chatTraderRequest

            # Call the trader API
            async with self.session.post(
                    f"{self.base_url}/api/ai/chat/trader",
                    json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Trade analysis completed for {chatTraderRequest.symbol.value}: {result}")
                else:
                    error_text = await response.text()
                    logger.error(f"API call failed with status {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"Error executing trade analysis for {chatTraderRequest.symbol.value}: {str(e)}")


# Initialize scheduler instance
trading_scheduler = TradingScheduler()
