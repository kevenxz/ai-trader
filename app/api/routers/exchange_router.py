# app/api/routers/exchange_router.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio
import sys
import os

# 添加exchanges模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from exchanges.binance.futures import BinanceFuturesClient, FuturesSymbol
from exchanges.binance.indicators import TechnicalIndicators
router = APIRouter(prefix="/api/exchange", tags=["exchange"])

# 更新 app/api/routers/exchange_router.py 中的 KlineResponse 模型
class KlineResponse(BaseModel):
    open_time: str
    open: str
    high: str
    low: str
    close: str
    volume: str
    close_time: str
    quote_asset_volume: str
    number_of_trades: str
    taker_buy_base_asset_volume: str
    taker_buy_quote_asset_volume: str
    # MACD指标
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    # RSI指标
    rsi: Optional[float] = None
    # 布林带指标
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    # 移动平均线
    ma_30: Optional[float] = None
    # 指数移动平均线
    ema_12: Optional[float] = None
    # 随机指标
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None


class KlinesResponse(BaseModel):
    symbol: str
    interval: str
    klines: List[KlineResponse]



# 定义可用的交易对列表
AVAILABLE_SYMBOLS = [symbol.value for symbol in FuturesSymbol]

@router.get("/binance/futures/klines", response_model=KlinesResponse)
async def get_binance_futures_klines(
    symbol: FuturesSymbol = Query(..., description="交易对", example="BTCUSDT"),
    interval: str = Query(
        "1h",
        description="K线间隔",
        example="1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M"
    ),
    limit: int = Query(500, ge=1, le=1500, description="返回的K线数量"),
    start_time: Optional[int] = Query(None, description="开始时间戳(毫秒)"),
    end_time: Optional[int] = Query(None, description="结束时间戳(毫秒)")
):
    """
    获取币安合约K线数据
    """
    try:
        # 验证symbol是否支持
        if symbol.value not in AVAILABLE_SYMBOLS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported symbol: {symbol.value}. Available symbols: {AVAILABLE_SYMBOLS}"
            )

        # 使用同步客户端（直接HTTP请求）
        client = BinanceFuturesClient()
        klines = client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )

        return KlinesResponse(
            symbol=symbol.value,
            interval=interval,
            klines=klines
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/binance/futures/symbols")
async def get_available_symbols():
    """
    获取支持的交易对列表
    """
    return {
        "symbols": AVAILABLE_SYMBOLS,
        "count": len(AVAILABLE_SYMBOLS)
    }

@router.get("/binance/futures/indicators")
async def get_supported_indicators():
    """
    获取所有支持的技术指标信息
    """
    try:
        indicators = TechnicalIndicators.get_supported_indicators()
        return {
            "indicators": indicators,
            "count": len(indicators)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 在 app/api/routers/exchange_router.py 文件中添加新的API端点
@router.get("/binance/futures/indicators/all", response_model=KlinesResponse)
async def get_binance_futures_indicators(
    symbol: FuturesSymbol = Query(..., description="交易对", example="BTCUSDT"),
    interval: str = Query(
        "1h",
        description="K线间隔",
        example="1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M"
    ),
    limit: int = Query(500, ge=1, le=1500, description="返回的K线数量"),
    start_time: Optional[int] = Query(None, description="开始时间戳(毫秒)"),
    end_time: Optional[int] = Query(None, description="结束时间戳(毫秒)")
):
    """
    获取币安合约K线数据及所有技术指标
    """
    try:
        # 验证symbol是否支持
        if symbol.value not in AVAILABLE_SYMBOLS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported symbol: {symbol.value}. Available symbols: {AVAILABLE_SYMBOLS}"
            )

        # 使用同步客户端获取带技术指标的K线数据
        client = BinanceFuturesClient()
        klines = client.get_klines_with_indicators(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )

        return KlinesResponse(
            symbol=symbol.value,
            interval=interval,
            klines=klines
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
