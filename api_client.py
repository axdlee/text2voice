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
    
    DEFAULT_VOICES = {
        "fishaudio/fish-speech-1.5": [
            "fishaudio/fish-speech-1.5:alex",
            "fishaudio/fish-speech-1.5:anna",
            "fishaudio/fish-speech-1.5:bella",
            "fishaudio/fish-speech-1.5:benjamin",
            "fishaudio/fish-speech-1.5:charles",
            "fishaudio/fish-speech-1.5:claire",
            "fishaudio/fish-speech-1.5:david",
            "fishaudio/fish-speech-1.5:diana"
        ],
        "fishaudio/fish-speech-1.4": [
            "fishaudio/fish-speech-1.4:alex",
            "fishaudio/fish-speech-1.4:anna",
            "fishaudio/fish-speech-1.4:bella",
            "fishaudio/fish-speech-1.4:benjamin",
            "fishaudio/fish-speech-1.4:charles",
            "fishaudio/fish-speech-1.4:claire",
            "fishaudio/fish-speech-1.4:david",
            "fishaudio/fish-speech-1.4:diana"
        ],
        "FunAudioLLM/CosyVoice2-0.5B": [
            "FunAudioLLM/CosyVoice2-0.5B:alex",
            "FunAudioLLM/CosyVoice2-0.5B:anna",
            "FunAudioLLM/CosyVoice2-0.5B:bella",
            "FunAudioLLM/CosyVoice2-0.5B:benjamin",
            "FunAudioLLM/CosyVoice2-0.5B:charles",
            "FunAudioLLM/CosyVoice2-0.5B:claire",
            "FunAudioLLM/CosyVoice2-0.5B:david",
            "FunAudioLLM/CosyVoice2-0.5B:diana"
        ],
        "RVC-Boss/GPT-SoVITS": [
            "RVC-Boss/GPT-SoVITS:alex",
            "RVC-Boss/GPT-SoVITS:anna",
            "RVC-Boss/GPT-SoVITS:bella",
            "RVC-Boss/GPT-SoVITS:benjamin",
            "RVC-Boss/GPT-SoVITS:charles",
            "RVC-Boss/GPT-SoVITS:claire",
            "RVC-Boss/GPT-SoVITS:david",
            "RVC-Boss/GPT-SoVITS:diana"
        ]
    }
    
    def __init__(self, api_key: str, api_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = api_url or "https://api.siliconflow.cn/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
    def create_speech(self, text: str, voice_id: Optional[str] = None, model: Optional[str] = None, response_format: str = "mp3", sample_rate: int = 32000, speed: float = 1, gain: float = 0) -> Dict[str, Any]:
        """
        将文本转换为语音
        """
        url = f"{self.base_url}/audio/speech"
        
        # 设置请求头
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        
        # 确定使用的模型
        selected_model = model or self.DEFAULT_MODEL
        
        # 准备请求数据
        data = {
            "model": selected_model,
            "input": text,
            "voice": voice_id or self.DEFAULT_VOICES[selected_model][0],  # 使用默认语音
            "response_format": response_format,  # 确保这是字符串类型
            "sample_rate": int(sample_rate),  # 确保这是整数类型
            "stream": True,
            "speed": float(speed),  # 确保这是浮点数类型
            "gain": float(gain)  # 确保这是浮点数类型
        }
            
        # 打印调试信息
        print(f"请求URL: {url}")
        print(f"请求头: {headers}")
        print(f"请求数据: {data}")
        
        # 发送请求
        response = requests.post(url, headers=headers, json=data)
        
        # 如果是400错误，打印详细的错误信息
        if response.status_code == 400:
            print(f"错误响应: {response.text}")
            
        response.raise_for_status()
        
        # 如果响应是二进制数据，直接返回
        if response.headers.get('content-type', '').startswith('audio/'):
            return response.content
            
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
        
    def upload_voice(self, audio: str, model: str, customName: str, text: str) -> Dict[str, Any]:
        """
        上传语音文件
        Args:
            audio: base64编码的音频数据，格式为 'data:audio/mpeg;base64,...'
            model: 模型名称
            customName: 自定义音色名称
            text: 音频对应的文本
        """
        url = f"{self.base_url}/uploads/audio/voice"
        
        # 准备multipart/form-data格式的数据
        files = {
            'audio': (None, audio),
            'model': (None, model),
            'customName': (None, customName),
            'text': (None, text)
        }
        
        # 打印调试信息
        print(f"请求URL: {url}")
        print(f"请求头: {self.headers}")
        print(f"请求数据: {files}")
        
        response = requests.post(url, headers=self.headers, files=files)
        
        # 如果是400错误，打印详细的错误信息
        if response.status_code == 400:
            print(f"错误响应: {response.text}")
            
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