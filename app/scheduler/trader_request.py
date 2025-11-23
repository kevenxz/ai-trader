import requests
import json
import time
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trader_task.log'),
        logging.StreamHandler()
    ]
)


def send_trader_request():
    url = "http://127.0.0.1:8000/api/ai/chat/trader"

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    data = {
        "service": "guiji",
        "messages": [
            {
                "role": "string",
                "content": "string"
            }
        ],
        "klines_count": 500,
        "model": "moonshotai/Kimi-K2-Thinking",
        "temperature": 0.4,
        "max_tokens": 293487,
        "enable_thinking": True,
        "session_id": "string",
        "is_Trader": True,
        "symbol": "ETHUSDT",
        "interval": "1h"
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=200)
        response.raise_for_status()
        logging.info(f"请求成功: {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"请求失败: {e}")
        return None


if __name__ == "__main__":
    while True:
        send_trader_request()
        # 等待20分钟
        time.sleep(20 * 60)