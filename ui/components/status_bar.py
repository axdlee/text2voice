from PyQt6.QtWidgets import QStatusBar, QProgressBar
from utils.logger import get_child_logger

class MainStatusBar(QStatusBar):
    """主状态栏"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_child_logger('status_bar')
        
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.hide()
        self.addWidget(self.progress_bar)
        
    def show_message(self, message: str, timeout: int = 0):
        """显示状态消息"""
        self.logger.debug(f"状态栏消息: {message}")
        self.showMessage(message, timeout)
        
    def show_progress(self, show: bool = True):
        """显示/隐藏进度条"""
        if show:
            self.progress_bar.setRange(0, 0)  # 设置为忙碌状态
            self.progress_bar.show()
        else:
            self.progress_bar.hide() 