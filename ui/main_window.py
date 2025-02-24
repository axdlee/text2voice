from PyQt6.QtWidgets import QDialog, QFileDialog
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
        
    def select_output_directory(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.core.get_config('output_dir', '')
        )
        if directory:
            self.core.save_config({'output_dir': directory})
            self.status_bar.show_message(f"已设置输出目录: {directory}", 3000)
        
    def on_model_changed(self, index):
        """模型变更回调"""
        model = self.conversion_panel.model_combo.currentData()
        self.logger.info(f"切换模型: {model}")
        
        # 更新相关UI状态
        self.conversion_panel.update_model_settings(model)
        
        # 保存当前选择
        self.core.save_config({'last_model': model})
        
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
            # 获取输出目录
            output_dir = self.core.get_config('output_dir', 'output')
            
            # 生成文件名 (使用前20个字符作为文件名)
            text = self.conversion_panel.text_input.toPlainText()[:20]
            filename = f"{text}_{int(time.time())}.{self.conversion_panel.format_combo.currentText()}"
            
            # 保存音频文件
            filepath = self.core.audio_mgr.save_audio(result, filename, output_dir)
            
            # 播放音频
            self.core.audio_mgr.play(filepath)
            
            self.status_bar.show_message(f"转换完成: {filename}", 5000)
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
        try:
            dialog = VoiceListDialog(self)
            dialog.exec()
        except Exception as e:
            self.logger.error("显示音色列表失败", exc_info=True)
            self.show_error(f"显示音色列表失败: {str(e)}")

    def upload_voice(self):
        """上传自定义音色"""
        if not self.core.tts_service:
            self.show_error("请先设置API密钥!")
            return
            
        dialog = UploadVoiceDialog(self, self.core.tts_service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 刷新音色列表
            self.conversion_panel.refresh_voices()

    def delete_voice_and_refresh(self, voice_id: str, voice_list_dialog):
        """删除音色并刷新列表
        Args:
            voice_id: 要删除的音色ID
            voice_list_dialog: 音色列表对话框
        """
        try:
            # 删除音色
            self.core.tts_service.delete_voice(voice_id)
            
            # 获取当前选中的模型
            current_model = self.conversion_panel.model_combo.currentData()
            
            # 刷新音色列表对话框
            voice_list_dialog.refresh_voices()
            
            # 刷新主窗口的音色列表，传入当前模型
            self.conversion_panel.refresh_voices(current_model)
            
            # 显示成功消息
            self.show_info(f"音色删除成功!")
            
        except Exception as e:
            self.logger.error("删除音色失败", exc_info=True)
            self.show_error(f"删除失败: {str(e)}") 