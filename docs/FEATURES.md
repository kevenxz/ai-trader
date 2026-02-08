# AlphaPulse 订单管理模块 - 功能文档

## 1. 系统概述

AlphaPulse 是一个AI驱动的加密货币交易平台，提供订单管理、盈亏追踪和数据分析功能。

### 系统架构图

```mermaid
graph TB
    subgraph Frontend["前端 (React)"]
        TradingOrders["订单管理页面"]
        Dashboard["仪表盘"]
        Scheduler["任务调度器"]
    end

    subgraph Backend["后端 (FastAPI)"]
        OrderRouter["订单路由"]
        RealtimeRouter["实时追踪路由"]
        SchedulerRouter["调度器路由"]
        ProfitTracker["盈亏追踪器"]
    end

    subgraph External["外部服务"]
        Binance["币安合约API"]
        AI["AI分析服务"]
    end

    subgraph Database["数据库 (PostgreSQL)"]
        Orders["ai_trading_orders"]
        Tracking["order_profit_tracking"]
    end

    Frontend --> Backend
    Backend --> External
    Backend --> Database
```

---

## 2. 核心功能模块

### 2.1 订单管理流程

```mermaid
flowchart LR
    A[用户创建订单] --> B{验证参数}
    B -->|通过| C[保存到数据库]
    B -->|失败| D[返回错误]
    C --> E[订单状态: OPEN]
    E --> F{监控价格}
    F -->|触发止损| G[状态: STOP_LOSS]
    F -->|触发止盈| H[状态: TAKE_PROFIT]
    F -->|手动平仓| I[状态: CLOSED]
    G --> J[记录最终盈亏]
    H --> J
    I --> J
```

**功能说明：**
| 步骤 | 功能 | 说明 |
|------|------|------|
| 创建订单 | 用户输入交易参数 | 支持交易对、方向、价格、止损止盈 |
| 参数验证 | 检查必填字段 | entry_price, stop_loss 为必填 |
| 保存订单 | 写入数据库 | 自动生成订单ID和时间戳 |
| 价格监控 | 定时获取当前价 | 调用币安API获取实时价格 |
| 状态更新 | 触发条件判断 | 自动更新订单状态 |

---

### 2.2 盈亏计算流程

```mermaid
flowchart TD
    A[调用计算盈亏接口] --> B[获取订单信息]
    B --> C{订单状态是否OPEN?}
    C -->|否| D[返回错误: 订单已关闭]
    C -->|是| E[调用币安API获取当前价格]
    E --> F{价格获取成功?}
    F -->|否| G[返回错误: 无法获取价格]
    F -->|是| H[计算盈亏百分比]
    H --> I{方向判断}
    I -->|BUY| J["盈亏 = (当前价-入场价)/入场价 × 100"]
    I -->|SELL| K["盈亏 = (入场价-当前价)/入场价 × 100"]
    J --> L[检查止损/止盈触发]
    K --> L
    L --> M[保存追踪记录]
    M --> N[返回计算结果]
```

**计算公式：**
```
# 做多 (BUY)
profit_percentage = ((current_price - entry_price) / entry_price) * 100

# 做空 (SELL)  
profit_percentage = ((entry_price - current_price) / entry_price) * 100

# 杠杆收益
leveraged_profit = profit_percentage * leverage
```

---

### 2.3 实时追踪机制

```mermaid
sequenceDiagram
    participant User as 用户
    participant API as API服务
    participant Tracker as 追踪器
    participant Binance as 币安API
    participant DB as 数据库

    User->>API: 启用实时追踪
    API->>DB: 保存配置
    loop 每个追踪周期
        Tracker->>DB: 获取开放订单
        Tracker->>Binance: 批量获取价格
        Binance-->>Tracker: 返回价格数据
        Tracker->>Tracker: 计算盈亏
        Tracker->>DB: 保存追踪记录
    end
    User->>API: 禁用实时追踪
    API->>DB: 更新配置
```

**追踪周期选项：**
| 周期 | 说明 | 适用场景 |
|------|------|------|
| 30m | 每30分钟追踪 | 高频交易 |
| 1h | 每1小时追踪 | 日内交易 |
| 2h | 每2小时追踪 | 短线交易 |
| 4h | 每4小时追踪 | 波段交易 |
| 6h | 每6小时追踪 | 中长线交易 |

---

### 2.4 仪表盘数据聚合

```mermaid
graph LR
    subgraph 数据源
        A[订单表]
        B[追踪记录表]
    end

    subgraph 聚合计算
        C[总盈亏统计]
        D[胜率计算]
        E[币种分组]
        F[每日汇总]
        G[周期分析]
    end

    subgraph 输出
        H[仪表盘API]
        I[每日盈亏API]
        J[周期统计API]
    end

    A --> C
    A --> D
    A --> E
    A --> F
    B --> G

    C --> H
    D --> H
    E --> H
    F --> I
    G --> J
```

---

## 3. 数据模型

### 3.1 订单模型 (AITradingOrder)

```mermaid
erDiagram
    ai_trading_orders {
        int id PK "订单ID"
        string symbol "交易对"
        string interval "K线周期"
        string recommendation "交易方向 BUY/SELL"
        string risk_level "风险等级 LOW/MEDIUM/HIGH"
        float entry_price "入场价格"
        float stop_loss "止损价格"
        float target_t1 "目标价1"
        float target_t2 "目标价2"
        float target_t3 "目标价3"
        float leverage "杠杆倍数"
        float quantity "交易数量"
        float open_amount "开仓金额"
        string status "订单状态"
        datetime created_at "创建时间"
        datetime closed_at "平仓时间"
        float final_profit_percentage "最终盈亏"
        boolean is_win "是否盈利"
    }

    order_profit_tracking {
        int id PK "记录ID"
        int order_id FK "关联订单"
        float current_price "当前价格"
        float profit_percentage "盈亏百分比"
        string tracking_interval "追踪周期"
        boolean is_stop_loss_triggered "止损触发"
        boolean is_take_profit_triggered "止盈触发"
        datetime tracked_at "记录时间"
    }

    ai_trading_orders ||--o{ order_profit_tracking : "has"
```

---

## 4. 状态机

### 订单状态流转

```mermaid
stateDiagram-v2
    [*] --> OPEN: 创建订单
    OPEN --> CLOSED: 手动平仓
    OPEN --> STOP_LOSS: 触发止损价
    OPEN --> TAKE_PROFIT_T1: 触发目标价1
    OPEN --> TAKE_PROFIT_T2: 触发目标价2
    OPEN --> TAKE_PROFIT_T3: 触发目标价3
    
    CLOSED --> [*]
    STOP_LOSS --> [*]
    TAKE_PROFIT_T1 --> [*]
    TAKE_PROFIT_T2 --> [*]
    TAKE_PROFIT_T3 --> [*]
```

---

## 5. 定时任务

```mermaid
gantt
    title 定时任务执行时间线
    dateFormat HH:mm
    section AI分析
    BTCUSDT 15分钟分析    :a1, 00:00, 15m
    ETHUSDT 15分钟分析    :a2, 00:15, 15m
    section 盈亏追踪
    30分钟追踪任务        :b1, 00:00, 30m
    1小时追踪任务         :b2, 00:00, 60m
```
