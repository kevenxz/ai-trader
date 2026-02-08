# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import ai_router, health, exchange_router
from app.api.routers.scheduler_router import router as scheduler_router
from app.api.routers.order_router import router as order_router
import logging
import logging.config

from app.core.config import setup_logging
from app.core.interceptors import RequestResponseLoggerMiddleware, ResponseBodyCaptureMiddleware

# 初始化日志配置

setup_logging()

# 为所有模块设置日志级别
logging.getLogger("app").setLevel(logging.INFO)
logging.getLogger("ai_integration").setLevel(logging.INFO)



app = FastAPI(
    title="AI Integration API",
    description="统一AI服务平台接口",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 添加中间件
app.add_middleware(RequestResponseLoggerMiddleware)
app.add_middleware(ResponseBodyCaptureMiddleware)


# 注册路由
app.include_router(ai_router)
app.include_router(health)
app.include_router(exchange_router)
app.include_router(scheduler_router)
app.include_router(order_router)

from app.api.routers.realtime_router import router as realtime_router
app.include_router(realtime_router)


# 数据库和调度器生命周期管理
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库和调度器"""
    try:
        # 初始化数据库连接池 (不再执行schema.sql)
        from app.db.connection import get_db_pool
        await get_db_pool()
        logging.info("Database pool initialized")
        
        # 启动盈亏追踪调度器
        from app.scheduler.profit_tracker import profit_tracker
        await profit_tracker.start()
        logging.info("Profit tracker started")
    except Exception as e:
        logging.warning(f"Startup initialization warning: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    try:
        # 停止盈亏追踪调度器
        from app.scheduler.profit_tracker import profit_tracker
        await profit_tracker.stop()
        
        # 关闭数据库连接池
        from app.db.connection import close_db_pool
        await close_db_pool()
        logging.info("Resources cleaned up")
    except Exception as e:
        logging.warning(f"Shutdown cleanup warning: {str(e)}")

# Mount static files
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Allow API routes to pass through (though they should be caught by include_router above if matched)
        # But since this is a catch-all, we need to be careful.
        # Actually, FastAPI matches specific routes first.
        # But if an API route is 404, it might fall here.
        # We only want to serve index.html for non-API routes.
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
             raise HTTPException(status_code=404, detail="Not Found")

        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Frontend not found"}
else:
    @app.get("/")
    async def root():
        return {
            "message": "AI Integration Platform API",
            "version": "1.0.0",
            "docs": "/docs",
            "frontend": "Not built or not found"
        }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # 使用自定义日志配置
    )
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    print("Server started")
