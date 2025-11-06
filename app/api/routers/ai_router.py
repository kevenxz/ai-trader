# app/api/routers/ai_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
from app.core.ai_manager import ai_manager

router = APIRouter(prefix="/api/ai", tags=["ai"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    service: str
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    enable_thinking: Optional[bool] = False
    session_id: Optional[str] = None

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
