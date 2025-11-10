# exchanges/binance/indicators.py
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

class TechnicalIndicators:
    """技术指标计算器"""

    # 定义支持的技术指标
    SUPPORTED_INDICATORS = {
        "macd": {
            "name": "MACD",
            "description": "异同移动平均线",
            "parameters": {
                "fast_period": {"default": 12, "type": "int", "description": "快速EMA周期"},
                "slow_period": {"default": 26, "type": "int", "description": "慢速EMA周期"},
                "signal_period": {"default": 9, "type": "int", "description": "信号线周期"}
            },
            "outputs": ["macd", "macd_signal", "macd_histogram"]
        },
        "rsi": {
            "name": "RSI",
            "description": "相对强弱指数",
            "parameters": {
                "period": {"default": 14, "type": "int", "description": "计算周期"}
            },
            "outputs": ["rsi"]
        },
        "bollinger_bands": {
            "name": "Bollinger Bands",
            "description": "布林带",
            "parameters": {
                "period": {"default": 20, "type": "int", "description": "计算周期"},
                "num_std": {"default": 2, "type": "int", "description": "标准差倍数"}
            },
            "outputs": ["bb_upper", "bb_middle", "bb_lower"]
        },
        "ma": {
            "name": "Moving Average",
            "description": "移动平均线",
            "parameters": {
                "period": {"default": 30, "type": "int", "description": "计算周期"}
            },
            "outputs": ["ma_30"]
        },
        "ema": {
            "name": "Exponential Moving Average",
            "description": "指数移动平均线",
            "parameters": {
                "period": {"default": 12, "type": "int", "description": "计算周期"}
            },
            "outputs": ["ema_12"]
        },
        "stochastic": {
            "name": "Stochastic Oscillator",
            "description": "随机指标",
            "parameters": {
                "k_period": {"default": 14, "type": "int", "description": "K值周期"},
                "d_period": {"default": 3, "type": "int", "description": "D值周期"}
            },
            "outputs": ["stoch_k", "stoch_d"]
        }
    }

    @staticmethod
    def get_supported_indicators() -> Dict[str, Any]:
        """
        获取所有支持的技术指标信息

        Returns:
            包含所有技术指标信息的字典
        """
        return TechnicalIndicators.SUPPORTED_INDICATORS

    @staticmethod
    def calculate_macd(klines: List[Dict[str, Any]],
                      fast_period: int = 12,
                      slow_period: int = 26,
                      signal_period: int = 9) -> List[Dict[str, Any]]:
        """
        计算MACD指标

        Args:
            klines: K线数据列表
            fast_period: 快速EMA周期
            slow_period: 慢速EMA周期
            signal_period: 信号线周期

        Returns:
            包含MACD指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)

        # 计算快速和慢速EMA
        ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()

        # 计算MACD线
        macd_line = ema_fast - ema_slow

        # 计算信号线
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # 计算柱状图
        histogram = macd_line - signal_line

        # 添加到原始数据
        df['macd'] = macd_line
        df['macd_signal'] = signal_line
        df['macd_histogram'] = histogram

        return df.to_dict('records')

    @staticmethod
    def calculate_rsi(klines: List[Dict[str, Any]], period: int = 14) -> List[Dict[str, Any]]:
        """
        计算RSI指标

        Args:
            klines: K线数据列表
            period: RSI周期

        Returns:
            包含RSI指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)

        # 计算价格变化
        delta = df['close'].diff()

        # 分离上涨和下跌
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        # 计算RS
        rs = gain / loss

        # 计算RSI
        rsi = 100 - (100 / (1 + rs))

        df['rsi'] = rsi

        return df.to_dict('records')

    @staticmethod
    def calculate_bollinger_bands(klines: List[Dict[str, Any]],
                                 period: int = 20,
                                 num_std: int = 2) -> List[Dict[str, Any]]:
        """
        计算布林带指标

        Args:
            klines: K线数据列表
            period: 计算周期
            num_std: 标准差倍数

        Returns:
            包含布林带指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)

        # 计算中轨（移动平均线）
        middle_band = df['close'].rolling(window=period).mean()

        # 计算标准差
        std_dev = df['close'].rolling(window=period).std()

        # 计算上下轨
        upper_band = middle_band + (std_dev * num_std)
        lower_band = middle_band - (std_dev * num_std)

        df['bb_upper'] = upper_band
        df['bb_middle'] = middle_band
        df['bb_lower'] = lower_band

        return df.to_dict('records')

    @staticmethod
    def calculate_ma(klines: List[Dict[str, Any]], period: int = 30) -> List[Dict[str, Any]]:
        """
        计算简单移动平均线

        Args:
            klines: K线数据列表
            period: 移动平均周期

        Returns:
            包含移动平均线的K线数据
        """
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)

        # 计算移动平均线
        ma = df['close'].rolling(window=period).mean()

        df[f'ma_{period}'] = ma

        return df.to_dict('records')

    @staticmethod
    def calculate_ema(klines: List[Dict[str, Any]], period: int = 12) -> List[Dict[str, Any]]:
        """
        计算指数移动平均线

        Args:
            klines: K线数据列表
            period: EMA周期

        Returns:
            包含指数移动平均线的K线数据
        """
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)

        # 计算EMA
        ema = df['close'].ewm(span=period, adjust=False).mean()

        df[f'ema_{period}'] = ema

        return df.to_dict('records')

    @staticmethod
    def calculate_stochastic(klines: List[Dict[str, Any]],
                           k_period: int = 14,
                           d_period: int = 3) -> List[Dict[str, Any]]:
        """
        计算随机指标(KDJ)

        Args:
            klines: K线数据列表
            k_period: %K周期
            d_period: %D周期

        Returns:
            包含随机指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)

        # 计算%K
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        percent_k = 100 * ((df['close'] - low_min) / (high_max - low_min))

        # 计算%D
        percent_d = percent_k.rolling(window=d_period).mean()

        df['stoch_k'] = percent_k
        df['stoch_d'] = percent_d

        return df.to_dict('records')

    @staticmethod
    def calculate_all(klines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        计算所有常用技术指标

        Args:
            klines: K线数据列表

        Returns:
            包含所有技术指标的K线数据
        """
        # 依次计算各种指标
        result = TechnicalIndicators.calculate_macd(klines)
        result = TechnicalIndicators.calculate_rsi(result)
        result = TechnicalIndicators.calculate_bollinger_bands(result)
        result = TechnicalIndicators.calculate_ma(result, 30)
        result = TechnicalIndicators.calculate_ema(result, 12)
        result = TechnicalIndicators.calculate_stochastic(result)
        # 确保所有原始字符串字段仍为字符串类型
        for item in result:
            item['open'] = str(item['open'])
            item['high'] = str(item['high'])
            item['low'] = str(item['low'])
            item['close'] = str(item['close'])
            item['volume'] = str(item['volume'])
            # 处理技术指标中的 NaN 值
            for key in item:
                if isinstance(item[key], (float, np.floating)) and np.isnan(item[key]):
                    item[key] = None

        return result
