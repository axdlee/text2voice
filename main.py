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

# 加载环境变量
load_dotenv()

class ConversionWorker(QThread):
    finished = pyqtSignal(object)  # 改为object类型，可以传递二进制数据
    error = pyqtSignal(str)
    
    def __init__(self, client, text, voice_id=None, model=None, sample_rate=32000, speed=1.0, gain=0.0, response_format="mp3"):
        super().__init__()
        self.client = client
        self.text = text
        self.voice_id = voice_id
        self.model = model
        self.sample_rate = sample_rate
        self.speed = speed
        self.gain = gain
        self.response_format = response_format
        
    def run(self):
        try:
            result = self.client.create_speech(
                text=self.text,
                voice_id=self.voice_id,
                model=self.model,
                response_format=self.response_format,
                sample_rate=self.sample_rate,
                speed=self.speed,
                gain=self.gain
            )
            self.finished.emit(result)
        except Exception as e:
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
        # 添加模型名称映射
        self.model_display_to_actual = {
            "CosyVoice2-0.5B (免费)": "FunAudioLLM/CosyVoice2-0.5B",
            "GPT-SoVITS (免费)": "RVC-Boss/GPT-SoVITS",
            "Fish-Speech-1.5 (付费)": "fishaudio/fish-speech-1.5",
            "Fish-Speech-1.4 (付费)": "fishaudio/fish-speech-1.4"
        }
        super().__init__()
        self.config_file = 'data/config.json'
        self.api_key = None
        self.api_url = None
        self.output_directory = 'temp'  # 默认输出目录
        self.client = None
        self.audio_player = AudioPlayer()
        self.current_audio_url = None
        self.conversion_thread = None
        self.custom_voice_list = QListWidget()
        self.delete_buttons = []  # 存储删除按钮的列表
        
        # 先创建UI
        self.initUI()
        
        # 再加载配置
        self.load_config()
        
        # 初始化客户端并加载音色列表
        if self.api_key:
            self.client = SiliconFlowClient(self.api_key, self.api_url)
            self.load_voice_list()  # 只在客户端初始化后加载一次

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
        #left_layout.addWidget(QLabel('自定义音色列表:'))
        #left_layout.addWidget(self.custom_voice_list)
        
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
        if not self.client:
            QMessageBox.warning(self, "错误", "API客户端未初始化!")
            return
        
        try:
            # 清空现有音色
            self.voice_combo.clear()
            
            # 加载系统音色
            voices = self.client.get_voice_list()
            print(f"获取到的音色列表: {voices}")  # 调试信息
            
            # 先添加自定义音色
            custom_voices = voices.get('result', [])
            print(f"自定义音色列表: {custom_voices}")  # 调试信息
            
            selected_model = self.model_combo.currentData()
            for voice in custom_voices:
                print(f"处理音色: {voice}")  # 调试信息
                voice_model = voice.get('model')
                # 如果voice_model在映射表中，使用映射后的值
                if voice_model in self.model_display_to_actual:
                    voice_model = self.model_display_to_actual[voice_model]
                print(f"处理后的音色模型: {voice_model}, 当前选中模型: {selected_model}")  # 调试信息
                
                if voice_model == selected_model:  # 仅添加当前模型的音色
                    voice_name = voice.get('customName', '未命名')
                    voice_id = voice.get('uri')
                    print(f"添加自定义音色 - 名称: {voice_name}, ID: {voice_id}")  # 调试信息
                    if voice_id:  # 确保有效的voice_id
                        self.voice_combo.addItem(f"自定义音色: {voice_name}", voice_id)
            
            # 再添加默认音色选项
            self.voice_combo.addItem("默认语音", None)  # 添加默认选项
            
            # 添加系统音色
            if selected_model in SiliconFlowClient.DEFAULT_VOICES:
                for voice in SiliconFlowClient.DEFAULT_VOICES[selected_model]:
                    voice_name = voice.split(':')[-1]
                    self.voice_combo.addItem(f"系统音色: {voice_name}", voice)
                    print(f"添加系统音色: {voice_name}")  # 调试信息
                        
        except Exception as e:
            print(f"加载音色列表时出错: {str(e)}")  # 调试信息
            QMessageBox.warning(self, "错误", f"加载语音列表失败: {str(e)}")
            
    def update_voice_options(self):
        if not self.client:
            return
        
        try:
            # 清空现有音色
            self.voice_combo.clear()
            
            selected_model = self.model_combo.currentData()
            voices = self.client.get_voice_list()
            
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
        if not self.client:
            QMessageBox.warning(self, "错误", "请设置API密钥!")
            return
            
        text = self.text_input.toPlainText()
        if not text:
            QMessageBox.warning(self, "错误", "请输入要转换的文本!")
            return
            
        voice_id = self.voice_combo.currentData()
        model = self.model_combo.currentData()
        
        # 如果选择了付费模型，显示提醒
        if "(付费)" in self.model_combo.currentText():
            reply = QMessageBox.question(self, "付费提醒", 
                "您选择的是付费模型，将会产生费用。是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
        
        # 获取参数值
        sample_rate = int(self.sample_rate_combo.currentText())
        speed = self.speed_input.value()
        gain = self.gain_input.value()
        response_format = self.format_combo.currentText()
        
        self.convert_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 显示忙碌状态
        
        self.conversion_thread = ConversionWorker(self.client, text, voice_id, model, sample_rate, speed, gain, response_format)
        self.conversion_thread.finished.connect(self.handle_conversion_finished)
        self.conversion_thread.error.connect(self.handle_conversion_error)
        self.conversion_thread.start()
        
    def handle_conversion_finished(self, audio_data):
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
            os.makedirs(self.output_directory, exist_ok=True)
            audio_path = os.path.join(self.output_directory, new_file_name)
            
            # 如果是URL，下载音频
            if isinstance(audio_data, str) and audio_data.startswith('http'):
                response = requests.get(audio_data)
                response.raise_for_status()
                audio_content = response.content
            else:
                # 如果是二进制数据，直接使用
                audio_content = audio_data
                
            with open(audio_path, 'wb') as f:
                f.write(audio_content)
                
            self.current_audio_url = audio_path
            QMessageBox.information(self, '成功', f'文本转换完成! 文件已保存为: {new_file_name}')
        except Exception as e:
            QMessageBox.warning(self, '错误', f'保存音频文件失败: {str(e)}')
            
    def handle_conversion_error(self, error_msg):
        self.convert_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.warning(self, "错误", f"转换失败: {error_msg}")
        
    def play_audio(self):
        if not self.current_audio_url:
            return
            
        try:
            self.audio_player.play(self.current_audio_url, self._on_playback_complete)
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"播放失败: {str(e)}")
            
    def _on_playback_complete(self):
        """
        音频播放完成的回调函数
        """
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def stop_audio(self):
        self.audio_player.stop()
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.api_key = config.get('api_key')
                self.api_url = config.get('api_url')
                self.output_directory = config.get('output_directory', 'temp')  # 加载输出目录
                
                # 加载模型设置
                if 'model_settings' in config:
                    model_settings = config['model_settings']
                    for model, settings in model_settings.items():
                        # 如果是当前选中的模型，应用其设置
                        if model == self.model_combo.currentData():
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
                            break

    def save_config(self):
        config = {
            'api_key': self.api_key,
            'api_url': self.api_url,
            'output_directory': self.output_directory,
            'model_settings': {}
        }
        # 更新API设置
        config['api_key'] = self.api_key
        config['api_url'] = self.api_url

        # 确保model_settings存在
        if 'model_settings' not in config:
            config['model_settings'] = {}

        # 更新当前模型的设置
        selected_model = self.model_combo.currentData()
        config['model_settings'][selected_model] = {
            'voice_id': self.voice_combo.currentData(),
            'sample_rate': int(self.sample_rate_combo.currentText()),
            'speed': self.speed_input.value(),
            'gain': self.gain_input.value(),
            'response_format': self.format_combo.currentText()
        }
        
        # 保存配置
        os.makedirs('data', exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    def open_settings(self):
        dialog = SettingsDialog(self.api_key, self.api_url)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.api_key, self.api_url = dialog.get_settings()
            self.client = SiliconFlowClient(self.api_key, self.api_url)
            self.save_config()  # 保存配置文件
        
    def upload_voice(self):
        dialog = UploadVoiceDialog([(self.model_combo.itemText(i), self.model_combo.itemData(i)) for i in range(self.model_combo.count())], self.model_combo.currentData(), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            file_path, name, text, model = dialog.get_data()
            # 验证customName的有效性
            if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', name):
                QMessageBox.warning(self, "错误", "音色名称无效。只能包含字母、数字、下划线和连字符，且不能超过64个字符。")
                return
            if not text:
                QMessageBox.warning(self, "错误", "请输入要转换的文本!")
                return
            try:
                # 读取音频文件
                with open(file_path, 'rb') as f:
                    audio_data = f.read()
                
                # 构建multipart/form-data格式的音频数据
                audio_content = f'data:audio/mpeg;base64,{base64.b64encode(audio_data).decode("utf-8")}'
                
                # 使用model的实际值而不是显示名称
                actual_model = self.model_display_to_actual.get(model, model)  # 获取映射后的模型值
                
                response = self.client.upload_voice(
                    audio=audio_content,
                    model=actual_model,
                    customName=name,
                    text=text
                )
                QMessageBox.information(self, "成功", "音色上传成功!")
                self.load_voice_list()  # 重新加载音色列表
            except Exception as e:
                QMessageBox.warning(self, "错误", f"上传失败: {str(e)}")
                print(f"详细错误信息: {e}")
        
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
        if self.client:  # 只在客户端已初始化时加载音色列表
            self.load_voice_list()

    def load_custom_voice_list(self):
        if not self.client:
            return
        try:
            self.custom_voice_list.clear()  # 清空现有列表
            voices = self.client.get_voice_list().get('result', [])
            for voice in voices:
                voice_name = voice.get('customName', '未命名')
                voice_id = voice.get('uri')
                # 创建一个容器
                container = QWidget()
                layout = QHBoxLayout(container)
                item = QListWidgetItem()  # 创建空的列表项
                self.custom_voice_list.addItem(item)  # 添加空的列表项
                item.setSizeHint(container.sizeHint())  # 设置列表项的大小
                # 添加音色名称标签
                name_label = QLabel(voice_name)
                layout.addWidget(name_label)
                # 创建删除按钮
                delete_button = QPushButton('删除')
                delete_button.clicked.connect(lambda checked, id=voice_id: self.delete_voice(id))
                layout.addWidget(delete_button)  # 将删除按钮添加到布局中
                # 将容器设置为列表项的widget
                self.custom_voice_list.setItemWidget(item, container)
                self.delete_buttons.append(delete_button)
        except Exception as e:
            QMessageBox.warning(self, '错误', f'加载自定义音色列表失败: {str(e)}')

    def delete_voice(self, voice_id):
        try:
            # 打印出要删除的 voice_id 以便调试
            print(f"尝试删除音色: {voice_id}")
            
            # 调用 API 删除音色
            response = self.client.delete_voice(voice_id)
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
        dialog = QDialog(self)
        dialog.setWindowTitle('自定义音色列表')
        layout = QVBoxLayout()
        custom_voice_list_widget = QListWidget()

        # 创建并启动线程
        self.load_voice_thread = LoadVoiceListThread(self.client)
        self.load_voice_thread.finished.connect(lambda voices: self.populate_voice_list(custom_voice_list_widget, voices))
        self.load_voice_thread.start()

        layout.addWidget(custom_voice_list_widget)
        dialog.setLayout(layout)
        dialog.exec()

    def populate_voice_list(self, custom_voice_list_widget, voices):
        for voice in voices:
            voice_name = voice.get('customName', '未命名')
            voice_id = voice.get('uri')
            item = QListWidgetItem(voice_name)
            item.setData(Qt.ItemDataRole.UserRole, voice_id)  # 存储音色ID
            custom_voice_list_widget.addItem(item)
            delete_button = QPushButton('删除')
            delete_button.clicked.connect(lambda checked, id=voice_id: self.delete_voice(id))
            custom_voice_list_widget.setItemWidget(item, delete_button)

def main():
    app = QApplication(sys.argv)
    window = TextToSpeechApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 