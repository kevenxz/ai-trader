# ai_integration/factory.py
from typing import Dict, Type, Optional, Any
from .services.ai_service import AIService
from .services.guiji import GuijiService


class AIServiceFactory:
    """AI服务工厂类 - 支持多平台配置"""

    # 服务映射表
    _service_mapping: Dict[str, str] = {
        "deepseek": "deepseek",
        "siliconflow": "guiji"  # 硅基流动别名
    }

    @classmethod
    def create_service(
        cls,
        service_type: str,
        api_key: str,
        platform: str = "default",
        **kwargs
    ) -> Optional[AIService]:
        """
        创建AI服务实例

        Args:
            service_type: 服务类型 (如: kimi, deepseek)
            api_key: API密钥
            platform: 平台标识 (如: default, siliconflow, moonshot)
            **kwargs: 其他配置参数
        """
        # 解析实际服务类型
        actual_service = cls._service_mapping.get(service_type.lower(), service_type.lower())

        if actual_service == "guiji":
            # 根据平台设置不同的base_url
            # base_url = cls._get_kimi_base_url(platform)
            # kwargs['base_url'] = base_url
            return GuijiService(api_key, **kwargs)
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
