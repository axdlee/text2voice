import requests
import json
import os
from typing import Optional, Dict, Any

class SiliconFlowClient:
    DEFAULT_MODEL = "FunAudioLLM/CosyVoice2-0.5B"
    AVAILABLE_MODELS = {
        "fishaudio/fish-speech-1.5": "Fish-Speech-1.5 (充值余额付费)",
        "fishaudio/fish-speech-1.4": "Fish-Speech-1.4 (充值余额付费)",
        "FunAudioLLM/CosyVoice2-0.5B": "CosyVoice2-0.5B (赠送余额付费)",
        "RVC-Boss/GPT-SoVITS": "GPT-SoVITS (赠送余额付费)"
    }
    
    def __init__(self, api_key: str, api_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = api_url or "https://api.siliconflow.cn/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
    def create_speech(self, text: str, voice_id: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
        """
        将文本转换为语音
        """
        url = f"{self.base_url}/audio/speech"
        
        # 设置Content-Type为multipart/form-data
        headers = self.headers.copy()
        
        # 准备表单数据
        data = {
            "model": model or self.DEFAULT_MODEL,
            "input": text,
            "response_format": "mp3",
            "sample_rate": 44100,
            "stream": False
        }
        
        if voice_id:
            data["voice"] = voice_id
            
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
        
    def get_voice_list(self) -> Dict[str, Any]:
        """
        获取可用的语音列表
        """
        url = f"{self.base_url}/audio/voice/list"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
        
    def delete_voice(self, voice_id: str) -> Dict[str, Any]:
        """
        删除指定的语音
        """
        url = f"{self.base_url}/audio/voice/{voice_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
        
    def upload_voice(self, file_path: str, name: str) -> Dict[str, Any]:
        """
        上传语音文件
        """
        url = f"{self.base_url}/uploads/audio/voice"
        
        # 读取音频文件并进行base64编码
        with open(file_path, 'rb') as f:
            audio_data = f.read()
            
        data = {
            'model': 'fishaudio/fish-speech-1.5',
            'customName': name,
            'text': '在一无所知中, 梦里的一天结束了，一个新的轮回便会开始',
            'audio': ('audio.mp3', audio_data, 'audio/mpeg')
        }
        
        response = requests.post(url, headers=self.headers, files=data)
        response.raise_for_status()
        return response.json()
        
    def create_transcription(self, file_path: str) -> Dict[str, Any]:
        """
        创建音频转写
        """
        url = f"{self.base_url}/audio/transcriptions"
        files = {
            'file': open(file_path, 'rb')
        }
        data = {
            'model': 'FunAudioLLM/SenseVoiceSmall'
        }
        response = requests.post(url, headers=self.headers, data=data, files=files)
        response.raise_for_status()
        return response.json() 