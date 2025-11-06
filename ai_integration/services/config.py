# ai_integration/config.py
import os
from typing import Dict, Any, Optional
import yaml
import inspect  # 引入 inspect 模块
class AIConfig:
    """AI服务配置管理类 - 支持运行时参数覆盖"""

    def __init__(self, config_path: str = "ai_config.yaml"):
        # 首先尝试使用传入的路径（可能是相对或绝对）
        if os.path.exists(config_path):
            self.config_path = config_path
        else:
            # 如果传入路径不存在，则尝试相对于 config.py 文件所在目录查找
            this_file_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
            alt_config_path = os.path.join(this_file_dir, "..", config_path)  # 假设 yaml 在上一级
            alt_config_path = os.path.abspath(alt_config_path)
            if os.path.exists(alt_config_path):
                self.config_path = alt_config_path
                print(f"Fallback to resolved config path: {self.config_path}")
            else:
                # 如果都找不到，仍使用原始路径，让 _load_config 处理 fallback
                self.config_path = config_path

        self._config = self._load_config()
        self._runtime_overrides: Dict[str, Any] = {}

        # 打印配置文件内容
        print("AI Config:")
        for service_name, service_config in self._config.get('services', {}).items():
            print(f"  {service_name}:")
            for key, value in service_config.items():
                print(f"    {key}: {value}")

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {
            "services": {
                "deepseek": {
                    "api_key": "",
                    "base_url": "https://api.deepseek.com",
                    "model": "deepseek-chat",
                    "enabled": False
                },
                "kimi": {
                    "api_key": "",
                    "base_url": "https://api.moonshot.cn",
                    "model": "moonshot-v1-8k",
                    "platform": "default",
                    "enabled": False
                }
            },
            "default_service": "kimi"
        }

    def set_runtime_config(self, service_name: str, config: Dict[str, Any]) -> None:
        """设置运行时配置（来自前端）"""
        self._runtime_overrides[service_name] = config

    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """获取指定服务的配置（优先使用运行时配置）"""
        # 基础配置
        base_config = self._config.get('services', {}).get(service_name, {})

        # 运行时覆盖配置
        runtime_config = self._runtime_overrides.get(service_name, {})

        # 合并配置，运行时配置优先
        merged_config = base_config.copy()
        merged_config.update(runtime_config)

        return merged_config

    def get_all_services(self) -> Dict[str, Any]:
        """获取所有服务配置"""
        services = self._config.get('services', {}).copy()
        # 应用运行时覆盖
        for service_name, override_config in self._runtime_overrides.items():
            if service_name in services:
                services[service_name].update(override_config)
            else:
                services[service_name] = override_config
        return services

    def get_default_service(self) -> str:
        """获取默认服务"""
        return self._config.get('default_service', '')

    def get_available_platforms(self, service_name: str) -> Dict[str, str]:
        """获取服务可用的平台列表"""
        if service_name == "kimi":
            return {
                "default": "默认平台",
                "siliconflow": "硅基流动",
                "moonshot": "月之暗面",
                "cn": "中国大陆节点",
                "global": "国际节点"
            }
        return {"default": "默认平台"}
