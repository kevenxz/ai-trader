# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import ai_router, health
import logging
import logging.config

# 为所有模块设置日志级别
logging.getLogger("app").setLevel(logging.INFO)
logging.getLogger("ai_integration").setLevel(logging.INFO)


# 配置全局日志格式
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s]-[%(name)s]-[%(levelname)s] : %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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

# 注册路由
app.include_router(ai_router)
app.include_router(health)

@app.get("/")
async def root():
    return {
        "message": "AI Integration Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    print("Server started")
