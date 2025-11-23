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
        },
        "atr": {
            "name": "Average True Range",
            "description": "平均真实范围",
            "parameters": {
                "period": {"default": 14, "type": "int", "description": "计算周期"}
            },
            "outputs": ["atr"]
        },
        "cci": {
            "name": "Commodity Channel Index",
            "description": "商品通道指数",
            "parameters": {
                "period": {"default": 20, "type": "int", "description": "计算周期"}
            },
            "outputs": ["cci"]
        },
        "williams_r": {
            "name": "Williams %R",
            "description": "威廉姆斯%R",
            "parameters": {
                "period": {"default": 14, "type": "int", "description": "计算周期"}
            },
            "outputs": ["williams_r"]
        },
        "momentum": {
            "name": "Momentum",
            "description": "动量指标",
            "parameters": {
                "period": {"default": 10, "type": "int", "description": "计算周期"}
            },
            "outputs": ["momentum"]
        },
        "ichimoku": {
            "name": "Ichimoku Cloud",
            "description": "顺势指标",
            "parameters": {
                "tenkan_sen_period": {"default": 9, "type": "int", "description": "转换线周期"},
                "kijun_sen_period": {"default": 26, "type": "int", "description": "基准线周期"},
                "senkou_span_b_period": {"default": 52, "type": "int", "description": "先行跨度B周期"}
            },
            "outputs": ["tenkan_sen", "kijun_sen", "senkou_span_a", "senkou_span_b", "chikou_span"]
        },
        "parabolic_sar": {
            "name": "Parabolic SAR",
            "description": "抛物线转向指标",
            "parameters": {
                "acceleration": {"default": 0.02, "type": "float", "description": "步长"},
                "maximum": {"default": 0.2, "type": "float", "description": "最大步长"}
            },
            "outputs": ["sar"]
        },
        "vwap": {
            "name": "Volume Weighted Average Price",
            "description": "成交量加权平均价",
            "parameters": {},
            "outputs": ["vwap"]
        },
        "mfi": {
            "name": "Money Flow Index",
            "description": "资金流量指数",
            "parameters": {
                "period": {"default": 14, "type": "int", "description": "计算周期"}
            },
            "outputs": ["mfi"]
        },
        "obv": {
            "name": "On-Balance Volume",
            "description": "平衡成交量",
            "parameters": {},
            "outputs": ["obv"]
        },
        "adl": {
            "name": "Accumulation/Distribution Line",
            "description": "累积/派发线",
            "parameters": {},
            "outputs": ["adl"]
        },
        "cmf": {
            "name": "Chaikin Money Flow",
            "description": "蔡金资金流量",
            "parameters": {
                "period": {"default": 20, "type": "int", "description": "计算周期"}
            },
            "outputs": ["cmf"]
        },
        "standard_deviation": {
            "name": "Standard Deviation",
            "description": "标准差",
            "parameters": {
                "period": {"default": 20, "type": "int", "description": "计算周期"}
            },
            "outputs": ["std"]
        },
        "adx": {
            "name": "Average Directional Index",
            "description": "平均方向指数",
            "parameters": {
                "period": {"default": 14, "type": "int", "description": "计算周期"}
            },
            "outputs": ["adx", "di_plus", "di_minus"]
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

        # 修改字段名为包含周期的形式
        df[f'rsi_{period}'] = rsi

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
    def calculate_atr(klines: List[Dict[str, Any]], period: int = 14) -> List[Dict[str, Any]]:
        """
        计算平均真实范围(ATR)

        Args:
            klines: K线数据列表
            period: ATR周期

        Returns:
            包含ATR指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)

        # 计算真实波幅(TR)
        df['tr0'] = abs(df['high'] - df['low'])
        df['tr1'] = abs(df['high'] - df['close'].shift(1))
        df['tr2'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)

        # 计算ATR
        df[f'atr_{period}'] = df['tr'].rolling(window=period).mean()

        # 清理临时列
        df.drop(['tr0', 'tr1', 'tr2', 'tr'], axis=1, inplace=True)

        return df.to_dict('records')

    @staticmethod
    def calculate_cci(klines: List[Dict[str, Any]], period: int = 20) -> List[Dict[str, Any]]:
        """
        计算商品通道指数(CCI)

        Args:
            klines: K线数据列表
            period: CCI周期

        Returns:
            包含CCI指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)

        # 计算典型价格
        df['tp'] = (df['high'] + df['low'] + df['close']) / 3

        # 计算简单移动平均
        df['sma_tp'] = df['tp'].rolling(window=period).mean()

        # 计算平均绝对偏差 (使用手动计算替代 mad())
        def mean_abs_deviation(x):
            return np.mean(np.abs(x - np.mean(x)))

        df['mad'] = df['tp'].rolling(window=period).apply(mean_abs_deviation, raw=True)

        # 计算CCI
        df[f'cci_{period}'] = (df['tp'] - df['sma_tp']) / (0.015 * df['mad'])

        # 清理临时列
        df.drop(['tp', 'sma_tp', 'mad'], axis=1, inplace=True)

        return df.to_dict('records')

    @staticmethod
    def calculate_williams_r(klines: List[Dict[str, Any]], period: int = 14) -> List[Dict[str, Any]]:
        """
        计算威廉姆斯%R指标

        Args:
            klines: K线数据列表
            period: 周期

        Returns:
            包含威廉姆斯%R指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)

        # 计算周期内最高价和最低价
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()

        # 计算威廉姆斯%R
        df[f'williams_r_{period}'] = (highest_high - df['close']) / (highest_high - lowest_low) * -100

        return df.to_dict('records')

    @staticmethod
    def calculate_momentum(klines: List[Dict[str, Any]], period: int = 10) -> List[Dict[str, Any]]:
        """
        计算动量指标

        Args:
            klines: K线数据列表
            period: 动量周期

        Returns:
            包含动量指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)

        # 计算动量
        df[f'momentum_{period}'] = df['close'] - df['close'].shift(period)

        return df.to_dict('records')

    @staticmethod
    def calculate_ichimoku(klines: List[Dict[str, Any]],
                          tenkan_sen_period: int = 9,
                          kijun_sen_period: int = 26,
                          senkou_span_b_period: int = 52) -> List[Dict[str, Any]]:
        """
        计算顺势指标(Ichimoku Cloud)

        Args:
            klines: K线数据列表
            tenkan_sen_period: 转换线周期
            kijun_sen_period: 基准线周期
            senkou_span_b_period: 先行跨度B周期

        Returns:
            包含顺势指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)

        # 计算转换线 (Tenkan-sen)
        period9_high = df['high'].rolling(window=tenkan_sen_period).max()
        period9_low = df['low'].rolling(window=tenkan_sen_period).min()
        df['tenkan_sen'] = (period9_high + period9_low) / 2

        # 计算基准线 (Kijun-sen)
        period26_high = df['high'].rolling(window=kijun_sen_period).max()
        period26_low = df['low'].rolling(window=kijun_sen_period).min()
        df['kijun_sen'] = (period26_high + period26_low) / 2

        # 计算先行跨度A (Senkou Span A)
        df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(kijun_sen_period)

        # 计算先行跨度B (Senkou Span B)
        period52_high = df['high'].rolling(window=senkou_span_b_period).max()
        period52_low = df['low'].rolling(window=senkou_span_b_period).min()
        df['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(kijun_sen_period)

        # 计算滞后跨度 (Chikou Span)
        df['chikou_span'] = df['close'].shift(-kijun_sen_period)

        return df.to_dict('records')

    @staticmethod
    def calculate_parabolic_sar(klines: List[Dict[str, Any]],
                                acceleration: float = 0.02,
                                maximum: float = 0.2) -> List[Dict[str, Any]]:
        """
           计算抛物线转向指标(Parabolic SAR)

           Args:
               klines: K线数据列表
               acceleration: 步长
               maximum: 最大步长

           Returns:
               包含抛物线转向指标的K线数据
           """
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)

        sar = [0.0] * len(df)

        # 1. 判断初始趋势
        bull = df['close'].iloc[1] >= df['close'].iloc[0]

        af = acceleration
        if bull:
            ep = df['high'].iloc[0]  # 多头趋势极值 = 最高价
            sar[0] = df['low'].iloc[0]  # SAR 在下方
        else:
            ep = df['low'].iloc[0]  # 空头趋势极值 = 最低价
            sar[0] = df['high'].iloc[0]  # SAR 在上方

        for i in range(1, len(df)):
            # 2. 先计算候选SAR
            psar = sar[i - 1] + af * (ep - sar[i - 1])

            # 3. 按方向做约束
            if bull:
                # 通常用前1~2根的low做约束，这里简化为1根或2根都可以
                psar = min(psar, df['low'].iloc[i - 1])
                if i > 1:
                    psar = min(psar, df['low'].iloc[i - 2])
                # 4. 判断是否反转
                if df['low'].iloc[i] < psar:
                    # 反转为空头
                    bull = False
                    sar[i] = ep  # 反转当根SAR = 上一趋势极值
                    af = acceleration
                    ep = df['low'].iloc[i]  # 新空头趋势的初始极值
                else:
                    sar[i] = psar
                    # 更新EP/AF
                    if df['high'].iloc[i] > ep:
                        ep = df['high'].iloc[i]
                        af = min(af + acceleration, maximum)
            else:
                psar = max(psar, df['high'].iloc[i - 1])
                if i > 1:
                    psar = max(psar, df['high'].iloc[i - 2])
                if df['high'].iloc[i] > psar:
                    # 反转为多头
                    bull = True
                    sar[i] = ep
                    af = acceleration
                    ep = df['high'].iloc[i]
                else:
                    sar[i] = psar
                    if df['low'].iloc[i] < ep:
                        ep = df['low'].iloc[i]
                        af = min(af + acceleration, maximum)

        df['sar'] = sar
        return df.to_dict('records')

    @staticmethod
    def calculate_vwap(klines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        计算成交量加权平均价(VWAP)

        Args:
            klines: K线数据列表

        Returns:
            包含VWAP指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)

        # 计算典型价格
        df['tp'] = (df['high'] + df['low'] + df['close']) / 3

        # 计算TP*Volume
        df['tp_volume'] = df['tp'] * df['volume']

        # 计算累积值
        df['cumulative_tp_volume'] = df['tp_volume'].cumsum()
        df['cumulative_volume'] = df['volume'].cumsum()

        # 计算VWAP
        df['vwap'] = df['cumulative_tp_volume'] / df['cumulative_volume']

        # 清理临时列
        df.drop(['tp', 'tp_volume', 'cumulative_tp_volume', 'cumulative_volume'], axis=1, inplace=True)

        return df.to_dict('records')

    @staticmethod
    def calculate_mfi(klines: List[Dict[str, Any]], period: int = 14) -> List[Dict[str, Any]]:
        """
        计算资金流量指数(MFI)

        Args:
            klines: K线数据列表
            period: MFI周期

        Returns:
            包含MFI指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)

        # 计算典型价格
        df['tp'] = (df['high'] + df['low'] + df['close']) / 3

        # 计算资金流量
        df['raw_money_flow'] = df['tp'] * df['volume']

        # 确定资金流向
        df['positive_flow'] = 0.0
        df['negative_flow'] = 0.0

        for i in range(1, len(df)):
            if df['tp'].iloc[i] > df['tp'].iloc[i-1]:
                df.loc[df.index[i], 'positive_flow'] = df['raw_money_flow'].iloc[i]
            elif df['tp'].iloc[i] < df['tp'].iloc[i-1]:
                df.loc[df.index[i], 'negative_flow'] = df['raw_money_flow'].iloc[i]

        # 计算周期内的正负资金流量总和
        df['positive_money_flow'] = df['positive_flow'].rolling(window=period).sum()
        df['negative_money_flow'] = df['negative_flow'].rolling(window=period).sum()

        # 计算资金比率
        df['money_ratio'] = df['positive_money_flow'] / df['negative_money_flow']

        # 计算MFI
        df[f'mfi_{period}'] = 100 - (100 / (1 + df['money_ratio']))

        # 清理临时列
        df.drop(['tp', 'raw_money_flow', 'positive_flow', 'negative_flow',
                 'positive_money_flow', 'negative_money_flow', 'money_ratio'],
                axis=1, inplace=True)

        return df.to_dict('records')

    @staticmethod
    def calculate_obv(klines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)

        # 初始化 OBV（标准：第一根为0）
        obv = [0.0]

        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i - 1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i - 1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])

        df['obv'] = obv
        return df.to_dict('records')

    @staticmethod
    def calculate_adl(klines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        计算累积/派发线(ADL)

        Args:
            klines: K线数据列表

        Returns:
            包含ADL指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)

        # 计算CLV(收盘价位置值)
        df['clv'] = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        df['clv'].fillna(0, inplace=True)  # 处理除零情况

        # 计算资金流量
        df['money_flow_volume'] = df['clv'] * df['volume']

        # 计算累积/派发线
        df['adl'] = df['money_flow_volume'].cumsum()

        # 清理临时列
        df.drop(['clv', 'money_flow_volume'], axis=1, inplace=True)

        return df.to_dict('records')

    @staticmethod
    def calculate_cmf(klines: List[Dict[str, Any]], period: int = 20) -> List[Dict[str, Any]]:
        """
        计算蔡金资金流量(CMF)

        Args:
            klines: K线数据列表
            period: CMF周期

        Returns:
            包含CMF指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)

        # 计算CLV(收盘价位置值)
        df['clv'] = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        df['clv'].fillna(0, inplace=True)  # 处理除零情况

        # 计算资金流量
        df['money_flow_volume'] = df['clv'] * df['volume']

        # 计算周期内资金流量和成交量的移动平均
        df['money_flow_volume_sum'] = df['money_flow_volume'].rolling(window=period).sum()
        df['volume_sum'] = df['volume'].rolling(window=period).sum()

        # 计算CMF
        df[f'cmf_{period}'] = df['money_flow_volume_sum'] / df['volume_sum']

        # 清理临时列
        df.drop(['clv', 'money_flow_volume', 'money_flow_volume_sum', 'volume_sum'],
                axis=1, inplace=True)

        return df.to_dict('records')

    @staticmethod
    def calculate_standard_deviation(klines: List[Dict[str, Any]], period: int = 20) -> List[Dict[str, Any]]:
        """
        计算标准差

        Args:
            klines: K线数据列表
            period: 标准差周期

        Returns:
            包含标准差指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)

        # 计算标准差
        df[f'std_{period}'] = df['close'].rolling(window=period).std()

        return df.to_dict('records')
    @staticmethod
    def calculate_adx(klines: List[Dict[str, Any]], period: int = 14) -> List[Dict[str, Any]]:
        """
        计算平均方向指数(ADX)

        Args:
            klines: K线数据列表
            period: ADX周期

        Returns:
            包含ADX指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)

        # 计算真实波幅(TR)
        df['tr'] = 0.0
        df['tr'].iloc[0] = df['high'].iloc[0] - df['low'].iloc[0]

        for i in range(1, len(df)):
            df.iloc[i, df.columns.get_loc('tr')] = max(
                df['high'].iloc[i] - df['low'].iloc[i],
                abs(df['high'].iloc[i] - df['close'].iloc[i-1]),
                abs(df['low'].iloc[i] - df['close'].iloc[i-1])
            )

        # 计算+DM和-DM
        df['plus_dm'] = 0.0
        df['minus_dm'] = 0.0

        for i in range(1, len(df)):
            up_move = df['high'].iloc[i] - df['high'].iloc[i-1]
            down_move = df['low'].iloc[i-1] - df['low'].iloc[i]

            if up_move > down_move and up_move > 0:
                df.iloc[i, df.columns.get_loc('plus_dm')] = up_move

            if down_move > up_move and down_move > 0:
                df.iloc[i, df.columns.get_loc('minus_dm')] = down_move

        # 计算+DI和-DI
        df['atr_period'] = df['tr'].rolling(window=period).mean()
        df['plus_di_period'] = df['plus_dm'].rolling(window=period).mean()
        df['minus_di_period'] = df['minus_dm'].rolling(window=period).mean()

        df['di_plus'] = (df['plus_di_period'] / df['atr_period']) * 100
        df['di_minus'] = (df['minus_di_period'] / df['atr_period']) * 100

        # 计算DX
        dx = abs(df['di_plus'] - df['di_minus']) / (df['di_plus'] + df['di_minus']) * 100

        # 计算ADX
        df[f'adx_{period}'] = dx.rolling(window=period).mean()

        # 清理临时列
        df.drop(['tr', 'plus_dm', 'minus_dm', 'atr_period', 'plus_di_period',
                 'minus_di_period'], axis=1, inplace=True)

        return df.to_dict('records')

    @staticmethod
    def calculate_volatility(klines: List[Dict[str, Any]], period: int = 20) -> List[Dict[str, Any]]:
        """
        计算波动率指标

        Args:
            klines: K线数据列表
            period: 波动率周期

        Returns:
            包含波动率指标的K线数据
        """
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)

        # 计算收益率
        df['returns'] = df['close'].pct_change()

        # 计算波动率(收益率的标准差)
        df[f'volatility_{period}'] = df['returns'].rolling(window=period).std()

        # 删除临时列
        df.drop(['returns'], axis=1, inplace=True)

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
        # 依次计算各种指标，传入默认周期参数
        result = TechnicalIndicators.calculate_macd(klines)
        result = TechnicalIndicators.calculate_rsi(result, 14)
        result = TechnicalIndicators.calculate_bollinger_bands(result)
        result = TechnicalIndicators.calculate_ma(result, 30)
        result = TechnicalIndicators.calculate_ma(result, 10)
        result = TechnicalIndicators.calculate_ema(result, 12)
        result = TechnicalIndicators.calculate_ema(result, 26)

        result = TechnicalIndicators.calculate_stochastic(result)
        result = TechnicalIndicators.calculate_atr(result, 14)
        result = TechnicalIndicators.calculate_cci(result, 20)
        result = TechnicalIndicators.calculate_williams_r(result, 14)
        result = TechnicalIndicators.calculate_momentum(result, 10)
        result = TechnicalIndicators.calculate_ichimoku(result)
        result = TechnicalIndicators.calculate_parabolic_sar(result)
        result = TechnicalIndicators.calculate_vwap(result)
        result = TechnicalIndicators.calculate_mfi(result, 14)
        result = TechnicalIndicators.calculate_obv(result)
        result = TechnicalIndicators.calculate_adl(result)
        result = TechnicalIndicators.calculate_cmf(result, 20)
        result = TechnicalIndicators.calculate_standard_deviation(result, 20)
        result = TechnicalIndicators.calculate_adx(result, 14)
        result = TechnicalIndicators.calculate_volatility(result)


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
