import os
from pathlib import Path
from typing import Optional
from utils.logger import get_child_logger
from audio_player import AudioPlayer

class AudioManager:
    """音频管理器"""
    def __init__(self, output_dir: str = 'temp'):
        self.logger = get_child_logger('audio')
        self.output_dir = output_dir
        self.player = AudioPlayer()
        self.current_file: Optional[str] = None
        
    def save_audio(self, audio_data: bytes, filename: str) -> str:
        """保存音频文件"""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            filepath = os.path.join(self.output_dir, filename)
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