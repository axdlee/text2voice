import os
from pathlib import Path
from typing import Optional
from utils.logger import get_child_logger
from audio.player_factory import AudioPlayerFactory
import pygame

class AudioManager:
    """音频管理器"""
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
        self.logger = get_child_logger('audio')
        
        # 初始化音频播放器
        self.logger.info("初始化 Pygame 音频播放器...")
        pygame.mixer.init()
        
        # 创建临时目录
        self.temp_dir = 'temp'
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        self.player = AudioPlayerFactory.create_player()
        self.current_file: Optional[str] = None
        
    def save_audio(self, audio_data: bytes, filename: str, output_dir: str = None) -> str:
        """保存音频文件
        Args:
            audio_data: 音频数据
            filename: 文件名
            output_dir: 输出目录，如果为None则使用临时目录
        """
        try:
            # 确定输出目录
            save_dir = output_dir if output_dir else self.temp_dir
            os.makedirs(save_dir, exist_ok=True)
            
            # 保存文件
            filepath = os.path.join(save_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            self.logger.info(f"音频文件已保存: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error("保存音频失败", exc_info=True)
            raise
            
    def play(self, filepath: str, callback: Optional[callable] = None) -> None:
        """播放音频"""
        try:
            self.current_file = filepath
            self.player.play(filepath, callback)
            self.logger.info(f"开始播放音频: {filepath}")
        except Exception as e:
            self.logger.error("播放音频失败", exc_info=True)
            raise
            
    def stop(self) -> None:
        """停止播放"""
        self.player.stop()
        self.logger.info("停止音频播放")

    def cleanup(self):
        """清理临时文件"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                self.logger.info(f"清理临时目录: {self.temp_dir}")
                shutil.rmtree(self.temp_dir)
                os.makedirs(self.temp_dir, exist_ok=True)
        except Exception as e:
            self.logger.error("清理临时文件失败", exc_info=True)
            raise 