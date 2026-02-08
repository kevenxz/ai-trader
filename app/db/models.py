# app/db/models.py
"""Pydantic models for AI Trading Orders"""

from datetime import datetime
from typing import Optional, List, Literal
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enum"""
    OPEN = "OPEN"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT_T1 = "TAKE_PROFIT_T1"
    TAKE_PROFIT_T2 = "TAKE_PROFIT_T2"
    TAKE_PROFIT_T3 = "TAKE_PROFIT_T3"
    CLOSED = "CLOSED"


class TrackingInterval(str, Enum):
    """Tracking interval enum"""
    THIRTY_MIN = "30m"
    ONE_HOUR = "1h"
    TWO_HOUR = "2h"
    FOUR_HOUR = "4h"
    SIX_HOUR = "6h"


class Recommendation(str, Enum):
    """Trading recommendation enum"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class RiskLevel(str, Enum):
    """Risk level enum"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AITradingOrder(BaseModel):
    """AI Trading Order model"""
    id: Optional[int] = None
    symbol: str
    interval: str
    ai_model: Optional[str] = None
    recommendation: Literal["BUY", "SELL", "HOLD"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    trend_status: Optional[str] = None
    momentum: Optional[str] = None
    entry_price_min: Optional[float] = None
    entry_price_max: Optional[float] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    stop_loss_percentage: Optional[float] = None
    target_t1: Optional[float] = None
    target_t2: Optional[float] = None
    target_t3: Optional[float] = None
    position_size_percentage: Optional[float] = None
    leverage: Optional[float] = 1.0
    quantity: Optional[float] = None
    open_amount: Optional[float] = None
    status: OrderStatus = OrderStatus.OPEN
    analysis_summary: Optional[str] = None
    indicator_alerts: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    closed_price: Optional[float] = None
    final_profit_percentage: Optional[float] = None
    pnl_ratio: Optional[float] = None
    is_win: Optional[bool] = None
    raw_analysis: Optional[dict] = None

    class Config:
        from_attributes = True

    @field_validator('recommendation', 'risk_level', mode='before')
    def case_insensitive(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class OrderProfitTracking(BaseModel):
    """Order Profit Tracking model"""
    id: Optional[int] = None
    order_id: int
    current_price: float
    profit_percentage: float
    profit_amount: Optional[float] = None
    floating_pnl: Optional[float] = None
    interval_pnl_ratio: Optional[float] = None
    tracking_interval: str
    is_stop_loss_triggered: bool = False
    is_take_profit_triggered: bool = False
    triggered_target: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tracked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """Order creation request model"""
    symbol: str
    interval: str
    ai_model: Optional[str] = None
    recommendation: Literal["BUY", "SELL", "HOLD"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    trend_status: Optional[str] = None
    momentum: Optional[str] = None
    entry_price_min: Optional[float] = None
    entry_price_max: Optional[float] = None
    entry_price: float
    stop_loss: Optional[float] = None
    stop_loss_percentage: Optional[float] = None
    target_t1: Optional[float] = None
    target_t2: Optional[float] = None
    target_t3: Optional[float] = None
    position_size_percentage: Optional[float] = None
    analysis_summary: Optional[str] = None
    indicator_alerts: Optional[str] = None
    raw_analysis: Optional[dict] = None


class OrderCreateManual(BaseModel):
    """Manual order creation request model"""
    symbol: str
    interval: str = "4h"
    recommendation: Literal["BUY", "SELL"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    entry_price: float
    stop_loss: float
    target_t1: Optional[float] = None
    target_t2: Optional[float] = None
    target_t3: Optional[float] = None
    leverage: float = 1.0
    quantity: Optional[float] = None
    open_amount: Optional[float] = None
    position_size_percentage: Optional[float] = 5.0
    analysis_summary: Optional[str] = None


class OrderStatistics(BaseModel):
    """Order statistics model"""
    symbol: str
    total_orders: int
    open_orders: int
    stop_loss_orders: int
    take_profit_orders: int
    avg_profit: Optional[float] = None
    win_rate: Optional[float] = None


class ProfitSummary(BaseModel):
    """Profit summary for an order"""
    order_id: int
    symbol: str
    entry_price: float
    current_price: float
    profit_percentage: float
    status: str
    tracking_history: List[OrderProfitTracking] = []


class PriceExtremes(BaseModel):
    """Price extremes within a time period"""
    period: str
    low_price: Optional[float] = None
    low_price_time: Optional[datetime] = None
    high_price: Optional[float] = None
    high_price_time: Optional[datetime] = None


class ScheduledJob(BaseModel):
    """Scheduled trading job model"""
    job_id: str
    symbol: str
    interval: str 
    schedule_type: str 
    schedule_value: int 
    is_active: bool = True
    created_at: Optional[datetime] = None


class TakeProfitStats(BaseModel):
    """Take profit statistics breakdown"""
    t1_count: int = 0
    t1_total_profit: float = 0.0
    t2_count: int = 0
    t2_total_profit: float = 0.0
    t3_count: int = 0
    t3_total_profit: float = 0.0


class ProfitPeriodStats(BaseModel):
    """Statistics for a specific time period"""
    period: str  # today/week/month/all
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_orders: int = 0
    closed_orders: int = 0
    open_orders: int = 0
    win_count: int = 0  # 盈利订单数
    loss_count: int = 0  # 亏损订单数
    total_profit_percentage: float = 0.0
    avg_profit_percentage: float = 0.0
    win_rate: Optional[float] = None
    take_profit_stats: Optional[TakeProfitStats] = None
    stop_loss_stats: Optional[dict] = None
    price_extremes: Optional[PriceExtremes] = None


class ProfitAnalyticsResponse(BaseModel):
    """Complete profit analytics response"""
    period: str
    symbol: Optional[str] = None
    stats: ProfitPeriodStats
    orders_summary: List[dict] = []
