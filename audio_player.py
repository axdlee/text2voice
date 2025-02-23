import pygame
import os
from typing import Optional

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_audio: Optional[str] = None
        
    def play(self, audio_file: str):
        """
        播放音频文件
        """
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
            
        if self.is_playing():
            self.stop()
            
        self.current_audio = audio_file
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        
    def stop(self):
        """
        停止播放
        """
        if self.is_playing():
            pygame.mixer.music.stop()
            self.current_audio = None
            
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