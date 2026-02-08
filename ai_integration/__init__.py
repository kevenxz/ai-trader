# ai_integration/__init__.py
"""AI Integration Package - 统一AI服务管理"""

from ai_integration.manager import AIManager

# 创建全局AI管理器实例
ai_manager = AIManager("ai_config.yaml")

__all__ = ["AIManager", "ai_manager"]
