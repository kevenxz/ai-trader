# app/api/routers/ai_router.py
from xml.etree.ElementTree import tostring

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
from app.core.ai_manager import ai_manager
from exchanges.binance import FuturesSymbol, BinanceFuturesClient

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    service: str
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 16389
    enable_thinking: Optional[bool] = False
    session_id: Optional[str] = None


class ChatTraderRequest(BaseModel):
    service: str = "guiji"
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 16389
    enable_thinking: Optional[bool] = False
    klines_count: Optional[int] = 100
    session_id: Optional[str] = None
    is_Trader: Optional[bool] = False
    symbol: FuturesSymbol = Query(..., description="交易对", example="BTCUSDT")
    interval: str = Query(
        "1h",
        description="K线间隔",
        example="1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M"
    ),


class ServiceConfig(BaseModel):
    service: str
    config: Dict[str, Any]


class ServiceInfoResponse(BaseModel):
    services: Dict[str, Dict[str, Any]]


@router.get("/services")
async def list_services():
    """获取可用的AI服务列表"""
    try:
        services = ai_manager.list_services()
        return {"services": services, "count": len(services)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_service_config():
    """获取AI服务配置信息"""
    try:
        service_info = ai_manager.get_service_info()
        return ServiceInfoResponse(services=service_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def update_service_config(config: ServiceConfig):
    """更新AI服务配置"""
    try:
        success = ai_manager.add_service_dynamically(
            config.service,
            config.config
        )
        if success:
            return {"message": f"Service {config.service} configured successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to configure service {config.service}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat_completion(request: ChatRequest):
    """AI聊天接口"""
    try:
        # 获取服务实例
        service = ai_manager.get_service(request.service)
        if not service:
            raise HTTPException(
                status_code=400,
                detail=f"Service {request.service} not available. Please check configuration."
            )

        # 转换消息格式
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # 调用AI服务
        result = await service.chat_completion(
            messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            enable_thinking=request.enable_thinking,
            session_id=request.session_id
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/trader")
async def chat_completion(request: ChatTraderRequest):
    """AI聊天接口"""
    try:
        # 获取服务实例
        service = ai_manager.get_service(request.service)
        if not service:
            raise HTTPException(
                status_code=400,
                detail=f"Service {request.service} not available. Please check configuration."
            )

        session = service.get_current_session(request.symbol)
        if session is None or len(session) == 0:
            await service.chat_completion(
                None,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                enable_thinking=request.enable_thinking,
                session_id=request.symbol,
                is_trader=request.is_Trader,
                symbol=request.symbol,
                interval=request.interval
            )

        # 判断是否新增交易k线数据
        if request.is_Trader is True:
            # 使用同步客户端获取带技术指标的K线数据
            client = BinanceFuturesClient()
            klines = client.get_klines_with_indicators(
                symbol=request.symbol,
                interval=request.interval,
                limit=request.klines_count,
                start_time=None,
                end_time=None
            )
            # 将k线数据的后100根作为系统消息添加到消息列表开头
            messages = [{"role": "system", "content": str(klines[-120:])}]
            # system_message = {"role": "system", "content": str(klines)}
            # messages = [system_message]
        else:
            # 转换消息格式 - 修复字典访问方式
            messages = []
            for msg in request.messages:
                if isinstance(msg, dict):
                    # 如果msg是字典，直接使用字典键访问
                    messages.append({"role": msg["role"], "content": msg["content"]})
                else:
                    # 如果msg是ChatMessage对象，使用属性访问
                    messages.append({"role": msg.role, "content": msg.content})


        # 调用AI服务
        result = await service.chat_completion(
            messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            enable_thinking=request.enable_thinking,
            session_id=request.symbol,
            is_trader=request.is_Trader,
            symbol=request.symbol,
            interval=request.interval
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embedding")
async def get_embedding(service: str, text: str, model: Optional[str] = None):
    """获取文本嵌入向量"""
    try:
        # 获取服务实例
        ai_service = ai_manager.get_service(service)
        if not ai_service:
            raise HTTPException(
                status_code=400,
                detail=f"Service {service} not available"
            )

        # 获取嵌入向量
        embedding = await ai_service.embedding(text, model=model)
        return {"embedding": embedding, "dimension": len(embedding)}
    except NotImplementedError:
        raise HTTPException(status_code=400, detail=f"Service {service} does not support embedding")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
