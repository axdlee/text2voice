from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QListWidget, QWidget, QFrame,
                           QListWidgetItem)
from utils.logger import get_child_logger

class VoiceListDialog(QDialog):
    """自定义音色列表对话框"""
    def __init__(self, parent=None, tts_service=None):
        super().__init__(parent)
        self.logger = get_child_logger('voice_list_dialog')
        self.tts_service = tts_service
        self.parent = parent
        
        self.setWindowTitle('自定义音色列表')
        self.setMinimumWidth(600)
        
        self._init_ui()
        self._load_voices()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 添加表头
        layout.addWidget(self._create_header())
        
        # 添加分割线
        layout.addWidget(self._create_separator())
        
        # 创建列表
        self.voice_list = QListWidget()
        layout.addWidget(self.voice_list)
        
        # 添加底部按钮
        layout.addLayout(self._create_bottom_buttons())
        
        self.setLayout(layout)
        
    def _create_header(self):
        """创建表头"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 5, 10, 5)
        
        headers = [
            ("模型", 200),
            ("自定义名称", 200),
            ("操作", 100)
        ]
        
        for title, width in headers:
            label = QLabel(title)
            label.setFixedWidth(width)
            layout.addWidget(label)
            
        layout.addStretch()
        return container
        
    def _create_separator(self):
        """创建分割线"""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line
        
    def _create_bottom_buttons(self):
        """创建底部按钮"""
        layout = QHBoxLayout()
        close_button = QPushButton('关闭')
        close_button.setFixedWidth(100)
        close_button.clicked.connect(self.accept)
        layout.addStretch()
        layout.addWidget(close_button)
        return layout
        
    def _load_voices(self):
        """加载音色列表"""
        try:
            response = self.tts_service.get_voices()
            voices = response.get('result', [])
            self.logger.info(f"加载自定义音色列表, 获取到 {len(voices)} 个音色")
            
            for voice in voices:
                self._add_voice_item(voice)
                
        except Exception as e:
            self.logger.error("加载音色列表失败", exc_info=True)
            raise
            
    def _add_voice_item(self, voice):
        """添加音色列表项"""
        try:
            voice_name = voice.get('customName', '未命名')
            voice_id = voice.get('uri')
            voice_model = voice.get('model', '')
            
            if not all([voice_name, voice_id, voice_model]):
                self.logger.warning(f"跳过无效音色数据: {voice}")
                return
                
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(10, 5, 10, 5)
            
            # 添加标签
            for text, width in [(voice_model, 200), (voice_name, 200)]:
                label = QLabel(text)
                label.setFixedWidth(width)
                layout.addWidget(label)
            
            # 添加删除按钮
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.setContentsMargins(0, 0, 0, 0)
            
            delete_button = QPushButton('删除')
            delete_button.setFixedWidth(80)
            delete_button.clicked.connect(
                lambda: self.parent.delete_voice_and_refresh(voice_id, self.voice_list)
            )
            button_layout.addWidget(delete_button)
            
            layout.addWidget(button_container)
            layout.addStretch()
            
            # 创建列表项
            item = QListWidgetItem()
            self.voice_list.addItem(item)
            item.setSizeHint(container.sizeHint())
            self.voice_list.setItemWidget(item, container)
            
        except Exception as e:
            self.logger.error(f"添加音色列表项失败: {voice}", exc_info=True)
            raise 