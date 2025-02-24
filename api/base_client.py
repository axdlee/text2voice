from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from utils.logger import get_child_logger

class BaseTTSClient(ABC):
    """TTS 客户端基类"""
    
    def __init__(self, api_key: str, api_url: Optional[str] = None):
        self.logger = get_child_logger('api_client')
        self.api_key = api_key
        self.base_url = api_url
        
    @abstractmethod
    def create_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model: Optional[str] = None,
        response_format: str = "mp3",
        sample_rate: int = 32000,
        speed: float = 1.0,
        gain: float = 0.0
    ) -> bytes:
        """文本转语音"""
        pass
        
    @abstractmethod
    def get_voice_list(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取可用音色列表"""
        pass
        
    @abstractmethod
    def delete_voice(self, voice_id: str) -> Dict[str, Any]:
        """删除指定音色"""
        pass
        
    @abstractmethod
    def upload_voice(self, audio: str, model: str, 
                    custom_name: str, text: str) -> Dict[str, Any]:
        """上传自定义音色"""
        pass
        
    @abstractmethod
    def get_available_models(self) -> Dict[str, str]:
        """获取可用模型列表"""
        pass
        
    @abstractmethod
    def get_default_voices(self, model: str) -> List[str]:
        """获取指定模型的默认音色"""
        pass 