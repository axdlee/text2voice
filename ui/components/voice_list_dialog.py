from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QWidget, QTableWidget, QTableWidgetItem,
                           QHeaderView)
from utils.logger import get_child_logger
from PyQt6.QtCore import Qt

class VoiceListDialog(QDialog):
    """自定义音色列表对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.logger = parent.logger
        
        self.setWindowTitle("音色列表")
        self.setMinimumWidth(600)  # 加宽一点
        self.setMinimumHeight(400)  # 设置最小高度
        self._init_ui()
        self.refresh_voices()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 音色列表表格
        self.voice_table = QTableWidget()
        self.voice_table.setColumnCount(3)
        self.voice_table.setHorizontalHeaderLabels(["模型", "音色名称", "操作"])
        
        # 设置表格样式
        header = self.voice_table.horizontalHeader()
        # 设置"模型"列宽为200像素
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.voice_table.setColumnWidth(0, 200)
        
        # 设置"音色名称"列宽为150像素
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.voice_table.setColumnWidth(1, 150)
        
        # "操作"列自适应
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        # 设置行号宽度为40像素
        self.voice_table.verticalHeader().setDefaultSectionSize(40)  # 设置行高
        self.voice_table.verticalHeader().setFixedWidth(40)  # 设置行号宽度
        
        # 设置表格其他样式
        self.voice_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.voice_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.voice_table.setAlternatingRowColors(True)  # 设置隔行变色
        
        # 设置表格边距
        self.voice_table.setContentsMargins(10, 10, 10, 10)
        
        layout.addWidget(self.voice_table)
        
        # 添加底部按钮
        button_layout = QHBoxLayout()
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_voices)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def refresh_voices(self):
        """刷新音色列表"""
        try:
            # 清空表格
            self.voice_table.setRowCount(0)
            
            # 获取音色列表
            voices = self.parent.core.tts_service.get_voices()
            
            # 添加音色项
            for voice in voices.get('result', []):
                if isinstance(voice, dict):
                    name = voice.get('customName', '')
                    uri = voice.get('uri', '')
                    model = voice.get('model', '').split('/')[-1]  # 只显示模型名称
                    
                    if name and uri:
                        row = self.voice_table.rowCount()
                        self.voice_table.insertRow(row)
                        
                        # 添加模型
                        model_item = QTableWidgetItem(model)
                        self.voice_table.setItem(row, 0, model_item)
                        
                        # 添加音色名称
                        name_item = QTableWidgetItem(name)
                        self.voice_table.setItem(row, 1, name_item)
                        
                        # 添加操作按钮
                        button_widget = QWidget()
                        button_layout = QHBoxLayout(button_widget)
                        button_layout.setContentsMargins(4, 4, 4, 4)
                        
                        delete_button = QPushButton("删除")
                        delete_button.setStyleSheet("""
                            QPushButton {
                                background-color: #ff4d4d;
                                color: white;
                                border: none;
                                padding: 5px 10px;
                                border-radius: 3px;
                            }
                            QPushButton:hover {
                                background-color: #ff6666;
                            }
                            QPushButton:pressed {
                                background-color: #cc0000;
                            }
                        """)
                        delete_button.clicked.connect(
                            lambda checked, voice_id=uri: self.parent.delete_voice_and_refresh(voice_id, self)
                        )
                        
                        button_layout.addWidget(delete_button)
                        button_layout.addStretch()
                        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                        self.voice_table.setCellWidget(row, 2, button_widget)
                        
        except Exception as e:
            self.logger.error("刷新音色列表失败", exc_info=True) 