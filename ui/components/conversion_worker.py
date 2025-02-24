from PyQt6.QtCore import QThread, pyqtSignal
from utils.logger import get_child_logger

class ConversionWorker(QThread):
    """文本转语音转换线程"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, tts_service, text, params):
        super().__init__()
        self.logger = get_child_logger('worker')
        self.logger.info("初始化转换线程...")
        self.tts_service = tts_service
        self.text = text
        self.params = params
        
    def run(self):
        try:
            self.logger.info("开始文本转语音任务...")
            self.logger.debug(f"转换参数: {self.params}")
            result = self.tts_service.convert_text(
                text=self.text,
                params=self.params
            )
            self.logger.info("转换任务完成")
            self.finished.emit(result)
        except Exception as e:
            self.logger.error("转换任务失败", exc_info=True)
            self.error.emit(str(e)) 