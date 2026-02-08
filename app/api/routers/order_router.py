# app/api/routers/order_router.py
"""API Router for AI Trading Orders"""

from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Path
from pydantic import BaseModel

from app.db.models import (
    AITradingOrder, 
    OrderProfitTracking, 
    OrderStatistics,
    ProfitSummary,
    ProfitAnalyticsResponse,
    Recommendation,
    RiskLevel,
    OrderStatus,
    OrderCreateManual
)

router = APIRouter(prefix="/api/orders", tags=["Trading Orders"])


class OrderListResponse(BaseModel):
    """Order list response"""
    orders: List[AITradingOrder]
    total: int
    page: int
    page_size: int


class ProfitTrackingResponse(BaseModel):
    """Profit tracking response"""
    order_id: int
    history: List[OrderProfitTracking]
    summary: dict


class SymbolStats(BaseModel):
    """Per-symbol statistics"""
    symbol: str
    total_orders: int
    open_orders: int
    closed_orders: int
    win_count: int
    loss_count: int
    total_profit: float
    win_rate: Optional[float] = None


class DashboardResponse(BaseModel):
    """Dashboard overview response"""
    total_profit_percentage: float
    total_orders: int
    open_orders: int
    closed_orders: int
    win_count: int
    loss_count: int
    win_rate: Optional[float] = None
    symbol_stats: List[SymbolStats]


@router.post("", response_model=AITradingOrder)
async def create_order(order_data: OrderCreateManual):
    """
    手动创建订单
    
    允许用户通过页面创建新订单，填写基础参数
    """
    try:
        from app.services.order_service import order_service
        from app.db.models import OrderCreate
        
        # 计算止损百分比
        stop_loss_percentage = None
        if order_data.entry_price and order_data.stop_loss:
            if order_data.recommendation == "BUY":
                stop_loss_percentage = ((order_data.entry_price - order_data.stop_loss) / order_data.entry_price) * 100
            else:
                stop_loss_percentage = ((order_data.stop_loss - order_data.entry_price) / order_data.entry_price) * 100
        
        order = OrderCreate(
            symbol=order_data.symbol,
            interval=order_data.interval,
            recommendation=order_data.recommendation,
            risk_level=order_data.risk_level,
            entry_price=order_data.entry_price,
            entry_price_min=order_data.entry_price * 0.99,
            entry_price_max=order_data.entry_price * 1.01,
            stop_loss=order_data.stop_loss,
            stop_loss_percentage=stop_loss_percentage,
            target_t1=order_data.target_t1,
            target_t2=order_data.target_t2,
            target_t3=order_data.target_t3,
            position_size_percentage=order_data.position_size_percentage,
            analysis_summary=order_data.analysis_summary or "手动创建订单"
        )
        
        order_id = await order_service.create_order(order)
        
        # 更新杠杆、数量、金额
        if order_data.leverage or order_data.quantity or order_data.open_amount:
            from app.db.connection import execute_query
            await execute_query(
                """UPDATE ai_trading_orders 
                   SET leverage = $1, quantity = $2, open_amount = $3 
                   WHERE id = $4""",
                order_data.leverage, order_data.quantity, order_data.open_amount, order_id
            )
        
        created_order = await order_service.get_order(order_id)
        return created_order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=OrderListResponse)
async def get_orders(
    symbol: Optional[str] = Query(None, description="筛选交易对"),
    status: Optional[str] = Query(None, description="筛选订单状态 (OPEN/STOP_LOSS/TAKE_PROFIT_T1/TAKE_PROFIT_T2/TAKE_PROFIT_T3/CLOSED)"),
    recommendation: Optional[str] = Query(None, description="筛选推荐方向 (BUY/SELL/HOLD)"),
    risk_level: Optional[str] = Query(None, description="筛选风险等级 (LOW/MEDIUM/HIGH)"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取订单列表
    
    支持按交易对、状态、推荐方向、风险等级、日期范围筛选，分页返回
    """
    try:
        from app.services.order_service import order_service
        from datetime import datetime
        
        # Parse dates
        parsed_start = None
        parsed_end = None
        if start_date:
            parsed_start = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            parsed_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        
        offset = (page - 1) * page_size
        orders = await order_service.get_orders(
            symbol=symbol,
            status=status,
            recommendation=recommendation,
            risk_level=risk_level,
            start_date=parsed_start,
            end_date=parsed_end,
            limit=page_size,
            offset=offset
        )
        
        # 获取总数
        from app.db.connection import fetch_val
        count_query = "SELECT COUNT(*) FROM ai_trading_orders"
        conditions = []
        params = []
        param_idx = 1
        
        if symbol and symbol.strip():
            conditions.append(f"symbol = ${param_idx}")
            params.append(symbol.strip())
            param_idx += 1
        if status and status.strip():
            conditions.append(f"status = ${param_idx}")
            params.append(status.strip())
            param_idx += 1
        if recommendation and recommendation.strip():
            conditions.append(f"recommendation = ${param_idx}")
            params.append(recommendation.strip().upper())
            param_idx += 1
        if risk_level and risk_level.strip():
            conditions.append(f"risk_level = ${param_idx}")
            params.append(risk_level.strip().upper())
            param_idx += 1
        if parsed_start:
            conditions.append(f"created_at >= ${param_idx}")
            params.append(parsed_start)
            param_idx += 1
        if parsed_end:
            conditions.append(f"created_at <= ${param_idx}")
            params.append(parsed_end)
            param_idx += 1
        
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)
        
        total = await fetch_val(count_query, *params) or 0
        
        return OrderListResponse(
            orders=orders,
            total=total,
            page=page,
            page_size=page_size
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# 静态路由 (必须在 /{order_id} 动态路由之前定义)
# =============================================

@router.get("/dashboard")
async def get_dashboard():
    """
    Get dashboard overview data
    
    Returns total stats and per-symbol breakdown
    """
    try:
        from app.services.order_service import order_service
        result = await order_service.get_dashboard_stats()
        return result
    except Exception as e:
        import traceback
        print(f"[ERROR] Dashboard error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/daily-profit")
async def get_daily_profit(
    days: int = Query(30, description="天数，默认30天")
):
    """获取每日盈亏数据"""
    try:
        from app.db.connection import fetch_all
        
        query = f"""
            SELECT 
                DATE(closed_at) as date,
                COALESCE(SUM(final_profit_percentage), 0) as total_profit,
                COUNT(*) as order_count,
                COALESCE(SUM(CASE WHEN is_win = true THEN 1 ELSE 0 END), 0) as win_count
            FROM ai_trading_orders 
            WHERE closed_at IS NOT NULL 
            AND closed_at >= CURRENT_DATE - INTERVAL '{days} days'
            GROUP BY DATE(closed_at)
            ORDER BY date DESC
        """
        
        rows = await fetch_all(query)
        return [{
            "date": str(row["date"]) if row["date"] else "",
            "total_profit": float(row["total_profit"] or 0),
            "order_count": row["order_count"] or 0,
            "win_count": row["win_count"] or 0
        } for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/profit-curve")
async def get_profit_curve(
    days: int = Query(90, description="天数，默认90天"),
    symbol: Optional[str] = Query(None, description="筛选币种，为空则返回总收益曲线")
):
    """
    获取收益曲线数据
    
    - 返回累计收益百分比曲线和收益金额
    - 支持按币种筛选
    - 收益金额 = 开仓金额 × 杠杆 × 收益百分比 / 100
    - 用于绘制收益曲线图表
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from app.db.connection import fetch_all
        
        logger.info(f"[profit-curve] 请求参数: days={days}, symbol={symbol}")
        
        # 构建查询条件
        where_conditions = ["closed_at IS NOT NULL", f"closed_at >= CURRENT_DATE - INTERVAL '{days} days'"]
        
        if symbol and symbol.strip():
            where_conditions.append(f"symbol = '{symbol.strip()}'")
        
        where_clause = " AND ".join(where_conditions)
        
        # 查询每日盈亏数据 - 合约交易收益金额 = 开仓金额 × 收益百分比 / 100 (不需要乘杠杆)
        query = f"""
            SELECT 
                DATE(closed_at) as date,
                symbol,
                COALESCE(SUM(final_profit_percentage), 0) as daily_profit,
                COUNT(*) as order_count,
                COALESCE(SUM(CASE WHEN is_win = true THEN 1 ELSE 0 END), 0) as win_count,
                COALESCE(SUM(
                    CASE 
                        WHEN open_amount > 0 THEN
                            open_amount * (final_profit_percentage / 100.0)
                        WHEN entry_price > 0 AND quantity > 0 THEN
                            entry_price * quantity * (final_profit_percentage / 100.0)
                        ELSE 0
                    END
                ), 0) as daily_profit_amount,
                COALESCE(SUM(
                    CASE 
                        WHEN open_amount > 0 THEN open_amount
                        WHEN entry_price > 0 AND quantity > 0 THEN entry_price * quantity
                        ELSE 0
                    END
                ), 0) as total_position_value
            FROM ai_trading_orders 
            WHERE {where_clause}
            GROUP BY DATE(closed_at), symbol
            ORDER BY date ASC
        """
        
        logger.debug(f"[profit-curve] 执行查询: {query[:200]}...")
        rows = await fetch_all(query)
        logger.info(f"[profit-curve] 查询返回 {len(rows)} 条记录")
        
        # 按日期聚合计算累计收益
        date_profits = {}
        for row in rows:
            date_str = str(row["date"]) if row["date"] else ""
            if date_str not in date_profits:
                date_profits[date_str] = {
                    "date": date_str,
                    "daily_profit": 0,
                    "daily_profit_amount": 0,
                    "cumulative_profit": 0,
                    "cumulative_profit_amount": 0,
                    "order_count": 0,
                    "win_count": 0,
                    "position_value": 0
                }
            date_profits[date_str]["daily_profit"] += float(row["daily_profit"] or 0)
            date_profits[date_str]["daily_profit_amount"] += float(row["daily_profit_amount"] or 0)
            date_profits[date_str]["order_count"] += row["order_count"] or 0
            date_profits[date_str]["win_count"] += row["win_count"] or 0
            date_profits[date_str]["position_value"] += float(row["total_position_value"] or 0)
        
        # 计算累计收益
        sorted_dates = sorted(date_profits.keys())
        cumulative_profit = 0
        cumulative_amount = 0
        result = []
        for date_str in sorted_dates:
            data = date_profits[date_str]
            cumulative_profit += data["daily_profit"]
            cumulative_amount += data["daily_profit_amount"]
            result.append({
                "date": date_str,
                "daily_profit": round(data["daily_profit"], 4),
                "daily_profit_amount": round(data["daily_profit_amount"], 2),
                "cumulative_profit": round(cumulative_profit, 4),
                "cumulative_profit_amount": round(cumulative_amount, 2),
                "order_count": data["order_count"],
                "win_count": data["win_count"],
                "position_value": round(data["position_value"], 2)
            })
        
        logger.info(f"[profit-curve] 返回 {len(result)} 个数据点, 累计收益: {cumulative_profit:.4f}%, 金额: ${cumulative_amount:.2f}")
        
        return {
            "symbol": symbol or "ALL",
            "days": days,
            "data_points": len(result),
            "total_profit_percentage": round(cumulative_profit, 4),
            "total_profit_amount": round(cumulative_amount, 2),
            "curve": result
        }
    except Exception as e:
        import traceback
        logger.error(f"[profit-curve] 错误: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/available-symbols")
async def get_available_symbols():
    """获取所有有订单的币种列表"""
    try:
        from app.db.connection import fetch_all
        
        query = """
            SELECT DISTINCT symbol, COUNT(*) as order_count
            FROM ai_trading_orders 
            GROUP BY symbol
            ORDER BY order_count DESC
        """
        
        rows = await fetch_all(query)
        return [{
            "symbol": row["symbol"],
            "order_count": row["order_count"]
        } for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/interval-stats")
async def get_interval_stats():
    """获取不同周期的盈亏追踪统计"""
    try:
        from app.db.connection import fetch_all
        
        query = """
            SELECT 
                tracking_interval,
                COUNT(*) as tracking_count,
                AVG(profit_percentage) as avg_profit,
                AVG(interval_pnl_ratio) as avg_pnl_ratio,
                SUM(CASE WHEN is_stop_loss_triggered = true THEN 1 ELSE 0 END) as stop_loss_count,
                SUM(CASE WHEN is_take_profit_triggered = true THEN 1 ELSE 0 END) as take_profit_count
            FROM order_profit_tracking 
            WHERE tracking_interval IN ('30m', '1h', '2h', '4h', '6h')
            GROUP BY tracking_interval
            ORDER BY 
                CASE tracking_interval 
                    WHEN '30m' THEN 1 
                    WHEN '1h' THEN 2 
                    WHEN '2h' THEN 3 
                    WHEN '4h' THEN 4 
                    WHEN '6h' THEN 5 
                END
        """
        
        rows = await fetch_all(query)
        return [{
            "interval": row["tracking_interval"],
            "tracking_count": row["tracking_count"],
            "avg_profit": float(row["avg_profit"] or 0),
            "avg_pnl_ratio": float(row["avg_pnl_ratio"] or 0),
            "stop_loss_count": row["stop_loss_count"] or 0,
            "take_profit_count": row["take_profit_count"] or 0
        } for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/summary", response_model=List[OrderStatistics])
async def get_statistics(
    symbol: Optional[str] = Query(None, description="筛选交易对")
):
    """获取订单统计数据（胜率、总盈亏等）"""
    try:
        from app.services.order_service import order_service
        stats = await order_service.get_statistics(symbol)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profit-tracker/status")
async def get_profit_tracker_status():
    """获取盈亏追踪调度器状态"""
    try:
        from app.scheduler.profit_tracker import profit_tracker
        return profit_tracker.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profit-tracker/start")
async def start_profit_tracker():
    """启动盈亏追踪调度器"""
    try:
        from app.scheduler.profit_tracker import profit_tracker
        await profit_tracker.start()
        return {"message": "Profit tracker started", "status": profit_tracker.get_status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profit-tracker/stop")
async def stop_profit_tracker():
    """停止盈亏追踪调度器"""
    try:
        from app.scheduler.profit_tracker import profit_tracker
        await profit_tracker.stop()
        return {"message": "Profit tracker stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-all-profits")
async def calculate_all_profits():
    """手动触发所有未平仓订单的盈亏计算"""
    try:
        from app.services.order_service import order_service
        from exchanges.binance.futures import BinanceFuturesClient
        
        open_orders = await order_service.get_open_orders()
        
        if not open_orders:
            return {"message": "No open orders to process", "processed": 0, "results": []}
        
        client = BinanceFuturesClient()
        results = []
        
        for order in open_orders:
            try:
                ticker = client.get_symbol_ticker(order.symbol)
                current_price = float(ticker.get('price', 0))
                
                if current_price <= 0 or not order.entry_price:
                    continue
                
                if order.recommendation == "BUY":
                    profit_percentage = ((current_price - order.entry_price) / order.entry_price) * 100
                else:
                    profit_percentage = ((order.entry_price - current_price) / order.entry_price) * 100
                
                await order_service.add_profit_tracking(
                    order_id=order.id,
                    current_price=current_price,
                    profit_percentage=profit_percentage,
                    tracking_interval="manual"
                )
                
                results.append({
                    "order_id": order.id,
                    "symbol": order.symbol,
                    "profit_percentage": round(profit_percentage, 4)
                })
            except Exception as e:
                results.append({
                    "order_id": order.id,
                    "symbol": order.symbol,
                    "error": str(e)
                })
        
        return {
            "message": f"Calculated profit for {len(results)} orders",
            "processed": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profit-analytics", response_model=ProfitAnalyticsResponse)
async def get_profit_analytics(
    period: str = Query("month", description="时间段 (today/week/month/all/custom)"),
    symbol: Optional[str] = Query(None, description="筛选交易对"),
    start_date: Optional[str] = Query(None, description="自定义开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="自定义结束日期 (YYYY-MM-DD)")
):
    """获取盈利分析数据"""
    try:
        from app.services.order_service import order_service
        from datetime import datetime
        
        parsed_start = None
        parsed_end = None
        if period == "custom":
            if start_date:
                parsed_start = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                parsed_end = datetime.strptime(end_date, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59
                )
        
        analytics = await order_service.get_profit_analytics(
            period=period,
            symbol=symbol,
            start_date=parsed_start,
            end_date=parsed_end
        )
        
        return analytics
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================
# 动态路由 (包含 {order_id} 参数)
# =============================================

@router.get("/{order_id}", response_model=AITradingOrder)
async def get_order(
    order_id: int = Path(..., description="订单ID")
):
    """获取单个订单详情"""
    try:
        from app.services.order_service import order_service
        
        order = await order_service.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/profits", response_model=ProfitTrackingResponse)
async def get_order_profits(
    order_id: int = Path(..., description="订单ID"),
    interval: Optional[str] = Query(None, description="筛选追踪周期 (30m/1h/2h/4h)")
):
    """获取订单盈亏追踪历史"""
    try:
        from app.services.order_service import order_service
        
        order = await order_service.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        history = await order_service.get_profit_history(order_id, interval)
        
        # 计算概览
        summary = {
            "order_id": order_id,
            "symbol": order.symbol,
            "entry_price": order.entry_price,
            "current_status": order.status.value if hasattr(order.status, 'value') else order.status,
            "tracking_count": len(history),
            "latest_profit": history[0].profit_percentage if history else None,
            "max_profit": max((h.profit_percentage for h in history), default=None),
            "min_profit": min((h.profit_percentage for h in history), default=None),
        }
        
        return ProfitTrackingResponse(
            order_id=order_id,
            history=history,
            summary=summary
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profit-analytics", response_model=ProfitAnalyticsResponse)
async def get_profit_analytics(
    period: str = Query("month", description="时间段 (today/week/month/all/custom)"),
    symbol: Optional[str] = Query(None, description="筛选交易对"),
    start_date: Optional[str] = Query(None, description="自定义开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="自定义结束日期 (YYYY-MM-DD)")
):
    """
    获取盈利分析数据
    
    - period: today/week/month/all/custom
    - 包含时间段内的盈亏统计、止盈止损分类、价格极值
    """
    try:
        from app.services.order_service import order_service
        from datetime import datetime
        
        # 解析自定义日期
        parsed_start = None
        parsed_end = None
        if period == "custom":
            if start_date:
                parsed_start = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                parsed_end = datetime.strptime(end_date, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59
                )
        
        analytics = await order_service.get_profit_analytics(
            period=period,
            symbol=symbol,
            start_date=parsed_start,
            end_date=parsed_end
        )
        
        return analytics
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.delete("/{order_id}")
async def close_order(
    order_id: int = Path(..., description="订单ID"),
    closed_price: Optional[float] = Query(None, description="平仓价格")
):
    """手动平仓订单"""
    try:
        from app.services.order_service import order_service
        from app.db.models import OrderStatus
        
        order = await order_service.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        if order.status != OrderStatus.OPEN:
            raise HTTPException(status_code=400, detail=f"Order {order_id} is already closed")
        
        # 获取当前价格
        if not closed_price:
            from exchanges.binance.futures import BinanceFuturesClient
            client = BinanceFuturesClient()
            ticker = client.get_symbol_ticker(order.symbol)
            closed_price = float(ticker.get('price', 0))
        
        # 计算收益
        if order.entry_price:
            if order.recommendation == "BUY":
                profit_percentage = ((closed_price - order.entry_price) / order.entry_price) * 100
            else:
                profit_percentage = ((order.entry_price - closed_price) / order.entry_price) * 100
        else:
            profit_percentage = 0
        
        await order_service.update_order_status(
            order_id=order_id,
            status=OrderStatus.CLOSED,
            closed_price=closed_price,
            final_profit_percentage=profit_percentage
        )
        
        return {
            "message": f"Order {order_id} closed",
            "closed_price": closed_price,
            "final_profit_percentage": profit_percentage
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ProfitCalculationResult(BaseModel):
    """Result of manual profit calculation"""
    order_id: int
    symbol: str
    current_price: float
    entry_price: float
    profit_percentage: float
    is_stop_loss_triggered: bool = False
    is_take_profit_triggered: bool = False
    triggered_target: Optional[str] = None


@router.post("/{order_id}/calculate-profit", response_model=ProfitCalculationResult)
async def calculate_order_profit(
    order_id: int = Path(..., description="订单ID")
):
    """
    手动触发单个订单的盈亏计算
    
    获取当前价格并计算该订单的实时盈亏百分比
    """
    try:
        from app.services.order_service import order_service
        from exchanges.binance.futures import BinanceFuturesClient
        
        order = await order_service.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        if order.status != OrderStatus.OPEN:
            raise HTTPException(status_code=400, detail=f"Order {order_id} is not open")
        
        # 获取当前价格
        client = BinanceFuturesClient()
        ticker = client.get_symbol_ticker(order.symbol)
        current_price = float(ticker.get('price', 0))
        
        if current_price <= 0:
            raise HTTPException(status_code=400, detail="Unable to get current price")
        
        # 计算盈亏
        entry_price = order.entry_price or 0
        if entry_price <= 0:
            raise HTTPException(status_code=400, detail="Order has no valid entry price")
        
        if order.recommendation == "BUY":
            profit_percentage = ((current_price - entry_price) / entry_price) * 100
        else:
            profit_percentage = ((entry_price - current_price) / entry_price) * 100
        
        # 检查止损/止盈
        is_stop_loss = False
        is_take_profit = False
        triggered_target = None
        
        if order.stop_loss:
            if order.recommendation == "BUY":
                is_stop_loss = current_price <= order.stop_loss
            else:
                is_stop_loss = current_price >= order.stop_loss
        
        # 检查止盈
        targets = [("T3", order.target_t3), ("T2", order.target_t2), ("T1", order.target_t1)]
        for target_name, target_price in targets:
            if target_price:
                if order.recommendation == "BUY" and current_price >= target_price:
                    is_take_profit = True
                    triggered_target = target_name
                    break
                elif order.recommendation != "BUY" and current_price <= target_price:
                    is_take_profit = True
                    triggered_target = target_name
                    break
        
        # 记录盈亏追踪
        await order_service.add_profit_tracking(
            order_id=order.id,
            current_price=current_price,
            profit_percentage=profit_percentage,
            tracking_interval="manual",
            is_stop_loss_triggered=is_stop_loss,
            is_take_profit_triggered=is_take_profit,
            triggered_target=triggered_target
        )
        
        return ProfitCalculationResult(
            order_id=order.id,
            symbol=order.symbol,
            current_price=current_price,
            entry_price=entry_price,
            profit_percentage=profit_percentage,
            is_stop_loss_triggered=is_stop_loss,
            is_take_profit_triggered=is_take_profit,
            triggered_target=triggered_target
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-all-profits")
async def calculate_all_profits():
    """
    手动触发所有未平仓订单的盈亏计算
    
    批量获取当前价格并计算所有OPEN订单的实时盈亏
    """
    try:
        from app.services.order_service import order_service
        from exchanges.binance.futures import BinanceFuturesClient
        
        open_orders = await order_service.get_open_orders()
        
        if not open_orders:
            return {"message": "No open orders to process", "processed": 0, "results": []}
        
        client = BinanceFuturesClient()
        results = []
        
        for order in open_orders:
            try:
                ticker = client.get_symbol_ticker(order.symbol)
                current_price = float(ticker.get('price', 0))
                
                if current_price <= 0 or not order.entry_price:
                    continue
                
                if order.recommendation == "BUY":
                    profit_percentage = ((current_price - order.entry_price) / order.entry_price) * 100
                else:
                    profit_percentage = ((order.entry_price - current_price) / order.entry_price) * 100
                
                await order_service.add_profit_tracking(
                    order_id=order.id,
                    current_price=current_price,
                    profit_percentage=profit_percentage,
                    tracking_interval="manual"
                )
                
                results.append({
                    "order_id": order.id,
                    "symbol": order.symbol,
                    "current_price": current_price,
                    "profit_percentage": profit_percentage
                })
            except Exception as order_err:
                results.append({
                    "order_id": order.id,
                    "symbol": order.symbol,
                    "error": str(order_err)
                })
        
        return {
            "message": f"Processed {len(results)} orders",
            "processed": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

