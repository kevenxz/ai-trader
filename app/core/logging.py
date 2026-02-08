# app/core/logging.py
"""Enhanced Structured Logging Framework - AlphaPulse Trading Platform

Features:
- Structured JSON logging with TraceID
- Console (colored) + File output
- File rotation by size/date
- Unified logger factory
"""

import logging
import logging.handlers
import threading
import uuid
import os
from datetime import datetime
from contextvars import ContextVar
from typing import Dict, Any, Optional
from pathlib import Path

# =============================================
# 配置常量
# =============================================

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "app.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(trace_id)s | %(message)s"
JSON_FORMAT = True  # 是否使用JSON格式
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

# 全局TraceID上下文变量
trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')


# =============================================
# 日志颜色配置 (Console)
# =============================================

class ColorCodes:
    """ANSI颜色代码"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"


LEVEL_COLORS = {
    "DEBUG": ColorCodes.GRAY,
    "INFO": ColorCodes.GREEN,
    "WARNING": ColorCodes.YELLOW,
    "ERROR": ColorCodes.RED,
    "CRITICAL": ColorCodes.MAGENTA + ColorCodes.BOLD,
}


# =============================================
# 自定义 Formatter
# =============================================

class TraceIdFilter(logging.Filter):
    """添加TraceID到日志记录"""
    
    def filter(self, record):
        record.trace_id = trace_id_var.get() or "-"
        return True


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""
    
    def format(self, record):
        # 获取颜色
        level_color = LEVEL_COLORS.get(record.levelname, "")
        reset = ColorCodes.RESET
        
        # 格式化日志
        log_fmt = (
            f"{ColorCodes.GRAY}%(asctime)s{reset} | "
            f"{level_color}%(levelname)-8s{reset} | "
            f"{ColorCodes.CYAN}%(name)s{reset} | "
            f"{ColorCodes.BLUE}%(trace_id)s{reset} | "
            f"%(message)s"
        )
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


class JsonFormatter(logging.Formatter):
    """JSON格式日志"""
    
    def format(self, record):
        import json
        
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "trace_id": getattr(record, 'trace_id', '-'),
            "message": record.getMessage(),
            "thread": threading.current_thread().name,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'extra'):
            log_record.update(record.extra)
        
        return json.dumps(log_record, ensure_ascii=False)


# =============================================
# Logger 工厂
# =============================================

def setup_logging(
    level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True,
    json_format: bool = False
):
    """
    配置日志系统
    
    Args:
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
        json_format: 文件是否使用JSON格式
    """
    # 确保日志目录存在
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 添加TraceID过滤器
    trace_filter = TraceIdFilter()
    
    # 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredFormatter())
        console_handler.addFilter(trace_filter)
        root_logger.addHandler(console_handler)
    
    # 文件处理器 (带轮转)
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        
        if json_format:
            file_handler.setFormatter(JsonFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                LOG_FORMAT,
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
        
        file_handler.addFilter(trace_filter)
        root_logger.addHandler(file_handler)
    
    # 设置第三方库日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器
    
    Args:
        name: 日志器名称 (通常使用 __name__)
    
    Returns:
        配置好的日志器实例
    """
    return logging.getLogger(name)


# =============================================
# TraceID 管理
# =============================================

def generate_trace_id() -> str:
    """生成新的TraceID"""
    return f"trace_{uuid.uuid4().hex[:16]}"


def set_trace_id(trace_id: str = None) -> str:
    """设置当前线程的TraceID"""
    if trace_id is None:
        trace_id = generate_trace_id()
    trace_id_var.set(trace_id)
    return trace_id


def get_trace_id() -> str:
    """获取当前线程的TraceID"""
    return trace_id_var.get() or ""


# =============================================
# 便捷日志器
# =============================================

# 默认日志器实例
logger = get_logger("alphapulse")


# 初始化日志系统
def init_logging():
    """初始化日志系统 (在应用启动时调用)"""
    setup_logging(
        level=os.getenv("LOG_LEVEL", "INFO"),
        enable_console=True,
        enable_file=True,
        json_format=os.getenv("LOG_JSON", "false").lower() == "true"
    )