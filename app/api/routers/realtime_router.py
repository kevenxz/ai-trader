from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.connection import execute_query, fetch_one, fetch_all, fetch_val

router = APIRouter(prefix="/api/realtime", tags=["Realtime"])

class RealtimeConfigResponse(BaseModel):
    id: int
    order_id: int
    is_enabled: bool
    tracking_interval: str
    created_at: datetime
    
class UpdateConfig(BaseModel):
    tracking_interval: str

@router.get("/orders/{order_id}", response_model=Optional[RealtimeConfigResponse])
async def get_realtime_config(order_id: int = Path(..., description="Order ID")):
    """Get real-time tracking config for an order"""
    try:
        query = "SELECT * FROM realtime_tracking_config WHERE order_id = $1"
        row = await fetch_one(query, order_id)
        if row:
            return RealtimeConfigResponse(**row)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/{order_id}/enable")
async def enable_realtime(order_id: int = Path(..., description="Order ID")):
    """Enable real-time tracking for an order"""
    try:
        # Check if exists
        check_query = "SELECT id FROM realtime_tracking_config WHERE order_id = $1"
        existing = await fetch_one(check_query, order_id)
        
        if existing:
            query = "UPDATE realtime_tracking_config SET is_enabled = true WHERE order_id = $1 RETURNING *"
            row = await fetch_one(query, order_id)
        else:
            query = """
                INSERT INTO realtime_tracking_config (order_id, is_enabled, tracking_interval)
                VALUES ($1, true, '1m') RETURNING *
            """
            row = await fetch_one(query, order_id)
            
        return RealtimeConfigResponse(**row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/{order_id}/disable")
async def disable_realtime(order_id: int = Path(..., description="Order ID")):
    """Disable real-time tracking for an order"""
    try:
        query = "UPDATE realtime_tracking_config SET is_enabled = false WHERE order_id = $1 RETURNING *"
        row = await fetch_one(query, order_id)
        if not row:
             raise HTTPException(status_code=404, detail="Configuration not found")
        return RealtimeConfigResponse(**row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/orders/{order_id}")
async def update_config(
    body: UpdateConfig,
    order_id: int = Path(..., description="Order ID")
):
    """Update tracking interval"""
    try:
        # Check if exists
        check_query = "SELECT id FROM realtime_tracking_config WHERE order_id = $1"
        existing = await fetch_one(check_query, order_id)
        
        if existing:
            query = "UPDATE realtime_tracking_config SET tracking_interval = $1 WHERE order_id = $2 RETURNING *"
            row = await fetch_one(query, body.tracking_interval, order_id)
        else:
            query = """
                INSERT INTO realtime_tracking_config (order_id, is_enabled, tracking_interval)
                VALUES ($1, true, $2) RETURNING *
            """
            row = await fetch_one(query, order_id, body.tracking_interval)
            
        return RealtimeConfigResponse(**row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
