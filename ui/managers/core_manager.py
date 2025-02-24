from typing import Optional, Dict, Any
from utils.logger import get_child_logger
from utils.config_manager import ConfigManager
from utils.audio_manager import AudioManager
from services.tts_service import TTSService
from ui.components.conversion_worker import ConversionWorker

class CoreManager:
    """核心功能管理器"""
    def __init__(self):
        self.logger = get_child_logger('core')
        self.config = ConfigManager()
        self.audio_mgr = AudioManager(self.config.get('output_directory', 'temp'))
        self.tts_service: Optional[TTSService] = None
        self.conversion_thread: Optional[ConversionWorker] = None
        
        # 初始化服务
        api_key = self.config.get('api_key')
        api_url = self.config.get('api_url')
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
        """保存配置"""
        self.logger.info("保存配置...")
        self.config.config = config
        self.config.save()
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        return self.config.get(key, default) 