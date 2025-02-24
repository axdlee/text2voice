from typing import Optional, Dict
from api.base_client import BaseTTSClient
from api.silicon_flow_client import SiliconFlowClient
from utils.logger import get_child_logger

class TTSClientFactory:
    """TTS 客户端工厂"""
    _logger = get_child_logger('client_factory')
    _instances: Dict[str, BaseTTSClient] = {}
    
    @classmethod
    def create_client(cls, provider: str, api_key: str, 
                     api_url: Optional[str] = None) -> BaseTTSClient:
        """创建 TTS 客户端"""
        if provider not in cls._instances:
            cls._logger.info(f"创建 TTS 客户端: {provider}")
            
            providers = {
                'silicon_flow': SiliconFlowClient,
                # 在这里添加其他服务提供商
            }
            
            client_class = providers.get(provider)
            if not client_class:
                raise ValueError(f"未知的服务提供商: {provider}")
                
            cls._instances[provider] = client_class(api_key, api_url)
            
        return cls._instances[provider]
        
    @classmethod
    def get_client(cls, provider: str) -> Optional[BaseTTSClient]:
        """获取已创建的客户端实例"""
        return cls._instances.get(provider) 