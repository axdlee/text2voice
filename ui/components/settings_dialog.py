from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, 
                           QDialogButtonBox)
from utils.logger import get_child_logger

class SettingsDialog(QDialog):
    """设置对话框"""
    def __init__(self, api_key: str, api_url: str, parent=None):
        super().__init__(parent)
        self.logger = get_child_logger('settings_dialog')
        self.api_key = api_key
        self.api_url = api_url
        
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("设置")
        layout = QFormLayout()
        
        # API密钥输入
        self.api_key_input = QLineEdit(self.api_key)
        if not self.api_key:
            self.api_key_input.setPlaceholderText("请输入硅基流动API密钥")
            
        # API地址输入
        self.api_url_input = QLineEdit(self.api_url)
        if not self.api_url:
            self.api_url_input.setText("https://api.siliconflow.cn/v1")
            
        # 添加表单项
        layout.addRow("硅基流动API地址:", self.api_url_input)
        layout.addRow("硅基流动API密钥:", self.api_key_input)
        
        # 添加按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def get_settings(self):
        """获取设置值"""
        return self.api_key_input.text(), self.api_url_input.text() 