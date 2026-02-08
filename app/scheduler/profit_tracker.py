# app/scheduler/profit_tracker.py
"""Profit Tracking Scheduler - 定时追踪订单盈亏"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.models import OrderStatus, TrackingInterval

logger = logging.getLogger(__name__)


class ProfitTracker:
    """定时追踪订单盈亏的调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

    async def start(self):
        """启动盈亏追踪调度器"""
        if self._is_running:
            logger.info("Profit tracker already running")
            return

        # 添加定时任务 - 30分钟、1小时、2小时、4小时
        tracking_schedules = [
            ("profit_30m", "*/30 * * * *", TrackingInterval.THIRTY_MIN),
            ("profit_1h", "0 * * * *", TrackingInterval.ONE_HOUR),
            ("profit_2h", "0 */2 * * *", TrackingInterval.TWO_HOUR),
            ("profit_4h", "0 */4 * * *", TrackingInterval.FOUR_HOUR),
        ]

        # 添加实时追踪任务 (每分钟)
        self.scheduler.add_job(
            self._track_profits,
            trigger=CronTrigger(minute="*"),
            id="profit_realtime",
            name="Profit tracking - Realtime",
            kwargs={"interval": "realtime"},
            replace_existing=True
        )

        for job_id, cron_expr, interval in tracking_schedules:
            self.scheduler.add_job(
                self._track_profits,
                trigger=CronTrigger.from_crontab(cron_expr),
                id=job_id,
                name=f"Profit tracking - {interval.value}",
                kwargs={"interval": interval.value},
                replace_existing=True
            )
            logger.info(f"Added profit tracking job: {job_id} with schedule '{cron_expr}'")

        self.scheduler.start()
        self._is_running = True
        logger.info("Profit tracker started with 4 tracking intervals")

    async def stop(self):
        """停止盈亏追踪调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        self._is_running = False
        logger.info("Profit tracker stopped")

    async def _track_profits(self, interval: str):
        """
        追踪所有OPEN状态订单的盈亏
        
        Args:
            interval: 追踪周期 (30m/1h/2h/4h) 或 'realtime'
        """
        try:
            from app.services.order_service import order_service
            from exchanges.binance.futures import BinanceFuturesClient
            
            logger.info(f"开始 {interval} 盈亏追踪...")
            
            # 获取所有未平仓订单
            open_orders = await order_service.get_open_orders()
            
            if not open_orders:
                return
            
            # 获取实时配置
            realtime_configs = await order_service.get_active_realtime_configs()
            
            # 确定要处理的订单
            orders_to_process = []
            if interval == "realtime":
                # 实时模式：只处理开启了配置的订单
                orders_to_process = [o for o in open_orders if o.id in realtime_configs]
            else:
                # 定时模式：处理所有订单 (或者可以排除实时订单以避免重复，但保留重复检查更安全)
                orders_to_process = open_orders

            if not orders_to_process:
                return

            logger.info(f"追踪 {len(orders_to_process)} 个未平仓订单 (模式: {interval})")
            
            # 获取Binance客户端
            client = BinanceFuturesClient()
            
            for order in orders_to_process:
                try:
                    # 获取该订单的追踪K线周期
                    tracking_interval = interval
                    if order.id in realtime_configs:
                        tracking_interval = realtime_configs[order.id].get('tracking_interval', '1m')
                    elif interval == "realtime":
                        tracking_interval = '1m'

                    await self._process_order(
                        order=order,
                        client=client,
                        order_service=order_service,
                        interval=tracking_interval
                    )
                except Exception as order_error:
                    logger.error(f"处理订单 {order.id} 失败: {str(order_error)}")
            
            logger.info(f"完成 {interval} 盈亏追踪")
            
        except ImportError as e:
            logger.warning(f"盈亏追踪跳过（依赖未初始化）: {str(e)}")
        except Exception as e:
            logger.error(f"盈亏追踪失败: {str(e)}")

    async def _process_order(
        self,
        order,
        client,
        order_service,
        interval: str
    ):
        """处理单个订单的盈亏追踪"""
        from app.core import robot
        
        # 获取K线数据 (使用High/Low进行检测)
        try:
            # 确保interval符合Binance要求 (例如 'realtime' 不是有效interval)
            kline_interval = interval if interval in ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d'] else '1h'
            
            klines = client.get_klines(order.symbol, interval=kline_interval, limit=1)
            if not klines:
                logger.warning(f"获取K线数据失败: {order.symbol} {kline_interval}")
                return
                
            latest_kline = klines[-1]
            current_price = float(latest_kline['close'])
            high_price = float(latest_kline['high'])
            low_price = float(latest_kline['low'])
            
        except Exception as e:
            logger.error(f"获取行情异常 {order.symbol}: {e}")
            return
        
        if current_price <= 0:
            logger.warning(f"订单 {order.id} ({order.symbol}) 价格无效: {current_price}")
            return
        
        # 计算盈亏百分比
        entry_price = order.entry_price
        if not entry_price or entry_price <= 0:
            logger.warning(f"订单 {order.id} 入场价格无效")
            return
        
        # 根据方向计算盈亏
        if order.recommendation == "BUY":
            profit_percentage = ((current_price - entry_price) / entry_price) * 100
        else:  # SELL
            profit_percentage = ((entry_price - current_price) / entry_price) * 100
        
        profit_amount = (current_price - entry_price) if order.recommendation == "BUY" else (entry_price - current_price)
        
        # 检查是否触发止损 (使用High/Low)
        is_stop_loss = self._check_stop_loss(order, current_price, high_price, low_price)
        
        # 检查是否触发止盈 (使用High/Low)
        take_profit_result = self._check_take_profit(order, current_price, high_price, low_price)
        is_take_profit = take_profit_result["triggered"]
        triggered_target = take_profit_result.get("target")
        
        # 记录盈亏追踪 (记录当前Closed Price)
        await order_service.add_profit_tracking(
        await order_service.add_profit_tracking(
            order_id=order.id,
            current_price=current_price,
            profit_percentage=profit_percentage,
            profit_amount=profit_amount,
            tracking_interval=interval,
            is_stop_loss_triggered=is_stop_loss,
            is_take_profit_triggered=is_take_profit,
            triggered_target=triggered_target
        )
        
        # 如果触发止损或止盈，更新订单状态
        if is_stop_loss:
            await order_service.update_order_status(
                order_id=order.id,
                status=OrderStatus.STOP_LOSS,
                closed_price=current_price,
                final_profit_percentage=profit_percentage
            )
            await self._send_alert(order, current_price, profit_percentage, "止损触发")
            
        elif is_take_profit:
            status = getattr(OrderStatus, f"TAKE_PROFIT_{triggered_target}", OrderStatus.CLOSED)
            await order_service.update_order_status(
                order_id=order.id,
                status=status,
                closed_price=current_price,
                final_profit_percentage=profit_percentage
            )
            await self._send_alert(order, current_price, profit_percentage, f"止盈触发 ({triggered_target})")
        
        logger.debug(f"订单 {order.id}: 当前价 {current_price}, 盈亏 {profit_percentage:.2f}%")

    def _check_stop_loss(self, order, current_price: float, high_price: float, low_price: float) -> bool:
        """检查是否触发止损"""
        if not order.stop_loss:
            return False
        
        if order.recommendation == "BUY":
            # 买入单：如果最低价跌破止损价，触发止损
            return low_price <= order.stop_loss
        else:  # SELL
            # 卖出单：如果最高价涨破止损价，触发止损
            return high_price >= order.stop_loss

    def _check_take_profit(self, order, current_price: float, high_price: float, low_price: float) -> Dict[str, Any]:
        """检查是否触发止盈"""
        result = {"triggered": False, "target": None}
        
        targets = [
            ("T3", order.target_t3),
            ("T2", order.target_t2),
            ("T1", order.target_t1),
        ]
        
        for target_name, target_price in targets:
            if not target_price:
                continue
            
            if order.recommendation == "BUY":
                # 买入单：如果最高价触及目标价
                if high_price >= target_price:
                    result["triggered"] = True
                    result["target"] = target_name
                    break
            else:  # SELL
                # 卖出单：如果最低价触及目标价
                if low_price <= target_price:
                    result["triggered"] = True
                    result["target"] = target_name
                    break
        
        return result

    async def _send_alert(
        self,
        order,
        current_price: float,
        profit_percentage: float,
        alert_type: str
    ):
        """发送钉钉提醒"""
        from app.core import robot
        
        emoji = "🟢" if profit_percentage > 0 else "🔴"
        
        msg = f"""{emoji} **{alert_type}**

📍 订单号: #{order.id}
💹 交易对: {order.symbol}
📊 方向: {order.recommendation}

💰 入场价: ${order.entry_price}
📈 当前价: ${current_price}
💵 盈亏: {profit_percentage:+.2f}%

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        await robot.send_msg(msg)
        logger.info(f"订单 {order.id} {alert_type}: 盈亏 {profit_percentage:+.2f}%")

    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
            })
        
        return {
            "is_running": self._is_running,
            "jobs": jobs
        }


# 全局实例
profit_tracker = ProfitTracker()
