# ai_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class AIService(ABC):
    """AI服务抽象基类"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
    
    @abstractmethod
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """聊天完成接口"""
        pass
    
    @abstractmethod
    async def embedding(self, text: str, **kwargs) -> List[float]:
        """文本嵌入接口"""
        pass
    # 添加获取当前对话接口
    @abstractmethod
    def get_current_session(self, session_id: str) -> Dict[str, Any]:
        """获取当前对话接口"""
        pass
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """服务名称"""
        pass
