from abc import ABC, abstractmethod
from typing import Optional, Callable
from utils.logger import get_child_logger

class BaseAudioPlayer(ABC):
    """音频播放器抽象基类"""
    def __init__(self):
        self.logger = get_child_logger('audio_player')
        self.current_audio: Optional[str] = None
        self.on_playback_complete: Optional[Callable] = None
        
    @abstractmethod
    def initialize(self) -> None:
        """初始化播放器"""
        pass
        
    @abstractmethod
    def play(self, audio_file: str, on_complete: Optional[Callable] = None) -> None:
        """播放音频文件"""
        pass
        
    @abstractmethod
    def stop(self) -> None:
        """停止播放"""
        pass
        
    @abstractmethod
    def is_playing(self) -> bool:
        """检查是否正在播放"""
        pass
        
    @abstractmethod
    def set_volume(self, volume: float) -> None:
        """设置音量 (0.0 到 1.0)"""
        pass
        
    def cleanup(self) -> None:
        """清理资源"""
        pass 