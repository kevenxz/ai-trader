# ai_integration/services/kimi.py
import json
from collections import defaultdict, deque

import aiohttp
from typing import Dict, Any, List, Optional

from app.core import prompts, robot
from exchanges.binance import BinanceFuturesClient, FuturesSymbol
from .ai_service import AIService
import logging

# 设置日志记录器
logger = logging.getLogger(__name__)


class GuijiService(AIService):
    """硅基流动服务实现 - 支持多平台"""

    def __init__(
            self,
            api_key: str,
            base_url: str = "https://api.moonshot.cn",
            model: str = "moonshot-v1-8k",
            max_history_length: int = 300  # 最大历史记录长度
    ):
        super().__init__(api_key, base_url)
        self.model = model
        self.max_history_length = max_history_length
        self.platform_info = self._detect_platform(base_url)
        self.session_histories = defaultdict(lambda: deque(maxlen=max_history_length))

    def _detect_platform(self, base_url: str) -> Dict[str, str]:
        """检测平台信息"""
        if "siliconflow" in base_url:
            return {"name": "siliconflow", "display": "硅基流动"}
        elif "moonshot" in base_url:
            return {"name": "moonshot", "display": "月之暗面"}
        else:
            return {"name": "unknown", "display": "未知平台"}

    def add_to_history(self, session_id: str, message: Dict[str, str]):
        """将消息添加到指定会话的历史记录中"""
        self.session_histories[session_id].append(message)

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """获取指定会话的历史记录"""
        return list(self.session_histories[session_id])

    @property
    def service_name(self) -> str:
        return f"kimi-{self.platform_info['name']}"

    def _log_request(self, url: str, headers: dict, payload: dict):
        """记录请求日志"""
        try:
            payload_str = json.dumps(payload, ensure_ascii=False)
        except (TypeError, ValueError):
            payload_str = str(payload)

        logger.info(f"GUIJI Request: {url}")
        logger.info(f"curl -X POST {url} \\\n"
                    f"  -H 'Authorization: Bearer {headers.get('Authorization', '').split(' ')[-1]}' \\\n"
                    f"  -H 'Content-Type: {headers.get('Content-Type', 'application/json')}' \\\n"
                    f"  -d '{payload_str}'")

    def get_current_session(self, session_id: str) -> list[dict[str, str]]:
        return self.get_history(session_id)

    async def chat_completion(self, messages: List[Dict[str, str]],
                              session_id: Optional[str] = None, symbol: Optional[BinanceFuturesClient] = None,
                              **kwargs) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 如果提供了 session_id，则合并历史消息
        if session_id:
            history = self.get_history(session_id)
            # 判断历史消息长度
            if history is not None and len(history) > 0:
                combined_messages = history + messages
            else:
                combined_messages = [{"role": "system", "content": prompts.AI_TRADER_PROMPTS}]
                messages = combined_messages
        else:
            combined_messages = messages

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": combined_messages,
            "temperature": kwargs.get("temperature", 0.5),
            "max_tokens": kwargs.get("max_tokens", 8192),
            # "enable_thinking": kwargs.get("enable_thinking", False),

            "stream": kwargs.get("stream", False)
        }

        # 移除None值
        payload = {k: v for k, v in payload.items() if v is not None}

        # 打印整个请求日志  整个curl
        # 记录请求日志
        self._log_request(f"{self.base_url}/chat/completions", headers, payload)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=1000)
                ) as response:
                    result = await response.json()
                    if response.status == 200:
                        logger.info(f"GUIJI Response: {result}")
                        # 将新消息添加到历史记录中
                        if session_id and len(self.get_current_session(session_id)) == 0:
                            for msg in messages:
                                self.add_to_history(session_id, msg)
                            self.add_to_history(session_id, result['choices'][0]['message'])

                        # 推送钉钉
                        await robot.send_msg(
                            "***" + symbol.value + "***\n" + result['choices'][0]['message'][
                                'content'])
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"GUIJI API Error: {response.status} - {error_text}")
                        raise Exception(f"GUIJI API Error: {response.status} - {error_text}")

            except aiohttp.ClientError as e:
                logger.error(f"Network error: {str(e)}")
                raise Exception(f"Network error: {str(e)}")

    async def embedding(self, text: str, **kwargs) -> List[float]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": kwargs.get("model", "moonshot-ai/embedding-v1"),
            "input": text
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                        f"{self.base_url}/v1/embeddings",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["data"][0]["embedding"]
                    else:
                        error_text = await response.text()
                        raise Exception(f"Kimi Embedding API Error: {response.status} - {error_text}")
            except aiohttp.ClientError as e:
                raise Exception(f"Network error: {str(e)}")


import requests

url = "https://api.siliconflow.cn/v1/chat/completions"

payload = {
    "model": "deepseek-ai/DeepSeek-V3.2-Exp",
    "messages": [
        {
            "role": "user",
            "content": "What opportunities and challenges will the Chinese large model industry face in 2025?"
        }
    ],
    "stream": False,
    "max_tokens": 100,
    "enable_thinking": True,
    "thinking_budget": 4096,
    "min_p": 0.05,
    "stop": None,
    "temperature": 0.7,
    "top_p": 0.7,
    "top_k": 50,
    "frequency_penalty": 0.5,
    "n": 1,
    "response_format": {"type": "text"},
    "tools": [
        {
            "type": "function",
            "function": {
                "description": "<string>",
                "name": "<string>",
                "parameters": {},
                "strict": False
            }
        }
    ]
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
