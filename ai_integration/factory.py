# ai_integration/factory.py
from typing import Dict, Type, Optional, Any
from .services.ai_service import AIService
from .services.guiji import GuijiService


class AIServiceFactory:
    """AI服务工厂类 - 支持多平台配置"""

    # 服务映射表
    _service_mapping: Dict[str, str] = {
        "deepseek": "deepseek",
        "siliconflow": "guiji",  # 硅基流动别名
        "qiniu": "langchain",    # 七牛云使用LangChain
        "langchain": "langchain"  # LangChain服务
    }

    @classmethod
    def create_service(
        cls,
        service_type: str,
        api_key: str,
        platform: str = "default",
        use_langchain: bool = False,
        **kwargs
    ) -> Optional[AIService]:
        """
        创建AI服务实例

        Args:
            service_type: 服务类型 (如: kimi, deepseek, qiniu)
            api_key: API密钥
            platform: 平台标识 (如: default, siliconflow, moonshot)
            use_langchain: 是否使用LangChain实现
            **kwargs: 其他配置参数
        """
        # 解析实际服务类型
        actual_service = cls._service_mapping.get(service_type.lower(), service_type.lower())
        
        # 如果配置了use_langchain或服务类型为qiniu，使用LangChain实现
        if use_langchain or actual_service == "langchain" or service_type.lower() == "qiniu":
            from .services.langchain_service import LangChainService
            return LangChainService(
                api_key=api_key,
                base_url=kwargs.get('base_url', 'https://api.qnaigc.com/v1'),
                model=kwargs.get('model', 'deepseek-ai/DeepSeek-V3'),
                available_models=kwargs.get('available_models', [])
            )

        if actual_service == "guiji":
            # 过滤掉LangChain特有的参数
            guiji_kwargs = {k: v for k, v in kwargs.items() 
                           if k not in ['available_models', 'use_langchain']}
            return GuijiService(api_key, **guiji_kwargs)
        # elif actual_service == "deepseek":
        #     from .services.deepseek import DeepSeekService
        #     return DeepSeekService(api_key, **kwargs)

        return None

    @classmethod
    def _get_kimi_base_url(cls, platform: str) -> str:
        """获取Kimi服务的基础URL"""
        platform_urls = {
            "default": "https://api.moonshot.cn",
            "siliconflow": "https://api.siliconflow.cn",  # 假设的硅基流动平台
            "moonshot": "https://api.moonshot.cn",
            "cn": "https://api.moonshot.cn",
            "global": "https://api-global.moonshot.cn"  # 假设的全球节点
        }
        return platform_urls.get(platform, platform_urls["default"])

    @classmethod
    def get_supported_services(cls) -> list:
        """获取支持的服务列表"""
        return list(set(cls._service_mapping.values()))

    @classmethod
    def get_service_aliases(cls) -> Dict[str, str]:
        """获取服务别名映射"""
        return cls._service_mapping.copy()
