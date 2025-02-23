import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                           QListWidget, QMessageBox, QComboBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import requests
from dotenv import load_dotenv
from api_client import SiliconFlowClient
from audio_player import AudioPlayer

# 加载环境变量
load_dotenv()

class ConversionWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, client, text, voice_id=None):
        super().__init__()
        self.client = client
        self.text = text
        self.voice_id = voice_id
        
    def run(self):
        try:
            result = self.client.create_speech(self.text, self.voice_id)
            self.finished.emit(result.get('url', ''))
        except Exception as e:
            self.error.emit(str(e))

class TextToSpeechApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('SILICON_API_KEY')
        self.client = SiliconFlowClient(self.api_key) if self.api_key else None
        self.audio_player = AudioPlayer()
        self.current_audio_url = None
        self.conversion_thread = None
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
        
        # 语音选择下拉框
        self.voice_combo = QComboBox()
        self.voice_combo.addItem("默认语音", None)
        left_layout.addWidget(QLabel("选择语音:"))
        left_layout.addWidget(self.voice_combo)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        # 控制按钮区
        button_layout = QHBoxLayout()
        self.convert_btn = QPushButton("转换为语音")
        self.play_btn = QPushButton("播放")
        self.stop_btn = QPushButton("停止")
        
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.convert_btn)
        button_layout.addWidget(self.play_btn)
        button_layout.addWidget(self.stop_btn)
        
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
        
        # 加载语音列表
        self.load_voice_list()
        
    def load_voice_list(self):
        if not self.client:
            return
            
        try:
            voices = self.client.get_voice_list()
            for voice in voices.get('voices', []):
                self.voice_combo.addItem(voice.get('name', ''), voice.get('id'))
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
        
        self.convert_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 显示忙碌状态
        
        self.conversion_thread = ConversionWorker(self.client, text, voice_id)
        self.conversion_thread.finished.connect(self.handle_conversion_finished)
        self.conversion_thread.error.connect(self.handle_conversion_error)
        self.conversion_thread.start()
        
    def handle_conversion_finished(self, audio_url):
        self.current_audio_url = audio_url
        self.convert_btn.setEnabled(True)
        self.play_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # 下载音频文件
        try:
            response = requests.get(audio_url)
            response.raise_for_status()
            
            # 保存到临时文件
            os.makedirs('temp', exist_ok=True)
            audio_path = os.path.join('temp', 'output.mp3')
            with open(audio_path, 'wb') as f:
                f.write(response.content)
                
            self.current_audio_url = audio_path
            QMessageBox.information(self, "成功", "文本转换完成!")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"下载音频文件失败: {str(e)}")
            
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