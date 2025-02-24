from PyQt6.QtWidgets import QDialog
from ui.base.main_window import BaseMainWindow
from ui.components.settings_dialog import SettingsDialog
from ui.components.voice_list_dialog import VoiceListDialog
from ui.components.upload_dialog import UploadVoiceDialog
import re
import base64
import os
import time

class MainWindow(BaseMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.logger.info("初始化主窗口...")
        self.init_ui()
        
    def convert_text(self):
        """转换文本"""
        try:
            if not self.core.tts_service:
                self.show_error("请先设置API密钥!")
                return
                
            text = self.conversion_panel.text_input.toPlainText()
            if not text:
                self.show_warning("请输入要转换的文本!")
                return
                
            # 获取转换参数
            params = {
                'voice_id': self.conversion_panel.voice_combo.currentData(),
                'model': self.conversion_panel.model_combo.currentData(),
                'sample_rate': int(self.conversion_panel.sample_rate_combo.currentText()),
                'speed': self.conversion_panel.speed_input.value(),
                'gain': self.conversion_panel.gain_input.value(),
                'response_format': self.conversion_panel.format_combo.currentText()
            }
            
            # 开始转换
            self.status_bar.show_progress(True)
            worker = self.core.start_conversion(text, params)
            worker.finished.connect(self._on_conversion_finished)
            worker.error.connect(self._on_conversion_error)
            worker.start()
            
        except Exception as e:
            self.logger.error("转换失败", exc_info=True)
            self.show_error(f"转换失败: {str(e)}")
            self.status_bar.show_progress(False)
            
    def _on_conversion_finished(self, result):
        """转换完成回调"""
        try:
            # 保存音频文件
            filename = f"output_{int(time.time())}.{self.conversion_panel.format_combo.currentText()}"
            filepath = self.core.audio_mgr.save_audio(result, filename)
            
            # 播放音频
            self.core.audio_mgr.play(filepath)
            
            self.status_bar.show_message("转换完成", 5000)
            self.status_bar.show_progress(False)
            
        except Exception as e:
            self.logger.error("处理转换结果失败", exc_info=True)
            self.show_error(f"处理转换结果失败: {str(e)}")
            self.status_bar.show_progress(False)
            
    def _on_conversion_error(self, error):
        """转换错误回调"""
        self.show_error(f"转换失败: {error}")
        self.status_bar.show_progress(False)
        
    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(
            self.core.get_config('api_key', ''),
            self.core.get_config('api_url', '')
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            api_key, api_url = dialog.get_settings()
            self.core.init_tts_service(api_key, api_url)
            self.core.save_config({
                'api_key': api_key,
                'api_url': api_url
            })
            
    def show_custom_voice_list(self):
        """显示自定义音色列表"""
        if not self.core.tts_service:
            self.show_error("请先设置API密钥!")
            return
            
        dialog = VoiceListDialog(self, self.core.tts_service)
        dialog.exec() 