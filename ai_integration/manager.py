# ai_integration/manager.py
from typing import Dict, List, Optional, Any
from .services.config import AIConfig
from .factory import AIServiceFactory
from .services.ai_service import AIService

class AIManager:
    """AI服务管理器 - 支持前端动态配置"""

    def __init__(self, config_path: str = "ai_config.yaml"):
        self.config = AIConfig(config_path)
        self._services: Dict[str, AIService] = {}
        self._load_services_from_config()

    def _load_services_from_config(self) -> None:
        """从配置文件加载服务"""
        services_config = self.config.get_all_services()
        for service_name, config in services_config.items():
            if config.get('enabled', False):
                self._create_and_add_service(service_name, config)

    def _create_and_add_service(self, service_name: str, config: Dict[str, Any]) -> bool:
        """创建并添加服务实例"""
        api_key = config.get('api_key')
        if not api_key:
            return False

        # 从配置中提取参数
        platform = config.get('platform', 'default')
        base_url = config.get('base_url')
        use_langchain = config.get('use_langchain', False)
        available_models = config.get('available_models', [])

        # 创建服务实例
        service = AIServiceFactory.create_service(
            service_name,
            api_key,
            platform=platform,
            base_url=base_url,
            model=config.get('model'),
            use_langchain=use_langchain,
            available_models=available_models
        )

        if service:
            self._services[service_name] = service
            return True
        return False

    def update_service_config(self, service_name: str, config: Dict[str, Any]) -> bool:
        """
        动态更新服务配置（来自前端）

        Args:
            service_name: 服务名称
            config: 新的配置参数
        """
        # 更新运行时配置
        self.config.set_runtime_config(service_name, config)

        # 重新创建服务实例
        if service_name in self._services:
            del self._services[service_name]

        return self._create_and_add_service(service_name, config)

    def add_service_dynamically(self, service_name: str, config: Dict[str, Any]) -> bool:
        """
        动态添加新服务（来自前端配置）

        Args:
            service_name: 服务名称
            config: 服务配置
        """
        config['enabled'] = True
        return self.update_service_config(service_name, config)

    def get_service(self, service_name: str) -> Optional[AIService]:
        """获取AI服务实例"""
        return self._services.get(service_name)

    def list_services(self) -> List[str]:
        """列出所有已配置的服务"""
        return list(self._services.keys())

    def get_service_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务信息（供前端显示）"""
        info = {}
        services_config = self.config.get_all_services()
        for service_name, config in services_config.items():
            info[service_name] = {
                "enabled": config.get('enabled', False),
                "platform": config.get('platform', 'default'),
                "model": config.get('model', ''),
                "available": service_name in self._services,
                "platforms": self.config.get_available_platforms(service_name)
            }
        return info
