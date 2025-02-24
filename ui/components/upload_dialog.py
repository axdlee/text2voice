from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QLineEdit, QTextEdit, QComboBox, QFileDialog)
from utils.logger import get_child_logger
from api.silicon_flow_client import SiliconFlowClient
import re

class UploadVoiceDialog(QDialog):
    """上传音色对话框"""
    def __init__(self, parent, tts_service):
        super().__init__(parent)
        self.parent = parent
        self.tts_service = tts_service
        self.logger = parent.logger
        
        # 获取可用模型列表
        self.models = SiliconFlowClient.AVAILABLE_MODELS.items()
        
        self.setWindowTitle("上传自定义音色")
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 音色名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("音色名称:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("只能包含字母、数字、下划线和连字符")
        # 设置最大长度
        self.name_input.setMaxLength(64)
        # 设置输入掩码（可选）
        self.name_input.setInputMask("nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn;_")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # 选择模型
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        for model_id, display_name in self.models:
            self.model_combo.addItem(display_name, model_id)
        
        # 设置默认选中的模型
        default_model = SiliconFlowClient.DEFAULT_MODEL
        default_index = self.model_combo.findData(default_model)
        if default_index >= 0:
            self.model_combo.setCurrentIndex(default_index)
        
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)
        
        # 选择文件
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("音频文件:"))
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        file_layout.addWidget(self.file_path)
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_button)
        layout.addLayout(file_layout)
        
        # 添加文本输入
        text_layout = QVBoxLayout()
        text_layout.addWidget(QLabel("音频对应文本:"))
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("请输入音频对应的文本内容...")
        text_layout.addWidget(self.text_input)
        layout.addLayout(text_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.upload_button = QPushButton("上传")
        self.upload_button.clicked.connect(self._upload)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def _browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", "Audio Files (*.mp3 *.wav)"
        )
        if file_path:
            self.file_path.setText(file_path)
            
    def get_data(self):
        """获取表单数据"""
        return (
            self.file_path.text(),
            self.name_input.text(),
            self.model_combo.currentData(),
            self.text_input.toPlainText()
        ) 

    def _upload(self):
        """上传音色"""
        try:
            # 获取表单数据
            file_path, name, model, text = self.get_data()
            
            # 验证输入
            if not file_path:
                self.parent.show_warning("请选择音频文件!")
                return
            if not name:
                self.parent.show_warning("请输入音色名称!")
                return
                
            # 验证音色名称格式
            if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', name):
                self.parent.show_warning(
                    "音色名称格式错误!\n"
                    "- 只能包含字母、数字、下划线和连字符\n"
                    "- 长度不能超过64个字符"
                )
                return
                
            if not text:
                self.parent.show_warning("请输入音频对应的文本内容!")
                return
                
            # 读取音频文件
            with open(file_path, 'rb') as f:
                audio_data = f.read()
                
            # 上传音色
            self.logger.info(f"开始上传音色: {name}")
            self.tts_service.upload_voice(
                voice_name=name,
                model=model,
                audio_data=audio_data,
                text=text
            )
            
            self.parent.show_info(f"音色 {name} 上传成功!")
            self.accept()
            
        except Exception as e:
            self.logger.error("上传音色失败", exc_info=True)
            self.parent.show_error(f"上传失败: {str(e)}") 