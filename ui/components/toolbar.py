from PyQt6.QtWidgets import QToolBar, QPushButton
from utils.logger import get_child_logger

class MainToolBar(QToolBar):
    """主工具栏"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_child_logger('toolbar')
        self.parent = parent
        
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        # 设置按钮
        settings_button = QPushButton("设置")
        settings_button.clicked.connect(self.parent.open_settings)
        self.addWidget(settings_button)
        
        # 自定义音色按钮
        custom_voice_button = QPushButton("自定义音色")
        custom_voice_button.clicked.connect(self.parent.show_custom_voice_list)
        self.addWidget(custom_voice_button)
        
        # 上传音色按钮
        upload_button = QPushButton("上传音色")
        upload_button.clicked.connect(self.parent.upload_voice)
        self.addWidget(upload_button)
        
        # 选择输出目录按钮
        output_button = QPushButton("输出目录")
        output_button.clicked.connect(self.parent.select_output_directory)
        self.addWidget(output_button) 