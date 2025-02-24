import pygame
import os
from typing import Optional, Callable
from PyQt6.QtCore import QTimer
from audio.base_player import BaseAudioPlayer

class PygameAudioPlayer(BaseAudioPlayer):
    """基于 Pygame 的音频播放器实现"""
    def __init__(self):
        super().__init__()
        self.logger.info("初始化 Pygame 音频播放器...")
        self.check_timer = None
        self.initialize()
        
    def initialize(self) -> None:
        """初始化 Pygame 混音器"""
        try:
            pygame.mixer.init()
            self.logger.debug("Pygame 混音器初始化成功")
        except Exception as e:
            self.logger.error("Pygame 混音器初始化失败", exc_info=True)
            raise
            
    def play(self, audio_file: str, on_complete: Optional[Callable] = None) -> None:
        """播放音频文件"""
        try:
            if not os.path.exists(audio_file):
                raise FileNotFoundError(f"音频文件不存在: {audio_file}")
                
            if self.is_playing():
                self.stop()
                
            self.current_audio = audio_file
            self.on_playback_complete = on_complete
            
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            self.logger.debug(f"开始播放: {audio_file}")
            
            # 创建定时器检查播放状态
            if self.check_timer is None:
                self.check_timer = QTimer()
                self.check_timer.timeout.connect(self._check_playback_status)
            self.check_timer.start(100)  # 每100毫秒检查一次
            
        except Exception as e:
            self.logger.error(f"播放失败: {audio_file}", exc_info=True)
            raise
            
    def stop(self) -> None:
        """停止播放"""
        if self.is_playing():
            pygame.mixer.music.stop()
            self.logger.debug("停止播放")
        self.current_audio = None
        if self.check_timer:
            self.check_timer.stop()
            
    def is_playing(self) -> bool:
        """检查是否正在播放"""
        return pygame.mixer.music.get_busy()
        
    def set_volume(self, volume: float) -> None:
        """设置音量"""
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        self.logger.debug(f"设置音量: {volume}")
        
    def cleanup(self) -> None:
        """清理资源"""
        try:
            self.stop()
            pygame.mixer.quit()
            self.logger.debug("清理 Pygame 资源")
        except Exception as e:
            self.logger.error("清理资源失败", exc_info=True)
            
    def _check_playback_status(self):
        """检查播放状态"""
        if not self.is_playing() and self.current_audio:
            self.current_audio = None
            if self.check_timer:
                self.check_timer.stop()
            if self.on_playback_complete:
                self.on_playback_complete() 