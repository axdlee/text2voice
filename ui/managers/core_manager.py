from typing import Optional, Dict, Any
from utils.logger import get_child_logger
from utils.config_manager import ConfigManager
from utils.audio_manager import AudioManager
from services.tts_service import TTSService
from ui.components.conversion_worker import ConversionWorker

class CoreManager:
    """核心功能管理器"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._initialized = True
        self.logger = get_child_logger('core')
        self.config_mgr = ConfigManager()
        self.audio_mgr = AudioManager()
        self.tts_service = None
        self.conversion_thread: Optional[ConversionWorker] = None
        
        # 初始化TTS服务
        api_key = self.get_config('api_key', '')
        api_url = self.get_config('api_url', '')
        if api_key:
            self.init_tts_service(api_key, api_url)
            
    def init_tts_service(self, api_key: str, api_url: Optional[str] = None):
        """初始化TTS服务"""
        self.logger.info("初始化TTS服务...")
        self.tts_service = TTSService(api_key, api_url)
        
    def start_conversion(self, text: str, params: Dict[str, Any]):
        """开始转换任务"""
        if not self.tts_service:
            self.logger.error("TTS服务未初始化")
            raise RuntimeError("TTS服务未初始化")
            
        if self.conversion_thread and self.conversion_thread.isRunning():
            self.logger.warning("已有转换任务正在运行")
            return
            
        self.conversion_thread = ConversionWorker(
            self.tts_service,
            text,
            params
        )
        return self.conversion_thread
        
    def save_config(self, config: Dict[str, Any]):
        """保存配置
        Args:
            config: 要更新的配置项
        """
        self.logger.info("保存配置...")
        # 获取当前配置
        current_config = self.config_mgr.config or {}
        # 更新配置（而不是替换）
        current_config.update(config)
        # 保存更新后的配置
        self.config_mgr.config = current_config
        self.config_mgr.save()
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        return self.config_mgr.get(key, default) 