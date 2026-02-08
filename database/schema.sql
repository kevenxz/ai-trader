-- AI Trading Orders Database Schema
-- PostgreSQL

-- 交易订单表
CREATE TABLE IF NOT EXISTS ai_trading_orders (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,                -- 交易对，如BTCUSDT
    interval VARCHAR(10) NOT NULL,              -- K线周期，如1h, 4h, 1d
    ai_model VARCHAR(100),                      -- AI模型名称
    recommendation VARCHAR(10) NOT NULL,        -- 交易建议: BUY(买入)/SELL(卖出)/HOLD(观望)
    risk_level VARCHAR(10) NOT NULL,            -- 风险等级: LOW(低)/MEDIUM(中)/HIGH(高)
    trend_status VARCHAR(20),                   -- 趋势状态: 多头/空头/震荡
    momentum VARCHAR(20),                       -- 动量方向: bullish(看涨)/bearish(看跌)/neutral(中性)
    entry_price_min DECIMAL(20, 8),             -- 建议入场价格下限
    entry_price_max DECIMAL(20, 8),             -- 建议入场价格上限
    entry_price DECIMAL(20, 8),                 -- 实际入场价格(开单时的市场价格)
    stop_loss DECIMAL(20, 8),                   -- 止损价格
    stop_loss_percentage DECIMAL(10, 4),        -- 止损百分比
    target_t1 DECIMAL(20, 8),                   -- 第一目标价(T1)
    target_t2 DECIMAL(20, 8),                   -- 第二目标价(T2)
    target_t3 DECIMAL(20, 8),                   -- 第三目标价(T3)
    position_size_percentage DECIMAL(10, 2),    -- 建议仓位百分比
    leverage DECIMAL(5, 2) DEFAULT 1,           -- 杠杆倍数
    quantity DECIMAL(20, 8),                    -- 成交数量
    open_amount DECIMAL(20, 8),                 -- 开仓金额
    status VARCHAR(20) DEFAULT 'OPEN',          -- 订单状态: OPEN/STOP_LOSS/TAKE_PROFIT_T1/T2/T3/CLOSED
    analysis_summary TEXT,                      -- AI分析摘要
    indicator_alerts TEXT,                      -- 指标预警信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 更新时间
    closed_at TIMESTAMP,                        -- 平仓时间
    closed_price DECIMAL(20, 8),                -- 平仓价格
    final_profit_percentage DECIMAL(10, 4),     -- 最终盈亏百分比
    pnl_ratio DECIMAL(10, 4),                   -- 盈亏比 (盈利/亏损)
    is_win BOOLEAN,                             -- 是否胜利
    raw_analysis JSONB                          -- 完整AI分析结果JSON
);

-- 盈亏追踪表
CREATE TABLE IF NOT EXISTS order_profit_tracking (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES ai_trading_orders(id) ON DELETE CASCADE,
    current_price DECIMAL(20, 8) NOT NULL,      -- 追踪时的当前价格
    profit_percentage DECIMAL(10, 4) NOT NULL,  -- 当前盈亏百分比
    profit_amount DECIMAL(20, 8),               -- 当前盈亏金额
    floating_pnl DECIMAL(20, 8),                -- 当前浮动盈亏金额
    interval_pnl_ratio DECIMAL(10, 4),          -- 周期盈亏比
    tracking_interval VARCHAR(10) NOT NULL,     -- 追踪周期: 30m/1h/2h/4h/6h
    is_stop_loss_triggered BOOLEAN DEFAULT FALSE,   -- 是否触发止损
    is_take_profit_triggered BOOLEAN DEFAULT FALSE, -- 是否触发止盈
    triggered_target VARCHAR(10),               -- 触发的目标价: T1/T2/T3
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 更新时间
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 追踪记录时间
);

-- 实时追踪配置表
CREATE TABLE IF NOT EXISTS realtime_tracking_config (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES ai_trading_orders(id) ON DELETE CASCADE,
    is_enabled BOOLEAN DEFAULT true,
    tracking_interval VARCHAR(10) DEFAULT '1m',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON ai_trading_orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_status ON ai_trading_orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_risk_level ON ai_trading_orders(risk_level);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON ai_trading_orders(created_at);
CREATE INDEX IF NOT EXISTS idx_tracking_order_id ON order_profit_tracking(order_id);
CREATE INDEX IF NOT EXISTS idx_tracking_interval ON order_profit_tracking(tracking_interval);
CREATE INDEX IF NOT EXISTS idx_tracking_tracked_at ON order_profit_tracking(tracked_at);

-- 统计视图
CREATE OR REPLACE VIEW order_statistics AS
SELECT 
    symbol,
    COUNT(*) as total_orders,
    COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_orders,
    COUNT(CASE WHEN status = 'STOP_LOSS' THEN 1 END) as stop_loss_orders,
    COUNT(CASE WHEN status LIKE 'TAKE_PROFIT%' THEN 1 END) as take_profit_orders,
    AVG(CASE WHEN final_profit_percentage IS NOT NULL THEN final_profit_percentage END) as avg_profit,
    COUNT(CASE WHEN final_profit_percentage > 0 THEN 1 END)::FLOAT / 
        NULLIF(COUNT(CASE WHEN final_profit_percentage IS NOT NULL THEN 1 END), 0) * 100 as win_rate
FROM ai_trading_orders
GROUP BY symbol;

-- =============================================
-- 表注释
-- =============================================

COMMENT ON TABLE ai_trading_orders IS 'AI交易订单表 - 存储AI分析生成的交易订单';
COMMENT ON TABLE order_profit_tracking IS '订单盈亏追踪表 - 记录订单在不同时间点的盈亏情况';

-- =============================================
-- ai_trading_orders 字段注释
-- =============================================

COMMENT ON COLUMN ai_trading_orders.id IS '订单ID，主键自增';
COMMENT ON COLUMN ai_trading_orders.symbol IS '交易对，如BTCUSDT';
COMMENT ON COLUMN ai_trading_orders.interval IS 'K线周期，如1h, 4h, 1d';
COMMENT ON COLUMN ai_trading_orders.ai_model IS 'AI模型名称';
COMMENT ON COLUMN ai_trading_orders.recommendation IS '交易建议: BUY(买入)/SELL(卖出)/HOLD(持有)';
COMMENT ON COLUMN ai_trading_orders.risk_level IS '风险等级: LOW(低)/MEDIUM(中)/HIGH(高)';
COMMENT ON COLUMN ai_trading_orders.trend_status IS '趋势状态: 多头/空头/震荡';
COMMENT ON COLUMN ai_trading_orders.momentum IS '动量方向: bullish(看涨)/bearish(看跌)/neutral(中性)';
COMMENT ON COLUMN ai_trading_orders.entry_price_min IS '建议入场价格下限';
COMMENT ON COLUMN ai_trading_orders.entry_price_max IS '建议入场价格上限';
COMMENT ON COLUMN ai_trading_orders.entry_price IS '实际入场价格(开单时的市场价格)';
COMMENT ON COLUMN ai_trading_orders.stop_loss IS '止损价格';
COMMENT ON COLUMN ai_trading_orders.stop_loss_percentage IS '止损百分比';
COMMENT ON COLUMN ai_trading_orders.target_t1 IS '第一目标价(T1)';
COMMENT ON COLUMN ai_trading_orders.target_t2 IS '第二目标价(T2)';
COMMENT ON COLUMN ai_trading_orders.target_t3 IS '第三目标价(T3)';
COMMENT ON COLUMN ai_trading_orders.position_size_percentage IS '建议仓位百分比';
COMMENT ON COLUMN ai_trading_orders.status IS '订单状态: OPEN(持仓中)/STOP_LOSS(止损)/TAKE_PROFIT_T1/T2/T3(止盈)/CLOSED(已平仓)';
COMMENT ON COLUMN ai_trading_orders.analysis_summary IS 'AI分析摘要';
COMMENT ON COLUMN ai_trading_orders.indicator_alerts IS '指标预警信息';
COMMENT ON COLUMN ai_trading_orders.created_at IS '订单创建时间';
COMMENT ON COLUMN ai_trading_orders.updated_at IS '订单更新时间';
COMMENT ON COLUMN ai_trading_orders.closed_at IS '订单平仓时间';
COMMENT ON COLUMN ai_trading_orders.closed_price IS '平仓价格';
COMMENT ON COLUMN ai_trading_orders.final_profit_percentage IS '最终盈亏百分比';
COMMENT ON COLUMN ai_trading_orders.pnl_ratio IS '盈亏比 (盈利/亏损)';
COMMENT ON COLUMN ai_trading_orders.is_win IS '是否胜利: true(盈利)/false(亏损)';
COMMENT ON COLUMN ai_trading_orders.leverage IS '杠杆倍数';
COMMENT ON COLUMN ai_trading_orders.quantity IS '成交数量';
COMMENT ON COLUMN ai_trading_orders.open_amount IS '开仓金额';
COMMENT ON COLUMN ai_trading_orders.raw_analysis IS '完整AI分析结果JSON';

-- =============================================
-- order_profit_tracking 字段注释
-- =============================================

COMMENT ON COLUMN order_profit_tracking.id IS '追踪记录ID，主键自增';
COMMENT ON COLUMN order_profit_tracking.order_id IS '关联的订单ID';
COMMENT ON COLUMN order_profit_tracking.current_price IS '追踪时的当前价格';
COMMENT ON COLUMN order_profit_tracking.profit_percentage IS '当前盈亏百分比';
COMMENT ON COLUMN order_profit_tracking.profit_amount IS '当前盈亏金额';
COMMENT ON COLUMN order_profit_tracking.floating_pnl IS '当前浮动盈亏金额';
COMMENT ON COLUMN order_profit_tracking.interval_pnl_ratio IS '周期盈亏比';
COMMENT ON COLUMN order_profit_tracking.tracking_interval IS '追踪周期: 30m/1h/2h/4h/6h';
COMMENT ON COLUMN order_profit_tracking.is_stop_loss_triggered IS '是否触发止损';
COMMENT ON COLUMN order_profit_tracking.is_take_profit_triggered IS '是否触发止盈';
COMMENT ON COLUMN order_profit_tracking.triggered_target IS '触发的目标价: T1/T2/T3';
COMMENT ON COLUMN order_profit_tracking.created_at IS '创建时间';
COMMENT ON COLUMN order_profit_tracking.updated_at IS '更新时间';
COMMENT ON COLUMN order_profit_tracking.tracked_at IS '追踪记录时间';

-- =============================================
-- 视图注释
-- =============================================

COMMENT ON VIEW order_statistics IS '订单统计视图 - 按交易对汇总订单统计数据，包括胜率、平均盈亏等';

-- =============================================
-- 枚举值说明
-- =============================================
-- 订单状态 (status):
--   OPEN: 持仓中
--   STOP_LOSS: 止损平仓
--   TAKE_PROFIT_T1: T1止盈
--   TAKE_PROFIT_T2: T2止盈
--   TAKE_PROFIT_T3: T3止盈
--   CLOSED: 手动平仓

-- 风险等级 (risk_level):
--   LOW: 低风险
--   MEDIUM: 中等风险
--   HIGH: 高风险

-- 交易建议 (recommendation):
--   BUY: 买入做多
--   SELL: 卖出做空
--   HOLD: 观望

-- 追踪周期 (tracking_interval):
--   30m, 1h, 2h, 4h, 6h

-- =============================================
-- 测试数据
-- =============================================

-- 测试订单1: BTC多单，已止盈T1
INSERT INTO ai_trading_orders (
    symbol, interval, ai_model, recommendation, risk_level, trend_status, momentum,
    entry_price_min, entry_price_max, entry_price, stop_loss, stop_loss_percentage,
    target_t1, target_t2, target_t3, position_size_percentage, leverage, quantity, open_amount,
    status, analysis_summary, closed_at, closed_price, final_profit_percentage, pnl_ratio, is_win
) VALUES (
    'BTCUSDT', '4h', 'deepseek-v3', 'BUY', 'LOW', '多头', 'bullish',
    94000.00, 95000.00, 94500.00, 92000.00, 2.65,
    97000.00, 99000.00, 102000.00, 10.00, 5.00, 0.05, 4725.00,
    'TAKE_PROFIT_T1', 'BTC突破关键阻力位，趋势确认向上',
    CURRENT_TIMESTAMP, 97200.00, 2.86, 1.08, true
);

-- 测试订单2: ETH多单，持仓中
INSERT INTO ai_trading_orders (
    symbol, interval, ai_model, recommendation, risk_level, trend_status, momentum,
    entry_price_min, entry_price_max, entry_price, stop_loss, stop_loss_percentage,
    target_t1, target_t2, target_t3, position_size_percentage, leverage, quantity, open_amount,
    status, analysis_summary
) VALUES (
    'ETHUSDT', '1h', 'deepseek-v3', 'BUY', 'MEDIUM', '多头', 'bullish',
    3300.00, 3350.00, 3320.00, 3200.00, 3.61,
    3500.00, 3650.00, 3800.00, 8.00, 3.00, 1.5, 4980.00,
    'OPEN', 'ETH测试多头动力，建议小仓位试探'
);

-- 测试订单3: SOL空单，已止损
INSERT INTO ai_trading_orders (
    symbol, interval, ai_model, recommendation, risk_level, trend_status, momentum,
    entry_price_min, entry_price_max, entry_price, stop_loss, stop_loss_percentage,
    target_t1, target_t2, target_t3, position_size_percentage, leverage, quantity, open_amount,
    status, analysis_summary, closed_at, closed_price, final_profit_percentage, pnl_ratio, is_win
) VALUES (
    'SOLUSDT', '15m', 'gpt-4o', 'SELL', 'MEDIUM', '空头', 'bearish',
    240.00, 245.00, 242.50, 255.00, 5.15,
    230.00, 220.00, 210.00, 5.00, 10.00, 20.0, 4850.00,
    'STOP_LOSS', 'SOL短期超卖反弹，谨慎做空',
    CURRENT_TIMESTAMP, 256.00, -5.57, -1.08, false
);

-- 测试追踪数据
INSERT INTO order_profit_tracking (order_id, current_price, profit_percentage, profit_amount, floating_pnl, interval_pnl_ratio, tracking_interval)
VALUES 
    (1, 95200.00, 0.74, 35.00, 35.00, 0.28, '30m'),
    (1, 96100.00, 1.69, 80.00, 80.00, 0.64, '1h'),
    (1, 97000.00, 2.65, 125.00, 125.00, 1.00, '2h'),
    (2, 3380.00, 1.81, 90.00, 90.00, 0.50, '30m'),
    (2, 3420.00, 3.01, 150.00, 150.00, 0.83, '1h');
