from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QLineEdit, QTextEdit, QComboBox)
from utils.logger import get_child_logger

class UploadVoiceDialog(QDialog):
    """上传音色对话框"""
    def __init__(self, models, selected_model, parent=None):
        super().__init__(parent)
        self.logger = get_child_logger('upload_dialog')
        self.models = models
        self.selected_model = selected_model
        
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("上传音色")
        layout = QVBoxLayout()
        
        # 音频选择
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("选择音频文件...")
        self.browse_button = QPushButton("浏览")
        self.browse_button.clicked.connect(self._browse_file)
        
        # 模型选择
        self.model_combo = QComboBox()
        for display_name, model_id in self.models:
            self.model_combo.addItem(display_name, model_id)
        
        if self.selected_model:
            index = self.model_combo.findData(self.selected_model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
                
        # 音色名称
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入音色名称...")
        
        # 文本输入
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("输入要转换的文本...")
        
        # 添加所有控件
        layout.addWidget(self.file_path_input)
        layout.addWidget(self.browse_button)
        layout.addWidget(QLabel("选择模型:"))
        layout.addWidget(self.model_combo)
        layout.addWidget(QLabel("音色名称:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("要转换的文本:"))
        layout.addWidget(self.text_input)
        
        # 确认和取消按钮
        buttons = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        
        self.setLayout(layout)
        
    def _browse_file(self):
        """浏览文件"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", "Audio Files (*.mp3 *.wav)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
            
    def get_data(self):
        """获取表单数据"""
        return (
            self.file_path_input.text(),
            self.name_input.text(),
            self.text_input.toPlainText(),
            self.model_combo.currentData()
        ) 