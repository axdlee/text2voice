import pygame
import os
from typing import Optional, Callable
from PyQt6.QtCore import QTimer

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_audio: Optional[str] = None
        self.on_playback_complete: Optional[Callable] = None
        self.check_timer = None
        
    def play(self, audio_file: str, on_complete: Optional[Callable] = None):
        """
        播放音频文件
        """
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
            
        if self.is_playing():
            self.stop()
            
        self.current_audio = audio_file
        self.on_playback_complete = on_complete
        
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        
        # 创建定时器检查播放状态
        if self.check_timer is None:
            self.check_timer = QTimer()
            self.check_timer.timeout.connect(self._check_playback_status)
        self.check_timer.start(100)  # 每100毫秒检查一次
        
    def stop(self):
        """
        停止播放
        """
        if self.is_playing():
            pygame.mixer.music.stop()
        self.current_audio = None
        if self.check_timer:
            self.check_timer.stop()
            
    def is_playing(self) -> bool:
        """
        检查是否正在播放
        """
        return pygame.mixer.music.get_busy()
        
    def set_volume(self, volume: float):
        """
        设置音量 (0.0 到 1.0)
        """
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        
    def _check_playback_status(self):
        """
        检查播放状态
        """
        if not self.is_playing() and self.current_audio:
            self.current_audio = None
            if self.check_timer:
                self.check_timer.stop()
            if self.on_playback_complete:
                self.on_playback_complete() 