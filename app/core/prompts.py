# app/core/prompts.py
"""技术指标字段提示词配置文件 - LangChain集成版本"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


class TargetLevel(BaseModel):
    """目标价位模型"""
    level: str = Field(description="目标级别，如T1, T2, T3")
    price: float = Field(description="目标价格")
    percentage: float = Field(description="涨跌幅百分比")
    reason: str = Field(description="对应阻力/指标信号说明")


class TraderOutputModel(BaseModel):
    """交易决策输出模型 - 用于LangChain结构化输出"""
    recommendation: Literal["BUY", "SELL", "HOLD"] = Field(
        description="交易建议：BUY（买入）、SELL（卖出）、HOLD（持有）"
    )
    trend_status: str = Field(
        description="趋势状态：多头/空头/震荡（基于MA/云图/ADX）"
    )
    momentum: Literal["bullish", "bearish", "neutral"] = Field(
        description="动量方向（MACD/RSI/Stoch共识）"
    )
    volume_price_confirmation: Literal["确认", "背离", "中性"] = Field(
        description="量价确认状态（OBV/MFI/VWAP分析）"
    )
    entry_price_min: float = Field(description="入场区间最低价")
    entry_price_max: float = Field(description="入场区间最高价")
    stop_loss: float = Field(description="止损位价格")
    stop_loss_percentage: float = Field(description="止损百分比（基于ATR）")
    targets: List[TargetLevel] = Field(description="目标价位列表")
    position_size_percentage: float = Field(
        description="仓位建议，占总资金百分比（基于波动率调整）"
    )
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="风险等级"
    )
    indicator_alerts: Optional[str] = Field(
        default=None,
        description="指标异常提示（关键指标背离或矛盾信号说明）"
    )
    analysis_summary: Optional[str] = Field(
        default=None,
        description="分析总结"
    )


# 创建输出解析器实例
trader_output_parser = PydanticOutputParser(pydantic_object=TraderOutputModel)

# 获取输出格式说明
TRADER_OUTPUT_FORMAT = trader_output_parser.get_format_instructions()

# K线基础字段提示词
KLINE_FIELD_PROMPTS = {
    "open_time": "开盘时间",
    "open": "开盘价",
    "high": "最高价",
    "low": "最低价",
    "close": "收盘价(当前K线未结束)",
    "volume": "成交量",
    "close_time": "收盘时间",
    "quote_asset_volume": "成交额",
    "number_of_trades": "成交笔数",
    "taker_buy_base_asset_volume": "主动买入成交量",
    "taker_buy_quote_asset_volume": "主动买入成交额"
}
AI_TRADER_PROMPTS = """---

**角色定位**  
你是一名资深的量化加密货币分析师，精通多因子模型与市场微观结构。你擅长运用综合技术指标体系进行系统性分析，并以数据驱动的方式输出交易决策,
你可以从专业机构的角度，实现高级的量化策略，你开仓的是合约并且是一百倍的杠杆，你需要分析对应的趋势，你专业在一小时，两小时，四小时级别，并且可以通过k线分析出市场的行情趋势，震旦、波段等行情
，下面是一些技术指标和对应的周期，接下来的数据对话，我将给你120个k线数据。

**核心技术指标体系**  
**基础k线数据**
- 收盘价
- 开盘价
- 最高价
- 最低价
- 成交量
- 成交额
- 成交笔数
- 成交时间

**趋势类指标**  
- 移动平均系：MA30、EMA12  
- 云图系：Ichimoku（转换线/基准线/先行带/迟行带）  
- 趋势强度：ADX14（含±DI方向指标）  
- 均势指标：Parabolic SAR
- 斐波那契回撤

**动量类指标**  
- MACD系（12/26/9周期）  
- RSI14  
- 随机摆动系（%K14/%D3）  
- 威廉%R14  
- 动量指标（10周期）  
- CCI20

**波动率与风控指标**  
- 布林带（20周期，上下轨及中轴）  
- ATR14（真实波动幅度）  
- 标准差（20周期）  
- 波动率（20周期）

**量价确认指标**  
- VWAP（成交量加权均价）  
- MFI14（资金流量指数）  
- OBV（能量潮）  
- ADL（积累/派发线）  
- CMF20（佳庆资金流）

**分析框架**  
1. **趋势判定**  
   - 多空排列：MA30/EMA12/Ichimoku云层相对位置  
   - 趋势强度：ADX14 > 25视为有效趋势，±DI交叉确认方向  

2. **动量验证**  
   - MACD：零轴上下/金叉死叉/背离信号  
   - RSI/Stoch/Williams：超买超卖区域及背离  
   - 多动量指标共振分析  

3. **波动结构**  
   - 布林带宽度与价格相对位置  
   - ATR确定止损幅度与仓位规模  
   - 标准差评估价格离散程度  

4. **量价健康度**  
   - VWAP突破有效性确认  
   - MFI/OBV/ADL与价格走势的背离检测  
   - CMF资金流向验证  

5. **云图综合研判**  
   - 价格与云层相对关系  
   - 转换线/基准线金叉死叉  
   - 迟行线位置确认  
**下面的json是指定k线输入格式，接下你只需要分析我给你的下面格式的json数组**
    symbol: str # 交易对
    interval: str # 周期
    open_time: str # 开盘时间:
    open: str # 开盘价
    high: str # 最高价
    low: str # 最低价
    close: str # 收盘价(当前K线未
    volume: str # 成交量
    close_time: str # 收盘时间
    quote_asset_volume: str # 成交额
    number_of_trades: str # 成交笔数
    taker_buy_base_asset_volume: str # 主动买入成交量
    taker_buy_quote_asset_volume: str # 主动买入成交额
    # MACD指标 (已包含周期)
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    # RSI指标 (添加周期)
    rsi_14: Optional[float] = None
    # 布林带指标 (已包含周期)
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    # 移动平均线 (已包含周期)
    ma_30: Optional[float] = None
    ma_10: Optional[float] = None
    # 指数移动平均线 (已包含周期)
    ema_12: Optional[float] = None
    # 指数移动平均线 (已包含周期)
    ema_26: Optional[float] = None
    # 随机指标
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    # ATR指标 (添加周期)
    atr_14: Optional[float] = None
    # CCI指标 (添加周期)
    cci_20: Optional[float] = None
    # 威廉姆斯%R指标 (添加周期)
    williams_r_14: Optional[float] = None
    # 动量指标 (添加周期)
    momentum_10: Optional[float] = None
    # 顺势指标
    tenkan_sen: Optional[float] = None
    kijun_sen: Optional[float] = None
    senkou_span_a: Optional[float] = None
    senkou_span_b: Optional[float] = None
    chikou_span: Optional[float] = None
    # 抛物线SAR指标
    sar: Optional[float] = None
    # VWAP指标
    vwap: Optional[float] = None
    # MFI指标 (添加周期)
    mfi_14: Optional[float] = None
    # OBV指标
    obv: Optional[float] = None
    # ADL指标
    adl: Optional[float] = None
    # CMF指标 (添加周期)
    cmf_20: Optional[float] = None
    # 标准差指标 (添加周期)
    std_20: Optional[float] = None
    # ADX指标 (添加周期)
    adx_14: Optional[float] = None
    di_plus: Optional[float] = None
    di_minus: Optional[float] = None
    # 波动率指标
    volatility_20: Optional[float] = None  # 20周期波动率

**重要：你必须严格按照下面的JSON格式输出你的分析结果，不要输出任何其他内容，只输出JSON对象**

```json
{{
  "recommendation": "BUY|SELL|HOLD",
  "trend_status": "多头|空头|震荡",
  "momentum": "bullish|bearish|neutral",
  "volume_price_confirmation": "确认|背离|中性",
  "entry_price_min": 价格数字,
  "entry_price_max": 价格数字,
  "stop_loss": 止损价格数字,
  "stop_loss_percentage": 止损百分比数字,
  "targets": [
    {{"level": "T1", "price": 目标价格, "percentage": 涨幅百分比, "reason": "对应阻力/指标信号"}},
    {{"level": "T2", "price": 目标价格, "percentage": 涨幅百分比, "reason": "强阻力/斐波那契"}},
    {{"level": "T3", "price": 目标价格, "percentage": 涨幅百分比, "reason": "趋势目标"}}
  ],
  "position_size_percentage": 仓位百分比数字,
  "risk_level": "LOW|MEDIUM|HIGH",
  "indicator_alerts": "如有关键指标背离或矛盾信号在此说明，否则为null",
  "analysis_summary": "简要分析总结"
}}
```

注意事项：
1. 所有数字字段直接使用数字，不要使用字符串
2. recommendation只能是 "BUY"、"SELL" 或 "HOLD" 之一
3. momentum只能是 "bullish"、"bearish" 或 "neutral" 之一
4. risk_level只能是 "LOW"、"MEDIUM" 或 "HIGH" 之一
5. 不要在JSON外面添加任何文字说明
6. 确保JSON格式正确可解析"""


# 技术指标字段提示词
INDICATOR_FIELD_PROMPTS = {
    # MACD指标
    "macd": "MACD线 - 快速EMA与慢速EMA的差值",
    "macd_signal": "MACD信号线 - MACD的移动平均线",
    "macd_histogram": "MACD柱状图 - MACD与信号线的差值",

    # RSI指标
    "rsi_14": "相对强弱指数(RSI) - 衡量价格动量和超买/超卖条件，14周期",

    # 布林带指标
    "bb_upper": "布林带上轨 - 中轨加上2倍标准差",
    "bb_middle": "布林带中轨 - 20周期简单移动平均线",
    "bb_lower": "布林带下轨 - 中轨减去2倍标准差",

    # 移动平均线
    "ma_30": "30周期简单移动平均线 - 平滑价格数据，识别趋势方向",
    "ema_12": "12周期指数移动平均线 - 对近期价格更敏感的移动平均线",

    # 随机指标
    "stoch_k": "随机指标K值 - 当前收盘价在近期价格区间中的位置",
    "stoch_d": "随机指标D值 - K值的3周期移动平均",

    # ATR指标
    "atr_14": "14周期平均真实范围 - 衡量市场波动性",

    # CCI指标
    "cci_20": "20周期商品通道指数 - 识别超买/超卖条件和趋势强度",

    # 威廉姆斯%R指标
    "williams_r_14": "14周期威廉姆斯%R - 衡量超买/超卖状况的动量指标",

    # 动量指标
    "momentum_10": "10周期动量指标 - 衡量价格变化速度",

    # 顺势指标(Ichimoku Cloud)
    "tenkan_sen": "转换线(9周期) - 用于衡量短期趋势动向",
    "kijun_sen": "基准线(26周期) - 用于衡量中期趋势动向",
    "senkou_span_a": "先行跨度A - 转换线和基准线的平均值向前推移",
    "senkou_span_b": "先行跨度B(52周期) - 用于衡量长期趋势动向",
    "chikou_span": "滞后跨度 - 当前收盘价向后推移26周期",

    # 抛物线SAR指标
    "sar": "抛物线转向指标 - 提供止损和反转信号",

    # VWAP指标
    "vwap": "成交量加权平均价 - 基于成交量加权的平均价格",

    # MFI指标
    "mfi_14": "14周期资金流量指数 - 结合价格和成交量的RSI变体",

    # OBV指标
    "obv": "平衡成交量 - 基于成交量的累积指标",

    # ADL指标
    "adl": "累积/派发线 - 基于价格和成交量的资金流指标",

    # CMF指标
    "cmf_20": "20周期蔡金资金流量 - 衡量资金流入流出强度",

    # 标准差指标
    "std_20": "20周期标准差 - 衡量价格波动性",

    # ADX指标
    "adx_14": "14周期平均方向指数 - 衡量趋势强度",
    "di_plus": "正向方向指标 - 衡量上升趋势强度",
    "di_minus": "负向方向指标 - 衡量下降趋势强度",

    # 波动率指标
    "volatility_20": "20周期波动率 - 基于收益率的标准差计算"
}

# 所有字段提示词
ALL_FIELD_PROMPTS = {**KLINE_FIELD_PROMPTS, **INDICATOR_FIELD_PROMPTS}

def get_field_prompt(field_name: str) -> str:
    """
    获取字段的提示文本

    Args:
        field_name: 字段名称

    Returns:
        字段的提示文本
    """
    return ALL_FIELD_PROMPTS.get(field_name, field_name)

def get_all_prompts() -> dict:
    """
    获取所有字段的提示词

    Returns:
        包含所有字段提示词的字典
    """
    return ALL_FIELD_PROMPTS.copy()
