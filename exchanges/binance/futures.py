# exchanges/binance/futures.py
import requests
import time
from typing import List, Dict, Any, Optional
from enum import Enum
import pandas as pd
import numpy as np
from urllib.parse import urlencode

class FuturesSymbol(Enum):
    """合约交易对枚举"""
    BTCUSDT = "BTCUSDT"
    ETHUSDT = "ETHUSDT"
    BNBUSDT = "BNBUSDT"
    XRPUSDT = "XRPUSDT"
    DOGEUSDT = "DOGEUSDT"
    SOLUSDT = "SOLUSDT"
    ADAUSDT = "ADAUSDT"
    DOTUSDT = "DOTUSDT"
    MATICUSDT = "MATICUSDT"
    LTCUSDT = "LTCUSDT"
    # 可根据需要添加更多交易对

class BinanceFuturesClient:
    """币安合约交易客户端（直接HTTP请求）"""

    BASE_URL = "https://fapi.binance.com"

    # K线间隔映射
    INTERVAL_MAP = {
        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "8h": "8h",
        "12h": "12h",
        "1d": "1d",
        "3d": "3d",
        "1w": "1w",
        "1M": "1M"
    }

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = ""
        self.api_secret = ""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get_klines(
        self,
        symbol: FuturesSymbol,
        interval: str = "1h",
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取合约K线数据（直接HTTP请求）

        Args:
            symbol: 交易对枚举值
            interval: K线间隔 (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            limit: 返回的K线数量，最大1500，默认500
            start_time: 开始时间戳 (毫秒)
            end_time: 结束时间戳 (毫秒)

        Returns:
            K线数据列表
        """
        # 验证interval参数
        if interval not in self.INTERVAL_MAP:
            raise ValueError(f"Unsupported interval: {interval}")

        # 构建请求参数
        params = {
            "symbol": symbol.value,
            "interval": self.INTERVAL_MAP[interval],
            "limit": limit
        }

        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        try:
            # 发送HTTP GET请求获取K线数据
            url = f"{self.BASE_URL}/fapi/v1/klines"
            headers = {
                "X-MBX-APIKEY": self.api_key
            }

            response = requests.get(url, params=params, headers=headers, timeout=30)

            if response.status_code == 200:
                return self._format_klines(response.json())
            else:
                raise Exception(f"Binance API Error: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network Error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error fetching klines: {str(e)}")

    def _format_klines(self, klines_data: List[List]) -> List[Dict[str, Any]]:
        """
        格式化K线数据

        Args:
            klines_data: 原始K线数据

        Returns:
            格式化后的K线数据
        """
        formatted_klines = []
        for kline in klines_data:
            formatted_klines.append({
                "open_time": str(kline[0]),
                "open": str(kline[1]),
                "high": str(kline[2]),
                "low": str(kline[3]),
                "close": str(kline[4]),
                "volume": str(kline[5]),
                "close_time": str(kline[6]),
                "quote_asset_volume": str(kline[7]),
                "number_of_trades": str(kline[8]),
                "taker_buy_base_asset_volume": str(kline[9]),
                "taker_buy_quote_asset_volume": str(kline[10]),
                "ignore": kline[11]
            })
        return formatted_klines

    # 在 exchanges/binance/futures.py 文件中的 BinanceFuturesClient 类中添加新方法
    def get_klines_with_indicators(
            self,
            symbol: FuturesSymbol,
            interval: str = "1h",
            limit: int = 500,
            start_time: Optional[int] = None,
            end_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取合约K线数据并计算所有技术指标

        Args:
            symbol: 交易对枚举值
            interval: K线间隔 (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            limit: 返回的K线数量，最大1500，默认500
            start_time: 开始时间戳 (毫秒)
            end_time: 结束时间戳 (毫秒)

        Returns:
            包含所有技术指标的K线数据列表
        """
        # 获取原始K线数据
        klines = self.get_klines(symbol, interval, limit, start_time, end_time)

        # 计算所有技术指标
        from .indicators import TechnicalIndicators
        klines_with_indicators = TechnicalIndicators.calculate_all(klines)

        return klines_with_indicators
