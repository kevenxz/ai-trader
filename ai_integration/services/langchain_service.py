# ai_integration/services/langchain_service.py
"""LangChain-based AI Service Implementation for Qiniu Cloud and other OpenAI-compatible APIs"""

import json
import logging
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field

from .ai_service import AIService
from app.core.prompts import AI_TRADER_PROMPTS, TraderOutputModel
from app.core import robot
from exchanges.binance import FuturesSymbol
from exchanges.binance.futures import BinanceFuturesClient

# 设置日志记录器
logger = logging.getLogger(__name__)


class LangChainService(AIService):
    """基于LangChain的AI服务实现 - 支持七牛云及OpenAI兼容API"""

    def __init__(
            self,
            api_key: str,
            base_url: str = "https://api.qnaigc.com/v1",
            model: str = "deepseek-ai/DeepSeek-V3",
            max_history_length: int = 300,
            available_models: Optional[List[str]] = None
    ):
        super().__init__(api_key, base_url)
        self.model = model
        self.max_history_length = max_history_length
        self.available_models = available_models or []
        self.session_histories = defaultdict(lambda: deque(maxlen=max_history_length))

        # 初始化LangChain ChatOpenAI客户端
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.1,
            max_tokens=8192
        )

        # 创建输出解析器
        self.output_parser = StrOutputParser()
        self.trader_output_parser = PydanticOutputParser(pydantic_object=TraderOutputModel)

        # 创建Trader提示模板
        self.trader_prompt = ChatPromptTemplate.from_messages([
            ("system", AI_TRADER_PROMPTS),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

        # 创建通用聊天提示模板
        self.chat_prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

        self.platform_info = self._detect_platform(base_url)

    def _detect_platform(self, base_url: str) -> Dict[str, str]:
        """检测平台信息"""
        if "qnaigc" in base_url:
            return {"name": "qiniu", "display": "七牛云"}
        elif "siliconflow" in base_url:
            return {"name": "siliconflow", "display": "硅基流动"}
        elif "openai" in base_url:
            return {"name": "openai", "display": "OpenAI"}
        else:
            return {"name": "unknown", "display": "未知平台"}

    def add_to_history(self, session_id: str, message: Dict[str, str]):
        """将消息添加到指定会话的历史记录中"""
        self.session_histories[session_id].append(message)

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """获取指定会话的历史记录"""
        return list(self.session_histories[session_id])

    def _convert_to_langchain_messages(self, messages: List[Dict[str, str]]):
        """将字典消息转换为LangChain消息对象"""
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                langchain_messages.append(HumanMessage(content=content))
        return langchain_messages

    @property
    def service_name(self) -> str:
        return f"langchain-{self.platform_info['name']}"

    def get_current_session(self, session_id: str) -> List[Dict[str, str]]:
        """获取当前会话"""
        return self.get_history(session_id)

    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return self.available_models

    async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            session_id: Optional[str] = None,
            symbol: Optional[FuturesSymbol] = None,
            is_trader: bool = False,
            **kwargs
    ) -> Dict[str, Any]:
        """
        聊天完成接口 - 使用LangChain实现
        
        Args:
            messages: 消息列表
            session_id: 会话ID
            symbol: 交易对（用于交易分析）
            is_trader: 是否为交易分析模式
            **kwargs: 其他参数（model, temperature, max_tokens等）
        """
        try:
            # 动态更新LLM配置
            model = kwargs.get("model", self.model)
            temperature = kwargs.get("temperature", 0.1)  # 交易分析使用更低的temperature
            max_tokens = kwargs.get("max_tokens", 8192)

            # 创建新的LLM实例以应用不同参数
            llm = ChatOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # 获取历史消息
            history = []
            if session_id:
                history_dicts = self.get_history(session_id)
                if history_dicts:
                    history = self._convert_to_langchain_messages(history_dicts)
                elif is_trader:
                    # 交易模式下初始化系统提示
                    history = [SystemMessage(content=AI_TRADER_PROMPTS)]

            # 构建输入
            if messages:
                last_message = messages[-1]
                user_input = last_message.get("content", "")
            else:
                user_input = ""

            # 选择合适的提示模板和链
            if is_trader:
                chain = self.trader_prompt | llm | self.output_parser
            else:
                chain = self.chat_prompt | llm | self.output_parser

            # 执行链
            logger.info(
                f"LangChain Request: model={model}, platform={self.platform_info['name']}, is_trader={is_trader}")

            response_content = await chain.ainvoke({
                "history": history,
                "input": user_input
            })

            # 如果是交易模式，尝试解析JSON
            parsed_json = None
            if is_trader:
                try:
                    # 尝试从响应中提取JSON
                    json_content = self._extract_json(response_content)
                    if json_content:
                        parsed_json = json.loads(json_content)
                        # 打印解析后的JSON数据
                        logger.info(f"======= 交易分析JSON结果 =======")
                        logger.info(f"Symbol: {symbol.value if symbol else 'N/A'}")
                        logger.info(f"Parsed JSON:\n{json.dumps(parsed_json, ensure_ascii=False, indent=2)}")
                        logger.info(f"================================")

                        # 验证JSON结构（使用Pydantic）
                        try:
                            from app.core.prompts import TraderOutputModel
                            validated_output = TraderOutputModel(**parsed_json)
                            logger.info(
                                f"JSON验证通过: recommendation={validated_output.recommendation}, risk_level={validated_output.risk_level}")

                            # 如果风险等级为LOW或MEDIUM，创建订单
                            if validated_output.risk_level in ["LOW", "MEDIUM"]:
                                await self._create_trading_order(
                                    symbol=symbol,
                                    interval=kwargs.get("interval", "1h"),
                                    analysis=parsed_json
                                )
                        except Exception as validation_error:
                            logger.warning(f"JSON结构验证警告: {str(validation_error)}")
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON解析失败: {str(e)}")
                    logger.warning(f"原始响应内容: {response_content[:500]}...")

            # 构建响应格式（兼容OpenAI格式）
            result = {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": response_content
                    },
                    "finish_reason": "stop"
                }],
                "model": model,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }

            # 如果解析成功，添加结构化数据到响应中
            if parsed_json:
                result["parsed_data"] = parsed_json

            logger.info(f"LangChain Response completed: model={model}")

            # 更新会话历史
            if session_id:
                if messages:
                    for msg in messages:
                        self.add_to_history(session_id, msg)
                self.add_to_history(session_id, {"role": "assistant", "content": response_content})

            # 推送钉钉（交易模式）
            if symbol and is_trader:
                # 如果有解析后的JSON，格式化输出
                if parsed_json:
                    ding_msg = self._format_trader_message(symbol.value, parsed_json)
                else:
                    ding_msg = f"***{symbol.value}***\n{response_content}"
                await robot.send_msg(ding_msg)

            return result

        except Exception as e:
            logger.error(f"LangChain chat completion error: {str(e)}")
            raise Exception(f"LangChain API Error: {str(e)}")

    def _extract_json(self, content: str) -> Optional[str]:
        """从响应内容中提取JSON字符串"""
        import re

        # 尝试直接解析（如果整个内容就是JSON）
        content = content.strip()
        if content.startswith('{') and content.endswith('}'):
            return content

        # 尝试从markdown代码块中提取
        json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', content)
        if json_match:
            return json_match.group(1).strip()

        # 尝试查找第一个 { 和最后一个 } 之间的内容
        first_brace = content.find('{')
        last_brace = content.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return content[first_brace:last_brace + 1]

        return None

    def _format_trader_message(self, symbol: str, data: Dict[str, Any]) -> str:
        """格式化交易分析消息用于钉钉推送"""
        recommendation = data.get("recommendation", "N/A")
        trend = data.get("trend_status", "N/A")
        momentum = data.get("momentum", "N/A")
        risk = data.get("risk_level", "N/A")
        entry_min = data.get("entry_price_min", 0)
        entry_max = data.get("entry_price_max", 0)
        stop_loss = data.get("stop_loss", 0)
        position = data.get("position_size_percentage", 0)

        targets = data.get("targets", [])
        target_str = ""
        for t in targets:
            target_str += f"\n  {t.get('level', '')}: ${t.get('price', 0)} (+{t.get('percentage', 0)}%)"

        msg = f"""***{symbol} 交易分析***
        
📊 **建议**: {recommendation}
📈 趋势: {trend} | 动量: {momentum}
⚠️ 风险等级: {risk}

💰 **交易计划**:
• 入场区间: ${entry_min} - ${entry_max}
• 止损位: ${stop_loss}
• 仓位建议: {position}%
• 目标位:{target_str}

{data.get('analysis_summary', '')}"""

        if data.get('indicator_alerts'):
            msg += f"\n\n⚡ 指标提示: {data.get('indicator_alerts')}"

        return msg

    async def _create_trading_order(
            self,
            symbol: Optional[FuturesSymbol],
            interval: str,
            analysis: Dict[str, Any]
    ) -> Optional[int]:
        """
        当AI分析返回LOW或MEDIUM风险时，创建交易订单
        
        Args:
            symbol: 交易对
            interval: K线周期
            analysis: 解析后的分析结果
            
        Returns:
            订单ID，如果创建成功
        """
        if not symbol:
            logger.warning("无法创建订单：symbol为空")
            return None

        try:
            from app.services.order_service import order_service

            # 获取当前价格
            try:
                client = BinanceFuturesClient()
                ticker = await client.get_symbol_ticker(symbol.value)
                current_price = float(ticker.get('price', 0))
            except Exception as price_error:
                logger.warning(f"获取当前价格失败，使用入场价格: {str(price_error)}")
                current_price = analysis.get('entry_price_min', 0) or analysis.get('entry_price_max', 0)

            if current_price <= 0:
                logger.warning(f"无效价格: {current_price}，跳过订单创建")
                return None

            # 创建订单
            order_id = await order_service.create_order_from_analysis(
                symbol=symbol.value,
                interval=interval,
                analysis=analysis,
                current_price=current_price,
                ai_model=self.model
            )

            if order_id:
                logger.info(
                    f"✅ 成功创建交易订单 #{order_id} - {symbol.value} | 模型: {self.model} | 风险: {analysis.get('risk_level')} | 入场价: {current_price}")

                # 推送订单创建通知到钉钉
                order_msg = f"""🔔 **新订单创建**

📍 订单号: #{order_id}
💹 交易对: {symbol.value}
🤖 AI模型: {self.model}
📊 建议: {analysis.get('recommendation')}
⚠️ 风险: {analysis.get('risk_level')}
💰 入场价: ${current_price}
🛑 止损: ${analysis.get('stop_loss', 'N/A')}"""

                await robot.send_msg(order_msg)

            return order_id

        except ImportError:
            logger.warning("订单服务未初始化(数据库可能未配置)，跳过订单创建")
            return None
        except Exception as e:
            logger.error(f"创建交易订单失败: {str(e)}")
            return None

    async def embedding(self, text: str, **kwargs) -> List[float]:
        """文本嵌入接口"""
        # 使用LangChain的Embeddings接口
        from langchain_openai import OpenAIEmbeddings

        model = kwargs.get("model", "text-embedding-3-small")

        embeddings = OpenAIEmbeddings(
            api_key=self.api_key,
            base_url=self.base_url,
            model=model
        )

        try:
            result = await embeddings.aembed_query(text)
            return result
        except Exception as e:
            logger.error(f"LangChain embedding error: {str(e)}")
            raise Exception(f"LangChain Embedding Error: {str(e)}")
