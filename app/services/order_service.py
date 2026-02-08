# app/services/order_service.py
"""Order Service for AI Trading Orders"""

import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.db.connection import execute_query, fetch_one, fetch_all, fetch_val
from app.db.models import (
    AITradingOrder, OrderProfitTracking, OrderCreate, OrderStatus, OrderStatistics,
    PriceExtremes, TakeProfitStats, ProfitPeriodStats, ProfitAnalyticsResponse
)

logger = logging.getLogger(__name__)


class OrderService:
    """Service for managing AI trading orders"""

    async def create_order(self, order: OrderCreate) -> int:
        """
        Create a new trading order
        
        Args:
            order: OrderCreate model with order details
            
        Returns:
            The ID of the created order
        """
        query = """
            INSERT INTO ai_trading_orders (
                symbol, interval, ai_model, recommendation, risk_level,
                trend_status, momentum, entry_price_min, entry_price_max,
                entry_price, stop_loss, stop_loss_percentage,
                target_t1, target_t2, target_t3, position_size_percentage,
                analysis_summary, indicator_alerts, raw_analysis
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19
            ) RETURNING id
        """
        
        order_id = await fetch_val(
            query,
            order.symbol,
            order.interval,
            order.ai_model,
            order.recommendation,
            order.risk_level,
            order.trend_status,
            order.momentum,
            order.entry_price_min,
            order.entry_price_max,
            order.entry_price,
            order.stop_loss,
            order.stop_loss_percentage,
            order.target_t1,
            order.target_t2,
            order.target_t3,
            order.position_size_percentage,
            order.analysis_summary,
            order.indicator_alerts,
            json.dumps(order.raw_analysis) if order.raw_analysis else None
        )
        
        logger.info(f"Created order {order_id} for {order.symbol} - {order.recommendation} ({order.risk_level})")
        return order_id

    async def create_order_from_analysis(
        self,
        symbol: str,
        interval: str,
        analysis: Dict[str, Any],
        current_price: float,
        ai_model: Optional[str] = None
    ) -> Optional[int]:
        """
        Create order from AI analysis result if risk level is LOW or MEDIUM
        
        Args:
            symbol: Trading symbol
            interval: K-line interval
            analysis: Parsed TraderOutputModel dict
            current_price: Current market price
            
        Returns:
            Order ID if created, None otherwise
        """
        risk_level = analysis.get("risk_level", "HIGH")
        
        # Only create orders for LOW or MEDIUM risk
        if risk_level not in ["LOW", "MEDIUM"]:
            logger.info(f"Skipping order creation for {symbol}: risk_level={risk_level} (HIGH)")
            return None
        
        # Extract targets
        targets = analysis.get("targets", [])
        target_t1 = next((t.get("price") for t in targets if t.get("level") == "T1"), None)
        target_t2 = next((t.get("price") for t in targets if t.get("level") == "T2"), None)
        target_t3 = next((t.get("price") for t in targets if t.get("level") == "T3"), None)
        
        order = OrderCreate(
            symbol=symbol,
            interval=interval,
            ai_model=ai_model,
            recommendation=analysis.get("recommendation", "HOLD"),
            risk_level=risk_level,
            trend_status=analysis.get("trend_status"),
            momentum=analysis.get("momentum"),
            entry_price_min=analysis.get("entry_price_min"),
            entry_price_max=analysis.get("entry_price_max"),
            entry_price=current_price,
            stop_loss=analysis.get("stop_loss"),
            stop_loss_percentage=analysis.get("stop_loss_percentage"),
            target_t1=target_t1,
            target_t2=target_t2,
            target_t3=target_t3,
            position_size_percentage=analysis.get("position_size_percentage"),
            analysis_summary=analysis.get("analysis_summary"),
            indicator_alerts=analysis.get("indicator_alerts"),
            raw_analysis=analysis
        )
        
        return await self.create_order(order)

    async def get_order(self, order_id: int) -> Optional[AITradingOrder]:
        """Get order by ID"""
        query = "SELECT * FROM ai_trading_orders WHERE id = $1"
        row = await fetch_one(query, order_id)
        if row:
            if row.get('raw_analysis'):
                row['raw_analysis'] = json.loads(row['raw_analysis']) if isinstance(row['raw_analysis'], str) else row['raw_analysis']
            return AITradingOrder(**row)
        return None

    async def get_open_orders(self) -> List[AITradingOrder]:
        """Get all open orders"""
        query = "SELECT * FROM ai_trading_orders WHERE status = 'OPEN' ORDER BY created_at DESC"
        rows = await fetch_all(query)
        orders = []
        for row in rows:
            if row.get('raw_analysis'):
                row['raw_analysis'] = json.loads(row['raw_analysis']) if isinstance(row['raw_analysis'], str) else row['raw_analysis']
            orders.append(AITradingOrder(**row))
        return orders

    async def get_orders(
        self,
        symbol: Optional[str] = None,
        status: Optional[str] = None,
        recommendation: Optional[str] = None,
        risk_level: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AITradingOrder]:
        """Get orders with optional filters"""
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
        
        if start_date:
            conditions.append(f"created_at >= ${param_idx}")
            params.append(start_date)
            param_idx += 1
        
        if end_date:
            conditions.append(f"created_at <= ${param_idx}")
            params.append(end_date)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM ai_trading_orders 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])
        
        rows = await fetch_all(query, *params)
        orders = []
        for row in rows:
            if row.get('raw_analysis'):
                row['raw_analysis'] = json.loads(row['raw_analysis']) if isinstance(row['raw_analysis'], str) else row['raw_analysis']
            orders.append(AITradingOrder(**row))
        return orders

    async def update_order_status(
        self,
        order_id: int,
        status: OrderStatus,
        closed_price: Optional[float] = None,
        final_profit_percentage: Optional[float] = None
    ) -> bool:
        """Update order status"""
        query = """
            UPDATE ai_trading_orders 
            SET status = $1, closed_at = $2, closed_price = $3, final_profit_percentage = $4
            WHERE id = $5
        """
        closed_at = datetime.now() if status != OrderStatus.OPEN else None
        await execute_query(query, status.value, closed_at, closed_price, final_profit_percentage, order_id)
        logger.info(f"Updated order {order_id} status to {status.value}")
        return True

    async def add_profit_tracking(
        self,
        order_id: int,
        current_price: float,
        profit_percentage: float,
        tracking_interval: str,
        profit_amount: Optional[float] = None,
        is_stop_loss_triggered: bool = False,
        is_take_profit_triggered: bool = False,
        triggered_target: Optional[str] = None
    ) -> int:
        """Add profit tracking record"""
        query = """
            INSERT INTO order_profit_tracking (
                order_id, current_price, profit_percentage, profit_amount,
                tracking_interval, is_stop_loss_triggered, is_take_profit_triggered, triggered_target
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """
        
        tracking_id = await fetch_val(
            query,
            order_id, current_price, profit_percentage, profit_amount,
            tracking_interval, is_stop_loss_triggered, is_take_profit_triggered, triggered_target
        )
        
        logger.debug(f"Added profit tracking {tracking_id} for order {order_id}: {profit_percentage}%")
        return tracking_id

    async def get_profit_history(
        self,
        order_id: int,
        interval: Optional[str] = None
    ) -> List[OrderProfitTracking]:
        """Get profit tracking history for an order"""
        if interval:
            query = """
                SELECT * FROM order_profit_tracking 
                WHERE order_id = $1 AND tracking_interval = $2
                ORDER BY tracked_at DESC
            """
            rows = await fetch_all(query, order_id, interval)
        else:
            query = """
                SELECT * FROM order_profit_tracking 
                WHERE order_id = $1
                ORDER BY tracked_at DESC
            """
            rows = await fetch_all(query, order_id)
        
        return [OrderProfitTracking(**row) for row in rows]

    async def get_statistics(self, symbol: Optional[str] = None) -> List[OrderStatistics]:
        """Get order statistics"""
        if symbol:
            query = "SELECT * FROM order_statistics WHERE symbol = $1"
            rows = await fetch_all(query, symbol)
        else:
            query = "SELECT * FROM order_statistics"
            rows = await fetch_all(query)
        
        return [OrderStatistics(**row) for row in rows]

    async def get_profit_analytics(
        self,
        period: str = "month",
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ProfitAnalyticsResponse:
        """
        获取盈利分析数据
        
        Args:
            period: 时间段 (today/week/month/all/custom)
            symbol: 可选，筛选交易对
            start_date: 自定义开始日期
            end_date: 自定义结束日期
        
        Returns:
            ProfitAnalyticsResponse with complete analytics
        """
        from datetime import timedelta
        
        now = datetime.now()
        
        # 计算时间范围
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == "week":
            start_date = now - timedelta(days=7)
            end_date = now
        elif period == "month":
            start_date = now - timedelta(days=30)
            end_date = now
        elif period == "all":
            start_date = None
            end_date = None
        # custom uses provided start_date/end_date
        
        # 构建查询条件
        conditions = []
        params = []
        param_idx = 1
        
        if start_date:
            conditions.append(f"created_at >= ${param_idx}")
            params.append(start_date)
            param_idx += 1
        if end_date:
            conditions.append(f"created_at <= ${param_idx}")
            params.append(end_date)
            param_idx += 1
        if symbol:
            conditions.append(f"symbol = ${param_idx}")
            params.append(symbol)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 获取所有订单统计
        query = f"""
            SELECT 
                COUNT(*) as total_orders,
                COUNT(CASE WHEN status != 'OPEN' THEN 1 END) as closed_orders,
                COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_orders,
                COUNT(CASE WHEN final_profit_percentage > 0 THEN 1 END) as win_count,
                COUNT(CASE WHEN final_profit_percentage < 0 THEN 1 END) as loss_count,
                COALESCE(SUM(final_profit_percentage), 0) as total_profit,
                COALESCE(AVG(CASE WHEN final_profit_percentage IS NOT NULL THEN final_profit_percentage END), 0) as avg_profit,
                COUNT(CASE WHEN status = 'STOP_LOSS' THEN 1 END) as stop_loss_count,
                COALESCE(SUM(CASE WHEN status = 'STOP_LOSS' THEN final_profit_percentage END), 0) as stop_loss_total,
                COUNT(CASE WHEN status = 'TAKE_PROFIT_T1' THEN 1 END) as t1_count,
                COALESCE(SUM(CASE WHEN status = 'TAKE_PROFIT_T1' THEN final_profit_percentage END), 0) as t1_total,
                COUNT(CASE WHEN status = 'TAKE_PROFIT_T2' THEN 1 END) as t2_count,
                COALESCE(SUM(CASE WHEN status = 'TAKE_PROFIT_T2' THEN final_profit_percentage END), 0) as t2_total,
                COUNT(CASE WHEN status = 'TAKE_PROFIT_T3' THEN 1 END) as t3_count,
                COALESCE(SUM(CASE WHEN status = 'TAKE_PROFIT_T3' THEN final_profit_percentage END), 0) as t3_total
            FROM ai_trading_orders
            WHERE {where_clause}
        """
        
        stats_row = await fetch_one(query, *params)
        
        # 获取价格极值
        price_extremes = await self.get_price_extremes(
            period=period,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        # 构建止盈统计
        take_profit_stats = TakeProfitStats(
            t1_count=stats_row.get('t1_count', 0) if stats_row else 0,
            t1_total_profit=float(stats_row.get('t1_total', 0) or 0) if stats_row else 0,
            t2_count=stats_row.get('t2_count', 0) if stats_row else 0,
            t2_total_profit=float(stats_row.get('t2_total', 0) or 0) if stats_row else 0,
            t3_count=stats_row.get('t3_count', 0) if stats_row else 0,
            t3_total_profit=float(stats_row.get('t3_total', 0) or 0) if stats_row else 0,
        )
        
        # 构建止损统计
        stop_loss_stats = {
            "count": stats_row.get('stop_loss_count', 0) if stats_row else 0,
            "total_loss": float(stats_row.get('stop_loss_total', 0) or 0) if stats_row else 0,
        }
        
        # 计算胜率
        total_closed = (stats_row.get('win_count', 0) or 0) + (stats_row.get('loss_count', 0) or 0) if stats_row else 0
        win_rate = ((stats_row.get('win_count', 0) or 0) / total_closed * 100) if total_closed > 0 else None
        
        # 构建响应
        period_stats = ProfitPeriodStats(
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_orders=stats_row.get('total_orders', 0) if stats_row else 0,
            closed_orders=stats_row.get('closed_orders', 0) if stats_row else 0,
            open_orders=stats_row.get('open_orders', 0) if stats_row else 0,
            win_count=stats_row.get('win_count', 0) if stats_row else 0,
            loss_count=stats_row.get('loss_count', 0) if stats_row else 0,
            total_profit_percentage=float(stats_row.get('total_profit', 0) or 0) if stats_row else 0,
            avg_profit_percentage=float(stats_row.get('avg_profit', 0) or 0) if stats_row else 0,
            win_rate=win_rate,
            take_profit_stats=take_profit_stats,
            stop_loss_stats=stop_loss_stats,
            price_extremes=price_extremes,
        )
        
        # 获取订单摘要列表
        orders_summary = await self._get_orders_summary(where_clause, params)
        
        return ProfitAnalyticsResponse(
            period=period,
            symbol=symbol,
            stats=period_stats,
            orders_summary=orders_summary
        )

    async def get_price_extremes(
        self,
        period: str,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[PriceExtremes]:
        """获取时间段内的价格极值"""
        conditions = []
        params = []
        param_idx = 1
        
        if start_date:
            conditions.append(f"tracked_at >= ${param_idx}")
            params.append(start_date)
            param_idx += 1
        if end_date:
            conditions.append(f"tracked_at <= ${param_idx}")
            params.append(end_date)
            param_idx += 1
        if symbol:
            conditions.append(f"o.symbol = ${param_idx}")
            params.append(symbol)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT 
                MIN(current_price) as low_price,
                MAX(current_price) as high_price
            FROM order_profit_tracking t
            JOIN ai_trading_orders o ON t.order_id = o.id
            WHERE {where_clause}
        """
        
        row = await fetch_one(query, *params)
        if not row or (row.get('low_price') is None and row.get('high_price') is None):
            return None
        
        # 获取最低价时间
        low_query = f"""
            SELECT tracked_at FROM order_profit_tracking t
            JOIN ai_trading_orders o ON t.order_id = o.id
            WHERE {where_clause} AND current_price = ${param_idx}
            ORDER BY tracked_at LIMIT 1
        """
        low_time_row = await fetch_one(low_query, *params, row.get('low_price'))
        
        # 获取最高价时间
        high_query = f"""
            SELECT tracked_at FROM order_profit_tracking t
            JOIN ai_trading_orders o ON t.order_id = o.id
            WHERE {where_clause} AND current_price = ${param_idx}
            ORDER BY tracked_at LIMIT 1
        """
        high_time_row = await fetch_one(high_query, *params, row.get('high_price'))
        
        return PriceExtremes(
            period=period,
            low_price=float(row.get('low_price')) if row.get('low_price') else None,
            low_price_time=low_time_row.get('tracked_at') if low_time_row else None,
            high_price=float(row.get('high_price')) if row.get('high_price') else None,
            high_price_time=high_time_row.get('tracked_at') if high_time_row else None,
        )

    async def _get_orders_summary(self, where_clause: str, params: list) -> List[dict]:
        """获取订单摘要列表"""
        query = f"""
            SELECT 
                id, symbol, recommendation, status, 
                entry_price, closed_price, final_profit_percentage,
                created_at, closed_at
            FROM ai_trading_orders
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT 50
        """
        
        rows = await fetch_all(query, *params)
        return [
            {
                "id": row.get('id'),
                "symbol": row.get('symbol'),
                "recommendation": row.get('recommendation'),
                "status": row.get('status'),
                "entry_price": float(row.get('entry_price')) if row.get('entry_price') else None,
                "closed_price": float(row.get('closed_price')) if row.get('closed_price') else None,
                "profit_percentage": float(row.get('final_profit_percentage')) if row.get('final_profit_percentage') else None,
                "created_at": row.get('created_at').isoformat() if row.get('created_at') else None,
                "closed_at": row.get('closed_at').isoformat() if row.get('closed_at') else None,
            }
            for row in rows
        ]

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics"""
        # 1. Get total stats
        total_query = """
            SELECT 
                COUNT(*) as total_orders,
                COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_orders,
                COUNT(CASE WHEN status != 'OPEN' THEN 1 END) as closed_orders,
                COUNT(CASE WHEN final_profit_percentage > 0 THEN 1 END) as win_count,
                COUNT(CASE WHEN final_profit_percentage < 0 THEN 1 END) as loss_count,
                COALESCE(SUM(final_profit_percentage), 0) as total_profit_percentage
            FROM ai_trading_orders
        """
        total_row = await fetch_one(total_query)
        
        # Calculate win rate
        win_count = total_row.get('win_count', 0) or 0
        loss_count = total_row.get('loss_count', 0) or 0
        total_closed = win_count + loss_count
        win_rate = (win_count / total_closed * 100) if total_closed > 0 else None
        
        # 2. Get per-symbol stats
        symbol_query = """
            SELECT 
                symbol,
                COUNT(*) as total_orders,
                COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_orders,
                COUNT(CASE WHEN status != 'OPEN' THEN 1 END) as closed_orders,
                COUNT(CASE WHEN final_profit_percentage > 0 THEN 1 END) as win_count,
                COUNT(CASE WHEN final_profit_percentage < 0 THEN 1 END) as loss_count,
                COALESCE(SUM(final_profit_percentage), 0) as total_profit
            FROM ai_trading_orders
            GROUP BY symbol
            ORDER BY total_orders DESC
        """
        symbol_rows = await fetch_all(symbol_query)
        
        symbol_stats = []
        for row in symbol_rows:
            s_win = row.get('win_count', 0) or 0
            s_loss = row.get('loss_count', 0) or 0
            s_total_closed = s_win + s_loss
            s_win_rate = (s_win / s_total_closed * 100) if s_total_closed > 0 else None
            
            symbol_stats.append({
                "symbol": row.get('symbol'),
                "total_orders": row.get('total_orders', 0),
                "open_orders": row.get('open_orders', 0),
                "closed_orders": row.get('closed_orders', 0),
                "win_count": s_win,
                "loss_count": s_loss,
                "total_profit": float(row.get('total_profit', 0) or 0),
                "win_rate": s_win_rate
            })
            
        return {
            "total_profit_percentage": float(total_row.get('total_profit_percentage', 0) or 0),
            "total_orders": total_row.get('total_orders', 0),
            "open_orders": total_row.get('open_orders', 0),
            "closed_orders": total_row.get('closed_orders', 0),
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": win_rate,
            "symbol_stats": symbol_stats
        }


    async def get_active_realtime_configs(self) -> Dict[int, dict]:
        """Get all active realtime tracking configurations"""
        query = "SELECT * FROM realtime_tracking_config WHERE is_enabled = true"
        rows = await fetch_all(query)
        return {row['order_id']: dict(row) for row in rows}


# Global service instance
order_service = OrderService()
