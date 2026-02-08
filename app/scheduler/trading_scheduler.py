# app/scheduler/trading_scheduler.py

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, TYPE_CHECKING
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job

from exchanges.binance.futures import FuturesSymbol

# 使用 TYPE_CHECKING 延迟导入，避免循环导入
if TYPE_CHECKING:
    from app.api.routers.ai_router import ChatTraderRequest

logger = logging.getLogger(__name__)


class TradingScheduler:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.scheduler = AsyncIOScheduler()
        self.session = None
        self.jobs = {}  # Store job references

    async def start(self):
        """Start the scheduler"""
        if self.session is None or  self.session.closed:
            self.session = aiohttp.ClientSession()

        if self.scheduler.running:
            self.scheduler.resume()
        else:
            self.scheduler.start()
        logger.info("Trading scheduler started")

    async def stop(self):
        """Stop the scheduler"""
        if self.session:
            await self.session.close()
            self.session = None
        if self.scheduler.running:
            self.scheduler.pause()
        logger.info("Trading scheduler stopped")

    def add_trading_job(self,
                        job_id: str,
                        chatTraderRequest: "ChatTraderRequest",
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
            "kline_interval": chatTraderRequest.interval,
            "schedule_type": type,
            "schedule_value": interval,
            "trader_config": {
                "service": chatTraderRequest.service,
                "model": chatTraderRequest.model,
                "klines_count": chatTraderRequest.klines_count,
                "temperature": chatTraderRequest.temperature,
                "enable_thinking": chatTraderRequest.enable_thinking,
                "is_trader": chatTraderRequest.is_Trader
            },
            "is_paused": False
        }

        logger.info(f"Added trading job: {job_id} with schedule '{cron_exp}'")
        return job_id

    def remove_job(self, job_id: str):
        """Remove a scheduled job"""
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            logger.info(f"Removed trading job: {job_id}")

    def pause_job(self, job_id: str):
        """Pause a specific job"""
        if job_id in self.jobs:
            self.scheduler.pause_job(job_id)
            self.jobs[job_id]["is_paused"] = True
            logger.info(f"Paused trading job: {job_id}")
            return True
        return False

    def resume_job(self, job_id: str):
        """Resume a paused job"""
        if job_id in self.jobs:
            self.scheduler.resume_job(job_id)
            self.jobs[job_id]["is_paused"] = False
            logger.info(f"Resumed trading job: {job_id}")
            return True
        return False

    async def run_job_now(self, job_id: str):
        """Run a job immediately without waiting for schedule"""
        if job_id not in self.jobs:
            return False
        
        job_data = self.jobs[job_id]
        logger.info(f"Manually triggering job: {job_id}")
        
        # 确保 session 已初始化
        session_created = False
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            session_created = True
        
        try:
            # 从存储的配置重建 ChatTraderRequest
            from app.api.routers.ai_router import ChatTraderRequest
            from exchanges.binance.futures import FuturesSymbol
            
            trader_config = job_data.get("trader_config", {})
            request = ChatTraderRequest(
                service=trader_config.get("service", "guiji"),
                model=trader_config.get("model"),
                symbol=FuturesSymbol(job_data["symbol"]),
                interval=job_data["kline_interval"],
                klines_count=trader_config.get("klines_count", 100),
                temperature=trader_config.get("temperature", 0.7),
                enable_thinking=trader_config.get("enable_thinking", False),
                is_Trader=trader_config.get("is_trader", True),
                messages=[]
            )
            
            # 异步执行交易分析
            await self._execute_trade_analysis(request, job_data["kline_interval"], job_id)
            logger.info(f"Manual execution completed for job: {job_id}")
            return True
        finally:
            # 如果是临时创建的 session，执行完后关闭
            if session_created and self.session and not self.session.closed:
                await self.session.close()
                self.session = None

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
        interval = job_details["kline_interval"]

        # Remove old job
        self.remove_job(job_id)

        # Add new job with updated interval
        return self.add_trading_job(job_id, symbol, interval, hours)

    def get_jobs_status(self):
        """Get status of all scheduled jobs"""
        status = {}
        for job_id, job_data in self.jobs.items():
            # Get fresh job from scheduler to access next_run_time
            next_run = None
            try:
                scheduler_job = self.scheduler.get_job(job_id)
                if scheduler_job and hasattr(scheduler_job, 'next_run_time') and scheduler_job.next_run_time:
                    next_run = scheduler_job.next_run_time.isoformat()
            except Exception as e:
                logger.warning(f"Failed to get next_run_time for job {job_id}: {e}")
            
            status[job_id] = {
                "symbol": job_data["symbol"],
                "kline_interval": job_data["kline_interval"],
                "schedule_type": job_data["schedule_type"],
                "schedule_value": job_data["schedule_value"],
                "next_run_time": next_run,
                "is_paused": job_data.get("is_paused", False),
                "trader_config": job_data.get("trader_config", {})
            }
        return status

        # kwargs={
        #       "chatTraderRequest": chatTraderRequest,
        #       "interval": interval,
        #       "job_id": job_id
        #   }

    async def _execute_trade_analysis(self, chatTraderRequest: "ChatTraderRequest", interval: str, job_id: str):
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
            payload = chatTraderRequest.model_dump()
            # Ensure symbol is serializable
            if hasattr(chatTraderRequest.symbol, 'value'):
                payload['symbol'] = chatTraderRequest.symbol.value
            else:
                payload['symbol'] = str(chatTraderRequest.symbol)

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
