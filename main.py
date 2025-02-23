import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                           QListWidget, QMessageBox, QComboBox, QProgressBar, 
                           QDialog, QLineEdit, QFormLayout, QDialogButtonBox, 
                           QFileDialog, QInputDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import requests
from dotenv import load_dotenv
from api_client import SiliconFlowClient
from audio_player import AudioPlayer
from typing import Dict, Any

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

class TextToSpeechApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_file = 'data/config.json'
        self.api_key = None
        self.api_url = None
        self.output_directory = 'temp'  # 默认输出目录
        self.client = None
        self.audio_player = AudioPlayer()
        self.current_audio_url = None
        self.conversion_thread = None
        
        # 先创建UI
        self.initUI()
        
        # 再加载配置
        self.load_config()
        
        # 初始化客户端
        if self.api_key:
            self.client = SiliconFlowClient(self.api_key, self.api_url)
            self.load_voice_list()

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
        self.voice_combo.addItem("默认语音", None)
        left_layout.addWidget(QLabel("选择语音:"))
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
        
        # 其他参数输入
        self.sample_rate_input = QLineEdit("32000")
        self.speed_input = QLineEdit("1")
        self.gain_input = QLineEdit("0")
        left_layout.addWidget(QLabel("采样率:"))
        left_layout.addWidget(self.sample_rate_input)
        left_layout.addWidget(QLabel("倍速:"))
        left_layout.addWidget(self.speed_input)
        left_layout.addWidget(QLabel("音量增益:"))
        left_layout.addWidget(self.gain_input)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
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
        
        # 右侧布局
        right_layout = QVBoxLayout()
        
        # 语音列表
        right_layout.addWidget(QLabel("语音列表:"))
        self.voice_list = QListWidget()
        right_layout.addWidget(self.voice_list)
        
        # 添加左右布局到主布局
        layout.addLayout(left_layout, stretch=2)
        layout.addLayout(right_layout, stretch=1)
        
        # 设置主布局
        main_widget.setLayout(layout)
        
        # 连接信号
        self.convert_btn.clicked.connect(self.convert_text)
        self.play_btn.clicked.connect(self.play_audio)
        self.stop_btn.clicked.connect(self.stop_audio)
        self.settings_btn.clicked.connect(self.open_settings)
        self.upload_voice_btn.clicked.connect(self.upload_voice)
        self.output_dir_btn.clicked.connect(self.select_output_directory)
        self.model_combo.currentIndexChanged.connect(self.load_voice_list)
        
        # 加载语音列表
        self.load_voice_list()
        
    def load_voice_list(self):
        if not self.client:
            QMessageBox.warning(self, "错误", "API客户端未初始化!")
            return
        
        try:
            # 清空现有音色
            self.voice_combo.clear()
            
            # 加载系统音色
            selected_model = self.model_combo.currentData()
            voices = self.client.get_voice_list()
            print(f"获取到的音色列表: {voices}")  # 调试信息
            for voice in voices.get('voices', []):
                if voice.get('model') == selected_model:  # 仅添加当前模型的音色
                    self.voice_combo.addItem(voice.get('name', ''), voice.get('id'))
            # 移除没有可用音色的提示
            
            # 添加默认音色选项
            for model, voices in SiliconFlowClient.DEFAULT_VOICES.items():
                if model == selected_model:
                    for voice in voices:
                        self.voice_combo.addItem(voice, voice)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载语音列表失败: {str(e)}")
            
    def update_voice_options(self):
        if not self.client:
            return
        
        try:
            # 清空现有音色
            self.voice_combo.clear()
            
            selected_model = self.model_combo.currentData()
            voices = self.client.get_voice_list()
            for voice in voices.get('voices', []):
                if voice.get('model') == selected_model:  # 仅添加当前模型的音色
                    self.voice_combo.addItem(voice.get('name', ''), voice.get('id'))
            # 添加默认语音选项
            for model, voices in SiliconFlowClient.DEFAULT_VOICES.items():
                if model == selected_model:
                    for voice in voices:
                        self.voice_combo.addItem(voice, voice)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载语音列表失败: {str(e)}")

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
        
        sample_rate = int(self.sample_rate_input.text())
        speed = float(self.speed_input.text())
        gain = float(self.gain_input.text())
        response_format = self.format_combo.currentText()  # 获取所选音频格式
        
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
            # 保存到用户选择的输出目录
            os.makedirs(self.output_directory, exist_ok=True)
            audio_path = os.path.join(self.output_directory, 'output.mp3')
            
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
            QMessageBox.information(self, "成功", "文本转换完成!")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存音频文件失败: {str(e)}")
            
    def handle_conversion_error(self, error_msg):
        self.convert_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.warning(self, "错误", f"转换失败: {error_msg}")
        
    def play_audio(self):
        if not self.current_audio_url:
            return
            
        try:
            self.audio_player.play(self.current_audio_url)
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"播放失败: {str(e)}")
            
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
                            self.sample_rate_input.setText(str(settings.get('sample_rate', 32000)))
                            self.speed_input.setText(str(settings.get('speed', 1.0)))
                            self.gain_input.setText(str(settings.get('gain', 0.0)))
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
            'sample_rate': int(self.sample_rate_input.text()),
            'speed': float(self.speed_input.text()),
            'gain': float(self.gain_input.text()),
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
        file_path, _ = QFileDialog.getOpenFileName(self, "选择音频文件", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            name, ok = QInputDialog.getText(self, "输入音色名称", "音色名称:")
            if ok:
                try:
                    response = self.client.upload_voice(file_path, name)
                    QMessageBox.information(self, "成功", "音色上传成功!")
                    self.load_voice_list()  # 重新加载音色列表
                except Exception as e:
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

def main():
    app = QApplication(sys.argv)
    window = TextToSpeechApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 