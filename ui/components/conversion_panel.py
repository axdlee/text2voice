from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QComboBox, QDoubleSpinBox, QTextEdit, QPushButton)
from utils.logger import get_child_logger
from api.silicon_flow_client import SiliconFlowClient

class ConversionPanel(QWidget):
    """转换控制面板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_child_logger('conversion_panel')
        self.parent = parent
        
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        for model_id, display_name in SiliconFlowClient.AVAILABLE_MODELS.items():
            self.model_combo.addItem(display_name, model_id)
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)
        
        # 音色选择
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("音色:"))
        self.voice_combo = QComboBox()
        voice_layout.addWidget(self.voice_combo)
        layout.addLayout(voice_layout)
        
        # 采样率选择
        sample_rate_layout = QHBoxLayout()
        sample_rate_layout.addWidget(QLabel("采样率:"))
        self.sample_rate_combo = QComboBox()
        for rate in [8000, 16000, 24000, 32000, 44100, 48000]:
            self.sample_rate_combo.addItem(str(rate))
        self.sample_rate_combo.setCurrentText("32000")
        sample_rate_layout.addWidget(self.sample_rate_combo)
        layout.addLayout(sample_rate_layout)
        
        # 语速调节
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("语速:"))
        self.speed_input = QDoubleSpinBox()
        self.speed_input.setRange(0.1, 5.0)
        self.speed_input.setSingleStep(0.1)
        self.speed_input.setValue(1.0)
        speed_layout.addWidget(self.speed_input)
        layout.addLayout(speed_layout)
        
        # 增益调节
        gain_layout = QHBoxLayout()
        gain_layout.addWidget(QLabel("增益:"))
        self.gain_input = QDoubleSpinBox()
        self.gain_input.setRange(-20.0, 20.0)
        self.gain_input.setSingleStep(0.1)
        self.gain_input.setValue(0.0)
        gain_layout.addWidget(self.gain_input)
        layout.addLayout(gain_layout)
        
        # 格式选择
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "wav"])
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)
        
        # 文本输入
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("请输入要转换的文本...")
        layout.addWidget(self.text_input)
        
        # 转换按钮
        self.convert_button = QPushButton("开始转换")
        layout.addWidget(self.convert_button)
        
        self.setLayout(layout)
        
        # 连接信号
        self.model_combo.currentIndexChanged.connect(self.parent.on_model_changed)
        self.convert_button.clicked.connect(self.parent.convert_text) 