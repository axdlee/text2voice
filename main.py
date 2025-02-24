import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                           QListWidget, QMessageBox, QComboBox, QProgressBar, 
                           QDialog, QLineEdit, QFormLayout, QDialogButtonBox, 
                           QFileDialog, QInputDialog, QDoubleSpinBox, QListWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import requests
from dotenv import load_dotenv
from api_client import SiliconFlowClient
from audio_player import AudioPlayer
from typing import Dict, Any
import base64
import re
import time
from utils.logger import logger, get_child_logger
from utils.config_manager import ConfigManager
from utils.audio_manager import AudioManager
from services.tts_service import TTSService

# 加载环境变量
load_dotenv()

class ConversionWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, tts_service, text, voice_id=None, model=None, sample_rate=32000, speed=1.0, gain=0.0, response_format="mp3"):
        super().__init__()
        self.logger = get_child_logger('worker')
        self.logger.info("初始化转换线程...")
        self.tts_service = tts_service
        self.text = text
        self.params = {
            'voice_id': voice_id,
            'model': model,
            'sample_rate': sample_rate,
            'speed': speed,
            'gain': gain,
            'response_format': response_format
        }
        
    def run(self):
        try:
            self.logger.info("开始文本转语音任务...")
            self.logger.debug(f"转换参数: {self.params}")
            result = self.tts_service.convert_text(
                text=self.text,
                params=self.params
            )
            self.logger.info("转换任务完成")
            self.finished.emit(result)
        except Exception as e:
            self.logger.error("转换任务失败", exc_info=True)
            self.error.emit(str(e))

class SettingsDialog(QDialog):
    def __init__(self, api_key: str, api_url: str):
        super().__init__()
        self.setWindowTitle("设置")
        self.api_key_input = QLineEdit(api_key)
        self.api_url_input = QLineEdit(api_url)
        
        layout = QFormLayout()
        layout.addRow("硅基流动API地址:", self.api_url_input)
        layout.addRow("硅基流动API密钥:", self.api_key_input)

        if not api_key:
            self.api_key_input.setPlaceholderText("请输入硅基流动API密钥")
        if not api_url:
            self.api_url_input.setText("https://api.siliconflow.cn/v1")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_settings(self):
        return self.api_key_input.text(), self.api_url_input.text()

class UploadVoiceDialog(QDialog):
    def __init__(self, models, selected_model, parent=None):
        super().__init__(parent)
        self.setWindowTitle("上传音色")
        self.layout = QVBoxLayout()

        # 音频选择
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("选择音频文件...")
        self.browse_button = QPushButton("浏览")
        self.browse_button.clicked.connect(self.browse_file)

        # 模型选择
        self.model_combo = QComboBox()
        for model in models:
            self.model_combo.addItem(model[1], model[0])  # 显示名称和数据
        index = self.model_combo.findData(selected_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)  # 设置默认选中模型

        # 音色名称输入
        self.custom_name_input = QLineEdit()
        self.custom_name_input.setPlaceholderText("输入音色名称...")

        # 文本输入
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("输入要转换的文本...")

        # 添加控件到布局
        self.layout.addWidget(self.file_path_input)
        self.layout.addWidget(self.browse_button)
        self.layout.addWidget(QLabel("选择模型:"))
        self.layout.addWidget(self.model_combo)
        self.layout.addWidget(QLabel("音色名称:"))
        self.layout.addWidget(self.custom_name_input)
        self.layout.addWidget(QLabel("要转换的文本:"))
        self.layout.addWidget(self.text_input)

        # 确认和取消按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择音频文件", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            self.file_path_input.setText(file_path)

    def get_data(self):
        return self.file_path_input.text(), self.custom_name_input.text(), self.text_input.toPlainText(), self.model_combo.currentData()

class LoadVoiceListThread(QThread):
    finished = pyqtSignal(list)  # 发送获取到的音色列表

    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        voices = self.client.get_voice_list().get('result', [])
        self.finished.emit(voices)  # 发射信号，传递获取到的音色列表

class TextToSpeechApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = get_child_logger('ui')
        self.logger.info("初始化用户界面...")
        
        # 添加模型显示名称到实际值的映射
        self.model_display_to_actual = {
            "CosyVoice2-0.5B (免费)": "FunAudioLLM/CosyVoice2-0.5B",
            "GPT-SoVITS (免费)": "RVC-Boss/GPT-SoVITS",
            "Fish-Speech-1.5 (付费)": "fishaudio/fish-speech-1.5",
            "Fish-Speech-1.4 (付费)": "fishaudio/fish-speech-1.4"
        }
        
        # 初始化服务
        self.config = ConfigManager()
        self.audio_mgr = AudioManager(self.config.get('output_directory', 'temp'))
        self.tts_service = None
        
        # 初始化变量
        self.api_key = self.config.get('api_key')
        self.api_url = self.config.get('api_url')
        self.output_directory = self.config.get('output_directory', 'temp')
        self.current_audio_url = None
        self.conversion_thread = None
        self.delete_buttons = []
        self.custom_voice_list = QListWidget()
        
        # 初始化 API 客户端
        if self.api_key:
            self.tts_service = TTSService(self.api_key, self.api_url)
            
        # 初始化UI
        self.initUI()

    def initUI(self):
        self.setWindowTitle('文本转语音工具')
        self.setGeometry(100, 100, 800, 600)
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        layout = QHBoxLayout()
        
        # 左侧布局
        left_layout = QVBoxLayout()
        
        # 文本输入区
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("请输入要转换的文本...")
        left_layout.addWidget(QLabel("文本输入:"))
        left_layout.addWidget(self.text_input)
        
        # 模型选择下拉框
        self.model_combo = QComboBox()
        self.model_combo.addItem("CosyVoice2-0.5B (免费)", "FunAudioLLM/CosyVoice2-0.5B")
        self.model_combo.addItem("GPT-SoVITS (免费)", "RVC-Boss/GPT-SoVITS")
        self.model_combo.addItem("Fish-Speech-1.5 (付费)", "fishaudio/fish-speech-1.5")
        self.model_combo.addItem("Fish-Speech-1.4 (付费)", "fishaudio/fish-speech-1.4")
        
        # 使用红色标记付费模型
        for i in range(self.model_combo.count()):
            if "(付费)" in self.model_combo.itemText(i):
                self.model_combo.setItemData(i, Qt.GlobalColor.red, Qt.ItemDataRole.ForegroundRole)
        
        left_layout.addWidget(QLabel("选择模型:"))
        left_layout.addWidget(self.model_combo)
        
        # 语音选择下拉框
        self.voice_combo = QComboBox()
        self.voice_combo.addItem("默认音色", None)
        left_layout.addWidget(QLabel("选择音色:"))
        left_layout.addWidget(self.voice_combo)
        
        # 添加可选语音
        self.update_voice_options()
        
        # 添加音频格式选择下拉框
        self.format_combo = QComboBox()
        self.format_combo.addItem("mp3")
        self.format_combo.addItem("opus")
        self.format_combo.addItem("wav")
        self.format_combo.addItem("pcm")
        left_layout.addWidget(QLabel("选择音频格式:"))
        left_layout.addWidget(self.format_combo)
        
        # 采样率选择下拉框
        self.sample_rate_combo = QComboBox()
        left_layout.addWidget(QLabel("采样率:"))
        left_layout.addWidget(self.sample_rate_combo)
        
        # 音速选择器
        self.speed_input = QDoubleSpinBox()
        self.speed_input.setRange(0.25, 4.0)
        self.speed_input.setSingleStep(0.1)
        self.speed_input.setValue(1.0)
        left_layout.addWidget(QLabel("倍速:"))
        left_layout.addWidget(self.speed_input)
        
        # 增益选择器
        self.gain_input = QDoubleSpinBox()
        self.gain_input.setRange(-10, 10)
        self.gain_input.setSingleStep(0.1)
        self.gain_input.setValue(0.0)
        left_layout.addWidget(QLabel("音量增益:"))
        left_layout.addWidget(self.gain_input)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        # 自定义音色列表
        self.custom_voice_list = QListWidget()
        self.custom_voice_list.itemClicked.connect(self.on_custom_voice_clicked)
        
        # 控制按钮区
        button_layout = QHBoxLayout()
        self.convert_btn = QPushButton("转换为语音")
        self.play_btn = QPushButton("播放")
        self.stop_btn = QPushButton("停止")
        self.settings_btn = QPushButton("设置")
        self.upload_voice_btn = QPushButton("上传参考音色")
        self.output_dir_btn = QPushButton("选择输出目录")
        
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.convert_btn)
        button_layout.addWidget(self.play_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.settings_btn)
        button_layout.addWidget(self.upload_voice_btn)
        button_layout.addWidget(self.output_dir_btn)
        
        left_layout.addLayout(button_layout)
        
        # 在TextToSpeechApp类中添加自定义音色列表按钮
        self.show_custom_voice_list_btn = QPushButton('显示自定义音色列表')
        self.show_custom_voice_list_btn.clicked.connect(self.show_custom_voice_list)
        left_layout.addWidget(self.show_custom_voice_list_btn)
        
        # 设置主布局
        layout.addLayout(left_layout, stretch=2)
        
        # 设置主布局
        main_widget.setLayout(layout)
        
        # 连接信号
        self.convert_btn.clicked.connect(self.convert_text)
        self.play_btn.clicked.connect(self.play_audio)
        self.stop_btn.clicked.connect(self.stop_audio)
        self.settings_btn.clicked.connect(self.open_settings)
        self.upload_voice_btn.clicked.connect(self.upload_voice)
        self.output_dir_btn.clicked.connect(self.select_output_directory)
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        self.format_combo.currentIndexChanged.connect(self.update_sample_rate_options)
        
        # 初始化采样率选项
        self.update_sample_rate_options()
        
        # 加载自定义音色列表
        self.load_custom_voice_list()
        
        # 删除音色的功能
        self.custom_voice_list.itemClicked.connect(self.on_custom_voice_clicked)
        
    def load_voice_list(self):
        if not self.tts_service:
            self.logger.error("API客户端未初始化")
            QMessageBox.warning(self, "错误", "API客户端未初始化!")
            return
        
        try:
            self.logger.info("开始加载音色列表...")
            # 清空现有音色
            self.voice_combo.clear()
            
            # 加载系统音色
            response = self.tts_service.get_voices(self.model_combo.currentData())
            voices = response.get('result', [])
            self.logger.debug(f"获取到的音色列表: {voices}")
            
            selected_model = self.model_combo.currentData()
            self.logger.info(f"当前选中模型: {selected_model}")
            
            # 添加音色到下拉框
            for voice in voices:
                voice_model = voice.get('model')
                if voice_model == selected_model:  # 仅添加当前模型的音色
                    voice_name = voice.get('customName', '未命名')
                    voice_id = voice.get('uri')
                    if voice_id:  # 确保有效的voice_id
                        self.logger.info(f"添加自定义音色: {voice_name} ({voice_id})")
                        self.voice_combo.addItem(f"自定义音色: {voice_name}", voice_id)
            
            # 添加默认音色
            self.logger.info("添加默认音色选项")
            self.voice_combo.addItem("默认语音", None)
            
            # 添加系统音色
            if selected_model in SiliconFlowClient.DEFAULT_VOICES:
                for voice in SiliconFlowClient.DEFAULT_VOICES[selected_model]:
                    voice_name = voice.split(':')[-1]
                    self.logger.info(f"添加系统音色: {voice_name}")
                    self.voice_combo.addItem(f"系统音色: {voice_name}", voice)
                    
        except Exception as e:
            self.logger.error("加载音色列表失败", exc_info=True)
            QMessageBox.warning(self, "错误", f"加载语音列表失败: {str(e)}")
            
    def update_voice_options(self):
        if not self.tts_service:
            return
        
        try:
            # 清空现有音色
            self.voice_combo.clear()
            
            selected_model = self.model_combo.currentData()
            voices = self.tts_service.get_voices(selected_model)
            
            # 先添加自定义音色
            for voice in voices.get('result', []):
                if voice.get('model') == selected_model:  # 仅添加当前模型的音色
                    voice_name = voice.get('customName', '未命名')
                    voice_id = voice.get('uri')
                    if voice_id:  # 确保有效的voice_id
                        self.voice_combo.addItem(f"自定义音色: {voice_name}", voice_id)
            
            # 再添加默认音色选项
            self.voice_combo.addItem("默认语音", None)  # 添加默认选项
            for model, voices in SiliconFlowClient.DEFAULT_VOICES.items():
                if model == selected_model:
                    for voice in voices:
                        self.voice_combo.addItem(f"系统音色: {voice.split(':')[-1]}", voice)
                        
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载语音列表失败: {str(e)}")

    def update_sample_rate_options(self):
        # 清空当前选项
        self.sample_rate_combo.clear()
        
        selected_format = self.format_combo.currentText()
        if selected_format == "mp3":
            # mp3格式支持32000和44100 Hz
            self.sample_rate_combo.addItems(["32000", "44100"])
            self.sample_rate_combo.setCurrentText("44100")
        elif selected_format == "opus":
            # opus格式仅支持48000 Hz
            self.sample_rate_combo.addItem("48000")
        elif selected_format in ["wav", "pcm"]:
            # wav和pcm格式支持更多采样率
            self.sample_rate_combo.addItems(["8000", "16000", "24000", "32000", "44100"])
            self.sample_rate_combo.setCurrentText("44100")

    def convert_text(self):
        if not self.tts_service:
            self.logger.error("API客户端未初始化")
            QMessageBox.warning(self, "错误", "请设置API密钥!")
            return
            
        text = self.text_input.toPlainText()
        if not text:
            self.logger.warning("未输入转换文本")
            QMessageBox.warning(self, "错误", "请输入要转换的文本!")
            return
            
        voice_id = self.voice_combo.currentData()
        model = self.model_combo.currentData()
        
        self.logger.info(f"准备转换文本: {text[:50]}...")
        self.logger.debug(f"转换参数: model={model}, voice={voice_id}")
        
        # 如果选择了付费模型，显示提醒
        if "(付费)" in self.model_combo.currentText():
            self.logger.info("用户选择了付费模型，显示确认对话框")
            reply = QMessageBox.question(self, "付费提醒", 
                "您选择的是付费模型，将会产生费用。是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                self.logger.info("用户取消了付费模型转换")
                return
        
        # 获取参数值
        sample_rate = int(self.sample_rate_combo.currentText())
        speed = self.speed_input.value()
        gain = self.gain_input.value()
        response_format = self.format_combo.currentText()
        
        self.logger.debug(f"音频参数: sample_rate={sample_rate}, speed={speed}, gain={gain}, format={response_format}")
        
        self.convert_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 显示忙碌状态
        
        self.conversion_thread = ConversionWorker(
            self.tts_service, text, voice_id, model, sample_rate, speed, gain, response_format
        )
        self.conversion_thread.finished.connect(self.handle_conversion_finished)
        self.conversion_thread.error.connect(self.handle_conversion_error)
        self.logger.info("启动转换线程")
        self.conversion_thread.start()

    def handle_conversion_finished(self, audio_data):
        self.logger.info("文本转换完成，准备保存音频文件...")
        self.convert_btn.setEnabled(True)
        self.play_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        try:
            # 从输入文本中获取默认文件名
            input_text = self.text_input.toPlainText()
            # 获取前10个字符，移除特殊字符和空格
            default_name = re.sub(r'[\\/:*?"<>|\s]', '', input_text[:10])
            if not default_name:  # 如果处理后的文本为空，使用时间戳
                default_name = f'output_{int(time.time())}'
            
            # 弹出对话框让用户输入文件名
            new_file_name, ok = QInputDialog.getText(self, '保存文件', '请输入文件名:', QLineEdit.EchoMode.Normal, default_name)
            if not ok or not new_file_name:
                # 如果用户没有输入文件名，使用默认文件名
                selected_format = self.format_combo.currentText()
                if selected_format == 'mp3':
                    file_extension = 'mp3'
                elif selected_format == 'opus':
                    file_extension = 'opus'
                elif selected_format == 'wav':
                    file_extension = 'wav'
                elif selected_format == 'pcm':
                    file_extension = 'pcm'
                else:
                    file_extension = 'mp3'  # 默认值
                new_file_name = f'{default_name}.{file_extension}'
            else:
                # 根据选择的格式设置文件扩展名
                selected_format = self.format_combo.currentText()
                if selected_format == 'mp3':
                    new_file_name += '.mp3'
                elif selected_format == 'opus':
                    new_file_name += '.opus'
                elif selected_format == 'wav':
                    new_file_name += '.wav'
                elif selected_format == 'pcm':
                    new_file_name += '.pcm'

            # 保存到用户选择的输出目录
            audio_path = self.audio_mgr.save_audio(audio_data, new_file_name)
            
            self.current_audio_url = audio_path
            self.logger.info(f"音频文件已保存: {audio_path}")
            QMessageBox.information(self, '成功', f'文本转换完成! 文件已保存为: {new_file_name}')
        except Exception as e:
            self.logger.error(f"保存音频文件失败: {str(e)}", exc_info=True)
            QMessageBox.warning(self, '错误', f'保存音频文件失败: {str(e)}')
            
    def handle_conversion_error(self, error_msg):
        self.logger.error(f"转换失败: {error_msg}")
        self.convert_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.warning(self, "错误", f"转换失败: {error_msg}")
        
    def play_audio(self):
        if not self.current_audio_url:
            self.logger.warning("没有可播放的音频文件")
            return
        try:
            self.logger.info(f"开始播放音频: {self.current_audio_url}")
            self.audio_mgr.play(self.current_audio_url, self._on_playback_complete)
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"播放失败: {str(e)}")
            self.logger.error(f"音频播放失败: {str(e)}", exc_info=True)
            
    def _on_playback_complete(self):
        """
        音频播放完成的回调函数
        """
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def stop_audio(self):
        self.audio_mgr.stop()
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def load_config(self):
        """加载配置"""
        self.logger.info("加载配置文件...")
        
        # 加载基本设置
        self.api_key = self.config.get('api_key')
        self.api_url = self.config.get('api_url')
        self.output_directory = self.config.get('output_directory', 'temp')
        
        # 加载模型设置
        model_settings = self.config.get('model_settings', {})
        selected_model = self.model_combo.currentData()
        if selected_model in model_settings:
            settings = model_settings[selected_model]
            
            # 设置语音
            if settings.get('voice_id'):
                index = self.voice_combo.findData(settings.get('voice_id'))
                if index >= 0:
                    self.voice_combo.setCurrentIndex(index)
                    
            # 设置其他参数
            self.sample_rate_combo.setCurrentText(str(settings.get('sample_rate', 32000)))
            self.speed_input.setValue(settings.get('speed', 1.0))
            self.gain_input.setValue(settings.get('gain', 0.0))
            self.format_combo.setCurrentText(settings.get('response_format', 'mp3'))
            
        self.logger.debug(f"已加载配置: {self.config.config}")

    def save_config(self):
        """保存配置"""
        self.logger.info("保存配置文件...")
        config = {
            'api_key': self.api_key,
            'api_url': self.api_url,
            'output_directory': self.output_directory,
            'model_settings': {}
        }

        # 更新当前模型的设置
        selected_model = self.model_combo.currentData()
        config['model_settings'][selected_model] = {
            'voice_id': self.voice_combo.currentData(),
            'sample_rate': int(self.sample_rate_combo.currentText()),
            'speed': self.speed_input.value(),
            'gain': self.gain_input.value(),
            'response_format': self.format_combo.currentText()
        }
        
        # 使用 ConfigManager 保存配置
        self.config.config = config
        self.config.save()
        self.logger.debug(f"已保存配置: {config}")

    def open_settings(self):
        dialog = SettingsDialog(self.api_key, self.api_url)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.api_key, self.api_url = dialog.get_settings()
            self.tts_service = TTSService(self.api_key, self.api_url)
            self.save_config()  # 保存配置文件
        
    def upload_voice(self):
        self.logger.info("开始上传自定义音色...")
        dialog = UploadVoiceDialog(
            [(self.model_combo.itemText(i), self.model_combo.itemData(i)) 
             for i in range(self.model_combo.count())], 
            self.model_combo.currentData(), 
            self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            file_path, name, text, display_model = dialog.get_data()
            
            # 验证customName的有效性
            if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', name):
                self.logger.warning(f"无效的音色名称: {name}")
                QMessageBox.warning(self, "错误", "音色名称无效。只能包含字母、数字、下划线和连字符，且不能超过64个字符。")
                return
                
            if not text:
                self.logger.warning("未输入转换文本")
                QMessageBox.warning(self, "错误", "请输入要转换的文本!")
                return
                
            try:
                # 读取音频文件
                with open(file_path, 'rb') as f:
                    audio_data = f.read()
                
                # 构建multipart/form-data格式的音频数据
                audio_content = f'data:audio/mpeg;base64,{base64.b64encode(audio_data).decode("utf-8")}'
                
                # 获取实际的模型ID
                actual_model = self.model_combo.currentData()  # 使用 data 值而不是显示文本
                self.logger.debug(f"上传音色参数 - 显示模型: {display_model}")
                self.logger.debug(f"上传音色参数 - 实际模型: {actual_model}")
                self.logger.debug(f"上传音色参数 - 名称: {name}")
                
                response = self.tts_service.upload_voice(
                    audio=audio_content,
                    model=actual_model,  # 使用实际的模型ID
                    customName=name,
                    text=text
                )
                
                self.logger.info(f"音色上传成功: {name}")
                QMessageBox.information(self, "成功", "音色上传成功!")
                self.load_voice_list()  # 重新加载音色列表
                
            except Exception as e:
                self.logger.error(f"音色上传失败: {str(e)}", exc_info=True)
                QMessageBox.warning(self, "错误", f"上传失败: {str(e)}")
        
    def select_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_directory)
        if directory:
            self.output_directory = directory
            QMessageBox.information(self, "成功", f"输出目录已设置为: {self.output_directory}")
            self.save_config()  # 保存配置
        
    def closeEvent(self, event):
        # 清理临时文件
        try:
            if os.path.exists('temp'):
                for file in os.listdir('temp'):
                    os.remove(os.path.join('temp', file))
                os.rmdir('temp')
        except:
            pass
        event.accept()

    def on_model_changed(self):
        if self.tts_service:  # 只在客户端已初始化时加载音色列表
            self.load_voice_list()

    def load_custom_voice_list(self):
        if not self.tts_service:
            return
        try:
            self.custom_voice_list.clear()  # 清空现有列表
            response = self.tts_service.get_voices()  # 获取所有音色
            voices = response.get('result', [])
            
            self.logger.info(f"加载自定义音色列表, 获取到 {len(voices)} 个音色")
            
            for voice in voices:
                try:
                    voice_name = voice.get('customName', '未命名')
                    voice_id = voice.get('uri')
                    voice_model = voice.get('model', '')
                    
                    if not all([voice_name, voice_id, voice_model]):
                        self.logger.warning(f"跳过无效音色数据: {voice}")
                        continue
                        
                    # 创建容器
                    container = QWidget()
                    layout = QHBoxLayout(container)
                    
                    # 创建列表项
                    item = QListWidgetItem()
                    self.custom_voice_list.addItem(item)
                    item.setSizeHint(container.sizeHint())
                    
                    # 添加音色信息标签
                    name_label = QLabel(f"{voice_name} ({voice_model})")
                    layout.addWidget(name_label)
                    
                    # 创建删除按钮
                    delete_button = QPushButton('删除')
                    delete_button.clicked.connect(lambda checked, vid=voice_id: self.delete_voice(vid))
                    layout.addWidget(delete_button)
                    
                    # 设置容器为列表项的widget
                    self.custom_voice_list.setItemWidget(item, container)
                    self.delete_buttons.append(delete_button)
                    
                    self.logger.debug(f"添加自定义音色: {voice_name} ({voice_id})")
                    
                except Exception as e:
                    self.logger.error(f"处理音色数据失败: {voice}", exc_info=True)
                    continue
                
        except Exception as e:
            self.logger.error("加载自定义音色列表失败", exc_info=True)
            QMessageBox.warning(self, '错误', f'加载自定义音色列表失败: {str(e)}')

    def delete_voice(self, voice_id):
        try:
            # 打印出要删除的 voice_id 以便调试
            print(f"尝试删除音色: {voice_id}")
            
            # 调用 API 删除音色
            response = self.tts_service.delete_voice(voice_id)
            QMessageBox.information(self, '成功', '音色删除成功!')
            self.load_custom_voice_list()  # 重新加载音色列表
        except Exception as e:
            QMessageBox.warning(self, '错误', f'删除音色失败: {str(e)}')

    def on_custom_voice_clicked(self, item):
        # 实现自定义音色列表项点击后的逻辑
        voice_id = item.data(Qt.ItemDataRole.UserRole)
        # 在这里可以添加更多逻辑，例如显示音色详情或编辑音色
        print(f"点击了音色: {voice_id}")

    def show_custom_voice_list(self):
        """显示自定义音色列表对话框"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle('自定义音色列表')
            layout = QVBoxLayout()
            
            # 重新加载音色列表
            self.load_custom_voice_list()
            
            # 添加列表到对话框
            layout.addWidget(self.custom_voice_list)
            
            # 添加关闭按钮
            close_button = QPushButton('关闭')
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            self.logger.error("显示自定义音色列表失败", exc_info=True)
            QMessageBox.warning(self, '错误', f'显示自定义音色列表失败: {str(e)}')

def main():
    logger.info("软件启动...")

    try:
        app = QApplication(sys.argv)
        window = TextToSpeechApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.error("软件崩溃!", exc_info=True)
        raise

if __name__ == '__main__':
    main() 