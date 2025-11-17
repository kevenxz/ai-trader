import logging
import time
import hmac
import hashlib
import base64
import urllib.parse

import aiohttp
# 设置日志级别
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
async def send_msg(msg):
    timestamp = str(round(time.time() * 1000))
    secret = 'SEC3f09d2cc9d3d93e4e63507adf9c38d1e03c7de8df71f68fe9a2ad3c74e481e3b'
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    url = 'https://oapi.dingtalk.com/robot/send?access_token=653160d4afa2b265db9d005c787aa8884cf6342fce43b50ad2e3f2d2e87d3f4b' + '&timestamp=' + timestamp + '&sign=' + sign

    data = {
        "msgtype": "text",
        "text": {
            "content": msg
        }
    }
    connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
    timeout = aiohttp.ClientTimeout(total=10)  # 总共最多等待10秒
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as temp_session:
        return await _do_request(temp_session, url, data)

async def _do_request(session, url, data):
    try:
        async with session.post(url, json=data) as response:
            result = await response.json()
            if response.status == 200:
                logger.info("Message sent successfully: %s", result)
                return result
            else:
                error_text = await response.text()
                logger.error("Failed to send message. Status: %d, Response: %s", response.status, error_text)
                raise Exception(f"DingTalk API Error: {response.status} - {error_text}")
    except aiohttp.ClientError as e:
        logger.exception("Network error occurred while sending message.")
        raise Exception(f"Network error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected error during message sending.")
        raise e
def send_msg_sync(msg):
    """同步版本的消息发送函数"""
    import asyncio
    return asyncio.run(send_msg(msg))
if __name__ == '__main__':
    send_msg_sync("***")