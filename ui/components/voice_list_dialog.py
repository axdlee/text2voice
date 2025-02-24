from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QListWidget, QWidget, QFrame,
                           QListWidgetItem)
from utils.logger import get_child_logger
from PyQt6.QtCore import Qt

class VoiceListDialog(QDialog):
    """自定义音色列表对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.logger = parent.logger
        
        self.setWindowTitle("音色列表")
        self.setMinimumWidth(400)  # 设置最小宽度
        self._init_ui()
        self.refresh_voices()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 音色列表
        self.voice_list = QListWidget()
        layout.addWidget(self.voice_list)
        
        # 添加底部按钮
        button_layout = QHBoxLayout()
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def refresh_voices(self):
        """刷新音色列表"""
        try:
            # 清空列表
            self.voice_list.clear()
            
            # 获取音色列表
            voices = self.parent.core.tts_service.get_voices()
            
            # 添加音色项
            for voice in voices.get('result', []):
                if isinstance(voice, dict):
                    name = voice.get('customName', '')
                    uri = voice.get('uri', '')
                    if name and uri:
                        item = QListWidgetItem(f"自定义音色: {name}")
                        item.setData(Qt.ItemDataRole.UserRole, uri)
                        
                        # 添加删除按钮
                        delete_button = QPushButton("删除")
                        delete_button.clicked.connect(
                            lambda checked, voice_id=uri: self.parent.delete_voice_and_refresh(voice_id, self)
                        )
                        
                        # 创建widget容器
                        widget = QWidget()
                        layout = QHBoxLayout()
                        layout.addWidget(QLabel(f"自定义音色: {name}"))
                        layout.addStretch()
                        layout.addWidget(delete_button)
                        widget.setLayout(layout)
                        
                        # 添加到列表
                        self.voice_list.addItem(item)
                        self.voice_list.setItemWidget(item, widget)
                        
        except Exception as e:
            self.logger.error("刷新音色列表失败", exc_info=True) 