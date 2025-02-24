from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QComboBox, QDoubleSpinBox, QTextEdit, QPushButton)
from utils.logger import get_child_logger
from api.silicon_flow_client import SiliconFlowClient

class ConversionPanel(QWidget):
    """转换控制面板"""
    # 定义格式与采样率的对应关系
    FORMAT_SAMPLE_RATES = {
        'opus': [48000],
        'wav': [8000, 16000, 24000, 32000, 44100],
        'pcm': [8000, 16000, 24000, 32000, 44100],
        'mp3': [32000, 44100]
    }
    
    # 格式默认采样率
    FORMAT_DEFAULT_RATES = {
        'opus': 48000,
        'wav': 44100,
        'pcm': 44100,
        'mp3': 44100
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_child_logger('conversion_panel')
        self.parent = parent
        
        self._init_ui()
        
        # 获取当前选中的模型
        current_model = self.model_combo.currentData()
        # 初始化后刷新音色列表，传入当前模型
        self.refresh_voices(current_model)
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        for model_id, display_name in SiliconFlowClient.AVAILABLE_MODELS.items():
            self.model_combo.addItem(display_name, model_id)
        
        # 设置默认选中的模型
        default_model = SiliconFlowClient.DEFAULT_MODEL
        default_index = self.model_combo.findData(default_model)
        if default_index >= 0:
            self.model_combo.setCurrentIndex(default_index)
        
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)
        
        # 音色选择
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("音色:"))
        self.voice_combo = QComboBox()
        voice_layout.addWidget(self.voice_combo)
        layout.addLayout(voice_layout)
        
        # 格式选择
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['mp3', 'opus', 'wav', 'pcm'])
        self.format_combo.setCurrentText('mp3')  # 默认选择mp3
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)
        
        # 采样率选择
        sample_rate_layout = QHBoxLayout()
        sample_rate_layout.addWidget(QLabel("采样率:"))
        self.sample_rate_combo = QComboBox()
        sample_rate_layout.addWidget(self.sample_rate_combo)
        layout.addLayout(sample_rate_layout)
        
        # 语速调节
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("语速:"))
        self.speed_input = QDoubleSpinBox()
        self.speed_input.setRange(0.25, 4.0)  # 更新语速范围
        self.speed_input.setSingleStep(0.1)
        self.speed_input.setValue(1.0)
        speed_layout.addWidget(self.speed_input)
        layout.addLayout(speed_layout)
        
        # 增益调节
        gain_layout = QHBoxLayout()
        gain_layout.addWidget(QLabel("增益:"))
        self.gain_input = QDoubleSpinBox()
        self.gain_input.setRange(-10.0, 10.0)  # 更新增益范围
        self.gain_input.setSingleStep(0.1)
        self.gain_input.setValue(0.0)
        gain_layout.addWidget(self.gain_input)
        layout.addLayout(gain_layout)
        
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

        # 初始化采样率选项
        self._update_sample_rates('mp3')

    def _on_format_changed(self, format_name: str):
        """输出格式变更处理"""
        self._update_sample_rates(format_name)
        
    def _update_sample_rates(self, format_name: str):
        """更新采样率选项"""
        self.sample_rate_combo.clear()
        
        # 获取当前格式支持的采样率
        sample_rates = self.FORMAT_SAMPLE_RATES.get(format_name, [])
        
        # 添加采样率选项
        for rate in sample_rates:
            self.sample_rate_combo.addItem(str(rate))
            
        # 设置默认采样率
        default_rate = self.FORMAT_DEFAULT_RATES.get(format_name)
        if default_rate:
            self.sample_rate_combo.setCurrentText(str(default_rate))

    def refresh_voices(self, model: str = None):
        """刷新音色列表
        Args:
            model: 指定模型，如果为None则获取所有音色
        """
        try:
            if not self.parent.core.tts_service:
                return
                
            # 清空当前列表
            self.voice_combo.clear()
            
            # 获取音色列表
            voices = self.parent.core.tts_service.get_voices(model)
            
            # 先添加默认音色
            if model:
                default_voices = SiliconFlowClient.DEFAULT_VOICES.get(model, [])
                for voice in default_voices:
                    name = voice.split(':')[-1]  # 获取音色名称
                    self.voice_combo.addItem(f"默认音色: {name}", voice)
            
            # 再添加自定义音色
            for voice in voices.get('result', []):
                if isinstance(voice, dict):
                    # 如果是字典格式
                    name = voice.get('customName', '')
                    uri = voice.get('uri', '')
                    if name and uri:
                        self.voice_combo.addItem(f"自定义音色: {name}", uri)
                else:
                    self.logger.warning(f"未知的音色数据格式: {voice}")
                    
            # 如果有保存的上次选择，则设置为当前选择
            last_voice = self.parent.core.get_config('last_voice')
            if last_voice:
                index = self.voice_combo.findData(last_voice)
                if index >= 0:
                    self.voice_combo.setCurrentIndex(index)
                    
        except Exception as e:
            self.logger.error("刷新音色列表失败", exc_info=True)
            
    def update_model_settings(self, model):
        """更新模型相关设置"""
        # 根据不同模型更新UI状态
        if model == 'silicon_flow':
            # Silicon Flow模型的特定设置
            self.sample_rate_combo.setEnabled(True)
            self.speed_input.setEnabled(True)
            self.gain_input.setEnabled(True)
            
        elif model == 'other_model':
            # 其他模型的特定设置
            pass
            
        # 保存当前设置
        self.parent.core.save_config({
            'last_model': model,
            'sample_rate': self.sample_rate_combo.currentText(),
            'speed': self.speed_input.value(),
            'gain': self.gain_input.value()
        })
        
        # 刷新音色列表，传入当前选中的模型
        self.refresh_voices(model) 