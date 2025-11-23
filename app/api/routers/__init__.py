# app/api/routers/__init__.py
"""API路由模块"""
from . import ai_router as ai_router_module
from . import health as health_module
from . import exchange_router as exchange_router_module
from . import scheduler_router as scheduler_router_module

# 保持原来的导入方式
from .ai_router import router as ai_router
from .health import router as health
from .exchange_router import router as exchange_router
from .scheduler_router import router as scheduler_router

__all__ = ["ai_router", "health","exchange_router","scheduler_router"]
