# core/interceptors.py
import time
import json
import uuid
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.middleware.base import BaseHTTPMiddleware

from .logging import logger, trace_id_var


class RequestResponseLoggerMiddleware(BaseHTTPMiddleware):
    """请求响应日志中间件"""

    def __init__(self, app: ASGIApp, max_body_size: int = 1024 * 10):  # 10KB
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next):
        # 生成或获取TraceID
        trace_id = self._get_or_create_trace_id(request)
        trace_id_var.set(trace_id)

        # 记录请求开始
        start_time = time.time()

        # 读取请求体（非流式请求）
        request_body = await self._read_request_body(request)

        # 记录请求信息
        await self._log_request(request, request_body, trace_id)

        # 处理请求并捕获响应
        response = await call_next(request)

        # 记录响应信息
        process_time = time.time() - start_time
        await self._log_response(request, response, process_time, trace_id)

        # 添加跟踪头
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        return response

    def _get_or_create_trace_id(self, request: Request) -> str:
        """从请求头获取或生成TraceID"""
        trace_id = request.headers.get("X-Trace-ID") or request.headers.get("Trace-Id")
        if not trace_id:
            trace_id = f"trace_{uuid.uuid4().hex[:16]}"
        return trace_id

    async def _read_request_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """读取请求体"""
        try:
            # 只处理JSON和表单数据
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")

                if "application/json" in content_type:
                    body = await request.body()
                    if body:
                        body_str = body.decode('utf-8')
                        if len(body_str) <= self.max_body_size:
                            try:
                                return json.loads(body_str)
                            except json.JSONDecodeError:
                                return {"raw_body": body_str[:500]}  # 限制长度

                elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                    form_data = await request.form()
                    return dict(form_data)

        except Exception as e:
            logger.warning(f"读取请求体失败: {str(e)}")

        return None

    async def _log_request(self, request: Request, body: Optional[Dict], trace_id: str):
        """记录请求日志"""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        # 过滤敏感头信息
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in ['authorization', 'cookie', 'proxy-authorization']
        }

        log_data = {
            "type": "REQUEST",
            "method": request.method,
            "url": str(request.url),
            "clientIp": client_ip,
            "userAgent": user_agent,
            "queryParams": dict(request.query_params),
            "headers": headers,
            "body": body
        }

        # 直接打印到控制台确保可见
        print(f"[REQUEST] {request.method} {request.url.path} | IP: {client_ip} | TraceID: {trace_id}")
        
        logger.info(
            f"请求开始: {request.method} {request.url.path}",
            extra={"request": log_data}
        )

    async def _log_response(self, request: Request, response: Response, process_time: float, trace_id: str):
        """记录响应日志"""
        log_data = {
            "type": "RESPONSE",
            "method": request.method,
            "url": str(request.url),
            "statusCode": response.status_code,
            "processTime": process_time,
            "responseHeaders": dict(response.headers)
        }

        # 直接打印到控制台确保可见
        print(f"[RESPONSE] {request.method} {request.url.path} | Status: {response.status_code} | Time: {process_time:.4f}s")

        logger.info(
            f"请求完成: {request.method} {request.url.path} | 状态码: {response.status_code} | 耗时: {process_time:.4f}s",
            extra={"response": log_data}
        )


class ResponseBodyCaptureMiddleware:
    """响应体捕获中间件（用于记录响应体）"""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_sender = ResponseSender(send, trace_id_var.get())
        await self.app(scope, receive, response_sender.send)


class ResponseSender:
    """自定义响应发送器，用于捕获响应体"""

    def __init__(self, send: Send, trace_id: str):
        self.send = send
        self.trace_id = trace_id
        self.response_body = b""
        self.started = False

    async def send(self, message: Message):
        if message["type"] == "http.response.start":
            self.started = True
        elif message["type"] == "http.response.body":
            if "body" in message and message["body"]:
                self.response_body += message["body"]

        await self.send(message)

        # 如果是最后一个chunk，记录响应体
        if message.get("more_body", False) is False and self.started and self.response_body:
            await self._log_response_body()

    async def _log_response_body(self):
        """记录响应体"""
        try:
            body_str = self.response_body.decode('utf-8')
            if len(body_str) <= 2048:  # 限制响应体日志长度
                try:
                    response_data = json.loads(body_str)
                    logger.debug(
                        "响应体内容",
                        extra={"responseBody": response_data}
                    )
                except json.JSONDecodeError:
                    logger.debug(
                        "响应体内容(非JSON)",
                        extra={"responseBody": body_str[:500]}
                    )
        except Exception as e:
            logger.warning(f"记录响应体失败: {str(e)}")