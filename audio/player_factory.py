from typing import Optional, Type
from audio.base_player import BaseAudioPlayer
from audio.pygame_player import PygameAudioPlayer
from utils.logger import get_child_logger

class AudioPlayerFactory:
    """音频播放器工厂"""
    _logger = get_child_logger('player_factory')
    _instance: Optional[BaseAudioPlayer] = None
    
    @classmethod
    def create_player(cls, player_type: str = 'pygame') -> BaseAudioPlayer:
        """创建音频播放器实例"""
        if cls._instance is None:
            cls._logger.info(f"创建音频播放器: {player_type}")
            
            player_types = {
                'pygame': PygameAudioPlayer
                # 在这里添加其他播放器类型
            }
            
            player_class = player_types.get(player_type)
            if not player_class:
                cls._logger.error(f"未知的播放器类型: {player_type}")
                raise ValueError(f"未知的播放器类型: {player_type}")
                
            cls._instance = player_class()
            
        return cls._instance
        
    @classmethod
    def get_player(cls) -> Optional[BaseAudioPlayer]:
        """获取当前播放器实例"""
        return cls._instance 