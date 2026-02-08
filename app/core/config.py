# app/core/config.py
"""Application Configuration - AlphaPulse Trading Platform"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# =============================================
# 应用配置
# =============================================

class Settings:
    """应用配置类"""
    
    # 基础配置
    APP_NAME: str = "AlphaPulse"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_JSON: bool = os.getenv("LOG_JSON", "false").lower() == "true"
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # API配置
    API_PREFIX: str = "/api"
    
    # 路径配置
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    LOG_DIR: Path = BASE_DIR / "logs"


# 全局配置实例
settings = Settings()


# =============================================
# 日志初始化 (向后兼容)
# =============================================

def setup_logging():
    """初始化日志系统 (兼容旧代码)"""
    from app.core.logging import init_logging
    init_logging()