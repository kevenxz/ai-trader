# app/api/routers/scheduler_router.py

from fastapi import APIRouter, HTTPException
from fastapi.params import Query
from pydantic import BaseModel
from typing import Optional
import logging

from app.api.routers.ai_router import ChatTraderRequest
from app.scheduler.trading_scheduler import trading_scheduler
from exchanges.binance.futures import FuturesSymbol

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])
logger = logging.getLogger(__name__)

class ScheduleJobRequest(BaseModel):
    job_id: str
    chatTraderRequest: ChatTraderRequest
    symbol: str
    interval: int = 20 # 间隔次数
    type: str = Query(
        "m", # 分钟 小时
        description="定时任务执行周期 分钟 小时",
        example="m,h"
    ),

class UpdateIntervalRequest(BaseModel):
    hours: int

@router.post("/jobs")
async def schedule_job(request: ScheduleJobRequest):
    """Schedule a new trading job"""
    try:
        job_id = trading_scheduler.add_trading_job(
            job_id=request.job_id,
            chatTraderRequest=request.chatTraderRequest,
            interval=request.interval,
            type=request.type
        )
        return {"message": f"Job {job_id} scheduled successfully", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/jobs/{job_id}")
async def remove_job(job_id: str):
    """Remove a scheduled job"""
    try:
        trading_scheduler.remove_job(job_id)
        return {"message": f"Job {job_id} removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.put("/jobs/{job_id}/interval")
# async def update_job_interval(job_id: str, request: UpdateIntervalRequest):
#     """Update the interval of an existing job"""
#     try:
#         new_job_id = trading_scheduler.update_job_interval(job_id, request.hours)
#         return {"message": f"Job {new_job_id} interval updated successfully", "job_id": new_job_id}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/jobs")
# async def get_jobs_status():
#     """Get status of all scheduled jobs"""
#     try:
#         status = trading_scheduler.get_jobs_status()
#         return {"jobs": status}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_scheduler():
    """Start the scheduler"""
    try:
        await trading_scheduler.start()
        return {"message": "Scheduler started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_scheduler():
    """Stop the scheduler"""
    try:
        await trading_scheduler.stop()
        return {"message": "Scheduler stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
