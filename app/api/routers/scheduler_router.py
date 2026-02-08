from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.scheduler.trading_scheduler import trading_scheduler
from app.db.models import ScheduledJob
from app.api.routers.ai_router import ChatTraderRequest
from enum import Enum
from exchanges.binance.futures import FuturesSymbol

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scheduler", tags=["Scheduler"])

class JobCreate(BaseModel):
    symbol: str
    interval: str = "15m"
    schedule_type: str = "m"  # "m" for minutes, "h" for hours
    schedule_value: int = 15
    # Trader configuration parameters
    service: str = "guiji"  # AI服务: guiji, qiniu, deepseek
    model: Optional[str] = None  # AI模型，不同平台有不同选项
    klines_count: int = 100  # K线数量
    temperature: float = 0.7  # AI温度参数
    enable_thinking: bool = False  # 是否启用思考模式
    is_trader: bool = True  # 是否启用交易分析模式

class JobResponse(BaseModel):
    job_id: str
    symbol: str
    interval: str
    schedule_type: str
    schedule_value: int
    next_run_time: Optional[str] = None
    status: str = "active"
    # Trader configuration in response
    service: Optional[str] = None
    model: Optional[str] = None
    klines_count: Optional[int] = None
    temperature: Optional[float] = None
    enable_thinking: Optional[bool] = None
    is_trader: Optional[bool] = None

@router.get("/jobs", response_model=List[JobResponse])
async def get_jobs():
    """Get all scheduled jobs"""
    try:
        logger.info("[scheduler] 获取定时任务列表")
        jobs_status = trading_scheduler.get_jobs_status()
        response = []
        for job_id, details in jobs_status.items():
            trader_config = details.get("trader_config", {})
            response.append(JobResponse(
                job_id=job_id,
                symbol=details.get("symbol", ""),
                interval=str(details.get("kline_interval", "15m")),
                schedule_type=details.get("schedule_type", "m"),
                schedule_value=int(details.get("schedule_value", 15)),
                next_run_time=details.get("next_run_time"),
                status="paused" if details.get("is_paused") else "active",
                service=trader_config.get("service"),
                model=trader_config.get("model"),
                klines_count=trader_config.get("klines_count"),
                temperature=trader_config.get("temperature"),
                enable_thinking=trader_config.get("enable_thinking"),
                is_trader=trader_config.get("is_trader")
            ))
        logger.info(f"[scheduler] 返回 {len(response)} 个定时任务")
        return response
    except Exception as e:
        logger.error(f"[scheduler] 获取任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs", response_model=JobResponse)
async def add_job(job: JobCreate):
    """Add a new scheduled job with trader configuration"""
    try:
        logger.info(f"[scheduler] 添加定时任务: symbol={job.symbol}, interval={job.interval}, schedule={job.schedule_value}{job.schedule_type}")
        
        # Validate symbol
        try:
            symbol_enum = FuturesSymbol(job.symbol)
        except ValueError:
            logger.warning(f"[scheduler] 无效的交易对: {job.symbol}")
            raise HTTPException(status_code=400, detail=f"Invalid symbol: {job.symbol}")

        job_id = f"trade_{job.symbol.lower()}_{job.interval}"
        
        # Create request model with trader configuration
        request = ChatTraderRequest(
            service=job.service,
            model=job.model,
            symbol=symbol_enum,
            interval=job.interval,
            klines_count=job.klines_count,
            temperature=job.temperature,
            enable_thinking=job.enable_thinking,
            is_Trader=job.is_trader,
            messages=[]  # Empty messages, will be populated with k-line data
        )
        
        trading_scheduler.add_trading_job(
            job_id=job_id,
            chatTraderRequest=request,
            interval=job.schedule_value,
            type=job.schedule_type
        )
        
        logger.info(f"[scheduler] 定时任务添加成功: {job_id}")
        return JobResponse(
            job_id=job_id,
            symbol=job.symbol,
            interval=job.interval,
            schedule_type=job.schedule_type,
            schedule_value=job.schedule_value,
            next_run_time=None,
            status="active",
            service=job.service,
            model=job.model,
            klines_count=job.klines_count,
            temperature=job.temperature,
            enable_thinking=job.enable_thinking,
            is_trader=job.is_trader
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[scheduler] 添加任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/jobs/{job_id}")
async def remove_job(job_id: str):
    """Remove a scheduled job"""
    try:
        logger.info(f"[scheduler] 删除定时任务: {job_id}")
        trading_scheduler.remove_job(job_id)
        return {"message": f"Job {job_id} removed"}
    except Exception as e:
        logger.error(f"[scheduler] 删除任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a specific scheduled job"""
    try:
        logger.info(f"[scheduler] 暂停定时任务: {job_id}")
        success = trading_scheduler.pause_job(job_id)
        if success:
            return {"message": f"Job {job_id} paused", "status": "paused"}
        else:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[scheduler] 暂停任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """Resume a paused scheduled job"""
    try:
        logger.info(f"[scheduler] 恢复定时任务: {job_id}")
        success = trading_scheduler.resume_job(job_id)
        if success:
            return {"message": f"Job {job_id} resumed", "status": "active"}
        else:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[scheduler] 恢复任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/run")
async def run_job_now(job_id: str):
    """Run a scheduled job immediately without waiting for schedule"""
    try:
        logger.info(f"[scheduler] 立即执行定时任务: {job_id}")
        success = await trading_scheduler.run_job_now(job_id)
        if success:
            return {"message": f"Job {job_id} executed successfully", "status": "executed"}
        else:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[scheduler] 立即执行任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_scheduler():
    """Start the scheduler"""
    try:
        logger.info("[scheduler] 启动调度器")
        await trading_scheduler.start()
        return {"message": "Scheduler started"}
    except Exception as e:
        logger.error(f"[scheduler] 启动调度器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_scheduler():
    """Stop the scheduler"""
    try:
        logger.info("[scheduler] 停止调度器")
        await trading_scheduler.stop()
        return {"message": "Scheduler stopped"}
    except Exception as e:
        logger.error(f"[scheduler] 停止调度器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_scheduler_status():
    """Get scheduler status"""
    try:
        running = trading_scheduler.scheduler.running
        jobs_count = len(trading_scheduler.jobs)
        logger.debug(f"[scheduler] 状态查询: running={running}, jobs={jobs_count}")
        return {"running": running, "jobs_count": jobs_count}
    except Exception as e:
        logger.error(f"[scheduler] 获取状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
