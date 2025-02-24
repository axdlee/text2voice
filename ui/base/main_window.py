from PyQt6.QtWidgets import QMainWindow, QMessageBox
from utils.logger import get_child_logger
from ui.managers.core_manager import CoreManager
from ui.components.toolbar import MainToolBar
from ui.components.status_bar import MainStatusBar
from ui.components.conversion_panel import ConversionPanel
import logging

class BaseMainWindow(QMainWindow):
    """主窗口基类"""
    def __init__(self):
        super().__init__()
        # 确保这些实例只创建一次
        self.core = CoreManager()  # 使用单例模式
        self.logger = logging.getLogger(__name__)
        
        # 初始化UI组件
        self.toolbar = None
        self.status_bar = None
        self.conversion_panel = None
        
        # 设置窗口基本属性
        self.setWindowTitle("Text2Voice")
        self.setMinimumSize(800, 600)
        
    def init_ui(self):
        """初始化UI"""
        # 创建工具栏
        self.toolbar = MainToolBar(self)
        self.addToolBar(self.toolbar)
        
        # 创建状态栏
        self.status_bar = MainStatusBar(self)
        self.setStatusBar(self.status_bar)
        
        # 创建转换面板
        self.conversion_panel = ConversionPanel(self)
        self.setCentralWidget(self.conversion_panel)
        
    def show_error(self, message: str, title: str = "错误"):
        """显示错误对话框"""
        self.logger.error(message)
        QMessageBox.critical(self, title, message)
        
    def show_info(self, message: str, title: str = "提示"):
        """显示信息对话框"""
        self.logger.info(message)
        QMessageBox.information(self, title, message)
        
    def show_warning(self, message: str, title: str = "警告"):
        """显示警告对话框"""
        self.logger.warning(message)
        QMessageBox.warning(self, title, message)
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 清理临时文件
            self.core.audio_mgr.cleanup()
            event.accept()
        except Exception as e:
            self.logger.error("清理临时文件失败", exc_info=True)
            event.accept() 